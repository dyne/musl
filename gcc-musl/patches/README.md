# Selected release patch sets

Updated 2026-10-31. Historical version directories remain available for older
configurations; patches are selected by the exact source version.

## GCC 16.2.0

Ported the nine patches from `gcc-15.1.0`, preserving their changes: SSP
nonshared linkage, the private posix_memalign declaration, J2 support, static
PIE link specs, m68k sqrt, the libstdc++ directory copy-on-write workaround,
and the three FDPIC fixes. Hunks were refreshed against the 16.2.0 release
sources. The libstdc++ ChangeLog patch is deliberately a no-op: cowpatch must
materialize that directory before GCC's build writes into it.

## Binutils 2.47

Ported J2 support and SH FDPIC PR31619 from `binutils-2.44`, with refreshed
contexts (including upstream's boolean/type changes). Two old patches are
already incorporated and must not be applied again:

- `0003-riscv-pie-symbol-binding.diff`: `RISCV_COPY_INPUT_RELOC` already tests
  `bfd_link_pie(INFO)` alongside `SYMBOLIC_BIND` in `bfd/elfnn-riscv.c`.
- `0004-s390x-pie-symbol-binding.diff`: the corresponding condition in
  `bfd/elf64-s390.c` now uses `bfd_link_executable(info) || SYMBOLIC_BIND(...)`,
  covering PIE and ordinary executables.

## Musl 1.2.6

The release integrates both CVE-2025-26519 patches from 1.2.5. Carry the three
newer patch files verbatim from [richfelker/musl-cross-make at
5e8042e63de29f8473fc3b0b831a587ba284e1a8](https://github.com/richfelker/musl-cross-make/tree/5e8042e63de29f8473fc3b0b831a587ba284e1a8/patches/musl-1.2.6):

- CVE-2026-107891: integer overflow checks in regcomp.
- CVE-2026-40200: qsort heap invariants and bounds (three upstream commits).
- CVE-2026-6042: GB18030 iconv mappings and decoding complexity.

`tests/toolchain.c` exercises sorting, GB18030 non-BMP decoding and POSIX regex
through static and static-PIE binaries. It is a functional smoke check, not an
exhaustive vulnerability regression suite. Foreign binaries need target runners.

For the next update, inspect each patch against pristine release sources; check
whether it is already integrated before porting. Regenerate diffs with LF line
boundaries (C sources can contain form-feed characters), then verify the complete
patch sequence with zero fuzz and through the project's actual cowpatch path.
