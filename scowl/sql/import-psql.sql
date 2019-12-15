begin;

create schema orig;
set search_path = orig;

\i sql/schema.sql
\i sql/schema-speller.sql

create index words_word on words (word);
create index speller_words_word on speller_words (word);

\copy words from 'words.tab'
\copy info from 'info.tab'
\copy speller_words from 'speller_words.tab'
\copy post from 'post.tab'
\copy speller_cross from 'speller_cross.tab'
\copy dict_info from 'dict_info.tab'

commit;
