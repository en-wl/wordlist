#
# Make dam sure that the locale is set to C
#

LANG=C
LC_ALL=C
LC_CTYPE=C
LC_COLLATE=C
export LANG LC_ALL LC_CTYPE LC_COLLATE

#
# Special targets
#

levels := $(shell cat l/levels-list 2> /dev/null)

programs := src/deaccent src/find-accented

.PHONY: all
all: $(foreach l, $(levels), final/english-words.$(l)) \
  final/special-roman-numerals.35 final/special-hacker.50 \
  README

.PHONY: clean
clean:
	rm -f working/* $(programs) r/varcon/*.lst r/varcon/variant.tab r/mwords/*.lst r/alt12dicts/*.lst r/ispell/all.* r/pos/word.lst r/uk-freq-class/uk.?? r/census/*.lst debug/*
	make -C speller clean

#
# README
#

README: src/make-README $(foreach l, $(levels), final/english-words.$(l))
	src/make-README

#
# Actual word list creation
#

working/%.mk: l/levels-list
	src/make-call-list $*

make_words = working/words.$(1): $(shell src/make-words-deps $(1)); \
	src/make-words $(1)
-include working/make_words.mk
working/words.00:
	-rm -f working/words.00
	touch working/words.00

split_list = $(shell src/list-combin working/ $(1).pre): \
  $(shell src/split-words-deps $(1)); \
	 src/split-words $(1)
$(call split_list,00)
-include working/split_list.mk

make_final = $(shell src/list-combin final/ $(1) ):                        \
   src/make-final working/with-accents.lst src/add-accents                 \
   $(shell src/list-combin working/ $(1).pre)                              \
   $(shell src/list-combin working/ $(shell src/get-level prev $(1)).pre); \
	src/make-final  $(1)
-include working/make_final.mk

#
# Special lists
#

working/all.lst working/all.lst-unfiltered: \
  src/make-all.lst $(shell find l/supplement/ l/add-affixes/ l/add-possessive -type l)
	$<

working/variant_1.lst working/variant_2.lst working/variant_3.lst: \
  src/make-variant.lst         r/alt12dicts/variant-also.lst \
  r/alt12dicts/variant-yes.lst r/alt12dicts/variant-maybe.lst \
  r/infl/variant_0.lst  r/infl/variant_1.lst  r/infl/variant_2.lst \
  r/varcon/british.lst r/varcon/british_z.lst r/varcon/canadian.lst \
  r/varcon/w_variant-amer.lst r/varcon/w_variant-nonamer.lst  \
  r/special/variant_1  r/special/variant_2  r/special/variant_3 \
  r/special/never-variant
	touch working/possessive-also.lst
	$<
	rm working/possessive-also.lst
	$(MAKE) working/possessive-also.lst
	$<

working/contractions.lst: src/make-contractions.lst working/words.95 working/proper-names.lst working/abbreviations.lst
	$<

working/known-upper.lst: src/make-known-upper.lst l/upper/* \
  src/add-other-spellings r/varcon/voc.tab r/varcon/variant.tab
	$<

working/proper-names.lst: src/make-proper-names.lst \
  working/known-upper.lst l/proper-names/*            \
  working/all.lst working/abbreviations.lst.pre
	$<

working/abbreviations.lst.pre: src/make-abbreviations.lst.pre \
  src/add-affixes \
  working/all.lst working/known-upper.lst l/abbreviations/* \
  r/special/never-abbreviations
	$<

working/abbreviations.lst: src/make-abbreviations.lst \
  working/abbreviations.lst.pre working/proper-names.lst
	$<

working/upper.lst: src/make-upper.lst \
  src/add-affixes working/possessive-also.lst \
  working/known-upper.lst working/abbreviations.lst
	$<

working/possessive-also.lst: src/make-possessive.lst r/special/add-possessive \
  working/abbreviations.lst.pre working/proper-names.lst
	$<

working/with-accents.lst working/without-accents.lst: \
  src/make-accent-lists src/deaccent src/find-accented l/accented/squashed-accented.lst
	$<

# 
# Special lists in final
#

final/special-roman-numerals.35: r/special/roman-numerals
	cp $< $@

final/special-hacker.50: l/hacker/* r/special/hacker-exclude
	cat l/hacker/* | sort -u | comm -23 - r/special/hacker-exclude > $@

#
# Modified form of Raw Lists
#

r/mwords/frequent.lst: src/make-frequent.lst r/mwords/10001fr.equ r/mwords/10002fr.equ
	$<

r/census/dist.all.last.lst r/census/dist.female.first.lst r/census/dist.male.first.lst: \
  src/proc-census \
  r/census/dist.all.last r/census/dist.female.first r/census/dist.male.first
	$<

$(foreach b, \
  02of12 05of12 11of12 abbr not-abbr variant-maybe variant-also variant-yes not-variant,\
  r/alt12dicts/$(b).lst): src/proc-alt12dicts
	$<

r/alt12dicts/3esl.lst: r/alt12dicts/3esl.txt src/clean-alan-list
	src/clean-alan-list < $< > $@

r/alt12dicts/2of4brif.lst: r/alt12dicts/2of4brif.txt src/clean-alan-list
	src/clean-alan-list < $< > $@

r/alt12dicts/5desk.lst: r/alt12dicts/5desk.txt src/clean-alan-list
	src/clean-alan-list < $< > $@

r/alt12dicts/signature.lst: r/alt12dicts/signature.txt src/clean-alan-list
	src/clean-alan-list < $< > $@

r/alt12dicts/neol-50.lst r/alt12dicts/neol-80.lst: r/alt12dicts/neol2016.txt
	src/proc-neol

l/supplement/50/neol-50.lst: r/alt12dicts/neol-50.lst
l/supplement/80/neol-80.lst: r/alt12dicts/neol-80.lst

#
#r/ispell/all.0 r/ispell/all.1: r/ispell/all.%: \
#  src/make-ispell-all.lst 
#	$< $*

#$(foreach b, \
#  abbreviations acronyms english variant non-american all,\
#  r/12dicts/$(b).lst): \
#src/proc-12dicts r/12dicts/6of12.txt
#	src/proc-12dicts

r/varcon/american.lst r/varcon/british.lst r/varcon/british_z.lst r/varcon/canadian.lst: \
  r/varcon/split r/varcon/varcon.txt
	cd r/varcon; ./split

r/varcon/w_variant-amer.lst r/varcon/w_variant-nonamer.lst: \
  r/varcon/split r/varcon/varcon.txt
	cd r/varcon; ./w_variant

r/varcon/variant.tab: r/varcon/make-variant r/varcon/varcon.txt r/varcon/variant-also.tab r/varcon/variant-infl.tab
	cd r/varcon; ./make-variant no-infl

r/ukacd/deaccented.lst: src/make-ukacd-deaccented.lst \
  r/ukacd/ukacd17.txt src/deaccent
	$<

r/ukacd/squashed.lst: src/make-ukacd-squashed.lst r/ukacd/deaccented.lst
	$<

r/ukacd/squashed-accented.lst: \
  src/make-ukacd-squashed-accented.lst r/ukacd/ukacd17.txt
	$<

r/pos/word.lst: r/pos/part-of-speech.txt
	cat r/pos/part-of-speech.txt | cut -f1 > r/pos/word.lst

r/uk-freq-class/uk.%: src/proc-uk-freq-class
	$<

#
# Special programs creation
#

$(programs): src/%: src/%.cc
	cd src && make $*

#
# Level information
#

l/levels-list: l/levels
	sed 's/#.*$$//' < l/levels > l/levels-list

#
# Makefiles creation
#

Makefile: l/levels-list

deps: .symbolic-deps
.symbolic-deps: $(shell find l -type d)
	src/make-symbolic-deps
-include .symbolic-deps

#
# Sanity checks and related
#
scowl.db: final/*
	-rm scowl.db
	sql/create.sh

test: scowl.db
	make -C speller hunspell
	sql/test
