SHELL := /bin/bash

.PHONY: all aspell hunspell libreoffice clean dist-clean

all: 
	@echo "Please use hunspell, aspell, or libreoffice as target"

.aspell: make-aspell-dict deaccent
	./make-aspell-dict
	touch .aspell
aspell: .aspell

.hunspell: make-hunspell-dict add-no-suggest en.aff en.dic.supp README_en.txt.sh
	./make-hunspell-dict -all
	touch .hunspell
hunspell: .hunspell

.libreoffice: .hunspell make-libreoffice
	./make-libreoffice
	touch .libreoffice
libreoffice: .libreoffice

clean: to-clean
	(shopt -s nullglob; echo $$(cat to-clean); rm -f $$(cat to-clean))
	rm -rf lo-dict-en-esdb*

dist-clean: clean
	rm -rf hunspell/
	rm -f aspell6-en-*.tar.bz2
	rm -f dict-en-esdb*.oxt

to-clean: .gitignore Makefile
	sed -e '/^#/d' -e 's/^\///' -e '/^hunspell\//d' -e '/^aspell6-en/d'  -e '/^dict-en-esdb/d' -e '/\/$$/d' .gitignore > to-clean

%: %.cc
	g++ -O $*.cc -o $*

deaccent: deaccent.cc
