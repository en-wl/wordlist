#/bin/sh

set -e

SQLITE3=${SQLITE3:-sqlite3}
SQLITE_DB="../scowl.db"
PSQL="psql"
PGDATABASE="scowl"
SCHEMA="v2"

(
  for tbl in `cat tables`
  do
      cat <<EOF
COPY $tbl FROM stdin WITH (FORMAT csv, QUOTE '''', NULL 'NULL');
EOF
      "$SQLITE3" "$SQLITE_DB" <<EOF
.mode quote
.nullvalue '\N'
select * from $tbl;
EOF
      cat <<EOF
\.
EOF
  done
) > data.sql

if [ "$1" = drop ]; then
    DROP_SCHEMA="drop schema if exists $SCHEMA cascade;"
fi

"$PSQL" $PGDATABASE <<EOF
SET client_min_messages = warning;
begin;
$DROP_SCHEMA
create schema if not exists $SCHEMA;
set search_path=$SCHEMA;
\i schema.sql
\i data.sql
commit;
analyze;
\i views.sql
alter view variant_info rename to variant_info_mview;
\i scowl.sql
alter view variant_info_mview rename to variant_info;
EOF
