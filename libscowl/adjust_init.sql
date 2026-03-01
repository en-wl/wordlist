begin;

-- note: tables and views must be created with "temp.<name>"
--   (and not create ... temp <name>"
--   as the python code will replace "temp." with "main." when SQL_DEBUG is
--   set to "True"

create table temp.use_info_from (
  main_group_id integer, -- destitution group id
  other_group_id integer, -- source group_id
  also_merge boolean not null default true,
  primary key (main_group_id, other_group_id)
) without rowid;

create view temp.to_merge as
  select main_group_id, other_group_id
  from temp.use_info_from
  where also_merge;
select * from temp.to_merge limit 0;

create table temp.to_remove (
 word_id integer primary key
);

create table temp.explicit (
 word_id integer primary key
);

create table temp.new_words (
  word_id integer primary key,
  main_group_id integer not null,
  lemma_id integer not null,
  pos text text not null,
  word text text not null,
  word_key text not null,
  entry_rank text
);

create table temp.new_lemma_variant_info (
  main_group_id integer,
  lemma_id integer,
  spelling text,
  variant_level smallint,
  primary key (main_group_id, lemma_id, spelling)
) without rowid;

create table temp.new_lemma_comments (
  main_group_id integer not null,
  lemma_id integer not null,
  order_num int not null,
  comment text,
  primary key (main_group_id, lemma_id, order_num)
) without rowid;

create table temp.new_derived_variant_info (
  main_group_id integer not null,
  lemma_id integer,
  pos text,
  word_id integer not null,
  spelling text not null,
  variant_level smallint not null,
  primary key (word_id, main_group_id, spelling)
) without rowid;

create table temp.new_group_info (
  main_group_id integer primary key,
  base_pos text not null,
  defn_note text,
  pos_class text,
  usage_note text,
  group_rank text
); 

create table temp.new_entry_info (
  word_id integer primary key,
  main_group_id integer not null,
  other_group_id integer not null,
  entry_rank text not null
);

create table temp.scowl_info_to_clear (
  size integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  primary key (main_group_id, size, category, region, tag)
) without rowid;

create table temp.new_scowl_data (
  size integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  pos text,
  replace boolean,
  primary key (main_group_id, pos, size, category, region, tag)
) without rowid;

create table temp.new_scowl_override (
  size integer,
  category text default '',
  region text default '',
  tag text default '',
  main_group_id integer,
  word text,
  replace boolean,
  primary key (main_group_id, word, size, category, region, tag)
) without rowid;

create table temp.new_group_comments (
  group_id integer primary key,
  comment text -- null to remove comment
);

create table temp.new_cluster_comments (
  headword text not null primary key,
  other_words text,
  comment text -- null to remove comment
) without rowid;



commit;
