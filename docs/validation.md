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

## Readline addition (2026-11-07)

GNU Readline 8.3, with unchanged official patches 001–006, was built from the
SHA-256-pinned GNU archive. Its detached signature verified against the key
published by the maintainer; see `libs/patches/README.md` for provenance.
The static ncurses dependency also builds with `-fPIC` so that line editing
can be linked into static PIE executables.

| Check | Result |
| --- | --- |
| `make test` | 53 passed, no skips |
| ShellCheck, Bash syntax, `git diff --check` | Passed |
| VitePress `npm run build` | Passed |
| Clean ncurses/Readline builds for all four target tuples | Passed with GCC 16.2.0 |
| Repeated unchanged library builds | No archive rebuilds |
| Installed files | Both archives, all eight public headers, both `.pc` files and GPL notice present; no shared objects |
| Relocated pkg-config static-PIE and direct static consumers | All four targets linked with correct ELF machine and no INTERP/NEEDED |
| Native Readline and standalone History consumers | Executed successfully before and after relocation |
| Full native SDK smoke with new ncurses/Readline overlaid onto v2.5.1 | Passed |

A headless Bitcoin Core build was stopped at the user's request; it is no
longer required by musl CI or the test suite. Focused installed-package
consumers and relocation checks remain required.

The native library build used this checkout's staged compiler. Foreign builds
used checksum-verified v2.5.1 compilers. Each build used an isolated
`BUILD_ROOT=build/readline-libs`, target-specific `PREFIX` and the actual
`libs/GNUmakefile` rules, selecting just `ncurses-6.6.tar.gz readline-8.3.tar.gz`
through `ARCHIVES` for the focused build. Relocation removed the original
library prefix before configuring the consumers in `tests/readline/`.
History was independently linked without Readline or ncurses. Foreign binaries
were inspected but not executed. This does not validate a fresh compiler
bootstrap or the privileged production Alpine build.

The companion installer at revision
`244f10edd4456601a110815c7fa42b9f4c0ce761` passed
`python3 tests/live.py --versions v2.5.1 --work ../musl/.cache/readline-action`
for all four published targets, including cold extraction, warm archive reuse,
relocation and C/C++ consumers. `CCACHE_DIR` was set inside the workspace for
these checks. The checked archive SHA-256 values were:

| Release suffix | v2.5.1 SHA-256 |
| --- | --- |
| x86_64 | `02556d8cabc4686676c19cdc718262f14ab98d3dc109469fab99ae63caf75c13` |
| arm_64 | `144327df1488d90ce9271acd157bb6a71b2f28162b12c9597c0b685441289399` |
| arm_hf | `078aaffd45cf13abef0e5642787e64d11399289eee1e81468be942a83ffd538b` |
| riscv_64 | `29b50f269d02e20ee84eb8985a185c34abd5a4b153798885990396d042317541` |

No companion action change or release was needed for this additive library
package. Those installer results cover the existing published release; the
next release containing Readline still requires the configured post-publication
GitHub action-consumer workflow against its exact assets. No release was
published during this change.

Build, consumer, relocation, offline-test and action evidence is retained under
`build/readline-validation/`; source caches and isolated installations are in
`.cache/readline-*`.
