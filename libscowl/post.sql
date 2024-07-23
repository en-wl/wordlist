begin;

delete from pos_classes;
insert into pos_classes select distinct pos_class from groups order by pos_class;

delete from usage_notes;
insert into usage_notes select distinct usage_note from groups order by usage_note;

delete from categories;
insert into categories select distinct category from _scowl_combined order by category;

delete from tags;
insert into tags select distinct tag from _scowl_combined order by category;

delete from variant_info_mview;
insert into variant_info_mview select * from variant_info;
    
analyze;
commit;
