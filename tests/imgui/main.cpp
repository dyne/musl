#include <imgui.h>
#include <imgui_impl_sdl3.h>
#include <imgui_impl_sdlrenderer3.h>
#include <SDL3/SDL.h>

#include <cstdio>
#include <cstring>
#include <stdexcept>

static void require(bool value, const char* operation)
{
    if (!value) throw std::runtime_error(operation);
}

int main()
{
    try {
        require(SDL_SetHint(SDL_HINT_VIDEO_DRIVER, "offscreen"), "offscreen hint");
        require(SDL_Init(SDL_INIT_VIDEO), "SDL_Init");
        auto window = SDL_CreateWindow("ImGui offscreen", 320, 240, SDL_WINDOW_HIDDEN);
        require(window, "SDL_CreateWindow");
        auto surface = SDL_CreateSurface(320, 240, SDL_PIXELFORMAT_RGBA32);
        require(surface, "SDL_CreateSurface");
        auto renderer = SDL_CreateSoftwareRenderer(surface);
        require(renderer, "SDL_CreateSoftwareRenderer");
        IMGUI_CHECKVERSION();
        ImGui::CreateContext();
        ImGui::GetIO().IniFilename = nullptr;
        ImGui::GetIO().LogFilename = nullptr;
        require(ImGui_ImplSDL3_InitForSDLRenderer(window, renderer), "SDL3 platform backend");
        require(ImGui_ImplSDLRenderer3_Init(renderer), "SDL3 renderer backend");
        // The first frame creates the font texture; the second draws a UI.
        for (int frame = 0; frame < 2; ++frame) {
            ImGui_ImplSDLRenderer3_NewFrame();
            ImGui_ImplSDL3_NewFrame();
            ImGui::NewFrame();
            ImGui::SetNextWindowPos({10, 10}, ImGuiCond_Always);
            ImGui::SetNextWindowSize({280, 180}, ImGuiCond_Always);
            ImGui::Begin("Static musl");
            ImGui::TextUnformatted("Dear ImGui on SDL3 software rendering");
            ImGui::Button("Hello");
            ImGui::End();
            ImGui::Render();
            require(ImGui::GetDrawData()->TotalVtxCount > 0, "widget draw geometry");
            require(SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255) && SDL_RenderClear(renderer), "clear surface");
            ImGui_ImplSDLRenderer3_RenderDrawData(ImGui::GetDrawData(), renderer);
            require(SDL_RenderPresent(renderer), "SDL_RenderPresent");
        }
        bool colored = false;
        bool font_pixels = false;
        const auto pixels = static_cast<const unsigned char*>(surface->pixels);
        for (int y = 0; y < surface->h; ++y)
            for (int x = 0; x < surface->w; ++x) {
                const auto pixel = pixels + y * surface->pitch + x * 4;
                colored |= pixel[0] != 0 || pixel[1] != 0 || pixel[2] != 0;
                font_pixels |= pixel[0] > 200 && pixel[1] > 200 && pixel[2] > 200;
            }
        require(colored, "rendered widget pixels");
        require(font_pixels, "rasterized font pixels");
        ImGui_ImplSDLRenderer3_Shutdown();
        ImGui_ImplSDL3_Shutdown();
        ImGui::DestroyContext();
        SDL_DestroyRenderer(renderer);
        SDL_DestroySurface(surface);
        SDL_DestroyWindow(window);
        SDL_Quit();
        std::puts("Dear ImGui SDL3 offscreen widgets and font texture rendering passed");
    } catch (const std::exception& error) {
        std::fprintf(stderr, "%s: %s\n", error.what(), SDL_GetError());
        return 1;
    }
}
