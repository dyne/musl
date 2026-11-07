#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <readline/readline.h>
#include <readline/keymaps.h>
#include <readline/tilde.h>

int main(void) {
    FILE *input = tmpfile();
    FILE *output = tmpfile();
    if (!input || !output) return 1;
    fputs("musl readline\n", input);
    rewind(input);
    rl_instream = input;
    rl_outstream = output;
    rl_readline_name = "dyne-smoke";
    /* Smoke runs use INPUTRC=/dev/null and TERM=dumb for reproducibility. */
    rl_initialize();
    if (rl_variable_bind("editing-mode", "emacs")) return 2;
    char *line = readline(NULL);
    int failed = !line || strcmp(line, "musl readline") || !rl_get_keymap();
    free(line);
    fclose(input);
    fclose(output);
    return failed;
}
