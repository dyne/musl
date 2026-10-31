#!/bin/sh
# Usage: compiler-cache.sh CCACHE_LAUNCHER GCC_DRIVER COMMAND [ARGS...]
# Hash the GCC frontends once per build command, not once per compilation.
set -eu
if [ "$#" -lt 3 ]; then
    echo 'Usage: compiler-cache.sh CCACHE_LAUNCHER GCC_DRIVER COMMAND [ARGS...]' >&2
    exit 2
fi
launcher=$1
compiler=$2
shift 2
if [ -z "$launcher" ]; then exec "$@"; fi

directory=$(dirname "$compiler")
frontend=$directory/cc1
if [ ! -f "$frontend" ]; then frontend=$("$compiler" -print-prog-name=cc1); fi
test -f "$frontend" || { echo "Cannot locate GCC frontend for $compiler" >&2; exit 1; }
fingerprints=$(sha256sum "$compiler" "$frontend" "$0")
frontend=$directory/cc1plus
if [ ! -f "$frontend" ]; then frontend=$("$compiler" -print-prog-name=cc1plus); fi
if [ -f "$frontend" ]; then
    fingerprints="$fingerprints
$(sha256sum "$frontend")"
fi
identity=$(printf '%s\n' "$fingerprints" | sha256sum)
CCACHE_NAMESPACE=${CCACHE_NAMESPACE:+$CCACHE_NAMESPACE-}gcc-${identity%% *}
CCACHE_COMPILERCHECK=${CCACHE_COMPILERCHECK:-content}
export CCACHE_NAMESPACE CCACHE_COMPILERCHECK
exec "$@"
