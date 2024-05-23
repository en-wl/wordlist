import argparse

from . import *

def createDB(args):
    conn = openDB(args.db, create = True)
    clusters = importText(sys.stdin)
    exportToDB(clusters, conn)
    conn.close()

def exportDB(args):
    conn = openDB(args.db)
    clusters = importFromDB(conn)
    exportAsText(clusters, conn, sys.stdout)

def printWordList(args):
    conn = openDB(args.db)
    kwargs = {k: v for k,v in args.__dict__.items() if k not in ('db', 'func')}
    for w in sorted(getWords(conn, **kwargs)):
        print(w)
    
def lst(arg):
    return [v.strip() for v in arg.split(',')]

class Lst(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        lst = [v.strip() for v in values.split(',')]
        cls = Exclude if option_string.endswith('-to-exclude') else Include
        noDefault = True if 'no-default' in lst else False
        lst = cls(*(v for v in lst if v != 'no-default'), noDefault = noDefault)
        setattr(namespace, self.dest, lst)

def strOrBool(arg):
    if arg.lower() in ('t', 'true'):
        return True
    elif arg.lower() in ('f', 'false'):
        return False
    return arg

parser = argparse.ArgumentParser('libscowl')
subparsers = parser.add_subparsers()

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
p.add_argument('db', nargs='?', default='scowl.db')

p = subparsers.add_parser('word-list',
                          aliases=['wl'],
                          help='export a wordlist to stdout',
                          epilog='''
LIST arguments expect a comma separated list and generally include the default
value.  To not include the default value add 'no-default' as one if the list
members.
''',
                          allow_abbrev=False,
                          argument_default=argparse.SUPPRESS)
p.set_defaults(func=printWordList)
p.add_argument('db', nargs='?', default='scowl.db')

p.add_argument('--size', type=int, metavar='INT')
p.add_argument('--spellings', type=lst, metavar='LIST')
p.add_argument('--regions', type=lst, metavar='LIST')
p.add_argument('--variant-level', choices=[*variantFromSymbol.keys()], dest='variantLevel')
p.add_argument('--poses', '--poses-to-exclude', action=Lst, dest='poses', metavar='LIST')
p.add_argument('--pos-classes', '--pos-classes-to-exclude', action=Lst, dest='posClasses', metavar='LIST')
p.add_argument('--pos-categories', '--pos-categories-to-exclude', action=Lst, dest='posCategories', metavar='LIST')
p.add_argument('--categories', action=Lst, dest='categories', metavar='LIST')
p.add_argument('--tags', '--tags-to-exclude', action=Lst, dest='tags', metavar='LIST')
p.add_argument('--usage-notes', '--usage-notes-to-exclude', action=Lst, dest='usageNotes', metavar='LIST')

p.add_argument('--no-word-filter', action='store_false', dest='useWordFilter')

p.add_argument('--space', action='store_true')
p.add_argument('--hyphen', action='store_true')
p.add_argument('--dot', type=strOrBool, choices=('strip', True, False))
p.add_argument('--digits', action='store_true')
p.add_argument('--special', action='store_true')
p.add_argument('--apostrophe', type=strOrBool, choices=('middle', True, False))

p.add_argument('--deaccent', action='store_true')

args = parser.parse_args()
if not hasattr(args, 'func'):
    parser.print_usage()
    exit(1)
args.func(args)
