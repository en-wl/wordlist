.read 'sql/schema-speller.sql'

insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_US',       1, 1,0,0,0,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_GB-ise',   1, 0,1,0,0,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_GB-ize',   1, 0,0,1,0,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_CA',       1, 0,0,0,1,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_AU',       1, 0,0,0,0,1,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_US-large', 2, 1,0,0,0,0, 0,70);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_GB-large', 2, 0,1,1,0,0, 0,70);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_CA-large', 2, 0,0,0,1,0, 0,70);
insert into dict_info (dict,onum,US,GBs,GBz,CA,AU,max_variant,max_size) values ('en_AU-large', 2, 0,0,0,0,1, 0,70);

--drop view if exists lookup;
create view lookup as 
  select word, word_lower, iid, spid, coalesce(d.US and i.US,i.US) US, coalesce(d.GBs and i.GBs,i.GBs) GBs,
    coalesce(d.GBz and i.GBz, i.GBz) GBz, coalesce(d.CA and i.CA,i.CA) CA, coalesce(d.CA and i.CA,i.CA) CA, coalesce(d.AU and i.AU,i.AU) AU,
    SP, variant, category, size, speller_words.pid, added, accented, coalesce(onum,9) onum, dict
    from speller_words join (info join post using (iid)) as i using (pid) left join (speller_cross join dict_info using (did)) as d using (pid)
order by word,onum,added,SP,size,variant;

