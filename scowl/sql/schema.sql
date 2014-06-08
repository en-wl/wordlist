create table words (
  word text,
  lid  int
);

create table lists (
  lid int,
  spelling text,
  US int, GBs int, GBz int, CA int, SP int,
  variant int default -1,
  category text,
  size int,
  primary key (lid),
  unique (spelling, category, size)
);

.separator \t
.import working/lists.tab lists
.import working/words.tab words





