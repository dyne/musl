# Local validation — 2026-10-31

These results apply to the build/release reliability changes on top of
`5840222`. No tag, release, mirror upload, or host installation was performed.
Generated inputs, build trees, logs and packages remain under the ignored
`.cache/` and `build/` directories.

| Check | Result |
| --- | --- |
| `make test` | 28 passed, no skips |
| `shellcheck prepare.sh scripts/*.sh` | Passed |
| actionlint 1.7.7 on `.github/workflows/main.yml` | Passed |
| `git diff --check` | Passed |
| VitePress `npm run build` | Passed |
| Fresh static-small x86_64 GCC/musl source build and installation | Passed on this Linux host |
| Newly built compiler compiling/running C and C++20 smoke tests | Passed |
| Clean library builds for x86_64, ARM HF, ARM64 and RISC-V | All four passed |
| C/C++20/thread/atomic/Kyoto link and ELF checks | All four passed |
| Native x86_64 application and packaged ccache execution | Passed before and after preparation |
| Target-aware preparation and archive layout checks | All four passed |
| SHA256SUMS with exactly four local archives | All four checksums passed |

The fresh bootstrap used an isolated copy of the compiler builder, the default
static-small configuration and verified source archives. It resumed from normal
stamps after fixing ARCH propagation; no downloaded compiler was substituted.
The final command was:

```sh
make -C .cache/compiler-check/gcc-musl -j8 install \
  ARCH=x86_64-linux-musl SOURCES="$PWD/.cache/sources"
```

The four clean library builds used checksum-verified published 2.2.0 compiler
packages, the final recipes and fresh dedicated prefixes:

```sh
make -C libs ARCH="$tuple" JOBS=3 \
  TOOLCHAIN="$PWD/.cache/toolchains/dyne/gcc-musl" \
  PREFIX="$PWD/.cache/install/$tuple"
TOOLCHAIN="$PWD/.cache/toolchains/dyne/gcc-musl" \
TARGET_PREFIX="$PWD/.cache/install/$tuple" make smoke ARCH="$tuple"
```

Each package was prepared in a separate staging tree. The x86_64 package used
the fresh compiler; foreign packages used their verified published compilers
and freshly built libraries. Smoke tests ran against the stripped files before
compression, then `scripts/check-archive.py` checked the archives. Local
compression used `XZ_OPT='-1 -T2'`, rather than CI's stronger compression;
content checks are independent of compression level.

Evidence is in `.cache/regression.log`, `.cache/actionlint.log`,
`.cache/compiler-install.log`, `.cache/new-compiler-smoke.log`,
`.cache/final-validation-status.log`, `.cache/final-validated-<tuple>.log`,
`.cache/package-validation-status.log`, `.cache/package-<tuple>.log`, and
`.cache/docs-build.log`. Local archives and their checksum manifest are under
`.cache/package/`.

The fresh compiler bootstrap used static glibc host tools; its target runtime
is musl. The production Ubuntu/Alpine v3.24 workflow has not run here: creating
its privileged `/alpine` chroot is outside this workspace's permissions. Fresh
foreign GCC bootstraps remain for that workflow; local foreign library tests
used released GCC 15.1.0 compilers. Foreign applications were linked/inspected,
but not executed on hardware or an emulator.

Expired logs leave the historical CI failure's cause unproven. Two additional
defects found here have direct reproductions and regression coverage: a target
tuple overriding musl's own ARCH, and host binutils beneath the target sysroot
being sent to a foreign strip executable.
