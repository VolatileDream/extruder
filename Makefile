
all: extruder test

test: extruder
	echo "{{ ls }}" | ./extruder

libmill/configure :
	cd libmill ; ./autogen.sh

libmill/Makefile : libmill/configure
	cd libmill ; ./configure

libmill/.libs/libmill.a : libmill/Makefile
	cd libmill ; make check

extruder: libmill/.libs/libmill.a main.c
	gcc -static -O3 -std=c99 -I . main.c -L libmill/.libs/ -lmill -o extruder
