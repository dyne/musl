#!/bin/sh
# Run from the repository root, after selecting gcc-musl/config.mak.
set -eu
arch=${1:?Usage: toolchain-state.sh TARGET}
case "$arch" in ''|*[!a-zA-Z0-9_.+-]*) echo 'Invalid target tuple' >&2; exit 2;; esac
state="build/toolchain/$arch"
mkdir -p "$state"
temporary=$(mktemp "$state/config.tmp.XXXXXX")
trap 'rm -f "$temporary"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
{
    make --no-print-directory -s -C gcc-musl print-config ARCH="$arch"
    sha256sum GNUmakefile gcc-musl/Makefile gcc-musl/litecross/Makefile \
        gcc-musl/config.mak scripts/toolchain-state.sh scripts/compiler-cache.sh sources.sha256
    find gcc-musl/patches -type f -exec sha256sum {} + | LC_ALL=C sort
    cc -dumpmachine
    cc -dumpversion
} > "$temporary"
if ! cmp -s "$temporary" "$state/config"; then
    echo "Toolchain configuration changed: rebuilding $arch" >&2
    rm -rf "gcc-musl/build/local/$arch" "dyne/gcc-musl/$arch" \
        "dyne/gcc-musl/lib/gcc/$arch" "dyne/gcc-musl/libexec/gcc/$arch"
    rm -f dyne/gcc-musl/bin/"$arch"-*
    mv -f "$temporary" "$state/config"
fi
