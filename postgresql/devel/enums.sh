#/bin/sh

SQLITE3=${SQLITE3:-/opt/sqlite3/bin/sqlite3}

$SQLITE3 ../scowl.db < devel/export-enums.sql > enums.sql

