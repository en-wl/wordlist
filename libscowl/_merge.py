from collections import defaultdict
import io

from ._core import *
from ._import import *
from ._db import *
from ._export import *
from ._adjust import adjustEntries

def mergeEntries(conn, f = None, *,
                 simplifyScowlInfo = None, ignoreErrors = None,
                 adjustPOS = 'default', preview = False):
    """
    Merge entries in SCOWL text format into an existing database.

    This is essentially an "incremental import": it parses the same text format
    that libscowl exports, then inserts new groups/words or merges them into
    existing groups.

    Supported header (first line):
      #:: merge [<tag>|<category>] [FLAGS]

    Transactions:
    - Runs inside a single transaction, with a SAVEPOINT per group so that one
      bad group doesn't abort the whole merge.
    - If preview=True, prints the affected clusters and rolls back the whole
      transaction.
    - If preview=False, commits but clears cluster_map (caller should rebuild it
      via createClusterMap/finalizeDB).
    """
    if simplifyScowlInfo is True:
        raise RuntimeError("simplifyScowlInfo unimplemented")
    if f is None:
        f = sys.stdin
    onConflict = 'merge'
    onVariantConflict = 'replace'
    doAdjustPos = False
    clearEntryRank = True
    tag = None
    lines = list(f)
    if len(lines) > 0 and lines[0].startswith('#:: '):
        header = lines[0][4:].split()
        if len(header) == 0 or header[0] != 'merge':
            raise ValueError("unexpected file format")
        for flag in header[1:]:
            if flag[0] == '[' and flag[-1] == ']':
                tag = flag
            elif flag[0] == '(' and flag[-1] == ')':
                tag = flag
            elif flag == ':skip-on-variant-conflict':
                onVariantConflict = 'skip'
            elif flag == 'error-on-variant-conflict':
                onVariantConflict = 'error'
            elif flag == ':replace-on-conflict':
                onConflict = 'replace'
            elif flag == ':error-on-conflict':
                onConflict = 'error'
            elif flag == ':adjust-pos':
                doAdjustPos = True
            elif flag == ':keep-entry-rank':
                # experiential, name may change
                clearEntryRank = False
            else:
                raise ValueError(f"unknown flag found in header: {flag}")
        lines = lines[1:]

    adjustOnly = False
    _adjustPosPreview = 'no'
    if adjustPOS == 'default':
        pass
    elif adjustPOS == 'skip':
        doAdjustPos = False
    elif adjustPOS == 'only':
        adjustOnly = True
    elif adjustPOS == 'script':
        adjustOnly = True
        _adjustPosPreview = 'script'
    elif adjustPOS == 'preview':
        adjustOnly = True
        _adjustPosPreview = 'result'
    else:
        raise ValueError("adjustPOS must be one of: default, skip, only, script, or preview")

    if doAdjustPos and preview:
        raise ValueError("can not preview when also adjusting POS")

    # parse input
    groups = []
    clusterComments = {}
    _mergeText(lines, groups, clusterComments)
    groups = _finalizeGroups(groups)
    failedCnt = 0

    try:
        # do initial matchup
        _matchGroups(conn, groups)

        # adjust POS if required
        if doAdjustPos:
            _adjustPos(conn, groups, preview=_adjustPosPreview)
        if adjustOnly:
            return False
        if doAdjustPos:
            # redo matchup after adjusting POS
            conn.executescript((_dir / 'merge_match.sql').read_text())

        conn.execute("begin")

        # group_id allocation: _exportGroup increments by 2 for some "combined POS"
        # groups (n_v, aj_av) so we advance by 2 to stay on the same parity and to
        # keep room for those paired ids.
        next_group_id,  = next(conn.execute("select coalesce(max(group_id) + 2, 1) from groups"))
        next_word_id, = next(conn.execute("select coalesce(max(word_id) + 1, 1) from words"))

        conn.execute("create temp table groups_to_del (group_id integer primary key)")
        if onConflict == 'replace':
            conn.execute("insert or ignore into groups_to_del "
                         "select group_id from matched")
            removeEntries(conn)

        # Used for preview mode: track which group_ids were inserted/merged so we
        # can find all clusters that became connected to them.
        conn.execute("create temp table merged_groups (group_id integer primary key)")

        for idx, grp in enumerate(groups):
            if tag and tag[0] == '[':
                for l in grp.lines:
                    for si in l.si:
                        si.tags.add(tag)
                for o in grp.override.values():
                    for si in o.si:
                        si.tags.add(tag)
            elif tag and tag[0] == '(':
                category = tag[1:-1]
                for l in grp.lines:
                    for si in l.si:
                        si.category = category
                for o in grp.override.values():
                    for si in o.si:
                        si.category = category
            try:
                conn.execute("savepoint sp")
                (next_group_id, next_word_id) = _mergeGroup(conn, grp, idx, next_group_id, next_word_id,
                                                            onConflict = onConflict,
                                                            onVariantConflict = onVariantConflict,
                                                            clearEntryRank = clearEntryRank)
                conn.execute("insert or ignore into merged_groups values (?)", (grp._group_id,))
                conn.execute("release sp")
            except ValueError as err:
                conn.execute("rollback to sp")
                conn.execute("release sp")
                #raise
                _warn(f"failed to add group: {grp.headword} <{grp.base_pos}> {{{grp.defn_note}}}: {err}")
                failedCnt += 1

        for c in clusterComments.values():
            conn.execute("insert or replace into cluster_comments (headword, other_words, comment) values (?, ?, ?)",
                         (c.word, c.other_words, c.comment))

        if failedCnt > 0 and not ignoreErrors:
            raise ValueError(f"failed to add {failedCnt}/{len(groups)} groups")

        removeEntries(conn)

        if preview:
            # Show the clusters that would be affected. We start from the merged
            # groups, grab their lemma words (via fuzzy -> word_key), then include
            # every other group that shares those word_keys.
            clusters = importFromDB(conn, filterQuery =
                                    "with l as (select * from words join fuzzy using (word) where lemma_id = word_id) "
                                    "  select b.group_id from merged_groups m cross join l as a on m.group_id = a.group_id cross join l as b using (word_key) ")
            exportAsText(clusters, conn, sys.stdout, showExtraInfo = False)
            return False
        else:
            conn.execute("drop table merged_groups")
            conn.execute("delete from cluster_map")
            conn.commit()
            return True

    finally:
        conn.rollback()
        if not DEBUG_SQL:
            conn.executescript((_dir / 'merge_cleanup.sql').read_text())

def _matchGroups(conn, grps):
    if DEBUG_SQL:
        conn.executescript((_dir / 'merge_cleanup.sql').read_text())
        conn.executescript((_dir / 'merge_init.sql').read_text().replace("temp.", "main."))
    else:
        conn.executescript((_dir / 'merge_init.sql').read_text())
        
    conn.execute("begin")
    for idx, grp in enumerate(grps):
        conn.execute("insert into new_groups (idx, base_pos, defn_note, pos_class) values (?,?,?,?) ",
                     (idx, grp.base_pos, ifDefault(grp.defn_note, None), ifDefault(grp.pos_class, None)))
        for lemma in grp.entries:
            conn.execute("insert into new_lemmas (idx, lemma) values (?,?) ",
                         (idx, lemma.lemma))
    conn.commit()

    conn.executescript((_dir / 'merge_match.sql').read_text())

def _adjustPos(conn, grps, preview = 'no'):
    assert preview in ('no', 'script', 'result')
    # lemma, other_pos => [base_pos]
    pos_adjs = defaultdict(list)
    rows = conn.execute("""
      with
        candidates as (
          select distinct group_id, base_pos as orig_pos, base_pos as new_pos, 0 as num
            from (new_groups join new_lemmas using (idx)) 
            join lemmas using (lemma, base_pos)
          union all
          select distinct group_id, a.other_pos as orig_pos, a.base_pos as new_pos, 1 as num
            from (new_groups join new_lemmas using (idx) join overlapping_pos using (base_pos)) as a
            join lemmas b on a.lemma = b.lemma and a.other_pos = b.base_pos
          union all
          select distinct group_id, b.base_pos, a.base_pos, 2 as num
            from (new_groups join new_lemmas using (idx)) as a
            join lemmas b on a.lemma = b.lemma and a.base_pos != '' and b.base_pos = ''),
        with_rank as (
          select *,
                 rank() over (partition by group_id, new_pos order by num) as rnk
            from candidates)
      select lemma, orig_pos, new_pos
        from with_rank
        join lemmas using (group_id)
        left join lemma_variant_info using (lemma_id)
        where rnk = 1 and num > 0 and coalesce(spelling, '_') in ('A', '_') and coalesce(variant_level, 0) == 0
        order by lemma, orig_pos, new_pos;
    """)
    for lemma, orig_pos, new_pos in rows:
        pos_adjs[(lemma, orig_pos)].append(new_pos)

    invalid = []
    lines = ['#:: adjust :keep-comments']
    for (lemma, orig_pos), new_poses in pos_adjs.items():
        if orig_pos not in ('m', 'a', ''):
            continue

        if orig_pos == 'm' and 'v' not in new_poses:
            #min_size, = next(conn.execute("select min(size) as min_size  "
            #                              "from lemmas join scowl_data using (group_id) "
            #                              "where base_pos = 'm' and pos not in ('m0', 'ms') "
            #                              "and lemma=? ", (lemma,)))
            new_poses.append('v')
                                
        lines.extend(f"{lemma} <{orig_pos}→{new_pos}/>" for new_pos in new_poses)

    adjustInput = '\n\n'.join(lines)

    if len(adjustInput) == 1:
        return

    if (preview == 'script'):
        print(adjustInput)
        return

    adjustEntries(conn, io.StringIO(adjustInput), preview = (preview != 'no'))

def _mergeGroup(conn, grp, idx, next_group_id, next_word_id,
                *, onConflict, onVariantConflict, clearEntryRank):

    assert onConflict in ('merge', 'replace', 'error')
    assert onVariantConflict in ('skip', 'replace', 'error')

    #
    # Check for matching or conflicting groups
    #

    row = next(conn.execute("select lemma, base_pos, other_pos from pos_conflicts where idx = ?", (idx,)), None)
    if row:
        raise ValueError("can't merge group: "
                         f"existing pos <{row['other_pos']}> conflicts with <{row['base_pos']}> "
                         f"for lemma: {row['lemma']}")

    rows = conn.execute("select group_id from matched where idx = ? and keep",
                        (idx,))
    group_ids = {id for id, in rows}

    # nothing to merge so just create a new group and return
    if not group_ids:
        grp._group_id = next_group_id
        return _exportGroup(conn, grp, next_group_id, next_word_id, updateFuzzy=True)

    if onConflict != 'merge': # 'replace' should already be handled
        raise ValueError(f"group already exists: {grp.entries[0].lemma} <{grp.base_pos}> {{{grp.defn_note}}}")

    # check for conflicts
    row = next(conn.execute("select * from conflicts where idx = ?", (idx,)), None)
    if row:
        if row['pos_class']:
            raise ValueError("can't merge groups: conflicting pos class")
        if row['usage_note']:
            raise ValueError("can't merge groups: conflicting usage note")
        if row['group_rank']:
            raise ValueError("can't merge groups: conflicting group rank")

    group_id = min(group_ids)

    # merge groups if needed
    if len(group_ids) > 1:
        other_group_ids = group_ids - {group_id}
        conn.executemany("update words set group_id = ? where group_id = ?",
                         ((group_id, _id) for _id in other_group_ids))
        conn.executemany("insert or ignore into scowl_data(size,category,region,tag,group_id,pos) "
                         "select size,category,region,tag,?,pos "
                         "from scowl_data where group_id = ?",
                         ((group_id, _id) for _id in other_group_ids))
        conn.executemany("insert into groups_to_del values (?)", ((_id,) for _id in other_group_ids))
        # clear existing comments for now
        conn.execute("delete from group_comments where group_id = ?", (group_id,))

    #
    # Merge new info into existing group
    #

    grp._group_id = group_id
    cur = conn.execute("select pos_class, usage_note, group_rank from groups where group_id = ?" , (group_id,))
    (pos_class, usage_note, group_rank) = next(cur)
    conn.execute("update groups set pos_class = ?, usage_note = ?, group_rank = ? where group_id = ?",
                 (ifDefault(grp.pos_class, pos_class),
                  ifDefault(grp.usage_note, usage_note),
                  ifDefault(grp.group_rank, group_rank),
                  group_id))

    haveLemmaSpellings = False
    lemmaSpellings = {}
    for le in grp.entries:
        lemma_id = None
        foundLemma = None

        for pos in posmap(grp.base_pos, le.words.keys()):
            wes = le.words.get(pos, [])
            # If any word entry for this (lemma,pos) specifies spellings, we
            # treat the incoming derived_variant_info as authoritative and
            # remove any existing derived_variant_info rows for the matched
            # words (so we don't accumulate stale spellings).
            haveDerivedSpelling = any(we.spellings is not None for we in wes)

            for we in wes:
                if lemma_id is None:
                    # For a lemma, the first matching word we see is treated as
                    # the lemma row (word_id == lemma_id).
                    word_id, = next(conn.execute("select word_id from words where group_id = ? and word = ? and pos = ? and word_id = lemma_id",
                                                 (group_id, we.word, pos)),
                                    (None,))
                    foundLemma = word_id is not None
                elif foundLemma:
                    word_id, = next(conn.execute("select word_id from words where group_id = ? and lemma_id = ? and word = ? and pos = ?",
                                                 (group_id, lemma_id, we.word, pos)),
                                    (None,))
                else:
                    word_id = None

                if word_id is None:
                    word_id = next_word_id
                    next_word_id += 1
                    if lemma_id is None:
                        lemma_id = word_id
                    conn.execute("insert into words (word_id, group_id, lemma_id, pos, word, entry_rank) values (?, ?, ?, ?, ?, ?)",
                                 (word_id, group_id, lemma_id, pos, we.word, we.entry_rank))
                    conn.execute("insert or ignore into fuzzy (word, word_key) values (?, ?) ", (we.word, clusterKey(we.word).decode('ascii')))
                else:
                    if lemma_id is None:
                        lemma_id = word_id
                    if clearEntryRank or we.entry_rank is not Default:
                        conn.execute("update words set entry_rank = ? where word_id = ?", (we.entry_rank, word_id,))
                    if haveDerivedSpelling:
                        conn.execute("delete from derived_variant_info where word_id = ?", (word_id,))

                # derived_variant_info:
                # - If '' is present, it means "apply this variant_level to all
                #   of the lemma's spellings" (or '_' if lemma spellings are
                #   unknown).
                if we.spellings is not None and '' in we.spellings:
                    variant_level = we.spellings['']
                    spellings = le.spellings.keys() if le.spellings else ['_']
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, variant_level) for sp in spellings))
                elif we.spellings is not None:
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, vl) for sp, vl in we.spellings.items()))

        if le.spellings:
            haveLemmaSpellings = True
        lemmaSpellings[lemma_id] = le.spellings

        # fixme: be more intelligent about lemma comments
        conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                         ((lemma_id, i, c) for i, c in enumerate(le.comments)))

        ov = grp.override.get(le.lemma, None)
        if ov:
            # Override scowl_data for the lemma word, plus any explicitly listed
            # word forms that belong to that lemma.
            for si in ov.si:
                for tag in si.tags:
                    conn.execute("insert or ignore into scowl_override (size, category, region, tag, word_id) values (?, ?, ?, ?, ?)",
                                 (si.size, si.category, si.region, tag, lemma_id))
                    for word in ov.words:
                        conn.execute("insert or ignore into scowl_override "
                                     "select ?, ?, ?, ?, word_id from words where lemma_id = ? and word = ?",
                                     (si.size, si.category, si.region, tag, lemma_id, word))

    if haveLemmaSpellings:
        # lemma_variant_info:
        # Existing DB rows represent the "preferred" spellings/variant levels
        # for a lemma itself (not derived forms). We only update these if the
        # incoming group provides spellings for at least one lemma.
        existing = dict(conn.execute("select lemma_id,min(variant_level) "
                                     "from words left join lemma_variant_info using (lemma_id) "
                                     "where group_id = ? and word_id = lemma_id "
                                     "group by lemma_id",
                                     (group_id,)))

        # max_vl is the strictness level for the "unaccounted lemma" check
        # below: we treat the merge file as defining variant info up to this
        # level (at least 4/"common"), so omitting an existing lemma that would
        # be valid within that range is an error.
        max_vl = max(4, *(vl for lemma_id, sps in lemmaSpellings.items() for sp, vl in sps.items()))

        anyVariantInfo = False
        fullCoverage = True
        for lemma_id, vl in existing.items():
            if vl is None:
                vl = -1
            else:
                anyVariantInfo = True
            if lemma_id not in lemmaSpellings:
                fullCoverage = False
                if vl < max_vl:
                    raise ValueError("unaccounted for lemma when trying to add lemma variant info")

        if onVariantConflict == 'replace':
            for lemma_id, sps in lemmaSpellings.items():
                conn.execute("delete from lemma_variant_info where lemma_id = ?", (lemma_id,))
                conn.executemany("insert into lemma_variant_info (lemma_id, spelling, variant_level) values (?, ?, ?)",
                                 ((lemma_id, sp, vl) for sp, vl in sps.items()))
            if fullCoverage:
                # If the incoming spellings cover every lemma in the group,
                # group_comments tend to be redundant/stale (they often record
                # the spellings that we just replaced).
                conn.execute("delete from group_comments where group_id = ?", (group_id,))
        elif onVariantConflict == 'skip':
            pass
        elif anyVariantInfo:
            raise ValueError("existing lemma variant info found")

    for l in grp.lines:
        for pos in l.poses:
            conn.executemany("insert or ignore into scowl_data (size, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                             ((si.size, si.category, si.region, tag, group_id, pos) for si in l.si for tag in si.tags))

    if grp.commentLines:
        conn.execute("insert or replace into group_comments (group_id, comment) values (?, ?)",
                     (group_id, str(grp.commentLines)))

    return (next_group_id, next_word_id)
