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
export CFLAGS="-I/opt/dyne/${ARCH}/include -Os ${CFLAGS}
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
option(FOR_MUSL_DYNE "Install target will copy everything inside /opt/musl-dyne" 0)
option(FORCE_STATIC "Force linker flags to build static executables (may fix or break some cases)" 0)
```

## Source components

All sources are mirrored on [files.dyne.org](https://files.dyne.org/musl/sources)

The latest build includes the following source components: `binutils-2.44.tar.gz`, `gcc-15.1.0.tar.xz`, `gmp-6.1.2.tar.bz2`, `linux-5.8.5.tar.xz`, `mpc-1.1.0.tar.gz`, `mpfr-4.0.2.tar.bz2`, and `musl-1.2.5.tar.gz`.

Additional base libraries and utilities provided are `libressl-4.1.0`, `zlib-ng-2.2.4`, `curl-8.15.0`, `libssh2-1.11.1`, and `ccache-4.11.3`.

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

The sequence of commands to build is:
1. `sudo make chroot`
2. `/alpine/enter-chroot make gcc`
3. `/alpine/enter-chroot make libs`

Assuming you are building in */home/user/devel/musl* then the built toolchain will be found at the same path inside the chroot, for example in /opt/alpine*/home/user/devel/musl/dyne*.

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

1. Check upstream updates https://github.com/richfelker/musl-cross-make and rebase if necessary
2. Update components in config.mak (defaults are in Makefile)
3. Run make to download sources/ from mirrors
4. Upload sources to files.dyne.org in musl/sources
5. Update `sources/download_from_dyne.sh` script
6. Prefix commit with semantic versioning (`fix:` or `feat:`)
