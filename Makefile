
all: prep scowl

.PHONY: scowl
scowl:
	$(MAKE) -C scowl

.PHONY: clean
clean:
	$(MAKE) -C scowl clean

prep: enable enable-sup ukacd yawl mwords census uk-freq-class

enable: other/enable2k.zip
	mkdir -p enable
	unzip -LL other/enable2k.zip -d enable

enable-sup: other/supp2k.zip
	mkdir -p enable-sup
	unzip -LL other/supp2k.zip -d enable-sup
	cp other/supp2k-nopos.lst enable-sup/nopos.lst

ukacd: other/ukacd17.zip
	mkdir -p ukacd
	unzip -LL other/ukacd17.zip -d ukacd

yawl: other/yawl-0.2.tar.gz
	mkdir -p yawl
	tar -x -v -z -C yawl -f other/yawl-0.2.tar.gz --strip-components=1

mwords: other/mwords.tar.gz
	tar xfvz other/mwords.tar.gz
	touch mwords

census: other/census-names-1990.zip
	mkdir -p census
	unzip other/census-names-1990.zip -d census

uk-freq-class: other/wlist.html.gz
	mkdir -p uk-freq-class
	gunzip -c other/wlist.html.gz > uk-freq-class/wlist.html
