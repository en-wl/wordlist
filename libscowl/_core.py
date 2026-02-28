from collections import namedtuple, defaultdict
from itertools import groupby, chain
from types import SimpleNamespace
from typing import NamedTuple,Any
from pathlib import Path
from operator import methodcaller
from copy import copy, deepcopy
import sys
import os
import sqlite3
import json
import re

# †

from ._common import *
from ._constdata import *

DEBUG_SQL = strtobool(os.environ.get('SCOWL_DEBUG_SQL', 'False'))

def _warn(msg):
    sys.stderr.write(f'warning: {msg}\n')

class StreamWrapper:
    def __init__(self, out):
        self.lastLine = None
        self.out = out

    def write(self, line):
        if self.lastLine is not None:
            self.out.write(self.lastLine)
        self.lastLine = line

    def finish(self):
        if self.lastLine is not None and self.lastLine != '\n':
            self.out.write(self.lastLine)

def ifNone(a, b):
    return b if a is None else a

def noneIf(a, b):
    return None if a == b else a

# Default is a special value to indicate that a value has not been provided in
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
        if isinstance(other, (DefaultType, str)):
            return True
        return NotImplemented
    def __gt__(self, other):
        if isinstance(other, (DefaultType, str)):
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

_deaccentMap = dict(zip(_accented, _deaccented))

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
    group_rank: Any
    lemma: Any
    entry_rank: Any

def parseLemmaPart(w):
    w = w.strip()
    if w == '-':
        return LemmaPart(None, None, None)
    group_rank = Default
    if w[0] in '_@!-':
        group_rank = _fixRank(w[0])
        w = w[1:]
    return LemmaPart(group_rank, *parseWordPart(w))

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
        raise ValueError('posmap: unrecognized pattern')
    leftover = poses - set(new_poses)
    if leftover:
        raise ValueError(f'posmap: leftover forms: {leftover}')
    return new_poses

def posesFromList(base_pos, words, isPossessive):
    poses = None
    if len(words) == 1:
        poses = [basePosInfo[base_pos].lemma_pos]
    elif base_pos == 'n':
        if len(words) == 4:
            poses = ['n0', 'ns', 'np', 'nsp']
        elif len(words) == 3:
            poses = ['n0', 'ns', 'np']
        elif len(words) == 2:
            if words[1] and isPossessive(words[1]):
                poses = ['n0', 'np']
            else:
                poses = ['n0', 'ns']
    elif base_pos == 'n':
        if len(words) == 4:
            poses = ['ns', 'nss', 'nsp', 'nssp']
        elif len(words) == 3:
            poses = ['ns', 'nss', 'nsp']
        elif len(words) == 2:
            if words[1] and isPossessive(words[1]):
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
            if words[-1] and isPossessive(words[-1]):
                poses = ['m0', 'vd', 'vn', 'vg', 'ms', 'np']
            else:
                poses = ['m0', 'vd', 'vg', 'ms', 'np', 'nsp']
        if len(words) == 5:
            if words[-1] and isPossessive(words[-1]):
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
    if poses is None:
        raise ValueError(f"could not map list of words of length {len(words)} with base pos of '{base_pos}'")
    return poses

_spellings_ab = ('A', 'B', 'Z', 'C', 'D')
_spellings = ('*', '_', 'A', 'B', 'Z', 'C', 'D')

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
        self.groups.sort(key = methodcaller('sortKey'))

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
        'group_rank',# str
        'entries',   # [ LemmaEntry ]
        'lines',     # [ Line ]
        'override',  # { lemma: Override }
        'problems',  # [ str ]
        'commentLines', # GroupComment
        '_group_id',
        '_redundantSpellings',
        '_lemmaIncluded',
    )

    @property
    def lemmas(self):
        return (le.lemma for le in self.entries)

    def merge(self, attr, v, allowDefault = True):
        v0 = getattr(self, attr, None)
        if v0 is None or (allowDefault and v0 is Default):
            setattr(self, attr, v)
        elif v is not None and v != v0:
            raise ValueError(f'conflicting values for {attr} within group')

    def adjDefault(self, attr, v):
        if getattr(self, attr, Default) is Default:
            setattr(self, attr, v)

    def sortKey(self):
        l = self.lines[0]
        si = l.si[0]
        return (si.size + (100 if si.region != '' else 0) + (200 if si.category != '' else 0),
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
            self.problems.append(f"missing spellings: {' '.join(missing)}")

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
        'size',    # int
        'category', # str
        'region',   # str
        'tags',     # Tags
    )
    def __init__(self, size, category = '', region = '', tags = None):
        self.size = size
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
        out.write(f'{self.size}')
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
            out.write(f': {self.grp.group_rank}{lemma}{entry_rank}')
        else:
            out.write(': -')

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
        lemma = WordEntry()
        (group_rank, lemma.word, lemma.entry_rank) = parseLemmaPart(m['lemma'])
        if lemma.word is None:
            lemma = None
        g.merge('group_rank', group_rank, allowDefault = False)
        g.merge('base_pos', ifNone(m['base_pos'],''))
        g.merge('pos_class', ifNone(m['pos_class'], Default))
        g.merge('defn_note', ifNone(m['defn_note'], Default))
        g.merge('usage_note', ifNone(m['usage_note'], Default))
        l.finishParse(g, lemma, m, entriesBySpellings)
        return l

_lineRegex = re.compile(r'(?: (?P<tags>[0-9]+ [^:#]*):\s* |)'
                        r'(?: (?P<override>\+)\s*:\s* | (?P<spellings>[A-Za-z_][^:<>{}#]*) (\{(?P<num> [0-9]+)\}\s*|):\s* |)'
                        r'(?P<lemma>[^:<>{}#()]+)'
                        r'(?: <(?P<base_pos>[^/]*) (?:/(?P<pos_class>.*)|)>\s* |)'
                        r'(?: {(?P<defn_note>.+)}\s* |)'
                        r'(?: \((?P<usage_note>[^:#|]+)\)\s* |)'
                        r'(?: : \s* (?P<words>[^#]*) |)'
                        r'(?: \# (?P<comments>.*) |)',
                        re.VERBOSE)
def _matchLine(line):
    line = line.strip()
    m = _lineRegex.fullmatch(line)
    return m

def _splitWords(wordsStr, lemmaSpellingsKeys = ('_',), allowAsterisk = False):
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
            we = WordEntry.parse(w, None, allowAsterisk)
            wes = [] if we is None else [we]
        words.append(wes)
    return words

class Line(LineBase):
    __slots__ = (
        'poses',    # { <pos> } -- i.e. set of poses
    )

    def __init__(self, grp, si, poses = None):
        super().__init__(grp, si)
        if poses is None:
            self.poses = set()
        else:
            self.poses = poses

    def sortKey(self):
        si = self.si[0]
        return (si.size, si.category, si.region, basePosInfo[self.grp.base_pos].lemma_pos not in self.poses, sorted(si.tags))

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
        addedPoses = Line.procWords(spellings.keys() if spellings else '_',
                                    lemma, g.base_pos, m['words'], le.words)
        self.poses.update(addedPoses)
        if m['comments']:
            le.comments.extend(Line.splitComments(m['comments']))

    @staticmethod
    def procWords(lemmaSpellingsKeys, lemma, base_pos, wordsStr, wordsByPos, allowAsterisk = False):
        if lemma is None:
            words = [[]]
        else:
            words = [[lemma]]
        words += _splitWords(wordsStr, lemmaSpellingsKeys, allowAsterisk)
        poses = posesFromList(base_pos, words, lambda w: w[0].word.endswith("'s"))
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
            si.print(out)
        out.write(': +')
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
            out.write(':')
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
            self.lines = [line.rstrip() for line in text.splitlines()]

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
            l = re.sub(r'^## ?','', l).rstrip()
            c.lines.append(l)
        return c

class WordEntry(SlotsDataClass):
    __slots__ = (
        'spellings',      # Spellings
        'word',           # str
        'entry_rank',     # str
        'duplicate',      # bool
        '_word_id',
    )
    def __init__(self, word = None, entry_rank = Default):
        self.spellings = None
        if word is not None:
            self.word = word
            self.entry_rank = entry_rank
            self.duplicate = False
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
    def parse(wstr, lemmaSpellingsKeys = None, allowAsterisk = False):
        if wstr == '-':
            return None
        if allowAsterisk and wstr in ("*", "*'", "*'s"):
            return WordEntry(wstr)
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

def _finalizeGroups(groups, conn = None):
    if conn:
        expected_spellings = tuple(sp for sp, in conn.execute("select spelling from spellings where spelling != '_' order by order_num"))
    else:
        expected_spellings = _spellings_ab

    filteredGroups = []
    for grp in groups:
        if not grp.lines:
            continue
        grp.finalize(expected_spellings)
        for le in grp.entries:
            le.finalize()
        filteredGroups.append(grp)

    return filteredGroups

def _createClusters(groups, clusterComments = None):
    if clusterComments is None:
        clusterComments = {}
    groupsByHeadword = defaultdict(list)
    clusterMapping = {}
    for grp in groups:
        groupsByHeadword[clusterKey(grp.headword)].append(grp)
        members = set()
        for lemma in grp.lemmas:
            w = clusterKey(lemma)
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

def _createClustersSimple(groups, clusterComments = None):
    if clusterComments is None:
        clusterComments = {}
    clusters = []
    for grp in groups:
        cls = Cluster()
        cls.groups = [grp]
        cls.comments = []
        for lemma in grp.lemmas:
            try:
                cls.comments.append(clusterComments.pop(clusterKey(lemma)))
            except KeyError:
                pass
        cls.finalize()
        clusters.append(cls)
    if clusterComments:
        _warn('unused cluster comments: {}'.format(', '.join(map(str, clusterComments.keys()))))
    return clusters

_dir = Path(__file__).parent.resolve()

__all__ = [sym for sym in globals().keys() if not sym.startswith('__')]

