--
-- split n_v back into n/v, and aj_av back into aj_av
--

begin;

create temp table _new_base_pos (
  base_pos text not null primary key,
  a_base_pos text,
  b_base_pos text
);

insert into _new_base_pos values
  ('aj_av', 'aj', 'av'),
  ('n_v', 'n', 'v');

create temp table _groups as
  select g.*, a_base_pos, b_base_pos, coalesce(other_id,group_id + 1) as other_id
    from groups as g
    join _new_base_pos using (base_pos)
    left join _combined using (group_id)
;
create unique index _groups_idx on _groups(group_id);

insert into groups
  select other_id, b_base_pos, pos_class, defn_note, usage_note, lemma_rank
  from _groups;

update or ignore groups as g 
  set base_pos = (select a_base_pos from _groups where group_id = g.group_id);

create temp table _new_pos (
  pos text not null primary key,
  a_pos text,
  b_pos text
);

insert into _new_pos values
  ('a0', 'aj0', 'av0'),
  ('a1', 'aj1', 'av1'),
  ('a2', 'aj2', 'av2'),
  ('m0', 'n0', 'v0'),
  ('ms', 'ns', 'vs');

create table _new_words (
  word_id integer primary key,
  group_id integer,
  lemma_id integer,
  pos text,
  word text,
  entry_rank text,
  orig_word_id integer
);

insert into _new_words (word_id)
  select max(word_id) from words;
  
insert into _new_words (group_id, pos, word, entry_rank, orig_word_id)
  select other_id, b_pos, word, entry_rank, word_id
  from _groups
  join words w using (group_id)
  join _new_pos using (pos)
  where pos in ('a0', 'm0');

update _new_words set lemma_id = word_id;

delete from _new_words where orig_word_id is null;

create temp table _new_lemma_ids as
  select a.lemma_id, b.lemma_id as new_lemma_id from words a join _new_words b on a.word_id = b.orig_word_id;
create unique index _new_lemma_ids_idx on _new_lemma_ids(lemma_id);

insert into _new_words (group_id, lemma_id, pos, word, entry_rank, orig_word_id)
  select other_id, new_lemma_id, b_pos, word, entry_rank, word_id
  from _groups
  join words w using (group_id)
  join _new_pos using (pos)
  join _new_lemma_ids using (lemma_id)
  where pos not in ('a0', 'm0');

insert into words
  select word_id, group_id, lemma_id, pos, word, entry_rank from _new_words;

insert into scowl_data
  select distinct level,category,region,tag,b.group_id, b.pos from (words a join scowl_data s using (group_id,pos)) join _new_words b on a.word_id = b.orig_word_id;

insert into scowl_override
  select distinct level,category,region,tag,b.word_id from (words a join scowl_override s using (word_id)) join _new_words b on a.word_id = b.orig_word_id;

insert into lemma_variant_info
  select b.lemma_id, spelling, variant_level from (words a join lemma_variant_info v using (lemma_id)) join  _new_words b on a.word_id = b.orig_word_id where a.word_id = a.lemma_id;

insert into derived_variant_info
  select b.word_id, spelling, variant_level from (words a join derived_variant_info using (word_id)) join  _new_words b on a.word_id = b.orig_word_id;

insert into lemma_comments
  select b.lemma_id, order_num, comment from (words a join lemma_comments using (lemma_id)) join _new_words b on a.word_id = b.orig_word_id where a.word_id = a.lemma_id;

insert into group_comments
  select other_id,word,other_words,comment from _groups a join group_comments b on a.other_id = b.group_id;

update or ignore words as w
 set pos = (select a_pos from _new_pos where pos = w.pos)
 where group_id in (select group_id from _groups);

update or ignore scowl_data as w
 set pos = (select a_pos from _new_pos where pos = w.pos)
 where group_id in (select group_id from _groups);

update words as w
  set group_id = (select other_id from _groups where group_id = w.group_id),
      lemma_id = (select new_lemma_id from _new_lemma_ids where lemma_id = w.lemma_id)
  where group_id in (select group_id from _groups) and pos in ('vg', 'vn', 'vd');

update scowl_data as w
  set group_id = (select other_id from _groups where group_id = w.group_id)
  where group_id in (select group_id from _groups) and pos in ('vg', 'vn', 'vd');

delete from _combined;

delete from variant_info_mview;
insert into variant_info_mview select * from variant_info;

commit;

