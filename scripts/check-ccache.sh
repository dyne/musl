#!/usr/bin/env bash
# Run from the repository root after building the compiler.
set -euo pipefail
arch=${1:?Usage: check-ccache.sh TARGET}
case "$arch" in ''|*[!a-zA-Z0-9_.+-]*) echo 'Invalid target tuple' >&2; exit 2;; esac
: "${CCACHE_DIR:?Set CCACHE_DIR to the restored cache directory}"
launcher=${CCACHE_LAUNCHER:-$(command -v ccache)}
compiler=${BOOTSTRAP_COMPILER_DIR:-$PWD/gcc-musl/build/local/$arch/obj_gcc/gcc}
build=$PWD/build/cache-probe/$arch
mkdir -p "$build"
test "$("$launcher" --get-config compiler_check)" = content

hits() {
    "$launcher" --print-stats | awk '
        $1 == "direct_cache_hit" || $1 == "preprocessed_cache_hit" { total += $2 }
        END { print total + 0 }'
}
before=$(hits)
for language in c cpp; do
    driver=xgcc
    flags=()
    if [[ $language == cpp ]]; then driver=xg++; flags=(-std=c++20); fi
    for _ in 1 2; do
        rm -f "$build/$language.o"
        sh scripts/compiler-cache.sh "$launcher" "$compiler/xgcc" \
            "$launcher" "$compiler/$driver" -B "$compiler/" "${flags[@]}" \
            -c "tests/cache-probe.$language" -o "$build/$language.o"
        test -s "$build/$language.o"
    done
done
after=$(hits)
if (( after - before < 2 )); then
    echo "Expected C and C++ bootstrap cache hits; observed $((after - before))" >&2
    exit 1
fi
echo "Bootstrap C/C++ cache probe passed: $((after - before)) hits in four compilations"
