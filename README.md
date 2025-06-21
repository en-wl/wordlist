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
more complicated, and unreleased, process.  The results of this process is in
the file `scowl-pre.txt`.  That file is then combined with other files to
create the final version `scowl.txt` and the sqlite3 database `scowl.db`.


Requirements
------------

SCOWLv2 requires Python 3 and SQLite.  It currently requires Python 3.7 and
SQLite 3.33.0.  Newer versions should work, older versions may work but are
not supported.

A Unix like environment is also required for now.


Basic Usage
-----------

In order to use SCOWL the database must first be created from the source files
in the `data/` directly.  To do so simply type:

  make

which will create the sqlite3 file `scowl.db` which is all that you need for
most operations.  If required the flat text file can also be created with `make
scowl.txt`.

To work with SCOWL use the `scowl` script provided in the root directory.
This script is a very thin wrapper around the `libscowl` python module.  The
module is not available on PyPI, but instead included with SCOWL.  This script
is meant to be run from the root directory of the SCOWL distribution.

To extract wordlists from the database use:

    ./scowl --db scowl.db word-list > wl.txt

If `--db` option specifies the database file to use.  The option defaults to
'scowl.db' or the value of the `SCOWL_DB` environment variable if set.

The default options for word-list will create a word-list that corresponds to
the default dictionary for American English, with the exception that dialectic
marks (i.e. accents) are preserved.  To remove the marks use the `--deaccent`
option:

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

Using the SQLite3 database directly is also supported.  Most of the database
is defined in the files `schema.sql`, `views.sql` and `scowl.sql` in the
`libscowl/` directory.  The main entry point for extrating word lists is the
`scowl_v0` query.

As SCOWLv2 is still in an alpha/testing phase the command line utility and
schema is subject to change.  At some point the command line interface will
stabilize.  The schema may still be subject to change but a new `scowl_v1`
view will be provided that is guaranteed to always provide the same results.
New columns may be added, but not in a way that will break existing queries.
If is is necessary to break existing queries a new view will be provided.


Searching the Database
----------------------

To search for an entry in scowl use:

    ./scowl search [--db scowl.db] [--by-cluster] WORD [WORD ...]

where WORD is one or more words to search.  By default search will return the
groups with any of the supplied words.  To instead return the entire cluster
use `--by-cluster`.  Note that the search is case sensitive.


Filtering the Database
----------------------

You can also filter the database to only show the information you are
interested in and avoid noise.  You can either create a new database or simply
export the results.

For example, to filter the database to only include sizes 70 or lower and
export the results to scowl-filtered.txt:

    ./scowl filter --size 70 by-line --db scowl.db --export > scowl-filtered.txt

To instead create a new database with the results use:

    ./scowl filter --size 70 by-line --db scowl.db --target scowl-filtered.dn

There are three ways to filter the database `by-line`, `by-group` and
`by-cluster`.  `by-line` will only keep the lines that match the filter
arguments, `by-group` will instead keep the entire group and `by-cluster`
will keep the entire cluster.  If you use the `by-cluster` option the
`--show-clusters` option might be useful when exporting the database.  For
example:

    ./scowl filter --size 70 by-cluster --export --show-clusters > scowl-filtered.txt

When filtering by line you can also remove some information, which can help
simplify complex entries.  The available filters are `size` to remove the size
and instead use the size specified in the --size argument, `category` to
remove all categories, `region` to remove all regions and `tag` to remove all
tags.  If you filter by a single spelling then the spelling information will
automatically be removed.  For example, to get a simplified view of what will
be included for the default word list in American English:

    ./scowl filter by-line --size 60 --spellings A --variant-level 1 \
            --simplify size,tag --export > scowl-filtered.txt

See `./scowl filter --help` for additional usage.


Using the libscowl package directly
-----------------------------------

As previously mentioned the `scowl` script is a very thin wrapper around the
`libscowl` package.  As such, you can instead use `python3 -m libscowl`
instead of going through the script.  Use of the python module directly
instead of through the command line interface is also supported to some
extent.  Calling the high level functions as it done in the `__main__.py` is
supported, but the API may stil change.  Direct use of the internal data
structures, however, is not supported.


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

    LINE := SCOWL_INFO ': '
            ([VARIANT-INFO ' ' ... | OVERRIDE) ': ']
            LEMMA_INFO
            [': ' ENTRY ', ' ...]
            ['#!' WARNING] ...
            ['#' COMMENT] ...
            '\n'

    SCOWL_INFO := SIZE [' ' REGION] [' ' CATEGORY] ([' ' TAG] ...)

    LEMMA_INFO := LEMMA [' <' POS ['/' POS-CLASS ] '>'] [' {' DEFN-NOTE '}'] [' (' USAGE-NOTE ')']

    REGION := 'US' | 'GB' | 'CA' | 'AU'

    TAG := '[' TAG-TEXT ']'

    LEMMA := [GROUP-ANNOTATION] WORD [ANNOTATION] | '-'

    VARIANT-INFO := SPELLING [VARIANT-LEVEL]

    SPELLING := 'A' | 'B' | 'Z' | 'C' | 'D' | '_'

    VARIANT-LEVEL := '.' | '=' | '?' | 'v' | '~' | 'V' | '-' | '@' | 'x'

    OVERRIDE := '+'

    GROUP-ANNOTATION := '-' | '@' | '!'

    ANNOTATION := '*' | '-' | '@' | '~' | '!' | '†'

    ENTRY := DERIVED | '(' [DERIVED-VARIANT-INFO ' ' ... ': '] DERIVED '|' ... ')'

    DERIVED := WORD [ANNOTATION] | '-'

    DERIVED-VARIANT-INFO := [SPELLING] [VARIANT-LEVEL]

    GROUP-COMMENT := '## ' COMMENT-TEXT

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

The source for the majority of words is from lists that Alan Beale has a large
part in creating, which provides a level of consistency.  These lists are then
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
    v: verb
    m: noun/verb
    aj: adjective
    av: adverb
    a: adjective/adverb
    pn: pronoun
    c: conjunction
    pp: preposition
    d: determiner
    i: interjection
    abbr: abbreviation
    s: contraction
    pre: prefix
    suf: suffix
    wp: multi-word part
    we: multi-word ending
    x: non word (for example a roman numeral)
    n_v: noun and verb
    aj_av: adjective and adverb

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

    pn: p0
    pn: p0 pn1 pns pnd pnp pnr0 pnrs

    d: d
    d: d ds
    d: d d1 d2

    a*: a*0
    a*: a*0 a*1 a*2

    we: we [wes] [wep]
    we: we wes wep weps

Entries marked by square brackets are optional and can be excluded without the
use of a dash placeholder.  Trailing entries for pronouns (pn) can also be
excluded without the use of a dash placeholder.

The derived forms are as follows:

    n0: noun
    ns: noun: plural
    nss: noun: plural of plural
    np: noun: possessive
    nsp: noun: plural possessive
    nssp: noun: plural of plural possessive
    v0: verb
    vd: verb: past tense (-ed)
    vd2: verb: past tense plural (were)
    vn: verb: past participle (-en)
    vg: verb: present participle (-ing)
    vs: verb: present tense (-s)
    vs2: verb: present tense second-person singular (are)
    vs3: verb: present tense third-person singular (is)
    vs4: verb: present tense plural (are)
    m0: noun/verb
    ms: noun/verb: (-s)
    aj0: adjective
    aj1: adjective: comparative (-er)
    aj2: adjective: superlative (-est)
    av0: adverb
    av1: adverb: comparative (-er)
    av2: adverb: superlative (-est)
    a0: adjective/adverb
    a1: adjective/adverb: comparative (-er)
    a2: adjective/adverb: superlative (-est)
    pn0: pronoun
    pn1: pronoun: objective (you/him/her/...)
    pns: pronoun: plural
    pnd: pronoun: determiner (your/his/her/...)
    pnp: pronoun: possessive (yours/his/hers/...)
    pnr0: pronoun: reflexive singular (yourself/...)
    pnrs: pronoun: reflexive plural (yourselves/...)
    c: conjunction
    pp: preposition
    d: determiner
    ds: determiner: plural
    d1: determiner: comparative
    d2: determiner: superlative
    i: interjection
    abbr: abbreviation
    s: contraction
    pre: prefix
    suf: suffix
    wp: multi-word part
    we: multi-word ending
    wes: multi-word ending: plural
    wep: multi-word ending: possessive
    weps: multi-word ending: plural possessive
    x: non word

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


Database structure
------------------

The textual format does not map directly to the underlying database.  In
particular it includes some redundant information that is not present in the
database:

 * The group annotation, pos, pos-class, defn-note, and usage-note are
   associated with the group and not the lemma and as such must be the same
   for each line.

 * SCOWL information is attached to a particular POS within a group and not
   the word itself.  This means that all variants of a word must have the same
   SCOWL info.


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

For the foreseeable future `scowl.txt` will be generated by combining
`scowl-pre.txt` will the other files in the `data/` directory using the
`combine.py` perl script.

To add new entries to SCOWL you should generally add the info to `data/extra`.
Words added to this file will get the `[extra]` tag.  If a word is special in
some way, for example a neologism, then the word can be added to
`data/signature` instead to have the `[+]` tag applied.  Both these files are
in the _merge_ format.

To make corrections or add variants information use one of `data/fixes`,
`data/variants`, or `data/compounds`.  The first should be used for making
corrections, the seond for adding variant information, and the last for adding
variant information strictly related to the preferred form of compound words.
These files are in the _adjust_ format.

To bump a word to a higher SCOWL size use `data/exclude`.  This file is also
in the _adjust_ format however it should only use a subset of the format.  The
SCOWL size given should be the minimal SCOWL size that the word should be
included and the tag '[-]' must be used.

There are other files are used by the `combine.py` that are in a special
format.  These files should, in general, not need to be modified.

### Merge file format

_Merge_ files are used when adding new entries.  The format is exactly the
same as `scowl.txt` except that new data is merged with existing groups when
there is a match.  See `./scowl merge --help` for more info.

### Adjust file format

_Adjust_ files are used when adjustments are needed to be made to entries or
groups.  This included marking new variants.

#### File format

The format is similar to the main `scowl.txt` format but the parsing and
processing is different.  Each line is similar to a line in `scowl.txt`
but is optionally prefixed by one of `+`, `-`, `=`, `~`, or `#` that dictates
how that line is processed.  The prefix _must_ be followed by a space.  The
prefixes have the following approximate meanings:

    none: match and make adjustments
    +: add
    -: remove
    =: replace
    ~: transfer
    #: a comment (i.e. ignored)

Unless prefixed with a `+`, a line is first matched with an exiting lemma in
the database using the word, pos, and defn-note.  If no match is found the
group will be skipped.  If the line is prefixed with a `-`, than that lemma
will be removed from the group.  If the line is prefixed with a `~`, than no
additional actions will be taken, but the information found in the database
will be used to make adjusted to the scowl info.

If a line has no prefix, or is prefixed with a `=`, than after a match is made,
any other information provided as part of the the lemma info, will change the
existing information in the database.  If a piece of information is blank,
than it will be reset to the default or removed; however, if it is missing
than no change will be made.  For example, a pos of `<n/>` will will remove
the pos-class for the group but a pos of `<n>` will not.  A underscore `_` can
be used as an annotation to replace a group or entry rank with the default.
The pos and defn-note can also change if the `→` (U+2192) is used as part of
the pos or defn-note.  For example:

    dialog <n→wp> {dialog box}

will change the pos from a noun to a word-part.  If have a compose key
configured on Linux you can type `→` with
<kbd>Compose</kbd><kbd>-</kbd><kbd>&gt;</kbd>.  You can also just copy and
paste as you shouldn't need to type `→` very often.

If the line has no prefix, than any derived forms provided will be matched by
the word and pos and any forms with a single dash (`-`) will be ignored.  If
the line has a prefix of `=`, than any derived info will instead replace the
existing ones for that lemmas.

If any variant info is given for a lemma or a derived form, than the variant
information for all relevant lemmas or forms will be replaced, including
those without a variant prefix.  For example `(hyaenas | V: hyaena)` will
change the variant info for both _hyaenas_ and _hyaena_ even though _hyaenas_
doesn't have a variant prefix.

If two lines within the same group match different existing groups, the two
groups will be merged when the prefix is anything but `~`.

SCOWL info is handled separately and can not be changed in the same line as
the other information.  A SCOWL line generally has the form:

    SCOWL-INFO ': ...'

Where the `...` is a literal.  If any SCOWL info is given the line must be
prefixed with one of `+`, `-`, or `=`.  If the prefix is a `+` that scowl info
is added.  If the prefix is a `-` than that specific scowl info is removed.
If the prefix is a `=` than the scowl info is partly replaced.  In particular
any scowl info with a size less then the provided size will be removed.

The _adjust_ format can be used to create new groups.  When adding a group
either a SCOWL info line or a line with `~` prefix must be part of the group.
When the `~` prefix is used that line will be used to intelligently assign
SCOWL info for the group.  For example this:

    ~ rive <v>: -, riven, -, -
    + riven <aj>

will assign `riven` the same SCOWL info as the derived form `riven` for the
verb `rive` as the word matches.

#### Examples

The most straight forward use of an _adjust_ file is to add variant info.  For
example:

    A C: kindergartner <n>
    AV B: kindergartener <n>
    A- B-: kindergärtner <n>

Will mark _kindergartner_, _kindergartener_, and _kindergärtner_ as variants
of each other.  If any of the lemmas were in separate groups they will be combined.

Sometimes one or more of the lemmas in a variant group may be missing derived
forms.  The _adjust_ file can also be used to correct this; for example:

    A B=: fete <n>: fetes
    Av B: fête <n>: fêtes

    A B=: fete <v>: feted, feting, fetes
    + Av B: fête <v>: fêted, fêting, fêtes

will mark _fete_ and _fête_ as variants of each other.  In addition it will
add the verb form of _fête_ to match the verb form of _fete_.  Listing the
derived forms in the other lines is not strictly needed, but will help avoid
errors as when a derived form is listed in an entry without a prefix it must
match what is in the database.

The _adjust_ file format can also be used to adjust variant info for derived
entries; for example:

    strew <v>: -, (strewn | .: strewed), -, -


will adjust the variant information for the past participle form.  The derived
forms with a `-` will be ignored, so no other adjustments will be made.

The word _thru_ is somewhat of a special case.  In is acceptable to use _thru_
as part of the word _drive-thru_, but generally not considered a proper
spelling of _through_.  It is also different enough in spelling that it
unlikely that the two forms will get confused so I want to let the word _thru_
in but only at SCOWL sizes 70 or higher.  I also want to add an entry for
_thru_ when part of _drive-thru_ but tag it for _US_ only.  The following
lines accomplish this:

    A B: through <aj_av>
    AV B-: thru <aj_av>
    + 70: +: thru <aj_av>

    A B: through <pp>
    AV B-: thru <pp>
    + 70: +: thru <pp>

    + thru <we> # drive-thru
    = 50 US: ...

The `+` after the size is a an override to force the word _thru_ in at size 70
at all variant levels.  The comment at the end is a lemma comment and will
carry over to scowl.txt.


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
