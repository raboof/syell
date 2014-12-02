#include <stdio.h>

#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>

#include "tty_redirect.h"

int redirect_needed(int fds[], int n_fds) {
  int i;
  for (i = 0; i < n_fds; i++)
    if (isatty(fds[i]))
      return 1;
  return 0;
}

void reattach_controlling_terminal(int ptyfd) {
  int current_tty = open("/dev/tty", O_NOCTTY|O_NONBLOCK|O_RDONLY);
  if (current_tty < 0) {
    perror("Could not open current tty");
    return;
  }

  if (ioctl(current_tty, TIOCNOTTY, NULL) < 0) 
    perror("Could not detach from tty");

  // We currently don't attach the target terminal as the controlling terminal,
  // as it seems special privileges are needed for that and it doesn't appear
  // to be needed in practice...

  return;

  /** 
    There is a bit of trickery involved to make sure the target pty becomes the 
    controlling terminal of the program we execve.

    Invariants are:
    * every process in a session has the same terminal
    * to attach to a controlling terminal, we must be a session leader
    * a process that is a process group leader cannot become session leader
    
    At this point:
    * bash has made us our own process group leader
    * we want to become a session leader (but that's not allowed for a pg leader) 
    
    What we want to do is: 
    * fork() off a child process
    * make that child process start a new process group
    * join that process group ourselves
    * ... and then we're allowed to become session leader and attach a controlling terminal
  */

  int child_pid = fork();
  if (fork < 0)
    perror("Failed to fork process group leader");
  else if (child_pid == 0) {
    if (setpgid(0, 0) < 0)
      perror("Could not create process group");
    exit(0);
  }

  // TODO get rid of this race condition, i.e. by detecting the death of the child process?
  sleep(1);

  if (setpgid(0, child_pid) < 0)
    perror("Failed to join childs' process group");

  if (setsid() < 0)
    perror("Could not create session group");
  
  if (ioctl(ptyfd, TIOCSCTTY, 1) < 0) 
    perror("Error stealing tty");
}

void redirect_ttyoutput(int new_destination, int original) {
  if (isatty(original))
    dup2(new_destination, original);
}

void redirect_ptys(int targetpty, int fds[], int n_fds) {
  int i;
  for (i = 0; i < n_fds; i++)
    redirect_ttyoutput(targetpty, fds[i]);
}

