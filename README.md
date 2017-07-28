This is the git repository for SCOWL (and friends).

SCOWL (Spell Checker Oriented Word Lists) is a database of English
words that can be used to create word lists suitable for use in spell
checkers of various sizes and dialects (America, British (both -ise
and -ize), Canadian and Australian). However, I am sure it will have
numerous other uses as well.

SCOWL is derived from many sources under a BSD compatible license.
The combined work is freely available under a
[MIT-like](https://raw.githubusercontent.com/kevina/wordlist/master/scowl/Copyright)
license.

To build simply type:

    make

To build the aspell and hunspell dictionaries (you will need Aspell
0.60 installed):

    cd scowl/speller
    make aspell
    make hunspell

For more information please see our homepage at <http://wordlist.aspell.net>.
