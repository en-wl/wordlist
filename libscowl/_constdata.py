
# generated file, must be kept in sync with constdata.sql

from ._common import SlotsDataClass

class PosInfo(SlotsDataClass):
    __slots__ = ('order_num', 'name', 'base_pos', 'descr', 'note', 'extra_info')

class BasePosInfo(SlotsDataClass):
    __slots__ = ('order_num', 'name', 'lemma_pos', 'category', 'descr', 'extra_info')

class SpellingInfo(SlotsDataClass):
    __slots__ = ('order_num', 'spelling', 'region', 'descr')

posInfo = {
  '?': PosInfo(order_num=1, name='?', base_pos='', descr='unknown', note=None, extra_info=None),
  'n0': PosInfo(order_num=4, name='n0', base_pos='n', descr='noun', note=None, extra_info=None),
  'ns': PosInfo(order_num=5, name='ns', base_pos='n', descr='noun: plural', note=None, extra_info=None),
  'nss': PosInfo(order_num=6, name='nss', base_pos='n', descr='noun: plural of plural', note=None, extra_info=None),
  'np': PosInfo(order_num=7, name='np', base_pos='n', descr='noun: possessive', note=None, extra_info=None),
  'nsp': PosInfo(order_num=8, name='nsp', base_pos='n', descr='noun: plural possessive', note=None, extra_info=None),
  'nssp': PosInfo(order_num=9, name='nssp', base_pos='n', descr='noun: plural of plural possessive', note=None, extra_info=None),
  'v0': PosInfo(order_num=10, name='v0', base_pos='v', descr='verb', note=None, extra_info=None),
  'vd': PosInfo(order_num=11, name='vd', base_pos='v', descr='verb: past tense (-ed)', note=None, extra_info=None),
  'vd2': PosInfo(order_num=12, name='vd2', base_pos='v', descr='verb: past tense plural (were)', note=None, extra_info=None),
  'vn': PosInfo(order_num=13, name='vn', base_pos='v', descr='verb: past participle (-en)', note=None, extra_info=None),
  'vg': PosInfo(order_num=14, name='vg', base_pos='v', descr='verb: present participle (-ing)', note=None, extra_info=None),
  'vs': PosInfo(order_num=15, name='vs', base_pos='v', descr='verb: present tense (-s)', note=None, extra_info=None),
  'vs2': PosInfo(order_num=16, name='vs2', base_pos='v', descr='verb: present tense second-person singular (are)', note=None, extra_info=None),
  'vs3': PosInfo(order_num=17, name='vs3', base_pos='v', descr='verb: present tense third-person singular (is)', note=None, extra_info=None),
  'vs4': PosInfo(order_num=18, name='vs4', base_pos='v', descr='verb: present tense plural (are)', note=None, extra_info=None),
  'm0': PosInfo(order_num=19, name='m0', base_pos='m', descr='noun/verb', note='n0 or v0', extra_info=None),
  'ms': PosInfo(order_num=20, name='ms', base_pos='m', descr='noun/verb: (-s)', note='ns or vs', extra_info=None),
  'aj0': PosInfo(order_num=21, name='aj0', base_pos='aj', descr='adjective', note=None, extra_info=None),
  'aj1': PosInfo(order_num=22, name='aj1', base_pos='aj', descr='adjective: comparative (-er)', note=None, extra_info=None),
  'aj2': PosInfo(order_num=23, name='aj2', base_pos='aj', descr='adjective: superlative (-est)', note=None, extra_info=None),
  'av0': PosInfo(order_num=24, name='av0', base_pos='av', descr='adverb', note=None, extra_info=None),
  'av1': PosInfo(order_num=25, name='av1', base_pos='av', descr='adverb: comparative (-er)', note=None, extra_info=None),
  'av2': PosInfo(order_num=26, name='av2', base_pos='av', descr='adverb: superlative (-est)', note=None, extra_info=None),
  'a0': PosInfo(order_num=27, name='a0', base_pos='a', descr='adjective/adverb', note='aj0 or av0', extra_info=None),
  'a1': PosInfo(order_num=28, name='a1', base_pos='a', descr='adjective/adverb: comparative (-er)', note='aj1 or av1', extra_info=None),
  'a2': PosInfo(order_num=29, name='a2', base_pos='a', descr='adjective/adverb: superlative (-est)', note='aj2 or av2', extra_info=None),
  'pn0': PosInfo(order_num=30, name='pn0', base_pos='pn', descr='pronoun', note=None, extra_info=None),
  'pn1': PosInfo(order_num=31, name='pn1', base_pos='pn', descr='pronoun: objective (you/him/her/...)', note=None, extra_info=None),
  'pns': PosInfo(order_num=32, name='pns', base_pos='pn', descr='pronoun: plural', note=None, extra_info=None),
  'pnd': PosInfo(order_num=33, name='pnd', base_pos='pn', descr='pronoun: determiner (your/his/her/...)', note=None, extra_info=None),
  'pnp': PosInfo(order_num=34, name='pnp', base_pos='pn', descr='pronoun: possessive (yours/his/hers/...)', note=None, extra_info=None),
  'pnr0': PosInfo(order_num=35, name='pnr0', base_pos='pn', descr='pronoun: reflexive singular (yourself/...)', note=None, extra_info=None),
  'pnrs': PosInfo(order_num=36, name='pnrs', base_pos='pn', descr='pronoun: reflexive plural (yourselves/...)', note=None, extra_info=None),
  'c': PosInfo(order_num=37, name='c', base_pos='c', descr='conjunction', note=None, extra_info=None),
  'pp': PosInfo(order_num=38, name='pp', base_pos='pp', descr='preposition', note=None, extra_info=None),
  'd': PosInfo(order_num=39, name='d', base_pos='d', descr='determiner', note=None, extra_info=None),
  'ds': PosInfo(order_num=40, name='ds', base_pos='d', descr='determiner: plural', note=None, extra_info=None),
  'd1': PosInfo(order_num=41, name='d1', base_pos='d', descr='determiner: comparative', note=None, extra_info=None),
  'd2': PosInfo(order_num=42, name='d2', base_pos='d', descr='determiner: superlative', note=None, extra_info=None),
  'i': PosInfo(order_num=43, name='i', base_pos='i', descr='interjection', note=None, extra_info=None),
  'abbr': PosInfo(order_num=44, name='abbr', base_pos='abbr', descr='abbreviation', note=None, extra_info=None),
  's': PosInfo(order_num=45, name='s', base_pos='s', descr='contraction', note=None, extra_info=None),
  'pre': PosInfo(order_num=46, name='pre', base_pos='pre', descr='prefix', note=None, extra_info=None),
  'suf': PosInfo(order_num=47, name='suf', base_pos='suf', descr='suffix', note=None, extra_info=None),
  'wp': PosInfo(order_num=48, name='wp', base_pos='wp', descr='multi-word part', note=None, extra_info=None),
  'we': PosInfo(order_num=49, name='we', base_pos='we', descr='multi-word ending', note=None, extra_info=None),
  'wes': PosInfo(order_num=50, name='wes', base_pos='we', descr='multi-word ending: plural', note=None, extra_info=None),
  'wep': PosInfo(order_num=51, name='wep', base_pos='we', descr='multi-word ending: possessive', note=None, extra_info=None),
  'weps': PosInfo(order_num=52, name='weps', base_pos='we', descr='multi-word ending: plural possessive', note=None, extra_info=None),
  'x': PosInfo(order_num=53, name='x', base_pos='x', descr='non word', note=None, extra_info='for example a roman numeral'),
}

basePosInfo = {
  '': BasePosInfo(order_num=1, name='', lemma_pos='?', category='', descr='unknown', extra_info=None),
  'n': BasePosInfo(order_num=2, name='n', lemma_pos='n0', category='', descr='noun', extra_info=None),
  'pl': BasePosInfo(order_num=3, name='pl', lemma_pos='ns', category='', descr='plural noun', extra_info=None),
  'v': BasePosInfo(order_num=4, name='v', lemma_pos='v0', category='', descr='verb', extra_info=None),
  'n_v': BasePosInfo(order_num=5, name='n_v', lemma_pos='m0', category='', descr='noun and verb', extra_info=None),
  'm': BasePosInfo(order_num=6, name='m', lemma_pos='m0', category='', descr='noun/verb', extra_info=None),
  'aj': BasePosInfo(order_num=7, name='aj', lemma_pos='aj0', category='', descr='adjective', extra_info=None),
  'av': BasePosInfo(order_num=8, name='av', lemma_pos='av0', category='', descr='adverb', extra_info=None),
  'aj_av': BasePosInfo(order_num=9, name='aj_av', lemma_pos='a0', category='', descr='adjective and adverb', extra_info=None),
  'a': BasePosInfo(order_num=10, name='a', lemma_pos='a0', category='', descr='adjective/adverb', extra_info=None),
  'pn': BasePosInfo(order_num=11, name='pn', lemma_pos='pn0', category='', descr='pronoun', extra_info=None),
  'c': BasePosInfo(order_num=12, name='c', lemma_pos='c', category='', descr='conjunction', extra_info=None),
  'pp': BasePosInfo(order_num=13, name='pp', lemma_pos='pp', category='', descr='preposition', extra_info=None),
  'd': BasePosInfo(order_num=14, name='d', lemma_pos='d', category='', descr='determiner', extra_info=None),
  'i': BasePosInfo(order_num=15, name='i', lemma_pos='i', category='', descr='interjection', extra_info=None),
  'abbr': BasePosInfo(order_num=16, name='abbr', lemma_pos='abbr', category='special', descr='abbreviation', extra_info=None),
  's': BasePosInfo(order_num=17, name='s', lemma_pos='s', category='special', descr='contraction', extra_info=None),
  'pre': BasePosInfo(order_num=18, name='pre', lemma_pos='pre', category='nonword', descr='prefix', extra_info=None),
  'suf': BasePosInfo(order_num=19, name='suf', lemma_pos='suf', category='nonword', descr='suffix', extra_info=None),
  'wp': BasePosInfo(order_num=20, name='wp', lemma_pos='wp', category='wordpart', descr='multi-word part', extra_info=None),
  'we': BasePosInfo(order_num=21, name='we', lemma_pos='we', category='wordpart', descr='multi-word ending', extra_info=None),
  'x': BasePosInfo(order_num=22, name='x', lemma_pos='x', category='nonword', descr='non word', extra_info='for example a roman numeral'),
}

variantAsSymbol = {0: '', 1: '.', 2: '=', 3: '?', 4: 'v', 5: '~', 6: 'V', 7: '-', 8: '@', 9: 'x'}

variantFromSymbol = {'': 0, '.': 1, '=': 2, '?': 3, 'v': 4, '~': 5, 'V': 6, '-': 7, '@': 8, 'x': 9}

spellingInfo = {
  '_': SpellingInfo(order_num=1, spelling='_', region='', descr=''),
  'A': SpellingInfo(order_num=2, spelling='A', region='US', descr='American'),
  'B': SpellingInfo(order_num=3, spelling='B', region='GB', descr='British(ise)'),
  'Z': SpellingInfo(order_num=4, spelling='Z', region='GB', descr='British(ize)'),
  'C': SpellingInfo(order_num=5, spelling='C', region='CA', descr='Canadian'),
  'D': SpellingInfo(order_num=6, spelling='D', region='AU', descr='Australian'),
}

SPELLINGS = ('_', 'A', 'B', 'Z', 'C', 'D')

REGIONS = ('', 'US', 'GB', 'CA', 'AU')

POS_CATEGORIES = ('', 'nonword', 'special', 'wordpart')


