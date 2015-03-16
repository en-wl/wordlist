
all: 
	@echo "Please use hunspell or aspell as target"

.aspell: make-aspell-dict
	make -C src deaccent
	./make-aspell-dict $(size)
	touch .aspell
aspell: .aspell

.hunspell: make-hunspell-dict add-no-suggest en.aff en.dic.supp README_en.txt.sh
	make -C src deaccent
	./make-hunspell-dict -all $(size)
	touch .hunspell
hunspell: .hunspell

size = 60
cc = US
accents = with-and-without-accents
variant =
dictname = $(cc)$(variant)-$(accents)-$(size)

.single:
	./make-hunspell-dict -one en_$(dictname) \
	"mk-list $(variant) en_$(cc) $(size) | $(accents)"
	cp en_$(dictname).0 aspell/en_$(dictname).wl
	touch .single
single: .single

clean:
	rm -f .aspell .hunspell .single
	rm -f *.wl* en_*.dic en_*.aff *.zip *.tocheck README*.txt
	rm -f en_*txt en_*[0-2] nosug eng*.dat
	rm -rf hunspell aspell/*wl aspell/info aspell/Copyright
