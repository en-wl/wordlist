ALTER DATABASE
  CHARACTER SET = utf8
  COLLATE = utf8_bin;

SET storage_engine=MYISAM;

\. sql/schema.sql
\. sql/schema-speller.sql

create index words_word on words (word(16));
create index speller_words_word on speller_words (word(16));

