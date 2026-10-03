#!/usr/bin/env python3
"""CDE backdrops, coloured with a palette the way dtwm colours them.

The pixmaps in backdrops/cde/ are CDE's own backdrops (programs/backdrops,
CC BY-SA 3.0, "The Open Group"). The XPM files (.pm) name their colours
symbolically: background, topShadowColor, bottomShadowColor, selectColor,
foreground. dtwm fills these from the workspace's colour set, so the same
tile looks different in every palette. The XBM files (.bm) are two-colour
bitmaps: foreground on background.

Only the standard library is used, because the installer runs this on the
desktop when a palette is applied.

    python3 backdrops.py Alpine out/     # write every tile for a palette
"""
from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "backdrops" / "cde"


# Plain fills of the background or foreground colour; a plain desktop
# colour does the same.
PLAIN = {"Background", "Foreground"}


def names():
    return sorted(p.stem for p in SOURCE.iterdir() if p.suffix in (".pm", ".bm") and p.stem not in PLAIN)


def fill_mode(name):
    """Plasma image FillMode: 3 tiles; 5 tiles across and stretches down,
    for the screen-high gradients (Concave, Convex, SkyDark, SkyLight)."""
    path = SOURCE / f"{name}.pm"
    if path.exists():
        height = int(re.findall(r'"((?:[^"\\]|\\.)*)"', path.read_text(errors="replace"))[0].split()[1])
        if height >= 512:
            return 5
    return 3


def rgb(value):
    """#rgb, #rrggbb or #rrrrggggbbbb to an (r, g, b) byte tuple."""
    value = value.lstrip("#")
    n = len(value) // 3
    return tuple(int(value[i * n:i * n + 2], 16) for i in range(3))


def read_xpm(path, colours):
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', path.read_text(errors="replace"))
    width, height, ncolours, cpp = (int(v) for v in strings[0].split()[:4])
    table = {}
    for line in strings[1:1 + ncolours]:
        key, spec = line[:cpp], line[cpp:].split()
        fields = dict(zip(spec[::2], spec[1::2]))
        symbol = fields.get("s")
        if symbol in colours:
            table[key] = colours[symbol]
        elif fields.get("c", "None").lower() != "none":
            table[key] = rgb(fields["c"]) if fields["c"].startswith("#") else colours["background"]
        else:
            table[key] = colours["background"]
    rows = []
    for line in strings[1 + ncolours:1 + ncolours + height]:
        rows.append([table.get(line[i:i + cpp], colours["background"]) for i in range(0, width * cpp, cpp)])
    # SkyLight.pm declares 1024 rows and holds 1023: repeat the last one.
    while len(rows) < height:
        rows.append(list(rows[-1]))
    return width, height, rows


def read_xbm(path, colours):
    text = path.read_text()
    width = int(re.search(r"_width\s+(\d+)", text).group(1))
    height = int(re.search(r"_height\s+(\d+)", text).group(1))
    data = [int(v, 16) for v in re.findall(r"0x([0-9a-fA-F]{2})", text)]
    stride = (width + 7) // 8
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            bit = data[y * stride + x // 8] >> (x % 8) & 1
            row.append(colours["foreground"] if bit else colours["background"])
        rows.append(row)
    return width, height, rows


def png(width, height, rows, scale=1):
    raw = b""
    for row in rows:
        line = b"".join(bytes(px) * scale for px in row)
        raw += (b"\x00" + line) * scale

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width * scale, height * scale, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def desktop(name, colours, width, height, scale=1):
    """The backdrop already tiled to a whole screen, as PNG.

    Plasma's image wallpaper scales a picture to the screen before it tiles
    it, which blows a 64-pixel tile up to screen size. Filled in here and
    shown unscaled ("centred"), every pixel stays a pixel. The screen-high
    gradients are stretched down to the screen height instead."""
    path = SOURCE / f"{name}.pm"
    if not path.exists():
        path = SOURCE / f"{name}.bm"
    w, h, rows = (read_xpm if path.suffix == ".pm" else read_xbm)(path, colours)
    lines = [b"".join(bytes(px) * scale for px in row) for row in rows]
    w *= scale
    reps = -(-width // w)
    lines = [(line * reps)[:width * 3] for line in lines for _ in range(scale)]
    h *= scale
    if fill_mode(name) == 5:
        pick = [min(len(lines) - 1, y * len(lines) // height) for y in range(height)]
    else:
        pick = [y % h for y in range(height)]
    raw = b"".join(b"\x00" + lines[i] for i in pick)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def colours_for(colour_set):
    """Motif colours of one palette set ({bg, fg, ts, bs, sel}) by XPM symbol."""
    return {"background": rgb(colour_set["bg"]), "foreground": rgb(colour_set["fg"]),
            "topShadowColor": rgb(colour_set["ts"]), "bottomShadowColor": rgb(colour_set["bs"]),
            "selectColor": rgb(colour_set["sel"])}


def render(name, colours, scale=1):
    path = SOURCE / f"{name}.pm"
    if not path.exists():
        path = SOURCE / f"{name}.bm"
    reader = read_xpm if path.suffix == ".pm" else read_xbm
    return png(*reader(path, colours), scale=scale)


def write_all(colour_set, out, scale=1):
    """One PNG tile per backdrop into out/; returns the written names."""
    out.mkdir(parents=True, exist_ok=True)
    colours = colours_for(colour_set)
    for name in names():
        (out / f"{name}.png").write_bytes(render(name, colours, scale))
    return names()


if __name__ == "__main__":
    import palettes
    target = Path(sys.argv[2] if len(sys.argv) > 2 else "backdrops-out")
    if len(sys.argv) > 1 and sys.argv[1] != "Copper":
        colour_set = palettes.load(sys.argv[1])[2]
    else:
        colour_set = palettes.copper_desktop()
    print(", ".join(write_all(colour_set, target)))
