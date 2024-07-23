begin;

create view lemmas as
select word_id as lemma_id, group_id, word as lemma, pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, lemma_rank
  from words left join groups g using (group_id) where word_id = lemma_id;
select * from lemmas limit 0;

create view entries as
select a.word_id, a.group_id, a.lemma_id, b.word as lemma, b.pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, lemma_rank, a.word, a.pos, a.entry_rank
  from words a left join words b on (a.lemma_id = b.word_id) left join groups g on a.group_id = g.group_id;
select * from entries limit 0;

create view duplicate_derived as
select word
 from (select (select max(cluster_id) from clusters where cluster_id <= group_id) as cluster_id, word
         from words
         join (select word_id as lemma_id, word as lemma from words) as lemmas using (lemma_id)
        where word_id != lemma_id) as q
 group by word
 having count (distinct cluster_id) > 1
;

create view variant_info as
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
select * from variant_info limit 0;

create view duplicate_lemma_check as
select lemma, base_pos, pos_class, defn_note, usage_note from lemmas group by lemma, base_pos, pos_class, defn_note, usage_note having count(distinct group_id) > 1;
select * from duplicate_lemma_check limit 0;

commit;
