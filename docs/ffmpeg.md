# Build static FFmpeg with the musl SDK

The SDK provides the static C API for librsvg and its headless dependency
stack. Use it for SVG rasterisation, and use the profile below for a
software-only FFmpeg build with common audio and video decoding, subtitle
rendering, HTTPS, and MPEG-DASH.

## SDK libraries

Use the SDK's target prefix as the pkg-config search path. The packaged
`librsvg-2.0.pc` resolves the static dependency closure, including Cairo with
PNG and GObject support, Pixman, libpng, PangoCairo, PangoFT2, Fontconfig,
FriBidi, GLib, FreeType, HarfBuzz, and libxml2. The librsvg recipe disables
AVIF via dav1d and the GDK-Pixbuf integration.

For ALSA applications, use `pkg-config --static --cflags --libs alsa`.
The library supports built-in PCM plugins. External shared plugins need a
dynamic build. Set `ALSA_CONFIG_DIR="$SDK/share/alsa"` to use the SDK's
configuration on a system without ALSA data installed.

For stack traces, include `<execinfo.h>` and link `-lexecinfo` or use
`pkg-config --static --cflags --libs execinfo`. Build the code you want to
trace with `-funwind-tables`. The SDK's static provider reports addresses.
Keep debug information and record the load address for symbolisation of
static PIE executables.

## FFmpeg dependencies

Build the external libraries for the same musl target as the SDK. Keep
their installed headers, archives, and pkg-config metadata in a separate
prefix when convenient.

| Feature | External package | FFmpeg switch |
| --- | --- | --- |
| AV1 | dav1d | `--enable-libdav1d` |
| VP8/VP9 with WebM alpha | libvpx | `--enable-libvpx` |
| JPEG XL | libjxl, libjxl_threads | `--enable-libjxl` |
| Subtitles | libass | `--enable-libass` |
| zscale | zimg | `--enable-libzimg` |
| Additional image and container compression | bzip2, liblzma | `--enable-bzlib --enable-lzma` |

The recipe also enables SDK libraries for SVG, text, HTTPS, XML, and zlib,
plus iconv from musl. FFmpeg's native decoders handle H.264, HEVC, MPEG,
ProRes, DNxHD, FFV1, common audio codecs, and formats such as JPEG, TIFF,
WebP, and JPEG 2000. When decoding WebM with transparency, explicitly select
`libvpx` for VP8 or `libvpx-vp9` for VP9 before specifying the input.

## Configure and build

Start in a clean FFmpeg release source tree. Install GNU Make and pkg-config
on the build host. Use NASM for x86 assembly optimisations. Adjust the target,
FFmpeg architecture, and prefix paths for your build.

```sh
TARGET=x86_64-linux-musl
FF_ARCH=x86_64
FF_CROSS="/opt/dyne/gcc-musl/bin/$TARGET-"
SDK="/opt/dyne/$TARGET"
FF_DEPS="/opt/ffmpeg-deps/$TARGET"
FF_SOURCE="$PWD"
FF_OUT="$FF_SOURCE/install-musl"
FF_PKG_CONFIG="$(command -v pkg-config)"

export PKG_CONFIG_PATH=''
export PKG_CONFIG_LIBDIR="$SDK/lib/pkgconfig:$SDK/share/pkgconfig:$FF_DEPS/lib/pkgconfig:$FF_DEPS/lib64/pkgconfig:$FF_DEPS/share/pkgconfig"
unset PKG_CONFIG_SYSROOT_DIR

"$FF_PKG_CONFIG" --static --exists \
  dav1d vpx libjxl libjxl_threads librsvg-2.0 \
  libass freetype2 harfbuzz fontconfig fribidi zimg gnutls libxml-2.0 zlib liblzma
"$FF_PKG_CONFIG" --static --cflags --libs librsvg-2.0

mkdir "$FF_SOURCE/build-musl"
cd "$FF_SOURCE/build-musl"
"$FF_SOURCE/configure" \
  --prefix="$FF_OUT" --target-os=linux --arch="$FF_ARCH" \
  --enable-cross-compile --cross-prefix="$FF_CROSS" \
  --cc="${FF_CROSS}gcc" --cxx="${FF_CROSS}g++" \
  --pkg-config="$FF_PKG_CONFIG" --pkg-config-flags=--static \
  --extra-cflags="-I$SDK/include -I$FF_DEPS/include" \
  --extra-cxxflags="-I$SDK/include -I$FF_DEPS/include" \
  --extra-ldflags="-static -L$SDK/lib -L$FF_DEPS/lib -L$FF_DEPS/lib64" \
  --extra-libs="-lstdc++ -lm" \
  --enable-static --disable-shared --disable-autodetect --enable-pthreads \
  --disable-ffplay --disable-encoders --disable-debug --disable-doc \
  --enable-libdav1d --enable-libvpx --enable-libjxl --enable-librsvg \
  --enable-libass --enable-libfreetype --enable-libharfbuzz --enable-libfontconfig \
  --enable-libfribidi --enable-libzimg --enable-gnutls --enable-libxml2 \
  --enable-zlib --enable-bzlib --enable-lzma --enable-iconv
make -j"$(getconf _NPROCESSORS_ONLN)"
make install
```

The compiler uses its own libc sysroot. Leave the SDK and dependency prefixes
as include, library and pkg-config paths. The SDK metadata resolves paths
relative to its location. External metadata can use its installed absolute
prefix or its own relocatable paths. Keep `PKG_CONFIG_LIBDIR` limited to
target metadata so configure cannot pick up host libraries.

`--enable-static --disable-shared` controls FFmpeg's library outputs.
`--extra-ldflags=-static` controls executable linkage, and
`--pkg-config-flags=--static` requests private static dependency flags.
If a configure check fails, inspect `build-musl/ffbuild/config.log` for the
original link error and check the archives named by pkg-config.

## Verify executables and optionally export frames

Each executable should have no `INTERP` program header or `NEEDED` entries.
Run the decoder and input checks on a compatible target.

```sh
for bin in ffmpeg ffprobe; do
  "${FF_CROSS}readelf" -l -d "$FF_OUT/bin/$bin"
done
"$FF_OUT/bin/ffmpeg" -hide_banner -h decoder=librsvg
"$FF_OUT/bin/ffmpeg" -hide_banner -h decoder=libdav1d
"$FF_OUT/bin/ffmpeg" -filters
"$FF_OUT/bin/ffmpeg" -encoders
"$FF_OUT/bin/ffprobe" -v error -show_streams input.mp4
```

The strict profile keeps all FFmpeg encoders disabled. To export decoded
frames or PCM with the CLI, add these flags after `--disable-encoders`.

```sh
--enable-encoder=rawvideo,wrapped_avframe,pcm_s16le,pcm_f32le,png
```

With PNG enabled, select the SVG decoder and rasterisation width before
specifying the input.

```sh
"$FF_OUT/bin/ffmpeg" -c:v librsvg -width 2048 -i artwork.svg \
  -frames:v 1 -update 1 artwork.png
```

## Read frames into a buffer

In a C or C++ application, send input packets with `avcodec_send_packet()`
and receive decoded pixels in an `AVFrame` with `avcodec_receive_frame()`.
Read the planes through `frame->data` and use `frame->linesize` for row strides.
Keep a frame reference or copy the pixels if they must outlive the frame.
This path works with the encoder-free profile.

A caller can also capture binary stdout from the CLI. With the PNG encoder
enabled, this writes one PNG to stdout.

```sh
"$FF_OUT/bin/ffmpeg" -v error -c:v librsvg -width 2048 -i artwork.svg \
  -frames:v 1 -c:v png -f image2pipe pipe:1
```

For unpacked RGBA bytes, use `-c:v rawvideo -pix_fmt rgba -f rawvideo pipe:1`
with the rawvideo encoder enabled. Raw output has no header, so the caller
needs the frame dimensions and pixel format.

Provide fonts and Fontconfig configuration for SVG text and subtitles.
`FONTCONFIG_PATH="$SDK/etc/fonts"` selects the shipped configuration. HTTPS
uses a CA trust bundle on the target machine. SVG resources such as linked
images must also be available to the rasteriser.

See the [FFmpeg configure source](https://github.com/FFmpeg/FFmpeg/blob/master/configure),
[codec documentation](https://ffmpeg.org/ffmpeg-codecs.html), and
[librsvg build guide](https://gnome.pages.gitlab.gnome.org/librsvg/devel-docs/compiling.html).
