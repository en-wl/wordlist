Spell Checking Oriented Word Lists Version 2 (SCOWLv2)
======================================================

SCOWL (Spell Checker Oriented Word Lists) and Friends is a database of
information on English words useful for creating high-quality word lists
suitable for use in spell checkers of most dialects of English. The database
primary contains information on how common a word is, differences in spelling
between the dialects if English, spelling variant information, and (basic)
part-of-speech and inflection information.

The original SCOWL (SCOWLv1) was a compilation of the information in the
database into a set of simple word lists that can be combined to create
speller dictionaries of various sizes and dialects (American, British (both
-ise and -ize), Canadian and Australian).

SCOWLv2 instead combines all that information into a single text file and
SQLite3 database.  In order to keep the file size manageable and to avoid noise
entries the minimum SCOWL size is now 35 and the 95 size is not included.

The file includes part-of-speech (POS) and spelling variant information in one
place.

Unlike SCOWLv1, SCOWLv2 includes the proper spelling of abbreviations that
included the trailing dot.  It also includes words that were excluded from
SCOWLv1 such as hyphenated and open (i.e. with space) compound words, and
words with special symbols in them.

SCOWL is derived from many sources under a BSD compatible license. The
combined work is freely available under a MIT-like license.  See the file
Copyright for details.

SCOWLv2 is still a work in progress.  The 60 size should as of 2024-08-23
contain about the same set of words as SCOWLv1.  The processing of the source
data is completely different so the resulting wordlists are not the same.
Most of the changes I regard as corrections for improper handling of derived
forms or variants in SCOWLv1.  The handling of possessive forms have been
completely redone based partly on the noun category assigned by WordNet.  For
American English any new changes to non-possessive forms of words included in
speller dictionary have been accounted for and noted in the file
`misc/comp-60.txt`.  The 70 size should also be about the same but no attempt
has been made to verify this as of yet.

SCOWLv2 is generated from the the same sources that SCOWLv1 uses but via a far
more complicated, and unreleased, process.  At some point I will be be happy
with the results and the resulting file (`scowl.txt`) will be directly
editable.  However for now, I want the freedom to update the source scrips to
fix systematic errors so SCOWLv2 is distributed in a set of two files: the
result of the automatic process (`scowl-orig.txt`), and a patch file
(`patch`).


Requirements
------------

SCOWLv2 requires Python 3 and SQLite.  It is currently tested with Python 3.7
and SQLite 3.27.2.  Newer versions should work, older versions may work but
are not supported.

A Unix like environment is also required for now.


Basic Usage
-----------

In order to use SCOWL `scowl-orig.txt` must be combined with the patch file
(`patch`) to create `scowl.txt` and the a SQLite3 database file `scowl.db`.
To do both via the provided makefile simply type:

  make

To work with SCOWL use the `scowl` script provided in the root directory.
This script is a very thin wrapper around the `libscowl` python module.  The
module is not available on PyPI, but instead included with SCOWL.  This script
is meant to be run from the root directory of the SCOWL distribution.

To extract wordlists from the database use:

    ./scowl word-list scowl.db > wl.txt

Which will create a word list that corresponds to the default dictionary size
and variant level used when creating spell-checkers dictionaries, except that
dialectic marks (i.e. accents) are preserved.  To remove then marks use:

    ./scowl word-list scowl.db --deaccent > wl.txt

The default word filter strips the trailing dot from abbreviations, to instead
keep them:

    ./scowl word-list scowl.db --dot True > wl.txt

To exclude abbreviations altogether (including unmarked ones):
   
    ./scowl word-list --poses-to-exclude=abbr > wl.txt

To disable the word filter and include all words:

    ./scowl word-list --no-word-filter > wl.txt

To create a British word list:

    ./scowl word-list scowl.db --spellings B > wl.txt

To create a British word list that include -ise, -ize, and other variant
spellings:

    ./scowl word-list scowl.db --spellings B,Z --variant-level '~' > wl.txt

The default word list includes roman numerals and slang words only really used
by computer programmers such as "grepped".  To exclude these and any other
special categories of words use:

    ./scowl word-list --categories '' > wl.txt

To create a larger wordlist:

    ./scowl word-list --size 70 > wl.txt

For additional options use:

    ./scowl word-list --help

Using the SQLite3 database directly is also supported.  The main entry point
is the `scowl_v0` query.

As SCOWLv2 is still in an alpha/testing phase the command line utility and
schema is subject to change.  At some point the command line interface will
stabilize.  The schema may still be subject to change but a new `scowl_v1`
view will be provided that is guaranteed to always provide the same results.
New columns may be added, but not in a way that will break existing queries.
If is is necessary to break existing queries a new view will be provided.


Filtering the Database
----------------------

In addition to creating wordlists you can also filter the database to only
show the information you are interested in and avoid noise.  This works by
creating a new database file that then needs to be reexported with
`./scowl export-db`.

For example, to filter the database to only include sizes 70 or lower:

    ./scowl filter --size 70 by-line scowl.db scowl-filtered.db
    ./scowl export-db scowl-filtered.db > scowl-filtered.txt

There are three ways to filter the database `by-line`, `by-group` and
`by-cluster`.  `by-line` will only keep the lines that match the filter
arguments.  `by-group` will instead keep the entire group, which is useful if
you want to then edit the groups and reintegrate into the larger scowl
database.  `by-cluster` will instead keep the entire cluster, which is useful
to provide additional context.  If you use the `by-cluster` option the
`--show-clusters` option might be useful when exporting the database.  For
example:

    ./scowl filter --size 70 by-cluster scowl.db scowl-filtered.db
    ./scowl export-db --show-clusters scowl-filtered.db > scowl-filtered.txt

When filtering by line you can also remove some information, which can help
simplify complex entries.  The available filters are `size` to remove the size
and instead use the size specified in the --size argument, `category` to
remove all categories, `region` to remove all regions and `tag` to remove all
tags.  If you filter by a single spelling then the spelling information will
automatically be removed.  For example, to get a simplified view of what will
be included for the default word list in American English:

    ./scowl filter --size 60 --spellings A --variant-level 1 --simplify size,tag by-line scowl.db scowl-filtered.db
    ./scowl export-db --show-clusters scowl-filtered.db > scowl-filtered.txt

See `./scowl filter --help` for additional usage.


Using the libscowl package directly
-----------------------------------

As previously mentioned the `scowl` script is a very thin wrapper around the
`libscowl` package.  As such, you can instead use `python3 -m libscowl`
instead of going through the script.  Use of the python module directly
instead of through the command line interface is also supported but the API
may change without notice.  The best documentation to the API is via
`__main__.py`.


File Format
-----------

Most everything is stored in a single file (`scowl.txt`) with the following format:

    FILE := CLUSTER ...
            [FOOTNOTES]

    CLUSTER := GROUP ...
               [CLUSTER-COMMENT] ...

    GROUP := LINE ...
             GROUP-COMMENT
             '\n'

    LINE := SIZE [' ' REGION] [' ' CATEGORY] [' ' TAG] ': '
            [VARIANT-INFO ' ' ... ': ']
            LEMMA [' <' POS ['/' POS-CLASS ] '>'] [' {' DEFN-NOTE '}'] [' (' USAGE-NOTE ')']
            [': ' ENTRY ', ' ...]
            ['#!' WARNING] ...
            ['#' COMMENT] ...
            '\n'

    REGION := 'US' | 'GB' | 'CA' | 'AU'

    TAG := '[' TAG-TEXT ']'

    LEMMA := WORD [ANNOTATION] | '-'

    VARIANT-INFO := SPELLING [VARIANT-LEVEL]

    SPELLING := 'A' | 'B' | 'Z' | 'C' | 'D' | '_'

    VARIANT-INFO := '.' | '=' | '?' | 'v' | '~' | 'V' | '-' | 'x'

    ANNOTATION := '*' | '-' | '@' | '~' | '!' | '†'

    ENTRY := DERIVED | '(' [DERIVED-VARIANT-INFO ' ' ... ': '] DERIVED '|' ... ')'

    DERIVED := WORD [ANNOTATION] | '-'

    DERIVED-VARIANT-INFO := [SPELLING] [VARIANT-LEVEL]

    GROUP-COMMENT := '## ' HEADWORD [' (' OTHER-WORDS ')'] ': ' COMMENT-TEXT

    CLUSTER-COMMENT :=  '## ' HEADWORD [' (' OTHER-WORDS ')'] ':\n'
                        ('## ' COMMENT-TEXT '\n') ...
                        '\n'

    FOOTNOTES := ('#: ' FOOTNOTE-TEXT '\n') ...

Anything between single quotes is a literal.  Space is only present if it is
within single quotes.  Within a literal the `\n` means a new line.  Anything
between square brackets (`[]`) is optional.  The Bar (`|`) means a choice
between one or the other.  The ellipsis (`...`) means to optionally repeat the
previous element(s).  If the ellipsis is after a literal, it means to repeat,
but use the preceding literal as a separator.

A CLUSTER is a very loose groupings of groups in order to keep related words
together.  There is no indication within the file itself what the clusters are.

A GROUP represents one sense of a word.  Groups are separated by empty lines.

SIZE is the SCOWL size with larger numbers meaning less common words.
The sizes have the following approximate meanings:
  
    35: small
    50: medium
    60: medium-large (size used for default spell checking dictionary)
    70: large (size used for large spell checking dictionary)
    80: a valid word

A TAG is sometimes use to provide information on what source list the word
came from.

The source for the majority of words is from lists Alan Beale has a large part
in creating, which provides a level of consistency.  These lists are then
supplemented from a number of signature lists.  Most of these words are
unmarked.  Finally, some additional sources where used that Alan had no part
in and are often of British origin, words from these lists are tagged as the
fact they are from an alternative source provides useful information.

Words from a few special lists are also tagged.

Anything that starts with `#!` or `#:` is generated by the database export
code and is ignored when parsing.  Similarly the `†` annotation is generated by
the export code and ignored when parsing.

The '#:' lines at the end of the file contain dumps of various information
from the database.  If there is any disagreement between the documentation and
this information, the information at the end the file takes precedence.

The LEMMA is the base form of the word.

The part of speeches (POS) or as follows:

    n: noun
    n_v: noun and verb
    m: noun/verb
    v: verb
    aj: adjective
    av: adverb
    aj_av: adjective and adverb
    a: adjective/adverb
    c: conjunction/preposition
    i: interjection
    p: pronoun
    s: contraction
    pre: prefix
    wp: multi-word part
    we: multi-word ending
    abbr: abbreviation
    x: non word

The `m` and `a` are special POS'es that should not used for new entries.  The
`m` is assigned when all the word forms for a verb where found in a word
list, but no POS info was found for that word.  It is probably a verb and
could also be a noun.  Similarly, The `a` means it could be an adjective or
adverb.

The `n_v` and `aj_av` are special combined POS'es.

Within a line the derived forms of a word are in a specific order.  A single
dash (`-`) is used if a particular word form is missing.  The order is one of:

    n: n0
    n: n0 [ns] [np]
    n: n0 ns np nsp

    v: v0
    v: v0 vd [vn] vg vs
    v: v0 vd vd2 vn vg vs vs2 vs3 vs4

    n_v: m0
    n_v: m0 vd [vn] vg ms [np]
    n_v: m0 vd [vn] vg ms np nsp

    m: m0
    m: m0 vd [vn] vg ms

    a*: a*0
    a*: a*0 a*1 a*2

    we: we [wep]

entries marked by square brackets are optional and can be excluded without the
use of a dash placeholder.

The derived forms are as follows:

    ?: unknown
    c: conjunction/preposition
    i: interjection
    p: pronoun
    s: contraction
    n0: noun: singular
    ns: noun: plural
    np: noun: possessive
    nsp: noun: plural possessive
    v0: verb: root form
    vd: verb: past tense (-ed)
    vd2: verb: past tense plural
    vn: verb: past participle
    vg: verb: present participle (-ing)
    vs: verb: present tense (-s)
    vs2: verb: present tense second-person singular
    vs3: verb: present tense third-person singular
    vs4: verb: present tense plural
    m0: noun/verb: root form
    ms: noun/verb: (-s)
    aj0: adjective: root form
    aj1: adjective: comparative (-er)
    aj2: adjective: superlative (-est)
    av0: adverb: root form
    av1: adverb: comparative (-er)
    av2: adverb: superlative (-est)
    a0: adjective/adverb: root form
    a1: adjective/adverb: comparative (-er)
    a2: adjective/adverb: superlative (-est)
    pre: prefix
    wp: multi-word part
    we: multi-word ending: root form
    wep: multi-word ending: possessive
    abbr: abbreviation
    x: non word: for example a roman numeral

The POS-CLASS is a string to qualify the POS, for example `place`.  The
current tags are experimental and at the moment can't be used to reliably
filter out proper nouns.

The DEFN-NOTE is used to distinguish two different senses of the same lemma.

The USAGE-NOTE is currently used to mark offensive and vulgar words and might
also be used in the future to mark slang, informal, and non-standard words.

The SPELLING and REGION codes are as follows:

    A: US: American
    B: GB: British "ise" spelling
    Z: GB: British "ize" or Oxford spelling
    C: CA: Canadian
    D: AU: Australian
    _:     Other (Never used with any of the above).

If there are no tags with the `Z` spelling category within a group then `B`
implies `Z`.  Similarly if there are no `C` tags then `Z` implies `C`.  If
there are no `D` tags then `B` implies `D`.

The VARIANT-LEVELs are as follows:

    .: 1: include
    =: 2: equal
    ?: 3: disagreement
    v: 4: common
    ~: 5: variant
    V: 6: acceptable
    -: 7: uncommon
    @: 8: archaic
    x: 9: invalid

The `v` indicator is used for most words marked as variants in the dictionary.
However, some variants will be demoted to a `V`.  For example, if the variant
is marked as "also" by Merriam-Webster, or if only some dictionaries
acknowledge the existence of the variant.  `-` is used when the variant is
generally not listed is the dictionary but there is some evidence of its
usage.  The `@` is used for an archaic spelling of the word.  The `x` is used
when the spelling is generally considered a misspelling, and is only included
for completeness.

The `.`, `=`, and `?` are special cases for when there is little agreement on
the preferred form.  The `.` is used when both forms are considered equal and
should be included in the default word list; it is generally used when the
spellings is different enough that is unlikely one will be confused with the
other.  The `=` means they are still equal but only the non-variant should be
included by default.  The `?` is used when there is some disagreement but
there one form is generally preferred over the other.

The `~` indicator means the word is a variant but no information is available
on the level, it should not be used for new entries.

An annotation is one of the following:

    *: usage dependent
    -: uncommon
    @: archaic
    ~: inapplicable
    !: infrequent
    †: ambiguous lemma

The `*` annotation is used for nouns when, depending on usage, the plural is
sometimes same as the singular form.  This is generally used for certain
animals (especially fish) and cardinal numbers.

The `†` is added by the database export code to indicate that the spelling of
the derived form is also used for a separate unrelated lemma.

The `-` is used to mark a significantly less common form of a word.  `~` is
used to mark plurals nouns that are generally not used, for one reason or
another, except in very specific circumstances.  `!` is used for forms of a
word that are nearly non-existent.  `@` is used to mark archaic forms a word.


Combined POS Handling
---------------------

The POS pairs noun/verb and adjective/adverb are normally combined into a
single group when doing so will not introduce additional noise.  The POS pairs
can be split by using:

    ./scowl split-pos scowl.db

And can then be combined using:

    ./scowl combine-pos scowl.db

Both these commands modify the database in place and are reversible.


Variant Translation
-------------------

SCOWL contains all the information in VarCon but the resulting file format
does not lead to easy translation.  The underlying database does.

Within the database any words with the same `group_id` and `pos` are
considered variants of each other.  To get information on the variants
join the `words` table with `variant_info` using `word_id`.  For example:

    select group_id, pos, spelling, variant_level, word from words join variant_info using (word_id)

Note that there are still some variants that are unmarked and will be excluded
as they are not in `variant_info`.  If these unmarked variants are important,
there are different ways to extract that from the database.  How this is done
will be left as an exercise to the reader.


Modifying
---------

The eventual intent is to allow editing `scowl.txt` directly, however this is
not supported yet.  Instead any changes should be made to the patch file
`patch`.  If you make changes to this file simply type `make` to rebuild
`scowl.txt` and `scowl.db`.


Compatibility with SCOWLv1
--------------------------

SCOWLv2 is a complete overhaul of SCOWL and nearly everything changed.
However, there is limited backward compatibility support via the `mk-list`
script.  If you used `mk-list` in SCOWLv1 is should still produce the same
results, but please sanity check the output by comparing the results to the
the last version of SCOWLv1.  If you created word lists by combining files in
the `final/` directory your scripts will need to be rewritten.  Please use the
`word-list` command of the `scowl` script to get the wordslists you want.

If you are using the `word-list` command please note that the variant levels
has changed.  The original 0 level is now levels 0-1, the original 1 variant
level is now 2-4, level 2 is now 5-6, level 3 is now 7-8, and level 4 is 9.
This mapping is also available in the `varinats_levels` table in the database.


Creating Hunspell and Aspell Dictionaries
-----------------------------------------

The `speller/` directory of SCOWLv1 has been ported over.  Creating the Aspell
and Hunspell dictionaries should work the same as they did with SCOWLv1, but
again please sanity check the results.  Official dictionaries will continue to
be created.
