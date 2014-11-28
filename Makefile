all: detach isatty overrideexecve.so

.PHONY: clean

clean:
	@rm isatty detach overrideexecve.so || true
	@rm tty-*.txt || true

isatty: isatty.c
	gcc -Wall isatty.c -o isatty

detach: detach.c
	gcc -Wall detach.c -o detach

overrideexecve.so: overrideexecve.c
	gcc -Wall -fPIC -o overrideexecve.so -shared overrideexecve.c -pthread -ldl -ljack
