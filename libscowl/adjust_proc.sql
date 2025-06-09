-- Requires Sqlite 3.33.0

begin;

---
--- preliminaries
---

-- The sqlite3 query planner does not optimize well when tables are empty so
-- hack it a bit by inserting harmless entries in certain tables.  "cross
-- join"s are also used in places below to force a good join order

insert into new_entry_info values (0,0,0,'');

analyze temp;

-- filter table to optimize certain queries
create temp table group_ids_to_clean_up (group_id integer primary key);
insert or ignore into group_ids_to_clean_up
  select other_group_id as group_id from to_merge;
analyze group_ids_to_clean_up;

-- these two tables are used to fixup scowl_data, they needs to be created
-- before anything is updated

create temp table extra_scowl_data as
select other_group_id, a.pos as orig_pos, b.main_group_id, c.pos
  from to_remove
    join words a using (word_id)
    join to_merge on a.group_id = other_group_id
    join new_words b using (main_group_id,word)
    join new_words c on b.lemma_id = c.lemma_id
 where explicit and b.word_id = b.lemma_id;
insert into extra_scowl_data values (0, '', 0, '');
analyze extra_scowl_data;

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

--
-- fix up groups
--

update groups as a
   set base_pos = b.base_pos,
       defn_note = coalesce(b.defn_note, a.defn_note),
       pos_class = coalesce(b.pos_class, a.pos_class),
       usage_note = coalesce(b.usage_note, a.usage_note),
       lemma_rank = coalesce(b.lemma_rank, a.lemma_rank)
 from new_group_info as b
 where a.group_id = b.main_group_id;

insert or ignore into groups (group_id, base_pos, defn_note, pos_class, usage_note, lemma_rank)
  select main_group_id, base_pos,
         coalesce(defn_note,''),
         coalesce(pos_class,''),
         coalesce(usage_note,''),
         coalesce(lemma_rank,'')
  from new_group_info;

--
-- fix up words and lemma_variant_info
--

delete from words where word_id in (select word_id from to_remove);

insert into words select * from new_words;

-- words to split into new entries as they will end up in more than one group
create temp table split_info as
      select row_number() over (order by main_group_id,base_pos,word) + (select max(word_id) from words) as new_word_lemma_id,
      w.lemma_id as lemma_id, main_group_id, g.base_pos, word, other_group_id, w.pos as orig_pos
from to_merge join words as w on other_group_id = w.group_id join groups g on main_group_id = g.group_id
where w.pos = '?' and g.base_pos != '';

delete from words where lemma_id in (select lemma_id from split_info);
insert into words
  select new_word_lemma_id, main_group_id, new_word_lemma_id, new_pos, word, ''
    from split_info left join fix_pos using (base_pos, orig_pos);

delete from lemma_variant_info
  where lemma_id in (select lemma_id from new_lemma_variant_info);
insert into lemma_variant_info
  select coalesce(new_word_lemma_id,lemma_id) as lemma_id, spelling, variant_level
    from new_lemma_variant_info
    left join split_info using (main_group_id, lemma_id);

drop table split_info;

update words set group_id = main_group_id
from to_merge
where words.group_id = to_merge.other_group_id and to_merge.other_group_id != to_merge.main_group_id;

update words as a
   set pos = new_pos
  from new_group_info g, fix_pos as b
  where a.group_id = main_group_id and g.base_pos = b.base_pos and a.pos = b.orig_pos
    and a.pos != new_pos;

delete from words
  where word_id in (select word_id
                      from words a
                      join new_group_info g on a.group_id = main_group_id
                      left join fix_pos as b on g.base_pos = b.base_pos and a.pos = b.orig_pos
                     where new_pos is null);

update words as a set entry_rank = b.entry_rank
  from new_entry_info b
  where a.word_id = b.word_id;

delete from lemma_variant_info
where lemma_id in (select lemma_id from useless_lemma_variant_entries join group_ids_to_clean_up using (group_id));

--
-- fix up derived_variant_info
--

insert into new_derived_variant_info
  select v.lemma_id, v.pos, word_id, coalesce(lv.spelling, '_') as spelling, v.variant_level
  from new_derived_variant_info v left join words w using (word_id) left join lemma_variant_info lv using (lemma_id)
  where v.spelling = '*';
delete from new_derived_variant_info
  where spelling = '*';

delete from derived_variant_info
  where word_id in (select w.word_id from new_derived_variant_info v join words w using (lemma_id, pos));
insert into derived_variant_info
  select word_id, spelling, variant_level from new_derived_variant_info;

--
-- fix up scowl_data
--

-- when given this line like:
--   - analytic <n>: analytics
--   + _analytics <n>
-- copy of the scowl info for the word analytics to the new lemma of the same word
insert or ignore into scowl_data(level, category, region, tag, group_id, pos)
select sd.level, sd.category, sd.region, sd.tag, main_group_id as group_id, p.new_pos as pos
  from extra_scowl_data e
  join scowl_data sd on e.other_group_id = sd.group_id and e.orig_pos = sd.pos
  join new_group_info f using (main_group_id)
  join fix_pos p on f.base_pos = p.base_pos and e.pos = p.orig_pos;

-- fixup scowl info for new/updated entries
create temp table adj_scowl_data as
  select distinct sd.level,category,region,tag,main_group_id as group_id,new_pos as pos, adj_rank
  from scowl_data as sd
    join to_merge tm on sd.group_id = tm.other_group_id
    join new_group_info g using (main_group_id)
    join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = sd.pos
    left join adj_entry_ranks using (main_group_id, other_group_id, pos);
delete from scowl_data where (group_id) in (select group_id from adj_scowl_data);
insert or ignore into scowl_data(level, category, region, tag, group_id, pos)
  select coalesce(b.level, a.level) as level,
         coalesce(b.category, a.category) as category,
         coalesce(b.region, a.region) as region,
         coalesce(b.tag, a.tag) as tag,
         a.group_id,
         a.pos
    from adj_scowl_data a
    left join (adj_scowl_data b join words w using (group_id, pos))
      on a.group_id = b.group_id and a.pos = b.pos and a.adj_rank = w.entry_rank and b.adj_rank is null;
drop table adj_scowl_data;

-- clear out any requested scowl info
delete from scowl_data
  where (group_id, level, category, region, tag) in
    (select other_group_id, level, category, region, tag
       from scowl_info_to_clear
       join to_merge using (main_group_id));

-- add/update any explicitly provided scowl data
delete from scowl_data
  where (group_id, pos, level) in
    (select other_group_id, sd.pos, sd.level
       from (select main_group_id, pos, min(level) as level from new_scowl_data where replace group by main_group_id, pos)  nsd
       join to_merge using (main_group_id)
       join scowl_data sd on sd.group_id = other_group_id and (nsd.pos = '*' or sd.pos = nsd.pos) and sd.level < nsd.level);
insert or ignore into scowl_data(level,category,region,tag,group_id,pos)
  select nsd.level,category,region,tag,main_group_id,coalesce(new_pos, nsd.pos)
    from new_scowl_data nsd
    cross join new_group_info g using (main_group_id)
    cross join fix_pos p on g.base_pos = p.base_pos and nsd.pos = orig_pos
  where nsd.pos != '*';
insert or ignore into scowl_data(level,category,region,tag,group_id,pos)
  select level,category,region,tag,main_group_id,w.pos
    from new_scowl_data nsd
    cross join words w on nsd.main_group_id = w.group_id
    -- note: words has already been updated with the corrected pos, so no need to join with fix_pos
  where nsd.pos = '*';

--add any explicitly provided scowl overrides
-- fixme?: we might need to be a little more precise.... lemma....
insert or ignore into scowl_override(level,category,region,tag,word_id)
  select level,category,region,tag,word_id
    from new_scowl_override o
    cross join words w on o.main_group_id = w.group_id and o.word = w.word;

-- if a new word form is added give it the same scowl info as the lemma
insert into scowl_data
select b.level, b.category, b.region, b.tag, group_id, w.pos
  from (select distinct main_group_id as group_id, pos from to_merge join words on main_group_id = group_id) as w
  left join scowl_data as a using (group_id, pos)
  left join scowl_data as b using (group_id)
  where a.level is null
    and b.pos in (select lemma_pos from base_poses);

-- cleanup
delete from scowl_data as sd
  where group_id in (select * from group_ids_to_clean_up)
  and not exists (select * from words where group_id = sd.group_id and pos = sd.pos);
delete from scowl_data
  where (level,category,region,tag,group_id,pos)
        in (select * from scowl_data_cleanup join group_ids_to_clean_up using (group_id));

--
-- fix up comments
--

delete from lemma_comments where lemma_id in (select lemma_id from new_lemma_comments);
insert into lemma_comments select * from new_lemma_comments where comment is not null;

delete from group_comments where group_id in (select group_id from new_group_comments);
insert into group_comments select * from new_group_comments where comment is not null;

delete from cluster_comments where headword in (select headword from new_cluster_comments);

--
-- cleanup
--

delete from groups as g
  where group_id in (select * from group_ids_to_clean_up)
    and not exists (select * from words where group_id = g.group_id);
drop table group_ids_to_clean_up;

drop table adj_entry_ranks;
drop table extra_scowl_data;
