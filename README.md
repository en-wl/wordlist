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

Unlike SCOWLv1, SCOWLv2 includes the proper spelling of abbreviations (i.e.,
with the dot at the end) rather than stripping the trailing dot.  It also
includes words that were excluded from SCOWLv1 such as hyphenated and open
(i.e. with space) compound words, and words with special symbols in them.

SCOWLv2 is still a work in progress.  In particular, some of the sources in
SCOWLv1 are not yet included for sizes larger than 60.

SCOWL is derived from many sources under a BSD compatible license. The
combined work is freely available under a MIT-like license.


Usage
-----

In order to use SCOWL to create a word list the text file must first be
converted into a SQLite3 database by using the command line interface to
the `libscowl` python module.  The module is not available on PyPI, but instead
included with SCOWL.  The easiest way to use it just to run any commands from
the root directly in SCOWL.  It is currently tested with Python 3.7 and SQLite
3.27.2.  Newer versions should work, older versions may work but are not
supported.

To convert the text file to a database use

    python3 -m libscowl create-db scowl.db < scowl.txt

Once converted to a database you can then extract wordlists from the database
with:

    python3 -m libscowl word-list scowl.db > wl.txt

Which will create a word list that corresponds to the default dictionary size
and variant level used when creating spell-checkers dictionaries, except that
dialectic marks (i.e. accents) are preserved.  To remove then marks use:

    python3 -m libscowl word-list scowl.db --deaccent > wl.txt

The default word filter strips the trailing dot from abbreviations, to instead
keep them:

    python3 -m libscowl word-list scowl.db --dot True > wl.txt

To exclude abbreviations altogether (including unmarked ones):
   
    python3 -m libscowl word-list --poses-to-exclude=abbr > wl.txt

To disable the word filter and include all words:

    python3 -m libscowl word-list --no-word-filter > wl.txt

To create a British word list:

    python3 -m libscowl word-list scowl.db --spellings B > wl.txt

To create a British word list that include -ise, -ize, and other variant
spellings:

    python3 -m libscowl word-list scowl.db --spellings B,Z --variant-level '~' > wl.txt

The default word list includes roman numerals and slang words only really used
by computer programmers such as "grepped".  To include these any any other
special categories of words use:

    python3 -m libscowl word-list --categories '' > wl.txt

To create a larger wordlist:

    python3 -m libscowl word-list --size 70 > wl.txt

For additional options use:

    python3 -m libscowl word-list --help

To convert the database back into a text file use:

    python3 -m libscowl export-db scowl.wl > scowl.txt

Using the SQLite3 database directly is also supported.  The main entry point
is the `scowl_v0` query.

As SCOWLv2 is still in an alpha/testing phase the command line utility and
schema is subject to change.  At some point the command line interface will
stabilize.  The schema may still be subject to change but a new `scowl-v1`
view will be provided that is guaranteed to always provide the same results.
New columns may be added, but not in a way that will break existing queries.
If is is necessary to break existing queries a new view will be provided.


Modifying
---------

The eventual intent is to allow editing `scowl.txt` directly, however this is
not supported yet.  SCOWLv2 is created from a far more complicated PostgreSQL
database and it is easier to fix errors by fixing the source database.


File Format
-----------

Most everything is stored in a single file ('scowl.txt') with the following format:

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
    Z: GB: British "ize" spelling or OED preferred Spelling
    C: CA: Canadian
    D: AU: Australian
    _:     Other (Never used with any of the above).

If there are no tags with the `Z` spelling category within a group then `B`
implies `Z`.  Similarly if there are no `C` tags then `Z` implies `C`.  If
there are no `D` tags then `B` implies `D`.

The VARIANT-LEVELs are as follows:

    .: include
    =: equal
    ?: disagreement
    v: common
    ~: variant
    V: acceptable
    -: uncommon
    x: invalid

The `v` indicator is used for most words marked as variants in the dictionary.
However, some variants will be demoted to a `V`.  For example, if the variant
is marked as "also" by Merriam-Webster, or also if only some dictionaries
acknowledge the existence of the variant.  `-` is used when the variant is
generally not listed is the dictionary but there is some evidence of its
usage, or when it is marked as an archaic spelling for the word.  The `x` is
used when the spelling is almost generally considered a misspelling, and is
only included for completeness.

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

The '*' annotation is used for nouns when, depending on usage, the plural is
sometimes same as the singular form.  This is generally used for certain
animals (especially fish) and cardinal numbers.

The '†' is added by the database export code to indicate that the spelling of
the derived form is also used for a separate unrelated lemma.

The other annotations are used as documentation to indicate why that particular
form of a word is at a higher SCOWL level than others.  These annotations come
primarily from 2of12id in alt12dicts.
