begin;

insert into overlapping_pos values
  ('n', 'n_v'), ('n', 'm'), ('v', 'n_v'), ('v', 'm'), ('n_v', 'm'),
  ('aj', 'a'), ('aj', 'aj_av'), ('av', 'a'), ('av', 'aj_av'), ('aj_av', 'a');
insert into overlapping_pos select other_pos, base_pos from overlapping_pos;

commit;
