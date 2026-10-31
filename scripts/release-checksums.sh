#!/usr/bin/env bash
set -euo pipefail
cd "${1:?Usage: release-checksums.sh ARTIFACT_DIRECTORY}"
archives=()
for suffix in x86_64 arm_hf arm_64 riscv_64; do
    archive=dyne-gcc-musl-$suffix.tar.xz
    [[ -s $archive ]] || { echo "Missing release archive: $archive" >&2; exit 1; }
    archives+=("$archive")
done
temporary=$(mktemp .SHA256SUMS.XXXXXX)
trap 'rm -f "$temporary"' EXIT
sha256sum "${archives[@]}" > "$temporary"
mv -f "$temporary" SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt
