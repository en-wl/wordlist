#/bin/sh

set -e

usage () {
    echo 'usage: $0 <database> [<typeschema>] <schema> [drop]'
    exit 1
}

if [ $# -lt 2 ]; then
    usage
elif [ $# -eq 2 ]; then
    PGDATABASE="$1"
    TYPESCHEMA="$2"
    SCHEMA="$2"
elif [ $# -eq 3 ]; then
    if [ "$3" = drop ]; then
        DROP_SCHEMA="drop schema if exists $SCHEMA cascade;"
        PGDATABASE="$1"
        TYPESCHEMA="$2"
        SCHEMA="$2"
    else
        PGDATABASE="$1"
        TYPESCHEMA="$2"
        SCHEMA="$3"
    fi
elif [ $# -eq 4 ]; then
    if [ "$4" = drop ]; then
        DROP_SCHEMA="drop schema if exists $SCHEMA cascade;"
        PGDATABASE="$1"
        TYPESCHEMA="$2"
        SCHEMA="$3"
    else
        usage
    fi
fi

: ${SQLITE3:="sqlite3"}
: ${SCOWL_DB:="../scowl.db"}
PSQL="psql"

TRUNCATE_ALL="truncate `cat tables-const tables-core tables-aux | paste -s -d, -`;"

(
  for tbl in `cat tables-const tables-core tables-aux`
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

"$PSQL" --no-psqlrc $PGDATABASE <<EOF
SET client_min_messages = warning;
\set ON_ERROR_STOP true
begin;
$DROP_SCHEMA
SELECT 
  not exists (select 1 FROM information_schema.schemata WHERE schema_name = '$TYPESCHEMA') as create_types,
  not exists (select 1 FROM information_schema.schemata WHERE schema_name = '$SCHEMA') as create_schema;
\gset
\if :create_types
  create schema $TYPESCHEMA;
  set search_path=$TYPESCHEMA;
  \i types.sql
\endif
set search_path=$SCHEMA,$TYPESCHEMA;
\if :create_schema
  create schema if not exists $SCHEMA;
  \i schema.sql
  \i views.sql
  \i scowl.sql
  alter view duplicate_derived_view rename to duplicate_derived;
\else
  $TRUNCATE_ALL
\endif
\i data.sql
commit;
EOF
