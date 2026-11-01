# Build and release maintenance

The [local validation report](validation.md) records the initial checks and
their limits.

## Validation

The offline regression suite needs Python 3, PyYAML, GNU Make 4.3 or newer,
curl, Git, CMake, host C/C++ compilers, file, and standard GNU utilities.
Install host ccache to exercise the real cache-hit regression (CI requires it);
`CCACHE_TEST_BINARY=/absolute/path/to/ccache make test` can select another binary:

```sh
make test
shellcheck prepare.sh scripts/*.sh
```

It exercises download success and failure, corrupted caches, atomic download
publication, dependency ordering, missing archives, flag invalidation, target
isolation, cleanup, CMake options, preparation, tag identity, and checksums.
GitHub's `checks` job runs these checks before starting compiler builds.

The `gcc-musl-build` job runs for pull requests, master pushes, and manual
dispatches. Every matrix target gets a clean compiler/library build, preparation,
and `make smoke` before its archive is uploaded. A failure does not cancel other
targets, so their results remain available. Build output and configure logs are
retained as artifacts for 90 days, including failed builds.

## Compiler caching

CI keeps a separate compressed 2 GiB cache for each target, Alpine branch and
build flavor. Keys deliberately exclude commit and PR identifiers, allowing
PRs to restore snapshots warmed on `master`. GitHub's cache access rules still
apply: a PR's saved cache is available to that PR's reruns, not to other PRs or
`master`. Master release builds restore master caches. Parallel snapshots are
not merged, and the first build with a new key starts cold. This is GitHub
Actions cache storage, not a remote ccache service.

`CCACHE_DIR=$GITHUB_WORKSPACE/.cache/ccache` names the same bind-mounted directory
on Ubuntu and inside Alpine. The chroot entry script explicitly preserves
`CCACHE_*`, including `CCACHE_COMPILERCHECK=content`, compression and size limits.
CI checks this configuration inside Alpine and restores runner ownership before
the cache action saves the root-written files. Cache statistics and probes are
retained with the build logs.

Host compiler/binutils builds use ccache through `COMMON_CONFIG`. musl uses the
in-tree xgcc through ccache; libgcc/libstdc++ use GCC's `STAGE_CC_WRAPPER` hook,
preserving generated sysroot and compiler flags. Library builds also use ccache.
`scripts/compiler-cache.sh` fingerprints the driver, C/C++ frontends and target assembler
once per build command and selects a cache namespace. This lets identical
compiler contents survive timestamp changes while preventing different
frontends or assemblers from sharing results. The initial host GCC build precedes this helper
because its xgcc/frontends do not exist yet. No unsafe timestamp sloppiness is set.

For a local build with a host ccache:

```sh
export CCACHE_DIR="$PWD/.cache/ccache"
export CCACHE_COMPILERCHECK=content
export CCACHE_MAXSIZE=2G
make prepare
bash scripts/check-ccache.sh "${ARCH:-x86_64-linux-musl}"
ccache --show-stats
```

The probe removes and recompiles tracked C and C++ objects twice with the
in-tree drivers and requires actual hits. It runs for every CI target. Set
`CCACHE_LAUNCHER=` on make to build without caching; use a host executable,
not a foreign-target packaged ccache. Cache hits depend on matching compiler
contents, source paths, flags and headers; an unchanged cache key does not
guarantee reuse. See [GitHub cache scope](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache)
and the [ccache manual](https://ccache.dev/manual/latest.html).

## Package validation

`make smoke ARCH=<tuple>` compiles C against curl, libssh2, LibreSSL, zlib and
wide ncurses, plus C++20/thread/atomic/Kyoto Cabinet code. It checks ELF machine
identity and absence of dynamic dependencies, including packaged ccache.
It also discovers installed Boost/SQLite/ZeroMQ packages through CMake, links
GnuTLS and libsodium statically, and exercises CURVE and certificate-verified
WSS on native x86_64. See [the dependency profile and update procedure](bitcoin.md). Native
x86_64 applications and ccache are also executed. Foreign execution needs target
hardware or an emulator; a cross-link/ELF pass alone is not a runtime test.

The [headless SDL3 profile](sdl3.md) also exercises offscreen software rendering,
PNG/JPEG images, FreeType rasterization and HarfBuzz Arabic shaping. CMake and
pure-C pkg-config consumers must link statically, including after moving the
SDK with its original prefix unavailable. Python 3 generates the test font;
no system font package or desktop session is required.
The [Dear ImGui consumer](imgui.md) additionally renders widgets and font-atlas
pixels through SDL3's software backend, checking both installed package interfaces.

For a quick library-only reproduction with an existing verified compiler:

```sh
make -C libs ARCH=riscv64-linux-musl \
  TOOLCHAIN=/path/to/dyne/gcc-musl \
  PREFIX="$PWD/.cache/install/riscv64-linux-musl"
TOOLCHAIN=/path/to/dyne/gcc-musl \
TARGET_PREFIX="$PWD/.cache/install/riscv64-linux-musl" \
  make smoke ARCH=riscv64-linux-musl
```

This does not validate a fresh compiler bootstrap or the Alpine environment.
The `PREFIX` must be dedicated to this package set: configuration changes remove
and reconstruct it to avoid retaining obsolete headers and libraries.

## Sources and package changes

`sources.urls` records one exact upstream URL per manifest key. Compiler
and library Make rules always resolve their downloads through this manifest.
Packages use official release archives; config.sub comes from
[GNU Gnulib's upstream mirror](https://github.com/coreutils/gnulib/blob/52b0cbbc7bc3be8137ea0a71be48f62d68aa98ff/build-aux/config.sub)
at immutable commit `52b0cbbc7bc3be8137ea0a71be48f62d68aa98ff` using its raw
repository URL. This is the same GNU config revision `3d5db9ebe860`: both copies
have Git blob ID `8d39c4ba39fe355d2282cc414828c01b762df133` and SHA-256
`75d5d255a2a273b6e651f82eecfabf6cbcd8eaeae70e86b417384c8f4a58d8d3`.
The original revision key and checksum remain unchanged. Savannah's cgit
frontend returned intermittent 404s, and its Git endpoint subsequently exhausted
all three fetch attempts with slow-transfer/time-limit failures on two master
CI targets. The default build therefore does not depend on either endpoint.
Do not replace the immutable commit with a branch such as master.

For deliberately selected Git inputs, the downloader also supports
`git+https://REPOSITORY.git#FULL_40_HEX_COMMIT:relative/path`.
The downloader shallow-fetches that exact commit into a private temporary bare
repository and reads the blob. Git and `timeout` are required for fresh
Git inputs. Fetches have a 120-second limit and at most three attempts; revision,
file type and SHA-256 are checked before publishing. Temporary state is removed
on failure. Use a full commit, not a branch/tag or abbreviated revision.
The config.sub routing change does not change the helper or any package version.
There is no source-mirror upload
prerequisite, source-cache service dependency or fallback on HTTP/integrity errors.

The old `SOURCES_URL` mirror override has been removed; setting it no longer
changes build downloads. For a test fixture or deliberately managed source
location, supply a complete `SOURCE_URLS=/absolute/path/to/urls` manifest instead;
the committed checksums still apply. Local caches are retained and reverified,
so repeat builds do not redownload intact inputs. These cache directories are
local build state, separate from the removed remote source-cache dependency.

`scripts/download.sh` accepts URL, destination, SHA-256 manifest, optionally
a manifest key and URL manifest. An empty URL selects the key from the URL
manifest; an explicit URL takes precedence. Existing files are verified on each build; corrupt caches fail
closed. Remove only the identified corrupt cache entry before retrying. New
downloads go into a private temporary file beside the destination and are moved
into place only after transport success and checksum verification.

Compiler downloads use `gcc-musl/sources/`; library downloads use
`.cache/sources/`. `gcc-musl/sources/GNUmakefile` delegates to the compiler's
`fetch-sources` target, using the selected configuration. It is no longer a
second manually maintained archive list. An external `SOURCES` directory is
read-only input and must already contain the selected archives and config.sub.

For a new compiler version, update the base version and selected configurations,
add the filename's legacy `gcc-musl/hashes/*.sha1` catalog entry and its stronger
`sources.sha256` entry, and port the version-specific patches. The SHA-1 files
still identify supported archive names; SHA-256 enforces build-time integrity.
For config.sub, the manifest key includes `CONFIG_SUB_REV` even though the cached
filename is `config.sub`. A changed revision requires replacing the old cached
config.sub with the verified new one. Update the full repository commit in the
URL and the original GNU config revision key/configuration together; hash the
exact blob bytes, not an archive of the repository. When using Gnulib's copy,
record its commit separately and verify that its blob matches GNU config.

For libraries, update the version/archive variables in `libs/GNUmakefile`,
`sources.urls` and the SHA-256 manifest. Use the upstream release archive URL;
no Dyne source-cache publication is needed.
Adapt extraction or build options if upstream packaging changed. Add a new
library's installed-file target and its prerequisite edges to the build graph;
ensure the smoke test actually links its API. Update the public component list.

Digest provenance for the initial SHA-256 manifest: compiler archives and
config.sub were checked against this repository's existing committed SHA-1 pins
before recording SHA-256. All seven library archive digests were also compared
against exact upstream HTTPS downloads (ncurses via ftp.gnu.org; the others via
the upstream URLs recorded in the component list below). This is integrity
pinning, not a claim that upstream release signatures were independently audited.
Future updates should verify upstream signatures or published digests where
available before accepting new pins.

| Component | Upstream source |
| --- | --- |
| LibreSSL | https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/ |
| zlib-ng | https://github.com/zlib-ng/zlib-ng/releases |
| curl | https://curl.se/download/ |
| libssh2 | https://libssh2.org/download/ |
| ccache | https://github.com/ccache/ccache/releases |
| ncurses | https://ftp.gnu.org/gnu/ncurses/ |
| Kyoto Cabinet | https://dbmx.net/kyotocabinet/pkg/ |
| Boost headers | https://www.boost.org/releases/latest/ |
| SQLite | https://sqlite.org/download.html |
| ZeroMQ | https://github.com/zeromq/libzmq/releases |
| libsodium | https://github.com/jedisct1/libsodium/releases |
| GnuTLS | https://www.gnutls.org/download.html |
| Nettle (compatible 3.x) | https://ftp.gnu.org/gnu/nettle/ |

### Repeatable upstream update procedure

1. Record the date and check **stable releases** on each project's official
   website, release listing or API. Do not guess version numbers, use snapshots
   or assume GitHub tags are releases. Check unchanged packages too. For GitHub
   releases, for example:

   ```sh
   gh api repos/zlib-ng/zlib-ng/releases/latest --jq '{tag: .tag_name, prerelease, url: .html_url}'
   gh api repos/ccache/ccache/releases/latest --jq '{tag: .tag_name, prerelease, url: .html_url}'
   gh api repos/libssh2/libssh2/releases/latest --jq '{tag: .tag_name, prerelease, url: .html_url}'
   ```

2. Follow the actual release download links. Download into an ignored staging
   directory using `curl --fail --location --output <temporary> <exact-url>`.
   Compare published hashes or verify release signatures against upstream key
   fingerprints where available, then compute `sha256sum` of those exact bytes.
   Record the verification method and any signature-verification limitation.
   Renaming an archive is safe; repacking it changes the digest. In particular,
   zlib-ng's GitHub tag archive has a numeric URL but a `zlib-ng-VERSION` root;
   ccache's release asset is different from its GitHub-generated tag archive.
3. Update `sources.urls` and `sources.sha256` together. Update the compiler base
   pins and **both** `config.*.mak` variants, or the library variables. Add one
   supported `hashes/<archive>.sha1` entry for each selected compiler input.
   Choose an archive format upstream actually provides (MPC 1.4.1 uses xz).
   For a new Linux major version, use the corresponding upstream `vN.x` URL.
4. Compare pristine sources with every old version-specific patch. Preserve
   needed changes, drop already-integrated fixes, and record why in
   `gcc-musl/patches/README.md`. Check upstream musl-cross-make for post-release
   libc fixes. Keep patch provenance at an exact commit. Verify the full patch
   sequence without fuzz, then exercise the real cowpatch/extraction build.
   Do not run a whole-project `clean` while another target is building.
5. Run `make test` and ShellCheck, then `make -C libs fetch` and compiler
   `fetch-sources`. These verify caches; they never bless changed bytes by
   recomputing the committed hashes. A corrupt entry must be removed explicitly.
   Run clean compiler/library builds for all four targets, `make prepare`,
   `make smoke`, and archive checks. A library-only build with an old compiler
   does not validate a toolchain update. Native execution and foreign linking
   are different evidence; record which actually ran.
6. Update the component lists in `AGENTS.md` and `docs/readme.md`, and record
   build evidence and limitations. The offline source inventory check catches
   missing URLs/checksums/compiler catalog entries in either build flavor.
   PR CI runs the complete Alpine matrix; publish only after it passes.

### Stable releases checked on 2026-10-31

| Component / official release listing | Previous | Selected |
| --- | --- | --- |
| [GCC](https://gcc.gnu.org/) | 15.1.0 | 16.2.0 |
| [binutils](https://sourceware.org/binutils/) | 2.44 | 2.47 |
| [musl](https://musl.libc.org/releases.html) | 1.2.5 | 1.2.6 + upstream fixes |
| [Linux headers](https://www.kernel.org/) | 5.8.5 | 7.3.1 |
| [GMP](https://gmplib.org/) | 6.1.2 | 6.3.0 |
| [MPC](https://www.multiprecision.org/mpc/) | 1.1.0 | 1.4.1 |
| [MPFR](https://www.mpfr.org/mpfr-current/) | 4.0.2 | 4.2.2 |
| [LibreSSL](https://www.libressl.org/) | 4.1.0 | 4.4.0 |
| [zlib-ng](https://github.com/zlib-ng/zlib-ng/releases/latest) | 2.2.4 | 2.3.3 |
| [curl](https://curl.se/download.html) | 8.15.0 | 8.23.0 |
| [ccache](https://ccache.dev/) | 4.11.3 | 4.14.2 |
| [libssh2](https://github.com/libssh2/libssh2/releases/latest) | 1.11.1 | 1.11.1 (unchanged) |
| [ncurses](https://invisible-island.net/ncurses/announce.html) | 6.6 | 6.6 (unchanged) |
| [Kyoto Cabinet](https://dbmx.net/kyotocabinet/pkg/) | 1.2.80 | 1.2.80 (unchanged) |

For this update, new archives were downloaded from their exact upstream HTTPS
URLs. LibreSSL was compared with OpenBSD's published `SHA256`, Linux with
kernel.org's `sha256sums.asc`, and ccache with the release asset's SHA-256 in
GitHub's API. GnuPG is unavailable locally, so detached release signatures were
not verified. The other new digests pin the upstream HTTPS bytes; they are not
an independent signature-verification claim. The unchanged inputs retain
their previously verified digests. Linux's version selects API headers, not a
kernel image or a blanket minimum runtime kernel requirement.

The update's static-PIE smoke check exposed a pre-existing gap: the patched GCC
link specs alone cannot link non-PIC objects in `libc.a` into a PIE. Both Dyne
flavors now configure musl with `CFLAGS=-fPIC`. Applications must also compile
PIE objects with `-fPIE`; smoke checks link and inspect both `-static-pie` and
`-static -pie`, and execute them on the native target.

ccache's optional third-party source downloads are version/hash-pinned by the
upstream build scripts inside its verified release archive. They are separate
from this repository's top-level source mirror.

## Added target dependencies (2026-11-01)

Boost 1.92.0 and libsodium 1.0.22 archive SHA-256 values were compared with the
GitHub release asset digests. SQLite 3.54.1 was compared with the download page's
SHA3-256, then recorded as SHA-256. ZeroMQ 4.3.5 matches Bitcoin Core 32.1's
pinned SHA-256. GnuTLS 3.8.13's detached release signatures were verified with
the official GnuTLS release keyring (signing fingerprints
`5D46CB0F763405A7053556F47A75A648B3F9220C` and
`A6AB53A01D237A94F9EEC4D0412748A40AFCC2FB`). Nettle 3.10.2's SHA-256 was
computed from the official GNU HTTPS archive; its signature has not been
independently verified. GMP reuses the existing 6.3.0 compiler source pin.
These describe the checks performed for this update, not an automatic trust or
signature check on every build. Normal builds verify all selected SHA-256 pins.

GnuTLS needs Nettle >= 3.10; Nettle 4 is an API change, so use the maintained
3.x line until a clean build proves compatibility. GMP's old configure probes
need `-std=gnu17` with GCC 16's default C23, and its assembly build needs host
`m4`. The Alpine package list includes it. CMake launcher discovery uses the
host PATH, excluding packaged foreign-target `bin/ccache` executables. New static package metadata and
ZeroMQ patches are covered by file targets and fingerprint tests; missing
metadata triggers reinstallation. Read [bitcoin.md](bitcoin.md) before changing
this graph or enabling more optional crypto libraries.

## Release ordering and recovery

The release job consumes the four archives from the same validated workflow
run. It first checks completeness and writes exactly four SHA-256 entries;
`SHA256SUMS.txt` never hashes itself. Only then does semantic-release select and
tag a version on master. The canonical tag format is `vX.Y.Z`; all publication
steps use the action's actual Git-tag output and verify that it points to the
workflow's checked-out commit.

The workflow stages a draft GitHub release and uploads all assets, updates the
file mirror, then publishes the GitHub release. The changelog plugin was removed
because it generated an uncommitted file in an ephemeral job; generated release
notes are used directly instead. There is no npm publication.

Tags are retained on failure. To recover an incomplete publication, inspect the
existing tag, draft/public GitHub release, and file mirror first. Then dispatch
the workflow at the retained tag with the matching `release_tag` input:

```sh
gh workflow run main.yml --repo dyne/musl --ref vX.Y.Z -f release_tag=vX.Y.Z
```

This rebuilds and validates that exact commit, checks the existing tag identity,
and retries asset upload with replacement. It does not run semantic-release or
create a new version. An already-public release is refused to protect published
assets; repair its mirror using the existing published archives, rather than
silently substituting another build. A manual dispatch without `release_tag` validates only.
This retry facility applies to tags containing this workflow version. Legacy
bare tags and old workflows need deliberate recovery; do not manufacture or
delete tags to work around the identity check.

Required CI credentials remain `GITHUB_TOKEN` with contents-write permission in
the release job and `FILES_SSH_HOST`, `FILES_SSH_USER`, `FILES_SSH_KEY`, and
`FILES_SSH_PORT`. Pull-request build jobs have read-only repository permissions
and receive no mirror credentials.

The mirror still uses the established unversioned archive names in
`/srv/ftp/musl`. SCP updates across multiple files are not transactional; a failed
upload may leave a mixed set until retried. Verify the checksum file against all
four downloaded archives after publication. GitHub publication happens only
after SCP succeeds, and retrying the retained tag repairs partial uploads.

The build baseline pins Ubuntu 24.04 and Alpine v3.24, and pins semantic-release
to 24.2.7. Alpine package revisions, action major-version tags, and other host
packages can still evolve: this is not a bit-for-bit reproducible build claim.
