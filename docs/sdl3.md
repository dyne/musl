# SDL3: headless graphics, images and fonts

The SDK includes static SDL **3.4.18**, SDL_image **3.4.8**, SDL_ttf **3.2.2**,
FreeType **2.15.0** and HarfBuzz **15.0.0**, for all four target architectures.
This is the headless/offscreen profile: software rendering and image/text
processing work without a display server. It does not open visible desktop
windows or provide X11, Wayland, OpenGL, Vulkan or hardware audio backends.
Dummy/offscreen video and dummy/disk audio drivers are included. SDL_mixer and
SDL_net are not included.

[Dear ImGui 1.93.0](imgui.md) is also available for headless widgets on SDL3's
software renderer. Its built-in font rasterizer is independent of SDL_ttf.

## Capabilities

- SDL core supplies surfaces, software rendering, events, timers and threads.
  Dynamic loading and external Linux desktop/service backends are disabled.
- SDL_image uses the release's built-in codecs, including stb and NanoSVG.
  PNG and JPEG loading/saving work without separate libpng/libjpeg packages.
  BMP, GIF, QOI, PNM, PCX, TGA, simple SVG and other built-in formats are also
  enabled. AVIF, JPEG XL, TIFF, WebP and libpng/APNG support are disabled.
- SDL_ttf uses FreeType for TrueType/OpenType rasterization and HarfBuzz for
  complex-script shaping. Applications supply font files and choose their text
  direction/language and layout. No font collection is bundled. SVG/color emoji
  through PlutoSVG, PNG-compressed font bitmaps, bzip2 fonts and Brotli/WOFF2
  fonts are disabled. FreeType reuses the SDK's zlib for compressed font data.

FreeType's reverse HarfBuzz dependency is disabled, keeping the static build
graph acyclic: zlib → FreeType → HarfBuzz → SDL_ttf. SDL_ttf also links SDL core.

## CMake consumers

Use the SDK's normal toolchain options:

```sh
cmake -S . -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=/opt/dyne/gcc-musl/settings.cmake \
  -DARCH=x86_64-linux-musl -DFORCE_STATIC=ON -DCCACHE=OFF
cmake --build build
```

In the application's `CMakeLists.txt`:

```cmake
find_package(SDL3 3.4 CONFIG REQUIRED COMPONENTS SDL3-static)
find_package(SDL3_image 3.4 CONFIG REQUIRED COMPONENTS SDL3_image-static)
find_package(SDL3_ttf 3.2 CONFIG REQUIRED COMPONENTS SDL3_ttf-static)
target_link_libraries(my_app PRIVATE SDL3_ttf::SDL3_ttf-static
  SDL3_image::SDL3_image-static SDL3::SDL3-static)
```

The exported targets resolve the static font/zlib dependency closure. Enable
C++ in the consumer project alongside C when using the CMake font target,
because HarfBuzz is implemented in C++. `pkg-config --static` also supplies
the C++ runtime for C callers:

```sh
PKG_CONFIG_LIBDIR=/opt/dyne/x86_64-linux-musl/lib/pkgconfig \
  pkg-config --static --cflags --libs sdl3-image sdl3-ttf
```

Use the selected target's pkg-config database, with no host package paths.
Compile/link with that target's compiler and `-static`; use `-fPIE -static-pie`
for static PIE. New libraries are built with PIC and their package metadata
supports SDK relocation. HarfBuzz's CMake export is adjusted to preserve the
FreeType/zlib closure; see [the patch notes](https://github.com/dyne/musl/blob/master/libs/patches/README.md).

For offscreen windows, set `SDL_VIDEODRIVER=offscreen`; surface processing can
also run without creating a window. Use the software renderer. Visible windows,
GPU rendering and audio output require a different SDK backend profile.

## Maintenance and validation

Update the five version variables in `libs/GNUmakefile`, exact URLs in
`sources.urls` and SHA-256 pins in `sources.sha256` together. Recheck upstream
options, codec availability, static dependency metadata and the HarfBuzz export
patch. Builds never fetch optional codecs or vendored font libraries.
The initial SDL/SDL_image/HarfBuzz hashes match GitHub's release-asset digests;
SDL_ttf and FreeType hashes were computed from their exact upstream archives.

`make test` checks build order, source integrity, metadata recovery and package
helper invalidation. `make smoke` builds CMake and pure-C pkg-config consumers
and checks static-PIE ELF files for every target. Native x86_64 runs offscreen
software rendering, PNG/JPEG round trips, font rasterization and Arabic
lam–alef ligature shaping. A tiny original geometric font is generated with
Python's standard library; tests need no host fonts, display server or network.
Foreign runtime validation requires target hardware or emulation.

Preserve the installed license notices for SDL, SDL_image's bundled codecs,
SDL_ttf, FreeType and HarfBuzz when packaging. The upstream sources and current
release notes are [SDL](https://github.com/libsdl-org/SDL/releases/tag/release-3.4.18),
[SDL_image](https://github.com/libsdl-org/SDL_image/releases/tag/release-3.4.8),
[SDL_ttf](https://github.com/libsdl-org/SDL_ttf/releases/tag/release-3.2.2),
[FreeType](https://freetype.org/) and
[HarfBuzz](https://github.com/harfbuzz/harfbuzz/releases/tag/15.0.0).
