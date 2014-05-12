#VERSION="Version 7.1-0"

if [ -e .svn ];
then
  : ${VERSION:="SVN Verson `svnversion`"}
else
  : ${VERSION:="Version 7.1 (ish)"}
fi
: ${DATE:=`date +'%F'`}
: ${LEVEL:=60}

cat <<EOF
$VERSION
$DATE

README file for English Hunspell dictionaries derived from SCOWL.

These dictionaries are created using the speller/make-hunspell-dict
script in SCOWL.

The NOSUGGEST flag was added to certain taboo words.  While I made an
honest attempt to flag the strongest taboo words with the NOSUGGEST
flag, I MAKE NO GUARANTEE THAT I FLAGGED EVERY POSSIBLE TABOO WORD.
The list was originally derived from Németh László, however I removed
some words which, while being considered taboo by some dictionaries,
are not really considered swear words in today's society.

You can find SCOWL and friend at http://wordlist.sourceforge.net/.
Bug reports should go to the Issue Tracker found on the previously
mentioned web site.  General discussion should go to the
wordlist-devel at sourceforge net mailing list.

COPYRIGHT, SOURCES, and CREDITS:

The English dictionaries come directly from SCOWL (up to level
$LEVEL) and is thus under the same copyright of SCOWL.  The affix file is
a heavily modified version of the original english.aff file which was
released as part of Geoff Kuenning's Ispell and as such is covered by
his BSD license.  Part of SCOWL is also based on Ispell thus the
Ispell copyright is included with the SCOWL copyright.

EOF

cat ../Copyright
echo
echo "Build Date: `date`"
