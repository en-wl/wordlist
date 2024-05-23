import sys

from ._common import *
from ._constdata import *

def populateConstDataFromDB(conn):

    posInfo.clear()
    for r in conn.execute("select * from poses order by order_num"):
        posInfo[r['pos']] = PosInfo(
            order_num = r['order_num'],
            name = r['pos'],
            base_pos = r['base_pos'],
            category = r['pos_category'],
            descr = r['name'],
            note = r['note'],
            extra_info = r['extra_info'],
        )

    basePosInfo.clear()
    for r in conn.execute("select * from base_poses order by order_num"):
        basePosInfo[r['base_pos']] = BasePosInfo(
            order_num = r['order_num'],
            name = r['base_pos'],
            category = r['pos_category'],
            lemma_pos = r['lemma_pos'],
            descr = r['descr'],
            extra_info = r['extra_info'],
        )

    variantAsSymbol.clear()
    variantFromSymbol.clear()
    for r in conn.execute("select * from variant_levels"):
        variantAsSymbol[r['variant_level']] = r['variant_symbol']
        variantFromSymbol[r['variant_symbol']] = r['variant_level']

    spellingInfo.clear()
    for r in conn.execute("select * from spellings order by order_num"):
        spellingInfo[r['spelling']] = SpellingInfo(
            order_num = r['order_num'],
            spelling = r['spelling'],
            region = r['region'],
            descr = r['spelling_descr']
        )

    global SPELLINGS, REGIONS
    SPELLINGS = tuple(sp for (sp,) in conn.execute("select spelling from spellings order by order_num"));
    REGIONS = tuple(rgn for (rgn,) in conn.execute("select region from regions order by order_num"));

_moduleHeader = """
# generated file, must be kept in sync with constdata.sql

from ._common import SlotsDataClass

class PosInfo(SlotsDataClass):
    __slots__ = ('order_num', 'name', 'base_pos', 'category', 'descr', 'note', 'extra_info')

class BasePosInfo(SlotsDataClass):
    __slots__ = ('order_num', 'name', 'lemma_pos', 'category', 'descr', 'extra_info')

class SpellingInfo(SlotsDataClass):
    __slots__ = ('order_num', 'spelling', 'region', 'descr')

"""

_moduleFooter = """
"""

def exportConstData(out=None):
    if out is None:
        out = sys.stdout

    from pprint import pprint

    out.write(_moduleHeader)

    out.write('posInfo = {\n')
    for k, v in posInfo.items():
        out.write(f'  {k!r}: {v!r},\n')
    out.write('}\n\n')

    out.write('basePosInfo = {\n')
    for k, v in basePosInfo.items():
        out.write(f'  {k!r}: {v!r},\n')
    out.write('}\n\n')

    out.write(f'variantAsSymbol = {variantAsSymbol!r}\n\n')
    
    out.write(f'variantFromSymbol = {variantFromSymbol!r}\n\n')

    out.write('spellingInfo = {\n')
    for k, v in spellingInfo.items():
        out.write(f'  {k!r}: {v!r},\n')
    out.write('}\n\n')

    out.write(f'SPELLINGS = {SPELLINGS!r}\n\n')

    out.write(f'REGIONS = {REGIONS!r}\n\n')
    
    out.write(_moduleFooter)

