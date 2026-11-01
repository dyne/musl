# Library patches

The ZeroMQ 4.3.5 patches are copied from Bitcoin Core 32.1, commit
`f0de87f040621468b956f01f526a43a010310501`, directory
[`depends/patches/zeromq`](https://github.com/bitcoin/bitcoin/tree/f0de87f040621468b956f01f526a43a010310501/depends/patches/zeromq).

- `cmake_minimum.patch`: declare CMake 3.16 before project(), supporting CMake 4.
- `cacheline_undefined.patch`: compare getconf's `undefined` result as a string,
  not a number (upstream zeromq/libzmq#4711).
- `add_new_include.patch`: explicit `<new>` includes for modern compilers,
  upstream patch commit `2e8a6ccb414ca79636392604893c79c3b0d00dc4`.
- `no_librt.patch`: clock_gettime is provided by musl; omit obsolete librt
  discovery and exported link requirements (upstream zeromq/libzmq#4702).

Patches apply without fuzz after verified extraction. Their contents participate
in the library configuration fingerprint, so edits force a fresh extraction.
When changing ZeroMQ versions, check each patch against the pristine release.

`static-crypto-dependencies.patch` is maintained by dyne/musl. It replaces
raw absolute GnuTLS/libsodium library paths with pkg-config imported targets,
resolves their static dependency closure, recreates those targets in the
installed ZeroMQConfig.cmake and records libsodium in Requires.private. Missing
requested crypto backends fail configuration instead of disabling encryption.
This is required for static linking and relocating the installed SDK.

The profile enables TCP/IPC/inproc, WebSockets, WSS via GnuTLS, CURVE via
libsodium and POSIX threads. WebSockets require ENABLE_DRAFTS=ON in 4.3.5;
applications opt into the exposed draft API. LibreSSL is not a supported ZeroMQ
backend. Absent NSS, libbsd, OpenPGM and NORM backends are explicitly disabled.
GnuTLS reuses existing zlib-ng through its own static dependency graph.

## HarfBuzz 15.0.0

`static-freetype-export.patch` replaces the absolute FreeType archive in the
CMake export with a pkg-config imported target carrying FreeType's static zlib
closure. `libs/cmake/harfbuzzConfig.cmake` recreates it and Threads in consumers,
then loads the upstream export as `harfbuzz-targets.cmake`. This keeps the
static SDK relocatable. Both the patch and package helper invalidate library
state. Recheck the export and installed consumer when upgrading HarfBuzz.
