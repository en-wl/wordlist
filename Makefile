.PHONY: all clean

all: scowl.db

.DELETE_ON_ERROR:
scowl.db: ./combine.py
	rm -f scowl.db
	./combine.py

.DELETE_ON_ERROR:
scowl.txt: scowl.db
	./scowl export-db scowl.db > scowl.txt

clean:
	rm -f scowl.db scowl.txt
