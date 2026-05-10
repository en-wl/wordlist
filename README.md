English Speller Database (ESDB)
===============================

The English Speller Database (ESDB) is a database of information on English
words useful for creating high-quality speller dictionaries and wordlists for
most dialects of English.  The database primarily contains information on how
common a word is, differences in spelling between the dialects of English,
spelling variant information, (basic) part-of-speech, and inflection
information.

The project was originally called SCOWL (Spell Checker Originated Word Lists)
and Friends.  The "and Friends" part referred to the other components that
made up SCOWL including VarCon, AGID, and the various wordlists used to create
the final result.  The reason for the name change is documented in
[#465](https://github.com/en-wl/wordlist/discussions/465).

The original version (SCOWLv1) was a compilation of the information in the
database into a set of simple word lists that can be combined to create
speller dictionaries of various sizes and dialects (American, British (both
-ise and -ize), Canadian and Australian).

The new version (ESDB) instead combines all that information into a single
text file and SQLite3 database.  In order to keep the file size manageable and
to avoid noise entries the minimum ESDB size is now 35 and the 95 size is not
included.

Unlike the original version, the new version includes the proper spelling of
abbreviations that include the trailing dot.  It also includes words that were
excluded from the original version such as hyphenated and open (i.e. with
space) compound words, and words with special symbols in them.

ESDB is derived from many sources under a BSD compatible license.  The
combined work is freely available under an MIT-like license.  See the file
Copyright for details.

ESDB is still a work in progress.  The default size (60) has been vetted for
errors, and the larger size (70) should also be usable as a spellchecker
dictionary.  The processing of the source data is completely different so the
resulting wordlists are not the same.  Most of the changes I regard as
corrections for improper handling of derived forms or variants in SCOWLv1.
The handling of possessive forms has been completely redone based partly on
the noun category assigned by WordNet.  For American English any new changes
to non-possessive forms of words included in speller dictionary have been
accounted for and noted in the file [`docs/comp-60.txt`](docs/comp-60.txt).

The new version is generated from the same sources that the original uses but
via a far more complicated, and unreleased, process.  The results of this
process are in the file `scowl-pre.txt`.  That file is then combined with
other files to create the final version `scowl.txt` and the sqlite3 database
`scowl.db`.


Requirements
------------

ESDB requires Python 3 and SQLite.  It currently requires Python 3.7 and
SQLite 3.33.0.  Newer versions should work, older versions may work but are
not supported.

A Unix-like environment is not required but the rest of this documentation
will assume you are using one.  For details on how to run on Windows 10/11
directly see: https://github.com/en-wl/wordlist/issues/499.

Basic Usage
-----------

Until very recently the name SCOWL (and sometimes SCOWLv2) was still used for
the database.  For this reason all internal commands still use the original
name for now.

In order to use ESDB the database must first be created from the source files
in the `data/` directly.  If you have a Unix-like environment simply type:

    make

which will create the sqlite3 file `scowl.db` which is all that you need for
most operations.  If required the flat text file can also be created with
`make scowl.txt`.

To work with the database use the `scowl` script provided in the root
directory.  This script is a very thin wrapper around the `libscowl` Python
module.  The module is not available on PyPI, but instead included with the
database.  This script is meant to be run from the root directory of the ESDB
distribution.

To extract wordlists from the database use:

    ./scowl --db scowl.db word-list 60 A 1 > wl.txt

If `--db` option specifies the database file to use.  The option defaults to
'scowl.db' or the value of the `SCOWL_DB` environment variable if set.

The positional arguments to the `word-list` are the ESDB size (in this case
60), spellings to include (in this case `A` for American), and the max variant
level (in this case 1, which excludes most variants except for special cases
such as _dox_ and _doxx_).  The exact meaning of all these values are
described in the _[File Format](#file-format)_ section.

The above command will create a word-list that corresponds to the default
dictionary for American English, with the exception that diacritical marks
(i.e. accents) are preserved.  To remove the marks use the `--deaccent`
option:

    ./scowl word-list 60 A 1 --deaccent > wl.txt

The default word filter strips the trailing dot from abbreviations, to instead
keep them:

    ./scowl word-list 60 A 1 --dot True > wl.txt

To exclude abbreviations altogether (including unmarked ones):

    ./scowl word-list 60 A 1 --poses-to-exclude=abbr > wl.txt

To disable the word filter and include all words:

    ./scowl word-list 60 A 1 --no-word-filter > wl.txt

To create a British word list:

    ./scowl word-list 60 B 1 > wl.txt

To create a British word list that includes -ise, -ize, and other variant
spellings:

    ./scowl word-list 60 B,Z 5 > wl.txt

The default word list includes Roman numerals and slang words only really used
by computer programmers such as "grepped".  To exclude these and any other
special categories of words use:

    ./scowl word-list 60 A 1 --categories= > wl.txt

To create a larger wordlist:

    ./scowl word-list 70 A 1 > wl.txt

For additional options use:

    ./scowl word-list --help

Using the SQLite3 database directly is also supported.  Most of the database
is defined in the files `schema.sql`, `views.sql` and `scowl.sql` in the
`libscowl/` directory.  The main entry point for extracting word lists is the
`scowl_v0` query.

As ESDB is still in an alpha/testing phase the command line utility and schema
is subject to change.  At some point the command line interface will
stabilize.  The schema may still be subject to change but a new `esdb_v1`
view will be provided that is guaranteed to always provide the same results.
New columns may be added, but not in a way that will break existing queries.
If it is necessary to break existing queries a new view will be provided.


Searching the Database
----------------------

To search for an entry in scowl use:

    ./scowl search [--db scowl.db] [--by-cluster] [--exact] WORD [WORD ...]

where WORD is one or more words to search.  By default search will return the
groups with any of the supplied words.  To instead return the entire cluster
use `--by-cluster`.  The search by default is fuzzy.  To instead search for the
exact word use `--exact`.


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
`libscowl` package.  As such, you can use `python3 -m libscowl`
instead of going through the script.  Use of the Python module directly
instead of through the command line interface is also supported to some
extent.  Calling the high-level functions as is done in the `__main__.py` is
supported, but the API may still change.  Direct use of the internal data
structures, however, is not supported.


File Format
-----------

### Grammar

Most everything is stored in a single file (`scowl.txt`) with the following format:

    FILE := CLUSTER ...
            [FOOTNOTES]

    CLUSTER := GROUP ...
               [CLUSTER-COMMENT] ...

    GROUP := LINE ...
             [GROUP-COMMENT]
             '\n'

    LINE := SCOWL_INFO ': '
            [(VARIANT-INFO ' ' ... ['{' NUMBER '}'] | OVERRIDE) ': ']
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

Anything that starts with `#!` or `#:` is generated by the database export
code and is ignored when parsing.  Similarly the `†` annotation is generated by
the export code and ignored when parsing.

The '#:' lines at the end of the file contain dumps of various information
from the database.  If there is any disagreement between the documentation and
this information, the information at the end of the file takes precedence.

### Grammar Elements

#### CLUSTER

A CLUSTER is a very loose groupings of groups in order to keep related words
together.  There is no indication within the file itself what the clusters are.

#### GROUP

A GROUP represents one sense of a word.  Groups are separated by empty lines.

#### SIZE

SIZE is the ESDB size, with larger numbers meaning less common words.
The sizes have the following approximate meanings:

    35: small
    50: medium
    60: medium-large (size used for default spell checking dictionary)
    70: large (size used for large spell checking dictionary)
    80: a valid word in current usage
    85: a valid word

Size 35 is the recommended small size, 50 the medium and 70 the large.  Sizes
70 and below contain words found in most dictionaries, while size 80
contains all the strange and unusual words people like to use in word games
such as Scrabble (TM).  While a lot of the words in size 80 are not used
very often, they are all generally considered valid words in the English
language.  Words in the 85 size are also considered valid, but may no longer
be used in modern English.

For spell checking I recommend using size 60.  This size is the largest size
that I am fairly confident does not contain any misspellings or invalid words.
In addition, an effort is made to exclude valid yet problematic words (such as
"calender") from the 60 size that are likely to be a misspelling of a more
common word.  The 70 size is reasonable for those wanting a larger list, and
don't mind a few errors.  The 80 or larger sizes are not reasonable for spell
checking.

#### TAG

A TAG is sometimes used to provide information on what source list the word
came from.

The source for the majority of words is from lists that Alan Beale has a large
part in creating, which provides a level of consistency.  These lists are then
supplemented from a number of signature lists.  Most of these words are
unmarked.  Finally, some additional sources were used that Alan had no part
in and are often of British origin, words from these lists are tagged as the
fact they are from an alternative source provides useful information.

Words from a few special lists are also tagged.

For a complete list of tags see [docs/sources.md](docs/sources.md).

#### LEMMA

The LEMMA is the base form of the word.

#### POSes

The parts of speech (POS) are as follows:

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

The `m` and `a` are special POS tags that should not be used for new entries.
The `m` is assigned when all the word forms for a verb were found in a word
list, but no POS info was found for that word.  It is probably a verb and
could also be a noun.  Similarly, The `a` means it could be an adjective or
adverb.

The `n_v` and `aj_av` are special combined POS tags.

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

#### POS-CLASS

The POS-CLASS is a string used to qualify the POS.  The current tagging is
inconsistent, however; for example, the classes can't be used to reliably
filter out proper nouns.

the current choices are:

    person: first name of person
    surname: last name of person
    place: geographical place: United States, Maryland, Boston, etc.
    name: a proper noun/adj when no other label is a good fit

    demonym: [experiential] person or people related to a place
    trademark: [experiential] registered trademark

    abbr: an abbreviation that takes on inflected forms such as FAQs

    number: one, two, etc., used with <n> POS
    ordinal: first, second, etc., used with <n> POS

In addition the following temporary classes are used for words that need to be
classified:

    upper: an upper-case word that is found in most dictionaries
    name?: a likely proper noun/adj
    upper?: a possible proper noun/adj
    abbr?: a likely abbreviation

Note that proper nouns such as _Monday_, _September_, and _Easter_ don't get a
POS tag.  The category `upper` is reserved for words that have yet to be classified.

#### DEFN-NOTE

The DEFN-NOTE is used to distinguish two different senses of the same lemma.

#### USAGE-NOTE

The USAGE-NOTE is used to mark offensive, vulgar, slang, informal,
non-standard, and other similar words.  At the moment the marking of offensive,
vulgar words only covers the worst offenders and the marking of non-standard
and similar words is very incomplete.

The current usage notes for offensive and vulgar words are:

  * `offensive-1`: extremely offensive racial slurs which
    should generally not be used
  * `offensive-2`: offensive racial slurs which should, also, in general,
     not be used but don't have the stigma in modern society as those in
     `offensive-1`
  * `vulgar-1`: vulgar or swear words which should generally not be said
    around children
  * `vulgar-3`: words which are considered vulgar, offensive, or taboo by some
    dictionaries, but are not nearly as strong as those in `vulgar-1`,
    and generally not considered swear words today.

`offensive|vulgar-1|2` are marked as NOSUGGEST in Hunspell dictionaries to
keep them from being suggested when a word is misspelled.

The other usage notes in use are:

  * `colloquial`
  * `informal`
  * `nonstandard`

#### SPELLING and REGION

The SPELLING codes and REGION tags are as follows:

    A: US: American
    B: GB: British "ise" spelling
    Z: GB: British "ize" or Oxford spelling
    C: CA: Canadian
    D: AU: Australian
    _:     Other (Never used with any of the above).

A SPELLING code classifies alternative spellings of the same word.  A REGION
tag labels entries that are specific to a particular region.

Within a group, if there are no lines with the `Z` SPELLING code then `B`
implies `Z`; similarly if `C` is missing then `Z` implies `C`, and if `D` is
missing then `B` implies `D`.

#### VARIANT-LEVEL

The VARIANT-LEVELs are as follows:

     : 0: non-variant
    .: 1: include
    =: 2: equal
    ?: 3: disagreement
    v: 4: common
    ~: 5: variant
    V: 6: acceptable
    -: 7: uncommon
    @: 8: archaic
    x: 9: invalid

`v` is used for common variants where there is clear agreement on the
preferred form and the variant is reasonably frequent.  `V` is used for less
common but still clearly acceptable variants; typical cases are variants
marked as "also" in Merriam-Webster, or spellings that are only recognized by
some major dictionaries.  `-` is used when the variant is generally not listed
in standard dictionaries, but there is some evidence of real-world usage.  `@`
is used for archaic spellings of the word.  `x` is used for outright
misspellings that are only included for completeness.

The `.`, `=`, and `?` indicators are special cases for when there is no single
clearly preferred form.  `.` is used when both forms are considered
equal and should be included in the default word list; it is generally used
when the spellings are different enough that it is unlikely one will be
confused with the other.  `=` means they are still equal but only the form
without a variant marker should be included by default.  `?` is used when
there is some disagreement but one form is generally preferred over the other.

The `~` indicator is used for legacy data when no information is available on
the level.

When multiple lemmas with the same variant level need to coexist within the
same group, an optional number can be added after the variant info using curly
braces (e.g., `_V {1}`, `_V {2}`).

#### ANNOTATION and GROUP-ANNOTATION

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
used to mark plural nouns that are generally not used, for one reason or
another, except in very specific circumstances.  `!` is used for forms of a
word that are nearly non-existent.  `@` is used to mark archaic forms of a word.


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

The database contains all the information in VarCon but the resulting file format
does not lead to easy translation.  The underlying database does.

Within the database any words with the same `group_id` and `pos` are
considered variants of each other.  You can access variant information via the
`words_w_variant_info` view.

For example to convert the word _color_ from the American to the British
spelling you could use this query:

    select distinct b.word
      from words_w_variant_info as a
      join words_w_variant_info as b using (group_id, pos)
    where a.spelling in ('_','A') and a.variant_level <= 6
      and b.spelling in ('_','B') and b.variant_level <= 1 and a.word='color';

which, in this case, will return _colour_ as the only result.  This query will
match up to the variant level of 6 (_acceptable_ or `V`) for the American
spelling but only up to level 1 (_include_ or `.`) for the British.  In some
cases there may be multiple matches; for example, if the word was _program_,
the query will return both _program_ and _programme_ as the correct spelling
depends on context: it's _program_ in the case of _computer program_ but
_programme_ in most other contexts.  If the word is the same in both dialects
the query will return the same word.


Modifying
---------

For the foreseeable future `scowl.txt` will be generated by combining
`scowl-pre.txt` with the other files in the `data/` directory using the
`combine.py` Python script.

To add new entries to the database you should generally add the info to
`data/extra`.  Words added to this file will get the `[extra]` tag.  If a word
is special in some way, for example a neologism, then the word can be added to
`data/signature` instead to have the `[+]` tag applied.  Both these files are
in the _merge_ format.

To make corrections or add variant information use one of `data/fixes`,
`data/variants`, or `data/compounds`.  The first should be used for making
corrections, the second for adding variant information, and the last for adding
variant information strictly related to the preferred form of compound words.
These files are in the _adjust_ format.

To bump a word to a higher ESDB size use `data/exclude`.  This file is also
in the _adjust_ format however it should only use a subset of the format.  The
size given should be the minimal size that the word should be
included and the tag '[-]' must be used.

There are other files which are used by the `combine.py` script that are in a special
format.  These files should, in general, not need to be modified.


### Merge file format

_Merge_ files are used when adding new entries.  There is limited support for
merging groups and adding variant information with the addition of the new
entries.

Files of this format should start with the line:

    #:: merge [TAG] [FLAGS]

where TAG is an optional tag to add to all new entries.  FLAGS is any of:

    :replace-on-conflict
    :error-on-conflict
    :skip-on-variant-conflict
    :error-on-variant-conflict
    :adjust-pos

Without any flags groups are merged, variant information is replaced, and
`:adjust-pos` is not enabled.

After the header line, the format is exactly the same as `scowl.txt` except
that new data is merged with existing groups when there is a match.

#### Variant processing and conflict handling

Variant information can be provided as part of the new information.  By
default, if there is a match then the new information will take precedence as
long as it doesn't create inconsistencies.  If `:skip-on-variant-conflict` is
given than the existing variant information will take precedence.

If `:replace-on-conflict` is given than any matching groups will be replaced
instead of trying to merge the information.  Use this flag with caution.

If more than one existing group matches, then the two groups will be merged as
long as it doesn't create inconsistencies.

If any inconsistencies are found the merge will be aborted.

Variant level inconsistencies will arise when there are additional forms found
in the database that are not mentioned.  To resolve this, simply provide the
additional forms.

#### POS processing

It is an error to add entries if an existing entry with an overlapping POS is
already present.  This mostly applies to the `<m>` and `<a>` POS tags.  For
example, adding a `<n>` form of a word when an entry with the `<m>` POS
already exists is an error.  To fix this, the `<m>` entry needs to be split
into a separate `<n>` and `<v>`.

If the `:adjust-pos` flag is given, a pass is first done to split or adjust
existing entries so that the POS better matches the new entries.  This will
adjust both overlapping POSes, and also entries without a POS.  The
transformation is performed in an independent transaction, so the merge can
fail while the POS changes remain.  If this happens, you can generally just
rerun the merge command and the POS changes will be skipped as there is
nothing to do.

#### Comment handling

When merging, existing group comments are treated as notes about lemma
variants and may be dropped to avoid keeping stale commentary.  In particular:

- If multiple existing groups are merged together, existing group comments are
  cleared.
- If the merge input provides complete lemma variant information for the
  group (so the existing lemma variant info is replaced), the existing group
  comment is cleared.

If the merge input includes a new group comment, it replaces the existing one.

New cluster comments replace existing ones under the same headword.

### Adjust file format

_Adjust_ files are used when adjustments are needed to be made to entries or
groups.  This included marking new variants.

#### File format

_Adjust_ files should start with the line:

    #:: adjust

After that, the format is similar to the main `scowl.txt` format but the parsing and
processing is different.  Each line is similar to a line in `scowl.txt`
but is optionally prefixed by one of `?`, `+`, `-`, `=`, `~`, or `#` that dictates
how that line is processed.  The prefix _must_ be followed by a space.  The
prefixes have the following approximate meanings:

    none: match and make adjustments
    ?: match and make adjustments if found
    +: add
    -: remove
    =: replace
    ~: transfer
    #: a comment (i.e. ignored)

Unless prefixed with a `+`, a line is first matched with an existing lemma in
the database using the word, pos, and defn-note.  If no match is found the
group will be skipped.  To avoid this and instead just skip the line, use `?`.
If the line is prefixed with a `-`, then that lemma will be removed from the
group.  If the line is prefixed with a `~`, then no additional actions will be
taken, but the information found in the database will be used to make adjustments
to the scowl info.

If a line has no prefix, or is prefixed with a `=`, then after a match is made,
any other information provided as part of the the lemma info, will change the
existing information in the database.  If a piece of information is blank,
then it will be reset to the default or removed; however, if it is missing
then no change will be made.  For example, a pos of `<n/>` will remove
the pos-class for the group but a pos of `<n>` will not.  An underscore `_` can
be used as an annotation to replace a group or entry rank with the default.
The pos and defn-note can also change if the `→` (U+2192) is used as part of
the pos or defn-note.  For example:

    dialog <n→wp> {dialog box}

will change the pos from a noun to a word-part.  If you have a compose key
configured on Linux you can type `→` with
<kbd>Compose</kbd><kbd>-</kbd><kbd>&gt;</kbd>.  You can also just copy and
paste as you shouldn't need to type `→` very often.

If the line has no prefix, then any derived forms provided will be matched by
the word and POS and any forms with a single dash (`-`) will be ignored.

If the line has a prefix of `=`, then any derived info will instead replace
the existing ones for that lemma.  Using a dash in this case will cause the
derived forms for that POS place to removed.  To copy over existing derived
info an asterisk (`*`) can be used instead.

If any variant info is given for a lemma or a derived form, then the variant
information for all relevant lemmas or forms will be replaced, including
those without a variant prefix.  For example `(hyaenas | V: hyaena)` will
change the variant info for both _hyaenas_ and _hyaena_ even though _hyaenas_
doesn't have a variant prefix.

SCOWL info is handled separately and can not be changed in the same line as
the other information.  A SCOWL line generally has the form:

    SCOWL-INFO ': ...'

Where the `...` is a literal.  If any SCOWL info is given the line must be
prefixed with one of `+`, `-`, or `=`.  If the prefix is a `+` that scowl info
is added.  If the prefix is a `-` then that specific scowl info is removed.
If the prefix is a `=` then the scowl info is partly replaced.  In particular
any scowl info with a size less then the provided size will be removed.

#### Merging groups

If two lines within the same group match different groups in the database, the
two groups will be merged when the prefix is anything but `~`.

#### Creating new groups

If no lines that match an existing group are found, a new group will be
created.  When adding a group either a SCOWL info line or a line with `~`
prefix must be part of the group.  When the `~` prefix is used that line will
be used to intelligently assign SCOWL info for the group.  For example this:

    ~ rive <v>: -, riven, -, -
    + riven <aj>

will assign `riven` the same SCOWL info as the derived form `riven` for the
verb `rive` as the word matches.

#### Splitting groups

If a line in a different group within the adjust file matches the same group
within the database, the group will be split.  For example:

    cohost <m→n>

    cohost <m→v>

will split `cohost` with the `m` pos into a noun and a verb.  As a shortcut,
when splitting an `m` or `a` pos, you can also use `n_v` and `aj_av` as the
target pos, which will expand into an `n` and `v` or an `aj` and `av`
respectively.  For example, to split the above `cohost` group, you could
instead just write:

    cohost <m→n_v>

When splitting a group other changes must be made to the group to prevent
having the same lemma, pos, and defn-note within more than one group.  To
prevent this in the simple case, whenever a pos is changed, existing groups
with the target pos are merged into the same group.  In other words the above
example is equivalent to:

    ? cohost <n>
    cohost <m→n>

    ? cohost <v>
    cohost <m→v>
  
#### Examples

The most straightforward use of an _adjust_ file is to add variant info.  For
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

The word _thru_ is somewhat of a special case.  It is acceptable to use _thru_
as part of the word _drive-thru_, but generally not considered a proper
spelling of _through_.  It is also different enough in spelling that it is
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

ESDB is a complete overhaul of SCOWLv1 and nearly everything changed.
However, there is limited backward compatibility support via the `mk-list`
script.  If you used `mk-list` in SCOWLv1, it will produce the same
results.  If you created word lists by combining files in
the `final/` directory your scripts will need to be rewritten.  Please use the
`word-list` command of the `scowl` script to get the word lists you want.

If you are using the `word-list` command please note that the variant levels
have changed.  The original 0 level is now levels 0-1, the original 1 variant
level is now 2-4, level 2 is now 5-6, level 3 is now 7-8, and level 4 is 9.
This mapping is also available in the `variants_levels` table in the database.


Creating Hunspell and Aspell Dictionaries
-----------------------------------------

The `speller/` directory of SCOWLv1 has been ported over.  Creating the Aspell
and Hunspell dictionaries should work the same as it did with SCOWLv1.

