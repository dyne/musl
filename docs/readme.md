# 💪 GNU / musl compilers

## Introduction

This is a **fully static**, pre-built cross-compilation toolchain for x86_64 Linux hosts (any, including WSL2 and Alpine) that combines the GNU compiler collection (GCC with Binutils, GMP, MPC and MPFR) with the musl C library (pronounced "muscle").

Our C/C++ toolchain is optimized to be small in size, produce static binaries, and **support the latest C++20 standard** and be updated for future versions.

We enable bare-metal as well virtualized **builds of static binaries that run everywhere**, without installing additional system packages, chroots, docker images, qemu or dealing with distribution-specific patches.

## Usage

Download and install in one line of shell:
```
curl -L dl.dyne.org/musl | sudo tar -C /opt -xJf -
```

Or use the [dyne/musl-action](https://github.com/dyne/musl-action) in a github action:
```yaml
- uses: dyne/musl-action@main
  with:
    target_arch: 'x86_64' # or arm_64, arm_hf, riscv_64
```

The hard-coded absolute path this toolchain resides is: `/opt/dyne/gcc-musl`

One should therefore include `/opt/dyne/gcc-musl/bin` in $PATH:
```sh
export PATH=/opt/dyne/gcc-musl/bin:$PATH
```

Look inside the bin directory for the list of executable compiler tools and setup `CC`, `CXX`, `LD` and `AR` flags accordingly for each build system used by your projects. For example:
```sh
export ARCH="x86_64-linux-musl"
export CFLAGS="-I/opt/dyne/${ARCH}/include -Os ${CFLAGS}"
export CXXFLAGS="${CFLAGS}"
export LDFLAGS="-static -L/opt/dyne/${ARCH}/lib ${LDFLAGS}"
export CC="/opt/dyne/gcc-musl/bin/${ARCH}-gcc"
export CXX="/opt/dyne/gcc-musl/bin/${ARCH}-g++"
export AR="/opt/dyne/gcc-musl/bin/${ARCH}-ar"
export AS="/opt/dyne/gcc-musl/bin/${ARCH}-as"
export PKG_CONFIG_PATH="/opt/dyne/${ARCH}/lib/pkgconfig"
```

We also ship base libraries commonly used in C/C++ applications: **libreSSL, ZLib-ng, libSSH2 and libCURL**, as well ccache to speed compilation. There are found in `/opt/dyne/$ARCH` where `$ARCH` (default x86_64) is the target architecture that must be installed. Multiple target architectures can be installed and coexist in `/opt/dyne`.

### Easy use in CMake

If you are using `cmake` for your builds then use our toolchain file:
```sh
-DCMAKE_TOOLCHAIN_FILE="/opt/dyne/gcc-musl/settings.cmake"
```
Make sure to config `-DARCH=""` to your target architecture, here a list of all configurable options and their defaults:
```cmake
# Configurable settings
set(ARCH "x86_64-linux-musl" CACHE STRING "Target architecture to (cross)compile")
set(CMAKE_CXX_FLAGS "-static --static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow" CACHE STRING "C++ Compilation flags, default set for small and secure binaries")
set(CMAKE_C_FLAGS "-static --static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow" CACHE STRING "C Compilation flags, default set for small and secure binaries")
set(ROOT "/opt" CACHE STRING "Base root prefix for installation (often referred as PREFIX or DESTDIR)")
option(CCACHE "Use ccache to speed up compilation" 1)
option(FOR_MUSL_DYNE "Install into /opt/dyne/<target tuple>" 0)
option(FORCE_STATIC "Force linker flags to build static executables (may fix or break some cases)" 0)
```

## Source components

Exact release URLs are recorded in [sources.urls](https://github.com/dyne/musl/blob/master/sources.urls).
All build inputs download directly from their upstream projects: official
release archives for packages and a pinned GNU repository revision for config.sub.
Builds do not use Dyne's source cache or fall back to a source mirror.

The source configuration includes `binutils-2.47.tar.xz`, `gcc-16.2.0.tar.xz`, `gmp-6.3.0.tar.xz`, `linux-7.3.1.tar.xz` (userspace headers), `mpc-1.4.1.tar.xz`, `mpfr-4.2.2.tar.xz`, and `musl-1.2.6.tar.gz`.

Additional base libraries and utilities are `libressl-4.4.0`, `zlib-ng-2.3.3`, `curl-8.23.0`, `libssh2-1.11.1`, `ccache-4.14.2`, `ncurses-6.6` (wide-character static library), and `kyotocabinet-1.2.80`.

The SDK also includes Boost **1.92.0** headers, SQLite **3.54.1**, ZeroMQ
**4.3.5**, libsodium **1.0.22**, GnuTLS **3.8.13**, target GMP **6.3.0** and
Nettle/hogweed **3.10.2**. ZeroMQ includes CURVE encryption and secure WebSockets
through libsodium and GnuTLS; WebSockets use ZeroMQ's draft API. See
[Bitcoin Core and secure ZeroMQ](bitcoin.md) for configuration, limitations and
package-update instructions.

The SDK supplies [avena's dependencies](avena.md): C++17, threads, libatomic
and the OpenSSL-compatible static SSL/crypto libraries from LibreSSL. Avena's
core and WebSocket modules need no additional third-party packages.

[Headless SDL3 graphics](sdl3.md) includes SDL **3.4.18**, SDL_image **3.4.8**,
SDL_ttf **3.2.2**, FreeType **2.15.0** and HarfBuzz **15.0.0** for offscreen
software rendering, image loading and international text. Desktop windows,
GPU rendering and hardware audio backends are outside this profile.
[Dear ImGui 1.93.0](imgui.md) adds widgets and font-atlas rendering through
SDL3's software renderer, with no additional external libraries.

Versions were checked against upstream releases on 2026-11-01, with Nettle 3
pinned for GnuTLS API compatibility. Published
archives may lag the source configuration until release validation completes.

Downloads, including cached archives, are checked against the pinned
`sources.sha256` manifest. See [maintenance](maintenance.md) for package updates,
build validation, and release recovery.

Build flags used: `--disable-nls --disable-libmudflap --disable-libsanitizer --disable-lto`. Features enabled: decimal-float, fixed-point, quadmath, as well libitm to satisfy advanced C++ requirements. Debugging functions are omitted.

Builds are fully automated over CI and use semantic versioning that is
specific to dyne/musl and unrelated to gcc or musl release versions.

## Supported target architectures

We provide cross-compilers running on x86_64 and capable to target the
following architectures:

| name in docs  | file suffix | unix architecture name |
|---------------|-------------|------------------------|
| X86 64‑bit    | x86_64      | `x86_64-linux-musl`    |
| ARM 64‑bit    | arm_64      | `aarch64-linux-musl`   |
| ARM HF 32-bit | arm_hf      | `arm-linux-musleabihf` |
| RISC-V 64-bit | riscv_64    | `riscv64-linux-musl`   |

More architecture targets are available, [get in touch with us](mailto:info@dyne.org) if you need.

## Patches included

In addition to canonical musl support patches for GCC,
musl-cross-make's patch set provides:

- Static-linked PIE support
- Addition of `--enable-default-pie`
- Fixes for SH-specific bugs and bitrot in GCC
- Support for J2 Core CPU target in GCC & binutils
- SH/FDPIC ABI support

## Build it yourself

In order to build a static toolchain, we use Alpine in a chroot with bind-mount of current dir and therefore require super-user privileges.

From the repository directory:

```sh
export ARCH=x86_64-linux-musl  # or another target tuple listed above
sudo make chroot
/alpine/enter-chroot make prepare
/alpine/enter-chroot make smoke
/alpine/destroy --remove
```

`make prepare` builds the compiler and all libraries in dependency order before
stripping and packaging preparation. Outputs are visible on the host in
`./dyne/` through the bind mount. `make gcc` and `make libs` remain available for
individual stages; `make libs` first ensures the compiler is current. The build
uses the Alpine `v3.24` branch and the `static-small` configuration by default.
Select a different compiler configuration with `BUILD_FLAVOR=shared-optim`.
The Alpine branch is pinned, but package revisions within that branch can change.

Library work directories are separate for each target under `build/libs/`.
Changes to flags, recipes, versions, or the compiler invalidate library state
and replace that target's staged library prefix. Use dedicated installation
directories when overriding `PREFIX`. `make clean` removes staged outputs and
build state, keeping verified download caches. ncurses terminfo data is supplied
by the runtime system, not bundled in these library packages.

## License

All GNU software is licensed under the GNU GPL license.

We are very grateful to the
[musl-cross-make](https://github.com/richfelker/musl-cross-make)
project for its excellent work we build upon, its build tools and
documentation are licensed under the MIT/Expat license.

Each patch is distributed under the terms of the license of the
upstream project to which it is applied.

Resulting binary artifacts produced by our build retain the original
licensing from the upstream projects. The authors of musl-cross-make
or the Dyne.org foundation do not make any additional copyright claims
to these artifacts.

### Update

Unless you explicitly state otherwise, any contribution submitted for
inclusion shall be licensed as above without any additional terms or
conditions.

When updating to make a new release:

1. Review upstream [musl-cross-make](https://github.com/richfelker/musl-cross-make)
   changes and port relevant build and version-specific patch updates.
2. Update compiler versions in `gcc-musl/Makefile` and both Dyne configurations,
   or library versions in `libs/GNUmakefile`. Add the required source hash entries
   and verified URL/SHA-256 entries to `sources.urls` and `sources.sha256`.
3. Check version-specific patches for upstream integration and refresh remaining
   hunks. Ensure each selected input has its exact upstream URL recorded.
4. Run `make test` and clean builds/smoke checks for all four targets; update docs.
5. Use a conventional commit (`fix:`, `feat:`, or a documented breaking change).
   CI validates every target on pull requests and master pushes. On a releasing
   master push, semantic-release creates `vX.Y.Z` only after validation succeeds.

Failed publication preserves its tag and any draft assets. The
[maintenance guide](maintenance.md) explains how to retry the exact validated
commit without deleting tags or creating a new version.
