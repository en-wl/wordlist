
all: prep scowl

.PHONY: scowl
scowl:
	$(MAKE) -C scowl

.PHONY: clean
clean:
	$(MAKE) -C scowl clean

prep: .dirs .enable .enable-sup .ukacd .yawl .mwords .census .uk-freq-class

.dirs:
	mkdir -p scowl/working scowl/final
	touch .dirs

.enable: other/enable2k.zip
	unzip -LL other/enable2k.zip -d enable
	touch .enable

.enable-sup: other/supp2k.zip
	unzip -LL other/supp2k.zip -d enable-sup
	cp other/supp2k-nopos.lst enable-sup/nopos.lst
	touch .enable-sup

.ukacd: other/ukacd17.zip
	unzip -LL other/ukacd17.zip -d ukacd
	touch .ukacd

.yawl: other/yawl-0.2.tar.gz
	tar -x -v -z -C yawl -f other/yawl-0.2.tar.gz --strip-components=1
	touch .yawl

.mwords: other/mwords.tar.gz
	tar xfvz other/mwords.tar.gz --exclude=mwords/README
	cp other/mwords-readme-prefix mwords/README
	tar xfz other/mwords.tar.gz --to-stdout mwords/README >> mwords/README
	touch mwords
	touch .mwords

.census: other/census-names-1990.zip
	unzip other/census-names-1990.zip -d census
	touch .census

.uk-freq-class: other/wlist.html.gz
	gunzip -c other/wlist.html.gz > uk-freq-class/wlist.html
	touch .uk-freq-class

.PHONE: test
test: scowl_test varcon_test

.PHONY: scowl_test
scowl_test: scowl
	make -C scowl test

.PHONY: varcon_test
varcon_test:
	cd varcon && echo 'color' | ./translate american australian > /dev/null
