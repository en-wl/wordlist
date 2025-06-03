from collections import namedtuple, defaultdict
from itertools import groupby, chain
from types import SimpleNamespace
from typing import NamedTuple,Any
from pathlib import Path
import sys
import os
import sqlite3
import json
import re
import copy

# †

from ._common import *
from ._constdata import *

def _warn(msg):
    sys.stderr.write(f'warning: {msg}\n')

def ifNone(a, b):
    return b if a is None else a

def noneIf(a, b):
    return None if a == b else a

# Default is a speical value to indicate that a value has not been provided in
# the text input.
class DefaultType:
    __slots__ = ()
    def __new__(cls):
        return Default
    def __bool__(self):
        return False
    def __str__(self):
        return ''
    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return ''
        else:
            raise LookupError(protocol)
    def __repr__(self):
        return "Default"
    def __lt__(self, other):
        if isinstance(other, DefaultType):
            return False
        elif isinstance(other, str):
            return True
        return NotImplemented
    def __le__(self, other):
        if isinstance(other, DefaultType):
            return True
        elif isinstance(other, str):
            return True
        return NotImplemented
    def __gt__(self, other):
        if isinstance(other, DefaultType):
            return False
        elif isinstance(other, str):
            return False
        return NotImplemented
    def __ge__(self, other):
        if isinstance(other, DefaultType):
            return True
        elif isinstance(other, str):
            return False
        return NotImplemented

Default = object.__new__(DefaultType)

def ifDefault(a, b):
    return b if a is Default else a

def defaultIf(a, b):
    return Default if a == b else a

_accented   = "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöøùúûüý"
_deaccented = "AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuy"
_orderAlpha = "aáàâåäãAÁÀÂÅÄÃæÆbBcçCÇdDðÐeéèêëEÉÈÊËfFgGhHiíìîïIÍÌÎÏjJkKlLmMnñNÑoóòôöõøOÓÒÔÖÕØpPqQrRsSßtTuúùûüUÚÙÛÜvVwWxXyýYÝzZþÞ"
_order = '0123456789' + _orderAlpha + ".&/'- "
_wordRegex = rf"[{_orderAlpha}0-9.&'/](?:[{_orderAlpha}0-9.&'/ -]*[{_orderAlpha}0-9.&'/]|)"

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

_clusterKey = bytearray(256)
for c in _orderAlpha:
    _clusterKey[ord(c)] = ord(_deaccentMap.get(c,c).lower())
for c in '0123456789':
    _clusterKey[ord(c)] = ord(c)
def clusterKey(w):
    w = w.encode('iso-8859-1')
    return w.translate(_clusterKey).translate(None, b'\0')

def wordOrderKey(w):
    w = w.encode('iso-8859-1')
    return (w.translate(_sortOrder0).translate(None, b'\0'), w.translate(_sortOrder))

def validateWord(w):
    m = re.fullmatch(_wordRegex, w)
    if not m:
        raise ValueError(f"invalid word: {w}")

wordPartRegex = re.compile(rf'({_wordRegex})([_*@~!-]?)†?')

class WordPart(NamedTuple):
    word: Any
    rank: Any

def _fixRank(rank):
    if rank == '':
        return Default
    elif rank == '_':
        return ''
    else:
        return rank

def parseWordPart(w):
    m = wordPartRegex.fullmatch(w)
    if not m:
        raise ValueError(f"invalid word part: {w}")
    return WordPart(m[1], _fixRank(m[2]))

class LemmaPart(NamedTuple):
    lemma_rank: Any
    lemma: Any
    entry_rank: Any

def parseLemmaPart(w):
    lemma_rank = Default
    if w[0] in '_@!-':
        lemma_rank = _fixRank(w[0])
        w = w[1:]
    return LemmaPart(lemma_rank, *parseWordPart(w))

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
    elif base_pos == 'pl':
        if 'nssp' in poses:
            new_poses = ['ns', 'nss', 'nsp', 'nssp']
        elif 'nsp' in poses and 'nss' in poses:
            new_poses = ['ns', 'nss', 'nsp']
        elif 'nsp' in poses:
            new_poses = ['ns', 'nsp']
        elif 'nss' in poses:
            new_poses = ['ns', 'nss']
        else:
            new_poses = ['ns']
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
    elif base_pos == 'pn':
        if 'pnrs' in poses:
            new_poses = ['pn0', 'pn1', 'pns', 'pnd', 'pnp', 'pnr0', 'pnrs']
        elif 'pnr0' in poses:
            new_poses = ['pn0', 'pn1', 'pns', 'pnd', 'pnp', 'pnr0']
        elif 'pnp' in poses or 'pnd' in poses:
            new_poses = ['pn0', 'pn1', 'pns', 'pnd', 'pnp']
        elif 'pns' in poses:
            new_poses = ['pn0', 'pn1', 'pns']
        elif 'pn1' in poses:
            new_poses = ['pn0', 'pn1']
        else:
            new_poses = ['pn0']
    elif base_pos == 'd':
        if 'ds' in poses:
            new_poses = ['d', 'ds']
        elif 'd1' in poses or 'd2' in poses:
            new_poses = ['d', 'd1', 'd2']
        else:
            new_poses = ['d']
    elif base_pos == 'we':
        if 'wep' in poses:
            new_poses = ['we', 'wep']
        else:
            new_poses = ['we']
    elif len(poses) <= 1:
        new_poses = [basePosInfo[base_pos].lemma_pos]
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
    elif base_pos == 'n':
        if len(words) == 4:
            poses = ['ns', 'nss', 'nsp', 'nssp']
        elif len(words) == 3:
            poses = ['ns', 'nss', 'nsp']
        elif len(words) == 2:
            if words[1] and words[1][0].word.endswith("'s"):
                poses = ['ns', 'nsp']
            else:
                poses = ['ns', 'nss']
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
    elif base_pos == 'pn':
        poses = ['pn0', 'pn1', 'pns', 'pnd', 'pnp', 'pnr0', 'pnrs'][0:len(words)]
    elif base_pos == 'd':
        if len(words) == 2:
            poses = ['d', 'ds']
        elif len(words) == 3:
            poses = ['d', 'd1', 'd2']
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
        if str_ is None:
            return None
        s = Spellings()
        for sp in str_.split():
            m = re.fullmatch(r'([_ABZCD]?)([^1-9]?)', sp)
            if not m:
                raise ValueError(f'unrecognized spelling string: {sp}')
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
        return (exclude, tally.keys())
    else:
        return (None, tally.keys())

def _addMissingSpellings(sps, have):
    if sps is None: return
    if 'Z' not in have and 'Z' not in sps and 'B' in sps:
        sps['Z'] = sps['B']
    if 'C' not in have and 'C' not in sps and 'Z' in sps:
        sps['C'] = sps['Z']
    if 'D' not in have and 'D' not in sps and 'B' in sps:
        sps['D'] = sps['B']

def addMissingSpellings(entries, have = ()):
    have = set(have)
    for e in entries:
        sps = e.spellings
        if sps is None: continue
        for sp in sps.keys():
            if sp == '_' or sp == '': continue
            have.add(sp)
    for e in entries:
        _addMissingSpellings(e.spellings, have)
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
        'override',  # { lemma: Override }
        'problems',  # [ str ]
        'commentLines', # GroupComment
        '_group_id',
        '_redundantSpellings',
        '_lemmaIncluded',
    )

    def merge(self, attr, v, allowDefault = True):
        v = ifNone(v, Default)
        v0 = getattr(self, attr, None)
        if v0 is None or (allowDefault and v0 is Default):
            setattr(self, attr, v)
        elif v != v0:
            raise ValueError(f'conflicting values for {attr} within group')

    def adjDefault(self, attr, v):
        if getattr(self, attr, Default) is Default:
            setattr(self, attr, v)

    def sortKey(self):
        l = self.lines[0]
        si = l.si[0]
        return (si.level + (100 if si.region != '' else 0) + (200 if si.category != '' else 0),
                wordOrderKey(self.headword), self.defn_note, basePosInfo[self.base_pos].order_num, self.pos_class)

    def finalize(self, expected_spellings):
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
        if tally and len(tally) != len(expected_spellings):
            missing = [sp for sp in expected_spellings if sp not in tally]
            self.problems.append(f"missing spellings: {' '.join(missing)}");

        self.lines.sort(key = Line.sortKey)

        self._lemmaIncluded = False
        for l in self.lines:
            self._lemmaIncluded |= l.lemmaIncluded()

        for lemma, ov in self.override.items():
            try:
                le = next(le for le in self.entries if le.lemma == lemma)
                notfound = set(ov.words) - { we.word for we in chain.from_iterable(le.words.values()) }
                if notfound:
                    raise ValueError(f"\"{ov}\": unable to find: {', '.join(sorted(notfound))}")
            except StopIteration:
                raise ValueError(f"\"{ov}\": unable to find lemma: {lemma}")

class LemmaEntry(SlotsDataClass):
    __slots__ = (
        'grp',       # Group -- back reference
        'spellings', # Spellings
        'lemma',     # str
        'words',     # { <pos>: [WordEntry] }
        'problems', 
        'comments',
        '_num',
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
                if self.spellings:
                    extra = sorted(we.spellings.keys() - self.spellings.keys())
                    if extra:
                        self.problems.append(f"{we.word}: extra spellings: {' '.join(extra)}")
                    
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

class Tags(SlotsDataClass):
    __slots__ = ('data',)

    def __init__(self, *args):
        self.data = set(*args)
        if len(self.data) == 1 and '' in self.data:
            self.data.remove('')

    def add(self, item):
        return self.data.add(item)

    def print(self, out):
        for tag in sorted(self.data):
            if tag == '':
                tag = '[]'
            out.write(f' {tag}')

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        if self.data:
            return self.data.__iter__()
        else:
            return ('',).__iter__()

    def __len__(self):
        length = self.data.__len__()
        return 1 if length == 1 else length


class ScowlInfo(SlotsDataClass):
    __slots__ = (
        'level',    # int
        'category', # str
        'region',   # str
        'tags',     # Tags
    )
    def __init__(self, level, category = '', region = '', tags = None):
        self.level = level
        self.category = category
        self.region = region
        if tags is None:
            self.tags = Tags()
        else:
            self.tags = Tags(tags)

    @staticmethod
    def parse(tagsStr):
        sil = []
        tags = tagsStr.split()
        tags_len = len(tags)
        idx = 0
        while idx < tags_len:
            si = ScowlInfo(int(tags[idx]))
            idx += 1
            while idx < tags_len:
                tag = tags[idx]
                if tag[0] in '0123456789':
                    break
                if tag in REGIONS:
                    if si.region != '':
                        raise ValueError("duplicate regions")
                    si.region = tag
                elif tag[0] == '[':
                    if tag[-1] != ']':
                        raise ValueError(f"invalid tag: '{tag}'")
                    if tag == '[]':
                        si.tags.add('')
                    else:
                        si.tags.add(tag)
                else:
                    if si.category != '':
                        raise ValueError("duplicate categories")
                    si.category = tag
                idx += 1
            sil.append(si)
        return sil

    def print(self, out):
        out.write(f'{self.level}')
        if self.category != '': out.write(f' {self.category}')
        if self.region != '': out.write(f' {self.region}')
        self.tags.print(out)

class LineBase(SlotsDataClass):
    __slots__ = (
        'grp',      # Group -- back reference
        'si',       # [ScowlInfo]
    )

    def __init__(self, grp, si):
        self.grp = grp
        self.si = si
    def __str__(self):
        from io import StringIO
        buf = StringIO()
        self.print(buf)
        return buf.getvalue().rstrip()

    def _lemmaPart(self, out, lemma, entry_rank = Default):
        base_pos = defaultIf(self.grp.base_pos, '')
        pos_class = defaultIf(self.grp.pos_class, '')
        defn_note = defaultIf(self.grp.defn_note, '')
        usage_note = defaultIf(self.grp.usage_note, '')
        
        if lemma:
            out.write(f': {self.grp.lemma_rank}{lemma}{entry_rank}')
        else:
            out.write(f': -')

        if base_pos is Default and pos_class is Default:
            pass
        elif pos_class is Default:
            out.write(f' <{base_pos}>')
        else:
            out.write(f' <{base_pos}/{self.grp.pos_class}>')
        if defn_note is not Default:
            out.write(f' {{{self.grp.defn_note}}}')
        if usage_note is not Default:
            out.write(f' ({self.grp.usage_note})')

    @staticmethod
    def parse(line, g, entriesBySpellings):
        m = _matchLine(line)
        if m is None:
            return None
        si = ScowlInfo.parse(ifNone(m['tags'], ''))
        if not si:
            raise ValueError('size must be provided')
        if m['override'] is None:
            l = Line(g, si)
        else:
            l = Override(g, si)
        lemmaStr = m['lemma'].strip()
        if lemmaStr == '-':
            lemma = None
        else:
            lemma = WordEntry()
            (lemma_rank, lemma.word, lemma.entry_rank) = parseLemmaPart(lemmaStr)
            g.merge('lemma_rank', lemma_rank, allowDefault = False)
        g.merge('base_pos', ifNone(m['base_pos'],''))
        g.merge('pos_class', m['pos_class'])
        g.merge('defn_note', m['defn_note'])
        g.merge('usage_note', m['usage_note'])
        l.finishParse(g, lemma, m, entriesBySpellings)
        return l

def _matchLine(line):
    line = line.strip()
    m = re.fullmatch(r'(?: (?P<tags>[0-9]+ [^:#]*):\s* |)'
                     r'(?: (?P<override>\+)\s*:\s* | (?P<spellings>[^:<>{}#]+) (\{(?P<num> [0-9])\}\s*|):\s* |)'
                     r'(?P<lemma>[^:<>{}#()]+)'
                     r'(?: <(?P<base_pos>[^/]*) (?:/(?P<pos_class>.*)|)>\s* |)'
                     r'(?: {(?P<defn_note>.+)}\s* |)'
                     r'(?: \((?P<usage_note>[^:#|]+)\)\s* |)'
                     r'(?: : \s* (?P<words>[^#]+) |)'   
                     r'(?: \# (?P<comments>.*) |)'
                     ,       
                     line,
                     re.VERBOSE)
    return m

def _splitWords(wordsStr, lemmaSpellingsKeys = ('_',)):
    words = []
    if wordsStr is None or wordsStr == '':
        wordStrs = []
    else:
        wordStrs = wordsStr.split(',')
    for w in wordStrs:
        w = w.strip()
        m_ = re.fullmatch(r'\((.+)\)', w)
        if m_:
            wes = [we for we in (WordEntry.parse(w_.strip(), lemmaSpellingsKeys) for w_ in m_[1].split('|')) if we is not None]
        else:
            we = WordEntry.parse(w)
            wes = [] if we is None else [we]
        words.append(wes)
    return words

class Line(LineBase):
    __slots__ = (
        'poses',    # { <pos> } -- i.e. set of poses
    );

    def __init__(self, grp, si, poses = None):
        super().__init__(grp, si)
        if poses is None:
            self.poses = set()
        else:
            self.poses = poses

    def sortKey(self):
        si = self.si[0]
        return (si.level, si.category, si.region, basePosInfo[self.grp.base_pos].lemma_pos not in self.poses, sorted(si.tags))

    def lemmaIncluded(self):
        return basePosInfo[self.grp.base_pos].lemma_pos in self.poses

    def print(self, out = None, first = False, trimSpellings = True):
        if out is None:
            out = sys.stdout

        for le in self.grp.entries:
            needSep = False
            for si in self.si:
                if needSep:
                    out.write(' ')
                si.print(out)
                needSep = True
            
            if le.spellings:
                exclude = self.grp._redundantSpellings if trimSpellings and self.grp._redundantSpellings is not None else ()
                out.write(f': {le.spellings.str(exclude)}')
                num = le._num
                if num != 0:
                    out.write(f' {{{num}}}')

            poses = posmap(self.grp.base_pos, (pos for pos in self.poses if pos in le.words))
            if self.lemmaIncluded():
                lwe = le.words[poses[0]][0]
                self._lemmaPart(out, lwe.word, lwe.entry_rank)
            else:
                self._lemmaPart(out, None)

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

    def finishParse(self, g, lemma, m, entriesBySpellings):
        spellings = Spellings.parse(ifNone(m['spellings'], ''))
        spellingKey = (spellings.key(), m['num'])
        le = entriesBySpellings.get(spellingKey, None)
        if le is None:
            le = LemmaEntry()
            le.spellings = spellings
            entriesBySpellings[spellingKey] = le
        if lemma is not None:
            if not hasattr(le, 'lemma'):
                le.lemma = lemma.word
            elif le.lemma != lemma.word:
                raise ValueError(f"conflicting lemma entry for '{spellings}': {le.lemma} vs {lemma.word}")
        addedPoses = Line.procWords(spellings, lemma, g.base_pos, m, le.words)
        self.poses.update(addedPoses)
        if m['comments']:
            le.comments.extend(Line.splitComments(m['comments']))

    @staticmethod
    def procWords(lemmaSpellings, lemma, base_pos, m, wordsByPos):
        if lemmaSpellings:
            lemmaSpellingsKeys = lemmaSpellings.keys();
        else:
            lemmaSpellingsKeys = '_',
        if lemma is None:
            words = [[]]
        else:
            words = [[lemma]]
        words += _splitWords(m['words'], lemmaSpellingsKeys)
        poses = posesFromList(base_pos, words)
        if poses is None:
            raise ValueError(f"could not map list of words of length {len(words)} with base pos of '{base_pos}'")
        assert(len(words) == len(poses))
        addedPoses = []
        for pos, wes in zip(poses, words):
            if not wes:
                continue
            # fixme? sort wes first
            addedPoses.append(pos)
            if pos not in wordsByPos:
                wordsByPos[pos] = wes
            elif wordsByPos[pos] != wes:
                raise ValueError(f"conflicting word entry for '{pos}' for '{spellings}': {wordsByPos[pos]}, {wes}")
        return addedPoses

    @staticmethod
    def splitComments(commentsStr):
        if commentsStr is None:
            return None
        else:
            return (c.strip() for c in commentsStr.split('#') if not c.startswith('!'))

class Override(LineBase):
    __slots__ = (
        'lemma',  #
        'words',  # [ <word> ]
    )
    
    def __init__(self, grp, si, lemma = None, words = ()):
        super().__init__(grp, si)
        if lemma is not None:
            self.lemma = lemma
            self.words = words

    def print(self, out = None):
        for si in self.si:
            si.print(out);
        out.write(f': +')
        self._lemmaPart(out, self.lemma)
        if self.words:
            out.write(': ')
            out.write(', '.join(self.words))
        out.write('\n')
    
    def finishParse(self, g, lemma, m, entriesBySpellings):
        wordStrs = []
        if m['words']:
            wordStrs = m['words'].split(',')
        words = []
        for w in wordStrs:
            w = w.strip()
            validateWord(w)
            words.append(w)
        #le = next((le for le in self.grp.entries if le.lemma == lemma), None)
        #if le is None:
        #    raise ValueError('unable to find lemma: {lemma}')
        self.lemma = lemma.word
        self.words = sorted(words)

class ClusterComment(SlotsDataClass):
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
        out.write('\n')
        for line in self.comment.splitlines():
            out.write(f'## {line}\n')
        out.write('\n')

    @classmethod
    def parse(cls, first, *rest):
        m = re.fullmatch(r'\#\# \s* (.+?) \s* (\( (.*) \)|)  \s* : (.*)', first, re.VERBOSE)
        if not m:
            raise ValueError(f'invalid comment line: {first}')
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

class GroupComment(SlotsDataClass):
    __slots__ = ('lines',)

    def __init__(self, text = None):
        if text is None:
            self.lines = []
        else:
            self.lines = text.splitlines()

    def __str__(self):
        return '\n'.join(self.lines)

    def __bool__(self):
        return bool(self.lines)
    
    def print(self, out = None):
        for line in self.lines:
            out.write(f'## {line}\n')

    @classmethod
    def parse(cls, *lines):
        c = cls()
        for l in lines:
            l = re.sub(r'^## ?','', l)
            c.lines.append(l)
        return c

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
        (we.word, we.entry_rank) = parseWordPart(m[3])
        we.duplicate = False
        return we
    def __eq__(self, other):
        if not isinstance(other, WordEntry):
            return NotImplemented
        return self.spellings == other.spellings and self.word == other.word and self.entry_rank == other.entry_rank

########################################################################

def _createClusters(groups, clusterComments, conn = None):

    if conn:
        expected_spellings = tuple(sp for sp, in conn.execute("select spelling from spellings where spelling != '_' order by order_num"))
    else:
        expected_spellings = _spellings_ab
    
    groupsByHeadword = defaultdict(list)
    clusterMapping = {}
    for grp in groups:
        if not grp.lines: continue
        grp.finalize(expected_spellings)
        groupsByHeadword[clusterKey(grp.headword)].append(grp)
        members = set()
        for le in grp.entries:
            le.finalize()
            w = clusterKey(le.lemma)
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


_dir = Path(__file__).parent.resolve()
    
def openDB(dbfile, create = False, copyFrom = None, transCopy = False):

    if transCopy:
        copyFrom = dbfile
        dbfile = ':memory:'

    if not dbfile:
        raise ValueError

    if copyFrom:
        create = True

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

    conn = sqlite3.connect(dbfile, isolation_level = 'DEFERRED')
    
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON");
    conn.execute("PRAGMA synchronous = OFF");

    if isinstance(copyFrom, str):
        with openDB(copyFrom) as conn0:
            conn0.backup(conn)
    elif copyFrom:
        copyFrom.backup(conn)
    elif create:
        conn.executescript((_dir / 'schema.sql').read_text())
        conn.executescript((_dir / 'constdata.sql').read_text())
        conn.executescript((_dir / 'fix_pos.sql').read_text())
        conn.executescript((_dir / 'views.sql').read_text())
        conn.executescript((_dir / 'scowl.sql').read_text())
    
    return conn

########################################################################

def importFromDB(conn, *, filterTable = None, filterQuery = None):
    groups, clusterComments = _importFromDB(conn, filterTable, filterQuery)
    return _createClusters(groups, clusterComments, conn)

def _importFromDB(conn, filterTable, filterQuery):
    words = {}

    if filterTable:
        filterQuery = f"select * from {filterTable}"
        filterTable = None
    if filterQuery:
        groupIdFilter = f"(group_id in ({filterQuery}))"
        lemmaIdFilter = f"(lemma_id in (select lemma_id from words where {groupIdFilter}))"
        wordIdFilter = f"(word_id in (select word_id from words where {groupIdFilter}))"
        headwordFilter = f"(headword in (select word from words where {groupIdFilter}))"
    else:
        groupIdFilter = 'true'
        lemmaIdFilter = 'true'
        wordIdFilter = 'true'
        headwordFilter = 'true'

    cur = conn.cursor()

    groups = {}
    for r in cur.execute(f"select * from groups where {groupIdFilter}"):
        grp = Group()
        grp.base_pos = r['base_pos']
        grp.defn_note = r['defn_note']
        grp.usage_note = r['usage_note']
        grp.pos_class = r['pos_class']
        grp.lemma_rank = r['lemma_rank']
        grp._group_id = r['group_id']
        grp.entries = []
        grp.lines = []
        grp.override = {}
        grp.commentLines = GroupComment()
        groups[r['group_id']] = grp

    for r in cur.execute(f"select * from group_comments where {groupIdFilter}"):
        groups[r['group_id']].commentLines = GroupComment(r['comment']);

    wordsById = {}
    lemmasById = {}

    for r in cur.execute(f"select * from lemma_variant_info where {lemmaIdFilter}"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute(f"select * from derived_variant_info where {wordIdFilter}"):
        word_id = r['word_id']
        we = wordsById.get(word_id)
        if we is None:
            wordsById[word_id] = we = WordEntry()
            we.spellings = Spellings()
        we.spellings.add(r['spelling'],r['variant_level'])

    for r in cur.execute(f"select * from lemma_comments where {lemmaIdFilter} order by lemma_id, order_num"):
        lemma_id = r['lemma_id']
        le = lemmasById.get(lemma_id)
        if le is None:
            lemmasById[lemma_id] = le = LemmaEntry()
            le.spellings = Spellings()
        le.comments.append(r['comment'])

    lemma_id = -1
    le = None
    for r in cur.execute("select *, dup.word is not null as dup "
                         "from words left join duplicate_derived dup using (group_id, word) "
                         f"where {groupIdFilter} "
                         "order by lemma_id"):
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
        we.duplicate = bool(r['dup'])
        le.words.setdefault(r['pos'], []).append(we)
        if r['word_id'] == lemma_id:
            le.lemma = r['word']

    scowlInfoByGroupPos = defaultdict(lambda: defaultdict(list))
    linesByGroup = defaultdict(lambda: defaultdict(set))

    for r in cur.execute("select group_id, level, category, region, pos, group_concat(tag) as tags "
                         "from scowl_data "
                         f"where {groupIdFilter} "
                         "group by group_id, level, category, region, pos"):
        level = r['level']
        category = r['category']
        region = r['region']
        tags = sorted(r['tags'].split(','))
        key = (level, category, region, *tags)
        linesByGroup[r['group_id']][key,].add(r['pos'])
        #scowlInfoByGroupPos[r['group_id']][r['pos']].append(key)

    #for group_id, byPos in scowlInfoByGroupPos.items():
    #    for pos, key in byPos.items():
    #        key.sort()
    #        linesByGroup[group_id][tuple(key)].add(pos)

    for group_id, lines in linesByGroup.items():
        grp = groups[group_id]
        for si, poses in lines.items():
            grp.lines.append(Line(grp, [ScowlInfo(level, category, region, tags) for (level, category, region, *tags) in si], poses))

    overrideByGroup = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in cur.execute("select group_id, level, category, region, lemma, word, group_concat(tag) as tags "
                         "from scowl_override join entries using (word_id) "
                         f"where {wordIdFilter} " 
                         "group by group_id, level, category, region, lemma, word"):
        override = overrideByGroup[r['group_id']]
        level = r['level']
        category = r['category']
        region = r['region']
        tags = sorted(r['tags'].split(','))
        key = (level, category, region, *tags)
        override[key][r['lemma']].append(r['word'])

    for group_id, override in overrideByGroup.items():
        grp = groups[group_id]
        for (level, category, region, *tags), ov in override.items():
            for lemma, words in ov.items():
                grp.override[lemma] = Override(grp, [ScowlInfo(level, category, region, tags)], lemma, sorted(w for w in words if w != lemma))

    clusterComments = {}
    for r in cur.execute(f"select * from cluster_comments where {headwordFilter}"):
        clusterComments[clusterKey(r['headword'])] = ClusterComment(r['headword'], r['other_words'], r['comment'])

    for k in list(clusterComments.keys()):
        c = clusterComments[k]
        m = re.match(r'^see note( for | )"?([\w]+)"?', c.comment, re.IGNORECASE)
        if m:
            other = clusterComments[b'koran' if m[2] == 'Quran' else clusterKey(m[2])]
            other.other_words += f' {c.word} {c.other_words}'
            del clusterComments[k]

    return (groups.values(), clusterComments)

def searchDB(conn, words, byCluster):
    conn.execute("create temp table group_id_filter (group_id integer primary key)")
    for w in words:
        conn.execute("insert or ignore into group_id_filter select group_id from words where word = ?", (w,))
    conn.execute("analyze group_id_filter")
    if byCluster:
        conn.execute("insert or ignore into group_id_filter "
                     "select b.group_id from group_id_filter join cluster_map a using (group_id) join cluster_map b using (cluster_id)")
        conn.execute("analyze group_id_filter")
    clusters = importFromDB(conn, filterTable = "group_id_filter")
    conn.execute("drop table group_id_filter")
    return clusters
    
def exportToDB(clusters, conn):
    group_id = 1
    word_id = 1

    conn.execute("delete from scowl_override")
    conn.execute("delete from scowl_data")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from group_comments")
    conn.execute("delete from cluster_comments")
    conn.execute("delete from derived_variant_info")
    conn.execute("delete from lemma_variant_info")
    conn.execute("delete from words")
    conn.execute("delete from groups")
    
    for cluster in clusters:
        cluster_id = group_id

        for group in cluster.groups:
            conn.execute("insert into cluster_map (group_id, cluster_id) values (?, ?)", (group_id,cluster_id))

            group_id, word_id = _exportGroup(conn, group, group_id, word_id)

        for c in cluster.comments:
            conn.execute("insert into cluster_comments (headword, other_words, comment) values (?, ?, ?)",
                         (c.word, c.other_words, c.comment))

    conn.execute("analyze")
    conn.commit()

    conn.executescript((_dir / 'post.sql').read_text())

def _exportGroup(conn, group, group_id, word_id):
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
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, variant_level) for sp in spellings))
                elif we.spellings is not None:
                    conn.executemany("insert into derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                     ((word_id, sp, vl) for sp, vl in we.spellings.items()))
                word_id += 1

        conn.executemany("insert into lemma_variant_info (lemma_id, spelling, variant_level) values (?, ?, ?)",
                         ((lemma_id, sp, vl) for sp, vl in le.spellings.items()))

        conn.executemany("insert into lemma_comments (lemma_id, order_num, comment) values (?, ?, ?)",
                         ((lemma_id, i, c) for i, c in enumerate(le.comments)))

        ov = group.override.get(le.lemma, None)
        if ov:
            for si in ov.si:
                for tag in si.tags:
                    conn.execute("insert into scowl_override (level, category, region, tag, word_id) values (?, ?, ?, ?, ?)",
                                 (si.level, si.category, si.region, tag, lemma_id))
                    for word in ov.words:
                        conn.execute("insert into scowl_override "
                                     "select ?, ?, ?, ?, word_id from words where lemma_id = ? and word = ?",
                                     (si.level, si.category, si.region, tag, lemma_id, word))

    for l in group.lines:
        for pos in l.poses:
            for si in l.si:
                for tag in si.tags:
                    conn.execute("insert into scowl_data (level, category, region, tag, group_id, pos) values (?, ?, ?, ?, ?, ?)",
                                 (si.level, si.category, si.region, tag, group_id, pos))

    if group.commentLines:
        conn.execute("insert into group_comments (group_id, comment) values (?, ?)",
                     (group_id, str(group.commentLines)))

    group_id += 2 if group.base_pos in ('n_v', 'aj_av') else 1
    return (group_id, word_id)


class StreamWrapper:
    def __init__(self, out):
        self.lastLine = None
        self.out = out

    def write(self, line):
        if self.lastLine is not None:
            self.out.write(self.lastLine)
        self.lastLine = line

    def finish(self):
        if self.lastLine != '\n':
            self.out.write(self.lastLine)

def exportAsText(clusters, conn = None, out = None, *, trimSpellings = True, showClusters = False, showExtraInfo = True):
    if out is None:
        out = sys.stdout
    out = StreamWrapper(out)

    dbVars = SimpleNamespace()
    if conn:
        for var, val in conn.execute('select var, val from _variables'):
            setattr(dbVars, var, val)

    if hasattr(dbVars, 'filter_type') and showExtraInfo:
        out.write("#: FILTERED VIEW OF SCOWL DATA:\n")
        out.write(f"#:   {dbVars.filter_type}\n")
        out.write(f"#:   {dbVars.filter_where_clause}\n")
        if hasattr(dbVars, "filter_simplifications"):
            out.write(f"#:   simplifications: {dbVars.filter_simplifications}\n")
        out.write("\n")

    for cluster in clusters:

        for group in cluster.groups:

            first = True
            for line in group.lines:
                try:
                    line.print(out, first, trimSpellings)
                except ValueError as err:
                    _warn(f'skipping line: {line.grp.headword}: {line.poses}: {err}')
                first = False
            for lemma in sorted(group.override.keys()):
                group.override[lemma].print(out)

            if not group._lemmaIncluded:
                l = Line(group, [ScowlInfo(99)])
                l.poses.add(basePosInfo[group.base_pos].lemma_pos)
                l.print(out, False, trimSpellings)

            for c in group.problems:
                out.write(f"#! {c}\n")
            group.commentLines.print(out)
            out.write('\n')

        for c in cluster.comments:
            c.print(out)

        if showClusters:
            out.write('\n')

    if conn and showExtraInfo:
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
        for symbol, num, descr in conn.execute("select variant_symbol, variant_level, variant_descr from variant_levels where variant_symbol != '' order by variant_level"):
            out.write(f"#:   {symbol}: {num}: {descr}\n")
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

    out.finish()

def _mergeText(f, groups, clusterComments):
    grp = None
    lines = defaultdict(set)
    override = []
    entriesBySpellings = {}
    commentLines = []
    for lineStr in chain(f, ['']):
        lineStr = lineStr.strip()
        if lineStr == '':
            if lines:
                grp.lines = []
                for (level, category, region, tags), poses in lines.items():
                    l = Line(grp, [ScowlInfo(level, category, region, tags)], poses)
                    grp.lines.append(l)
                grp.entries = list(entriesBySpellings.values())
                have = addMissingSpellings(grp.entries)
                for le in grp.entries:
                    for wes in le.words.values():
                        addMissingSpellings(wes, have)
                groups.append(grp)
                if commentLines:
                    grp.commentLines = GroupComment.parse(*commentLines)
                grp.override = {}
                for ov in override:
                    grp.override[ov.lemma] = ov
            elif commentLines:
                c = ClusterComment.parse(*commentLines)
                clusterComments[clusterKey(c.word)] = c
            grp = None
            lines.clear()
            override.clear()
            entriesBySpellings.clear()
            commentLines.clear()
            continue
        
        if grp is None:
            grp = Group()
            grp.commentLines = GroupComment('')

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

        if isinstance(l, Override):
            override.append(l)
        # fixme: generalize and rework to index by pos not scowl info
        elif l.si[0].level is None or l.si[0].level < 99:
            key = (l.si[0].level, l.si[0].category, l.si[0].region, frozenset(l.si[0].tags))
            lines[key].update(l.poses)

def importText(f = None):
    groups = []
    clusterComments = {}
    _mergeText(sys.stdin if f is None else f, groups, clusterComments)
    return _createClusters(groups, clusterComments)

BasicInfo = namedtuple('BasicInfo', 'base_pos pos_class word is_lemma')

def roughParse(f = None):
    if f is None:
        f = sys.stdin

    for line in f:
        line = line.strip()
        if line == '' or line.startswith('#'):
            continue

        m = _matchLine(line)
        if m is None:
            raise ValueError(f"bad line: {line}")
        lemma = m['lemma'].strip()
        if lemma != '-':
            (lemma_rank, lemma, entry_rank) = parseLemmaPart(lemma)
            base_pos = m['base_pos']
            pos_class = m['pos_class']
            yield BasicInfo(base_pos, pos_class, lemma, True)

        try:
            words = _splitWords(m['words'])
        except:
            raise ValueError(f"bad line: {line}")

        for ws in words:
            for we in ws:
                yield BasicInfo(base_pos, pos_class, we.word, False)

def mergeEntries(conn, f = None, *, tag = None, onConflict = 'merge', preview = False):
    clusters = importText(f)

    conn.execute("begin")

    next_group_id,  = next(conn.execute("select max(group_id) + 2 from groups"))
    next_word_id, = next(conn.execute("select max(word_id) + 1 from words"))

    conn.execute("create temp table merged_groups (group_id integer primary key)")

    for cluster in clusters:
        for grp in cluster.groups:
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

        for comment in cluster.comments:
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

class LineInfo(SlotsDataClass):
    __slots__ = ('line', 'action', 'si', 'lemma', 'pos', 'defn_note', 'group_id', 'lemma_id', 'spellings', 'words', 'comments')
    def __init__(self, line):
        self.line = line
        self.words = {}
        self.action = 'adjust'

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

DEBUG_SQL = False
def adjustEntries(conn, f = None, *,
                  preview = False, strict = True, ignoreErrors = False,
                  groupComment = None, replaceComments = True):
    if f is None:
        f = sys.stdin

    groups = []
    word_ids = {}

    errors = False
    gi = GroupInfo()

    def registerLine(li, new_pos, outer_pos = None):
        ids = [*conn.execute("select distinct group_id, lemma_id from lemmas "
                             "where lemma = ? and base_pos = ? and defn_note = ?",
                             (li.lemma.word, li.pos, li.defn_note))]

        assert li.action in ('add', 'remove', 'adjust', 'replace')

        if new_pos is None:
            new_pos = li.pos
        if outer_pos is None:
            outer_pos = new_pos

        if li.action == 'add':
            assert li.pos == new_pos
            if len(ids) > 0:
                raise ValueError(f"cannot add line: lemma already exists")
            if new_pos not in gi.subGroups:
                gi.subGroups[new_pos] = SubGroupInfo(None)
        else:
            if len(ids) == 0:
                if li.pos == 'n_v':
                    li_n = copy.copy(li)
                    li_n.pos = 'n'
                    registerLine(li_n, None, outer_pos)
                    li_v = copy.copy(li)
                    li_v.pos = 'v'
                    registerLine(li_v, None, outer_pos)
                    return
                elif li.pos == 'aj_av':
                    li_n = copy.copy(li)
                    li_n.pos = 'aj'
                    registerLine(li_n, None, outer_pos)
                    li_v = copy.copy(li)
                    li_v.pos = 'av'
                    registerLine(li_v, None, outer_pos)
                    return
                elif not li.pos and gi.pos:
                    li.pos = gi.pos
                    registerLine(li, new_pos)
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
            errors = True
            _warn(f'{line}: {err}: skipping group')
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
                raise ValueError(f"bad line: {line}")

            li.si = ScowlInfo.parse(ifNone(m['tags'],''))
            li.lemma = WordEntry()
            (lemma_rank, li.lemma.word, li.lemma.entry_rank) = parseLemmaPart(m['lemma'].strip())

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

            Line.procWords(li.spellings, li.lemma, base_pos, m, li.words)

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
                    if li.action in ('add', 'replace'):
                        li.lemma_id = next_word_id
                        # fixme: need a check elsewhere that the line provided a lemma, otherwise this will fail
                        for pos, wes in li.words.items():
                            for we in wes:
                                conn.execute("insert into new_words (word_id, main_group_id, lemma_id, pos, word) values (?, ?, ?, ?, ?)",
                                             (next_word_id, sg.id, li.lemma_id, pos, we.word))
                                if we.spellings:
                                    conn.executemany("insert into new_derived_variant_info (word_id, spelling, variant_level) values (?, ?, ?)",
                                                     ((next_word_id, sp, vl) for sp, vl in we.spellings.items()))
                                next_word_id += 1
                    else:
                        # fixme: be more intelligent about this
                        if replaceComments:
                            conn.execute("insert or ignore into new_group_comments values (?, null)", (li.group_id,))

                    if li.spellings:
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
                except Exception as err:
                    raise ValueError(f"failed to add line: {li.line}")
            # fixme: look into avoiding duplicates
            conn.execute("insert or replace into new_group_info (main_group_id, base_pos, defn_note, pos_class, usage_note, lemma_rank) values (?, ?, ?, ?, ?, ?)",
                         (sg.id, base_pos, gi.defn_note, gi.pos_class, gi.usage_note,
                          None if gi.lemma_rank is None else '' if gi.lemma_rank == '_' else gi.lemma_rank))
            if comment:
                conn.execute("insert or replace into new_group_comments values (?, ?)", (sg.id, str(comment)))

            unaccountedFor = [
                *conn.execute("select word from words join to_merge on group_id = other_group_id "
                              "where main_group_id = ? and word_id = lemma_id and word_id not in (select * from lemmas_accounted_for)",
                              (sg.id,))] if strict else None
            if unaccountedFor:
                _warn(f"unaccounted lemmas, skipping group: {', '.join(word for word, in unaccountedFor)}")
                errors = True
                conn.execute("rollback to sp")
            else:
                conn.execute("drop table lemmas_accounted_for")

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

    #conn.commit()
    #exit(1)

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

def combinePOS(conn):
    conn.executescript((_dir / 'combine_pos.sql').read_text())
    conn.executescript((_dir / 'post.sql').read_text())

def splitPOS(conn):
    conn.executescript((_dir / 'split_pos.sql').read_text())
    conn.executescript((_dir / 'post.sql').read_text())
    
########################################################################

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

Query = namedtuple('Query', 'select from_ where')

def queryString(
        *,
        size = None,
        spellings = None,
        regions = None,
        variantLevel = None,
        variantLevels = None,
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
        try:
            vl = int(variantLevel)
        except ValueError:
            vl = variantFromSymbol[variantLevel]
        clauses.append(f"variant_level <= {vl}")

    if variantLevels is not None:
        if not (variantLevel is None):
            raise ValueError('both variantLevel and variantLevels can not be defined at the same time')
        clauses.append(f"variant_level in ({','.join(str(int(v)) for v in sorted(variantLevels))})")

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

    addSetQueryClause('pos_category', lambda p: p in POS_CATEGORIES, '', posCategories)

    addSetQueryClause('category', lambda _: True, '', categories)

    addSetQueryClause('tag', lambda _: True, '', tags)

    addSetQueryClause('usage_note', lambda _: True, '', usageNotes)

    if not clauses:
        clauses.append('true')

    return Query(
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
        return ''.join([rf"([{charSet}](?:[{charSetMiddle}]*[{charSet}]|))",
                        r'\.?' if dot == 'strip' else ''])

def getWords(conn, *, deaccent = False, useWordFilter = True, nosuggest = None, nosuggestSuffix = '/!', **args):
    """Returns a generator of words based on the arguments.

    Many arguments can filter by either including or excluding a set of
    values.  If the argument is a sequence then it will included the given
    along with the default value.  To not include the default use the Include
    class with the the noDefault parater set to True.  To exclude values
    instead, use the Exclude class.  A value of None means to not filter based
    on that argument.

    If _size_ is None it defaults to 60. 
    If _spellings_ is None it defaults to ('A',)
    If _region_ is None it value depends on _spellings_
    If _variant_level_ is None it defaults to '.'
    """
    args.setdefault('size', 60)
    args.setdefault('spellings', ('A',))
    if 'variantLevel' not in args and 'variantLevels' not in args:
        args['variantLevel'] = '.'
    
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

    nosuggestWords = set()
    if nosuggest is not None:
        if nosuggest:
            nosuggest = set(nosuggest)
        else:
            nosuggest = {'vulgar-1', 'vulgar-2', 'offensive-1', 'offensive-2'}
        possibleValues = {'vulgar-1', 'vulgar-2', 'vulgar-3', 'offensive-1', 'offensive-2', 'offensive-3'}
        leftover = nosuggest - possibleValues;
        if leftover:
            raise ValueError(leftover) # fixme
        choices = ','.join(f"'{c}'" for c in nosuggest)
        nosuggestQuery = f"select word from words join groups using (group_id) where usage_note in ({choices})"
        print(nosuggestQuery, file=sys.stderr)
        for w, in conn.execute(nosuggestQuery):
            nosuggestWords.add(w)

    for w, in conn.execute(query):
        orig = w
        if useWordFilter:
            m = wordFilter.fullmatch(w)
            if not m:
                continue
            w = m[1]
        if deaccent:
            w = deaccent(w)
        if orig in nosuggestWords:
            w = f"{w}{nosuggestSuffix}"
        yield w

import inspect
from inspect import signature,Signature,Parameter

getWords.__signature__ = Signature([
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD),
    *signature(queryString).parameters.values(),
    *signature(wordFilterRegEx).parameters.values(),
    *(p for p in signature(getWords).parameters.values() if p.kind == Parameter.KEYWORD_ONLY),
])

def _filterDB(filterType, conn, orig, *, simplify = (), **args):
    queryArgs = {p.name: args.pop(p.name, p.default) for p in signature(queryString).parameters.values()}
    whereClause = queryString(**queryArgs).where
    if 'variantsOnly' in args:
        del args['variantsOnly']
        whereClause = f"{whereClause} and group_id in (select group_id from orig.words group by group_id, pos having count(*) > 1)"
    print(whereClause, file=sys.stderr)
    if args:
        raise TypeError("unexpected args: {}".format(', '.join(args.keys())))

    conn.execute('attach database ? as orig', (orig,));

    if filterType == 'by-line':
        simplify = set(simplify)
        _filterByLine(conn, simplify, queryArgs, whereClause)
    elif filterType == 'by-group':
        simplify = ()
        _filterByGroup(conn, whereClause)
    elif filterType == 'by-cluster':
        simplify = ()
        _filterByGroup(conn, whereClause, includeCluster = True)
    else:
        raise ValueError(f"invalid filter type: {filterType}")

    conn.execute("insert into cluster_comments select * from orig.cluster_comments where headword in (select word from words)")
    conn.execute("insert into group_comments select * from orig.group_comments where group_id in (select group_id from groups)")
    conn.execute("insert into lemma_comments select * from orig.lemma_comments where lemma_id in (select lemma_id from words)")

    conn.execute("insert into cluster_map select * from orig.cluster_map")

    conn.execute("insert into _variables values(?, ?)", ('filter_type', filterType))
    conn.execute("insert into _variables values(?, ?)", ('filter_where_clause', whereClause))
    if simplify:
        conn.execute("insert into _variables values(?, ?)", ('filter_simplifications', ', '.join(sorted(simplify))))

def _filterByLine(conn, simplify, queryArgs, whereClause):
    conn.execute(f"create temp table filtered as select group_id, lemma_id, word_id from orig.scowl_ {whereClause}")
    conn.execute("insert into groups select * from orig.groups where group_id in (select group_id from filtered)")
    conn.execute("insert into words select * from orig.words where word_id in (select word_id from filtered union select lemma_id from filtered)")
    
    if queryArgs['size'] is None:
        simplify.discard('size')
    leftover = simplify - {'size', 'category', 'region', 'tag', 'tags'}
    if leftover:
        raise ValueError(f"invalid values for simplfy: {', '.join(sorted(leftover))}")

    _size_ = queryArgs['size'] if 'size' in simplify else 'level'
    _category_ = "''" if 'category' in simplify else 'category'
    _region_ = "''" if 'region' in simplify else 'region'
    _tag_ = "''" if 'tag' in simplify or 'tags' in simplify else 'tag'
    conn.execute(f"insert or ignore into scowl_data select {_size_}, {_category_}, {_region_}, {_tag_}, group_id, pos from orig._scowl_main {whereClause}")
    conn.execute(f"insert or ignore into scowl_override select {_size_}, {_category_}, {_region_}, {_tag_}, word_id from orig._scowl_override {whereClause}")
    if simplify:
        cleanupScowlData(conn)

    conn.execute("create temp table filtered_variant_info as select lemma_id, word_id, spelling, lemma_variant_level, derived_variant_level "
                 "from orig._scowl_main "
                 f"{whereClause} and (lemma_variant_level is not null or derived_variant_level is not null)")
    spellings = queryArgs['spellings']
    if spellings and len(spellings) == 1:
        conn.execute("insert into lemma_variant_info "
                     "select lemma_id, '_', min(lemma_variant_level) from filtered_variant_info where lemma_variant_level is not null group by lemma_id")
        conn.execute("insert into derived_variant_info "
                     "select word_id, '_', min(derived_variant_level) from filtered_variant_info where derived_variant_level is not null group by word_id")
        conn.execute("analyze")
        conn.execute("delete from lemma_variant_info "
                     "where lemma_id in (select lemma_id from lemmas where group_id in ("
                     "  select group_id from lemma_variant_info join lemmas using (lemma_id) group by group_id having min(variant_level = 0) is True))")
        conn.execute("delete from derived_variant_info "
                     "where word_id in (select word_id from words where (lemma_id, pos) in ("
                     "  select lemma_id, pos from derived_variant_info join words using (word_id) group by lemma_id, pos having min(variant_level = 0) is True))")
        simplify.add('spellings')
    else:
        conn.execute("insert into lemma_variant_info "
                     "select distinct lemma_id, spelling, lemma_variant_level from filtered_variant_info where lemma_variant_level is not null")
        conn.execute("insert into derived_variant_info "
                     "select distinct word_id, spelling, derived_variant_level from filtered_variant_info where derived_variant_level is not null")
        conn.execute("analyze")

    pruneConstTables(conn)

def _filterByGroup(conn, whereClause, includeCluster = False):
    conn.execute("create temp table filtered (group_id integer primary key)")
    conn.execute(f"insert or ignore into filtered select group_id from orig.scowl_ {whereClause}")

    if includeCluster:
        conn.execute("insert or ignore into filtered "
                     "select b.group_id from cluster_map a join filtered using (group_id) join cluster_map b using (cluster_id)")
                 
    conn.execute("insert into groups select * from orig.groups where group_id in (select group_id from filtered)")
    conn.execute("insert into words select * from orig.words where group_id in (select group_id from filtered)")

    conn.execute("insert into scowl_data select * from orig.scowl_data where group_id in (select group_id from filtered)")
    conn.execute("insert or ignore into scowl_override select level, category, region, tag, word_id "
                 "from orig._scowl_override where group_id in (select group_id from filtered)")

    conn.execute("insert into lemma_variant_info "
                 "select v.* from orig.lemma_variant_info v join lemmas using (lemma_id) where group_id in (select group_id from filtered)")
    conn.execute("insert into derived_variant_info "
                 "select v.* from orig.derived_variant_info v join words using (word_id) where group_id in (select group_id from filtered)")
    
def cleanupScowlData(conn):
    cleanupWhereClause = ("where a.level <= b.level "
                          "and (a.category = b.category or a.category = '' and b.category != '') "
                          "and (a.region = b.region or a.region = '' and b.region != '') "
                          "and (a.tag = b.tag or a.tag = '' and b.tag != '') "
                          "and (a.category != b.category or a.region != b.region or a.tag != b.tag) ")
    conn.execute("delete from scowl_data "
                 "where (level, category, region, tag, group_id, pos) "
                 f"in (select b.* from scowl_data a join scowl_data b using(group_id,pos) {cleanupWhereClause})");
    conn.execute("delete from scowl_override "
                 "where (level, category, region, tag, word_id) "
                 f"in (select b.* from scowl_override a join scowl_override b using(word_id) {cleanupWhereClause})");
    
def pruneConstTables(conn):
    conn.execute('create temp table used_variant_info as '
                 'select spelling, variant_level from lemma_variant_info '
                 'union '
                 'select spelling, variant_level from derived_variant_info')
    conn.execute("delete from spellings where spelling not in (select spelling from used_variant_info)")
    conn.execute("delete from variant_levels where variant_level not in (select variant_level from used_variant_info)")

def filterDB(orig, new, filterType, **args):
    
    conn = openDB(new, create=True)
    _filterDB(filterType, conn, orig, **args)
    conn.commit()
    if filterType == 'by-line' and conn.execute("select true from orig.groups where base_pos in ('n_v','aj_av') limit 1").fetchone():
        combinePOS(conn)

    conn.executescript((_dir / 'post.sql').read_text())
