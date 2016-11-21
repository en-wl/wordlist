cat <<EOF
name_english English
lang en
data-file en_phonet.dat
data-file en_affix.dat
author:
  name  Kevin Atkinson
  email kevina at gnu org
copyright Copyrighted
mode aspell6
version $SCOWL_VERSION-0
source-version $SCOWL_VERSION
complete true
accurate true
url http://wordlist.aspell.net/
#doc-encoding iso-8859-1
alt-encoding iso-8859-1 iso
readme-extra extra.txt iso-8859-1

alias en_US american
alias en_GB british
alias en_CA canadian
alias en_AU australian
alias en english

dict:
  name en_US-wo_accents
  alias en_US:awli
  add en-common
  add en_US-wo_accents-only
dict:
  name en_US-w_accents
  add en-common
  add en_US-w_accents-only

dict:
  name en_CA-wo_accents
  alias en_CA:awli
  add en-common
  add en_CA-wo_accents-only
dict:
  name en_CA-w_accents
  add en-common
  add en_CA-w_accents-only

dict:
  name en_GB-ise-wo_accents
  alias en_GB:awli
  alias en_GB-ise:awli
  alias en_GB-wo_accents:awli
  add en-common
  add en_GB-ise-wo_accents-only
dict:
  name en_GB-ise-w_accents
  alias en_GB-w_accents:awli
  add en-common
  add en_GB-ise-w_accents-only
dict:
  name en_GB-ize-wo_accents
  alias en_GB-ize:awli
  add en-common
  add en_GB-ize-wo_accents-only
dict:
  name en_GB-ize-w_accents
  add en-common
  add en_GB-ize-w_accents-only

dict:
  name en_AU-wo_accents
  alias en_AU:awli
  add en-common
  add en_AU-wo_accents-only
dict:
  name en_AU-w_accents
  add en-common
  add en_AU-w_accents-only

dict:
  name en-wo_accents
  alias en:awli
  add en-common
  add en-wo_accents-only
dict:
  name en-w_accents
  add en-common
  add en-w_accents-only

dict:
  name en-variant_0
  alias en_US-variant_0:awli
  add  en-variant_0
dict:
  name en-variant_1
  alias en_US-variant_1:awli
  add  en-variant_1
dict:
  name en-variant_2
  add  en-variant_2

dict:
  name en_GB-variant_0
  add  en_GB-variant_0
dict:
  name en_GB-variant_1
  add  en_GB-variant_1

dict:
  name en_CA-variant_0
  add  en_CA-variant_0
dict:
  name en_CA-variant_1
  add  en_CA-variant_1

dict:
  name en_AU-variant_0
  add  en_AU-variant_0
dict:
  name en_AU-variant_1
  add  en_AU-variant_1
EOF
