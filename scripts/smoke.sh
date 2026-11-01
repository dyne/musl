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
for library in ssl crypto z curl ssh2 ncursesw kyotocabinet sqlite3 gmp nettle hogweed gnutls sodium zmq SDL3 SDL3_image SDL3_ttf freetype harfbuzz imgui; do
    test -s "$target/lib/lib$library.a"
done
test -x "$target/bin/ccache"
"$compiler/bin/$arch-gcc" -static -Os tests/toolchain.c -o "$build/toolchain"
"$compiler/bin/$arch-gcc" -static-pie -fPIE -Os tests/toolchain.c -o "$build/static-pie"
"$compiler/bin/$arch-gcc" -static -pie -fPIE -Os tests/toolchain.c -o "$build/static-and-pie"
"$compiler/bin/$arch-gcc" -static -Os -I"$target/include" tests/smoke.c \
    -L"$target/lib" -lcurl -lssh2 -lssl -lcrypto -lz -lncursesw -lpthread -o "$build/c"
"$compiler/bin/$arch-g++" -static -Os -std=c++20 -I"$target/include" tests/smoke.cpp \
    -L"$target/lib" -lkyotocabinet -latomic -lpthread -o "$build/cpp"
cmake -S tests/dependencies -B "$build/dependencies" \
    -DCMAKE_TOOLCHAIN_FILE="$PWD/settings.cmake" -DARCH="$arch" \
    -DTOOLCHAIN_PREFIX="$compiler" -DTARGET_PREFIX="$target" -DCCACHE=OFF -DFORCE_STATIC=ON
cmake --build "$build/dependencies" --parallel 2
cmake -S tests/sdl -B "$build/sdl" \
    -DCMAKE_TOOLCHAIN_FILE="$PWD/settings.cmake" -DARCH="$arch" \
    -DTOOLCHAIN_PREFIX="$compiler" -DTARGET_PREFIX="$target" -DCCACHE=OFF -DFORCE_STATIC=ON
cmake --build "$build/sdl" --parallel 2
cmake -S tests/imgui -B "$build/imgui" \
    -DCMAKE_TOOLCHAIN_FILE="$PWD/settings.cmake" -DARCH="$arch" \
    -DTOOLCHAIN_PREFIX="$compiler" -DTARGET_PREFIX="$target" -DCCACHE=OFF -DFORCE_STATIC=ON
cmake --build "$build/imgui" --parallel 2
for binary in "$build/toolchain" "$build/static-pie" "$build/static-and-pie" \
    "$build/c" "$build/cpp" "$build/dependencies/dependencies" "$build/dependencies/pkgconfig" \
    "$build/dependencies/avena-dependencies" "$build/sdl/sdl" "$build/sdl/sdl-pkgconfig" \
    "$build/imgui/imgui" "$build/imgui/imgui-pkgconfig" "$target/bin/ccache"; do
    headers=$("$readelf" -h -l -d "$binary")
    grep -q "$machine" <<< "$headers"
    if grep -Eq 'INTERP|NEEDED' <<< "$headers"; then
        echo "Unexpected dynamic dependency: $binary" >&2
        exit 1
    fi
done
for binary in "$build/static-pie" "$build/static-and-pie" \
    "$build/dependencies/dependencies" "$build/dependencies/pkgconfig" "$build/sdl/sdl" "$build/sdl/sdl-pkgconfig" \
    "$build/imgui/imgui" "$build/imgui/imgui-pkgconfig"; do
    "$readelf" -h "$binary" | grep -Eq 'Type:[[:space:]]+DYN'
done
if [[ $arch == x86_64-linux-musl && $(uname -m) == x86_64 ]]; then
    "$build/toolchain"
    "$build/static-pie"
    "$build/static-and-pie"
    "$build/c"
    "$build/cpp"
    "$build/dependencies/dependencies"
    "$build/dependencies/pkgconfig"
    "$build/dependencies/avena-dependencies"
    ctest --test-dir "$build/sdl" --output-on-failure --parallel 1
    ctest --test-dir "$build/imgui" --output-on-failure --parallel 1
    "$target/bin/ccache" --version
    echo "Native libc/static-PIE, C, C++20/thread/database and ccache smoke tests passed"
else
    echo "Cross-target link/ELF checks passed for $arch; execution requires a target runner"
fi
