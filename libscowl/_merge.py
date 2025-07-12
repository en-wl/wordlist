from ._core import *
from ._import import *
from ._db import *
from ._export import *

def mergeEntries(conn, f = None, *,
                 onConflict = 'merge', onVariantConflict = 'replace',
                 simplifyScowlInfo = None, ignoreErrors = None,
                 preview = False):
    if simplifyScowlInfo is True:
        raise RuntimeError("simplifyScowlInfo unimplemented")
    if ignoreErrors is True:
        raise RuntimeError("ignoreErrors unimplemented")
    if f is None:
        f = sys.stdin
    tag = None
    lines = list(f)
    if len(lines) > 0 and lines[0].startswith('#:: '):
        header = lines[0][4:].split()
        if len(header) == 0 or header[0] != 'merge':
            raise ValueError("unexpected file format")
        if len(header) > 1:
            tag = header[1]
        lines = lines[1:]
    
    groups = []
    clusterComments = {}
    _mergeText(lines, groups, clusterComments)
    groups = _finalizeGroups(groups)

    conn.execute("begin")

    next_group_id,  = next(conn.execute("select coalesce(max(group_id) + 2, 1) from groups"))
    next_word_id, = next(conn.execute("select coalesce(max(word_id) + 1, 1) from words"))

    conn.execute("create temp table merged_groups (group_id integer primary key)")

    for grp in groups:
        if tag is not None:
            for l in grp.lines:
                for si in l.si:
                    si.tags.add(tag)
            for o in grp.override.values():
                for si in o.si:
                    si.tags.add(tag)
        try:
            conn.execute("savepoint sp")
            (next_group_id, next_word_id) = _mergeGroup(conn, grp, next_group_id, next_word_id,
                                                        onConflict = onConflict,
                                                        onVariantConflict = onVariantConflict)
            conn.execute("insert or ignore into merged_groups values (?)", (grp._group_id,))
            conn.execute("release sp")
        except Exception as err:
            conn.execute("rollback to sp")
            conn.execute("release sp")
            raise ValueError(f"failed to add group: {grp.headword} <{grp.base_pos}> {{{grp.defn_note}}}")

    for comment in clusterComments:
        # fixme
        pass

    if preview:
        clusters = importFromDB(conn, filterQuery =
                                "with l as (select * from words join fuzzy using (word) where lemma_id = word_id) "
                                "  select b.group_id from merged_groups m cross join l as a on m.group_id = a.group_id cross join l as b using (word_key) ")
        exportAsText(clusters, conn, sys.stdout, showExtraInfo = False)
        conn.rollback()
    else:
        conn.execute("drop table merged_groups")
        conn.execute("delete from cluster_map")
        conn.commit()


def _mergeGroup(conn, grp, next_group_id, next_word_id, *, onConflict, onVariantConflict):
    assert onConflict in ('merge', 'replace', 'error')
    assert onVariantConflict in ('replace', 'error')

    group_ids = set()
    for lemma in grp.entries:
        for (id,) in conn.execute("select group_id from lemmas "
                                  "where lemma = ? and base_pos = ? and defn_note = ?",
                                  (lemma.lemma, grp.base_pos, grp.defn_note)):
            group_ids.add(id)
    if len(group_ids) > 0 and onConflict == 'error':
        raise ValueError(f"group already exists: {grp.entries[0].lemma} <{grp.base_pos}> {{{grp.defn_note}}}")

    if onConflict == 'replace' and group_id is not None:
        conn.executemany("delete from groups where group_id = ?", ((group_id,) for group_id in group_ids))
        group_ids.clear()

    if not group_ids:
        grp._group_id = next_group_id
        return _exportGroup(conn, grp, next_group_id, next_word_id)

    group_id = (sorted(group_ids))[0]
    if len(group_ids) > 1:
        group_ids_str = ','.join(str(_id) for _id in group_ids)
        cur = conn.execute("select count(distinct pos_class), count(distinct usage_note), count(distinct group_rank) "
                           f"from groups where group_id in ({group_ids_str})")
        (pos_class_cnt, usage_note_cnt, group_rank_cnt) = next(cur)
        if pos_class_cnt > 1 and grp.pos_class is Default:
            raise ValueError("can't merge groups: conflicting pos class")
        if usage_note_cnt > 1 and grp.usage_note is Default:
            raise ValueError("can't merge groups: conflicting usage note")
        if group_rank_cnt > 1 and grp.group_rank is Default:
            raise ValueError("can't merge groups: conflicting lemma rank")
        other_group_ids = group_ids - {group_id}
        conn.executemany("update words set group_id = ? where group_id = ?",
                         ((group_id, _id) for _id in other_group_ids))
        conn.executemany("insert or ignore into scowl_data(size,category,region,tag,group_id,pos) "
                         "select size,category,region,tag,?,pos "
                         "from scowl_data where group_id = ?",
                         ((group_id, _id) for _id in other_group_ids))
        conn.executemany("delete from groups where group_id = ?", ((_id,) for _id in other_group_ids));
        # fixme: handle group comments
            
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
            haveDerivedSpelling = next((True for we in wes if we.spellings is not None), False)

            for we in wes:
                if we.spellings is not None:
                    haveDerivedSpelling = True

            for we in wes:
                if lemma_id is None:
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
                    if we.entry_rank != '':
                        conn.execute("update words set entry_rank = ? where word_id = ?", (we.entry_rank, word_id,))
                    if haveDerivedSpelling:
                        conn.execute("delete from derived_variant_info where word_id = ?", (word_id,))

                if we.spellings is not None and '' in we.spellings:
                    variant_level = we.spellings['']
                    spellings = le.spellings.keys() if le.spellings else ['_']
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, variant_level) for sp in spellings))
                elif we.spellings is not None:
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, vl) for sp, vl in we.spellings.items()))
                word_id += 1

        if le.spellings:
            haveLemmaSpellings = True
        lemmaSpellings[lemma_id] = le.spellings

        # fixme: be more intelligent about lemma comments
        conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                         ((lemma_id, i, c) for i, c in enumerate(le.comments)))

        ov = grp.override.get(le.lemma, None)
        if ov:
            for tag in ov.si.tags:
                conn.execute("insert or ignore into scowl_override (size, category, region, tag, word_id) values (?, ?, ?, ?, ?)",
                             (ov.si.size, ov.si.category, ov.si.region, tag, lemma_id))
                for word in ov.words:
                    conn.execute("insert or ignore into scowl_override "
                                 "select ?, ?, ?, ?, word_id from words where lemma_id = ? and word = ?",
                                 (ov.si.size, ov.si.category, ov.si.region, tag, lemma_id, word))

    if haveLemmaSpellings:
        existing = {
            lemma_id: vl for lemma_id, vl
            in conn.execute("select lemma_id,min(variant_level) "
                            "from words left join lemma_variant_info using (lemma_id) "
                            "where group_id = ? and word_id = lemma_id "
                            "group by lemma_id",
                            (group_id,))}

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
                conn.execute("delete from group_comments where group_id = ?", (group_id,))
        elif anyVariantInfo:
            raise ValueError("existing lemma variant info found")

    for l in grp.lines:
        for pos in l.poses:
            conn.executemany("insert or ignore into scowl_data (size, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                             ((si.size, si.category, si.region, tag, group_id, pos) for si in l.si for tag in si.tags))

    if grp.commentLines:
        conn.execute("insert into group_comments (group_id, comment) values (?, ?)",
                     (group_id, str(group.commentLines)))

    return (next_group_id, next_word_id)
