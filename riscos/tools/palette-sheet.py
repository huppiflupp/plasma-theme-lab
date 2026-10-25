#!/usr/bin/env python3
"""A sheet of all variants, drawn from build/ (no Plasma needed): per
variant a window with its title bar (the decoration's pictures over the
scheme's title colour), a list with a selection, a default and a normal
button, and a strip of iconbar on the desktop colour.

    palette-sheet.py OUT.png
"""
import importlib.util
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
FONT = ImageFont.truetype(str(ROOT / "fonts/TeXGyreHeros/texgyreheros-regular.otf"), 13)
SMALL = ImageFont.truetype(str(ROOT / "fonts/TeXGyreHeros/texgyreheros-regular.otf"), 11)


def tile(v, W=360, H=260):
    P = v["P"]
    ids = build.ids(v)
    art = build.OUT / f"kwin/decorations/{ids['decoration']}/contents/ui/art"
    L = lambda n: Image.open(art / f"{n}.png").convert("RGBA")
    im = Image.new("RGBA", (W, H), P["desktop"])
    tex = ROOT / "vendor/riscos-open/Sprites-RO400" / f"{v.get('tile', '')}.png"
    d = ImageDraw.Draw(im)
    # window
    x0, y0, x1, y1 = 14, 12, W - 14, H - 64
    d.rectangle([x0, y0, x1, y1], fill=P["border"])
    d.rectangle([x0 + 1, y0 + 22, x1 - 1, y1 - 1], fill=P["surface"])
    x = x0 + 1
    for n in ("back", "close"):
        b = L(n); im.alpha_composite(b, (x, y0 + 1)); x += 21
    right = x1 - 42
    d.rectangle([x, y0 + 1, right - 1, y0 + 20], fill=P["title_active"])
    for xx in range(x, right - 1, 16):
        for n, yy in (("tmidt", y0 + 1), ("tmidb", y0 + 11)):
            m = L(n)
            m = m.crop((0, 0, min(m.width, right - 1 - xx), m.height))
            im.alpha_composite(m, (xx, yy))
    xx = right
    for n in ("iconise", "toggle"):
        b = L(n); im.alpha_composite(b, (xx, y0 + 1)); xx += 21
    title = v["name"]
    tw = d.textlength(title, font=FONT)
    d.text(((x + right) / 2 - tw / 2, y0 + 4), title, font=FONT, fill=P["title_active_text"])
    # list
    lx0, ly0 = x0 + 10, y0 + 32
    d.rectangle([lx0, ly0, lx0 + 150, ly0 + 92], fill=P["window"], outline=P["border"])
    for i, (name, sel) in enumerate((("!Boot", False), ("Apps", True), ("Documents", False), ("Utilities", False))):
        yy = ly0 + 4 + i * 22
        if sel:
            d.rectangle([lx0 + 2, yy - 1, lx0 + 148, yy + 18], fill=P["selection"])
        d.text((lx0 + 8, yy + 2), name, font=FONT, fill=P["selection_text"] if sel else P["text"])
    # buttons
    bx = lx0 + 166
    for i, (label, default) in enumerate((("OK", True), ("Cancel", False))):
        yy = ly0 + 8 + i * 36
        if default:
            d.rectangle([bx - 3, yy - 3, bx + 103, yy + 27], fill=P.get("default_ring", P["title_active"]), outline=P["border"])
        d.rectangle([bx, yy, bx + 100, yy + 24], fill=P["surface"], outline=P["border"])
        d.line([(bx + 1, yy + 23), (bx + 1, yy + 1), (bx + 99, yy + 1)], fill=P["light"])
        d.line([(bx + 1, yy + 23), (bx + 99, yy + 23), (bx + 99, yy + 1)], fill=P["dark"])
        tw = d.textlength(label, font=FONT)
        d.text((bx + 50 - tw / 2, yy + 5), label, font=FONT, fill=P["text"])
    # radio
    ry = ly0 + 84
    d.ellipse([bx, ry, bx + 14, ry + 14], fill=P["window"], outline=P["dark"])
    d.ellipse([bx + 4, ry + 4, bx + 10, ry + 10], fill=P.get("radio", "#dd0000"))
    d.text((bx + 20, ry), "Option", font=FONT, fill=P["text"])
    # iconbar
    bar = Image.new("RGBA", (W, 46), P["panel"])
    if tex.exists():
        t = Image.open(tex).convert("RGBA")
        for xx in range(0, W, t.width):
            bar.alpha_composite(t, (xx, 0)) if t.height >= 46 else None
    bd = ImageDraw.Draw(bar)
    bd.line([(0, 0), (W, 0)], fill=P["light"])
    icons = build.OUT / "icons" / v["icons"] / "34x34/apps"
    for i, (n, lab) in enumerate((("drive-harddisk", "Discs"), ("user-home", "Home"), ("applications-all", "Apps"))):
        p = icons / f"{n}.png"
        if p.exists():
            ic = Image.open(p).convert("RGBA").resize((28, 28))
            bar.alpha_composite(ic, (10 + i * 44, 2))
        bd.text((10 + i * 44 + 14 - bd.textlength(lab, font=SMALL) / 2, 31), lab, font=SMALL, fill=P["panel_text"])
    clock = "2:23pm"
    cw = bd.textlength(clock, font=FONT) + 12
    bd.rectangle([W - cw - 12, 10, W - 12, 32], fill=P["window"], outline=P["border"])
    bd.text((W - cw - 6, 13), clock, font=FONT, fill=P["text"])
    im.alpha_composite(bar, (0, H - 46))
    return im


def main():
    tiles = [tile(v) for v in build.VARIANTS]
    cols = 4
    W, H = tiles[0].size
    out = Image.new("RGB", (cols * W + (cols + 1) * 8, ((len(tiles) + cols - 1) // cols) * (H + 8) + 8), "#202020")
    for i, t in enumerate(tiles):
        out.paste(t, (8 + (i % cols) * (W + 8), 8 + (i // cols) * (H + 8)))
    out.save(sys.argv[1])
    print(sys.argv[1])


if __name__ == "__main__":
    main()
