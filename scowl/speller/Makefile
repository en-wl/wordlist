
all: 
	@echo "Please use hunspell or aspell as target"

.aspell: make-aspell-dict
	make -C src deaccent
	./make-aspell-dict
	touch .aspell
aspell: .aspell

.hunspell: .aspell make-hunspell-dict add-no-suggest en.aff en.dic.supp
	./make-hunspell-dict
	touch .hunspell
hunspell: .hunspell

clean:
	rm -f .aspell .hunspell
	rm -f *.wl en_*.dic en_*.aff *.zip *.tocheck README_en_??.txt
