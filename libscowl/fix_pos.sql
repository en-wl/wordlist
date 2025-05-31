begin;

create temp table fix_pos_pre (
  base_pos, orig_pos, new_pos, level,
  primary key (base_pos, orig_pos, new_pos, level)
) without rowid;

insert into fix_pos_pre select base_pos,pos,pos,0 from poses;
with p(pos) as (values ('vd'), ('vn'), ('vg'))
  insert into fix_pos_pre select 'm', pos, pos, 0 from p;
insert into fix_pos_pre values
  ('v', 'm0', 'v0', 1),
  ('v', 'ms', 'vs', 1),
  ('n', 'm0', 'n0', 1),
  ('n', 'ms', 'ns', 1),
  ('aj', 'a0', 'aj0', 1),
  ('aj', 'a1', 'aj1', 1),
  ('aj', 'a2', 'aj2', 1),
  ('av', 'a0', 'av0', 1),
  ('av', 'a1', 'av1', 1),
  ('av', 'a2', 'av2', 1),
  ('wp', 'n0', 'wp', 2),
  ('we', 'n0', 'we', 2),
  ('we', 'ns', 'wes', 2),
  ('we', 'np', 'wep', 2),
  ('we', 'nsp', 'weps', 2),
  ('d', 'pn0', 'd', 2),
  ('d', 'pns', 'ds', 2),
  ('d', 'aj0', 'd', 2),
  ('d', 'aj1', 'd1', 2),
  ('d', 'aj2', 'd2', 2)
;

insert into fix_pos_pre
select b.base_pos,new_pos as orig_pos,orig_pos as new_pos, 2
  from fix_pos_pre as a join poses as b on a.orig_pos = b.pos where level > 0;

insert or ignore into fix_pos_pre
select distinct a.base_pos, c.new_pos as orig_pos, a.new_pos, 3
  from fix_pos_pre as a join fix_pos_pre as b on a.new_pos = b.orig_pos join fix_pos_pre as c on b.new_pos = c.orig_pos;

insert into fix_pos_pre values
  ('d', 'n0', 'd', 3),
  ('d', 'ns', 'ds', 3)
;

insert or ignore into fix_pos_pre
select b.base_pos,new_pos as orig_pos,orig_pos as new_pos, 3
  from fix_pos_pre as a join poses as b on a.orig_pos = b.pos where level > 0;

insert or ignore into fix_pos_pre
select distinct a.base_pos, c.new_pos as orig_pos, a.new_pos, 4
  from fix_pos_pre as a join fix_pos_pre as b on a.new_pos = b.orig_pos join fix_pos_pre as c on b.new_pos = c.orig_pos;

insert or ignore into fix_pos_pre
select distinct a.base_pos, c.new_pos as orig_pos, a.new_pos, 4
  from fix_pos_pre as a join fix_pos_pre as b on a.new_pos = b.orig_pos join fix_pos_pre as c on b.new_pos = c.orig_pos;

-- this query should be a noop
insert or ignore into fix_pos_pre
select distinct a.base_pos, c.new_pos as orig_pos, a.new_pos, 4
  from fix_pos_pre as a join fix_pos_pre as b on a.new_pos = b.orig_pos join fix_pos_pre as c on b.new_pos = c.orig_pos;

with lemma_poses as (select base_pos,pos,pos_category != '' as special from poses join base_poses using (base_pos) where pos = lemma_pos)
  insert or ignore into fix_pos_pre
    select a.base_pos, b.pos, a.pos,
           case when b.pos = '?' then 1
                when a.special or b.special then 3
                else 4 end
    from lemma_poses a cross join lemma_poses b;
;

delete from fix_pos;
insert into fix_pos select base_pos, orig_pos, new_pos, min(level) from fix_pos_pre group by base_pos, orig_pos, new_pos;

drop table fix_pos_pre;

commit;
