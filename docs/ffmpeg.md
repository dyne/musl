# Static FFmpeg with the musl SDK

Each target SDK includes FFmpeg **9.1**. It installs static `ffmpeg` and
`ffprobe` in the target's `bin/` directory. The C headers, static archives,
and pkg-config files are also included for libavcodec, libavdevice, libavfilter,
libavformat, libavutil, libswresample, and libswscale. Run the executables on
the target architecture. The cross-compiler and the host's pkg-config can
use the development files from the build machine.

## Decoding and rendering

| Feature | SDK support |
| --- | --- |
| Common video, audio, and image formats | Native FFmpeg decoders, including H.264, HEVC, ProRes, MPEG, AAC, FLAC, Opus, JPEG, and WebP |
| AV1, VP8/VP9, JPEG XL | dav1d, libvpx, libjxl, and libjxl_threads |
| SVG | librsvg, Cairo with PNG and GObject, Pixman, libpng, PangoCairo, PangoFT2, Fontconfig, FriBidi, GLib, FreeType, HarfBuzz, and libxml2 |
| Subtitles and text | libass, FreeType, HarfBuzz, Fontconfig, and FriBidi |
| Scaling and colour conversion | libswscale and zimg (`zscale`) |
| Local files and network inputs | FFmpeg demuxers, GnuTLS for HTTPS, and libxml2 for MPEG-DASH and IMF |
| Compression and character conversion | zlib, bzip2, liblzma, and musl iconv |

The SDK builds FFmpeg with software decoding and disables hardware
accelerators, FFplay, frei0r, and device inputs and outputs. It enables five
native encoders for exporting decoded data and running decode tests:
`rawvideo`, `wrapped_avframe`, `pcm_s16le`, `pcm_f32le`, and `png`.
For WebM with alpha, select `-c:v libvpx` or `-c:v libvpx-vp9` before the input
so FFmpeg decodes its alpha stream. librsvg builds without GDK-Pixbuf or
its optional dav1d-backed AVIF support. FFmpeg uses dav1d directly for AV1 video.
The JPEG XL libraries also link statically to Highway, Brotli, and Little CMS.

## Write a frame to a buffer

Read SVG bytes on standard input and capture one 32 × 32 RGBA frame from
standard output. A complete frame occupies 4,096 bytes.

```sh
svg_size=$(wc -c < artwork.svg)
"$SDK/bin/ffmpeg" -v error -f svg_pipe -frame_size "$svg_size" \
  -c:v librsvg -width 32 -height 32 \
  -i pipe:0 -frames:v 1 -pix_fmt rgba -f rawvideo pipe:1 < artwork.svg
```

For a single PNG buffer, replace `-pix_fmt rgba -f rawvideo` with
`-c:v png -f image2pipe`. Capture the child's stdout as bytes and use
its exit status to check that decoding succeeded. To probe a file, run
`"$SDK/bin/ffprobe" -v error -show_streams input.mp4`.

## Link an application

For a target such as `x86_64-linux-musl`, set `SDK` to the extracted
`dyne/x86_64-linux-musl` directory. Restrict pkg-config to the target's
relocatable metadata before cross-compiling.

```sh
export PKG_CONFIG_PATH=
export PKG_CONFIG_LIBDIR="$SDK/lib/pkgconfig"
unset PKG_CONFIG_SYSROOT_DIR

pkg-config --static --modversion libavcodec libavformat libswscale
"$SDK/../gcc-musl/bin/x86_64-linux-musl-gcc" -static player.c \
  $(pkg-config --static --cflags --libs libavformat libavcodec libavutil libswscale) \
  -o player
```

On ARM hard-float, link FFmpeg consumers with `-static`. The toolchain's
`libatomic.a` fallback lock code is incompatible with static PIE.

For in-process decoding, send a refcounted `AVPacket` to
`avcodec_send_packet()` and receive an `AVFrame` from
`avcodec_receive_frame()`. Read the planes using `frame->data` and
`frame->linesize`. Use libswscale when you need a particular pixel format
or want to copy into a tightly packed destination buffer.

Fonts and Fontconfig configuration are runtime resources for SVG text and
subtitle rendering. Applications verifying HTTPS certificates also need a
CA trust bundle. Set `FONTCONFIG_FILE="$SDK/etc/fonts/fonts.conf"` to use the
SDK's Fontconfig configuration.

## Related SDK libraries

Use `pkg-config --static --cflags --libs librsvg-2.0` to link
librsvg directly. For ALSA applications, link with
`pkg-config --static --cflags --libs alsa`. Set
`ALSA_CONFIG_DIR="$SDK/share/alsa"` to use the SDK's configuration.
Static ALSA supports built-in PCM plugins.

For stack traces, include `<execinfo.h>` and link with
`pkg-config --static --cflags --libs execinfo`. Compile the code you want to
trace with `-funwind-tables`. The static provider reports addresses.
Keep debug information and record the load address to symbolise static PIE
executables.

To rebuild the packaged profile, run `make prepare ARCH=<tuple>` in the
musl repository. The source pins and configuration are in `libs/ffmpeg.mk`.
`make smoke ARCH=<tuple>` checks static linkage and, on native x86_64, decodes
SVG into an `AVFrame` and checks raw RGBA and PNG on stdout.
