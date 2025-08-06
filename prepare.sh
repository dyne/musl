#!/bin/sh

# Simply strip and prepare the build in dyne/
# these operations are best done in a shell script
set -e

rm -f dyne/bin/*-lto-dump
rm -rf dyne/share
rm -f dyne/${1}/lib/*.py

find dyne/gcc-musl/bin dyne/gcc-musl/lib -type f -exec file {} + \
| grep -E '(LSB exec|pie exec|shared obj|ar archive)' | cut -d: -f1 \
| xargs strip -g

find dyne/${1} -type f -exec file {} + \
| grep -E '(LSB exec|pie exec|shared obj|ar archive)' | cut -d: -f1 \
| xargs dyne/gcc-musl/bin/${1}-strip -g

cat README.md | awk '
{gsub(/\[[^][]+\]\([^()]+\)/, gensub(/\[([^][]+)\]\([^()]+\)/, "\\1", "g")); print}
' | fmt -w 72 | tee dyne/${1}/README.txt > dyne/gcc-musl/README.txt

cp settings.cmake dyne/gcc-musl
