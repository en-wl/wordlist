set -e
set -x

#Update all the README and checkin the results.
#  that should include speller/aspell/doc/ChangeLog

#Define SCOWL_VERSION
#Define PREV_VERSION

if [ -z "$SCOWL_VERSION" -o -z "$PREV_VERSION" ]
then
  echo 'define $PREV_VERSION and $SCOWL_VERSION'
  exit 1
fi

test -e git/.git
test -e git/scowl/README.in

#PREP
  rm -rf git-fr
  git clone git git-fr
  cd git-fr
  mkdir stage
  make

#AGID:
  cd agid
if [ -n "`git rev-list rel-$PREV_VERSION..HEAD .`" ]
then
  git clean -xf .
  cd ..
  cp -a agid stage/agid-$SCOWL_VERSION
  cd stage
  zip -q9rl agid-$SCOWL_VERSION.zip agid-$SCOWL_VERSION/
  tar cfz agid-$SCOWL_VERSION.tar.gz agid-$SCOWL_VERSION/
  cd ..
else
  cd ..
  echo "SKIPPING AGID: No changes"
fi

#VarCon
  cd varcon
if [ -n "`git rev-list rel-$PREV_VERSION..HEAD .`" ]
then
  git clean -xf .
  cd ..
  cp -a varcon stage/varcon-$SCOWL_VERSION
  cd stage
  zip -q9rl varcon-$SCOWL_VERSION.zip varcon-$SCOWL_VERSION/
  tar cfz varcon-$SCOWL_VERSION.tar.gz varcon-$SCOWL_VERSION/
  cd ..
else
  cd ..
  echo "SKIPPING VarCon: No changes"
fi

#Alt12Dicts:
  cd alt12dicts
if [ -n "`git rev-list rel-$PREV_VERSION..HEAD .`" ]
then
  git clean -xf .
  cd ..
  cp -a alt12dicts stage/alt12dicts-$SCOWL_VERSION
  cd stage
  zip -q9rl alt12dicts-$SCOWL_VERSION.zip alt12dicts-$SCOWL_VERSION/
  tar cfz alt12dicts-$SCOWL_VERSION.tar.gz alt12dicts-$SCOWL_VERSION/
  cd ..
else
  cd ..
  echo "SKIPPING Alt12Dicts: No Changes"
fi

#SCOWL:
  cd scowl
  src/make-dist $SCOWL_VERSION
  mv scowl-$SCOWL_VERSION* ../stage
  cd ..

#Speller:
  cd scowl/speller
  make aspell hunspell
  cd aspell
  ln -s ../../../../aspell-lang/proc
  ./proc
  ./configure
  make dist
  cd ../../..

#Test:
  make test
