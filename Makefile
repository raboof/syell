all: detach isatty overrideexecve.so

.PHONY: clean

clean:
	@rm isatty detach overrideexecve.so *.o || true
	@rm tty-*.txt || true

CFLAGS=-Wall -fPIC

isatty: isatty.c
	$(CC) $(CFLAGS) isatty.c -o isatty

detach: detach.c
	$(CC) $(CFLAGS) detach.c -o detach

%.o : %.c
	$(CC) -c $(CFLAGS) $< -o $@

overrideexecve.so: overrideexecve.o tty_redirect.o tty_broker_client.o
	$(CC) -fPIC -o $@ -shared $^ -pthread -ldl
