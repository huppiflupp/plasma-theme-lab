#!/usr/bin/env python3
"""The window tools (DESIGN.md §3) as PNG, one folder per variant.

Each folder holds, at 1x and 2x (file@2x.png):

  back, close, iconise, toggle          the four title bar tools, 20x20 at 1x
  pback, pclose, piconise, ptoggle      the same pressed
  tleft, tright                         the title bar's end caps, 3x20
  tmidt, tmidb                          the title bar's middle, upper and
                                        lower half, tiled sideways; where
                                        they are transparent, the title
                                        colour (the colour scheme's) shows,
                                        as in the Wimp, which plots the
                                        tool sprites over colour 12 (cream)
                                        for the window with the input focus
  resize                                the size tool, for the corner

The Wimp draws one black line between the tools and around the window;
the decoration draws those itself (decoration/contents/ui/main.qml).

    classic   RISC OS 3: grey bevelled tools, engraved glyphs, a flat title
    select    RISC OS 4: the RO400 tool sprites of the RISC OS sources
              (vendor/riscos-open, Apache 2.0), with their stone texture
    modern    RISC OS for 2026: the same layout drawn smooth at 2x,
              softer bevels, thinner glyphs, no texture
    dark      modern in the dark palette

    toolart.py OUTDIR [variant ...]
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor/riscos-open/RO400"
NAMES = ["back", "close", "iconise", "toggle"]
RO400 = {"back": "bicon22", "close": "cicon22", "iconise": "iicon22", "toggle": "ticon22",
         "pback": "pbicon22", "pclose": "pcicon22", "piconise": "piicon22", "ptoggle": "pticon22",
         "tleft": "tbarlcap22", "tright": "tbarrcap22", "tmidt": "tbarmidt22", "tmidb": "tbarmidb22",
         "resize": "sicon22"}


def save(im, out, name, scale1=None):
    """Save the 1x picture and a 2x one (nearest neighbour: pixels stay
    pixels), or the given 2x picture."""
    im.save(out / f"{name}.png")
    big = scale1 if scale1 is not None else im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    big.save(out / f"{name}@2x.png")


# ---- classic: RISC OS 3 ---------------------------------------------------
# The Wimp's colours 1, 0, 2, 4, 7; graphite() swaps in darker ones.
C_FACE, C_LIGHT, C_MID, C_DARK, C_INK = (221, 221, 221), (255, 255, 255), (187, 187, 187), (119, 119, 119), (0, 0, 0)


def classic_face(pressed):
    im = Image.new("RGBA", (20, 20), C_FACE)
    d = ImageDraw.Draw(im)
    hi, lo = (C_DARK, C_LIGHT) if pressed else (C_LIGHT, C_DARK)
    d.line([(0, 19), (0, 0), (19, 0)], fill=hi)
    d.line([(1, 18), (1, 1), (18, 1)], fill=hi if not pressed else C_MID)
    d.line([(1, 19), (19, 19), (19, 1)], fill=lo)
    d.line([(2, 18), (18, 18), (18, 2)], fill=C_MID if not pressed else lo)
    return im, d


def engrave(d, shapes, off=0):
    """Glyph lines cut into the face: dark, with a white edge below right."""
    for kind, box in shapes:
        b = [v + off for v in box]
        if kind == "rect":
            d.rectangle([b[0] + 1, b[1] + 1, b[2] + 1, b[3] + 1], outline=C_LIGHT)
            d.rectangle(b, outline=C_DARK)
        elif kind == "fill":
            d.rectangle(b, fill=C_FACE)
        elif kind == "line":
            d.line([(b[0] + 1, b[1] + 1), (b[2] + 1, b[3] + 1)], fill=C_LIGHT, width=2)
            d.line([(b[0], b[1]), (b[2], b[3])], fill=C_DARK, width=2)


CLASSIC_GLYPHS = {
    "back": [("rect", (3, 3, 11, 11)), ("fill", (7, 7, 16, 16)), ("rect", (7, 7, 15, 15))],
    "close": [("line", (5, 5, 14, 14)), ("line", (5, 14, 14, 5))],
    "iconise": [("rect", (4, 8, 15, 11))],
    "toggle": [("rect", (6, 6, 13, 13))],
    "resize": [("rect", (4, 4, 15, 15)), ("fill", (4, 4, 10, 10)), ("rect", (4, 4, 10, 10))],
}


def classic(out):
    for name, glyph in CLASSIC_GLYPHS.items():
        for pressed in (False, True):
            if pressed and name == "resize":
                continue
            im, d = classic_face(pressed)
            engrave(d, glyph, 1 if pressed else 0)
            save(im, out, ("p" if pressed else "") + name)
    # Title: flat colour between black lines; caps one pixel of bevel.
    cap = Image.new("RGBA", (3, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(cap)
    d.line([(0, 0), (0, 19)], fill=C_LIGHT + (110,))
    save(cap, out, "tleft")
    cap = Image.new("RGBA", (3, 20), (0, 0, 0, 0))
    ImageDraw.Draw(cap).line([(2, 0), (2, 19)], fill=C_DARK + (110,))
    save(cap, out, "tright")
    mid = Image.new("RGBA", (16, 10), (0, 0, 0, 0))
    ImageDraw.Draw(mid).line([(0, 0), (15, 0)], fill=C_LIGHT + (110,))
    save(mid, out, "tmidt")
    mid = Image.new("RGBA", (16, 10), (0, 0, 0, 0))
    ImageDraw.Draw(mid).line([(0, 9), (15, 9)], fill=C_DARK + (110,))
    save(mid, out, "tmidb")


# ---- select: RISC OS 4 sprites --------------------------------------------
def select(out):
    for name, sprite in RO400.items():
        save(Image.open(VENDOR / f"{sprite}.png").convert("RGBA"), out, name)


# ---- modern / dark: drawn at 8x, scaled to 2x and 1x ------------------------
def modern(out, dark=False):
    face = (52, 56, 64) if dark else (232, 232, 228)
    light = (92, 98, 110) if dark else (255, 255, 255)
    shade = (24, 26, 30) if dark else (168, 168, 164)
    ink = (214, 220, 230) if dark else (70, 72, 78)
    accent = (238, 210, 90)          # RISC OS's yellow, for the pressed glyph
    S = 8                            # supersampling per 2x pixel
    N = 40 * S                       # a 2x tool: 40 px

    def tool(name, pressed):
        im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        r = 6 * S
        d.rounded_rectangle([S, S, N - S, N - S], r, fill=shade if not pressed else light)
        d.rounded_rectangle([S, S, N - 2 * S, N - 2 * S], r, fill=light if not pressed else shade)
        d.rounded_rectangle([2 * S, 2 * S, N - 2 * S, N - 2 * S], r - S, fill=face)
        col = accent if pressed else ink
        w = int(2.2 * S)
        o = S if pressed else 0
        c = N // 2 + o
        if name == "back":
            d.rounded_rectangle([10 * S + o, 10 * S + o, 24 * S + o, 24 * S + o], 2 * S, outline=col, width=w)
            d.rounded_rectangle([16 * S + o, 16 * S + o, 30 * S + o, 30 * S + o], 2 * S, fill=face, outline=col, width=w)
        elif name == "close":
            k = 9 * S
            d.line([(c - k, c - k), (c + k, c + k)], fill=col, width=w)
            d.line([(c - k, c + k), (c + k, c - k)], fill=col, width=w)
        elif name == "iconise":
            d.rounded_rectangle([c - 10 * S, c - 2 * S, c + 10 * S, c + 2 * S], S, fill=col)
        elif name == "toggle":
            d.rounded_rectangle([c - 8 * S, c - 8 * S, c + 8 * S, c + 8 * S], 2 * S, outline=col, width=w)
        elif name == "resize":
            d.rounded_rectangle([c - 10 * S, c - 10 * S, c + 10 * S, c + 10 * S], 2 * S, outline=col, width=w)
            d.rounded_rectangle([c - 10 * S, c - 10 * S, c, c], 2 * S, fill=col)
        big = im.resize((40, 40), Image.LANCZOS)
        return big.resize((20, 20), Image.LANCZOS), big

    for name in NAMES + ["resize"]:
        for pressed in (False, True):
            if pressed and name == "resize":
                continue
            small, big = tool(name, pressed)
            save(small, out, ("p" if pressed else "") + name, big)
    # The title: a soft sheen over the title colour, no texture.
    for nm, top in (("tmidt", True), ("tmidb", False)):
        big = Image.new("RGBA", (16, 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        for y in range(20):
            a = int((60 if dark else 90) * (1 - y / 19)) if top else int((40 if dark else 30) * (y / 19))
            d.line([(0, y), (15, y)], fill=((255, 255, 255, a) if top else (0, 0, 0, a)))
        save(big.resize((16, 10), Image.LANCZOS), out, nm, big)
    for nm in ("tleft", "tright"):
        big = Image.new("RGBA", (6, 40), (0, 0, 0, 0))
        save(big.resize((3, 20)), out, nm, big)


def graphite(out):
    """Classic drawn in the Wimp's darker greys (colours 5, 4, 6, 7)."""
    global C_FACE, C_LIGHT, C_MID, C_DARK
    saved = C_FACE, C_LIGHT, C_MID, C_DARK
    C_FACE, C_LIGHT, C_MID, C_DARK = (85, 85, 85), (153, 153, 153), (68, 68, 68), (34, 34, 34)
    try:
        classic(out)
    finally:
        C_FACE, C_LIGHT, C_MID, C_DARK = saved


VARIANTS = {"classic": classic, "select": select, "modern": modern, "graphite": graphite,
            "dark": lambda out: modern(out, dark=True)}


def main():
    out = Path(sys.argv[1])
    for v in sys.argv[2:] or VARIANTS:
        d = out / v
        d.mkdir(parents=True, exist_ok=True)
        VARIANTS[v](d)
        print(d)


if __name__ == "__main__":
    main()
