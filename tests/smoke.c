#include <curl/curl.h>
#include <libssh2.h>
#include <ncursesw/curses.h>
#include <openssl/ssl.h>
#include <zlib.h>

int main(void) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_method());
    if (!ctx || !zlibVersion() || !curses_version() || libssh2_init(0)) return 1;
    SSL_CTX_free(ctx);
    libssh2_exit();
    const curl_version_info_data *info = curl_version_info(CURLVERSION_NOW);
    return !(info->features & CURL_VERSION_SSL) ||
           !(info->features & CURL_VERSION_LIBZ) || !info->libssh_version;
}
