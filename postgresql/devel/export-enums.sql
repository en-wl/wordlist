-- this is a sqlite3 script
-- version 3.44.0 or better is required

select concat('create type pos as enum (',
              string_agg(concat('''', pos, ''''), ',' order by order_num),
              ');')
  from poses;

select concat('create type base_pos as enum (',
              string_agg(concat('''', base_pos, ''''), ',' order by order_num),
              ');')
  from base_poses;

select concat('create type rank_symbol as enum (',
              string_agg(concat('''', rank_symbol, ''''), ',' order by order_num),
              ');')
  from ranks;

select concat('create type variant_symbol as enum (',
              string_agg(concat('''', variant_symbol, ''''), ',' order by variant_level),
              ');')
  from variant_levels;

select concat('create type region as enum (',
              string_agg(concat('''', region, ''''), ',' order by order_num),
              ');')
  from regions;

select concat('create type spelling as enum (',
              string_agg(concat('''', spelling, ''''), ',' order by order_num),
              ');')
  from spellings;


