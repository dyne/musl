#include <SDL3/SDL.h>
#include <SDL3_image/SDL_image.h>
#include <SDL3_ttf/SDL_ttf.h>
#include <hb.h>
#include <hb-ot.h>

#include <cstring>
#include <iostream>
#include <stdexcept>

static void require(bool value, const char* operation)
{
    if (!value) throw std::runtime_error(operation);
}

int main(int argc, char** argv)
{
    try {
        require(argc == 2, "font fixture argument");
        require(SDL_SetHint(SDL_HINT_VIDEO_DRIVER, "offscreen"), "offscreen hint");
        require(SDL_Init(SDL_INIT_VIDEO), "SDL_Init");
        require(std::strcmp(SDL_GetCurrentVideoDriver(), "offscreen") == 0, "offscreen driver");
        auto window = SDL_CreateWindow("headless smoke", 16, 16, SDL_WINDOW_HIDDEN);
        require(window, "offscreen window");
        auto surface = SDL_CreateSurface(16, 16, SDL_PIXELFORMAT_RGBA32);
        require(surface, "SDL_CreateSurface");
        auto renderer = SDL_CreateSoftwareRenderer(surface);
        require(renderer, "SDL_CreateSoftwareRenderer");
        require(SDL_SetRenderDrawColor(renderer, 20, 80, 160, 255) && SDL_RenderClear(renderer), "software rendering");
        require(SDL_RenderPresent(renderer), "SDL_RenderPresent");
        for (bool png : {true, false}) {
            auto stream = SDL_IOFromDynamicMem();
            require(stream, "SDL_IOFromDynamicMem");
            require(png ? IMG_SavePNG_IO(surface, stream, false) : IMG_SaveJPG_IO(surface, stream, false, 90), "image encoding");
            require(SDL_SeekIO(stream, 0, SDL_IO_SEEK_SET) == 0, "image rewind");
            auto decoded = IMG_Load_IO(stream, true);
            require(decoded && decoded->w == 16 && decoded->h == 16, "PNG/JPEG image decoding");
            SDL_DestroySurface(decoded);
        }
        require(TTF_Init(), "TTF_Init");
        int major, minor, patch;
        TTF_GetHarfBuzzVersion(&major, &minor, &patch);
        require(major > 0, "SDL_ttf HarfBuzz support");
        auto font = TTF_OpenFont(argv[1], 24);
        require(font, "TTF_OpenFont");
        constexpr char arabic[] = "\xD9\x84\xD8\xA7"; // lam + alef
        auto text = TTF_RenderText_Blended(font, arabic, sizeof(arabic) - 1, {255, 255, 255, 255});
        require(text && text->w > 0 && text->h > 0, "Arabic text rasterization");
        auto blob = hb_blob_create_from_file_or_fail(argv[1]);
        require(blob, "hb_blob_create_from_file_or_fail");
        auto face = hb_face_create(blob, 0);
        auto hbfont = hb_font_create(face);
        hb_ot_font_set_funcs(hbfont);
        auto buffer = hb_buffer_create();
        hb_buffer_add_utf8(buffer, arabic, -1, 0, -1);
        hb_buffer_guess_segment_properties(buffer);
        hb_shape(hbfont, buffer, nullptr, 0);
        unsigned count = 0;
        const auto glyphs = hb_buffer_get_glyph_infos(buffer, &count);
        require(count == 1 && glyphs[0].codepoint == 6, "Arabic ligature shaping");
        hb_buffer_destroy(buffer);
        hb_font_destroy(hbfont);
        hb_face_destroy(face);
        hb_blob_destroy(blob);
        SDL_DestroySurface(text);
        TTF_CloseFont(font);
        TTF_Quit();
        SDL_DestroyRenderer(renderer);
        SDL_DestroySurface(surface);
        SDL_DestroyWindow(window);
        SDL_Quit();
        std::cout << "SDL3 offscreen/software, PNG/JPEG and Arabic shaping/rasterization passed\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << ": " << SDL_GetError() << '\n';
        return 1;
    }
}
