
all: prep scowl

.PHONY: scowl
scowl:
	$(MAKE) -C scowl

.PHONY: clean
clean:
	$(MAKE) -C scowl clean

prep: .enable .enable-sup .ukacd .yawl .mwords .census .uk-freq-class

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
	tar xfvz other/mwords.tar.gz
	touch mwords
	touch .mwords

.census: other/census-names-1990.zip
	unzip other/census-names-1990.zip -d census
	touch .census

.uk-freq-class: other/wlist.html.gz
	gunzip -c other/wlist.html.gz > uk-freq-class/wlist.html
	touch .uk-freq-class
