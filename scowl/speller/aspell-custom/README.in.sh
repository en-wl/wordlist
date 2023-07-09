cat <<EOF
GNU Aspell 0.60 Custom English Dictionary Package
$GIT_VER
Original Word List By:
  Kevin Atkinson <kevina at gnu org>
Copyright Terms: Copyrighted (see the file Copyright for the exact terms)
Wordlist URL: http://wordlist.aspell.net/

Created with http://app.aspell.net/create with the following parameters:
`cat "$PARMS_FILE"`

This is a Custom English dictionary for Aspell.  It requires Aspell 
version 0.60 or better.

If Aspell is installed and aspell and prezip-bin are all
in the path first do a:

  ./configure

Which should output something like:
  
  Finding Dictionary file location ... /usr/local/lib/aspell
  Finding Data file location ... /usr/local/share/aspell
  Testing if an English dictionary is already installed ... yes

if it did not something likely went wrong.

As this is a custom dictionary it is meant to coexist with the
existing English dictionary.  If the configure script detects 

and as such the language data files will
not be installed unless the configure script detectes

After that build the package with:
  make
and then optionally install it with
  make install

If any of the above mentioned programs are not in your path than the
variables, ASPELL and/or PREZIP need to be set to the
commands (with path) to run the utilities.  These variables may be set
in the environment before configure is run or specified at the command
line using the following syntax
  ./configure --vars VAR1=VAL1 ...
Other useful variables configure recognizes are ASPELL_PARMS.

To clean up after the build:
  make clean

To uninstall the files:
  make uninstall

After the custom dictionary is installed you can use with the "-d" or
"--master" option of Aspell.  For example:
  aspell -d en-custom ...

If you wish to make this the default dictionary for a particular
language you can use use the "add-dict-alias" config option.  For
example to to make it the default for en_US:
  echo 'add-dict-alias en_US en-custom' >> `aspell config per-conf-path`

If you wish to use this dictionary with a particular program than does
not allow you to directly select the dictionary than you can also add
the alias to the ASPELL_CONF env. variable, for example:
  ASPELL_CONF='add-dict-alias en_US en-custom' emacs

If you already have an English dictionary installed and do not wish to
install this custom dictionary you can simply use the dictionary file
(en-custom.rws) directly, for example:
  aspell -d /<path-to-file>/en-custom.rws
or
  ASPELL_CONF='add-dict-alias en_US /<path-to-file>/en-custom.rws' emacs

The individual word lists have an extension of ".cwl" and are
compressed to save space.  To uncompress a word list use 
"preunzip BASE.cwl" which will uncompress it and rename the file 
to "BASE.wl".  To dump a compressed word list to standard output use
"precat BASE.cwl".  To uncompress all word lists in the current
directory use "preunzip *.cwl".  For more help on "preunzip" use
"preunzip --help".

If you have any problem with installing or using the word lists please
let the Aspell maintainer, Kevin Atkinson, know at kevina@gnu.org.

Any additional documentation that came with the original word list can
be found in the doc/ directory.
EOF

