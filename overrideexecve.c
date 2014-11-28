// needed to use RTLD_NEXT from dlfcn.h
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

void redirect_ttyoutput(int new_destination, int original) {
  if (isatty(original))
    dup2(new_destination, original);
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

int length(char *const envp[]) {
  if (*envp == NULL)
    return 0;
  else 
    return 1 + length(envp + 1);
}

char** without_ourselves(char *const envp[]) {
  int source_items = length(envp); 
  char** result = calloc(source_items + 1, sizeof(char *));

  int source_item;
  int target_item;

  for (target_item = 0, source_item = 0; 
    source_item < source_items; 
    target_item++, source_item++) {

    if (strncmp("LD_PRELOAD", envp[source_item], 10) == 0)
      target_item--;
    else 
      result[target_item] = envp[source_item];

  }

  result[target_item] = NULL;

  return result;
}

int redirect_pty(char *pty) {
  int ptyfd = open(pty, O_RDWR);

  if (!isatty(ptyfd)) {
    fprintf(stderr, "ptyfd is not a tty\n");
    return -1;
  } else {
    redirect_ttyoutput(ptyfd, 0);
    redirect_ttyoutput(ptyfd, 1);
    redirect_ttyoutput(ptyfd, 2);
    redirect_ttyoutput(ptyfd, 255);

    return ptyfd;
  }

}

int call_original_execve(const char *filename, char *const argv[], char *const envp[]) {
  static int (*original_execve)() = NULL;
  int result;

  if(!original_execve)
    original_execve = (int(*)()) dlsym(RTLD_NEXT, "execve");

  if(!original_execve)
    fprintf(stderr, "Error dlsym'ing execve\n");

  result = original_execve(filename, argv, without_ourselves(envp));
  return result;
}

int execve(const char *filename, char *const argv[], char *const envp[]) {
  static int already_applied = 0;
  int ptyfd;

  if (!already_applied) {
    already_applied = 1;
    ptyfd = redirect_pty(getenv("CQRSH_PTY"));
    if (ptyfd > 0)
      reattach_controlling_terminal(ptyfd);
  }

  return call_original_execve(filename, argv, envp);
}
