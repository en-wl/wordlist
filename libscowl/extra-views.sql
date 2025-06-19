-- unused views that might be useful at some point

create view scowl_info as
  select level,category,region,tag,group_id,pos,null as word_id
    from scowl_data
union all
  select level,category,region,tag,group_id,null as pos,word_id
    from scowl_override join words using(word_id);
select * from scowl_info limit 0;

create view scowl_expanded as
  select level,category,region,tag,words.*
    from scowl_data join words using (group_id, pos)
union all
  select level,category,region,tag,words.*
    from scowl_override join words using(word_id);
select * from scowl_expanded limit 0;

