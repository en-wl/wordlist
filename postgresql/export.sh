#!/bin/sh

: ${SQLITE3:="sqlite3"}

set -e

usage() {
    echo "usage: $0 <database> <schema> <sqlite-db-file>"
    exit 1
}

if [ $# -ne 3 ]; then
    usage
fi

../scowl --db="$3" init-db

echo 'BEGIN;' > data.sql
echo 'PRAGMA foreign_keys=OFF;' >> data.sql
for tbl in `cat tables-core`
do
    pg_dump "$1" --table "$2.$tbl" --section=data --inserts \
        | grep -v -P '^(SET|SELECT)' \
        | sed "s/^INSERT INTO $2./INSERT INTO /" >> data.sql
done
echo 'analyze; ' >> data.sql
echo 'END;' >> data.sql

"$SQLITE3" -init /dev/null --bail "$3" < data.sql

../scowl --db="$3" finalize-db




