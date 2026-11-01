# Dear ImGui on SDL3

The SDK includes Dear ImGui **1.93.0**, its SDL3 platform backend and its
SDL_Renderer3 rendering backend in one static `libimgui.a`. It works with the
[headless SDL3 profile](sdl3.md), drawing widgets and text into software-rendered
surfaces. The profile does not provide visible desktop windows or GPU backends.

## Size and dependencies

The upstream source archive is approximately 2.1 MiB. The x86_64 static library
in the validated size-optimized build is approximately 1.9 MiB before stripping,
including the optional demo code. Applications only pull referenced archive
objects into their executable; the demo object is unused unless requested.
These measurements are for this configuration, not a fixed application size.

No new third-party libraries are required: this package links SDL3 and the
existing C++/musl runtimes. It does not depend on SDL_image, SDL_ttf, FreeType
or HarfBuzz. Dear ImGui's default font rasterizer is its bundled **stb_truetype**.
It generates a font-atlas texture, which the SDL renderer draws. An embedded
default font is available, so the basic UI requires no external font files.

Upstream also supports an optional FreeType rasterizer, which can improve
small-font hinting. FreeType is already in the SDK, but selecting that rasterizer
requires rebuilding Dear ImGui with its FreeType implementation. Defining a
macro only in an application does not change this prebuilt library.
Dear ImGui does not automatically use SDL_ttf or HarfBuzz for complex-script
shaping. SDL_ttf remains available independently for application-rendered text.

## Use the installed library

Configure with the SDK toolchain and `FORCE_STATIC=ON`, as for [SDL3](sdl3.md).
The CMake package exports the selected SDL backend dependency:

```cmake
find_package(imgui 1.93 CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE imgui::imgui)
```

Include `<imgui.h>`, `<imgui_impl_sdl3.h>` and
`<imgui_impl_sdlrenderer3.h>`. The SDK installs upstream `imconfig.h` unchanged;
build applications with compatible configuration/ABI settings.
The pkg-config interface is `pkg-config --static --cflags --libs imgui`, using
the selected target's package database and C++ compiler.

Initialize an offscreen SDL window, a surface and `SDL_CreateSoftwareRenderer`,
then create the ImGui context and initialize `ImGui_ImplSDL3_InitForSDLRenderer`
and `ImGui_ImplSDLRenderer3_Init`. Feed events to `ImGui_ImplSDL3_ProcessEvent`.
Each frame calls both backend `NewFrame` functions, `ImGui::NewFrame`, builds
widgets, calls `ImGui::Render` and passes the draw data to
`ImGui_ImplSDLRenderer3_RenderDrawData`. Present the software renderer.
The [SDK smoke consumer](https://github.com/dyne/musl/blob/master/tests/imgui/main.cpp)
is a complete headless rendering example with no font files or display server.

## Maintenance

Update `IMGUI` in `libs/GNUmakefile` and the exact URL/SHA-256 in the source
manifests together. The initial archive hash was computed from upstream's
versioned GitHub tag archive. Upstream ships sources rather than a CMake
package; `libs/cmake/imgui/` supplies the static build, exported target and
pkg-config metadata. These packaging files participate in the build fingerprint.
Backend sources are compiled unchanged. The stable release is used rather than
the separate docking branch.

`make smoke` checks CMake and pkg-config consumers, static-PIE ELF linkage and,
on native x86_64, rendered widget and font pixels. Validate SDK relocation with
the original installation path unavailable. Foreign runtime execution still
requires hardware or emulation. Preserve the MIT and bundled font/rasterizer
notices under `share/licenses/imgui` when distributing packages.

See upstream's [release](https://github.com/ocornut/imgui/releases/tag/v1.93.0),
[backend guide](https://github.com/ocornut/imgui/blob/v1.93.0/docs/BACKENDS.md) and
[font guide](https://github.com/ocornut/imgui/blob/v1.93.0/docs/FONTS.md).
