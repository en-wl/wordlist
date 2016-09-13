#!/bin/sh

set -x
set -e 

if [ -e scowl.db ]; then
  echo "scowl.db exists, remove it first"
  exit 1
fi

perl sql/to-sql.pl 
sqlite3 scowl.db < sql/create.sql

sqlite3 scowl.db < sql/speller.sql
perl sql/speller.pl
sqlite3 scowl.db < sql/speller-post.sql
