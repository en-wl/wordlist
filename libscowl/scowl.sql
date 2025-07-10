begin;

create view _scowl_combined as
select size, category, region, tag, group_id, pos, null as word_id
from scowl_data
union all
select size, category, region, tag, null, null, word_id
from scowl_override;
select * from _scowl_combined limit 0;

create view _scowl_main as
select group_id, lemma_id, word_id,
       size, category, region, tag, pos, base_pos, pos_category, pos_class, usage_note,
       spelling, variant_level as variant_level, legacy_level,
       lemma_variant_level, derived_variant_level,
       word,
       group_rank, entry_rank
  from scowl_data
  join words_w_variant_info using (group_id, pos)
  left join variant_levels using (variant_level)
  left join groups using (group_id)
  left join base_poses using (base_pos)
;
create view _scowl_override as
select group_id, lemma_id, word_id,
       size, category, region, tag, pos, base_pos, pos_category, pos_class, usage_note,
       spelling, 0 as variant_level, 0 as legacy_level,
       cast(null as smallint) as lemma_variant_level, cast(null as smallint) as derived_variant_level,
       word,
       group_rank, entry_rank
  from scowl_override
  join words using (word_id)
  join (select spelling from spellings) as s on spelling = '_'
  left join groups using (group_id)
  left join base_poses using (base_pos)
;

create view scowl_ as
select *, false as override from _scowl_main
union all
select *, true as override from _scowl_override;
select * from scowl_ limit 0;

create view scowl_v0 as
  select size, category, region, tag, pos, base_pos, pos_category, pos_class, usage_note, override, spelling, variant_level, legacy_level, word
  from scowl_;
select * from scowl_v0 limit 0;

create view duplicate_derived_view as
with duplicate_derived as (
  select word
   from (select cluster_id, word
           from words
           join cluster_map using (group_id)
           join (select word_id as lemma_id, word as lemma from words) as lemmas using (lemma_id)
          where word_id != lemma_id) as q
   group by word
   having count (distinct cluster_id) > 1
), s as (
  select cluster_id, group_id, word, size, variant_level
    from scowl_ join cluster_map using (group_id)
    where word_id != lemma_id and word in (select * from duplicate_derived))
select distinct b.group_id, word
  from s a join s b using (word)
  where a.cluster_id != b.cluster_id and (a.size < b.size or (a.size = b.size and a.variant_level <= b.variant_level));
select * from duplicate_derived_view limit 0;

commit;
