from ._core import *
from ._import import *
from ._db import *

def mergeEntries(conn, f = None, *, tag = None, onConflict = 'merge', preview = False):
    groups = []
    clusterComments = {}
    _mergeText(sys.stdin if f is None else f, groups, clusterComments)
    groups = _finalizeGroups(groups)

    conn.execute("begin")

    next_group_id,  = next(conn.execute("select max(group_id) + 2 from groups"))
    next_word_id, = next(conn.execute("select max(word_id) + 1 from words"))

    conn.execute("create temp table merged_groups (group_id integer primary key)")

    for grp in groups:
        if tag is not None:
            for l in grp.lines:
                for si in l.si:
                    si.tags.add(tag)
            for o in grp.override.values():
                for si in o.si:
                    si.tags.add(tag)
        (next_group_id, next_word_id) = _mergeGroup(conn, grp, next_group_id, next_word_id,
                                                    onConflict = onConflict)
        conn.execute("insert into merged_groups values (?)", (grp._group_id,))

    for comment in clusterComments:
        # fixme
        pass

    if preview:
        clusters = importFromDB(conn, filterTable = 'merged_groups')
        exportAsText(clusters, conn, sys.stdout, showExtraInfo = False)
        conn.rollback()
    else:
        conn.execute("drop table merged_groups")
        conn.execute("delete from cluster_map")
        conn.commit()


def _mergeGroup(conn, grp, next_group_id, next_word_id, *, onConflict):
    assert onConflict in ('merge', 'replace', 'error')

    group_ids = set()
    for lemma in grp.entries:
        for (id,) in conn.execute("select group_id from lemmas "
                                  "where lemma = ? and base_pos = ? and defn_note = ?",
                                  (lemma.lemma, grp.base_pos, grp.defn_note)):
            group_ids.add(id)
    if len(group_ids) > 0 and onConflict == 'error':
        raise ValueError(f"group already exists: {grp.entries[0].lemma} <{grp.base_pos}> {{{grp.defn_note}}}")
    if len(group_ids) > 1:
        raise ValueError(f"multiple groups found: {grp.entries[0].lemma} <{grp.base_pos}> {{{grp.defn_note}}}")

    group_id = next(iter(group_ids), None)
    if onConflict == 'replace' and group_id is not None:
        conn.execute("delete from groups where group_id = ?", (group_id,))
        group_id = None

    if group_id is None:
        grp._group_id = next_group_id
        return _exportGroup(conn, grp, next_group_id, next_word_id)

    grp._group_id = group_id
    cur = conn.execute("select pos_class, usage_note, lemma_rank from groups where group_id = ?" , (group_id,))
    (pos_class, usage_note, lemma_rank) = next(cur)
    conn.execute("update groups set pos_class = ?, usage_note = ?, lemma_rank = ? where group_id = ?",
                 (ifDefault(grp.pos_class, pos_class),
                  ifDefault(grp.usage_note, usage_note),
                  ifDefault(grp.lemma_rank, lemma_rank),
                  group_id))

    haveLemmaSpelling = next((True for le in grp.entries if le.spellings), False)

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

        if foundLemma and haveLemmaSpelling:
            conn.execute("delete from lemma_variant_info where lemma_id = ?", (lemma_id,))

        conn.executemany("insert into lemma_variant_info (lemma_id, spelling, variant_level) values (?, ?, ?)",
                         ((lemma_id, sp, vl) for sp, vl in le.spellings.items()))

        conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                         ((lemma_id, i, c) for i, c in enumerate(le.comments)))

        ov = grp.override.get(le.lemma, None)
        if ov:
            for tag in ov.si.tags:
                conn.execute("insert or ignore into scowl_override (level, category, region, tag, word_id) values (?, ?, ?, ?, ?)",
                             (ov.si.level, ov.si.category, ov.si.region, tag, lemma_id))
                for word in ov.words:
                    conn.execute("insert or ignore into scowl_override "
                                 "select ?, ?, ?, ?, word_id from words where lemma_id = ? and word = ?",
                                 (ov.si.level, ov.si.category, ov.si.region, tag, lemma_id, word))

    for l in grp.lines:
        for pos in l.poses:
            for tag in l.si.tags:
                conn.execute("insert or ignore into scowl_data (level, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                             (l.si.level, l.si.category, l.si.region, tag, group_id, pos))

    if grp.commentLines:
        conn.execute("insert into group_comments (group_id, comment) values (?, ?)",
                     (group_id, str(group.commentLines)))

    return (next_group_id, next_word_id)
