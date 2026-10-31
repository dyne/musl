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

`scripts/download.sh` accepts URL, destination, SHA-256 manifest and optionally
a manifest key. Existing files are verified on each build; corrupt caches fail
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

For libraries, update the version/archive variables in `libs/GNUmakefile` and
the SHA-256 manifest, then publish the exact archive to the source mirror.
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
