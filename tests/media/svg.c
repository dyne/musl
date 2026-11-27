#include <cairo-gobject.h>
#include <fontconfig/fontconfig.h>
#include <librsvg/rsvg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static cairo_status_t write_png(void *file, const unsigned char *data, unsigned int size) {
    return fwrite(data, 1, size, file) == size ? CAIRO_STATUS_SUCCESS : CAIRO_STATUS_WRITE_ERROR;
}

int main(int argc, char **argv) {
    if (argc != 2) return 1;
    FcConfig *fonts = FcConfigCreate();
    if (!fonts || !FcConfigAppFontAddFile(fonts, (const FcChar8 *)argv[1]) ||
        !FcConfigSetCurrent(fonts)) return 2;
    FcConfigDestroy(fonts);

    static const unsigned char svg[] =
        "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'>"
        "<rect width='12' height='12' fill='#0080ff'/>"
        "<text x='1' y='28' font-family='Dyne Smoke' font-size='12'>A</text></svg>";
    GError *error = NULL;
    RsvgHandle *handle = rsvg_handle_new_from_data(svg, sizeof svg - 1, &error);
    if (!handle) {
        fprintf(stderr, "%s\n", error->message);
        return 3;
    }
    cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 32, 32);
    cairo_t *cr = cairo_create(surface);
    RsvgRectangle viewport = {0, 0, 32, 32};
    if (!rsvg_handle_render_document(handle, cr, &viewport, &error)) {
        fprintf(stderr, "%s\n", error->message);
        return 4;
    }
    cairo_destroy(cr);
    g_object_unref(handle);
    cairo_surface_flush(surface);

    unsigned char *data = cairo_image_surface_get_data(surface);
    int stride = cairo_image_surface_get_stride(surface);
    if (*(const uint32_t *)data != 0xff0080ff || !cairo_gobject_surface_get_type()) return 5;
    int text_pixels = 0;
    for (int row = 16; row < 32; ++row) {
        const uint32_t *pixels = (const uint32_t *)(data + row * stride);
        for (int col = 0; col < 32; ++col)
            text_pixels += (pixels[col] >> 24) != 0;
    }
    if (!text_pixels) return 6;

    FILE *png = tmpfile();
    if (!png || cairo_surface_write_to_png_stream(surface, write_png, png) != CAIRO_STATUS_SUCCESS)
        return 7;
    cairo_surface_destroy(surface);
    rewind(png);
    unsigned char header[8];
    int valid = fread(header, 1, sizeof header, png) == sizeof header &&
                memcmp(header, "\x89PNG\r\n\x1a\n", sizeof header) == 0;
    fclose(png);
    return !valid;
}
