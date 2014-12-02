// needed to use RTLD_NEXT from dlfcn.h
#define _GNU_SOURCE

#include <stdlib.h>
#include <stdio.h>
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>

#include "tty_redirect.h"
#include "tty_broker_client.h"

int n_ptys_to_redirect = 4;
int ptys_to_redirect[] = { 0, 1, 2, 255 };

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

  if (!already_applied && redirect_needed(ptys_to_redirect, n_ptys_to_redirect)) {
    already_applied = 1;

    ptyfd = target_pty();
    if (ptyfd > 0) {
      redirect_ptys(ptyfd, ptys_to_redirect, n_ptys_to_redirect);
      reattach_controlling_terminal(ptyfd);
    }
  }

  return call_original_execve(filename, argv, envp);
}
