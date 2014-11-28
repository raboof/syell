#include <stdio.h>
#include <unistd.h>

int main() {
  printf("stdout is %sa tty.\n", isatty(1) ? "" : "not ");

  return 0;
}
