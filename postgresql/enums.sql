create type pos as enum ('?','n0','ns','nss','np','nsp','nssp','v0','vd','vds','vn','vg','vs','vs2','vs3','vss','m0','ms','aj0','aj1','aj2','av0','av1','av2','a0','a1','a2','pn0','pn1','pns','pnd','pnp','pnr0','pnrs','c','pp','d','ds','d1','d2','i','abbr','s','pre','suf','wp','we','wes','wep','weps','x');
create type base_pos as enum ('','n','pl','v','n_v','m','aj','av','aj_av','a','pn','c','pp','d','i','abbr','s','pre','suf','wp','we','x');
create type rank_symbol as enum ('','*','-','@','~','!');
create type variant_symbol as enum ('','.','=','?','v','~','V','-','@','x');
create type region as enum ('','US','GB','CA','AU');
create type spelling as enum ('_','A','B','Z','C','D');
