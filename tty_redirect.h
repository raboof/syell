int redirect_needed(int fds[], int n_fds);
void redirect_ptys(int targetpty, int fds[], int n_fds);
void reattach_controlling_terminal(int ptyfd);
