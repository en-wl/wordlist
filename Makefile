.PHONY: all clean

all: scowl.db scowl.txt

.DELETE_ON_ERROR:
scowl-tmp.txt: scowl-orig.txt patch
	./util/patch.py < patch > scowl-tmp.txt

.DELETE_ON_ERROR:
scowl.db: scowl-tmp.txt
	rm -f scowl.db
	./scowl create-db scowl.db < scowl-tmp.txt

.DELETE_ON_ERROR:
scowl.txt: scowl.db
	./scowl export-db scowl.db > scowl.txt

clean:
	rm -f scowl-tmp.txt
