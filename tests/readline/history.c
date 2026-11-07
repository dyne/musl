#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <readline/history.h>

int main(void) {
    using_history();
    add_history("first");
    add_history("second");
    if (history_length != 2 || !history_get(history_base) ||
        strcmp(history_get(history_base)->line, "first")) return 1;
    char *expanded = NULL;
    if (history_expand("!!", &expanded) != 1 || !expanded ||
        strcmp(expanded, "second")) return 2;
    free(expanded);
    stifle_history(1);
    if (history_length != 1 || strcmp(history_list()[0]->line, "second")) return 3;
    clear_history();
    return history_length != 0;
}
