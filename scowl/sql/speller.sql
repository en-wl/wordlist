--
-- Tables recording what words are in the speller dictionaries
--
--drop table if exists speller_words;
--drop table if exists post;
--drop table if exists speller;
--drop table if exists dict_info;

create table speller_words (
  word text,
  pid integer -- source list if any
);

create table post (
  pid integer primary key autoincrement,
  iid integer, -- source list if any
  added int, -- if the word was added via a post processing step
  accented int default 0, -- 
  unique(iid,added,accented)
);

create table speller (
  did int,
  pid int,
  unique(did,pid)
);

create table dict_info (
  did integer primary key autoincrement,
  dict text,
  onum int,
  US int, GBs int, GBz int, CA int,
  max_variant int, max_size int
);

insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_US',       1, 1,0,0,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_GB-ise',   1, 0,1,0,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_GB-ize',   1, 0,0,1,0,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_CA',       1, 0,0,0,1,-1,60);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_US-large', 2, 1,0,0,0, 0,70);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_GB-large', 2, 0,1,1,0, 0,70);
insert into dict_info (dict,onum,US,GBs,GBz,CA,max_variant,max_size) values ('en_CA-large', 2, 0,0,0,1, 0,70);

--drop view if exists lookup;
create view lookup as 
  select word, iid, spid, coalesce(d.US and i.US,i.US) US, coalesce(d.GBs and i.GBs,i.GBs) GBs, coalesce(d.GBz and i.GBz, i.GBz) GBz, coalesce(d.CA and i.CA,i.CA) CA, SP, variant, category, size, speller_words.pid, added, accented, coalesce(onum,9) onum, dict
    from speller_words join (info join post using (iid)) as i using (pid) left join (speller join dict_info using (did)) as d using (pid)
order by word,onum,added,SP,size,variant;

