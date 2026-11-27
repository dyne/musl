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
                    ["ssl", "crypto", "z", "curl", "ssh2", "ncursesw", "kyotocabinet", "sqlite3", "gmp", "nettle", "hogweed", "gnutls", "sodium", "zmq",
                     "SDL3", "SDL3_image", "SDL3_ttf", "freetype", "harfbuzz", "imgui",
                     "ffi", "pcre2-8", "glib-2.0", "gobject-2.0", "gmodule-2.0", "gthread-2.0", "gio-2.0",
                     "execinfo", "rsvg-2", "unwind", "cairo", "cairo-gobject", "pixman-1", "png16",
                     "pango-1.0", "pangocairo-1.0", "pangoft2-1.0", "fontconfig", "fribidi", "xml2", "asound"])
    required.update(target + "/include/" + header for header in
                    ["openssl/ssl.h", "zlib.h", "curl/curl.h", "libssh2.h", "ncursesw/curses.h", "kccachedb.h",
                     "boost/version.hpp", "boost/multi_index_container.hpp", "boost/test/included/unit_test.hpp",
                     "sqlite3.h", "sqlite3ext.h", "zmq.h", "gmp.h", "nettle/version.h", "gnutls/gnutls.h", "sodium.h",
                     "SDL3/SDL.h", "SDL3_image/SDL_image.h", "SDL3_ttf/SDL_ttf.h", "freetype2/ft2build.h", "harfbuzz/hb.h",
                     "imgui/imgui.h", "imgui/backends/imgui_impl_sdl3.h", "imgui/backends/imgui_impl_sdlrenderer3.h",
                     "ffi.h", "ffitarget.h", "pcre2.h", "glib-2.0/glib.h", "glib-2.0/glib-object.h",
                     "glib-2.0/gmodule.h", "glib-2.0/gio/gio.h", "gio-unix-2.0/gio/gunixinputstream.h",
                     "execinfo.h", "librsvg-2.0/librsvg/rsvg.h", "librsvg-2.0/librsvg/rsvg-cairo.h",
                     "librsvg-2.0/librsvg/rsvg-features.h", "librsvg-2.0/librsvg/rsvg-version.h",
                     "cairo/cairo.h", "cairo/cairo-gobject.h", "pixman-1/pixman.h", "png.h",
                     "pango-1.0/pango/pango.h", "pango-1.0/pango/pangocairo.h", "pango-1.0/pango/pangoft2.h",
                     "fontconfig/fontconfig.h", "fribidi/fribidi.h", "libxml2/libxml/parser.h",
                     "alsa/asoundlib.h"])
    required.update(target + "/lib/" + metadata for metadata in
                    ["pkgconfig/sqlite3.pc", "pkgconfig/libzmq.pc", "pkgconfig/gmp.pc", "pkgconfig/nettle.pc",
                     "pkgconfig/hogweed.pc", "pkgconfig/gnutls.pc", "pkgconfig/libsodium.pc", "cmake/ZeroMQ/ZeroMQConfig.cmake",
                     "pkgconfig/sdl3.pc", "pkgconfig/sdl3-image.pc", "pkgconfig/sdl3-ttf.pc", "pkgconfig/freetype2.pc", "pkgconfig/harfbuzz.pc",
                     "cmake/SDL3/SDL3Config.cmake", "cmake/SDL3_image/SDL3_imageConfig.cmake", "cmake/SDL3_ttf/SDL3_ttfConfig.cmake",
                     "cmake/harfbuzz/harfbuzzConfig.cmake", "cmake/harfbuzz/harfbuzz-targets.cmake",
                     "pkgconfig/imgui.pc", "cmake/imgui/imguiConfig.cmake", "cmake/imgui/imguiTargets.cmake",
                     "pkgconfig/libffi.pc", "pkgconfig/libpcre2-8.pc", "pkgconfig/glib-2.0.pc",
                     "pkgconfig/gobject-2.0.pc", "pkgconfig/gmodule-2.0.pc", "pkgconfig/gmodule-no-export-2.0.pc",
                     "pkgconfig/gthread-2.0.pc", "pkgconfig/gio-2.0.pc", "pkgconfig/gio-unix-2.0.pc",
                     "glib-2.0/include/glibconfig.h"])
    required.update(target + "/lib/pkgconfig/" + package + ".pc" for package in
                    ["execinfo", "librsvg-2.0", "cairo", "cairo-gobject", "cairo-png", "pixman-1",
                     "libpng", "pango", "pangocairo", "pangoft2", "fontconfig", "fribidi", "libxml-2.0", "alsa"])
    required.update({target + "/etc/fonts/fonts.conf", target + "/share/alsa/alsa.conf"})
    required.update(target + "/" + path for path in
                    ["lib/libmagic.a", "include/magic.h", "lib/pkgconfig/libmagic.pc",
                     "share/misc/magic.mgc", "share/licenses/libmagic/COPYING"])
    required.update(target + "/share/licenses/" + license for license in
                    ["boost/LICENSE_1_0.txt", "zeromq/LICENSE", "libsodium/LICENSE",
                     "gmp/COPYING", "nettle/COPYING.LESSERv3", "gnutls/COPYING.LESSERv2",
                     "SDL3/LICENSE.txt", "SDL3_image/LICENSE.txt", "SDL3_image/stb_image.h", "SDL3_image/nanosvg.h",
                     "SDL3_image/nanosvgrast.h", "SDL3_ttf/LICENSE.txt", "freetype/LICENSE.TXT",
                     "freetype/FTL.TXT", "freetype/GPLv2.TXT", "harfbuzz/COPYING", "imgui/LICENSE.txt",
                     "imgui/imstb_truetype.h", "imgui/imgui_draw.cpp", "libffi/LICENSE", "pcre2/LICENCE.md",
                     "glib/COPYING", "glib/gvdb/COPYING", "librsvg/COPYING.LIB", "librsvg/Cargo.lock",
                     "rust-std/COPYRIGHT", "rust-std/LICENSE-APACHE", "rust-std/LICENSE-MIT",
                     "cairo/COPYING", "pixman/COPYING", "libpng/LICENSE", "pango/COPYING",
                     "fontconfig/COPYING", "fribidi/COPYING", "libxml2/Copyright", "alsa-lib/COPYING"])
    for name in ["avcodec", "avdevice", "avfilter", "avformat", "avutil", "swresample", "swscale"]:
        required.update({f"{target}/lib/lib{name}.a", f"{target}/lib/pkgconfig/lib{name}.pc",
                         f"{target}/include/lib{name}/{name}.h"})
    required.update(target + "/bin/" + tool for tool in ["ffmpeg", "ffprobe"])
    required.update(target + "/lib/lib" + lib + ".a" for lib in
                    ["dav1d", "vpx", "jxl", "jxl_cms", "jxl_threads", "hwy", "brotlicommon",
                     "brotlidec", "brotlienc", "lcms2", "ass", "zimg", "bz2", "lzma"])
    required.update(target + "/lib/pkgconfig/" + lib + ".pc" for lib in
                    ["dav1d", "vpx", "libjxl", "libjxl_cms", "libjxl_threads", "libhwy", "libbrotlicommon",
                     "libbrotlidec", "libbrotlienc", "lcms2", "libass", "zimg", "liblzma"])
    required.update(target + "/share/licenses/" + license for license in
                    ["ffmpeg/COPYING.LGPLv2.1", "ffmpeg/LICENSE.md", "dav1d/COPYING", "libvpx/LICENSE",
                     "libvpx/PATENTS", "libjxl/LICENSE", "libjxl/PATENTS", "highway/LICENSE", "brotli/LICENSE",
                     "lcms2/LICENSE", "libass/COPYING", "zimg/COPYING", "bzip2/LICENSE", "xz/COPYING"])
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
