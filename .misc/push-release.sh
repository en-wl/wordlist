
set -e
set -x

( cd git-fr
  git tag -f rel-$SCOWL_VERSION )

test -e release-bk
rm -rf release
cp -al release-bk release

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

set +x
cat <<EOF
Please check everthing is in order and then
  1) ( cd release; rsync -v -n -a --delete . frs.sourceforge.net:/home/frs/project/wordlist/ )
  2) ( cd git-fr; git push -n git@github.com:kevina/wordlist.git master rel-$SCOWL_VERSION )
  3) ( cd git-fr/site; _tasks/deploy )
  4) Go to https://sourceforge.net/projects/wordlist/files/SCOWL/$SCOWL_VERSION/
     and update default version.
EOF
