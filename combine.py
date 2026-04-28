#!/usr/bin/python3

import time
import os
import shutil
import io
import sys

from contextlib import suppress

def usage():
    sys.stderr.write(f"usage: {sys.argv[0]} (create-db [--raw|--dont-combine-pos] [<db file>]) | sort\n")
    exit(1)

sys.path.insert(0, '.')
import libscowl
from libscowl import *
from libscowl import _importFromDB, _finalizeGroups, _createClusters, _mergeText

mergeFiles = (
    'data/extra',
    'data/signature',
    'data/coca',
    'data/coca_llm',
    'data/hacker',
)

adjustFiles = (
    'data/compounds',
    'data/variants',
    'data/fixes',
    'data/vn_fixes',
    'data/exclude',
)

if len(sys.argv) < 2:
    usage()

if sys.argv[1] == 'sort':
    for fn in adjustFiles:
        sortFileInPlace(files=[fn])
    for fn in mergeFiles:
        sortFileInPlace(files=[fn])
    exit(0)

if sys.argv[1] != 'create-db':
    usage()

idx = 2

rawMode = False
dontCombinePOS = False
if len(sys.argv) > idx and sys.argv[idx] == '--raw':
    rawMode = True
    dontCombinePOS = True
    idx += 1

if len(sys.argv) > idx and sys.argv[idx] == '--dont-combine-pos':
    dontCombinePOS = True
    idx += 1
if os.environ.get('SCOWL_OPTS', '') == 'dont-combine-pos':
    dontCombinePOS = True

dbfile = ''
if len(sys.argv) > idx:
    dbfile = sys.argv[idx]
    if dbfile.startswith('-'):
        usage()

if not dbfile:
    dbfile = os.environ.get('SCOWL_DB', '')
if not dbfile:
    dbfile = 'scowl.db'

t = None
def start(msg):
    global t
    t = time.monotonic()
    sys.stderr.write(msg)
    sys.stderr.write('... ')
    sys.stderr.flush()

def finish():
    global t
    sys.stderr.write(f"done ({time.monotonic()-t}s)\n")
    sys.stderr.flush()
    t = None

start("importing from scowl-pre.txt")
if DEBUG_SQL:
    conn = openDB("/tmp/scowl-pre.db", create=True)
else:
    conn = openDB(None)

CACHE_DIR = os.environ.get('SCOWL_CACHE', '')
if CACHE_DIR:
    CACHE_DIR = Path(CACHE_DIR)
else:
    CACHE_DIR = None

src = Path('data/scowl-pre.txt')
if CACHE_DIR:
    cached_txt = CACHE_DIR / 'scowl-pre.txt'
    cached_db = CACHE_DIR / 'scowl-pre.db'
    empty_db = CACHE_DIR / 'scowl-empty.db'
    empty_db_new = empty_db.with_suffix('.new')

    CACHE_DIR.mkdir(exist_ok=True)

    with libscowl.openDB(empty_db_new, create = True):
        pass

    try:
        changed = (empty_db.read_bytes() != empty_db_new.read_bytes() 
                   or src.read_bytes() != cached_txt.read_bytes())
    except FileNotFoundError:
        changed = True

    if changed:
        with open(src) as f:
            clusters = importText(f)
        shutil.copyfile(empty_db_new, cached_db)
        with openDB(cached_db) as c:
            exportToDB(clusters, c)
            c.backup(conn)
        del clusters
        shutil.copyfile(src, cached_txt)
        shutil.copyfile(empty_db_new, empty_db)
        sys.stderr.write(f"\nwrote to cache ({CACHE_DIR})\n")
    else:
        sys.stderr.write(f"\nreading from cache ({CACHE_DIR})\n")
        with openDB(cached_db) as c:
            c.backup(conn)

    os.remove(empty_db_new)

else:
    with open(src) as f:
        clusters = importText(f)
    exportToDB(clusters, conn)
    del clusters
finish()
del src

start("importing data/basic")
conn.execute("create temp table groups_to_del (group_id integer primary key);")
with open('data/basic') as f:
    for d in roughParse(f):
        if d.base_pos in ('d', 'pn'):
            poses = "'d','aj','av','a','n','pn',''"
        elif d.base_pos in ('c', 'pp'):
            poses = "'d','a','av','c','pp',''"
        elif d.base_pos == 'n' and d.pos_class in ('num', 'ord', 'number', 'ordinal'):
            poses = "'n','a','av','aj'"
        else:
            poses = f"'{d.base_pos}',''"
        conn.execute("insert or ignore into groups_to_del "
                     f"select group_id from entries where word = ? and base_pos in ({poses})", (d.word,))
    conn.execute("insert or ignore into groups_to_del "
                 "select group_id from lemmas where lemma in ('so', 'sol')")
removeEntries(conn)
conn.commit()
with open('data/basic') as f:
    mergeEntries(conn, f)
finish()

start('data/compounds-auto')
with open('data/compounds-auto') as f:
    adjustEntries(conn, f, strict = False, ignoreErrors = True, replaceComments = False, simplifyScowlInfo=False,
                  groupComment = 'Compound variant levels are a best guess based on freq and other related info.')
finish()

for fn in adjustFiles:
    start(fn)
    with open(fn) as f:
        adjustEntries(conn, f, simplifyScowlInfo=False)
    finish()

for fn in mergeFiles:
    start(fn)
    with open(fn) as f:
        mergeEntries(conn, f)
    finish()

if not rawMode:
    start("simplify SCOWL info")
    tagsToRemove = "'[12dicts]','[3esl]','[enable]','[ospdadd]','[2dicts]','[nopos]','[census]'"
    conn.execute("insert into scowl_data (size,category,region,tag,group_id,pos)"
                 "select size,category,region,'',group_id,pos "
                 f"  from scowl_data where tag in ({tagsToRemove}) "
                 "on conflict do nothing")
    conn.execute(f"delete from scowl_data where tag in ({tagsToRemove})")
    
    conn.execute("delete from scowl_data "
                 "where (size,category,region,tag,group_id,pos) "
                 "  in (select size,category,region,tag,group_id,pos from scowl_data_cleanup)")
    finish()

if not dontCombinePOS:
    start("combine POS")
    combinePOS(conn)
    finish()

start("finalizing DB")
finalizeDB(conn)
final = openDB(dbfile, copyFrom=conn)
final.close()
finish()
