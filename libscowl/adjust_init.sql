begin;

-- note: tables and views must be created with "temp.<name>"
--   (and not create ... temp <name>"
--   as the python code will replace "temp." with "main." when SQL_DEBUG is
--   set to "True"

create table temp.to_merge (
  main_group_id integer,
  other_group_id integer,
  primary key (main_group_id, other_group_id)
) without rowid;

create table temp.to_remove (
 word_id integer primary key,
 explicit boolean not null default false
);

create table temp.new_words (
  word_id integer primary key,
  main_group_id integer not null,
  lemma_id integer not null,
  pos text not null,
  word text not null,
  entry_rank text default ''
);

create table temp.new_lemma_variant_info (
  main_group_id integer,
  lemma_id integer,
  spelling text,
  variant_level smallint,
  primary key (main_group_id, lemma_id, spelling)
) without rowid;

create table temp.new_lemma_comments (
  lemma_id integer not null,
  order_num int not null,
  comment text,
  primary key (lemma_id, order_num)
) without rowid;

create table temp.new_derived_variant_info (
  lemma_id integer,
  pos text,
  word_id integer,
  spelling text,
  variant_level smallint,
  primary key (word_id, spelling)
) without rowid;

create table temp.new_group_info (
  main_group_id integer primary key,
  base_pos text not null,
  defn_note text,
  pos_class text,
  usage_note text,
  lemma_rank text
); 

create table temp.new_entry_info (
  word_id integer primary key,
  main_group_id integer not null,
  other_group_id integer not null,
  entry_rank text
);

create table temp.scowl_info_to_clear (
  level integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  primary key (main_group_id, level, category, region, tag)
) without rowid;

create table temp.new_scowl_data (
  level integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  pos text,
  replace boolean,
  primary key (main_group_id, pos, level, category, region, tag)
) without rowid;

create table temp.new_scowl_override (
  level integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  word text,
  replace boolean,
  primary key (main_group_id, word, level, category, region, tag)
) without rowid;

create table temp.new_group_comments (
  group_id integer primary key,
  comment text
);

commit;
