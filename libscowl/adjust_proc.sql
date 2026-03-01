-- Requires Sqlite 3.33.0

begin;

---
--- preliminaries
---

PRAGMA defer_foreign_keys = ON;

-- The sqlite3 query planner does not optimize well when tables are empty so
-- hack it a bit by inserting harmless entries in certain tables.  "cross
-- join"s are also used in places below to force a good join order

insert into new_entry_info values (0,0, 0, '');
insert into explicit values (0);
insert into scowl_info_to_clear values (99, '', '', '', 0);
insert into to_remove values (0);

analyze temp;

--
-- tables and views used to split entries as needed
--

create temp table to_split as
  select other_group_id from to_merge group by other_group_id having count(distinct main_group_id) > 1;

create temp table split_info (
  main_group_id integer not null, -- destitution group id
  other_group_id integer not null, -- source group_id
  word_id integer not null,
  new_word_id integer primary key,
  lemma text text not null,
  is_lemma boolean not null
);

insert into split_info
select main_group_id, other_group_id, word_id,
       row_number() over (order by main_group_id,other_group_id,word_id)
         + max((select max(word_id) from words), coalesce((select max(word_id) from new_words), 0)) as new_word_id,
       lemma, word_id == lemma_id as is_lemma
  from to_split
  cross join to_merge using (other_group_id)
  cross join entries on other_group_id = group_id;

create unique index split_info_idx on split_info(main_group_id, word_id);

create temp view split_lemmas as
  select main_group_id, other_group_id, word_id as lemma_id, new_word_id as new_lemma_id
  from split_info
  where is_lemma;

--
-- tables that need to be created before anything is modified
--

-- filter table to optimize certain queries
create temp table group_ids_to_clean_up (group_id integer primary key);
insert or ignore into group_ids_to_clean_up
  select other_group_id as group_id from to_merge;
analyze group_ids_to_clean_up;

create temp table extra_scowl_data as
select other_group_id, a.pos as orig_pos, b.main_group_id, c.pos
  from explicit
    join words a using (word_id)
    join use_info_from on a.group_id = other_group_id
    join new_words b using (main_group_id,word)
    join new_words c on b.lemma_id = c.lemma_id
 where b.word_id = b.lemma_id;
insert into extra_scowl_data values (0, '', 0, '');
analyze extra_scowl_data;

-- used to fixup scowl data
create temp table adj_entry_ranks as
select main_group_id, other_group_id, new_pos as pos, n.entry_rank as adj_rank
   from new_entry_info as n
   cross join words as w using (word_id)
   cross join new_group_info as g using (main_group_id)
   cross join fix_pos as p on g.base_pos = p.base_pos and orig_pos = w.pos
union
  select main_group_id, other_group_id, new_pos, nw.entry_rank as new_entry_rank
   from new_words nw
   cross join new_group_info as g using (main_group_id)
   cross join to_merge using (main_group_id)
   cross join words w on w.group_id = other_group_id and w.word = nw.word
   cross join fix_pos as p on g.base_pos = p.base_pos and orig_pos = w.pos
   where (nw.pos = new_pos or nw.pos = orig_pos) and nw.entry_rank != w.entry_rank;
insert into adj_entry_ranks values(0,0,'','');
analyze adj_entry_ranks;

create temp table default_entry_rank as
select main_group_id,pos,entry_rank as default_entry_rank
  from words w join to_merge on group_id = other_group_id
  group by main_group_id,pos
  having count(distinct entry_rank)==1;
insert into default_entry_rank values (0,'?','');
analyze default_entry_rank;

--
-- fix up groups
--

update groups as a
   set base_pos = b.base_pos,
       defn_note = coalesce(b.defn_note, a.defn_note),
       pos_class = coalesce(b.pos_class, a.pos_class),
       usage_note = coalesce(b.usage_note, a.usage_note),
       group_rank = coalesce(b.group_rank, a.group_rank)
 from new_group_info as b
 where a.group_id = b.main_group_id;

insert or ignore into groups (group_id, base_pos, defn_note, pos_class, usage_note, group_rank)
  select main_group_id, base_pos,
         coalesce(defn_note,''),
         coalesce(pos_class,''),
         coalesce(usage_note,''),
         coalesce(group_rank,'')
  from new_group_info;

--
-- fix up words
--

delete from words where word_id in (select word_id from to_remove);

insert into words (word_id, group_id, lemma_id, pos, word, entry_rank)
  select word_id, main_group_id, coalesce(new_lemma_id, lemma_id), pos, word, coalesce(entry_rank,default_entry_rank,'')
    from new_words
    left join default_entry_rank using (main_group_id, pos)
    left join split_lemmas using (main_group_id, lemma_id);

insert or ignore into fuzzy (word, word_key)
  select word, word_key from new_words;

create temp table adj_words_p0 as
select a.word_id, main_group_id, other_group_id,
       b.lemma_id as new_lemma_id, a.word, new_pos, new_entry_rank as adj_entry_rank, a.entry_rank as orig_entry_rank,
       c.word_id as found_word_id
  from to_merge as m
  cross join groups g on m.main_group_id = g.group_id
  cross join entries as a on m.other_group_id = a.group_id
  left join fix_pos as p on g.base_pos = p.base_pos and a.pos = p.orig_pos
  left join (select word_id, entry_rank as new_entry_rank from new_entry_info) as e using (word_id)
  -- info needed to merge lemmas
  left join (select word_id as lemma_id, group_id, word as lemma from words where word_id = lemma_id) b
    on b.group_id = main_group_id and a.lemma = b.lemma and main_group_id != other_group_id
  left join words c
    on c.group_id = main_group_id and c.lemma_id = b.lemma_id and c.word = a.word and c.pos = new_pos;

create temp table adj_words as
select word_id, new_word_id,
       main_group_id,other_group_id,coalesce(a.new_lemma_id,b.new_lemma_id) as new_lemma_id,word,new_pos,adj_entry_rank,orig_entry_rank
  from adj_words_p0 a
  left join (select main_group_id, other_group_id, a.word_id, a.new_word_id, b.new_word_id as new_lemma_id
               from split_info a join split_info b using (main_group_id, other_group_id, lemma)
              where b.is_lemma) b
    using (main_group_id, other_group_id, word_id)
  where new_pos is not null and found_word_id is null;
;
create index adj_words_idx on adj_words(word_id);

-- delete unused words
create temp table to_remove_also (word_id integer not null);
insert into to_remove_also select word_id from adj_words_p0 where new_pos is null or found_word_id is not null;
insert into to_remove_also select word_id from adj_words where new_word_id is not null;
delete from words where word_id in (select word_id from to_remove_also);
insert or ignore into to_remove select * from to_remove_also;
drop table temp.to_remove_also;

-- insert words to split
insert into words (word_id, group_id, lemma_id, pos, word, entry_rank)
  select new_word_id, main_group_id, new_lemma_id, new_pos, word, coalesce(adj_entry_rank,orig_entry_rank)
    from adj_words where new_word_id is not null;

-- update non-split words
update words as a
   set group_id = main_group_id,
       lemma_id = coalesce(new_lemma_id, lemma_id),
       pos = new_pos,
       entry_rank = coalesce(adj_entry_rank,orig_entry_rank)
  from adj_words as b
 where a.word_id = b.word_id and new_word_id is null;

-- propagate entry ranks across spelling variants
with
  adj_ranks as (
    select group_id, pos, min(a.entry_rank) filter (where a.entry_rank is not null) as entry_rank
      from (select main_group_id as group_id, pos, entry_rank from new_words where entry_rank is not null
            union all
            select main_group_id, new_pos, adj_entry_rank from adj_words) as a
      cross join words w using (group_id, pos)
      group by group_id, pos
      having count(distinct a.entry_rank) == 1
         and count(distinct w.entry_rank) > 1
         and count(*) filter (where a.entry_rank == '*') == 0
         and count(*) filter (where w.entry_rank == '*') == 0)
update words as a set entry_rank = b.entry_rank
  from adj_ranks b
  where a.group_id = b.group_id and a.pos = b.pos;

--
-- fix up lemma_variant_info
--

-- copy over existing lemma_variant_info
insert into new_lemma_variant_info
select main_group_id, new_lemma_id, spelling, variant_level
  from split_lemmas as a
  cross join lemma_variant_info b using (lemma_id)
where not exists (select 1 from new_lemma_variant_info n where a.main_group_id = n.main_group_id);

-- remove unused entries
delete from lemma_variant_info
  where lemma_id in (select word_id from to_remove);

-- update lemma_variant_info
delete from lemma_variant_info
  where lemma_id in (select lemma_id from new_lemma_variant_info);
insert into lemma_variant_info
  select coalesce(new_lemma_id,lemma_id) as lemma_id, spelling, variant_level
    from new_lemma_variant_info
    left join split_lemmas using (main_group_id, lemma_id);

-- cleanup
delete from lemma_variant_info
where lemma_id in (select lemma_id from useless_lemma_variant_entries join group_ids_to_clean_up using (group_id));

--
-- fix up derived_variant_info
--

-- view for derived_variant_info with new ids
create temp view fixed_derived_variant_info as
with
  adj as (select main_group_id,
                 coalesce(new_lemma_id, v.lemma_id) as lemma_id,
                 coalesce(new_pos, v.pos) as pos,
                 coalesce(new_word_id, v.word_id) as word_id,
                 spelling,
                 variant_level
            from new_derived_variant_info v left join adj_words using (main_group_id, word_id))
select v.lemma_id, v.pos, v.word_id,
       coalesce(nullif(v.spelling,'*'),lv.spelling, '_') as spelling,
       v.variant_level
from adj v
left join lemma_variant_info lv on v.spelling = '*' and v.lemma_id = lv.lemma_id;

-- copy over existing derived_variant_info
insert into new_derived_variant_info (main_group_id, word_id, spelling, variant_level)
select main_group_id, new_word_id, spelling, variant_level
  from split_info a
  cross join derived_variant_info v using (word_id)
where exists (select 1 from words n where n.word_id = new_word_id)
  and not exists (select 1 from fixed_derived_variant_info n where n.word_id = new_word_id);

-- remove unused entries
delete from derived_variant_info
  where word_id in (select word_id from to_remove);

-- update derived_variant_info
delete from derived_variant_info
  where word_id in (select w.word_id from fixed_derived_variant_info v cross join words w using (lemma_id, pos));
insert into derived_variant_info
  select word_id, spelling, variant_level from fixed_derived_variant_info;

-- cleanup
drop view fixed_derived_variant_info;

--
-- fix up scowl_data
--

-- when given this line like:
--   - analytic <n>: analytics
--   + _analytics <n>
-- copy of the scowl info for the word analytics to the new lemma of the same word
insert or ignore into scowl_data(size, category, region, tag, group_id, pos)
select sd.size, sd.category, sd.region, sd.tag, main_group_id as group_id, p.new_pos as pos
  from extra_scowl_data e
  join scowl_data sd on e.other_group_id = sd.group_id and e.orig_pos = sd.pos
  join new_group_info f using (main_group_id)
  join fix_pos p on f.base_pos = p.base_pos and e.pos = p.orig_pos;

-- fixup scowl info for new/updated entries
create temp table adj_scowl_data as
  select distinct sd.size,category,region,tag,main_group_id as group_id,new_pos as pos, adj_rank
  from scowl_data as sd
    join to_merge tm on sd.group_id = tm.other_group_id
    join new_group_info g using (main_group_id)
    join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = sd.pos
    left join adj_entry_ranks using (main_group_id, other_group_id, pos);
delete from scowl_data where (group_id) in (select group_id from adj_scowl_data);
insert or ignore into scowl_data(size, category, region, tag, group_id, pos)
  select coalesce(b.size, a.size) as size,
         coalesce(b.category, a.category) as category,
         coalesce(b.region, a.region) as region,
         coalesce(b.tag, a.tag) as tag,
         a.group_id,
         a.pos
    from adj_scowl_data a
    left join (adj_scowl_data b join words w using (group_id, pos))
      on a.group_id = b.group_id and a.pos = b.pos and a.adj_rank = w.entry_rank and b.adj_rank is null;
drop table adj_scowl_data;

-- clear out any requested scowl info and assign any removed entries the same
-- scowl info as the lemma
insert or ignore into scowl_data(size,category,region,tag,group_id,pos)
select sd2.size,sd2.category,sd2.region,sd2.tag,group_id,sd.pos
  from scowl_info_to_clear
  join to_merge using (main_group_id)
  join scowl_data sd using (size, category, region, tag)
  join words as w using (group_id)
  join scowl_data sd2 using (group_id)
  where other_group_id = sd.group_id
    and w.word_id = w.lemma_id
    and w.pos = sd2.pos;
delete from scowl_data
  where (group_id, size, category, region, tag) in
    (select other_group_id, size, category, region, tag
       from scowl_info_to_clear
       join to_merge using (main_group_id));

-- add/update any explicitly provided scowl data
create temp table old_scowl_data as
  select other_group_id as group_id, sd.pos, sd.size
     from (select main_group_id, pos, min(size) as size from new_scowl_data where replace group by main_group_id, pos)  nsd
     join to_merge using (main_group_id)
     join scowl_data sd on sd.group_id = other_group_id and (nsd.pos = '*' or sd.pos = nsd.pos) and sd.size < nsd.size;
delete from scowl_data
  where (group_id, pos, size) in (select * from old_scowl_data);
insert or ignore into scowl_data(size,category,region,tag,group_id,pos)
  select nsd.size,category,region,tag,main_group_id,coalesce(new_pos, nsd.pos)
    from new_scowl_data nsd
    cross join new_group_info g using (main_group_id)
    cross join fix_pos p on g.base_pos = p.base_pos and nsd.pos = orig_pos
  where nsd.pos != '*';
insert or ignore into scowl_data(size,category,region,tag,group_id,pos)
  select size,category,region,tag,main_group_id,w.pos
    from new_scowl_data nsd
    cross join words w on nsd.main_group_id = w.group_id
    -- note: words has already been updated with the corrected pos, so no need to join with fix_pos
  where nsd.pos = '*'
    and (nsd.tag != '[-]'
         or exists (select * from old_scowl_data osd
                    where osd.group_id = nsd.main_group_id and osd.pos = w.pos and osd.size <= nsd.size))
;
drop table old_scowl_data;

--add any explicitly provided scowl overrides
-- fixme?: we might need to be a little more precise.... lemma....
insert or ignore into scowl_override(size,category,region,tag,word_id)
  select size,category,region,tag,word_id
    from new_scowl_override o
    cross join words w on o.main_group_id = w.group_id and o.word = w.word;

-- if a new word form is added give it the same scowl info as the lemma
insert into scowl_data
select b.size, b.category, b.region, b.tag, group_id, w.pos
  from (select distinct main_group_id as group_id, pos from to_merge join words on main_group_id = group_id) as w
  left join scowl_data as a using (group_id, pos)
  left join scowl_data as b using (group_id)
  where a.size is null
    and b.pos in (select lemma_pos from base_poses);

-- cleanup
delete from scowl_data as sd
  where group_id in (select * from group_ids_to_clean_up)
  and not exists (select * from words where group_id = sd.group_id and pos = sd.pos);

--
-- fix up comments
--

-- copy over existing lemma comments
insert into new_lemma_comments
  select main_group_id, lemma_id, order_num, comment
    from split_lemmas s
    cross join lemma_comments l using (lemma_id)
where not exists (select 1 from new_lemma_comments n where n.main_group_id = s.main_group_id and n.lemma_id = l.lemma_id);

-- remove unused lemma comments
delete from lemma_comments
  where lemma_id in (select word_id from to_remove);

-- update lemma comments
delete from lemma_comments
 where lemma_id in (select lemma_id from new_lemma_comments);
insert into lemma_comments (lemma_id, order_num, comment)
  select coalesce(new_lemma_id, lemma_id), order_num, comment
    from new_lemma_comments
    left join split_lemmas using (main_group_id, lemma_id)
   where comment is not null;

-- copy over existing group comments
insert or ignore into new_group_comments (group_id, comment)
select main_group_id, gc.comment
  from to_merge
  cross join group_comments gc on gc.group_id = other_group_id
group by main_group_id
having count(distinct gc.comment) == 1;

-- update group comments
delete from group_comments where group_id in (select group_id from new_group_comments);
insert into group_comments select * from new_group_comments where comment is not null;

-- remove stale cluster comments
delete from cluster_comments where headword in (select headword from new_cluster_comments);

--
-- cleanup
--

delete from groups as g
  where group_id in (select * from group_ids_to_clean_up)
    and not exists (select * from words where group_id = g.group_id);

delete from group_comments as g
  where group_id in (select * from group_ids_to_clean_up)
    and not exists (select * from groups where group_id = g.group_id);

drop table adj_words;
drop table adj_words_p0;
drop view split_lemmas;
drop table split_info;
drop table to_split;

drop table default_entry_rank;
drop table adj_entry_ranks;
drop table extra_scowl_data;

--
-- check
--

create temp table new_duplicate_lemmas as
select lemma, base_pos, defn_note
from use_info_from
join lemmas a on a.group_id = main_group_id
join lemmas b using (lemma, base_pos, defn_note)
group by lemma, base_pos, defn_note having count(distinct b.group_id) > 1;
