#include <SDL3/SDL.h>
#include <SDL3_image/SDL_image.h>
#include <SDL3_ttf/SDL_ttf.h>
#include <stdio.h>

/* C callers need HarfBuzz's C++ runtime in pkg-config's static closure too. */
int main(int argc, char **argv)
{
    if (argc != 2 || !SDL_Init(0) || !TTF_Init()) return 1;
    TTF_Font *font = TTF_OpenFont(argv[1], 24);
    if (!font) return 2;
    SDL_Color color = {255, 255, 255, 255};
    SDL_Surface *text = TTF_RenderText_Blended(font, "fi", 2, color);
    if (!text || text->w <= 0 || text->h <= 0) return 3;
    SDL_IOStream *stream = SDL_IOFromDynamicMem();
    if (!stream || !IMG_SavePNG_IO(text, stream, false)) return 4;
    if (SDL_SeekIO(stream, 0, SDL_IO_SEEK_SET) != 0) return 5;
    SDL_Surface *decoded = IMG_Load_IO(stream, true);
    if (!decoded || decoded->w != text->w || decoded->h != text->h) return 6;
    SDL_DestroySurface(decoded);
    SDL_DestroySurface(text);
    TTF_CloseFont(font);
    TTF_Quit();
    SDL_Quit();
    puts("SDL3 image/font static C pkg-config closure passed");
    return 0;
}
