from ._core import *

def combinePOS(conn):
    conn.executescript((_dir / 'combine_pos.sql').read_text())
    conn.executescript((_dir / 'post.sql').read_text())

def splitPOS(conn):
    conn.executescript((_dir / 'split_pos.sql').read_text())
    conn.executescript((_dir / 'post.sql').read_text())
