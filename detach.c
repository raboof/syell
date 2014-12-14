#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

void write_pty(int fd) {
  char tty[255];
  char fd1[255];
  ssize_t tty_size;

  snprintf(fd1, 254, "/proc/%d/fd/1", getpid());
  tty_size = readlink(fd1, tty, 254);
  if (tty_size < 0) {
    perror("Could not read link");
    exit(-1);
  }
  if (write(fd, tty, tty_size) <= 0) {
    perror("Error writing");
  }
}

void log_pty(char *filename) {
  int file;

  file = creat(filename, S_IRUSR|S_IWUSR);
  if (file < 1) {
    perror("Could not open file for writing");
    exit(-1);
  }

  write_pty(file);

  close(file);
}

/**
 * Close stdin, stdout and stderr and wait for a while.
 * 
 * (start in an xterm to get a 'free' terminal)
 * 
 * Usage:
 *   detach [ttyfile]
 *
 * ttyfile: the device name of the tty attached to this process is written to a file with this name
 */
int main(int argc, char** argv) {
  if (argc > 1)
    log_pty(argv[1]);
  else
    write_pty(1);

  close(0);
  //close(1);
  //close(2);

  pause();

  return 0;
}
