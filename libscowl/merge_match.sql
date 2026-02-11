begin;

analyze new_lemmas;

drop table if exists temp.matched;
create table temp.matched (
  idx integer not null,
  group_id integer not null,
  keep boolean not null default true,
  primary key (idx, group_id)
) without rowid;

insert into temp.matched (idx, group_id)
select distinct idx, group_id
  from (new_groups join new_lemmas using (idx)) as a join lemmas b using (lemma, base_pos)
  where coalesce(a.defn_note, '') = b.defn_note;

analyze temp.matched;

with
  multi as (select idx from matched join new_groups using (idx) where defn_note is null group by idx having count(*) > 1),
  candidates as (select idx, group_id,
                        group_rank != '' as exclude
                   from multi join matched using (idx) join groups using (group_id)),
  exclude as (select idx,group_id
                from candidates
               where exclude
                 and idx in (select idx from candidates group by idx having count(*) filter (where not exclude) > 0))
update matched set keep = false
  where (idx, group_id) in (select * from exclude);

with
  multi as (select idx from matched group by idx having count(*) > 1),
  candidates as (select idx, group_id, coalesce(n.pos_class, '') != g.pos_class as exclude
                   from multi join new_groups as n using (idx) join matched using (idx) join groups as g using (group_id)),
  exclude as (select idx,group_id
                from candidates
               where exclude
                 and idx in (select idx from candidates group by idx having count(*) filter (where not exclude) > 0))
update matched set keep = false
  where (idx, group_id) in (select * from exclude);

drop table if exists temp.conflicts;
create table temp.conflicts (
  idx integer primary key,
  pos_class boolean not null,
  usage_note boolean not null,
  group_rank boolean not null
);

insert into temp.conflicts
with potential as (
  select idx,
         count(distinct pos_class) > 1 as pos_class,
         count(distinct usage_note) > 1 as usage_note,
         count(distinct group_rank) > 1 as group_rank
    from matched join groups using (group_id)
    where keep
    group by idx)
select * from potential where pos_class or usage_note or group_rank;

drop view if exists temp.pos_conflicts;
create view temp.pos_conflicts as
select idx, a.lemma, a.base_pos, other_pos
  from (new_groups join new_lemmas using (idx) join overlapping_pos using (base_pos)) as a
  join lemmas b on a.lemma = b.lemma and other_pos = b.base_pos;

commit;

