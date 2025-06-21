#!/usr/bin/python3

import time
import os
import shutil
import io
import sys

from contextlib import suppress

def usage():
    sys.stderr.write(f"usage: {sys.argv[0]} {{create-db,sort}}\n")
    exit(1)

sys.path.insert(0, '.')
import libscowl
from libscowl import *
from libscowl import _importFromDB, _finalizeGroups, _createClusters, _mergeText

adjustFiles = (
    'data/compounds',
    'data/variants',
    'data/fixes',
    'data/exclude',
)
mergeFiles = (
    ('data/extra', '[extra]'),
    ('data/signature', '[+]'),
)

action = None

if len(sys.argv) == 2:
    if sys.argv[1] in ('create-db','sort'):
        action = sys.argv[1]
    else:
        usage()
else:
    usage()

if action == 'sort':
    for fn in adjustFiles:
        sortFileInPlace('adjust', files=[fn])
    for fn, _ in mergeFiles:
        sortFileInPlace('merge', files=[fn])
    exit(0)

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
conn = openDB(None)
with open('data/scowl-pre.txt') as f:
    clusters = importText(f)
exportToDB(clusters, conn)
finish()
del clusters

start("importing data/basic")
with open('data/basic') as f:
    for d in roughParse(f):
        if d.base_pos in ('d', 'pn'):
            poses = "'d','aj','av','a','n','pn',''"
        elif d.base_pos in ('c', 'pp'):
            poses = "'d','a','av','c','pp',''"
        elif d.base_pos == 'n' and d.pos_class in ('num', 'ord', 'number', 'ordinal'):
            poses = "'n','a','av','aj'"
        else:
            poses = f"'{d.base_pos}',''";
        conn.execute("delete from groups "
                     f"where (group_id) in (select group_id from entries where word = ? and base_pos in ({poses}))", (d.word,))
    conn.execute("delete from groups "
                 "where (group_id) in (select group_id from lemmas where lemma in ('so', 'sol'))")
conn.commit()
with open('data/basic') as f:
    mergeEntries(conn, f, onConflict = 'error')
finish()

for fn in adjustFiles:
    start(fn)
    with open(fn) as f:
        adjustEntries(conn, f, simplifyScowlInfo=False)
    finish()

for fn, tag in mergeFiles:
    start(fn)
    with open(fn) as f:
        mergeEntries(conn, f, tag = tag)
    finish()

start("simplify SCOWL info")
conn.execute("delete from scowl_data "
             "where (level,category,region,tag,group_id,pos) "
             "  in (select level,category,region,tag,group_id,pos from scowl_data_cleanup)")
finish()

start("combine POS")
combinePOS(conn)
finish()

start("finalizing DB")
finalizeDB(conn)
final = openDB("scowl.db", copyFrom=conn)
final.close()
finish()

