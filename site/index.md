---
layout: page
---

SCOWL (Spell Checker Oriented Word Lists) and Friends is a database of
information on English words useful for creating high-quality word
lists suitable for use in spell checkers of most dialects of English.
The database primary contains information on how common a word is,
differences in spelling between the dialects if English, spelling
variant information, and (basic) part-of-speech and inflection
information.

SCOWL itself is a compilation of the information in the database into
a set of simple word lists that can be combined to create speller
dictionaries of various sizes and dialects (American, British (both
-ise and -ize), Canadian and Australian).

[View readme](/scowl-readme).
Download Version 2020.12.07 as: [tar.gz](http://downloads.sourceforge.net/wordlist/scowl-2020.12.07.tar.gz) (Unix EOL),
[zip](http://downloads.sourceforge.net/wordlist/scowl-2020.12.07.zip) (DOS/Windows EOL).
[Get source](http://github.com/en-wl/wordlist).

[Premade dictionaries](dicts) are available for Hunspell, Aspell, and
as plain wordlists.  If none of those dictionaries are suitable for
your needs a simple web app is available to 
[create a customized wordlist](http://app.aspell.net/create).

A simple web app is also available to [check if a word is in
SCOWL](http://app.aspell.net/lookup).  This app also assigns a score
that indicates if a word should or should not be considered for
inclusion based on its frequency in Google Book's corpus (1980-2008).
In addition, a [report sorted by
frequency](http://app.aspell.net/lookup-freq) is available that also
looks for similar more common words to help determine if adding the
less common word might cause a problem.

[VarCon](varcon) (Variant Conversion) is the primary source of
spelling differences and variant information.  It can also be used to
convert between American, British, Canadian and Australian spellings.

Alan Beale [12Dicts](12dicts) is another main source of information in
SCOWL.  It contains a variety of lists, of different sizes and
characteristics that are used by SCOWL.

The [2of12id.txt](alt12dicts-infl-readme) file, in the alternative
version of 12Dicts, is the primary source of part-of-speech and
inflection information, however it is limited to common words.
[AGID](agid-readme) contains more words but also likely to contain
more errors.

The SCOWL collection contains many [others pieces of
information](other).  Most of these are in the forms of other word
lists.

