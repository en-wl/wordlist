: ${SCOWL:=..}

if [ "$1" = "" ]; then
    echo "English Hunspell Dictionaries"
else
    echo "$1 Hunspell Dictionary"
fi
sh "$SCOWL/speller/HEADER.sh"

cat <<EOF
README file for English Hunspell dictionaries derived from SCOWL.

These dictionaries are created using the speller/make-hunspell-dict
script in SCOWL.

The following dictionaries are available:

  en_US (American)
  en_CA (Canadian)
  en_GB-ise (British with -ise/traditional spelling)
  en_GB-ize (British with -ize/Oxford spelling)
  en_AU (Australian)

  en_US-large
  en_CA-large
  en_GB-large (with both -ise and -ize spelling)
  en_AU-large

The default dictionaries correspond to SCOWL size 60 and, to encourage
consistent spelling, generally only include one spelling variant for a word.
The large dictionaries correspond to SCOWL size 70 and include common
spelling variants.  The larger dictionaries, however, (1) have not been as
carefully checked for errors as the normal dictionaries and thus may contain
misspelled or invalid words; and (2) contain uncommon, yet valid, words that
might cause problems as they are likely to be misspellings of more common
words (for example, "ort" and "calender").

The American, Canadian, and Australian dictionaries are considered the
official version for Hunspell.  The British ones are considered an 
alternative version.

For additional information, including information on how to contribute, see
https://wordlist.aspell.net/dicts/.

IMPORTANT CHANGES INTRODUCED ON 2026-02-22:

The Unicode "’" (U+2019) character was added to WORDCHARS so that Hunspell can
recognize words with the apostrophe.  Based on testing, this should allow
Hunspell to recognize both "can't" and "can’t".  The ASCII single quote at the
end of the word won't be considered part of the word, but the Unicode
character will.  This means "'color'" is okay, but "‘color’" will get flagged
when Hunspell does the tokenization.

IMPORTANT CHANGES INTRODUCED IN 2016.11.20:

New Australian dictionaries thanks to the work of Benjamin Titze
(btitze@protonmail.ch).

IMPORTANT CHANGES INTRODUCED IN 2016.04.24:

The dictionaries are now in UTF-8 format instead of ISO-8859-1.  This
was required to handle smart quotes correctly.

IMPORTANT CHANGES INTRODUCED IN 2016.01.19:

"SET UTF8" was changes to "SET UTF-8" in the affix file as some
versions of Hunspell do not recognize "UTF8".

ADDITIONAL NOTES:

The NOSUGGEST flag was added to certain taboo words.  While I made an
honest attempt to flag the strongest taboo words with the NOSUGGEST
flag, I MAKE NO GUARANTEE THAT I FLAGGED EVERY POSSIBLE TABOO WORD.
The list was originally derived from Németh László, however I removed
some words which, while being considered taboo by some dictionaries,
are not really considered swear words in today's society.

COPYRIGHT, SOURCES, and CREDITS:

The English dictionaries come directly from SCOWL and is thus under
the same copyright terms as SCOWL.  The affix file is a heavily
modified version of the original english.aff file, which was
released as part of Geoff Kuenning's Ispell and as such is covered by
his BSD license.

EOF

sh "$SCOWL/speller/Copyright.sh"

echo "Build Date: `date`"
