#/bin/sh

SQLITE3=${SQLITE3:-/opt/sqlite3/bin/sqlite3}

$SQLITE3 -init /dev/null ../scowl.db < devel/export-enums.sql > enums.sql

