import os
import sys
import argparse
from argparse import SUPPRESS,RawDescriptionHelpFormatter
from pathlib import Path
from tempfile import NamedTemporaryFile

import libscowl
from libscowl import variantFromSymbol, SPELLINGS, REGIONS, POS_CATEGORIES, Include, Exclude

def initDB(args):
    conn = libscowl.openDB(args.db, create = True)
    conn.close()

def createDB(args):
    conn = libscowl.openDB(args.db, create = True)
    clusters = libscowl.importText(sys.stdin)
    libscowl.exportToDB(clusters, conn)
    conn.close()

def exportDB(args):
    conn = libscowl.openDB(args.db)
    clusters = libscowl.importFromDB(conn)
    libscowl.exportAsText(clusters, conn, sys.stdout, showClusters = args.show_clusters)

def searchDB(args):
    conn = libscowl.openDB(args.db)
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'func')}
    clusters = libscowl.searchDB(conn, **kwargs)
    libscowl.exportAsText(clusters, conn, sys.stdout, showExtraInfo = False, showClusters = kwargs.get('byCluster', False))

def adjust(args):
    conn = libscowl.openDB(args.db)
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'func')}
    preview = kwargs.pop('preview')
    if preview:
        libscowl.adjustEntries(conn, sys.stdin, preview = True, **kwargs)
    else:
        libscowl.adjustEntries(conn, sys.stdin, preview = False, **kwargs)
        conn.executescript((libscowl._dir / 'post.sql').read_text())

def merge(args):
    conn = libscowl.openDB(args.db)
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'func')}
    preview = kwargs.pop('preview')
    if preview:
        libscowl.mergeEntries(conn, sys.stdin, preview = True, **kwargs)
    else:
        libscowl.mergeEntries(conn, sys.stdin, preview = False, **kwargs)
        conn.executescript((libscowl._dir / 'post.sql').read_text())

def sortFile(args):
    if args.replace:
        destFile = Path(args.files[0]).resolve(strict=True)
        if not destFile.is_file():
            raise OSError(None, 'Not a normal file', str(destFile))
        fp = NamedTemporaryFile(mode='w', delete = False, prefix=".tmp", dir=destFile.parent)
        try:
            libscowl.sortFile(inFiles = args.files, outfh = fp, fileFormat=args.fileFormat, indent=args.indent)
            fp.close()
            os.replace(fp.name, destFile)
        except:
            fp.close()
            try:
                os.remove(fp.name)
            except FileNotFoundError:
                pass
            raise
    else:
        libscowl.sortFile(inFiles = args.files if args.files else None, fileFormat=args.fileFormat, indent=args.indent)

def combinePOS(args):
    conn = libscowl.openDB(args.db)
    libscowl.combinePOS(conn)

def splitPOS(args):
    conn = libscowl.openDB(args.db)
    libscowl.splitPOS(conn)

def printWordList(args):
    conn = libscowl.openDB(args.db)
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'func')}
    words = sorted(libscowl.getWords(conn, **kwargs))
    for w in words:
        print(w)

def filterDB(args):
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'target', 'export', 'func', 'show_clusters')}
    conn = libscowl.filterDB(orig=args.db, new=getattr(args, 'target', None),  **kwargs)
    if getattr(args, 'export', False):
        clusters = libscowl.importFromDB(conn)
        libscowl.exportAsText(clusters, conn, sys.stdout, showClusters = getattr(args, 'show_clusters', False))
    conn.close()

def lst(arg):
    return [v.strip() for v in arg.split(',')]

class Lst(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        lst = [v.strip() for v in values.split(',')]
        cls = Exclude if option_string.startswith('--wo-') else Include
        noDefault = True if 'no-default' in lst else False
        lst = cls(*(v for v in lst if v != 'no-default'), noDefault = noDefault)
        setattr(namespace, self.dest, lst)

def variantNum(s):
    num = int(s)
    if num < 0 or num > 10:
        raise ValueError('variant level must be between 0-9 (inclusive)')
    return num

class VariantLevels(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        levels = Include()
        for v in values.split(','):
            r = [variantNum(num) for num in v.split('-', 1)]
            if len(r) == 1:
                levels.add(r[0])
            else:
                levels.update(range(r[0], r[1]+1))
        setattr(namespace, self.dest, levels)

class NoSuggest(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values == '':
            lst = ()
        else:
            lst = set(v.strip() for v in values.split(','))
        setattr(namespace, self.dest, lst)

def strOrBool(arg):
    if arg.lower() in ('t', 'true'):
        return True
    elif arg.lower() in ('f', 'false'):
        return False
    return arg

SCOWL_DB = os.environ.get('SCOWL_DB', '')
if not SCOWL_DB:
    SCOWL_DB = 'scowl.db'

progName = os.path.basename(sys.argv[0])
if progName == '__main__.py':
    progName = 'libscowl'
parser = argparse.ArgumentParser(progName)
parser.add_argument('--db', metavar='<file>', default=SCOWL_DB,
                    help=f"database file to use (default scowl.db); also SCOWL_DB")

subparsers = parser.add_subparsers(metavar='<command>')

def addParser(title, **args):
    p = subparsers.add_parser(title,
                              allow_abbrev=False,
                              argument_default=SUPPRESS,
                              formatter_class=RawDescriptionHelpFormatter,
                              **args)
    return p

def addDbArgument(p):
    p.add_argument('--db', metavar='<file>',
                   help=f"database file to use (default scowl.db); also SCOWL_DB")

p = addParser('import',
              help='create the database from stdin')
p.set_defaults(func=createDB)
addDbArgument(p)


p = addParser('export',
              help='export the database to stdout')
p.set_defaults(func=exportDB)
addDbArgument(p)
def addExportArguments(p):
    p.add_argument('--show-clusters', action='store_true', default=False)
addExportArguments(p)


p = addParser('word-list',
              aliases=['wl'],
              help='export a wordlist to stdout')
p.set_defaults(func=printWordList)
addDbArgument(p)

def addQueryArguments(p, defaults):
    def addArg(*flags, **args):
        if flags[0] in defaults:
            args['help'] = f"{args.get('help', '')} (default: {defaults[flags[0]]})"
        p.add_argument(*flags, **args)
    addArg('--size', type=int, metavar='<int>',
           help='max scowl size')
    addArg('--spellings', type=lst, metavar='<list>',
           help=f"any of: {', '.join(SPELLINGS[1:])}")
    addArg('--regions', type=lst, metavar='<list>',
           help=f"any of: {', '.join(REGIONS[1:])}")
    variantSymbolsStr = ','.join(symbol if symbol.isalnum() else f"'{symbol}'" for symbol in variantFromSymbol.keys())
    addArg('--variant-level', metavar='<char>', choices=[*variantFromSymbol.keys(),*map(str, range(0,10))], dest='variantLevel',
           help=f"one of: {variantSymbolsStr},0-9")
    addArg('--variant-levels', action=VariantLevels, dest='variantLevels', metavar='<list>')
    addArg('--poses', '--wo-poses', action=Lst, dest='poses', metavar='<list>')
    addArg('--pos-classes', '--wo-pos-classes', action=Lst, dest='posClasses', metavar='<list>')
    addArg('--pos-categories', '--wo-pos-categories', action=Lst, dest='posCategories', metavar='<list>',
           help=f"any of: {', '.join(POS_CATEGORIES[1:])}")
    addArg('--categories', action=Lst, dest='categories', metavar='<list>')
    addArg('--tags', '--wo-tags', action=Lst, dest='tags', metavar='<list>')
    addArg('--usage-notes', '--wo-usage-notes', action=Lst, dest='usageNotes', metavar='<list>')

    p.epilog='''
<list> arguments expect a comma separated list and generally include the default
value.  To not include the default value add 'no-default' as one if the list
members.
'''

def addFilterArguments(p):
    p.add_argument('--no-word-filter', action='store_false', dest='useWordFilter')

    p.add_argument('--space', action='store_true')
    p.add_argument('--hyphen', action='store_true')
    p.add_argument('--dot', type=strOrBool, choices=('strip', True, False))
    p.add_argument('--digits', action='store_true')
    p.add_argument('--special', action='store_true')
    p.add_argument('--apostrophe', type=strOrBool, choices=('middle', True, False))

    p.add_argument('--deaccent', action='store_true')

addQueryArguments(p, {'--size': 60, '--spellings': 'A', '--variant-level': '.'})
addFilterArguments(p)
p.add_argument('--nosuggest', action=NoSuggest, dest='nosuggest', metavar='<list>', const='', nargs='?',
               help=f"any of: vulgar-1,2,3 or offensive-1,2,3; if the flag is specified but no values are given defaults to: vulgar-1&2 and offensive-1&2")
p.add_argument('--nosuggest-suffix', type=str, dest='nosuggestSuffix', metavar='<str>',
               help=f"default: /!")


p = addParser('search',
              help='search the database')
p.set_defaults(func=searchDB)
addDbArgument(p)
p.add_argument('--by-cluster', action='store_true', default=False, dest='byCluster')
p.add_argument('words', nargs='+', metavar='<word>',
               help="word to search for")


p = addParser('filter',
              help='filter database')
p.set_defaults(func=filterDB)
addDbArgument(p)
p.add_argument('filterType', choices=('by-line', 'by-group', 'by-cluster'))
g = p.add_mutually_exclusive_group(required=True)
g.add_argument('--target', metavar='<file>',
               help='store the resulting database in <file>')
g.add_argument('--export', action='store_true',
               help='export the results to stdout')
del g
addExportArguments(p)
addQueryArguments(p, {})
p.add_argument('--variants-only', action='store_true', dest='variantsOnly')
p.add_argument('--simplify', type=lst, metavar='<list>', help="any of: size, category, region, tag")


p = addParser('combine-pos',
              help='combine n/v and aj/av groups when possible')
p.set_defaults(func=combinePOS)


p = addParser('split-pos',
              help='split groups with combined pos')
p.set_defaults(func=splitPOS)
addDbArgument(p)


p = addParser('init-db',
              help='create an empty database')
p.set_defaults(func=initDB)
addDbArgument(p)


p = addParser('adjust',
              help='add, remove, or adjust entries')
p.set_defaults(func=adjust)
addDbArgument(p)
p.add_argument('--preview', action='store_true', default=False, dest='preview')
p.add_argument('--ignore-errors', action='store_true', default=False, dest='ignoreErrors',
               help='ignore errors when possible by skipping the group')
p.add_argument('--no-cleanup', action='store_false', dest='simplifyScowlInfo',
               help="simplify scowl info")
p.add_argument('--cleanup',  action='store_true', dest='simplifyScowlInfo', help=SUPPRESS)


p = addParser('merge',
              help='add new entries',
              description='''
Add new entries from stdin to the database.  By default new data is merged
with existing groups with the same lemma/pos/defn_note.  If --on-conflict is
'replace' than the data from stdin will replace the existing group.  If --tag
is used that that tag will be added to all new entries.''')
p.set_defaults(func=merge)
addDbArgument(p)
p.add_argument('--preview', action='store_true', default=False, dest='preview')
#p.add_argument('--ignore-errors', action='store_true', default=False, dest='ignoreErrors')
p.add_argument('--on-conflict', default = 'merge', dest='onConflict', choices=['merge', 'replace', 'error'])
p.add_argument('--tag', dest='tag', metavar = '<tag>',
               help='scowl tag to add to all new entries')


p = addParser('sort',
              help='sort and combine adjust/merge files',
              description='''
Sort and combine adjust/merge files to stdout, or inplace if the `--replace`
option is used.

''')
p.set_defaults(func=sortFile)
p.add_argument('--indent', action='store_true', default=False, dest='indent')
p.add_argument('--replace', action='store_true', default=False, dest='replace',
               help='replace the first file with the combined result of all the files')
p.add_argument('fileFormat', choices=['adjust','merge'])
p.add_argument('files', metavar='<file>', nargs='*', default=[])

args = parser.parse_args()
if not hasattr(args, 'func'):
    parser.print_usage()
    exit(1)

try:
    args.func(args)
except BrokenPipeError:
    exit(1)
