#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <libavcodec/avcodec.h>
#include <libavdevice/avdevice.h>
#include <libavfilter/avfilter.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>

static int decode_svg(const AVCodec *decoder)
{
    static const char svg[] =
        "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'>"
        "<rect width='32' height='32' fill='#0080ff'/></svg>";
    AVCodecContext *context = avcodec_alloc_context3(decoder);
    AVPacket *packet = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();
    int passed = 0;
    if (!context || !packet || !frame ||
        avcodec_open2(context, decoder, NULL) < 0 ||
        av_new_packet(packet, sizeof svg - 1) < 0)
        goto cleanup;

    memcpy(packet->data, svg, packet->size);
    if (avcodec_send_packet(context, packet) < 0 ||
        avcodec_receive_frame(context, frame) < 0 ||
        frame->width != 32 || frame->height != 32 ||
        frame->format != AV_PIX_FMT_RGB32 || frame->linesize[0] < 128)
        goto cleanup;

    uint32_t pixel;
    memcpy(&pixel, frame->data[0] + 10 * frame->linesize[0] + 4 * 10, sizeof pixel);
    passed = pixel == UINT32_C(0xff0080ff);

cleanup:
    av_frame_free(&frame);
    av_packet_free(&packet);
    avcodec_free_context(&context);
    return passed;
}

int main(void)
{
    const AVCodec *svg = avcodec_find_decoder_by_name("librsvg");
    if (!avdevice_version() || !avutil_version() ||
        !swresample_version() || !swscale_version() ||
        !av_find_input_format("dash") || !avio_find_protocol_name("https://example.invalid") ||
        !avfilter_get_by_name("drawtext") || !avfilter_get_by_name("subtitles") ||
        !avfilter_get_by_name("zscale") ||
        !avcodec_find_decoder_by_name("libdav1d") || !avcodec_find_decoder_by_name("libjxl") ||
        !avcodec_find_decoder_by_name("libvpx") || !avcodec_find_decoder_by_name("libvpx-vp9")) {
        fputs("Missing a static FFmpeg library or decoding feature\n", stderr);
        return 1;
    }

    if (!svg || !decode_svg(svg)) {
        fputs("Could not decode SVG bytes into the expected AVFrame\n", stderr);
        return 1;
    }
    puts("Decoded SVG bytes directly into an AVFrame");
    return 0;
}
