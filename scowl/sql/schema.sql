--
-- Tables corresponding to entries in SCOWL where entries are combined
-- when possible.
--

create table words (
  word text not null,
  iid  int not null
);

create table info (
  iid integer primary key,
  spid varchar(6) not null,
  US boolean not null, GBs boolean not null, GBz boolean not null, CA boolean not null, AU boolean not null, SP boolean not null,
  variant int default -1 not null,
  category varchar(14) not null,
  size int not null,
  unique (spid, category, size)
);

create view scowl as select * from words join info using (iid);
