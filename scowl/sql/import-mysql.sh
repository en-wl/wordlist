#!/bin/sh

set -e

mysql -v -v -A scowl < sql/import-mysql.sql

mysqlimport --local --fields-terminated-by='\t' --fields-enclosed-by='' scowl \
  words.tab info.tab \
  speller_words.tab post.tab speller_cross.tab dict_info.tab

