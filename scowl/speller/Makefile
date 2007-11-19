
all: 
	@echo "Please use hunspell or aspell as target"

.aspell: make-aspell-dict
	./make-aspell-dict
	touch .aspell
aspell: .aspell

.hunspell: .aspell make-hunspell-dict add-no-suggest en_US.aff en_US.dic.supp
	./make-hunspell-dict
	touch .hunspell
hunspell: .hunspell

clean:
	rm -f .aspell .hunspell
	rm -f *.wl en_US.dic


