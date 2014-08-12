set -e
set -x

#Update all the README and checkin the results.

#Define SCOWL_VERSION

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
  git clean -xf .
  cd ..
  cp -a agid stage/agid-$SCOWL_VERSION
  cd stage
  zip -q9rl agid-$SCOWL_VERSION.zip agid-$SCOWL_VERSION/
  tar cfz agid-$SCOWL_VERSION.tar.gz agid-$SCOWL_VERSION/
  cd ..

#VarCon
  cd varcon
  git clean -xf .
  cd ..
  cp -a varcon stage/varcon-$SCOWL_VERSION
  cd stage
  zip -q9rl varcon-$SCOWL_VERSION.zip varcon-$SCOWL_VERSION/
  tar cfz varcon-$SCOWL_VERSION.tar.gz varcon-$SCOWL_VERSION/
  cd ..

#Alt12Dicts:
  cd alt12dicts
  git clean -xf .
  cd ..
  cp -a alt12dicts stage/alt12dicts-$SCOWL_VERSION
  cd stage
  zip -q9rl alt12dicts-$SCOWL_VERSION.zip alt12dicts-$SCOWL_VERSION/
  tar cfz alt12dicts-$SCOWL_VERSION.tar.gz alt12dicts-$SCOWL_VERSION/
  cd ..

#SCOWL:
  cd scowl
  src/make-dist $SCOWL_VERSION
  mv scowl-$SCOWL_VERSION* ../stage
  cd ..

#Speller:
  cd scowl/speller
  make aspell hunspell



