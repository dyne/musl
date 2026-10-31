#!/usr/bin/env bash
# Strip staged files with the correct host/target tools and prune target DSOs.
set -euo pipefail
arch=${1:?Usage: prepare.sh TARGET}
case "$arch" in ''|*[!a-zA-Z0-9_.+-]*) echo 'Invalid target tuple' >&2; exit 2;; esac
compiler=dyne/gcc-musl
target=dyne/$arch
target_strip=$compiler/bin/$arch-strip
host_strip=${HOST_STRIP:-strip}
[[ -d $compiler/$arch && -d $target && -x $target_strip ]] || {
    echo "Missing staged toolchain or libraries for $arch" >&2; exit 1;
}
command -v "$host_strip" >/dev/null
command -v file >/dev/null
work_tmp=$(mktemp -d)
trap 'rm -rf "$work_tmp"' EXIT

rm -f "$compiler/bin/"*-lto-dump "$target/lib/"*.py
rm -rf "$compiler/share/man" "$compiler/share/info"
find "$compiler/$arch" "$target" \
    \( -name '*.so' -o -name '*.so.*' -o -name '*.la' \) -delete

strip_tree() {
    local tree=$1 kind=$2 path description stripper relative first
    find "$tree" -type f -print0 > "$work_tmp/files"
    while IFS= read -r -d '' path; do
        description=$(file -b -- "$path")
        case "$description" in
            *ELF*|*'current ar archive'*|*'thin archive'*)
                stripper=$host_strip
                relative=${path#"$compiler/"}
                first=${relative%%/*}
                if [[ $kind == target || $path == "$compiler/$arch/"* ||
                      $path == "$compiler/lib/gcc/$arch/"* ]]; then
                    stripper=$target_strip
                elif [[ $path == "$compiler/lib/gcc/"* || $first == *-linux-musl* ]]; then
                    continue  # Leave other installed target sysroots alone.
                fi
                # GCC also installs host binutils under <target>/bin, and may
                # install host ELF plugins alongside target runtime archives.
                if [[ $kind == compiler && $description == *x86-64* ]]; then
                    stripper=$host_strip
                fi
                "$stripper" -g -- "$path"
                ;;
        esac
    done < "$work_tmp/files"
}
strip_tree "$compiler" compiler
strip_tree "$target" target

readme_tmp=$work_tmp/readme
sed -E 's/\[([^][]+)\]\([^()]+\)/\1/g' README.md > "$readme_tmp"
fmt -w 72 "$readme_tmp" > "$compiler/README.txt"
cp "$compiler/README.txt" "$target/README.txt"
cp settings.cmake "$compiler/"
