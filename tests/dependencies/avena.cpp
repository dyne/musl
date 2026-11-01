#include <openssl/err.h>
#include <openssl/ssl.h>

#include <atomic>
#include <cstdio>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <thread>

static void require(bool condition, const char* operation)
{
    if (!condition) throw std::runtime_error(operation);
}

int main()
{
    try {
        std::atomic<std::uint64_t> calls{0};
        std::thread worker([&] { calls.fetch_add(1); });
        worker.join();
        require(calls.load() == 1, "C++17 threads/atomics");

        // Exercise the OpenSSL API used by avena without external certificates
        // or network access. An empty memory transport must request more input.
        require(OPENSSL_init_ssl(0, nullptr) == 1, "OPENSSL_init_ssl");
        std::unique_ptr<SSL_CTX, decltype(&SSL_CTX_free)> context(
            SSL_CTX_new(TLS_client_method()), SSL_CTX_free);
        require(context != nullptr, "SSL_CTX_new");
        require(SSL_CTX_set_min_proto_version(context.get(), TLS1_2_VERSION) == 1,
                "SSL_CTX_set_min_proto_version");
        std::unique_ptr<SSL, decltype(&SSL_free)> connection(
            SSL_new(context.get()), SSL_free);
        require(connection != nullptr, "SSL_new");
        std::unique_ptr<BIO, decltype(&BIO_free)> input(BIO_new(BIO_s_mem()), BIO_free);
        std::unique_ptr<BIO, decltype(&BIO_free)> output(BIO_new(BIO_s_mem()), BIO_free);
        require(input && output, "BIO_new");
        SSL_set_bio(connection.get(), input.release(), output.release());
        SSL_set_connect_state(connection.get());
        ERR_clear_error();
        const int result = SSL_do_handshake(connection.get());
        require(result < 0 && SSL_get_error(connection.get(), result) == SSL_ERROR_WANT_READ,
                "SSL_do_handshake/SSL_get_error");
        require(BIO_ctrl_pending(SSL_get_wbio(connection.get())) > 0, "TLS ClientHello");
        std::cout << "avena C++17/thread/atomic and static TLS dependencies passed\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        ERR_print_errors_fp(stderr);
        return 1;
    }
}
