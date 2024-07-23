import os
import sys
import argparse

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
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('func')}
    libscowl.filterDB(**kwargs)

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

progName = os.path.basename(sys.argv[0])
if progName == '__main__.py':
    progName = 'libscowl'
parser = argparse.ArgumentParser(progName)
subparsers = parser.add_subparsers()

def addParser(title, **args):
    p = subparsers.add_parser(title,
                              allow_abbrev=False,
                              argument_default=argparse.SUPPRESS,
                              **args)
    return p

p = subparsers.add_parser('init-db',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=initDB)
p.add_argument('db', nargs='?', default='scowl.db')


p = subparsers.add_parser('create-db',
                          help='create the database from stdin',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=createDB)
p.add_argument('db', nargs='?', default='scowl.db')


p = subparsers.add_parser('export-db',
                          allow_abbrev=False,
                          help='export the database to stdout',
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=exportDB)
p.add_argument('--show-clusters', action='store_true', default=False)
p.add_argument('db', nargs='?', default='scowl.db')


p = subparsers.add_parser('combine-pos',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=combinePOS)
p.add_argument('db', nargs='?', default='scowl.db')


p = subparsers.add_parser('split-pos',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=splitPOS)
p.add_argument('db', nargs='?', default='scowl.db')


p = subparsers.add_parser('word-list',
                          aliases=['wl'],
                          help='export a wordlist to stdout',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=printWordList)
p.add_argument('db', nargs='?', default='scowl.db')

def addQueryArguments(p, defaults):
    def addArg(*flags, **args):
        if flags[0] in defaults:
            args['help'] = f"{args.get('help', '')} (default: {defaults[flags[0]]})"
        p.add_argument(*flags, **args)
    addArg('--size', type=int, metavar='INT',
           help='max scowl size')
    addArg('--spellings', type=lst, metavar='LIST',
           help=f"any of: {', '.join(SPELLINGS[1:])}")
    addArg('--regions', type=lst, metavar='LIST',
           help=f"any of: {', '.join(REGIONS[1:])}")
    addArg('--variant-level', metavar='CHAR', choices=[*variantFromSymbol.keys(),*map(str, range(0,10))], dest='variantLevel',
           help=f"one of: {','.join(variantFromSymbol.keys())},0-9")
    addArg('--variant-levels', action=VariantLevels, dest='variantLevels', metavar='LIST')
    addArg('--poses', '--wo-poses', action=Lst, dest='poses', metavar='LIST')
    addArg('--pos-classes', '--wo-pos-classes', action=Lst, dest='posClasses', metavar='LIST')
    addArg('--pos-categories', '--wo-pos-categories', action=Lst, dest='posCategories', metavar='LIST',
           help=f"any of: {', '.join(POS_CATEGORIES[1:])}")
    addArg('--categories', action=Lst, dest='categories', metavar='LIST')
    addArg('--tags', '--wo-tags', action=Lst, dest='tags', metavar='LIST')
    addArg('--usage-notes', '--wo-usage-notes', action=Lst, dest='usageNotes', metavar='LIST')

    p.epilog='''
LIST arguments expect a comma separated list and generally include the default
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
p.add_argument('--nosuggest', action=NoSuggest, dest='nosuggest', metavar='LIST', const='', nargs='?',
               help=f"any of: vulgar-1,2,3 or offensive-1,2,3; if the flag is specified but no values are given defaults to: vulgar-1&2 and offensive-1&2")
p.add_argument('--nosuggest-suffix', type=str, dest='nosuggestSuffix', metavar='STR',
               help=f"default: /!")

p = addParser('filter',
              help='filter database')
p.set_defaults(func=filterDB)
p.add_argument('filterType', choices=('by-line', 'by-group', 'by-cluster'))
p.add_argument('orig', nargs='?', default='scowl.db')
p.add_argument('new', nargs='?', default='scowl-filtered.db')
addQueryArguments(p, {})
p.add_argument('--variants-only', action='store_true', dest='variantsOnly')
p.add_argument('--simplify', type=lst, metavar='LIST', help="any of: size, category, region, tag")


args = parser.parse_args()
if not hasattr(args, 'func'):
    parser.print_usage()
    exit(1)
args.func(args)
