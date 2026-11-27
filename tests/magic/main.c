#include <magic.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    /* Gzip-compressed one-pixel GIF. */
    static const unsigned char gif_gzip[] = {
        0x1f, 0x8b, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0xff, 0x73, 0xf7,
        0x74, 0xb3, 0xb0, 0x4c, 0x64, 0x64, 0x60, 0x64, 0x68, 0x60, 0x00, 0x81,
        0xff, 0xff, 0xff, 0x2b, 0xfe, 0x64, 0x61, 0x04, 0x31, 0x75, 0x40, 0x04,
        0x48, 0x86, 0x81, 0x89, 0xd1, 0x85, 0xc1, 0x1a, 0x00, 0x78, 0x13, 0x95,
        0x27, 0x2a, 0x00, 0x00, 0x00
    };
    if (argc != 2) return 1;
    magic_t cookie = magic_open(MAGIC_MIME_TYPE | MAGIC_COMPRESS | MAGIC_COMPRESS_TRANSP);
    if (!cookie) return 2;
    if (magic_load(cookie, argv[1]) != 0) {
        fprintf(stderr, "magic_load: %s\n", magic_error(cookie));
        magic_close(cookie);
        return 3;
    }
    const char *mime = magic_buffer(cookie, gif_gzip, sizeof gif_gzip);
    int result = !mime || strcmp(mime, "image/gif") != 0;
    if (result)
        fprintf(stderr, "Expected image/gif, got %s\n", mime ? mime : magic_error(cookie));
    magic_close(cookie);
    return result;
}
