#!/bin/sh

SQLITE3=${SQLITE3:-sqlite3}
SQLITE_DB="../scowl2.db"
PGDATABASE="scowl"
SCHEMA="v2"

set -e


echo 'BEGIN;' > data.sql
echo 'PRAGMA foreign_keys=OFF;' >> data.sql
pg_dump $PGDATABASE --schema $SCHEMA --data-only --inserts | grep -v -P '^(SET|SELECT)' | sed "s/^INSERT INTO $SCHEMA./INSERT INTO /" >> data.sql
echo 'insert into duplicate_derived select * from duplicate_derived_view;' >> data.sql
echo 'insert into variant_info select * from variant_info_view;' >> data.sql
echo 'analyze; ' >> data.sql
echo 'END;' >> data.sql

cat ../libscowl/schema.sql data.sql ../libscowl/views.sql ../libscowl/scowl.sql | "$SQLITE3" -init /dev/null --bail "$SQLITE_DB"

