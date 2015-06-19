
extruder:
	gcc -static -O3 -std=c99 -I . main.c -L . -lmill -o extruder
