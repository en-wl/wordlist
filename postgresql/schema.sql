-- PostgreSQL version of the database for easier processing, manually created
-- and must remain in sync with official SqLite3 version.  Expected to be
-- processed with psql

\i 'enums.sql'

--
-- constant tables
--

create type pos_category as enum ('', 'special', 'wordpart', 'nonword');

create table poses (
  order_num integer not null unique,
  pos pos not null primary key,
  base_pos base_pos not null,
  pos_category pos_category not null,
  name text,
  note text,
  extra_info text
);

create table base_poses (
  order_num integer not null unique,
  base_pos base_pos not null primary key,
  lemma_pos pos,
  pos_category pos_category not null,
  descr text,
  extra_info text
);

create table ranks (
  order_num integer not null unique,
  rank_symbol rank_symbol not null primary key,
  rank_descr text
);

create table variant_levels (
  variant_level integer primary key check (0 <= variant_level and variant_level <= 9),
  variant_symbol variant_symbol not null unique,
  variant_descr text,
  legacy_level integer not null
);

create table regions (
  order_num integer not null unique,
  region region not null primary key,
  region_descr text
);

create table spellings (
  order_num integer not null unique,
  spelling spelling not null primary key,
  region region not null references regions(region),
  spelling_descr text not null
);

--
-- normal tables
--

create table groups (
  group_id integer primary key,
  base_pos base_pos not null references base_poses(base_pos),
  pos_class text not null default '',
  defn_note text not null default '',
  usage_note text not null default '',
  lemma_rank rank_symbol not null default '' references ranks(rank_symbol)
);

create table words (
  word_id integer primary key,
  group_id integer not null references groups(group_id),
  lemma_id integer not null references words(word_id),
  pos pos not null references poses(pos),
  word text not null,
  entry_rank rank_symbol default null references ranks(rank_symbol)
);

create unique index words_lemma on words(group_id, word) where word_id = lemma_id;
create index words_lemma_id on words(lemma_id);
create index words_word on words (word);
create index words_idx on words (group_id, pos);

create table lemma_variant_info (
  lemma_id integer not null references words(word_id) on delete cascade,
  spelling spelling not null references spellings(spelling),
  variant_level smallint not null default 0 references variant_levels(variant_level),
  primary key (lemma_id, spelling)
);

create table derived_variant_info (
  word_id integer not null references words(word_id) on delete cascade,
  spelling spelling not null default '_' references spellings(spelling),
  variant_level smallint not null references variant_levels(variant_level),
  primary key (word_id, spelling)
);

create table scowl_data (
  level integer not null check(5 <= level and level <= 95),
  category text not null default '',
  region region not null default '' references regions(region),
  tag text not null default '',
  group_id integer not null references groups(group_id),
  pos pos not null references poses(pos),
  --foreign key (group_id, pos) references words(group_id, pos),
  primary key (level, region, category, tag, group_id, pos)
);
create index scowl_data_index on scowl_data(group_id, pos);

create table scowl_override (
  level integer not null check(5 <= level and level <= 95),
  category text not null default '',
  region region not null default '' references regions(region),
  tag text not null default '',
  word_id integer not null references words(word_id),
  primary key (level, region, category, tag, word_id)
);
create index scowl_override_index on scowl_override(word_id);

create table cluster_comments (
  headword text not null primary key,
  other_words text not null,
  comment text not null
);

create table group_comments (
  group_id integer not null references groups(group_id) on delete cascade,
  word text not null,
  other_words text not null,
  comment text not null,
  primary key (group_id, word)
);

create table lemma_comments (
  lemma_id integer not null references words(word_id) on delete cascade,
  order_num int not null,
  comment text,
  primary key (lemma_id, order_num)
);

--
-- extra tables
--  
-- these tables are populated when exporting but not used when importing
--

create table clusters (
  cluster_id integer primary key
);

create table pos_classes (
  pos_class text primary key
);

create table usage_notes (
  usage_note text primary key
);

create table categories (
  category text primary key
);

create table tags (
  tag text primary key
);

--
-- internal tables
--

create table _combined (
  group_id integer primary key,
  other_id integer not null 
);

--
--
--

