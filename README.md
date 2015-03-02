This is the git repository for SCOWL (and friends).

SCOWL (Spell Checker Oriented Word Lists) is a database of English
words that can be used to create word lists suitable for use in spell
checkers of various sizes and dialects (America, British (both -ise
and -ize) and Canadian). However, I am sure it will have numerous
other uses as well.

SCOWL is derived from many sources under a BSD compatible license.
The combined work is freely available under a [MIT-like]
(https://raw.githubusercontent.com/kevina/wordlist/master/scowl/Copyright) license.

To build the master word-lists and utilities, simply type in the top level
directory:

    make clean
    make

The above step is required before making the other builds below.

To build the aspell word-lists or hunspell dictionaries (you will need Aspell
0.60 installed):

    cd scowl/speller
    make clean
    make aspell [size=<number>]
    make hunspell [size=<number>]

See 'size' below. The aspell word-lists will be in scowl/speller/aspell.
Aspell dictionaries are made with aspell's 'create' command. See 'info
aspell' for more details and additional information on creating the required
'multi' files. The hunspell dictionaries and word-lists will be in
scowl/speller/hunspell.

To build a single hunspell dictionary AND a single aspell word-list:

    make clean
    make single cc=<country-code> [size=<number>] [accents=deaccent] [variant=-vN]

'cc'			Can be one of: US, CA, GB-ise, or GB-ize.
'size'			Can be one of: 10, 20, 35, 40, 50, 55, 60, 70, 80, 95.
'accents=deaccent'	If not given, both with and without accents are included.
'variant'		-v[1-3] Spelling variant level.
 See: scowl/README for more information about these values.

Note: to build multiple sizes together, remove the .aspell, .hunspell, or
.single file (respectively) between builds instead of using 'make clean'.

For more information please see our homepage at <http://wordlist.aspell.net>.
