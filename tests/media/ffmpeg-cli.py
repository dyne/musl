"""Smoke-test the packaged FFmpeg binaries using only in-memory I/O."""
import json
import subprocess
import sys

svg = (b"<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'>"
       b"<rect width='32' height='32' fill='#0080ff'/></svg>")
ffmpeg, ffprobe, *runner = sys.argv[1:]


def run(program, args, data):
    return subprocess.run([*runner, program, "-v", "error", *args],
                          input=data, stdout=subprocess.PIPE, check=True).stdout


svg_input = ["-f", "svg_pipe", "-frame_size", str(len(svg)), "-c:v", "librsvg",
             "-i", "pipe:0", "-frames:v", "1"]
pixels = run(ffmpeg, [*svg_input, "-pix_fmt", "rgba", "-f", "rawvideo", "pipe:1"], svg)
if pixels != b"\x00\x80\xff\xff" * (32 * 32):
    raise SystemExit("Unexpected FFmpeg RGBA buffer")

png = run(ffmpeg, [*svg_input, "-c:v", "png", "-f", "image2pipe", "pipe:1"], svg)
stream, = json.loads(run(ffprobe, ["-show_entries", "stream=codec_name,width,height",
                                   "-of", "json", "pipe:0"], png))["streams"]
if stream != {"codec_name": "png", "width": 32, "height": 32}:
    raise SystemExit(f"Unexpected FFprobe output: {stream}")
