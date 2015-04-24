
set -e
set -x

if [ -z "$SCOWL_VERSION" -o -z "$PREV_VERSION" ]
then
  echo 'define $PREV_VERSION and $SCOWL_VERSION'
  exit 1
fi

( cd git-fr
  git tag -f rel-$SCOWL_VERSION )

test ! -e release-bk
test -e release
cp -al release release-bk

if [ -e git-fr/stage/agid-$SCOWL_VERSION.zip ]
then
  mkdir release/AGID/$SCOWL_VERSION
  cp git-fr/stage/agid-$SCOWL_VERSION.zip git-fr/stage/agid-$SCOWL_VERSION.tar.gz \
     release/AGID/$SCOWL_VERSION
  cp git-fr/stage/agid-$SCOWL_VERSION/README release/AGID/$SCOWL_VERSION
else
  ( cd release/AGID; ln -s $PREV_VERSION $SCOWL_VERSION)
fi

if [ -e git-fr/stage/varcon-$SCOWL_VERSION.zip ]
then
  mkdir release/VarCon/$SCOWL_VERSION
  cp git-fr/stage/varcon-$SCOWL_VERSION.zip git-fr/stage/varcon-$SCOWL_VERSION.tar.gz \
     release/VarCon/$SCOWL_VERSION
  cp git-fr/stage/varcon-$SCOWL_VERSION/README release/VarCon/$SCOWL_VERSION
else
  ( cd release/VarCon; ln -s $PREV_VERSION $SCOWL_VERSION)
fi

if [ -e git-fr/stage/alt12dicts-$SCOWL_VERSION.zip ]
then
  mkdir release/Alt12Dicts/$SCOWL_VERSION
  cp git-fr/stage/alt12dicts-$SCOWL_VERSION.zip git-fr/stage/alt12dicts-$SCOWL_VERSION.tar.gz \
     release/Alt12Dicts/$SCOWL_VERSION
  cp git-fr/stage/alt12dicts-$SCOWL_VERSION/README release/Alt12Dicts/$SCOWL_VERSION
else
  ( cd release/Alt12Dicts; ln -s $PREV_VERSION $SCOWL_VERSION)
fi

mkdir release/SCOWL/$SCOWL_VERSION
cp git-fr/stage/scowl-$SCOWL_VERSION.zip git-fr/stage/scowl-$SCOWL_VERSION.tar.gz \
   release/SCOWL/$SCOWL_VERSION
cp git-fr/stage/scowl-$SCOWL_VERSION/README release/SCOWL/$SCOWL_VERSION

mkdir release/speller/$SCOWL_VERSION
cp git-fr/scowl/speller/hunspell/*  release/speller/$SCOWL_VERSION
cp git-fr/scowl/speller/aspell/*.tar.bz2 release/speller/$SCOWL_VERSION

set +x
cat <<EOF
Please check everthing is in order and then
  1) ( cd release; rsync -v -n -a --delete . frs.sourceforge.net:/home/frs/project/wordlist/ )
  2) ( cd git-fr; git push -n git@github.com:kevina/wordlist.git master rel-$SCOWL_VERSION )
  3) ( cd git-fr/site; _tasks/deploy )
  4) ( cd git-fr; .misc/update-web-app )
  4) Go to https://sourceforge.net/projects/wordlist/files/SCOWL/$SCOWL_VERSION/
     and update default version.
  5) Go to https://misc.aspell.net/dict-submit/upload.php and upload Aspell 
     dictionary at release/speller/$SCOWL_VERSION/aspell6-en-$SCOWL_VERSION-0.tar.bz2
EOF
