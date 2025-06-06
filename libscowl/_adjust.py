from ._core import *
from ._db import *
from ._export import *

class LineInfo(SlotsDataClass):
    __slots__ = ('line', 'action', 'si', 'lemma', 'pos', 'defn_note', 'group_id', 'lemma_id', 'spellings', 'words', 'comments')
    def __init__(self, line):
        self.line = line
        self.words = {}
        self.action = 'adjust'
    def copy(self, base_pos):
        other = LineInfo(self.line)
        other.action = self.action
        other.si = self.si
        other.lemma = self.lemma
        other.pos = base_pos
        other.defn_note = self.defn_note
        other.spellings = self.spellings
        for pos,wes in self.words.items():
            try:
                new_pos = fixPos[(base_pos,pos)]
                other.words[new_pos] = [copy(we) for we in wes]
            except KeyError:
                pass
        other.comments = self.comments
        return other

class SubGroupInfo(SlotsDataClass):
    __slots__ = ('id', 'lines')
    def __init__(self, id, lines = None):
        self.id = id
        if lines is None:
            self.lines = []
        else:
            self.lines = lines

class GroupInfo(SlotsDataClass):
    __slots__ = ('id', 'subGroups', 'pos', 'defn_note', 'pos_class', 'usage_note', 'lemma_rank', 'commentLines', 'spellings', 'errors')
    def __init__(self):
        self.subGroups = {}
        self.pos = ''
        self.defn_note = None
        self.pos_class = None
        self.usage_note = None
        self.lemma_rank = None
        self.commentLines = []
        self.spellings = set()
        self.errors = []

def adjustEntries(conn, f = None, *,
                  preview = False, strict = True, ignoreErrors = False,
                  groupComment = None, replaceComments = True):
    if f is None:
        f = sys.stdin

    groups = []
    word_ids = {}

    errors = False
    def warn(msg):
        nonlocal errors
        errors = True
        _warn(msg)


    gi = GroupInfo()

    def registerLine(li, new_pos, outer_pos = None):
        assert li.action in ('add', 'remove', 'adjust', 'replace')

        if new_pos is None:
            new_pos = li.pos
        if outer_pos is None:
            outer_pos = new_pos

        if li.pos == 'n_v':
            registerLine(li.copy('n'), None, outer_pos)
            registerLine(li.copy('v'), None, outer_pos)
            return
        if li.pos == 'aj_av':
            registerLine(li.copy('aj'), None, outer_pos)
            registerLine(li.copy('av'), None, outer_pos)
            return

        combined_pos = 'n_v' if li.pos in ('n', 'v') else 'aj_av' if li.pos in ('aj', 'av') else None
        ids = [*conn.execute("select group_id from lemmas "
                             "where lemma = ? and base_pos = ? and defn_note = ?",
                             (li.lemma.word, combined_pos, li.defn_note))]
        if ids:
            raise ValueError(f"combined pos ({combined_pos}) found in database")

        ids = [*conn.execute("select distinct group_id, lemma_id from lemmas "
                             "where lemma = ? and base_pos = ? and defn_note = ?",
                             (li.lemma.word, li.pos, li.defn_note))]

        if li.action == 'add':
            assert li.pos == new_pos
            if len(ids) > 0:
                raise ValueError(f"cannot add line: lemma already exists")
            if new_pos not in gi.subGroups:
                gi.subGroups[new_pos] = SubGroupInfo(None)
        else:
            if len(ids) == 0:
                if not li.pos and gi.pos:
                    registerLine(li.copy(gi.pos), new_pos)
                    return
                raise ValueError(f'could not find match')
            elif len(ids) > 1:
                raise ValueError(f'multiple matches found')
            li.group_id = ids[0][0]
            li.lemma_id = ids[0][1]

            if not replaceComments:
                res = [*conn.execute("select * from group_comments where group_id = ?", (li.group_id,))]
                if res:
                    raise ValueError(f'conflicting group comments')

            if new_pos not in gi.subGroups:
                gi.subGroups[new_pos] = SubGroupInfo(li.group_id)
            elif gi.subGroups[new_pos].id is None:
                gi.subGroups[new_pos].id = li.group_id

        if gi.pos == '':
            gi.pos = outer_pos
        elif outer_pos != '' and outer_pos != gi.pos:
            raise ValueError(f'mismatch pos: {li.lemma.word}: expected {gi.pos}: got {outer_pos}')

        if li.spellings is not None:
            gi.spellings.update(li.spellings)
        gi.subGroups[new_pos].lines.append(li)

    def finalizeGroup():
        nonlocal gi, errors
        for line, err in gi.errors:
            warn(f'{line}: {err}: skipping group')
        nopos_sg = gi.subGroups.pop('', None)
        if nopos_sg and gi.subGroups:
            for sg in gi.subGroups.values():
                sg.lines += nopos_sg.lines
        elif nopos_sg:
            gi.subGroups[''] = nopos_sg
        if not gi.errors and gi.subGroups:
            groups.append(gi)
        gi = GroupInfo()

    def merge(attr, v):
        if v is None: return
        v0 = getattr(gi, attr, None)
        if v0 is None: setattr(gi, attr, v)
        elif v != v0: raise ValueError(f'conflicting values for {attr} within group')

    for line in f:
        line = line.strip()
        if line == '':
            finalizeGroup()
            continue

        if line.startswith('# '):
            continue

        if line.startswith('##'):
            gi.commentLines.append(line)
            continue

        li = LineInfo(line)
        if line.startswith('+ '):
            li.action = 'add'
            line = line[2:]
        elif line.startswith('- '):
            li.action = 'remove'
            line = line[2:]
        elif line.startswith('= '):
            li.action = 'replace'
            line = line[2:]

        try:
            m = _matchLine(line)
            if m is None:
                raise ValueError("bad line")

            li.si = ScowlInfo.parse(ifNone(m['tags'],''))
            li.lemma = WordEntry()
            (lemma_rank, li.lemma.word, li.lemma.entry_rank) = parseLemmaPart(m['lemma'].strip())
            if li.lemma.word is None:
                raise ValueError("must provide lemma")

            base_pos = ifNone(m['base_pos'], '')
            (base_pos, sep, new_base_pos) = base_pos.partition('→')
            if sep:
                base_pos = base_pos.rstrip()
                new_base_pos = new_base_pos.lstrip()
            else:
                new_base_pos = None
            li.pos = base_pos

            defn_note = ifNone(m['defn_note'], '')
            (defn_note, sep, new_defn_note) = defn_note.partition('→')
            if sep:
                defn_note = defn_note.rstrip()
                new_defn_note = new_defn_note.lstrip()
            else:
                new_defn_note = None
            li.defn_note = defn_note

            li.spellings = Spellings.parse(m['spellings'])
            li.comments = Line.splitComments(m['comments'])

            merge('defn_note', new_defn_note)
            merge('pos_class', m['pos_class'])
            merge('usage_note', m['usage_note'])
            merge('lemma_rank', noneIf(lemma_rank, Default))

            Line.procWords(li.spellings.keys() if li.spellings else '*',
                           li.lemma, base_pos, m['words'], li.words)

            registerLine(li, new_base_pos)

        except ValueError as err:
            gi.errors.append((line, err))

    finalizeGroup()

    if errors and not ignoreErrors:
        raise ValueError('aborting due to previous errors')

    if DEBUG_SQL:
        conn.executescript((_dir / 'adjust_cleanup.sql').read_text())
        conn.executescript((_dir / 'adjust_init.sql').read_text().replace("temp.", "main."))
    else:
        conn.executescript((_dir / 'adjust_init.sql').read_text())

    next_word_id = conn.execute("select max(word_id) from words").fetchone()[0] + 1

    for gi in groups:
        comment = None
        if gi.commentLines:
            comment = GroupComment.parse(*gi.commentLines)
        elif groupComment:
            comment = groupComment
        for base_pos, sg in gi.subGroups.items():
            conn.execute("savepoint sp")
            conn.execute("create temp table lemmas_accounted_for (lemma_id)")
            try:
                haveLemmaSpelling = False
                for li in sg.lines:
                    try:
                        if getattr(li, 'lemma_id', 0):
                            conn.execute("insert into lemmas_accounted_for values (?)", (li.lemma_id,))

                        group_id = getattr(li, 'group_id', sg.id)
                        conn.execute("insert or ignore into to_merge (main_group_id, other_group_id) values (?, ?)", (sg.id, group_id))

                        if li.action == 'remove':
                            conn.execute("insert into to_remove select word_id from words where lemma_id = ?", (li.lemma_id,))
                            continue

                        if li.action == 'replace':
                            conn.execute("insert into to_remove select word_id from words where lemma_id = ?", (li.lemma_id,))

                        _addMissingSpellings(li.spellings, gi.spellings)

                        if li.action == 'adjust':
                            for pos, wes in li.words.items():
                                for word_id, word, entry_rank in conn.execute("select word_id, word, entry_rank "
                                                                              "from words where lemma_id = ? and pos = ?",
                                                                              (li.lemma_id, pos)):
                                    we = next((we for we in wes if we.word == word), None)
                                    if we is None:
                                        raise ValueError(f"unaccounted for words with pos '{pos}' within line", )
                                    we._word_id = word_id
                                    if we.entry_rank is not Default and we.entry_rank != entry_rank:
                                        conn.execute("insert into new_entry_info values (?, ?, ?, ?)", (word_id, sg.id, group_id, we.entry_rank))

                        if li.action in ('add', 'replace'):
                            li.lemma_id = next_word_id

                        for pos, wes in li.words.items():
                            addMissingSpellings(wes, gi.spellings)
                            for we in wes:
                                if not hasattr(we, '_word_id'):
                                  conn.execute("insert into new_words (word_id, main_group_id, lemma_id, pos, word) values (?, ?, ?, ?, ?)",
                                               (next_word_id, sg.id, li.lemma_id, pos, we.word))
                                  we._word_id = next_word_id
                                  next_word_id += 1
                                if we.spellings:
                                    conn.executemany("insert into new_derived_variant_info values (?, ?, ?, ?, ?)",
                                                     ((li.lemma_id, pos, we._word_id, sp, vl) for sp, vl in we.spellings.items()))

                        # fixme: be more intelligent about this
                        if getattr(li, 'group_id', 0) and replaceComments:
                            conn.execute("insert or ignore into new_group_comments values (?, null)", (li.group_id,))

                        if li.spellings:
                            haveLemmaSpelling = True
                            conn.executemany("insert into new_lemma_variant_info (main_group_id, lemma_id, spelling, variant_level) values (?, ?, ?, ?)",
                                             ((sg.id, li.lemma_id, sp, vl) for sp, vl in li.spellings.items()))
                        for si in li.si:
                            conn.executemany("insert or ignore into new_scowl_data (main_group_id, level, category, region, tag) values (?, ?, ?, ?, ?)",
                                             ((sg.id, si.level, si.category, si.region, tag) for tag in si.tags))
                        if li.comments:
                            conn.executemany("insert into new_lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                                             ((li.lemma_id, i, c) for (i, c) in enumerate(li.comments)));
                        elif replaceComments:
                            conn.execute("insert or ignore into new_lemma_comments (lemma_id, order_num) values (?, -1)", (li.lemma_id,))
                    except ValueError as err:
                        raise ValueError(f"failed to add line: {li.line}: {err}")
                # fixme: look into avoiding duplicates
                conn.execute("insert or replace into new_group_info (main_group_id, base_pos, defn_note, pos_class, usage_note, lemma_rank) values (?, ?, ?, ?, ?, ?)",
                             (sg.id, base_pos, gi.defn_note, gi.pos_class, gi.usage_note,
                              None if gi.lemma_rank is None else '' if gi.lemma_rank == '_' else gi.lemma_rank))
                if comment:
                    conn.execute("insert or replace into new_group_comments values (?, ?)", (sg.id, str(comment)))

                unaccountedFor = [
                    *conn.execute("select word from words join to_merge on group_id = other_group_id "
                                  "where main_group_id = ? and word_id = lemma_id and word_id not in (select * from lemmas_accounted_for)",
                                  (sg.id,))] if haveLemmaSpelling and strict else None
                if unaccountedFor:
                    raise ValueError(f"unaccounted lemmas: {', '.join(word for word, in unaccountedFor)}")

                conn.execute("drop table lemmas_accounted_for")
            except ValueError as err:
                warn(f"{err}: skipping group")
                conn.execute("rollback to sp")

            conn.execute("release savepoint sp")

    if errors and not ignoreErrors:
        raise ValueError('aborting due to previous errors')

    conn.execute("create temp table filtered as "
                 "select to_merge.* "
                 "from to_merge "
                 "join groups a on main_group_id  = a.group_id "
                 "join groups b on other_group_id = b.group_id where a.base_pos = '' or b.base_pos != ''")
    res = [*conn.execute("select * from filtered a join filtered b on a.other_group_id = b.other_group_id and a.main_group_id != b.main_group_id")]
    if res:
        raise ValueError("duplicates found")
    conn.execute("drop table filtered")

    conn.executescript((_dir / 'adjust_proc.sql').read_text())

    if preview:
        clusters = importFromDB(conn, filterQuery = 'select main_group_id from to_merge')
        exportAsText(clusters, conn, sys.stdout, showExtraInfo = False)
        conn.rollback()
    else:
        conn.execute("delete from cluster_map")
        conn.commit()

    if not DEBUG_SQL:
        conn.executescript((_dir / 'adjust_cleanup.sql').read_text())
        conn.commit()

