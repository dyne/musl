#!/bin/sh
# Usage: compiler-cache.sh CCACHE_LAUNCHER GCC_DRIVER COMMAND [ARGS...]
# Hash GCC, its frontends and assembler once per build command.
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
# Litecross supplies this assembler through AS_FOR_TARGET; installed GCC can
# locate its own assembler. A binutils-only update must invalidate objects too.
assembler=$directory/../../obj_binutils/gas/as-new
if [ ! -f "$assembler" ]; then assembler=$("$compiler" -print-prog-name=as); fi
if [ ! -f "$assembler" ]; then assembler=$(command -v "$assembler"); fi
test -f "$assembler" || { echo "Cannot locate GCC assembler for $compiler" >&2; exit 1; }
fingerprints="$fingerprints
$(sha256sum "$assembler")"
identity=$(printf '%s\n' "$fingerprints" | sha256sum)
CCACHE_NAMESPACE=${CCACHE_NAMESPACE:+$CCACHE_NAMESPACE-}gcc-${identity%% *}
CCACHE_COMPILERCHECK=${CCACHE_COMPILERCHECK:-content}
export CCACHE_NAMESPACE CCACHE_COMPILERCHECK
exec "$@"
