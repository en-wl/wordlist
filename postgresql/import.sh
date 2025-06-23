#/bin/sh

set -e

if [ $# -lt 2 -o \( $# -eq 3 -a "$3" != drop \) -o $# -gt 3 ]
then
    echo 'usage: $0 <database> <schema> [drop]'
    exit 1
fi

: ${SQLITE3:="sqlite3"}
: ${SCOWL_DB:="../scowl.db"}
PSQL="psql"
PGDATABASE="$1"
SCHEMA="$2"

(
  for tbl in `cat tables`
  do
      cat <<EOF
COPY $tbl FROM stdin WITH (FORMAT csv, QUOTE '''', NULL 'NULL');
EOF
      "$SQLITE3" -init /dev/null "$SCOWL_DB" <<EOF
.mode quote
.nullvalue '\N'
select * from $tbl;
EOF
      cat <<EOF
\.
analyze $tbl;
EOF
  done
) > data.sql

if [ "$3" = drop ]; then
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
\i views.sql
alter view variant_info_view rename to variant_info;
\i scowl.sql
alter view duplicate_derived_view rename to duplicate_derived;
EOF
