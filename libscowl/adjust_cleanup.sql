begin;

drop table if exists new_duplicate_lemmas;
drop table if exists group_ids_to_clean_up;
drop table if exists new_cluster_comments;
drop table if exists new_group_comments;
drop table if exists new_scowl_data;
drop table if exists scowl_info_to_clear;
drop table if exists new_scowl_override;
drop table if exists new_entry_info;
drop table if exists new_group_info;
drop table if exists new_derived_variant_info;
drop table if exists new_derived_variant_info;
drop table if exists new_lemma_variant_info;
drop table if exists new_lemma_comments;
drop table if exists new_words;
drop table if exists explicit;
drop table if exists to_remove;
drop view if exists to_merge;
drop table if exists use_info_from;

commit;
