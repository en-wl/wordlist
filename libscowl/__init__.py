from collections import namedtuple, defaultdict
from itertools import groupby
from types import SimpleNamespace
from pathlib import Path
import sys
import os
import sqlite3
import json
import re

# †

from ._common import *
from ._constdata import *

def _warn(msg):
    sys.stderr.write(f'warning: {msg}\n')

def ifNone(a, b):
    return b if a is None else a

_accented   = "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöøùúûüý"
_deaccented = "AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuy"
_orderAlpha = "aáàâåäãAÁÀÂÅÄÃæÆbBcçCÇdDðÐeéèêëEÉÈÊËfFgGhHiíìîïIÍÌÎÏjJkKlLmMnñNÑoóòôöõøOÓÒÔÖÕØpPqQrRsSßtTuúùûüUÚÙÛÜvVwWxXyýYÝzZþÞ"
_order = '0123456789' + _orderAlpha + ".&/'- "
_wordRegex = f"[{_orderAlpha}0-9.&'/](?:[{_orderAlpha}0-9.&'/ -]*[{_orderAlpha}0-9.&'/]|)"

# note: any character not in _order is not allowed to be part of a word

_deaccentMap = {}
for k, v in zip(_accented, _deaccented):
    _deaccentMap[k] = v

_sortOrder = bytearray(256)
for i, c in enumerate(_order.encode('iso-8859-1')):
    assert(_sortOrder[c] == 0)
    _sortOrder[c] = i + 1

_sortOrder0 = bytearray(256)
for c in _orderAlpha:
    _sortOrder0[ord(c)] = _sortOrder[ord(_deaccentMap.get(c,c).lower())]

for c in '0123456789':
    _sortOrder0[ord(c)] = _sortOrder[ord(c)]

_deaccent = str.maketrans(_accented, _deaccented)
def deaccent(w):
    return w.translate(_deaccent)

def wordOrderKey(w):
    w = w.encode('iso-8859-1')
    return (w.translate(_sortOrder0).translate(None, b'\0'), w.translate(_sortOrder))

wordPartRegex = re.compile(f'(\+?)({_wordRegex})([*@~!-]?)†?')

def parseWordPart(w):
    m = wordPartRegex.fullmatch(w)
    if not m:
        raise ValueError(f"invalid word part: {w}")
    return (0 if m[1] == '+' else None, m[2],m[3])

def posmap(base_pos, poses):
    poses = set(poses)
    if base_pos == 'n':
        if 'nsp' in poses:
            new_poses = ['n0', 'ns', 'np', 'nsp']
        elif 'np' in poses and 'ns' in poses:
            new_poses = ['n0', 'ns', 'np']
        elif 'np' in poses:
            new_poses = ['n0', 'np']
        elif 'ns' in poses:
            new_poses = ['n0', 'ns']
        else:
            new_poses = ['n0']
    elif base_pos == 'v':
        if not {'vd2', 'vs2', 'vs3', 'vs4'}.isdisjoint(poses):
            new_poses = ['v0', 'vd', 'vd2', 'vn', 'vg', 'vs', 'vs2', 'vs3', 'vs4']
        elif 'vn' in poses:
            new_poses = ['v0', 'vd', 'vn', 'vg', 'vs']
        elif not {'vd', 'vg', 'vs'}.isdisjoint(poses):
            new_poses = ['v0', 'vd', 'vg', 'vs']
        else:
            new_poses = ['v0']
    elif base_pos == 'n_v':
        if 'vn' in poses:
            new_poses = ['m0', 'vd', 'vn', 'vg', 'ms']
        elif poses != set('m0'):
            new_poses = ['m0', 'vd', 'vg', 'ms']
        else:
            new_poses = ['m0']
        if 'nsp' in poses:
            new_poses +=  ['np', 'nsp']
        elif 'np' in poses:
            new_poses += ['np']
    elif base_pos == 'm':
        if 'vn' in poses:
            new_poses = ['m0', 'vd', 'vn', 'vg', 'ms']
        elif not {'vd', 'vg', 'ms'}.isdisjoint(poses):
            new_poses = ['m0', 'vd', 'vg', 'ms']
        else:
            new_poses = ['m0']
    elif base_pos == 'aj':
        if 'aj1' in poses or 'aj2' in poses:
            new_poses = ['aj0', 'aj1', 'aj2']
        else:
            new_poses = ['aj0']
    elif base_pos == 'av':
        if 'av1' in poses or 'av2' in poses:
            new_poses = ['av0', 'av1', 'av2']
        else:
            new_poses = ['av0']
    elif base_pos == 'a' or base_pos == 'aj_av':
        if 'a1' in poses or 'a2' in poses:
            new_poses = ['a0', 'a1', 'a2']
        else:
            new_poses = ['a0']
    elif base_pos == 'we':
        if 'wep' in poses:
            new_poses = ['we', 'wep']
        else:
            new_poses = ['we']
    elif len(poses) == 1:
        new_poses = [*poses]
    else:
        raise ValueError(f'posmap: unrecognized pattern')
    leftover = poses - set(new_poses)
    if leftover:
        raise ValueError(f'posmap: leftover forms: {leftover}')
    return new_poses

def posesFromList(base_pos, words):
    poses = None
    if len(words) == 1:
        poses = [basePosInfo[base_pos].lemma_pos]
    elif base_pos == 'n':
        if len(words) == 4:
            poses = ['n0', 'ns', 'np', 'nsp']
        elif len(words) == 3:
            poses = ['n0', 'ns', 'np']
        elif len(words) == 2:
            if words[1] and words[1][0].word.endswith("'s"):
                poses = ['n0', 'np']
            else:
                poses = ['n0', 'ns']
    elif base_pos == 'v':
        if len(words) == 9:
            poses = ['v0', 'vd', 'vd2', 'vn', 'vg', 'vs', 'vs2', 'vs3', 'vs4']
        elif len(words) == 5:
            poses = ['v0', 'vd', 'vn', 'vg', 'vs']
        elif len(words) == 4:
            poses = ['v0', 'vd', 'vg', 'vs']
    elif base_pos == 'n_v':
        if len(words) == 7:
            poses = ['m0', 'vd', 'vn', 'vg', 'ms', 'np', 'nsp']
        if len(words) == 6:
            if words[-1] and words[-1][0].word.endswith("'s"):
                poses = ['m0', 'vd', 'vn', 'vg', 'ms', 'np']
            else:
                poses = ['m0', 'vd', 'vg', 'ms', 'np', 'nsp']
        if len(words) == 5:
            if words[-1] and words[-1][0].word.endswith("'s"):
                poses = ['m0', 'vd', 'vg', 'ms', 'np']
            else:
                poses = ['m0', 'vd', 'vn', 'vg', 'ms']
        if len(words) == 4:
            poses = ['m0', 'vd', 'vg', 'ms']
    elif base_pos == 'm':
        if len(words) == 5:
            poses = ['m0', 'vd', 'vn', 'vg', 'ms']
        elif len(words) == 4:
            poses = ['m0', 'vd', 'vg', 'ms']
    elif base_pos == 'aj':
        if len(words) == 3:
            poses = ['aj0', 'aj1', 'aj2']
    elif base_pos == 'av':
        if len(words) == 3:
            poses = ['av0', 'av1', 'av2']
    elif base_pos == 'a' or base_pos == 'aj_av':
        if len(words) == 3:
            poses = ['a0', 'a1', 'a2']
    elif base_pos == 'we':
        if len(words) == 2:
            poses = ['we', 'wep']
    return poses

_spellings_ab = ('A', 'B', 'Z', 'C', 'D')
_spellings = ('_', 'A', 'B', 'Z', 'C', 'D')

class Spellings(dict):

    def add(self, spelling, variant_level):
        if self.get(spelling, variant_level) != variant_level:
            raise ValueError(f"conflicting variant level for '{spelling}'")
        self[spelling] = variant_level
        if len(self) > 1 and '_' in self:
            raise ValueError("cannot mix '_' with other spellings type")

    def union(self, other):
        res = Spellings(self)
        for sp, vl in other.items():
            res.add(sp, vl)

    def __str__(self):
        return self.str()

    def str(self, exclude = None):
        if exclude is None:        
            exclude = ()
        parts = []
        for sp in _spellings:
            if sp in exclude: continue
            vl = self.get(sp, None)
            if vl is None: continue
            symbol = variantAsSymbol[vl]
            parts.append(f"{sp}{symbol}")
        return ' '.join(parts)

    def key(self):
        return tuple((sp, self[sp]) for sp in sorted(self.keys()))

    @staticmethod
    def parse(str_, lemmaSpellingsKeys = None):
        s = Spellings()
        for sp in str_.split():
            m = re.fullmatch(r'([_ABZCD]?)([^1-9]?)', sp)
            if not m:
                raise ValueError('unrecognized spelling string: {sp}')
            spelling = m[1]
            try:
                variant_level = variantFromSymbol[m[2]]
            except KeyError:
                raise ValueError(f"unknown variant symbol: '{m[2]}'")
            if spelling:
                s.add(spelling,variant_level)
            elif lemmaSpellingsKeys is None:
                raise ValueError('missing spelling symbol')
            else:
                for sp in lemmaSpellingsKeys:
                    s.add(sp,variant_level)
        if not s and lemmaSpellingsKeys:
            for sp in lemmaSpellingsKeys:
                s.add(sp,0)
        return s
            
    def sortKey(self):
        res = []
        for idx, sp in enumerate(_spellings):
            vl = self.get(sp, None)
            if vl is None: continue
            res.append(idx)
            res.append(vl)
        return res
    
class Cluster:
    __slots__ = ('groups', 'comments')

    def finalize(self):
        self.groups.sort(key = Group.sortKey)

class Data:
    __slots__ = ('clusters', 'notes', 'fixme')

def getRedundantSpellings(seq):
    tally = defaultdict(dict)
    for spellings, word in seq:
        for sp, vl in spellings.items():
            if sp == '_' or sp == '': continue
            tally[sp][vl] = word
    if tally:
        exclude = set()
        if tally.get('D', None) == tally.get('B', None):
            exclude.add('D')
        if tally.get('C', None) == tally.get('Z', None):
            exclude.add('C')
        if tally.get('Z', None) == tally.get('B', None):
            exclude.add('Z')
        if len(tally) != 5:
            missing = [sp for sp in _spellings_ab if sp not in tally]
        else:
            missing = []
        return (exclude, tally.keys())
    else:
        return (None, tally.keys())

def addMissingSpellings(entries, have = ()):
    have = set(have)
    for e in entries:
        sps = e.spellings
        if sps is None: continue
        for sp in sps.keys():
            if sp == '_' or sp == '': continue
            have.add(sp)
    for e in entries:
        sps = e.spellings
        if sps is None: continue
        if 'Z' not in have and 'Z' not in sps and 'B' in sps:
            sps['Z'] = sps['B']
        if 'C' not in have and 'C' not in sps and 'Z' in sps:
            sps['C'] = sps['Z']
        if 'D' not in have and 'D' not in sps and 'B' in sps:
            sps['D'] = sps['B']
    return have
    
class Group:
    __slots__ = (
        'headword',  # str
        'base_pos',  # str
        'defn_note', # str
        'usage_note',# str
        'pos_class', # str
        'lemma_rank',# str
        'entries',   # [ LemmaEntry ]
        'lines',     # [ Line ]
        'problems',  # [ str ]
        'comments',  # [ Comment ]
        '_group_id',
        '_redundantSpellings',
        '_lemmaIncluded',
    )

    def sortKey(self):
        l = self.lines[0]
        return (l.level + (100 if l.region != '' else 0) + (200 if l.category != '' else 0),
                wordOrderKey(self.headword), self.defn_note, basePosInfo[self.base_pos].order_num, self.pos_class)

    def finalize(self):
        self.entries.sort(key = LemmaEntry.sortKey)
        self.headword = self.entries[0].lemma

        for _, g in groupby(self.entries, lambda le: le.spellings):
            g = list(g)
            if len(g) <= 1:
                g[0]._num = 0
            else:
                for i, le in enumerate(g):
                    le._num = i + 1

        (self._redundantSpellings, tally) = getRedundantSpellings((le.spellings,le.lemma) for le in self.entries)

        self.problems = []
        if tally and len(tally) != len(_spellings_ab):
            missing = [sp for sp in _spellings_ab if sp not in tally]
            self.problems.append(f"missing spellings: {' '.join(missing)}");

        self.lines.sort(key = Line.sortKey)

        self._lemmaIncluded = False
        for l in self.lines:
            self._lemmaIncluded |= l.lemmaIncluded()

class LemmaEntry(SlotsDataClass):
    __slots__ = (
        'grp',       # Group -- back reference
        'spellings', # Spellings
        'lemma',     # str
        'words',     # { <pos>: [WordEntry] }
        'problems', 
        'comments',
        '_num'
    )

    def __init__(self):
        self.words = {}
        self.comments = []

    def sortKey(self):
        return (self.spellings.sortKey(), self.lemma)

    def finalize(self):
        self.problems = []
        missing = []
        unmarked = []
        for wes in self.words.values():
            if len(wes) == 1 and wes[0].spellings is None:
                continue
            for we in wes:
                if we.spellings is None and self.spellings:
                    we.spellings = Spellings((sp, 0) for sp in self.spellings.keys())
                elif we.spellings is None:
                    we.spellings = Spellings((('_', 0),))
            wes.sort(key = WordEntry.sortKey)
            tally_vl0 = {}
            for we in wes:
                for sp, vl in we.spellings.items():
                    if vl == 0:
                        tally_vl0[sp] = tally_vl0.get(sp, 0) + 1
                    else:
                        tally_vl0.setdefault(sp, 0)
            for sp, cnt in tally_vl0.items():
                if cnt == 0:
                    missing.extend(we.word for we in wes if we.word not in missing)
                elif cnt > 1 and not any(we.entry_rank == '*' for we in wes):
                    unmarked.extend(we.word for we in wes if we.spellings.get(sp, -1) == 0 and we.word not in unmarked)
        if missing:
            words = ', '.join(missing)
            self.problems.append(f"missing non-variants: {words}")
        if unmarked:
            words = ', '.join(unmarked)
            self.problems.append(f"unmarked variants: {words}")

class Line(SlotsDataClass):
    __slots__ = (
        'grp',      # Group -- back reference
        'level',    # int
        'category', # str
        'region',   # str
        'tag',      # str
        'poses'     # { <pos> } -- i.e. set of poses
    )

    def __init__(self, grp, level, category = '', region = '', tag = ''):
        self.grp = grp
        self.level = level
        self.category = category
        self.region = region
        self.tag = tag
        self.poses = set()

    def match(self, level, category, region, tag):
        return self.level == level and self.category == category and self.region == region and self.tag == tag

    def sortKey(self):
        return (self.level, self.category, self.region, self.tag)

    def lemmaIncluded(self):
        return basePosInfo[self.grp.base_pos].lemma_pos in self.poses

    def print(self, out = None, first = False, trimSpellings = True):
        if out is None:
            out = sys.stdout

        keyStr = f'{self.level}'
        if self.category != '': keyStr += f' {self.category}'
        if self.region != '': keyStr += f' {self.region}'
        if self.tag != '': keyStr += f' {self.tag}'

        base_pos = self.grp.base_pos
        lemma_pos = basePosInfo[base_pos].lemma_pos
        
        if lemma_pos in self.poses:
            assert(self.lemmaIncluded())
            lemmaIncluded = True
        else:
            assert(not self.lemmaIncluded())
            lemmaIncluded = False

        for le in self.grp.entries:
            out.write(keyStr)
            
            if le.spellings:
                exclude = self.grp._redundantSpellings if trimSpellings and self.grp._redundantSpellings is not None else ()
                out.write(f': {le.spellings.str(exclude)}')
                num = le._num
                if num != 0:
                    out.write(f' {{{num}}}')

            if lemmaIncluded:
                assert(len(le.words[lemma_pos]) == 1)
                out.write(f': {le.lemma}{self.grp.lemma_rank}')
            else:
                out.write(f': -')

            if self.grp.pos_class == '' and base_pos == '':
                pass
            elif self.grp.pos_class == '':
                out.write(f' <{base_pos}>')
            else:
                out.write(f' <{base_pos}/{self.grp.pos_class}>')
            if self.grp.defn_note != '':
                out.write(f' {{{self.grp.defn_note}}}')
            if self.grp.usage_note != '':
                out.write(f' ({self.grp.usage_note})')

            poses = posmap(base_pos, (pos for pos in self.poses if pos in le.words))

            wordEntries = []
            for pos in poses[1:]:
                w = le.words.get(pos,None) if pos in self.poses else None
                if w is None:
                    wordEntries.append('-')
                    continue
                if len(w) == 1 and w[0].spellings is None:
                    wordEntries.append(f'{w[0]}')
                    continue
                if trimSpellings:
                    spellingsStrs = []
                    for w0 in w:
                        if not ((not le.spellings and '_' in w0.spellings)
                                or w0.spellings.keys() == le.spellings.keys()):
                            spellingsStrs = None
                            break
                        vls = set(w0.spellings.values())
                        if len(vls) != 1:
                            spellingsStrs = None
                            break
                        vl = vls.pop()
                        if vl == 0:
                            spellingsStrs.append('')
                        else:
                            spellingsStrs.append(variantAsSymbol[vl])
                    if spellingsStrs is None:
                        (redundantSpellings, tally) = getRedundantSpellings((w0.spellings, w0.word) for w0 in w if w0.spellings is not None)
                        if redundantSpellings and self.grp._redundantSpellings is not None:
                            redundantSpellings &= self.grp._redundantSpellings
                        spellingsStrs = [w0.spellings.str(redundantSpellings) for w0 in w]
                else:
                    spellingsStrs = [w0.spellings.str() for w0 in w]
                strs = []
                if len(w) == 1:
                    strs = ['-']
                strs.extend(w0.str(sps) for w0,sps in zip(w,spellingsStrs))
                wordEntries.append('({})'.format(' | '.join(strs)))
            wordsStr = ', '.join(wordEntries)
            if wordsStr:
                out.write(f': {wordsStr}')

            if first:
                out.write(''.join(' #! ' + c for c in le.problems))
                out.write(''.join(' # ' + c for c in le.comments))
            
            out.write('\n')
                
    @staticmethod
    def parse(line, g, entriesBySpellings):
        line = line.strip()
        m = re.fullmatch(r'(?P<level>[0-9]+) (?P<tags>[^:#]*):\s*' 
                         r'(?: (?P<spellings>[^:<>{}#]+) (\{(?P<num> [0-9])\}\s*|):\s* |)'
                         r'(?P<lemma>[^:<>{}#()]+)'
                         r'(?: <(?P<base_pos>[^/]*) (?:/(?P<pos_class>.+)|)>\s* |)'
                         r'(?: {(?P<defn_note>.+)}\s* |)'
                         r'(?: \((?P<usage_note>[^:#|]+)\)\s* |)'
                         r'(?: : \s* (?P<words>[^#]+) |)'   
                         r'(?: \# (?P<comments>.*) |)'
                         ,       
                         line,
                         re.VERBOSE)
        if m is None:
            return None
        l = Line(g, int(m['level']))
        for tag in m['tags'].split():
            if tag in REGIONS:
                if l.region != '':
                    raise ValueError("duplicate regions")
                l.region = tag
            elif tag[0] == '[':
                if tag[-1] != ']':
                    raise ValueError(f"invalid tag: '{tag}'")
                if l.tag != '':
                    raise ValueError("duplicate tags")
                l.tag = tag
            else:
                if l.category != '':
                    raise ValueError("duplicate categories")
                l.category = tag
        def merge(attr, v):
            v = ifNone(v, '')
            if not hasattr(g, attr):
                setattr(g, attr, v)
            elif getattr(g, attr) != v:
                raise ValueError(f'conflicting values for {attr} with group')
        lemmaStr = m['lemma'].strip()
        if lemmaStr == '-':
            lemma = None
        else:
            (lemma_variant_override, lemma, lemma_rank) = parseWordPart(lemmaStr)
            merge('lemma_rank', lemma_rank)
        merge('base_pos', m['base_pos'])
        merge('pos_class', m['pos_class'])
        merge('defn_note', m['defn_note'])
        merge('usage_note', m['usage_note'])
        spellings = Spellings.parse(ifNone(m['spellings'], ''))
        spellingKey = (spellings.key(), m['num'])
        le = entriesBySpellings.get(spellingKey, None)
        if le is None:
            le = LemmaEntry()
            le.spellings = spellings
            entriesBySpellings[spellingKey] = le
        if m['words'] is None or m['words'] == '':
            wordStrs = []
        else:
            wordStrs = m['words'].split(',')
        if lemma is None:
            words = [[]]
        else:
            if not hasattr(le, 'lemma'):
                le.lemma = lemma
            elif le.lemma != lemma:
                raise ValueError(f"conflicting lemma entry for '{spellings}'")
            we = WordEntry()
            we.word = lemma
            we.entry_rank = ''
            words = [[we]]
        if spellings:
            lemmaSpellingsKeys = spellings.keys();
        else:
            lemmaSpellingsKeys = '_',
        for w in wordStrs:
            w = w.strip()
            m_ = re.fullmatch('\((.+)\)', w)
            if m_:
                wes = [we for we in (WordEntry.parse(w_.strip(), lemmaSpellingsKeys) for w_ in m_[1].split('|')) if we is not None]
            else:
                we = WordEntry.parse(w)
                wes = [] if we is None else [we]
            words.append(wes)
        poses = posesFromList(g.base_pos, words)
        if poses is None:
            raise ValueError(f"could not map list of words of length {len(words)} with base pos of '{base_pos}'")
        assert(len(words) == len(poses))
        for pos, wes in zip(poses, words):
            if not wes:
                continue
            l.poses.add(pos)
            # fixme? sort wes first
            if pos not in le.words:
                le.words[pos] = wes
            elif le.words[pos] != wes:
                raise ValueError(f"conflicting word entry for '{pos}' for '{spellings}': {le.words[pos]}, {wes}")
        if m['comments']:
            le.comments.extend(c.strip() for c in m['comments'].split('#') if not c.startswith('!'))
        return l

class Comment(SlotsDataClass):
    __slots__  = ('word', 'other_words', 'comment')

    def __init__(self, word, other_words, comment):
        self.word = word
        self.other_words = other_words
        self.comment = comment

    def print(self, out = None):
        out.write(f'## {self.word}')
        if self.other_words:
            out.write(f' ({self.other_words}):')
        else:
            out.write(f':');
        if self.singleLine:
            out.write(f' {self.comment}\n')
        else:
            out.write('\n')
            for line in self.comment.splitlines():
                out.write(f'## {line}\n')
            out.write('\n')

    @classmethod
    def parse(cls, first, *rest):
        m = re.fullmatch(r'\#\# \s* (.+?) \s* (\( (.*) \)|)  \s* : (.*)', first, re.VERBOSE)
        if not m:
            raise ValueError(f'invalid commit line: {first}')
        c = cls(m[1].strip(), ifNone(m[3], '').strip(), m[4].strip())
        if c.comment:
            lines = [c.comment]
        else:
            lines = []
        for l in rest:
            l = re.sub(r'^## ?','', l)
            lines.append(l)
        c.comment = '\n'.join(lines)
        return c

class GroupComment(Comment):
    __slots__ = ()
    singleLine = True

class ClusterComment(Comment):
    __slots__ = ()
    singleLine = False

class WordEntry(SlotsDataClass):
    __slots__ = (
        'spellings',      # Spellings
        'word',           # str
        'entry_rank',     # str
        'duplicate',      # bool
    )
    def __init__(self):
        self.spellings = None
    def __str__(self):
        return self.str()
    def sortKey(self):
        return ([] if self.spellings is None else self.spellings.sortKey(), self.word)
    def str(self, spellingsStr = None):
        parts = []
        if spellingsStr is None:
            if self.spellings:
                parts.append(self.spellings.str())
        else:
            if spellingsStr != '':
                parts.append(spellingsStr)
        duplicate = '†' if self.duplicate else ''
        parts.append(f"{self.word}{self.entry_rank}{duplicate}")
        return ': '.join(parts)
    @staticmethod
    def parse(wstr, lemmaSpellingsKeys = None):
        if wstr == '-':
            return None
        m = re.fullmatch(r'((.*):\s*|)(.+)', wstr)
        if m is None:
            raise ValueError(f'invalid word entry: {wstr}')
        we = WordEntry()
        if m[2] is None and lemmaSpellingsKeys is None:
            we.spellings = None
        elif m[2] is None:
            we.spellings = Spellings((sp, 0) for sp in lemmaSpellingsKeys)
        else:
            we.spellings = Spellings.parse(m[2], lemmaSpellingsKeys)
        (variant_override, we.word, we.entry_rank) = parseWordPart(m[3])
        we.duplicate = False
        return we
    def __eq__(self, other):
        if not isinstance(other, WordEntry):
            return NotImplemented
        return self.spellings == other.spellings and self.word == other.word and self.entry_rank == other.entry_rank

def createClusters(groups, clusterComments):
    
    groupsByHeadword = defaultdict(list)
    clusterMapping = {}
    for grp in groups:
        if not grp.lines: continue
        grp.finalize()
        groupsByHeadword[grp.headword].append(grp)
        members = set()
        for le in grp.entries:
            le.finalize()
            w = le.lemma
            try:
                members |= clusterMapping[w]
            except KeyError:
                members.add(w)
        for w in members:
            clusterMapping[w] = members

    clusters = []
    while groupsByHeadword:
        cls = Cluster()
        (headword,cls.groups) = groupsByHeadword.popitem()
        cls.comments = []
        others = clusterMapping[headword]
        for w in others:
            try:
                cls.groups += groupsByHeadword.pop(w)
            except KeyError:
                pass
            try:
                cls.comments.append(clusterComments.pop(w))
            except KeyError:
                pass
        cls.finalize()
        clusters.append(cls)

    if clusterComments:
        _warn('unused cluster comments: {}'.format(', '.join(map(str, clusterComments.keys()))))

    clusters.sort(key = lambda c: wordOrderKey(c.groups[0].headword))

    return clusters


def _dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

_dir = Path(__file__).parent.resolve()
    
def openDB(dbfile, create = False):

    if not dbfile:
        raise ValueError

    if dbfile == ':memory:':
        create = True
    elif os.path.exists(dbfile):
        if create is True:
            raise FileExistsError(dbfile)
        create = False
    else: # file doesn't exist
        if create is False:
            raise FileNotFoundError(dbfile)
        create = True

    conn = sqlite3.connect(dbfile)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON");
    conn.execute("PRAGMA synchronous = OFF");

    if create:
        conn.executescript((_dir / 'schema.sql').read_text())
        conn.executescript((_dir / 'constdata.sql').read_text())
        conn.executescript((_dir / 'views.sql').read_text())
    
    return conn

def importFromDB(conn):
    words = {}

    cur = conn.cursor()
    #cur.row_factory = _dict_factory

    groups = {}
    for r in cur.execute('select * from groups'):
        grp = Group()
        grp.base_pos = r['base_pos']
        grp.defn_note = r['defn_note']
        grp.usage_note = r['usage_note']
        grp.pos_class = r['pos_class']
        grp.lemma_rank = r['lemma_rank']
        grp._group_id = r['group_id']
        grp.entries = []
        grp.lines = []
        grp.comments = []
        groups[r['group_id']] = grp

    for r in cur.execute('select * from group_comments'):
        groups[r['group_id']].comments.append(GroupComment(r['word'], r['other_words'], r['comment']))

    wordsById = {}
    lemmasById = {}

    for r in cur.execute("select * from lemma_variant_info"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute("select * from derived_variant_info"):
        word_id = r['word_id']
        we = wordsById.get(word_id)
        if we is None:
            wordsById[word_id] = we = WordEntry()
            we.spellings = Spellings()
        we.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute("select * from lemma_comments order by lemma_id, order_num"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.comments.append(r['comment'])

    duplicates = set(word for word, in cur.execute("select word from duplicate_derived"))

    lemma_id = -1
    le = None
    for r in cur.execute('select * from words order by lemma_id'):
        grp = groups[r['group_id']]
        if r['lemma_id'] != lemma_id:
            lemma_id = r['lemma_id']
            le = lemmasById.pop(lemma_id, None)
            if le is None:
                le = LemmaEntry()
                le.spellings = Spellings()
            le.grp = grp
            grp.entries.append(le)
        word_id = r['word_id']
        we = wordsById.pop(word_id, None)
        if we is None:
            we = WordEntry()
        we.word = r['word']
        we.entry_rank = r['entry_rank']
        we.duplicate = we.word in duplicates
        le.words.setdefault(r['pos'], []).append(we)
        if r['word_id'] == lemma_id:
            le.lemma = r['word']

    for r in cur.execute('select * from scowl_data order by group_id, level, category, region, tag, pos'):
        grp = groups[r['group_id']]
        level = r['level']
        category = r['category']
        region = r['region']
        tag = r['tag']
        if not grp.lines or not grp.lines[-1].match(level, category, region, tag):
            grp.lines.append(Line(grp, level, category, region, tag))
        l = grp.lines[-1]
        l.poses.add(r['pos'])

    clusterComments = {}
    for r in cur.execute("select * from cluster_comments"):
        clusterComments[r['headword']] = ClusterComment(r['headword'], r['other_words'], r['comment'])

    for k in list(clusterComments.keys()):
        c = clusterComments[k]
        m = re.match(r'^see note( for | )"?([\w]+)"?', c.comment, re.IGNORECASE)
        if m:
            other = clusterComments['Koran' if m[2] == 'Quran' else m[2]]
            other.other_words += f' {c.word} {c.other_words}'
            del clusterComments[k]

    return createClusters(groups.values(), clusterComments)

def exportToDB(clusters, conn):
    group_id = 1
    word_id = 1

    conn.execute("delete from scowl_data")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from group_comments")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from derived_variant_info")
    conn.execute("delete from lemma_variant_info")
    conn.execute("delete from words")
    conn.execute("delete from groups")
    
    for cluster in clusters:
        conn.execute("insert into clusters (cluster_id) values (?)", (group_id,))

        for group in cluster.groups:
            conn.execute("insert into groups (group_id, base_pos, pos_class, defn_note, usage_note, lemma_rank) values (?, ?, ?, ?, ?, ?)",
                         (group_id, group.base_pos, group.pos_class, group.defn_note, group.usage_note, group.lemma_rank))

            for le in group.entries:
                lemma_id = word_id
                for pos in posmap(group.base_pos, le.words.keys()):
                    for we in le.words.get(pos, []):
                        conn.execute("insert into words (word_id, group_id, lemma_id, pos, word, entry_rank) values (?, ?, ?, ?, ?, ?)",
                                     (word_id, group_id, lemma_id, pos, we.word, we.entry_rank))
                        if we.spellings is not None and '' in we.spellings:
                            variant_level = we.spellings['']
                            spellings = le.spellings.keys() if le.spellings else ['_']
                            conn.executemany("insert into derived_variant_info (word_id, lemma_id, spelling, variant_level) values (?, ?, ?, ?)",
                                             ((word_id, lemma_id, sp, variant_level) for sp in spellings))
                        elif we.spellings is not None:
                            conn.executemany("insert into derived_variant_info (word_id, lemma_id, spelling, variant_level) values (?, ?, ?, ?)",
                                             ((word_id, lemma_id, sp, vl) for sp, vl in we.spellings.items()))
                        word_id += 1

                conn.executemany("insert into lemma_variant_info (lemma_id, spelling, variant_level) values (?, ?, ?)",
                                 ((lemma_id, sp, vl) for sp, vl in le.spellings.items()))
                    
                conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                                 ((lemma_id, i, c) for i, c in enumerate(le.comments)))
                                     
            for l in group.lines:
                for pos in l.poses:
                    conn.execute("insert into scowl_data (level, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                                 (l.level, l.category, l.region, l.tag, group_id, pos))

            for c in group.comments:
                conn.execute("insert into group_comments (group_id, word, other_words, comment) values (?, ?, ?, ?)",
                             (group_id, c.word, c.other_words, c.comment))

            group_id += 2 if group.base_pos in ('n_v', 'aj_av') else 1

                
        for c in cluster.comments:
            conn.execute("insert into cluster_comments (headword, other_words, comment) values (?, ?, ?)",
                         (c.word, c.other_words, c.comment))

    conn.execute("analyze")

    conn.execute("insert into pos_classes select distinct pos_class from groups order by pos_class");

    conn.execute("insert into usage_notes select distinct usage_note from groups order by usage_note");

    conn.execute("insert into categories select distinct category from scowl_data data order by category");

    conn.execute("insert into tags select distinct tag from scowl_data data order by category");
    
    conn.commit()

def exportAsText(clusters, conn = None, out = None, trimSpellings = True):
    if out is None:
        out = sys.stdout

    for cluster in clusters:

        for group in cluster.groups:

            first = True
            for line in group.lines:
                try:
                    line.print(out, first, trimSpellings)
                except ValueError as err:
                    _warn(f'skipping line: {line.grp.headword}: {line.poses}: {err}')
                first = False

            if not group._lemmaIncluded:
                l = Line(group, 99)
                l.poses.add(basePosInfo[group.base_pos].lemma_pos)
                l.print(out, False, trimSpellings)

            for c in group.problems:
                out.write(f"#! {c}\n")
            for c in group.comments:
                c.print(out)
            out.write('\n')

        for c in cluster.comments:
            c.print(out)

    if conn:
        out.write('#: Part of Speech Codes:\n')
        for pos, descr, extra_info in conn.execute("select base_pos, descr, extra_info from base_poses where base_pos != '' order by order_num"):
            out.write(f"#:   {pos}: {descr}\n")
        out.write("#:\n")
        out.write('#: Part of Speech Classes:\n')
        for pos_class, in conn.execute("select pos_class from pos_classes where pos_class != '' order by pos_class"):
            out.write(f"#:   {pos_class}\n")
        out.write("#:\n")
        out.write('#: Annotations:\n')
        for symbol, descr in conn.execute("select rank_symbol, rank_descr from ranks where rank_symbol != '' order by order_num"):
            out.write(f"#:   {symbol}: {descr}\n")
        out.write('#:   †: ambiguous lemma\n')
        out.write("#:\n")
        out.write('#: Spelling/Region Codes:\n')
        for spelling, region, descr in conn.execute("select spelling, region, spelling_descr from spellings where spelling != '_' order by order_num"):
            out.write(f"#:   {spelling}: {region}: {descr}\n")
        out.write(f"#:   _:     Other\n")
        out.write('#:\n')
        out.write('#: Variant Levels:\n')
        for symbol, descr in conn.execute("select variant_symbol, variant_descr from variant_levels where variant_symbol != '' order by variant_level"):
            out.write(f"#:   {symbol}: {descr}\n")
        out.write('#:\n')
        out.write('#: Usage Notes:\n')
        for usage_note, in conn.execute("select usage_note from usage_notes where usage_note != '' order by usage_note"):
            out.write(f'#:   {usage_note}\n')
        out.write('#:\n')
        out.write('#: Categories:\n')
        for category, in conn.execute("select category from categories where category != ''order by category"):
            out.write(f'#:   {category}\n')
        out.write('#:\n')
        out.write('#: Tags:\n')
        for tag, in conn.execute("select tag from tags where tag != '' order by tag"):
            out.write(f'#:   {tag}\n')

def importText(f = None):
    if f is None:
        f = sys.stdin

    groups = []
    clusterComments = {}
    
    grp = None
    lines = defaultdict(set)
    entriesBySpellings = {}
    commentLines = []
    for lineStr in f:
        lineStr = lineStr.strip()
        if lineStr == '':
            if lines:
                grp.lines = []
                for (level, category, region, tag), poses in lines.items():
                    l = Line(grp, level, category, region, tag)
                    l.poses = poses
                    grp.lines.append(l)
                grp.entries = list(entriesBySpellings.values())
                have = addMissingSpellings(grp.entries)
                for le in grp.entries:
                    for wes in le.words.values():
                        addMissingSpellings(wes, have)
                groups.append(grp)
                for cl in commentLines:
                    grp.comments.append(GroupComment.parse(cl))
            elif commentLines:
                c = ClusterComment.parse(*commentLines)
                clusterComments[c.word] = c
            grp = None
            lines.clear()
            entriesBySpellings.clear()
            commentLines.clear()
            continue
        
        if grp is None:
            grp = Group()
            grp.comments = []
        try:
            l = Line.parse(lineStr, grp, entriesBySpellings)
        except ValueError as err:
            raise ValueError(f'invalid line: {lineStr}') from err
        
        if l is None:
            if lineStr.startswith('##'):
                commentLines.append(lineStr)
                continue
            elif lineStr.startswith('#!') or lineStr.startswith('#:'):
                continue

        if l is None:
            raise ValueError(f'invalid line: {lineStr}')

        if l.level < 99:
            key = (l.level, l.category, l.region, l.tag)
            lines[key].update(l.poses)

    #fixme handle last element
    #if grp and grp.lines:
    #    groups.append(grp)

    return createClusters(groups, clusterComments)

class SetFilter(set):
    def __init__(self, *members, noDefault = False):
        super().__init__(members)
        if noDefault:
            self._excludeDefault = True
    def _copy(self, newMembers):
        other = self.__class__(*newMembers)
        if hasattr(self, '_excludeDefault'):
            other._excludeDefault = True
        return other

class Include (SetFilter):
    pass

class Exclude (SetFilter):
    pass

def queryString(
        *,
        size = 60,
        spellings = ('A',),
        regions = None,
        variantLevel = '.',
        poses = None,
        posClasses = None,
        posCategories = None,
        categories = None,
        tags = None,
        usageNotes = None,
):
    clauses = []
    if size is not None:
        size = int(size)
        if size < 0 or size > 99:
            raise ValueError(size)
        clauses.append(f"level <= {size}")

    if variantLevel is not None:
        vl = variantFromSymbol[variantLevel]
        clauses.append(f"variant_level <= {vl}")

    def addSetQueryClause(var, check, default, members):
        if members is None:
            return
        for member in members:
            if not check(member):
                raise ValueError(member)
        if isinstance(members, Exclude):
            if not members:
                raise ValueError
            clauses.append("{} not in ({})".format(var,
                                                   ','.join(f"'{v}'" for v in set(members))))
        else:
            m = set(members)
            if default is not None and not getattr(members, '_excludeDefault', False):
                m.add(default)
            if not m:
                raise ValueError
            clauses.append("{} in ({})".format(var,
                                               ','.join(f"'{v}'" for v in m)))

    addSetQueryClause('spelling', lambda sp: sp in SPELLINGS, '_', spellings)

    if regions is None and spellings is not None:
        regions = [spellingInfo[sp].region for sp in spellings]

    addSetQueryClause('region', lambda r: r in REGIONS, '', regions)

    if poses:
        if not isinstance(poses, SetFilter):
            poses = Include(*poses)
        basePoses = poses._copy(poses & basePosInfo.keys())
        poses.difference_update(basePosInfo.keys())
        wordPoses = poses._copy(poses & posInfo.keys())
        poses.difference_update(posInfo.keys())
        for p in poses:
            raise ValueError(p)
        if basePoses:
            addSetQueryClause('base_pos', lambda _: True, None, basePoses)
        if wordPoses:
            addSetQueryClause('pos', lambda _: True, None, wordPoses)
            
    elif poses is not None:
        raise ValueError("poses can't be empty")

    addSetQueryClause('pos_class', lambda _: True, '', posClasses)

    validPosCategories = set(p.category for p in basePosInfo.values())
    addSetQueryClause('pos_category', lambda p: p in validPosCategories, '', posCategories)

    addSetQueryClause('category', lambda _: True, '', categories)

    addSetQueryClause('tag', lambda _: True, '', tags)

    addSetQueryClause('usage_note', lambda _: True, '', usageNotes)

    return (
        "select distinct word",
        "from scowl_v0",
        "where {}".format(' and '.join(clauses)),
    )

def wordFilterRegEx(
        *,
        space = False,
        hyphen  = False,
        dot = 'strip',
        digits = False,
        special = False,
        apostrophe = 'middle',
):
        charSet = ''.join([_orderAlpha,
                           '0-9' if digits else '',
                           '.' if dot is True else '',
                           "'" if apostrophe is True else '',
                           '&/' if special else '',
                           ' ' if space else '',
                           '-' if hyphen else ''])
        charSetMiddle = ''.join(["'" if apostrophe == 'middle' else '',
                                 charSet])
        return ''.join([f"([{charSet}](?:[{charSetMiddle}]*[{charSet}]|))",
                        r'\.?' if dot == 'strip' else ''])

def getWords(conn, *, deaccent = False, useWordFilter = True, **args):
    """Returns a generator of words based on the arguments.

    Many arguments can filter by either including or excluding a set of
    values.  If the argument is a sequence then it will included the given
    along with the default value.  To not include the default use the Include
    class with the the noDefault parater set to True.  To exclude values
    instead, use the Exclude class.  A value of None means to not filter based
    on that argument.

    """
    queryArgs = {p.name: args.pop(p.name, p.default) for p in signature(queryString).parameters.values()}
    query = ' '.join(queryString(**queryArgs))
    print(query, file=sys.stderr)

    filterArgs = {p.name: args.pop(p.name, p.default) for p in signature(wordFilterRegEx).parameters.values()}
    if useWordFilter:
        wordFilter = re.compile(wordFilterRegEx(**filterArgs))
        print(wordFilter.pattern, file=sys.stderr)

    if args:
        raise TypeError("unexpected args: {}".format(', '.join(args.keys())))

    if deaccent:
        deaccent = globals()['deaccent']
    else:
        deaccent = None

    for w, in conn.execute(query):
        if useWordFilter:
            m = wordFilter.fullmatch(w)
            if not m:
                continue
            w = m[1]
        if deaccent:
            w = deaccent(w)
        yield w

import inspect
from inspect import signature,Signature,Parameter

getWords.__signature__ = Signature([
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD),
    *signature(queryString).parameters.values(),
    *signature(wordFilterRegEx).parameters.values(),
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.KEYWORD_ONLY),
])

