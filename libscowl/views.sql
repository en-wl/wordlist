begin;

create view lemmas as
select word_id as lemma_id, group_id, word as lemma, pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, lemma_rank
  from words left join groups g using (group_id) where word_id = lemma_id;
select * from lemmas limit 0;

create view entries as
select a.word_id, a.group_id, a.lemma_id, b.word as lemma, b.pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, lemma_rank, a.word, a.pos, a.entry_rank
  from words a left join words b on (a.lemma_id = b.word_id) left join groups g on a.group_id = g.group_id;
select * from entries limit 0;

create view cluster_map_view as
select group_id, (select max(cluster_id) from clusters where cluster_id <= group_id) as cluster_id
  from groups
;
select * from cluster_map_view limit 0;

create view variant_info_view as
select word_id,
       spelling,
       case when a.variant_level >= coalesce(b.variant_level,-1) then a.variant_level else b.variant_level end as variant_level,
       a.variant_level as lemma_variant_level,
       b.variant_level as derived_variant_level
 from lemma_variant_info as a
 join words using (lemma_id)
 left join (select word_id, spelling, variant_level from derived_variant_info) as b using (word_id, spelling)
 left join (select distinct lemma_id, pos from derived_variant_info join words using (word_id)) as c using (lemma_id, pos)
 where b.variant_level is not null or c.pos is null
union all 
select word_id,
       spelling,
       variant_level,
       null as lemma_variant_level,
       variant_level as derived_variant_info
  from derived_variant_info d
  join words using (word_id)
  where lemma_id not in (select lemma_id from lemma_variant_info)
;
select * from variant_info_view limit 0;

create view duplicate_lemma_check as
select lemma, base_pos, pos_class, defn_note, usage_note from lemmas group by lemma, base_pos, pos_class, defn_note, usage_note having count(distinct group_id) > 1;
select * from duplicate_lemma_check limit 0;

create view scowl_data_cleanup as
select b.*
  from scowl_data as a join scowl_data b using (group_id, pos)
  where (
         (a.level < b.level and a.category = b.category and a.region = b.region and a.tag = b.tag)
         or (a.level <= b.level and a.category = '' and b.category = 'hacker' and a.region = b.region)
         or (a.level <= b.level and a.category = b.category and a.region = b.region and a.tag = '' and b.tag not in ('', '[cs]', '[-]') and b.level <= 35)
         or (a.level <= b.level and a.category = b.category and a.region = b.region and a.tag = '' and b.tag not in ('', '[cs]', '[+]', '[-]'))
         or (a.level < b.level and b.level >= 80 and a.category = b.category and a.region = b.region and a.tag not in ('[cs]', '[name]', '[town]'))
        );
select * from scowl_data_cleanup limit 0;

create view useless_lemma_variant_entries as
  select group_id, v.lemma_id, v.variant_level
  from lemma_variant_info v
  join words w on v.lemma_id = w.word_id
  join (select group_id from lemma_variant_info v join words w on v.lemma_id = w.word_id
        group by group_id
        having sum(cast(variant_level != 0 as int)) = 0) as group_ids_to_remove using (group_id);
select * from useless_lemma_variant_entries limit 0;

commit;
