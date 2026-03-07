begin;

create view lemmas as
select word_id as lemma_id, group_id, word as lemma, pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, group_rank
  from words left join groups g using (group_id) where word_id = lemma_id;
select * from lemmas limit 0;

create view entries as
select a.word_id, a.group_id, a.lemma_id, b.word as lemma, b.pos as lemma_pos, base_pos, pos_class, defn_note, usage_note, group_rank, a.word, a.pos, a.entry_rank
  from words a left join words b on (a.lemma_id = b.word_id) left join groups g on a.group_id = g.group_id;
select * from entries limit 0;

create view words_w_variant_info as
select a.group_id, a.pos,
       a.lemma_id, a.word_id, a.word, a.entry_rank,
       coalesce(nullif(lv.spelling,'_'), nullif(dv.spelling,'_'), '_') as spelling,
       case when lv.variant_level >= coalesce(dv.variant_level,0) then lv.variant_level else coalesce(dv.variant_level,0) end as variant_level,
       lv.variant_level as lemma_variant_level,
       dv.variant_level as derived_variant_level
  from words a
  left join lemma_variant_info lv using (lemma_id)
  left join derived_variant_info dv using (word_id)     
  where dv.variant_level is null
     or coalesce(lv.spelling, '_') = dv.spelling
     or coalesce(lv.spelling, '_') = '_'
     or dv.spelling = '_';
select * from words_w_variant_info limit 0;

create view duplicate_lemma_check as
select lemma, base_pos, pos_class, defn_note, usage_note from lemmas group by lemma, base_pos, pos_class, defn_note, usage_note having count(distinct group_id) > 1;
select * from duplicate_lemma_check limit 0;

create view scowl_data_cleanup as
select b.*
  from scowl_data as a join scowl_data b using (group_id, pos)
  where (
         (a.size < b.size and a.category = b.category and a.region = b.region and a.tag = b.tag)
         or (a.size <= b.size and a.category = '' and b.category = 'hacker' and a.region = b.region)
         or (a.size <= b.size and a.category = b.category and a.region in ('', b.region) and a.tag = '' and b.tag not in ('', '[cs]', '[-]') and b.size <= 35)
         or (a.size <= b.size and a.category = b.category and a.region in ('', b.region) and a.tag = '' and b.tag not in ('', '[cs]', '[+]', '[-]'))
         --or (a.size < b.size and b.size >= 80 and a.category = b.category and a.region = b.region and a.tag not in ('[cs]', '[name]', '[town]'))
        );
select * from scowl_data_cleanup limit 0;

create view lemma_variant_info_w_group_id as
  select group_id, v.*
  from lemma_variant_info v join words w on v.lemma_id = w.word_id
;

create view useless_lemma_variant_entries as
  select group_id, lemma_id
  from lemma_variant_info_w_group_id a
  where not exists (select * from lemma_variant_info_w_group_id b
                     where a.group_id = b.group_id  and (spelling != '_' or variant_level != 0));
select * from useless_lemma_variant_entries limit 0;

commit;
