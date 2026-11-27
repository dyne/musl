#include "execinfo.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <unwind.h>

struct trace {
    void **buffer;
    int size;
    int count;
    int skip;
};

static _Unwind_Reason_Code collect_frame(struct _Unwind_Context *context, void *data) {
    struct trace *trace = data;
    uintptr_t address = _Unwind_GetIP(context);
    if (!address)
        return _URC_END_OF_STACK;
    if (trace->skip) {
        trace->skip = 0;
        return _URC_NO_REASON;
    }
    trace->buffer[trace->count++] = (void *)address;
    return trace->count == trace->size ? _URC_END_OF_STACK : _URC_NO_REASON;
}

int backtrace(void **buffer, int size) {
    if (size <= 0)
        return 0;
    struct trace trace = {buffer, size, 0, 1};
    _Unwind_Backtrace(collect_frame, &trace);
    return trace.count;
}

enum { address_size = 2 + 2 * sizeof(uintptr_t) + 1 };

char **backtrace_symbols(void *const *buffer, int size) {
    if (size < 0 || (size_t)size > SIZE_MAX / (sizeof(char *) + address_size)) {
        errno = ENOMEM;
        return NULL;
    }
    char **symbols = malloc((size_t)size * (sizeof(char *) + address_size));
    if (!symbols)
        return NULL;
    char *text = (char *)(symbols + size);
    for (int i = 0; i < size; ++i) {
        symbols[i] = text;
        snprintf(text, address_size, "%p", buffer[i]);
        text += address_size;
    }
    return symbols;
}

void backtrace_symbols_fd(void *const *buffer, int size, int fd) {
    for (int i = 0; i < size; ++i) {
        char text[address_size + 1];
        int length = snprintf(text, sizeof text, "%p\n", buffer[i]);
        for (int offset = 0; offset < length;) {
            ssize_t written = write(fd, text + offset, (size_t)(length - offset));
            if (written < 0 && errno == EINTR)
                continue;
            if (written <= 0)
                return;
            offset += (int)written;
        }
    }
}
