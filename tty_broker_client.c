#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>

#include <string.h>

#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include "tty_broker_client.h"

char * get_pty_file_from_environment() {
  char * result = getenv("SYELL_PTY");
  if (result == NULL)
    return NULL;
  else
    return strdup(result);
}


int connect_to_broker(int port) {
  struct sockaddr_in tty_broker;
  int sock = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP);

  if (sock < 0) {
    perror("Could not create socket");
    return -1;
  }

  memset(&tty_broker, 0, sizeof(tty_broker));
  tty_broker.sin_family = AF_INET;
  tty_broker.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  tty_broker.sin_port = htons(port);

  if (connect(sock, (struct sockaddr *) &tty_broker, sizeof(tty_broker)) < 0) {
    perror("Could not connect");
    return -1;
  }
  return sock;
}

#define BUFSIZE 1024

char * get_pty_file_from_broker() {
  int port = atoi(getenv("TTY_BROKER_PORT"));
  int sock = connect_to_broker(port);
  unsigned char responseLength = -1;
  char buf[BUFSIZE];

  if (sock < 0) {
    return NULL;
  }

  if (send(sock, "x", 1, 0) < 0) {
    perror("Error sending command header");
    goto error;
  }

  if (read(sock, &responseLength, 1) < 0) {
    if (errno == EINTR)
      // This can succeed the second time - if not, give up after all.
      if (read(sock, &responseLength, 1) < 0) {
        perror("Error receiving response header");
        goto error;
      }
  }
  if (responseLength == -1) {
    fprintf(stderr, "Stream end encountered while trying to read response header\n");
  }
  if (responseLength > BUFSIZE + 1) {
    fprintf(stderr, "Response too large: %d\n", responseLength);
    goto error;
  }
  fprintf(stderr, "Reading response of size: %hhd", responseLength);
  if (read(sock, buf, responseLength) < responseLength) {
    fprintf(stderr, "Error receiving response\n");
    goto error;
  }
  buf[(int)responseLength] = '\0';
  fprintf(stderr, "Got response: %s", buf);

  close(sock);
  return strdup(buf);

error:
  close(sock);
  return NULL;
}

char * get_pty_file() {
  char * ptyfile = get_pty_file_from_environment();
  if (ptyfile != NULL)
    return ptyfile;
  else
    return get_pty_file_from_broker();
}

int target_pty() {
  char * ptyfile = get_pty_file();
  int ptyfd = open(ptyfile, O_RDWR);

  if (!isatty(ptyfd)) {
    fprintf(stderr, "ptyfd %d (%s) is not a tty\n", ptyfd, ptyfile);
    free(ptyfile);
    return -1;
  } else {
    free(ptyfile);
    return ptyfd;
  }
}
