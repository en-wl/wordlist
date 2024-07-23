
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
	rm -rf hunspell/ *.zip
	cat to-clean | xargs rm -f

to-clean: .gitignore
	echo `cat .gitignore | grep -v '^#'` | tr ' ' '\n' | grep -v hunspell/ | grep -v \.zip > to-clean

%: %.cc
	g++ -O $*.cc -o $*

deaccent: deaccent.cc
