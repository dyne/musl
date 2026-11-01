#!/usr/bin/env python3
"""Check the distributable layout without extracting untrusted archive paths."""
import fnmatch
from pathlib import PurePosixPath
import sys
import tarfile

TARGETS = {"x86_64-linux-musl", "arm-linux-musleabihf", "riscv64-linux-musl", "aarch64-linux-musl"}


def check(arch, archive):
    if arch not in TARGETS:
        raise ValueError("unsupported target tuple")
    compiler = "dyne/gcc-musl"
    target = "dyne/" + arch
    required = {compiler + "/settings.cmake", compiler + "/README.txt", target + "/README.txt",
                target + "/bin/ccache", compiler + "/" + arch + "/lib/libc.a"}
    required.update(compiler + "/bin/" + arch + "-" + tool for tool in ["gcc", "g++", "ar", "strip", "readelf"])
    required.update(compiler + "/" + arch + "/lib/" + lib for lib in ["libstdc++.a", "libatomic.a"])
    required.update(target + "/lib/lib" + lib + ".a" for lib in
                    ["ssl", "crypto", "z", "curl", "ssh2", "ncursesw", "kyotocabinet", "sqlite3", "gmp", "nettle", "hogweed", "gnutls", "sodium", "zmq"])
    required.update(target + "/include/" + header for header in
                    ["openssl/ssl.h", "zlib.h", "curl/curl.h", "libssh2.h", "ncursesw/curses.h", "kccachedb.h",
                     "boost/version.hpp", "boost/multi_index_container.hpp", "boost/test/included/unit_test.hpp",
                     "sqlite3.h", "sqlite3ext.h", "zmq.h", "gmp.h", "nettle/version.h", "gnutls/gnutls.h", "sodium.h"])
    required.update(target + "/lib/" + metadata for metadata in
                    ["pkgconfig/sqlite3.pc", "pkgconfig/libzmq.pc", "pkgconfig/gmp.pc", "pkgconfig/nettle.pc",
                     "pkgconfig/hogweed.pc", "pkgconfig/gnutls.pc", "pkgconfig/libsodium.pc", "cmake/ZeroMQ/ZeroMQConfig.cmake"])
    required.update(target + "/share/licenses/" + license for license in
                    ["boost/LICENSE_1_0.txt", "zeromq/LICENSE", "libsodium/LICENSE",
                     "gmp/COPYING", "nettle/COPYING.LESSERv3", "gnutls/COPYING.LESSERv2"])
    with tarfile.open(archive, "r:xz") as package:
        members = package.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if not path.parts or path.is_absolute() or ".." in path.parts or path.parts[0] != "dyne":
                raise ValueError("unexpected archive path: " + member.name)
            if str(path).startswith((target + "/", compiler + "/" + arch + "/")):
                if any(fnmatch.fnmatch(path.name, pattern) for pattern in ["*.so", "*.so.*", "*.la"]):
                    raise ValueError("unexpected target shared library: " + member.name)
        missing = required - {str(PurePosixPath(m.name)) for m in members if m.isfile() or m.issym() or m.islnk()}
        if missing:
            raise ValueError("missing package files: " + ", ".join(sorted(missing)))
        names = {str(PurePosixPath(m.name)) for m in members if m.isfile()}
        for pattern in [target + "/lib/cmake/Boost-*/BoostConfig.cmake",
                        target + "/lib/cmake/boost_headers-*/boost_headers-config.cmake"]:
            if not any(fnmatch.fnmatch(name, pattern) for name in names):
                raise ValueError("missing package metadata: " + pattern)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise ValueError("usage: check-archive.py TARGET ARCHIVE.tar.xz")
        check(sys.argv[1], sys.argv[2])
    except (ValueError, OSError, tarfile.TarError) as error:
        sys.exit(str(error))
    print("Package layout and target-library checks passed: " + sys.argv[2])
