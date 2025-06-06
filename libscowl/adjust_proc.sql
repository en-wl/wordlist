-- Requires Sqlite 3.33.0

begin;

analyze;

--
-- preliminaries and helper tables
--

-- filter table to optimize certain queries
create temp table group_ids_to_clean_up as
select group_id from to_remove join words using (word_id)
union
select main_group_id from new_lemma_variant_info;

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

--
-- fix up words and lemma_variant_info
--

delete from words where word_id in (select * from to_remove);

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

-- add/update any explicitly provided scowl info
delete from scowl_data
  where group_id in (select other_group_id from new_scowl_data
                       join to_merge using (main_group_id)
                      where pos is null);
insert into scowl_data(level,category,region,tag,group_id,pos)
  select distinct sd.level,category,region,tag,main_group_id,coalesce(new_pos, w.pos)
  from new_scowl_data sd
    join words w on sd.main_group_id = w.group_id
    join new_group_info g using (main_group_id)
    left join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = w.pos
  where sd.pos is null;

-- fixup scowl info when the rank has changed to be consistent with other
-- entries with the same rank and pos within group
create temp table adj_scowl_data as
select distinct level,category,region,tag,orig_group_id as group_id, sd.pos
  from (scowl_data join words using (group_id, pos)) as sd
  join (new_entry_info as n join words as w using (word_id)) on sd.group_id = main_group_id and sd.pos = w.pos and sd.entry_rank = n.entry_rank;
delete from scowl_data where (group_id, pos) in (select group_id, pos from adj_scowl_data);
insert into scowl_data select * from adj_scowl_data;
drop table adj_scowl_data;

-- fixup scowl info for new/updated entries
create temp table adj_scowl_data as
  select distinct sd.level,category,region,tag,main_group_id as group_id,coalesce(fix_pos.new_pos,sd.pos) as pos
  from scowl_data as sd
    join to_merge tm on sd.group_id = tm.other_group_id
    join new_group_info g using (main_group_id)
    left join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = sd.pos
  where main_group_id not in (select main_group_id from new_scowl_data);
delete from scowl_data where (group_id) in (select group_id from adj_scowl_data);
insert into scowl_data select * from adj_scowl_data;
drop table adj_scowl_data;

-- if a new word form is added give it the same scowl info as the lemma
insert into scowl_data
select b.level, b.category, b.region, b.tag, group_id, w.pos
  from (select distinct main_group_id as group_id, pos from new_words) as w
  left join scowl_data as a using (group_id, pos)
  left join scowl_data as b using (group_id)
  where a.level is null
    and b.pos in (select lemma_pos from base_poses);

-- cleanup
delete from scowl_data
  where (level,category,region,tag,group_id,pos)
        in (select * from scowl_data_cleanup where group_id in (select main_group_id from to_merge));
delete from scowl_data
  where (group_id, pos) in (
    select group_id, pos
      from scowl_data
      join group_ids_to_clean_up using (group_id)
      where (group_id, pos) not in (select group_id, pos from words));

--
-- fix up lemma and group comments
--

delete from lemma_comments where lemma_id in (select lemma_id from new_lemma_comments);
insert into lemma_comments select * from new_lemma_comments where comment is not null;

delete from group_comments where group_id in (select group_id from new_group_comments);
insert into group_comments select * from new_group_comments where comment is not null;

--
-- cleanup
--

delete from groups where group_id not in (select group_id from words);

drop table group_ids_to_clean_up;
