/* Exercise libc and the compiler's static/PIE link specs without extra libraries. */
#include <iconv.h>
#include <regex.h>
#include <stdlib.h>
#include <string.h>

static int compare(const void *left, const void *right) {
    int a = *(const int *)left, b = *(const int *)right;
    return (a > b) - (a < b);
}

int main(void) {
    int values[4096];
    for (int i = 0; i < 4096; ++i) values[i] = (i * 997) % 4096;
    qsort(values, 4096, sizeof(*values), compare);
    for (int i = 0; i < 4096; ++i) if (values[i] != i) return 1;

    /* GB18030's first non-BMP character must become U+10000 in UTF-8. */
    char input[] = "\x90\x30\x81\x30", output[8] = {0};
    char *in = input, *out = output;
    size_t in_left = 4, out_left = sizeof(output);
    iconv_t cd = iconv_open("UTF-8", "GB18030");
    if (cd == (iconv_t)-1) return 2;
    size_t result = iconv(cd, &in, &in_left, &out, &out_left);
    iconv_close(cd);
    if (result == (size_t)-1 || in_left || out - output != 4 ||
        memcmp(output, "\xf0\x90\x80\x80", 4)) return 3;

    regex_t regex;
    if (regcomp(&regex, "^(ab|cd)+[0-9]{1,3}$", REG_EXTENDED)) return 4;
    int match = regexec(&regex, "abcd123", 0, NULL, 0);
    regfree(&regex);
    return match ? 5 : 0;
}
