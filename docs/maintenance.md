# Build and release maintenance

The [local validation report](validation.md) records the initial checks and
their limits.

## Validation

The offline regression suite needs Python 3, PyYAML, GNU Make 4.3 or newer,
curl, CMake, a host C compiler, file, and standard GNU utilities:

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

`make smoke ARCH=<tuple>` compiles C against curl, libssh2, LibreSSL, zlib and
wide ncurses, plus C++20/thread/atomic/Kyoto Cabinet code. It checks ELF machine
identity and absence of dynamic dependencies, including packaged ccache. Native
x86_64 applications and ccache are also executed. Foreign execution needs target
hardware or an emulator; a cross-link/ELF pass alone is not a runtime test.

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

`sources.urls` records one exact HTTPS URL per manifest key. Builds use it by
default, so adopting a release does not depend on a prior source-mirror upload.
`SOURCES_URL=https://files.dyne.org/musl/sources` overrides all locations for a
populated mirror. It must contain byte-identical archives; there is no silent
fallback on HTTP or integrity failures. The pinned config.sub helper continues
to use the Dyne mirror rather than following an unpinned upstream branch.

`scripts/download.sh` accepts URL, destination, SHA-256 manifest, optionally
a manifest key and URL manifest. An empty URL selects the key from the URL
manifest; an explicit URL takes precedence. Existing files are verified on each build; corrupt caches fail
closed. Remove only the identified corrupt cache entry before retrying. New
downloads go into a private temporary file beside the destination and are moved
into place only after HTTP success and checksum verification.

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
config.sub with the verified new one.

For libraries, update the version/archive variables in `libs/GNUmakefile`,
`sources.urls` and the SHA-256 manifest. If maintaining the source mirror,
publish the exact archive there too.
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
   New Linux major versions need the corresponding `LINUX_SITE/vN.x` rule.
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

ccache's optional third-party source downloads are version/hash-pinned by the
upstream build scripts inside its verified release archive. They are separate
from this repository's top-level source mirror.

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
