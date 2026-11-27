#include <execinfo.h>
#include <librsvg/rsvg.h>

#include <cstdlib>
#include <cstring>
#include <unistd.h>

[[gnu::noinline]] static int collect(void **frames, int size) {
    return backtrace(frames, size);
}

int main() {
    if (!rsvg_handle_get_type()) return 1;
    void *frames[8];
    if (backtrace(nullptr, 0) != 0 || collect(frames, 1) != 1) return 1;
    int count = collect(frames, 8);
    if (count < 2 || count > 8 || frames[0] == frames[1]) return 2;

    char **symbols = backtrace_symbols(frames, count);
    if (!symbols) return 3;
    bool address = std::strncmp(symbols[0], "0x", 2) == 0;
    std::free(symbols);
    if (!address) return 4;

    int fds[2];
    if (pipe(fds) != 0) return 5;
    backtrace_symbols_fd(frames, 1, fds[1]);
    close(fds[1]);
    char line[32];
    ssize_t length = read(fds[0], line, sizeof line);
    close(fds[0]);
    return !(length > 3 && line[length - 1] == '\n');
}
