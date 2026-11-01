# Bitcoin Core and secure ZeroMQ

The SDK includes Boost 1.92.0 headers, SQLite 3.54.1 and ZeroMQ 4.3.5. These
cover the external target libraries for a headless Bitcoin Core 32.1 build
with SQLite wallets and optional ZeroMQ notifications, with IPC disabled.
Bitcoin Core bundles its other runtime libraries, including secp256k1,
LevelDB, CRC32C, minisketch and UniValue. It does not require an external
OpenSSL, Berkeley DB or libevent for this configuration.

All Boost headers are installed. Upstream CMake metadata is provided for the
`multi_index`/header-only `test` dependency closure used by Bitcoin Core,
including `Boost::headers`. Compiled Boost libraries are not included; copying
all headers does not make compiled components such as Boost.Filesystem usable.
SQLite keeps thread safety and automatic initialization, disables dynamic
extension loading, and ships its public-domain notice in `sqlite3.h`.

## Building Bitcoin Core

Install the chosen SDK under `/opt` and use a host CMake >= 3.22, Ninja/Make and
pkg-config. With a verified Bitcoin Core 32.1 source tree:

```sh
cmake -S /path/to/bitcoin -B build-bitcoin -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=/opt/dyne/gcc-musl/settings.cmake \
  -DARCH=x86_64-linux-musl -DCCACHE=OFF -DWITH_CCACHE=OFF -DFORCE_STATIC=ON \
  -DBUILD_GUI=OFF -DENABLE_IPC=OFF -DENABLE_WALLET=ON -DWITH_ZMQ=ON \
  -DBUILD_TESTS=OFF -DBUILD_BENCH=OFF -DBUILD_FUZZ_BINARY=OFF
cmake --build build-bitcoin --target bitcoind bitcoin-cli --parallel 4
```

Use another supported `ARCH` for cross-compilation; the tools run on x86_64
Linux. `ENABLE_IPC=OFF` avoids adding Cap'n Proto/libmultiprocess dependencies.
This produces the daemon and command-line RPC client; Qt and the GUI are absent.
Runtime data such as certificates and DNS configuration still comes from the
application or target system. Consult the selected Bitcoin release's build
documentation when changing versions or enabling other options.

## Encryption features

ZeroMQ's `tcp://`, `ipc://` and `inproc://` transports remain available. The SDK
also enables WebSockets (`ws://`), TLS WebSockets (`wss://`) and CURVE:

| Feature | Backend | Application responsibility |
| --- | --- | --- |
| `wss://` | GnuTLS 3.8.13 | Supply the server certificate/key and trusted client CA, and verify the expected hostname |
| CURVE | libsodium 1.0.22 | Manage client/server keypairs and authorize client public keys, normally through ZAP |

CURVE encrypts and authenticates ZeroMQ's own protocol. It is separate from TLS
and does not use X.509 certificates. Enabling CURVE support does not turn it on
for every socket or define an application's access policy. Bitcoin's usual
ZeroMQ publisher configuration does not automatically configure CURVE or WSS.
This change adds SDK capabilities, not a new Bitcoin RPC/notification transport.

ZeroMQ 4.3.5 requires `ENABLE_DRAFTS=ON` for WebSockets. Draft APIs can change
upstream. The installed CMake target and pkg-config flags expose
`ZMQ_BUILD_DRAFT_API`; direct users must define it before including `zmq.h` to
access `ZMQ_WSS_*` options. `zmq_has("WSS")` and `zmq_has("curve")` both return 1.
This is ZeroMQ messaging over WebSockets, not a generic browser WebSocket API.

GnuTLS uses target GMP 6.3.0, Nettle/hogweed 3.10.2 and existing zlib-ng, with
bundled libtasn1 and libunistring. Nettle 3.10.2 is deliberately pinned to the
supported Nettle 3 API required by this GnuTLS release; Nettle 4 changes that API.
GnuTLS tools, C++ wrapper, DANE, PKCS#11, TPM, IDN, Brotli and Zstd support are
disabled. LibreSSL remains the backend for curl/libssh2. ZeroMQ 4.3.5 cannot use
LibreSSL for WSS or CURVE. The absent NSS, libbsd, OpenPGM and NORM dependencies
are disabled rather than accidentally discovered on the host.

No CA bundle is shipped. GnuTLS's default trust file is
`/etc/ssl/certs/ca-certificates.crt` on the target system. Applications can supply
an explicit trust bundle; do not disable certificate or hostname verification.

## Static linking and package updates

`find_package(ZeroMQ CONFIG REQUIRED)` supplies `libzmq-static`. Its exported
CMake configuration resolves complete static GnuTLS/libsodium dependencies
through target pkg-config metadata. The toolchain clears host `PKG_CONFIG_PATH`
and restricts `PKG_CONFIG_LIBDIR` to the selected target prefix. Plain consumers
can use `pkg-config --static --cflags --libs libzmq` with that same target-only
database. New package `.pc` files and CMake exports work after relocating the SDK.

Update the version variables in `libs/GNUmakefile` and the matching exact URL
and SHA-256 entries in `sources.urls`/`sources.sha256`. GMP shares its archive pin
with the compiler but has a separate target build; update both uses together.
Boost uses the official `-cmake.tar.xz` release asset, with the local manifest
key `boost-VERSION.tar.xz`. SQLite's numeric archive key and year both change
independently of the dotted version. libsodium uses a fixed point-release asset,
not the moving `stable` tarball. For GnuTLS, recheck its required Nettle API,
bundled libtasn1/libunistring versions and enabled compression dependencies.

Check every ZeroMQ patch against the new pristine release and remove integrated
patches. Patch contents are part of the build fingerprint. See
[`libs/patches/README.md`](https://github.com/dyne/musl/blob/master/libs/patches/README.md)
for provenance and the static dependency export fix. Preserve upstream license
files and review static-link distribution obligations for the resulting program.

Run `make test`, ShellCheck, clean package builds and `make smoke` for all four
architectures before releasing. The dependency smoke executable finds the
installed packages, exercises Boost/SQLite and libsodium authenticated encryption
(including tamper rejection), exchanges CURVE messages over loopback TCP, and
exchanges WSS messages with a freshly generated localhost certificate. It also
checks that a wrong hostname cannot deliver application data. Only the native
x86_64 job executes these checks; foreign jobs compile/link and inspect the ELF.
When changing these packages, also configure and build the selected Bitcoin Core
release, then test its CLI and SQLite wallet on isolated offline regtest data.
