create table temp.split_info as
      select row_number() over (order by main_group_id,lemma_pos,word) + (select max(word_id) from words) as new_word_lemma_id, 
      w.lemma_id as lemma_id, main_group_id, lemma_pos as new_pos, word, other_group_id, w.pos 
from to_merge join words as w on other_group_id = w.group_id join groups on main_group_id = groups.group_id join base_poses using (base_pos)
where pos = '?' and lemma_pos != '?';

insert into new_scowl_data(level,category,region,tag,main_group_id,pos)
select distinct level,category,region,tag,main_group_id,w.pos
from new_scowl_data sd join new_lemma_variant_info vi using (main_group_id) join words w using (lemma_id)
where sd.pos is null;
delete from new_scowl_data where pos is null;

insert into new_scowl_data(level,category,region,tag,main_group_id,pos)
  select min(level) as level,category,region,tag,main_group_id, coalesce(si.new_pos,sd.pos) as pos
    from scowl_data as sd
    join to_merge tm on sd.group_id = tm.other_group_id
    left join split_info si using (main_group_id, other_group_id, pos)
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

delete from group_comments where group_id in (select other_group_id from to_merge);
insert into group_comments select * from new_group_comments;
