#include <gnutls/gnutls.h>
#include <sodium.h>
#include <sqlite3.h>
#include <zmq.h>

int main(void)
{
    if (!gnutls_check_version("3.8.0") || sodium_init() < 0 || !sqlite3_threadsafe() ||
        !zmq_has("curve") || !zmq_has("WSS")) return 1;
    void *context = zmq_ctx_new();
    return !context || zmq_ctx_term(context);
}
