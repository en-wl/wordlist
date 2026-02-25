## CHANGES

### 2026.02.25

_Dictionary-only release._

### Word Changes

  * Over 1,500 new high frequency words from the [Corpus of Contemporary
    American English (COCA)](https://www.english-corpora.org/coca/), selected by
    analyzing frequency data from the corpus and using LLMs to help filter the
    results.
  * Over 300 new hand-selected words from
    [GitHub issues](https://github.com/en-wl/wordlist/issues?q=is%3Aissue%20label%3A%22to%20add%22%20milestone%3A%222026-02%20Release%22).
    This includes many modern additions, such as:
    * Tech & Digital: _ChatGPT_, _LLM_, _codebase_ and _tokenize_/_tokenization_
    * Science & Medical: _AstraZeneca_, _BioNTech_, _Moderna_, and _psilocybin_
    * Culture & Society: _neurodiversity_, _influencer_, _doomscrolling_,
      and _staycation_
  * Numerous manual cleanups reported in
    [GitHub issues](https://github.com/en-wl/wordlist/issues?q=label%3A%22variant%20problem%22%20milestone%3A%222026-02%20Release%22);
    for example, _Kyiv_ was added and _Kiev_ was removed from the default
    dictionary and several variant issues were fixed such as _axe/ax_,
    _peddler_/_pedlar_ and _yogurt_/_yoghurt_/_yogourt_.
  * Removal of around 80 uncommon closed forms of compound words such as
    _highhanded_.
  * Removal of around 120 uncommon forms of words such as rarely used _-er_ or
    _-est_ adjective forms and obscure verb forms.
  * Major cleanup of the possessive forms of nouns.
  * Misc. other cleanups due to the change to the new database format.

### Other Changes

  * Words with diacritical marks (e.g., _naïve_) are now treated as normal
    variants.  If word lists were previously generated without the _strip_ option,
    some of these may now be missing from the output, as the marked version is
    officially considered a variant.
  * The Unicode `’` (U+2019) character was added to WORDCHARS in the Hunspell
    affix file so that Hunspell can recognize words with the apostrophe.
    Based on testing, this should allow Hunspell to recognize both `can't` and
    `can’t`.  The ASCII single quote at the end of the word won't be
    considered part of the word, but the Unicode character will.  This means
    `'color'` is okay, but `‘color’` will get flagged when Hunspell does the
    tokenization.
  * Simplified copyright statement.

### (2024-07-23)

GitHub repo. changed over from SCOWLv1 to SCOWLv2.

### 2020.12.07

  * Various new words.
  * Variant cleanups.
  * Bump _irregardless_, _froward_ (+ derivatives) and perpend to level 70.

### 2019.10.06

  * Various new words.
  * Remove _compare's_ and _fail's_.

### 2018.04.16

  * Various new words.
  * Fix build problems on macOS.

### 2017.08.24

  * Various new words.

### 2017.01.22

  * Various new words.

### 2016.11.20

  * New Australian spelling category thanks to the work of Benjamin
    Titze (<btitze@protonmail.ch>)
  * Various new words.

### 2016.06.26

  * Various new words.
  * Updated to Version 6.0.2 of 12dicts
  * Other minor changes.

### 2016.01.19

  * Various new words.
  * Clarified README to indicate why the 60 size is the preferred size
    for spell checking.
  * Remove some very uncommon possessive forms.
  * Change `SET UTF8` to `SET UTF-8` in hunspell affix file.

### 2015.08.24

  * Various new words.

### 2015.05.18

  * Added some new words found to have a high frequency in the COCA
    corpus.  (<http://corpus.byu.edu/coca/>).
  * Fix en spelling suggestions for `alot` and `exersize` in hunspell
    dictionary (upstreamed from the changes made in Firefox).

### 2015.04.24

  * Added some new words.
  * Convert hunspell dictionary to UTF-8 in order to handle smart
    quotes correctly.

### 2015.02.15

  * Added a large number of neologisms (newly invented words)
    such as _selfie_ and _smartwatch_ thanks to Alan Beale.
  * Various other new words.
  * Clean up the special-hacker category by removing some words that
    didn't exist in the Google Book's Corpus (1980 - 2008) and
    originated from the "Unofficial Jargon File Word Lists".

### 2015.01.28

  * Various new words, many from analyzing the Google Book's Corpus
    (1980 - 2008).  See <http://app.aspell.net/lookup-freq>.
  * Moved some uncommon words that can easily hide a misspelling of a
    more common word to level 70.  (_calender_, _adrenalin_ and _Joesph_)
  * Removed several _-er_ and _-est_ forms from adjectives that were so
    uncommon that they were not found anywhere is the Google Book's
    Corpus (1980 - 2008).

### 2014.11.17

  * Various new words.
  * Fix typo in Hunspell readme.

### 2014.08.11.1 (August 13, 2014)

* Forgot to mention this important change from 7.1 to 2014.08.11:

  * Shifted the variant levels up by one: `variant_0` is now `variant_1`,
    `variant_1` is now `variant_2`, and `variant_2` is now `variant_3`.

* Other minor fixes in this README.

* No changes to the contents of the lists.

### 2014.08.11

* Added some missing possessive forms.

* Added some new words and proper names.

* Clean up the categories (words, upper, proper-names etc) so that they
  are more accurate.

* Convert documentation to UTF-8.  For now, the wordlist are still in
  ISO-8859-1 to prevent compatibility problems.

* Add schema and scripts for creating a SQLite database from SCOWL.
  Add some utility and library functions using them.  This database is
  used by the new web app's (<http://app.aspell.net/lookup>
  & [create](http://app.aspell.net/create)).

* Enhance speller/make-hunspell-dict.  The biggest improvement is that
  it that it now generates several more dictionaries in addition to
  the official ones.  These additional dictionaries are ones for
  British English and larger dictionaries that include up to SCOWL
  size 70.

### Revision 7.1 (January 6, 2011)

* Updated to revision 5.1 of Varcon which corrected several errors.

* Fixed various problems with the variant processing which corrected a
  few more errors.

* Added several now common proper names and some other words now
  in common use.

* Include misc/ and speller/ directory which were in SVN but left
  out of the release tarball.

* Other minor fixes, including some fixes to the taboo word lists.

### Revision 7 (December 27, 2010)

* Updated to revision 5.0 of Varcon which corrected many errors,
  especially in the British and Canadian spelling categories.  Also
  added new spelling categories for the British and Canadian spelling
  variants and separated them out from the main `variant_*` categories.
  
* Moved Moby names lists (3897male.nam 4946fema.len 21986na.mes) to 95
  level since they contain too many errors and rare names.

* Moved frequently class 0 from Brian Kelk's Wordlist from 
  level 60 to 70, and also filter it with level 80 due to, too many
  misspellings.

* Many other minor fixes.

### Revision 6 (August 10, 2004)

* Updated to version 4.0 of the 12dicts package.

* Included the 3esl, 2of4brif, and 5desk list from the new 12dicts
  package.  The 3esl was included in the 40 size, the 2of4brif in the
  55 size and the 5desk in the 70 size.

* Removed the Ispell word list as it was a source of too many errors.
  This eliminated the 65 size.

* Removed clause 4 from the Ispell copyright with permission of Geoff
  Kuenning.

* Updated to version 4.1 of VarCon.

* Added the `british_z` spelling category which is British using the
  `ize` spelling.

### Revision 5 (January 3, 2002)

* Added variants that were not really spelling variants (such as
  _forwards_) back into the main list.

* Fixed a bug which caused variants of words to incorrectly appear in
  the non-variant lists.

* Moved rarely used inflections of a word into higher number lists.

* Added other inflections of a words based on the following criteria
  * If the word is in the base form: only include that word.
  * If the word is in a plural form: include the base word and the plural
  * If the word is a verb form (other than plural):  include all verb forms
  * If the word is an ad* form: include all ad* forms
  * If the word is in a possessive form: also include the non-possessive

* Updated to the latest version of many of the source dictionaries.

* Removed the DEC Word List due to the questionable licence and
  because removing it will not seriously decrease the quality of SCOWL
  (there are a few less proper names).  

### Revision 4a (April 4, 2001)

* Reran the scripts on a never version of AGID (3a) which fixes a bug
  which caused some common words to be improperly marked as variants.

### Revision 4 (January 28, 2001)

* Split the variant "spelling category" up into 3 different levels.
  
* Added words in the Ispell word list at the 65 level.

* Other changes due to using more recent versions of various sources
  included a more accurate version of AGID thanks to the work of
  Alan Beale

### Revision 3 (August 18, 2000)

* Renamed special-unix-terms to special-hacker and added a large
  number of commonly used words within the hacker (not cracker)
  community.

* Added a couple more signature words including "newbie".

* Minor changes due to changes in the inflection database.

### Revision 2 (August 5, 2000)

* Moved the male and female name lists from the mwords package and the
  DEC name lists form the 50 level to the 60 level and moved Alan's
  name list from the 60 level to the 50 level.  Also added the top
  1000 male, female, and last names from the 1990 Census report to the
  50 level.  This reduced the number of names in the 50 level from
  17,000 to 7,000.

* Added a large number of Uppercase words to the 50 level.

* Properly accented the possessive form of some words.

* Minor other changes due to changes in my raw data files which have
  not been released yet.  Email if you are interested in these files.

### Revision 1

Initial Release