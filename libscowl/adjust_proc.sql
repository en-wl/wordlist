-- Requires Sqlite 3.33.0

begin;

create temp table group_ids_to_clean_up as
select distinct group_id from to_remove join words using (word_id);

delete from words where word_id in (select * from to_remove);
insert into words select * from new_words;
insert into derived_variant_info select * from new_derived_variant_info;

delete from groups
  where group_id in (
    select group_id from group_ids_to_clean_up
    where group_id not in (select group_id from words));

delete from scowl_data
  where (group_id, pos) in (
    select group_id, pos
      from scowl_data
      join group_ids_to_clean_up using (group_id)
      where (group_id, pos) not in (select group_id, pos from words));

create table temp.split_info as
      select row_number() over (order by main_group_id,lemma_pos,word) + (select max(word_id) from words) as new_word_lemma_id, 
      w.lemma_id as lemma_id, main_group_id, lemma_pos as new_pos, word, other_group_id, w.pos 
from to_merge join words as w on other_group_id = w.group_id join groups on main_group_id = groups.group_id join base_poses using (base_pos)
where pos = '?' and lemma_pos != '?';

insert into new_scowl_data(level,category,region,tag,main_group_id,pos)
  select distinct sd.level,category,region,tag,main_group_id,coalesce(new_pos, w.pos)
  from new_scowl_data sd
    join new_lemma_variant_info vi using (main_group_id) -- fixme: maybe find better way to get lemma_id
    join words w using (lemma_id)
    join new_group_info g using (main_group_id)
    left join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = w.pos
  where sd.pos is null;
delete from new_scowl_data where pos is null;

insert or ignore into new_scowl_data(level,category,region,tag,main_group_id,pos)
  select min(sd.level) as level,category,region,tag,main_group_id, coalesce(si.new_pos,fix_pos.new_pos,sd.pos) as pos
  from scowl_data as sd
    join to_merge tm on sd.group_id = tm.other_group_id
    left join split_info si using (main_group_id, other_group_id, pos)
    join new_group_info g using (main_group_id)
    left join fix_pos on fix_pos.base_pos = g.base_pos and orig_pos = sd.pos
  where main_group_id not in (select main_group_id from new_scowl_data)
  group by category,region,tag,main_group_id,coalesce(si.new_pos,sd.pos);

analyze new_scowl_data;
delete from scowl_data where group_id in (select other_group_id from to_merge);
insert into scowl_data select * from new_scowl_data;
delete from scowl_data
  where (level,category,region,tag,group_id,pos)
        in (select * from scowl_data_cleanup where group_id in (select main_group_id from new_scowl_data));

update words set group_id = main_group_id 
from to_merge 
where words.group_id = to_merge.other_group_id and to_merge.other_group_id != to_merge.main_group_id;

delete from words where lemma_id in (select lemma_id from split_info);
insert into words select new_word_lemma_id, main_group_id, new_word_lemma_id, new_pos, word, '' from split_info;

delete from groups where group_id not in (select group_id from words);

delete from lemma_variant_info where lemma_id in (select lemma_id from new_lemma_variant_info);
insert into lemma_variant_info
  select coalesce(new_word_lemma_id,lemma_id) as lemma_id, spelling, variant_level from new_lemma_variant_info left join split_info using (main_group_id,lemma_id);

insert into group_ids_to_clean_up select distinct main_group_id from new_lemma_variant_info;

delete from lemma_variant_info
where lemma_id in (select lemma_id from useless_lemma_variant_entries join group_ids_to_clean_up using (group_id));

drop table group_ids_to_clean_up;

update groups as a
   set base_pos = b.base_pos,
       defn_note = coalesce(b.defn_note, a.defn_note),
       pos_class = coalesce(b.pos_class, a.pos_class),
       usage_note = coalesce(b.usage_note, a.usage_note),
       lemma_rank = coalesce(b.lemma_rank, a.lemma_rank)
 from new_group_info as b
 where a.group_id = b.main_group_id;

update words as a
   set pos = new_pos
  from new_group_info g, fix_pos as b
  where a.group_id = main_group_id and g.base_pos = b.base_pos and a.pos = b.orig_pos
    and a.pos != new_pos;

delete from lemma_comments where lemma_id in (select lemma_id from new_lemma_comments);
insert into lemma_comments select * from new_lemma_comments where comment is not null;

delete from group_comments where group_id in (select group_id from new_group_comments);
insert into group_comments select * from new_group_comments where comment is not null;
