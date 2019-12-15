--
-- Tables recording what words are in the speller dictionaries
--

create table speller_words (
  word text not null,
  word_lower text not null,
  pid integer not null -- source list
);

create table post (
  pid integer primary key,
  iid integer, -- source list if any
  added boolean not null, -- if the word was added via a post processing step
  accented boolean default false not null, -- 
  unique(iid,added,accented)
);

create table speller_cross (
  did int not null,
  pid int not null,
  unique(did,pid)
);

create table dict_info (
  did integer primary key,
  dict text not null,
  onum int not null,
  US boolean not null, GBs boolean not null, GBz boolean not null, CA boolean not null, AU boolean not null,
  max_variant int not null, max_size int not null
);

create view speller as select * from speller_words join post using (pid) left join (speller_cross join dict_info using (did)) using (pid);
