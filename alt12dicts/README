Unofficial Alternate 12Dicts package (Alt12Dicts)
Files by Alan Beale
Packaged by Kevin Atkinson

Version 2020.12.07

The files contained in this archive are the result of a rather
extensive conversation between me (Kevin Atkinson) and Alan Beale, the
author of the 12Dicts package.  I can be contacted at kevina@gnu.org
and Alan Beale can be contacted at biljir@pobox.com.  This archive
contains almost all the information originally found in release 4 of
the official 12Dicts package but in a different format as well as a
good deal of additional information.

This version has been updated with information from version 6.0.2 of
the official 12Dicts package, Version 5 and 6 of 12Dicts include a
number of new files not found in version 4; this package does not
include those yet.

The latest version of this package and the official 12Dicts package can
be found at http://wordlist.aspell.net/

The file README-orig contains the original Readme file distributed
with the official 12Dicts package.  README-infl contains the Readme
file for 2of12infl.txt and finally README-agid contains the Readme for
AGID which 2of12infl.txt is based on.

All of these files have been explicitly placed in the Public Domain by
Alan Beale.


2of12full.txt description:

The file 2of12full.txt contains the all words appearing in more than
than one of Alan Beale's source dictionaries.  Each line contains five
numbers, being the total number of dictionaries, the non-variant
entries, the variant entries, the non-American entries and the
"second-class" entries (appearances without a separate definition).
Counts of zero are replaced by hyphens.  For instance, the entry

7:  -  2#  5& -=   aeroplane

indicates that the word "aeroplane" is listed in 7 of the
dictionaries.  None list it as a primary American word, 2 list it as a
variant form, and 5 list it as a non-American word, and none list it
as a second-class word.  Note that words may be marked with a "&" for
either of 2 reasons.  They may represent a non-American spelling of an
American word, such as "aeroplane" or "gaol", or they may represent a
word not normally used in American English, such as "bloke" or
"lorry". Also note that there are two main kinds of second-class words
- ones listed in the entry for another word without definition
(usually associated with the suffixes -ly, -ness or -er/or), and ones
appearing in a list of undefined words with a common prefix. Finally,
observe that the numbers of non-variant, variant and non-American
entries will sum to the total dictionary count, while the scond-class
entry count is independent of them, except that of course it is never
greater than the total count.

Words marked with a colon (":") after it are abbreviations which are
entirely lower-case and alphabetic.

This file contains almost all the information found in the normal
12Dicts with two exceptions:

1) "Signature words" which did not appear in at least two dictionaries
are not included in 2of12full

2) The sources used differ in one respect from those for the 2of12 and
6of12 files. See README-infl for a full description.


signature.txt description:

The file signature.txt contains a list of signature words.  Signature
words are words are words which failed are not in at least 6
dictionaries but Alan Beale thought should be included at the 6of12
level (see README-orig).  Examples of some of the sorts of words are
included are:

1.  Words of the same category as other included words.  An example is
    the astrological sign "Cancer", which alone of all the astro-
    logical signs fails to appear in 6 or more of the dictionaries.
    Similarly, the omitted holiday "Christmas Eve" was added.
2.  Vulgarities, sexual terms and insults.  Some such words were
    already included, but most of the source dictionaries were quite
    squeamish about them.  These words are very widely known indeed;
    I hold that any list of "common" words which does not include the
    infamous f-word is simply discredited thereby.  Some may feel that
    it would have been better to leave some or all of these terms
    unmentioned.  Nevertheless, the expression of blasphemy,
    unwarranted contempt, and perverse lust, whether in words or in
    deeds, is a very human trait.  Suppressing the evidence of these
    aspects of the human condition in our language makes no more sense
    than excluding "leprosy", "gangrene" and "dementia", no matter how
    unpleasant they may be to contemplate.
3.  Conventional conversational phrases so common as to be practically
    invisible to native speakers.  Examples are "thank you", "good
    night", "uh-huh", "of course" and "gesundheit".
4.  Sports terminology, especially for football and baseball.


signature2.txt description:

The file signature2.txt contains inflections of irregular verbs not
explicitly mentioned in 2 source dictionaries, such as "outfought" and
"reheard".


variants.txt description:

The variants.txt file contains a subset of the words appearing in at
least one of the 12 source dictionaries marked as variants or
non-American.  This list contains only the words which are spelling
variants, words which represent different ways of saying the same
thing (such as "henceforward" as a variant of "henceforth") and
non-American words without a similar American form (such as "telly")
have been removed.  Each entry is followed by a tab, and a notation
indicating which of several classes the word falls into.  To describe
the classes, it is best to do a little algebra.  Let NV be the total
number of non-variants, A the number of American variants, B the
number of non-American variants, and V=A+B.  Then the following
annotations are to be interpreted as follows:

#! - A >= B, NV = 0
&! - A < B, NV = 0
#  - A >= B, V > NV
&  - A < B, V > NV
#? - A >= B, 0.65*NV < V <= NV
&? - A < B, 0.65*NV < V <= NV

Simplifying, the choice between # and & indicates which variety of
variant dominates, while ! and ? indicate a stronger or weaker than
average agreement on variance.

Additional notes on the list from Alan:

  I should note a couple other characteristics of this file.  First of
  all, there are cases where spellings exist which are clearly
  variants of one another, but where this is not recognized by the
  source dictionaries.  An example is the pair "levelheaded" and
  "level-headed".  These are clearly the same word, but none of my
  sources lists both of them.  I have chosen not to go beyond the
  source dictionaries and put such words on the variants list, even in
  obvious cases like this one.

  I should also note that there are cases where the question of
  whether 2 words are spelling variants or actually different words is
  not easy to answer.  For instance, consider the pairs
  "lengthways"/"lengthwise" or "toward"/"towards".  I've simply made
  whatever decision seemed best to me in cases like this ("lengthways"
  is a variant, "towards" is not), but recognize that any other
  observer (who could bring himself to care) would be likely to
  occasionally disagree.

Variants.txt has not been updated for release 6, as critical
information about how the list was constructed has unfortunately been
lost.


abbr.txt description:

This file contains (almost) all the abbreviations and acronyms from
the 12Dicts sources.  Abbreviations which also in a list of common
personal names (of about the same completeness as the ESL dictionaries)
are marked with a tilda ("~") after it.  There are still likely to be
some abbreviations not marked with a tilda that match less common
names.

Additional notes from Alan:

  For words containing upper-case, I [Alan Beale] had not recorded
  whether a word was an abbreviation, so I was forced to remove the
  non-abbreviations from the list by hand. Because of the need to
  remove non-abbreviations, I limited myself to consideration of
  upper-case words of 6 or fewer characters.  It is possible that a
  small number of acronyms or abbreviations longer than 6 characters
  might have been missed.


variant-notes.txt description:

The file variant-notes.txt contains some additional notes on
questionable variants sent to me when I pointed out that nought was
not marked as a variant.


2of12id.txt description:

See README-infl


2of4brif.txt, 3esl.txt, and 5desk.txt neol2016.txt description:

These files are identical to the original files in the 12Dicts package.
See README-orig for more info.


neol2016.poss description:

Possessive forms for words in neol2016.txt.  (Created by hand by
Kevin Atkinson, not provided by Alan).


signature3a.txt description:

The signature phrases from 3of6all.txt.


signature3g.txt description:

The signature words from 3of6game.txt.


signature4lem.txt description:

Extra head words added to 2+2+3lem to add British/American versions of
words when only one form was present, plus a few other words added for
various reasons.


signature4cmn.txt description:

Some very common abbreviations, capitalized words and contractions not
present in the BYU data, added to 2+2+3cmn.txt.


5d+2a.names2016.txt description:

A short list of names of renowned individuals since 1999 (plus one
government program and one social media site), added to 5d+2a.txt.
