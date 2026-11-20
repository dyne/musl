#include <gio/gio.h>
#include <gio/gunixinputstream.h>
#include <unistd.h>

static void activate(GSimpleAction *action, GVariant *parameter, gpointer data)
{
    g_assert_true(g_action_get_enabled(G_ACTION(action)));
    g_assert_cmpstr(g_variant_get_string(parameter, NULL), ==, "test");
    *(gboolean *)data = TRUE;
}

static void check_closure(void)
{
    gboolean activated = FALSE;
    GSimpleAction *action = g_simple_action_new("test", G_VARIANT_TYPE_STRING);
    GClosure *closure = g_cclosure_new(G_CALLBACK(activate), &activated, NULL);
    g_closure_set_marshal(closure, g_cclosure_marshal_generic);
    g_signal_connect_closure(action, "activate", closure, FALSE);
    g_action_activate(G_ACTION(action), g_variant_new_string("test"));
    g_assert_true(activated);
    g_object_unref(action);
}

static void check_compression(void)
{
    const char input[] = "GIO static gzip round trip";
    gchar compressed[128];
    gchar output[128];
    gsize bytes_read, compressed_size, output_size;
    GError *error = NULL;
    GZlibCompressor *compressor = g_zlib_compressor_new(G_ZLIB_COMPRESSOR_FORMAT_GZIP, -1);
    GZlibDecompressor *decompressor = g_zlib_decompressor_new(G_ZLIB_COMPRESSOR_FORMAT_GZIP);

    GConverterResult result = g_converter_convert(G_CONVERTER(compressor), input, sizeof(input),
        compressed, sizeof(compressed), G_CONVERTER_INPUT_AT_END, &bytes_read, &compressed_size, &error);
    g_assert_no_error(error);
    g_assert_cmpint(result, ==, G_CONVERTER_FINISHED);
    g_assert_cmpuint(bytes_read, ==, sizeof(input));
    result = g_converter_convert(G_CONVERTER(decompressor), compressed, compressed_size,
        output, sizeof(output), G_CONVERTER_INPUT_AT_END, &bytes_read, &output_size, &error);
    g_assert_no_error(error);
    g_assert_cmpint(result, ==, G_CONVERTER_FINISHED);
    g_assert_cmpuint(bytes_read, ==, compressed_size);
    g_assert_cmpmem(output, output_size, input, sizeof(input));
    g_object_unref(decompressor);
    g_object_unref(compressor);
}

static void check_unix_stream(void)
{
    int fds[2];
    char byte = 0;
    GError *error = NULL;

    g_assert_cmpint(pipe(fds), ==, 0);
    g_assert_cmpint(write(fds[1], "a", 1), ==, 1);
    close(fds[1]);
    GInputStream *stream = g_unix_input_stream_new(fds[0], TRUE);
    g_assert_cmpint(g_input_stream_read(stream, &byte, 1, NULL, &error), ==, 1);
    g_assert_no_error(error);
    g_assert_cmpint(byte, ==, 'a');
    g_object_unref(stream);
}

int main(void)
{
    g_assert_true(g_regex_match_simple("^G(IO|Lib)$", "GIO", 0, 0));
    check_closure();
    check_compression();
    check_unix_stream();
    g_print("GLib regex, GObject closure, GIO gzip and Unix stream passed\n");
    return 0;
}
