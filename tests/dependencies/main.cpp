#include <boost/multi_index_container.hpp>
#include <boost/multi_index/hashed_index.hpp>
#include <boost/multi_index/member.hpp>
#include <gnutls/gnutls.h>
#include <gnutls/x509.h>
#include <sodium.h>
#include <sqlite3.h>
#include <zmq.h>

#include <array>
#include <cstring>
#include <ctime>
#include <iostream>
#include <stdexcept>
#include <string>

static void require(bool condition, const char* operation)
{
    if (!condition) throw std::runtime_error(operation);
}

static void tls(int result)
{
    if (result < 0) throw std::runtime_error(gnutls_strerror(result));
}

// Every invocation creates its own key and short-lived localhost certificate.
// No external tools, network services, committed private keys or fixed dates.
struct Certificate {
    gnutls_x509_privkey_t key{};
    gnutls_x509_crt_t cert{};
    gnutls_datum_t key_pem{}, cert_pem{};
    Certificate()
    {
        tls(gnutls_x509_privkey_init(&key));
        tls(gnutls_x509_crt_init(&cert));
        tls(gnutls_x509_privkey_generate(key, GNUTLS_PK_EC, GNUTLS_CURVE_TO_BITS(GNUTLS_ECC_CURVE_SECP256R1), 0));
        tls(gnutls_x509_crt_set_version(cert, 3));
        unsigned char serial[16];
        randombytes_buf(serial, sizeof(serial));
        serial[0] &= 0x7f;
        serial[0] |= 1;
        tls(gnutls_x509_crt_set_serial(cert, serial, sizeof(serial)));
        tls(gnutls_x509_crt_set_activation_time(cert, std::time(nullptr) - 60));
        tls(gnutls_x509_crt_set_expiration_time(cert, std::time(nullptr) + 3600));
        tls(gnutls_x509_crt_set_dn_by_oid(cert, GNUTLS_OID_X520_COMMON_NAME, 0, "localhost", 9));
        tls(gnutls_x509_crt_set_subject_alt_name(cert, GNUTLS_SAN_DNSNAME, "localhost", 9, GNUTLS_FSAN_SET));
        tls(gnutls_x509_crt_set_basic_constraints(cert, 1, -1));
        tls(gnutls_x509_crt_set_key_usage(cert, GNUTLS_KEY_DIGITAL_SIGNATURE | GNUTLS_KEY_KEY_CERT_SIGN));
        tls(gnutls_x509_crt_set_key_purpose_oid(cert, GNUTLS_KP_TLS_WWW_SERVER, 0));
        tls(gnutls_x509_crt_set_key(cert, key));
        tls(gnutls_x509_crt_sign2(cert, cert, key, GNUTLS_DIG_SHA256, 0));
        tls(gnutls_x509_privkey_export2(key, GNUTLS_X509_FMT_PEM, &key_pem));
        tls(gnutls_x509_crt_export2(cert, GNUTLS_X509_FMT_PEM, &cert_pem));
    }
    ~Certificate()
    {
        gnutls_free(key_pem.data);
        gnutls_free(cert_pem.data);
        gnutls_x509_crt_deinit(cert);
        gnutls_x509_privkey_deinit(key);
    }
};

struct Context {
    void* value = zmq_ctx_new();
    Context() { require(value, "zmq_ctx_new"); }
    ~Context() { zmq_ctx_term(value); }
};

struct Socket {
    void* value;
    Socket(Context& context, int type) : value(zmq_socket(context.value, type))
    {
        require(value, "zmq_socket");
        option(ZMQ_LINGER, 0);
        option(ZMQ_RCVTIMEO, 8000);
        option(ZMQ_SNDTIMEO, 8000);
        option(ZMQ_HANDSHAKE_IVL, 5000);
        option(ZMQ_RECONNECT_IVL, -1);
    }
    ~Socket() { zmq_close(value); }
    void option(int name, const void* data, size_t size)
    {
        require(zmq_setsockopt(value, name, data, size) == 0, "zmq_setsockopt");
    }
    void option(int name, int number) { option(name, &number, sizeof(number)); }
    void option(int name, const std::string& text) { option(name, text.data(), text.size()); }
    std::string bind(const char* address)
    {
        require(zmq_bind(value, address) == 0, "zmq_bind");
        char endpoint[256];
        size_t size = sizeof(endpoint);
        require(zmq_getsockopt(value, ZMQ_LAST_ENDPOINT, endpoint, &size) == 0, "zmq_getsockopt");
        return endpoint;
    }
    void connect(const std::string& address)
    {
        require(zmq_connect(value, address.c_str()) == 0, "zmq_connect");
    }
};

static void exchange(Socket& server, Socket& client)
{
    const char message[] = "static-musl";
    char received[sizeof(message)]{};
    for (auto pair : {std::pair{&client, &server}, std::pair{&server, &client}}) {
        require(zmq_send(pair.first->value, message, sizeof(message), 0) == sizeof(message), "zmq_send");
        require(zmq_recv(pair.second->value, received, sizeof(received), 0) == sizeof(message), "zmq_recv");
        require(std::memcmp(message, received, sizeof(message)) == 0, "ZeroMQ message contents");
    }
}

static void databases()
{
    struct Record { int id; };
    using namespace boost::multi_index;
    multi_index_container<Record, indexed_by<hashed_unique<member<Record, int, &Record::id>>>> records;
    records.insert({42});
    require(!records.insert({42}).second && records.find(42) != records.end(), "Boost multi_index");
    sqlite3* database = nullptr;
    sqlite3_stmt* statement = nullptr;
    require(sqlite3_threadsafe() && sqlite3_open(":memory:", &database) == SQLITE_OK, "sqlite3_open");
    require(sqlite3_exec(database, "CREATE TABLE smoke(value); INSERT INTO smoke VALUES(42);", nullptr, nullptr, nullptr) == SQLITE_OK, "SQLite SQL");
    require(sqlite3_prepare_v2(database, "SELECT value FROM smoke", -1, &statement, nullptr) == SQLITE_OK, "sqlite3_prepare");
    require(sqlite3_step(statement) == SQLITE_ROW && sqlite3_column_int(statement, 0) == 42, "SQLite result");
    require(sqlite3_finalize(statement) == SQLITE_OK && sqlite3_close(database) == SQLITE_OK, "SQLite close");
}

static void sodium_roundtrip()
{
    std::array<unsigned char, crypto_secretbox_KEYBYTES> key;
    std::array<unsigned char, crypto_secretbox_NONCEBYTES> nonce;
    const unsigned char message[] = "authenticated static crypto";
    std::array<unsigned char, sizeof(message) + crypto_secretbox_MACBYTES> ciphertext;
    std::array<unsigned char, sizeof(message)> cleartext;
    crypto_secretbox_keygen(key.data());
    randombytes_buf(nonce.data(), nonce.size());
    require(crypto_secretbox_easy(ciphertext.data(), message, sizeof(message), nonce.data(), key.data()) == 0, "sodium encrypt");
    require(crypto_secretbox_open_easy(cleartext.data(), ciphertext.data(), ciphertext.size(), nonce.data(), key.data()) == 0, "sodium decrypt");
    require(std::memcmp(message, cleartext.data(), sizeof(message)) == 0, "sodium message contents");
    ciphertext[0] ^= 1;
    require(crypto_secretbox_open_easy(cleartext.data(), ciphertext.data(), ciphertext.size(), nonce.data(), key.data()) == -1, "sodium tamper rejection");
}

static void curve(Context& context)
{
    char server_public[41], server_secret[41], client_public[41], client_secret[41];
    require(zmq_curve_keypair(server_public, server_secret) == 0 && zmq_curve_keypair(client_public, client_secret) == 0, "CURVE keypairs");
    Socket server(context, ZMQ_REP), client(context, ZMQ_REQ);
    server.option(ZMQ_CURVE_SERVER, 1);
    server.option(ZMQ_CURVE_SECRETKEY, server_secret, 41);
    client.option(ZMQ_CURVE_SERVERKEY, server_public, 41);
    client.option(ZMQ_CURVE_PUBLICKEY, client_public, 41);
    client.option(ZMQ_CURVE_SECRETKEY, client_secret, 41);
    client.connect(server.bind("tcp://127.0.0.1:*"));
    exchange(server, client);
}

static void wss(Context& context, const Certificate& certificate, bool valid_hostname)
{
    Socket server(context, ZMQ_REP), client(context, ZMQ_REQ);
    server.option(ZMQ_WSS_KEY_PEM, certificate.key_pem.data, certificate.key_pem.size);
    server.option(ZMQ_WSS_CERT_PEM, certificate.cert_pem.data, certificate.cert_pem.size);
    client.option(ZMQ_WSS_TRUST_SYSTEM, 0);
    client.option(ZMQ_WSS_TRUST_PEM, certificate.cert_pem.data, certificate.cert_pem.size);
    client.option(ZMQ_WSS_HOSTNAME, std::string(valid_hostname ? "localhost" : "wrong.invalid"));
    client.connect(server.bind("wss://127.0.0.1:*"));
    if (valid_hostname) {
        exchange(server, client);
    } else {
        // Exercise certificate hostname verification, after the identical valid
        // certificate/transport setup succeeded. No untrusted data may arrive.
        server.option(ZMQ_RCVTIMEO, 1000);
        require(zmq_send(client.value, "untrusted", 9, 0) == 9, "queue untrusted test message");
        char data[16];
        require(zmq_recv(server.value, data, sizeof(data), 0) == -1 && zmq_errno() == EAGAIN, "WSS hostname rejection");
    }
}

int main()
{
    try {
        require(sodium_init() >= 0, "sodium_init");
        tls(gnutls_global_init());
        require(zmq_has("curve") && zmq_has("WSS") && zmq_has("draft"), "ZeroMQ secure features");
        databases();
        sodium_roundtrip();
        {
            Certificate certificate;
            Context context;
            curve(context);
            wss(context, certificate, true);
            wss(context, certificate, false);
        }
        gnutls_global_deinit();
        std::cout << "Boost, SQLite, libsodium, CURVE and verified WSS passed\n";
    } catch (const std::exception& error) {
        std::cerr << "Dependency smoke failed: " << error.what() << '\n';
        return 1;
    }
}
