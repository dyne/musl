# Working on dyne/musl

## Identity and startup

This is **dyne/musl**, a GCC/musl cross-toolchain and bundled-library project,
not the upstream musl libc source repository or an Alpine package repository.
musl supplies the C/POSIX runtime on Linux; GCC, binutils, libgcc and libstdc++
compile and link C/C++ applications against it. Static applications avoid a
dependency on the destination distribution's shared libc. Architecture, ABI,
CPU features, kernel interfaces and runtime data still matter.

The Git root is this directory; its parent is a workspace with a pointer here.
Start with `git status --short`, `git log -5 --oneline` and `git remote -v`.
The origin is `git@github.com:dyne/musl`. Treat the current files as authoritative
when they differ from historical notes or external musl-cross-make documentation.

Historical research baseline (2026-10-31): master was at `5840222`; the latest
published binaries were [2.2.0](https://github.com/dyne/musl/releases/tag/2.2.0)
from `5a5f419`. Both bare and v-prefixed tags existed. HEAD's
[release run](https://github.com/dyne/musl/actions/runs/25759592719) failed during
library builds, but detailed logs expired (HTTP 410). The original Kyoto Cabinet
recipe subsequently compiled for all four targets with the published compilers;
that does not establish the historical failure's cause. Recheck remote state
before making claims about what is currently published.

## Source map

| Path | Purpose |
| --- | --- |
| `GNUmakefile` | Build ordering, Alpine setup, compiler state, libraries, preparation, smoke/tests/clean |
| `gcc-musl/Makefile` | Source verification, extraction/patching, litecross orchestration |
| `gcc-musl/litecross/Makefile` | Binutils, GCC, musl bootstrap and userspace kernel headers |
| `gcc-musl/config.static-small.mak` | Default static host tools, size optimization |
| `gcc-musl/config.shared-optim.mak` | Alternate dynamically linked, host-native optimization |
| `gcc-musl/config.mak.dist`, `presets/` | Upstream examples; presets are inside gcc-musl |
| `gcc-musl/hashes/`, `gcc-musl/patches/` | Supported archive names and version-specific patches |
| `gcc-musl/sources/GNUmakefile` | Delegates fetching to the selected compiler configuration |
| `sources.urls`, `sources.sha256`, `scripts/download.sh` | Exact upstream URLs and integrity checks for new and cached inputs |
| `scripts/toolchain-state.sh` | Invalidates selected compiler build/install state when inputs change |
| `scripts/compiler-cache.sh`, `scripts/check-ccache.sh` | GCC/frontend cache identity and real bootstrap C/C++ hit probes |
| `libs/GNUmakefile` | Library versions, dependency graph, per-target sources and installation |
| `settings.cmake` | Consumer/internal cross-compilation settings |
| `prepare.sh`, `scripts/smoke.sh`, `tests/` | Package preparation, real C/C++ checks, offline regression suite |
| `.github/workflows/main.yml`, `.releaserc` | Validation before tagging; publication and retry |
| `docs/maintenance.md` | Detailed package-update, validation and recovery runbook |
| `docs/`, `.github/workflows/website.yml` | VitePress site and independent Pages deployment |

`README.md` is a symlink to `docs/readme.md`; edit its destination and preserve
the link. Preserve Make recipe tabs. This is a Make/shell/CMake build repository,
with no root npm application or CMake project. Never commit caches, extracted
sources or staged toolchains. They are ignored; inspect Git status and stage
deliberately.

## Host, targets and layout

Every shipped compiler runs on **x86_64 Linux**. Its target is one of:

| ARCH / GCC TARGET | Release suffix |
| --- | --- |
| `x86_64-linux-musl` (default) | `x86_64` |
| `arm-linux-musleabihf` | `arm_hf` |
| `riscv64-linux-musl` | `riscv_64` |
| `aarch64-linux-musl` | `arm_64` |

Staging is `dyne/gcc-musl/` for compiler tools and their internal
`<tuple>/` libc sysroot, and `dyne/<tuple>/` for extra libraries, headers,
pkg-config files and target utilities. Archives contain `dyne/` and are intended
for extraction under `/opt`. Multiple target directories can coexist.
The default host compiler flags require x86-64-v2, so the tools do not promise
support for every old x86_64 CPU. The alternate shared-optim flavor uses
`-march=native` and has stronger host/environment dependencies.

## Build mechanics and commands

The wrapper selects a configuration and checks compiler state. musl-cross-make
verifies sources, makes pristine `*.orig` trees and patched trees using
`cowpatch.sh`, then creates `gcc-musl/build/local/<tuple>/`. Litecross builds
binutils and the GCC compiler first. Its in-tree xgcc configures musl; musl
headers permit building libgcc, then libc is staged, then GCC's remaining target
libraries are built. Linux's headers_install supplies API headers, not a kernel.
The intermediate stages use `.lc_*` stamps.

From the Git root, on a host allowing privileged chroots:

```sh
export ARCH=x86_64-linux-musl
sudo make chroot
/alpine/enter-chroot make prepare
/alpine/enter-chroot make smoke
/alpine/destroy --remove
```

`prepare` depends on `libs`, which depends on `gcc`; root stages always enter
their sub-builds rather than skipping all libraries when SSL already exists.
`BUILD_FLAVOR=static-small` is the default. Pass other make options explicitly
through enter-chroot, e.g. `make prepare BUILD_FLAVOR=shared-optim`.
The legacy root MUSL_CONFIG flavor alias is accepted but cleared before entering
musl-cross-make, where MUSL_CONFIG means musl configure arguments.

Alpine is pinned to branch `v3.24` on x86_64, with required tools explicitly
installed. The bind mount exposes `./dyne` at the same working-directory path
inside and outside the chroot. The generated entry script preserves ARCH, CI and CCACHE_*
and handles sudo. Host mount privileges are required for `/alpine`; a restricted
workspace alone cannot reproduce this environment.

Library sources/build directories are under `build/libs/<tuple>/<package>/`.
Their configuration fingerprint includes recipes, flags, package versions,
toolchain identity and checksums. Changes recreate the dedicated target library
prefix to remove obsolete files. Do not point PREFIX at a shared installation
directory. `make clean` removes staged outputs and build state; verified download
caches remain. The compiler's distclean preserves the tracked sources GNUmakefile.

For isolated library work with an existing compiler, use the explicit
TOOLCHAIN/PREFIX commands in [maintenance](docs/maintenance.md). This does not
validate a fresh compiler bootstrap. Avoid concurrent independent compiler
builds in the same checkout; they share the selected config symlink and sources.

## Pinned inputs and updates

Current default compiler inputs: GCC **16.2.0**, binutils **2.47**, musl **1.2.6**,
Linux headers **7.3.1**, GMP **6.3.0**, MPC **1.4.1**, MPFR **4.2.2** and
config.sub revision **3d5db9ebe860**. Check both configuration variants and base
Makefile when updating; ISL is unselected. C/C++ are enabled. The default host
tools use static linking, -Os and x86-64-v2; NLS, sanitizer, mudflap and LTO are
disabled. Host ccache is used when available, including musl's in-tree xgcc and
GCC target runtimes through STAGE_CC_WRAPPER. The frontend-content namespace
helper also wraps library configure/build/install commands; do not replace
generated target compiler flags or add unsafe ccache timestamp sloppiness.
Both flavors build musl's static archive with `-fPIC` for static-PIE linkage;
PIE applications must compile their own objects with `-fPIE` too.

Bundled versions in `libs/GNUmakefile`: LibreSSL **4.4.0**, zlib-ng **2.3.3**,
curl **8.23.0**, libssh2 **1.11.1**, ccache **4.14.2**, ncurses **6.6**, Kyoto
Cabinet **1.2.80**. LibreSSL provides OpenSSL-compatible crypto; zlib-ng uses
zlib compatibility mode. curl explicitly depends on SSL, zlib and SSH2.
ncurses builds its wide-character static library without host-tic-dependent
database installation; runtime terminfo comes from the target system.
Kyoto disables zlib and respects selected compile flags instead of upstream's
automatic -march=native/-O2 additions. Packaged ccache targets ARCH and is not a
substitute for the x86_64 host ccache during cross-compilation.

Versions were checked against upstream stable releases on 2026-10-31; recheck
on every update. Linux supplies userspace headers, not a shipped kernel.
For upgrades, compare upstream richfelker/musl-cross-make with `gcc-musl/`,
preserving Dyne's wrapper. Update configuration/default pins, supported archive
catalog entries in hashes, URL/SHA-256 pins, and version-specific patches.
Musl 1.2.6 integrates the old CVE-2025-26519 patches and carries the three newer
upstream fixes for CVE-2026-107891, CVE-2026-40200 and CVE-2026-6042.
Read `gcc-musl/patches/README.md` for the patch-port record, and update docs.
There is no download_from_dyne.sh and no second explicit source manifest.

Every selected input comes directly from its upstream project using exact URLs
in `sources.urls`: official release archives for packages and GNU's repository
at revision `3d5db9ebe860` for config.sub. The old `SOURCES_URL` source-mirror
override has been removed and is ignored. No build input depends on Dyne's
source cache. There is no automatic version selection or mirror fallback.
Local verified download caches remain available for repeat and offline builds.
All selected compiler inputs and library caches are SHA-256 checked on builds.
New downloads fail on HTTP errors and publish only after verification. Corrupt
existing inputs fail closed; remove the identified entry before retrying.
An external SOURCES path must already contain all inputs and is treated as
immutable. See maintenance for digest provenance and config.sub revision keys.
config.sub uses `git+https://REPOSITORY.git#FULL_40_HEX_COMMIT:relative/path` in
the URL manifest. Its exact Git blob is fetched with bounded retries/timeouts
and checked against the unchanged SHA-256. Git and timeout are needed on a fresh
download; cgit's HTTP frontend returned intermittent 404s even at the full pin.

CI's compressed 2 GiB ccache snapshots are keyed by target, Alpine branch and
build flavor, with a stable v2 prefix and no commit/PR identifier. PRs can restore
master caches; GitHub isolates PR-written caches to that PR, so they cannot warm
master or other PRs. Master release builds restore master caches. Snapshots are
not merged across jobs. No external remote cache service is configured.
`CCACHE_DIR` is the same workspace `.cache/ccache` path inside/outside Alpine;
CCACHE_* is explicitly whitelisted and compiler_check is content. CI verifies
the chroot settings, requires real C/C++ hits from scripts/check-ccache.sh, saves
stats, then repairs runner ownership before cache upload. The first v2 build is
cold. See maintenance for local commands and cache limitations.

## CMake and package checks

Use `-DCMAKE_TOOLCHAIN_FILE=/opt/dyne/gcc-musl/settings.cmake -DARCH=<tuple>`.
ROOT changes the base path; TOOLCHAIN_PREFIX and TARGET_PREFIX can override the
compiler and additional-library locations separately. CMake uses the compiler's
libc sysroot and restricts library/header/package lookup to target roots; build
programs remain host tools. FOR_MUSL_DYNE installs into TARGET_PREFIX.
CCACHE defaults ON for consumers: provide host ccache or use `-DCCACHE=OFF`.
FORCE_STATIC adds static runtime linker flags.

Preparation uses Bash, validates ARCH and uses target strip for target files
and host strip for compiler executables. It removes DSOs/libtool metadata for
the selected target while leaving other target sysroots alone, retains license
directories, and copies README.txt/settings.cmake.

Run `make test` (Python 3 + PyYAML, Make >=4.3, curl, Git, CMake, cc/c++ and file) and
`shellcheck prepare.sh scripts/*.sh` for changed automation. The offline suite
checks cache failure paths, real Make rebuild/order behavior, cleanup, CMake,
preparation, checksums and tag identity. Install host ccache for the actual
cache-hit regression (required in CI); CCACHE_TEST_BINARY can select an existing
host binary. Tests also check pinned Git blobs, retries/cleanup and chroot cache
environment forwarding. For changed recipes, also run actual
clean target builds. `make smoke` links C against all bundled C libraries and
C++20/thread/atomic/Kyoto code, checks ELF architecture/static dependencies, and
runs x86_64 binaries on compatible hosts. It also checks the ported static-PIE
link specs and libc sorting/GB18030/regex functionality. Foreign runtime behavior needs hardware
or emulation. Never infer full build success from lint or cross-linking alone.
The [validation report](docs/validation.md) records the initial 28-test result,
fresh native bootstrap, four target library/package checks, and remaining
production-Alpine/foreign-runtime validation limits.

## Release and website

CI validates on PRs, master pushes and manual dispatch. All four target builds
and smoke checks must pass before a releasing master push invokes semantic-release.
Canonical tags are **vX.Y.Z**, using new_release_git_tag consistently.
Conventional fix/feat/breaking commits drive patch/minor/major versions,
independently of GCC/musl versions. Archive completeness and the four-entry
SHA256SUMS manifest are checked before tagging; the manifest does not hash itself.

Publication stages a GitHub draft with assets, uploads the established filenames
to /srv/ftp/musl, then publishes GitHub. Tags are preserved on failure.
A manual dispatch with release_tag retries only a tag pointing to that exact
checked-out commit; it refuses to replace an already-public release's assets.
Use the retained tag as --ref when master has advanced.
Without release_tag, dispatch validates only. See maintenance before recovery;
legacy bare tags are historical state, not the new naming convention.

The mirror upload is not transactional across files; partial state requires a
retry and checksum validation. Build logs/configure logs are retained 90 days.
Only the release job has contents-write permission and mirror secrets.
Alpine package revisions and action major tags can still change, so branch/
runner pins are not proof of bit-for-bit reproducibility.

Website work uses `cd docs && npm ci && npm run build` (Node 22 in CI).
VitePress uses base /musl/ and deploys docs/.vitepress/dist to GitHub Pages on
master. The independent website workflow watches docs/**. Update its lockfile
when changing dependencies.

musl-cross-make tooling is MIT/Expat (`gcc-musl/LICENSE`, `COPYRIGHT`); patches
and binaries retain their respective upstream licenses, including GNU components.
Preserve notices and source availability when distributing packages.

Primary references: [musl](https://wiki.musl-libc.org/getting-started.html),
[musl-cross-make](https://github.com/richfelker/musl-cross-make),
[semantic-release configuration](https://github.com/semantic-release/docs/blob/main/src/content/docs/usage/configuration.md),
[action v6](https://github.com/cycjimmy/semantic-release-action/blob/v6/README.md).
