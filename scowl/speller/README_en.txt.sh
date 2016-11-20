: ${SCOWL:=..}

echo $WHAT

if [ "$SCOWL_VERSION" ] && [ -e $SCOWL/../.git ] > /dev/null; then
  echo "Version $SCOWL_VERSION"
  ( cd $SCOWL/speller && git log --pretty=format:'%cd [%h]' -n 1 -- .. )
  echo
elif [ -e $SCOWL/../.git ] > /dev/null; then
  ( cd $SCOWL/speller && git log --pretty=format:'%cd [%h]' -n 1 -- .. )
  echo
elif [ -e $SCOWL/VERSION ]; then
  echo "Generated from SCOWL Version `cat $SCOWL/VERSION`"
  date
  echo
else
  echo "Unknown Version"
  date
  echo
fi

cat <<EOF
http://wordlist.sourceforge.net

README file for English Hunspell dictionaries derived from SCOWL.

These dictionaries are created using the speller/make-hunspell-dict
script in SCOWL.

The following dictionaries are available:

  en_US (American)
  en_CA (Canadian)
  en_GB-ise (British with "ise" spelling)
  en_GB-ize (British with "ize" spelling)
  en_AU (Australian)

  en_US-large
  en_CA-large
  en_GB-large (with both "ise" and "ize" spelling)
  en_AU-large

The normal (non-large) dictionaries correspond to SCOWL size 60 and,
to encourage consistent spelling, generally only include one spelling
variant for a word.  The large dictionaries correspond to SCOWL size
70 and may include multiple spelling for a word when both variants are
considered almost equal.  The larger dictionaries however (1) have not
been as carefully checked for errors as the normal dictionaries and
thus may contain misspelled or invalid words; and (2) contain
uncommon, yet valid, words that might cause problems as they are
likely to be misspellings of more common words (for example, "ort" and
"calender").

To get an idea of the difference in size, here are 25 random words
only found in the large dictionary for American English:

  Bermejo Freyr's Guenevere Hatshepsut Nottinghamshire arrestment
  crassitudes crural dogwatches errorless fetial flaxseeds godroon
  incretion jalapeño's kelpie kishkes neuroglias pietisms pullulation
  stemwinder stenoses syce thalassic zees

The en_US, en_CA and en_AU are the official dictionaries for Hunspell.
The en_GB and large dictionaries are made available on an experimental
basis.  If you find them useful please send me a quick email at
kevina@gnu.org.

If none of these dictionaries suite you (for example, maybe you want
the normal dictionary that also includes common variants) additional
dictionaries can be generated at http://app.aspell.net/create or by
modifying speller/make-hunspell-dict in SCOWL.  Please do let me know
if you end up publishing a customized dictionary.

If a word is not found in the dictionary or a word is there you think
shouldn't be, you can lookup the word up at http://app.aspell.net/lookup
to help determine why that is.

General comments on these list can be sent directly to me at
kevina@gnu.org or to the wordlist-devel mailing lists
(https://lists.sourceforge.net/lists/listinfo/wordlist-devel).  If you
have specific issues with any of these dictionaries please file a bug
report at https://github.com/kevina/wordlist/issues.

IMPORTANT CHANGES INTRODUCED In 2016.11.20:

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

The English dictionaries come directly from SCOWL $LEVEL
and is thus under the same copyright of SCOWL.  The affix file is
a heavily modified version of the original english.aff file which was
released as part of Geoff Kuenning's Ispell and as such is covered by
his BSD license.  Part of SCOWL is also based on Ispell thus the
Ispell copyright is included with the SCOWL copyright.

EOF

cat $SCOWL/Copyright
echo
echo "Build Date: `date`"
