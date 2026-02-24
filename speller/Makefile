SHELL := /bin/bash

.PHONY: all aspell hunspell clean dist-clean

all: 
	@echo "Please use hunspell or aspell as target"

.aspell: make-aspell-dict deaccent
	./make-aspell-dict
	touch .aspell
aspell: .aspell

.hunspell: make-hunspell-dict add-no-suggest en.aff en.dic.supp README_en.txt.sh
	./make-hunspell-dict -all
	touch .hunspell
hunspell: .hunspell

clean: to-clean
	(shopt -s nullglob; echo $$(cat to-clean); rm -f $$(cat to-clean))

dist-clean: clean
	rm -rf hunspell/
	rm -f aspell6-en-*.tar.bz2

to-clean: .gitignore
	sed -e '/^#/d' -e 's/^\///' -e '/^hunspell\//d' -e '/^aspell6-en/d'  .gitignore > to-clean

%: %.cc
	g++ -O $*.cc -o $*

deaccent: deaccent.cc
