--
-- combine n/v into n_v and aj/av into aj_av
--
-- foreign keys are exepcted to be enabled, otherwise there may be some orphan
-- records
-- 

begin;

create temp view _scowl as
select group_id, lemma_id, word_id, base_pos, 
       level as sk1, category as sk2, region as sk3, tag as sk4, -- sk = scowl key
       coalesce(spelling,'') as vk1, coalesce(lemma_variant_level,-1) as vk2, coalesce(derived_variant_level,-1) as vk3, -- vk = variant key
       lemma, w.word, pos, lemma_rank as wk1, pos_class as wk2, defn_note as wk3, usage_note as wk4, coalesce(entry_rank,'') as wk5, -- wk = word key
       coalesce(gc.word,'') as ck1, coalesce(gc.comment, '') as ck2, coalesce(lc.comment, '') as ck3, -- ck = comment key
       false as override
 from (scowl_data
       join entries using (group_id, pos)) as w
 left join variant_info as v using (word_id)
 left join group_comments as gc using (group_id)
 left join lemma_comments as lc using (lemma_id)
union all
select group_id, lemma_id, word_id, base_pos,
       level as sk1, category as sk2, region as sk3, tag as sk4, -- sk = scowl key
       '', -1, -1, -- vk
       lemma, w.word, pos, lemma_rank as wk1, pos_class as wk2, defn_note as wk3, usage_note as wk4, coalesce(entry_rank,'') as wk5, -- wk = word key
       '','','', -- ck
       true as override
 from (scowl_override
       join entries using (word_id)) as w
;

create temp table _match as
select a.group_id as a_group_id, b.group_id as b_group_id,
       a.lemma_id as a_lemma_id, b.lemma_id as b_lemma_id,
       a.word_id as a_word_id, b.word_id as b_word_id,
       a.pos as a_pos, b.pos as b_pos,
       word, lemma, override,
       sk1, sk2, sk3, sk4, vk1, vk2, vk3
  from _scowl a join _scowl b using (sk1, sk2, sk3, sk4, lemma, word, wk1, wk3, wk4, wk4, wk5, vk1, vk2, vk3, ck1, ck2, ck3, override)
  where (a.pos = 'aj0' and b.pos = 'av0')
     or (a.pos = 'aj1' and b.pos = 'av1')
     or (a.pos = 'aj2' and b.pos = 'av2')
     or (a.pos = 'n0'  and b.pos = 'v0')
     or (a.pos = 'ns'  and b.pos = 'vs')
;
create index _match_a_group_id on _match(a_group_id);
create index _match_b_group_id on _match(b_group_id);
create index _match_b_lemma_id on _match(b_lemma_id);
create index _match_b_word_id on _match(b_word_id);

delete from _match
 where a_group_id in (
   select group_id from _scowl
    where group_id in (select a_group_id from _match)
     and (group_id, sk1, sk2, sk3, sk4, vk1, vk2, vk3, word_id, override) not in (select a_group_id, sk1, sk2, sk3, sk4, vk1, vk2, vk3, a_word_id, override from _match)
     and pos in ('aj0', 'aj1', 'aj2', 'n0', 'ns')
   )
;

delete from _match
 where b_group_id in (
   select group_id from _scowl
    where group_id in (select b_group_id from _match)
     and (group_id, sk1, sk2, sk3, sk4, vk1, vk2, vk3, word_id, override) not in (select b_group_id, sk1, sk2, sk3, sk4, vk1, vk2, vk3, b_word_id, override from _match)
     and pos in ('av0', 'av1', 'av2', 'v0', 'vs')
   )
;

delete from _match
  where b_group_id in (
    select group_id from _scowl where base_pos = 'v' and pos not in ('v0', 'vd', 'vn', 'vg', 'vs')
  )
;

delete from scowl_data
  where (group_id, pos) in (select b_group_id, b_pos from _match where not override);

delete from scowl_override
  where word_id in (select b_word_id from _match where override);

update or ignore words
  set group_id = (select a_group_id from _match where b_group_id = group_id),
      lemma_id = (select a_lemma_id from _match where b_lemma_id = lemma_id);

delete from words
  where (word_id) in (select b_word_id from _match);

update words
  set pos = case when pos = 'aj0' then 'a0'
                 when pos = 'aj1' then 'a1'
                 when pos = 'aj2' then 'a2'
                 when pos = 'n0' then 'm0'
                 when pos = 'ns' then 'ms'
                 else pos end
  where group_id in (select a_group_id from _match);

update scowl_data 
  set pos = case when pos = 'aj0' then 'a0'
                 when pos = 'aj1' then 'a1'
                 when pos = 'aj2' then 'a2'
                 when pos = 'n0' then 'm0'
                 when pos = 'ns' then 'ms'
                 else pos end
  where group_id in (select a_group_id from _match);

update or ignore scowl_data as w
  set group_id = (select a_group_id from _match where b_group_id = group_id);

delete from groups
  where group_id not in (select group_id from words);

update groups
   set base_pos = 'aj_av'
 where group_id in (select a_group_id from _match where a_pos = 'aj0');

update groups
   set base_pos = 'n_v'
 where group_id in (select a_group_id from _match where a_pos = 'n0');

insert into _combined
select distinct a_group_id, b_group_id from _match;

delete from variant_info_mview;
insert into variant_info_mview select * from variant_info;

commit;
