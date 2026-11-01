# avena dependencies

[avena](https://github.com/LuganoPlanB/avena) combines a C++ web framework,
WebSockets and TLS. Its current root build needs the following SDK components:

| Requirement | Supplied by dyne/musl |
| --- | --- |
| C++17 compiler and standard library | GCC and libstdc++ |
| POSIX threads and dynamic-loader interface | musl (`pthread`, `dl`) |
| Atomic runtime | GCC's target libatomic |
| OpenSSL-compatible SSL/crypto headers and static archives | LibreSSL 4.4.0 (`libssl.a`, `libcrypto.a`) |

These dependencies are already bundled for each supported target. Core and
WebSocket code need no other external libraries. Avena's root build requires
OpenSSL API compatibility version 1.1 or later; LibreSSL provides that interface.
No additional source archive or separate OpenSSL installation is needed.

Host build tools are CMake 3.20 or later and Ninja or Make. Avena's test suites
also use the host `openssl` executable to generate temporary certificates.
When testing a foreign target, use a compatible target runner; the target
`bin/openssl` is not a substitute for the host executable.

## Build with the SDK

With the SDK installed under `/opt/dyne` and an avena checkout at `./avena`:

```sh
cmake -S avena -B build/avena -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=/opt/dyne/gcc-musl/settings.cmake \
  -DARCH=x86_64-linux-musl -DFORCE_STATIC=ON -DCCACHE=OFF \
  -DBUILD_TESTING=OFF -DAVENA_BUILD_TEST_SUPPORT=OFF \
  -DCMAKE_INSTALL_PREFIX="$PWD/install/avena"
cmake --build build/avena --parallel 2
cmake --install build/avena
```

Choose the matching `ARCH` for another installed SDK. To use this repository's
staged SDK, pass its absolute toolchain-file path and `-DROOT=/absolute/path/to/musl`.
Enable `CCACHE` when host ccache is available. Enable `BUILD_TESTING` and
`AVENA_BUILD_TEST_SUPPORT` and pass
`-DAVENA_OPENSSL_EXECUTABLE="$(command -v openssl)"` to build avena's suites.
This selects the host OpenSSL CLI: the target LibreSSL executable does not
support the DH fixture generator's `group:ffdhe2048` option. Then run
`ctest --test-dir build/avena --output-on-failure --parallel 1` on a compatible
host. Use a separate build directory when changing the SDK or target.

Avena is built separately from the SDK. Its static installation merges TLS
archives into one `libavena.a` and exports `avena::avena`; consumers do not need
separate TLS link flags. Configure an installed consumer with
`-Davena_DIR=/absolute/path/to/install/avena/lib/cmake/avena` alongside the same
SDK toolchain options. This explicit package directory also works with the
SDK's target-only CMake search rules.

`make smoke` checks CMake's static OpenSSL discovery, C++17 threads and atomics,
TLS context creation, and nonblocking TLS handshake/error handling without
network access. All targets receive static ELF checks; x86_64 runs the probe
on a compatible host. This dependency probe does not replace avena's own
HTTP, WebSocket and TLS integration suites.
