
create index speller_words_word on speller_words (word);
create index speller_words_word_lower on speller_words (word_lower);

insert into speller_cross select (select did from dict_info where dict='en_US'),
                           pid from info join post using (iid) where size <= 60 and (US or SP) and variant <= 0 and not accented;
insert into speller_cross select (select did from dict_info where dict='en_GB-ise'),
                           pid from info join post using (iid) where size <= 60 and (GBs or SP) and variant <= 0 and not accented;
insert into speller_cross select (select did from dict_info where dict='en_GB-ize'),
                           pid from info join post using (iid) where size <= 60 and (GBz or SP) and variant <= 0 and not accented;
insert into speller_cross select (select did from dict_info where dict='en_CA'),
                           pid from info join post using (iid) where size <= 60 and (CA or SP) and variant <= 0 and not accented;
insert into speller_cross select (select did from dict_info where dict='en_AU'),
                           pid from info join post using (iid) where size <= 60 and (AU or SP) and variant <= 0 and not accented;

insert into speller_cross select (select did from dict_info where dict='en_US-large'),
                    pid from info join post using (iid) where size <= 70 and (US or SP) and variant <= 1;
insert into speller_cross select (select did from dict_info where dict='en_GB-large'),
                    pid from info join post using (iid) where size <= 70 and (GBs or GBz or SP) and variant <= 1;
insert into speller_cross select (select did from dict_info where dict='en_CA-large'),
                    pid from info join post using (iid) where size <= 70 and (CA or SP) and variant <= 1;
insert into speller_cross select (select did from dict_info where dict='en_AU-large'),
                    pid from info join post using (iid) where size <= 70 and (AU or SP) and variant <= 1;


