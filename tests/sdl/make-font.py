"""Create an original tiny TrueType fixture, using only Python's standard library.

Every glyph is a rectangle. The GSUB table joins f+i and Arabic lam+alef, so
the consumer can verify shaping and rasterization without a host font package.
This deliberately small test font is not intended for application text.
"""
from pathlib import Path
import struct
import sys


def u16(*values):
    return struct.pack(">" + "H" * len(values), *values)


def checksum(data):
    data += b"\0" * (-len(data) % 4)
    return sum(struct.unpack(">" + "I" * (len(data) // 4), data)) & 0xffffffff


def make_font():
    head = bytearray(54)
    struct.pack_into(">IIIIHH", head, 0, 0x10000, 0x10000, 0, 0x5f0f3cf5, 0, 1000)
    struct.pack_into(">hhhhHHhhh", head, 36, 0, 0, 500, 700, 0, 8, 2, 1, 0)
    hhea = bytearray(36)
    struct.pack_into(">IhhhHhhhhh", hhea, 0, 0x10000, 800, -200, 0, 600, 0, 0, 500, 1, 0)
    struct.pack_into(">H", hhea, 34, 7)
    maxp = bytearray(32)
    struct.pack_into(">IHHH", maxp, 0, 0x10000, 7, 4, 1)
    struct.pack_into(">H", maxp, 14, 1)
    glyph = struct.pack(">hhhhhHH", 1, 0, 0, 500, 700, 3, 0)
    glyph += b"\1" * 4 + struct.pack(">hhhhhhhh", 0, 500, 0, -500, 0, 0, 700, 0)
    glyph += b"\0" * (-len(glyph) % 4)
    mappings = [(0x66, 1), (0x69, 2), (0x627, 5), (0x644, 4), (0xffff, 0)]
    cmap4 = u16(4, 16 + 8 * len(mappings), 0, 10, 8, 2, 2)
    cmap4 += u16(*(cp for cp, _ in mappings)) + u16(0)
    cmap4 += u16(*(cp for cp, _ in mappings))
    cmap4 += u16(*((gid - cp) & 0xffff for cp, gid in mappings)) + u16(0, 0, 0, 0, 0)
    names, strings = [], b""
    for name_id, text in [(1, "Dyne Smoke"), (2, "Regular"), (4, "Dyne Smoke Regular"), (6, "DyneSmoke-Regular")]:
        data = text.encode("utf-16-be")
        names.append(u16(3, 1, 0x409, name_id, len(data), len(strings)))
        strings += data
    name = u16(0, len(names), 6 + 12 * len(names)) + b"".join(names) + strings
    # DFLT script, default language, one 'liga' feature, ligature lookup type 4.
    scripts = u16(1) + b"DFLT" + u16(8, 4, 0, 0, 0xffff, 1, 0)
    features = u16(1) + b"liga" + u16(8, 0, 1, 0)
    substitution = u16(1, 10, 2, 18, 28, 1, 2, 1, 4)
    substitution += u16(1, 4, 3, 2, 2) + u16(1, 4, 6, 2, 5)
    lookups = u16(1, 4, 4, 0, 1, 8) + substitution
    gsub = struct.pack(">IHHH", 0x10000, 10, 10 + len(scripts), 10 + len(scripts) + len(features))
    gsub += scripts + features + lookups
    tables = {
        "GSUB": gsub, "cmap": u16(0, 1, 3, 1) + struct.pack(">I", 12) + cmap4,
        "glyf": glyph * 7, "head": bytes(head), "hhea": bytes(hhea),
        "hmtx": u16(600, 0) * 7,
        "loca": struct.pack(">8I", *(i * len(glyph) for i in range(8))),
        "maxp": bytes(maxp), "name": name, "post": struct.pack(">I", 0x30000) + b"\0" * 28,
    }
    count = len(tables)
    power = 2 ** (count.bit_length() - 1)
    header = struct.pack(">IHHHH", 0x10000, count, power * 16, power.bit_length() - 1, count * 16 - power * 16)
    offset, directory, body = 12 + 16 * count, b"", b""
    head_offset = 0
    for tag, data in sorted(tables.items()):
        directory += tag.encode("ascii") + struct.pack(">III", checksum(data), offset, len(data))
        if tag == "head":
            head_offset = offset
        data += b"\0" * (-len(data) % 4)
        body += data
        offset += len(data)
    font = bytearray(header + directory + body)
    struct.pack_into(">I", font, head_offset + 8, (0xb1b0afba - checksum(font)) & 0xffffffff)
    return font


if __name__ == "__main__":
    Path(sys.argv[1]).write_bytes(make_font())
