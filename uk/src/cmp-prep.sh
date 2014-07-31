set -e

export LC_ALL=C

mkdir -p working

gunzip ../scowl/speller/hunspell/*.gz

cat ../scowl/speller/hunspell/en_GB-ize.txt ../scowl/speller/hunspell/en_GB-ise.txt | sort -u > working/en_GB.txt
cp ../scowl/speller/hunspell/en_GB-large.txt working/

cat src/wordlist_marcoagpinto_20140701_140276w.txt | iconv -f utf-8 -t iso88591 | sort -u > working/marco.txt

cd working

comm -23 en_GB.txt marco.txt > en_GB-only.txt
comm -13 en_GB.txt marco.txt > marco-small-only.txt
comm -23 en_GB-large.txt marco.txt > en_GB-large-only.txt
comm -13 en_GB-large.txt marco.txt > marco-large-only.txt

aspell --local-data-dir ../src -l en2 munch-list < en_GB-only.txt > en_GB-only.munched

cat en_GB.txt | (cd ../../scowl; ./src/add-other-spellings table) > variant.tab




