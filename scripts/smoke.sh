#!/usr/bin/env bash
set -euo pipefail
arch=${1:?Usage: smoke.sh TARGET}
case "$arch" in
    x86_64-linux-musl) machine='Advanced Micro Devices X86-64' ;;
    arm-linux-musleabihf) machine=ARM ;;
    aarch64-linux-musl) machine=AArch64 ;;
    riscv64-linux-musl) machine=RISC-V ;;
    *) echo "Unsupported smoke-test target: $arch" >&2; exit 2 ;;
esac
compiler=${TOOLCHAIN:-$PWD/dyne/gcc-musl}
target=${TARGET_PREFIX:-$PWD/dyne/$arch}
build=${SMOKE_BUILD_DIR:-$PWD/build/smoke/$arch}
readelf=$compiler/bin/$arch-readelf
mkdir -p "$build"
for library in ssl crypto z curl ssh2 ncursesw kyotocabinet; do
    test -s "$target/lib/lib$library.a"
done
test -x "$target/bin/ccache"
"$compiler/bin/$arch-gcc" -static -Os -I"$target/include" tests/smoke.c \
    -L"$target/lib" -lcurl -lssh2 -lssl -lcrypto -lz -lncursesw -lpthread -o "$build/c"
"$compiler/bin/$arch-g++" -static -Os -std=c++20 -I"$target/include" tests/smoke.cpp \
    -L"$target/lib" -lkyotocabinet -latomic -lpthread -o "$build/cpp"
for binary in "$build/c" "$build/cpp" "$target/bin/ccache"; do
    headers=$("$readelf" -h -l -d "$binary")
    grep -q "$machine" <<< "$headers"
    if grep -Eq 'INTERP|NEEDED' <<< "$headers"; then
        echo "Unexpected dynamic dependency: $binary" >&2
        exit 1
    fi
done
if [[ $arch == x86_64-linux-musl && $(uname -m) == x86_64 ]]; then
    "$build/c"
    "$build/cpp"
    "$target/bin/ccache" --version
    echo "Native C, C++20/thread/database and ccache smoke tests passed"
else
    echo "Cross-target link/ELF checks passed for $arch; execution requires a target runner"
fi
