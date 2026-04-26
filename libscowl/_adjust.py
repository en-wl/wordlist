from ._core import *
from ._db import *
from ._export import *

import time
import traceback

class LineInfo(SlotsDataClass):
    __slots__ = ('line', 'action', 'lemma', 'pos', 'defn_note', 'group_id', 'lemma_id', 'spellings', 'words', 'comments')
    def __init__(self, line, action):
        self.line = line
        self.words = {}
        self.action = action
    def copy(self, base_pos = None):
        if base_pos is None:
            base_pos = self.pos
        other = LineInfo(self.line, self.action)
        other.lemma = copy(self.lemma)
        other.pos = base_pos
        other.defn_note = self.defn_note
        other.spellings = self.spellings
        for pos,wes in self.words.items():
            try:
                new_pos = fixPos[(base_pos,pos)]
                other.words[new_pos] = [other.lemma if id(we) == id(self.lemma) else copy(we) for we in wes]
            except KeyError:
                pass
        other.comments = self.comments
        return other

class AdjScowlInfo(SlotsDataClass):
    pass

class ScowlInfoToClear(AdjScowlInfo):
    __slots__ = ('line', 'si')
    def __init__(self, line):
        self.line = line

class ScowlLineInfo(AdjScowlInfo):
    __slots__ = ('line', 'action', 'si', 'words', 'expand')
    def __init__(self, line, action):
        self.line = line
        self.action = action
        self.expand = False
        self.words = {}

class ScowlOverrideLine(AdjScowlInfo):
    __slots__ = ('line', 'action', 'si', 'words')
    def __init__(self, line, action):
        self.line = line
        self.action = action
        self.words = []

class SubGroupInfo(SlotsDataClass):
    __slots__ = ('id', 'lines')
    def __init__(self, id, lines = None):
        self.id = id
        if lines is None:
            self.lines = []
        else:
            self.lines = lines

class GroupInfo(SlotsDataClass):
    __slots__ = ('id', 'subGroups', 'adjScowlInfo',
                 'pos', 'defn_note', 'pos_class', 'usage_note', 'group_rank',
                 'commentLines', 'spellings', 'haveDerived')

    def __init__(self):
        self.subGroups = {}
        self.adjScowlInfo = []
        self.pos = ''
        self.defn_note = None
        self.pos_class = None
        self.usage_note = None
        self.group_rank = None
        self.commentLines = []
        self.spellings = set()
        self.haveDerived = False

    def merge(self, attr, v):
        if v is None: return
        v0 = getattr(self, attr, None)
        if v0 is None: setattr(self, attr, v)
        elif v != v0: raise ValueError(f'conflicting values for {attr} within group')

    @staticmethod
    def resolveLine(li, new_pos):
        """Return (new_pos, keys) for a LineInfo / (new_pos) pair.
        """
        if new_pos is None:
            if li.action in ('adjust', 'match', 'add', 'replace'):
                new_pos = li.pos
            elif li.action in ('remove', 'transfer'):
                new_pos = ''
            else:
                raise AssertionError
        if li.pos == 'n_v' or new_pos == 'n_v':
            keys = ('n', 'v')
        elif li.pos == 'aj_av' or new_pos == 'aj_av':
            keys = ('aj', 'av')
        else:
            keys = (new_pos,)
        return new_pos, keys

    def registerLine(self, conn, li, new_pos = None):
        assert li.action in ('adjust', 'match', 'add', 'remove', 'replace', 'transfer')

        new_pos, keys = self.resolveLine(li, new_pos)

        if len(keys) > 1:
            # inherent split: recurse once per target key
            if li.pos in ('n_v', 'aj_av'):
                for k in keys:
                    self.registerLine(conn, li.copy(k))
            else:
                for k in keys:
                    self.registerLine(conn, li.copy(), k)
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
                raise ValueError("cannot add line: lemma already exists")
        else:
            if len(ids) == 0:
                if not li.pos and self.pos:
                    self.registerLine(conn, li.copy(self.pos), new_pos)
                    return
                if li.action == 'match':
                    return
                raise ValueError('could not find match')
            elif len(ids) > 1:
                raise ValueError('multiple matches found')
            li.group_id = ids[0][0]
            li.lemma_id = ids[0][1]

            group_id = None if li.action == 'transfer' else li.group_id
            if self.subGroups[new_pos].id is None:
                self.subGroups[new_pos].id = group_id

        if li.spellings is not None:
            self.spellings.update(li.spellings)

        self.subGroups[new_pos].lines.append(li)

class ClusterComment(SlotsDataClass):
    __slots__ = ('lines', 'action', 'headword', 'other_words', 'commentLines')
    def __init__(self, action):
        assert action in ('replace', 'add', 'remove')
        self.lines = []
        self.action = action
        self.other_words = []
        self.commentLines = []

def splitIntoGroups(f):
    lines = [line.strip() for line in f]
    lines.append('')

    header = None
    if len(lines) > 0 and lines[0].startswith('#:: '):
        header = lines[0][4:].lstrip()

    linesByGroup = []
    startIdx = None
    for idx, line in enumerate(lines):
        if header and idx == 0:
            pass
        elif line == '':
            if startIdx is not None:
                linesByGroup.append((startIdx, idx))
                startIdx = None
        elif startIdx is None:
            startIdx = idx

    return (header, lines, linesByGroup)

def getLineAction(line):
    action = 'adjust'
    if line.startswith('? '):
        action = 'match'
        line = line[2:].lstrip()
    if line.startswith('+ '):
        action = 'add'
        line = line[2:].lstrip()
    elif line.startswith('- '):
        action = 'remove'
        line = line[2:].lstrip()
    elif line.startswith('= '):
        action = 'replace'
        line = line[2:].lstrip()
    elif line.startswith('~ '):
        action = 'transfer'
        line = line[2:].lstrip()
    return (action, line)

def adjustEntries(conn, f = None, *,
                  preview = False, strict = True, ignoreErrors = False,
                  simplifyScowlInfo = True,
                  groupComment = None, replaceComments = True):
    if f is None:
        f = sys.stdin

    header, lines, linesByGroup = splitIntoGroups(f)
    if header:
        header = lines[0][4:].split()
        if len(header) == 0 or header[0] != 'adjust':
            raise ValueError("unexpected file format")
        for flag in header[1:]:
            if flag == ':keep-comments':
                replaceComments = False
            else:
                raise ValueError(f"unknown flag found in header: {flag}")

    errors = False
    def warn(msg):
        nonlocal errors
        errors = True
        _warn(msg)

    groups = []
    clusterComments = []


    next_group_id = conn.execute("select max(group_id) from groups").fetchone()[0] + 1
    group_id_counts = {}

    for startIdx, stopIdx in linesByGroup:
        try:
            gi = None
            groupLines = []
            for line in lines[startIdx:stopIdx]:
                if line.startswith('# ') or line == '#':
                    continue

                (action, line) = getLineAction(line)

                if line.startswith('##'):
                    if gi is None:
                        if action == 'adjust':
                            gi = GroupInfo()
                        else:
                            gi = ClusterComment(action)
                    gi.commentLines.append(line)
                    continue

                if gi is None:
                    gi = GroupInfo()
                elif not isinstance(gi, GroupInfo):
                    raise ValueError("bad line")

                m = _matchLine(line)
                if m is None:
                    raise ValueError("bad line")

                tags = m['tags']
                if tags is None: # i.e. no SCOWL info

                    li = LineInfo(line, action)

                    li.lemma = WordEntry()
                    (group_rank, li.lemma.word, li.lemma.entry_rank) = parseLemmaPart(m['lemma'].strip())
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

                    gi.merge('defn_note', new_defn_note)
                    gi.merge('pos_class', m['pos_class'])
                    gi.merge('usage_note', m['usage_note'])
                    gi.merge('group_rank', noneIf(group_rank, Default))

                    wordsStr = ifNone(m['words'],'').strip()
                    if wordsStr:
                        gi.haveDerived = True
                    Line.procWords(li.spellings.keys() if li.spellings else '*',
                                   li.lemma, base_pos, wordsStr, li.words,
                                   allowAsterisk = True)

                    groupLines.append((line, li, new_base_pos))

                else: # have SCOWL info

                    if action not in ('add', 'remove', 'replace'):
                        raise ValueError("scowl info must be prefixed with one of: +, -, or =")

                    lemma = m['lemma'].strip()

                    if action == 'remove':
                        li = ScowlInfoToClear(line)
                        if lemma != '...':
                            raise ValueError('bad line')
                    elif m['override']:
                        li = ScowlOverrideLine(line, action)
                        if lemma == '...':
                            raise ValueError('bad line')
                    else:
                        li = ScowlLineInfo(line, action)
                        if lemma == '...':
                            li.expand = True
                            if m['words'] is not None:
                                raise ValueError('bad line')

                    li.si = ScowlInfo.parse(tags)

                    if lemma != '...':
                        (group_rank, word, entry_rank) = parseLemmaPart(lemma)
                        if word is not None and entry_rank is not Default:
                            raise ValueError('can not adjust entry rank when providing scowl info')

                        base_pos = ifNone(m['base_pos'], '')

                        words = [word]
                        wordsStr = ifNone(m['words'], '').strip()
                        if wordsStr == '...':
                            li.expand=True
                            wordsStr = ''
                        if wordsStr:
                            for w in wordsStr.split(','):
                                w = w.strip()
                                if w == '-':
                                    w = None
                                else:
                                    (w, entry_rank) = parseWordPart(w.strip())
                                    if entry_rank is not Default:
                                        raise ValueError('can not adjust entry rank when providing scowl info')
                                words.append(w)
                        if isinstance(li, ScowlLineInfo):
                            poses = posesFromList(base_pos, words, lambda w: w and w.endswith("'s"))
                            for pos, word in zip(poses, words):
                                if word is None:
                                    continue
                                li.words[pos] = word
                        else:
                            li.words = words

                        if m['spellings'] is not None:
                            raise ValueError('can not adjust spelling when providing scowl info')
                        if m['comments'] is not None:
                            raise ValueError('can not set lemma comments when providing scowl info')

                        gi.merge('group_rank', noneIf(group_rank, Default))
                        gi.merge('defn_note', m['defn_note'])
                        gi.merge('pos_class', m['pos_class'])
                        gi.merge('group_rank', noneIf(group_rank, Default))

                    groupLines.append((line, li, ifNone(m['base_pos'], '')))

            if gi is None:
                pass
            elif isinstance(gi, GroupInfo):
                if not strict:
                    # allow <>/<m>/<a> to match more specific POSes, but keep group uniform
                    needAdj = False
                    adjLines = []
                    needed_pos = None
                    for line, li, new_pos in groupLines:
                        if not isinstance(li, LineInfo) or new_pos is not None:
                            adjLines = None
                            needed_pos = None
                            break
                        def match_uncertain(*pos):
                            nonlocal needed_pos, li
                            if li.pos != pos[0]:
                                return False
                            if len(pos) == 3:
                                matched = {p for p, in conn.execute(
                                    "select distinct base_pos from lemmas "
                                    "where lemma = ? and base_pos in (?, ?, ?) and defn_note = ?",
                                    (li.lemma.word, *pos, li.defn_note))}
                            elif pos[0] == '':
                                matched = {p for p, in conn.execute(
                                    "select distinct base_pos from lemmas "
                                    "where lemma = ? and defn_note = ?",
                                    (li.lemma.word, li.defn_note))}
                            else:
                                raise AssertionError
                            if not matched or pos[0] in matched:
                                return False
                            if len(matched) == 1:
                                adj_pos = next(iter(matched))
                            elif len(pos) == 3 and matched == {pos[1], pos[2]}:
                                adj_pos = f"{pos[1]}_{pos[2]}"
                            else:
                                raise ValueError(f"ambiguous match for <pos[0]>: {matched}")
                            li = li.copy(adj_pos)
                            if needed_pos is None:
                                needed_pos = adj_pos
                            elif li.pos != needed_pos:
                                raise ValueError(f"inconsistent resolved POSes within group: {needed_pos} vs {adj_pos}")
                            return True
                        needAdj = (match_uncertain('m', 'n', 'v') 
                                   or match_uncertain('a', 'aj', 'av')
                                   or match_uncertain('')
                                   or needAdj)
                        adjLines.append((line, li))
                    if needAdj and adjLines:
                        groupLines = [(line, li, needed_pos) for line, li in adjLines]
                    
                # prepare subgroups and unify pos
                for line, li, new_pos in groupLines:
                  if isinstance(li, LineInfo):
                      new_pos, keys = gi.resolveLine(li, new_pos)
                      for k in keys:
                          gi.subGroups.setdefault(k, SubGroupInfo(None))
                  elif not isinstance(li, AdjScowlInfo):
                      raise AssertionError
                  if new_pos:
                      if gi.pos == '':
                          gi.pos = new_pos
                      elif new_pos != gi.pos:
                          raise ValueError(f'mismatch pos: expected {gi.pos}: got {new_pos}')

                # create synthetic match lines when needed
                neededMatchLines = {}
                for line, li, new_pos in groupLines:
                    if not isinstance(li, LineInfo):
                        continue
                    pos = ifNone(new_pos, li.pos)
                    if li.pos != pos and li.action in ('adjust', 'replace'):
                        neededMatchLines.setdefault(li.lemma.word, (li, pos))
                    if li.pos == pos:
                        neededMatchLines[li.lemma.word] = (None, None)
                for orig, pos in neededMatchLines.values():
                    if orig is None:
                        continue
                    li = LineInfo(None, 'match')
                    li.lemma = copy(orig.lemma)
                    li.pos = pos
                    li.defn_note = orig.defn_note
                    li.spellings = Spellings()
                    li.comments = []
                    gi.registerLine(conn, li)
                for line, li, pos in groupLines:
                    if isinstance(li, LineInfo):
                        gi.registerLine(conn, li, pos)
                    elif isinstance(li, AdjScowlInfo):
                        gi.adjScowlInfo.append(li)
                    else:
                        raise AssertionError

                groupLines = []
                # prune empty subgroups
                gi.subGroups = {k: sg for k, sg in gi.subGroups.items() if sg.lines}
                if not gi.subGroups:
                    # fixme: should likely just skip the group
                    #_warn(f'{line}: skipping empty group')
                    #continue
                    raise ValueError("empty group")
                nopos_sg = gi.subGroups.pop('', None)
                if nopos_sg and gi.subGroups:
                    for sg in gi.subGroups.values():
                        sg.lines += nopos_sg.lines
                elif nopos_sg:
                    gi.subGroups[''] = nopos_sg
                for sg in gi.subGroups.values():
                    if sg.id is None:
                        sg.id = next_group_id
                        next_group_id += 1
                    group_id_counts[sg.id] = group_id_counts.get(sg.id, 0) + 1
                groups.append(gi)
            elif isinstance(gi, ClusterComment):
                if gi.action == 'remove':
                    gi.headword = gi.commentLines[0][3:].lstrip()
                else:
                    raise RuntimeError("not yet implemented")
                clusterComments.append(gi)
            else:
                raise AssertionError

        except ValueError as err:
            warn(f'{line}: {err}: skipping group')

        except Exception as err:
            traceback.print_exc()
            warn(f'{line}: skipping group due to exception')


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
            comment = GroupComment(groupComment)
        for base_pos, sg in gi.subGroups.items():
            conn.execute("savepoint sp")
            if group_id_counts[sg.id] > 1:
                sg.id = next_group_id
                next_group_id += 1
            conn.execute("create temp table lemmas_accounted_for (lemma_id)")
            try:
                haveLemmaSpelling = False
                for li in sg.lines:
                    try:
                        if getattr(li, 'lemma_id', 0):
                            conn.execute("insert into lemmas_accounted_for values (?)", (li.lemma_id,))

                        group_id = getattr(li, 'group_id', sg.id)

                        if li.action == 'transfer':
                            conn.execute("insert into use_info_from (main_group_id, other_group_id, also_merge) values (?, ?, false)"
                                         " on conflict do nothing",
                                         (sg.id, group_id))
                        else:
                            conn.execute("insert into use_info_from (main_group_id, other_group_id, also_merge) values (?, ?, true)"
                                         " on conflict (main_group_id, other_group_id) do update set also_merge = true where not excluded.also_merge",
                                         (sg.id, group_id))

                        keepPoses = set()
                        for pos, wes in li.words.items():
                            if wes and wes[0].word.startswith('*'):
                                keepPoses.add(pos)
                                wes.clear()

                        if li.action == 'remove' or li.action == 'transfer':
                            for pos, wes in li.words.items():
                                for we in wes:
                                    try:
                                        word_id, = next(conn.execute("select word_id from words where lemma_id = ? and pos = ? and word = ?",
                                                                     (li.lemma_id, pos, we.word)))
                                    except StopIteration:
                                        raise ValueError(f"uanble to find match for {we.word} with pos '{pos}'")
                                    if li.action == 'remove':
                                        conn.execute("insert into to_remove(word_id) values (?)", (word_id,))
                                    conn.execute("insert into explicit(word_id) values (?)", (word_id,))
                            if li.action == 'remove':
                                conn.execute("insert or ignore into to_remove (word_id) select word_id from words "
                                             "where lemma_id = ?", (li.lemma_id,))
                            continue

                        if li.action == 'replace':
                            keepPosesStr = ','.join(f"'{pos}'" for pos in keepPoses)
                            posFilter = f"and pos not in ({keepPosesStr})" if keepPoses else ''

                            conn.execute("insert or ignore into to_remove (word_id) select word_id from words "
                                         f"where lemma_id = ? and lemma_id != word_id {posFilter}", (li.lemma_id,))
                            we = li.lemma
                            word_id = li.lemma_id
                            we._word_id = word_id
                            if we.entry_rank is not Default:
                                conn.execute("insert into new_entry_info values (?, ?, ?, ?)", (word_id, sg.id, group_id, we.entry_rank))

                        _addMissingSpellings(li.spellings, gi.spellings)

                        if li.action == 'adjust' or li.action == 'match':
                            for pos, wes in li.words.items():
                                for word_id, word in conn.execute("select word_id, word from words where lemma_id = ? and pos = ?",
                                                                  (li.lemma_id, pos)):
                                    we = next((we for we in wes if we.word == word), None)
                                    if we is None:
                                        if li.action == 'match':
                                            continue
                                        raise ValueError(f"unaccounted for words with pos '{pos}' within line", )
                                    we._word_id = word_id
                                    if we.entry_rank is not Default:
                                        conn.execute("insert into new_entry_info values (?, ?, ?, ?)", (word_id, sg.id, group_id, we.entry_rank))

                        if li.action in ('add'):
                            li.lemma_id = next_word_id

                        for pos, wes in li.words.items():
                            addMissingSpellings(wes, gi.spellings)
                            for we in wes:
                                #print(f"{sg.id} {li.lemma_id}: {we._word_id} {we.word}")
                                if not hasattr(we, '_word_id'):
                                  conn.execute("insert into new_words (word_id, main_group_id, lemma_id, pos, word, word_key, entry_rank) values (?, ?, ?, ?, ?, ?, ?)",
                                               (next_word_id, sg.id, li.lemma_id, pos, we.word, clusterKey(we.word).decode('ascii'),
                                                ifDefault(we.entry_rank,None)))
                                  we._word_id = next_word_id
                                  next_word_id += 1
                                if we.spellings:
                                    conn.executemany("insert into new_derived_variant_info values (?, ?, ?, ?, ?, ?)",
                                                     ((sg.id, li.lemma_id, pos, we._word_id, sp, vl) for sp, vl in we.spellings.items()))

                        if li.spellings:
                            haveLemmaSpelling = True
                            conn.executemany("insert into new_lemma_variant_info (main_group_id, lemma_id, spelling, variant_level) values (?, ?, ?, ?)",
                                             ((sg.id, li.lemma_id, sp, vl) for sp, vl in li.spellings.items()))
                        if li.comments:
                            conn.executemany("insert into new_lemma_comments (main_group_id, lemma_id, order_num, comment) values (?, ?, ?, ?)",
                                             ((sg.id, li.lemma_id, i, c) for (i, c) in enumerate(li.comments)))
                        elif replaceComments:
                            conn.execute("insert or ignore into new_lemma_comments (main_group_id, lemma_id, order_num) values (?, ?, -1)", (sg.id, li.lemma_id,))
                    except ValueError as err:
                        raise ValueError(f"failed to add line: {li.line}: {err}")

                for s in gi.adjScowlInfo:
                    if isinstance(s, ScowlInfoToClear):
                        conn.executemany("insert or replace into scowl_info_to_clear values (?, ?, ?, ?, ?)",
                                         ((si.size, si.category, si.region, tag,
                                           sg.id) for si in s.si for tag in si.tags))
                    if isinstance(s, ScowlLineInfo):
                        # fixme: should likely verify words
                        if s.expand:
                            conn.executemany("insert or replace into new_scowl_data values (?, ?, ?, ?, ?, '*', ?)",
                                             ((si.size, si.category, si.region, tag,
                                               sg.id, s.action == 'replace') for si in s.si for tag in si.tags))
                        else:
                            conn.executemany("insert or replace into new_scowl_data values (?, ?, ?, ?, ?, ?, ?)",
                                             ((si.size, si.category, si.region, tag,
                                               sg.id, pos, s.action == 'replace') for si in s.si for tag in si.tags for pos in s.words.keys()))
                    elif isinstance(s, ScowlOverrideLine):
                        # fixme: should likely verify words
                        conn.executemany("insert or replace into new_scowl_override values (?, ?, ?, ?, ?, ?, ?)",
                                         ((si.size, si.category, si.region, tag,
                                           sg.id, word, s.action == 'replace') for si in s.si for tag in si.tags for word in s.words))

                for size, category, region, tag in conn.execute(
                        "select size, category, region, tag "
                        "  from scowl_info_to_clear c "
                        "  cross join (select main_group_id, other_group_id as group_id from to_merge) m using (main_group_id) "
                        "  left join scowl_data d using (group_id, size, category, region, tag) "
                        "  where main_group_id = ? "
                        "  group by size, category, region, tag "
                        "  having count(d.group_id) == 0 ", (sg.id,)):
                    raise ValueError(f"unable to remove scowl info: {size} {category} {region} {tag}")

                conn.execute("insert into new_group_info (main_group_id, base_pos, defn_note, pos_class, usage_note, group_rank) values (?, ?, ?, ?, ?, ?)",
                             (sg.id, base_pos, gi.defn_note, gi.pos_class, gi.usage_note,
                              None if gi.group_rank is None else '' if gi.group_rank == '_' else gi.group_rank))

                if comment and comment.lines == ['']:
                   conn.execute("insert or replace into new_group_comments values (?, NULL)", (sg.id,))
                elif comment:
                    conn.execute("insert or replace into new_group_comments values (?, ?)", (sg.id, str(comment)))
                elif haveLemmaSpelling and replaceComments:
                    conn.execute("insert or ignore into new_group_comments values (?, NULL)", (sg.id,))

                if haveLemmaSpelling and strict:
                    unaccountedFor = [
                        *conn.execute("select word from words join to_merge on group_id = other_group_id "
                                      "where main_group_id = ? and word_id = lemma_id and word_id not in (select * from lemmas_accounted_for)",
                                      (sg.id,))]
                    if unaccountedFor:
                        raise ValueError(f"unaccounted lemmas: {', '.join(word for word, in unaccountedFor)}")

                conn.execute("drop table lemmas_accounted_for")
            except ValueError as err:
                warn(f"{err}: skipping group")
                conn.execute("rollback to sp")

            conn.execute("release savepoint sp")

    for cs in clusterComments:
        if cs.action == 'remove':
            conn.execute("insert into new_cluster_comments(headword) values (?)", (cs.headword,))

    if errors and not ignoreErrors:
        raise ValueError('aborting due to previous errors')

    t = time.monotonic()
    conn.executescript((_dir / 'adjust_proc.sql').read_text())

    res = conn.execute("select lemma, base_pos, defn_note from new_duplicate_lemmas").fetchall()
    if (res):
        raise ValueError("duplicate lemmas created: " + '; '.join(f"{lemma} <{base_pos}> {{{defn_note}}}" for lemma, base_pos, defn_note in res))

    if simplifyScowlInfo:
        conn.execute("delete from scowl_data"
                     "  where (size,category,region,tag,group_id,pos) "
                     "    in (select * from scowl_data_cleanup join group_ids_to_clean_up using (group_id))")
    print(f'adjust_proc.sql: {time.monotonic()-t}s')

    if preview:
        clusters = importFromDB(conn, filterQuery =
                                "with l as (select * from words join fuzzy using (word) where lemma_id = word_id) "
                                "  select b.group_id from use_info_from cross join l as a on main_group_id = a.group_id cross join l as b using (word_key) ")
        exportAsText(clusters, conn, sys.stdout, showExtraInfo = False)
        conn.rollback()
    else:
        conn.execute("delete from cluster_map")
        conn.commit()

    if not DEBUG_SQL:
        conn.executescript((_dir / 'adjust_cleanup.sql').read_text())
        conn.commit()
