#include <uuid.h>

int main(void) {
    uuid_t generated, parsed;
    char text[UUID_STR_LEN];

    uuid_generate_random(generated);
    if (uuid_is_null(generated)) return 1;
    uuid_unparse_lower(generated, text);
    return uuid_parse(text, parsed) != 0 || uuid_compare(generated, parsed) != 0;
}
