#!/bin/sh

sqlite3 scowl.db < sql/export.sql
sqlite3 scowl.db < sql/export-speller.sql
