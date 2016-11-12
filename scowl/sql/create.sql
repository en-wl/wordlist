--
-- Tables directly corresponding to SCOWL lists
--

create table words_l (
  word text,
  lid  int
);

create table lists (
  lid int,
  spelling text,
  US int, GBs int, GBz int, CA int, AU int, SP int,
  variant int default -1,
  category text,
  size int,
  primary key (lid),
  unique (spelling, category, size)
);

.separator \t
.import working/lists.tab lists
.import working/words.tab words_l

create index word_l_word on words_l(word);

--
-- 
--

.read 'sql/schema.sql'

create temp table step1 as
  select word,US,GBs,GBz,CA,AU,SP,min(variant) variant,category,size
    from words_l join lists using (lid)
  group by word,US,GBs,GBz,CA,SP,category;

create temp table step2 as
  select word,max(US) US, max(GBs) GBs, max(GBz) GBz, max(CA) CA, max(AU) AU, max(SP) SP, variant,category,size
    from step1
  group by word,variant,category,size;

create temp table step3 as
  select word,
    case when US then 'A' else '' end
    || case when GBs then 'B' else '' end || case when GBz then 'Z' else '' end
    || case when CA then 'C' else '' end || case when AU then 'D' else '' end
    || case when SP then 'S' else '' end || case when variant = -1 then '' else variant end as spid,
    US, GBs, GBz, CA, AU, SP, variant, category, size
  from step2;

insert into info
  select null, spid,US,GBs,GBz,CA,AU,SP,variant,category,size
    from step3
   group by spid,US,GBs,GBz,CA,AU,SP,variant,category,size
   order by size, variant, US,GBs,GBz,CA,AU,SP, category;

insert into words
  select word, iid
    from step3 join info using (spid,category,size);

create index word_word on words(word);

