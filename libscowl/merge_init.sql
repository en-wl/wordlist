begin;

-- note: tables and views must be created with "temp.<name>"
--   (and not create ... temp <name>"
--   as the python code will replace "temp." with "main." when SQL_DEBUG is
--   set to "True"

create table temp.new_groups (
  idx integer primary key,
  base_pos text not null,
  pos_class text,
  defn_note text,
  usage_note text,
  group_rank text
);

create table temp.new_lemmas (
  idx integer not null,
  lemma text not null,
  primary key(idx, lemma)
) without rowid;
create index new_lemmas_idx on new_lemmas(lemma);

commit;

