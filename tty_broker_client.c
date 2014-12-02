#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

#include "tty_broker_client.h"

int target_pty() {
  char * ptyfile = getenv("CQRSH_PTY");
  int ptyfd = open(ptyfile, O_RDWR);

  if (!isatty(ptyfd)) {
    fprintf(stderr, "ptyfd is not a tty\n");
    return -1;
  } else {
    return ptyfd;
  }
}
