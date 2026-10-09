#!/usr/bin/env python3
"""The pictures of the KDE Store entry, from frames taken in the lab VM
(see TESTING.md, "Store pictures"): every frame a screenshot (1920x1080).

    store-pictures.py gif OUT.gif [--ms N] [--shared] FRAME "Label" FRAME "Label" ...
        the frames with a label in the top-right corner ("<Label" top left,
        "_Label" bottom right), N ms each (2500);
        FRAME@X0,Y0,X1,Y1[,SCALE] adds that part enlarged in an inset, as
        `zoom` does (SCALE default 3); --shared gives all frames one palette and
        leaves the pixels unchanged from the frame before transparent, so that
        a series on the same desktop stores only what changes
    store-pictures.py overview OUT.png BACK.png MID.png FRONT.png
        three desktops in perspective on a backdrop, the store's hero picture
    store-pictures.py zoom OUT.png IN.png X0 Y0 X1 Y1 [SCALE]
        the frame with the given part of it enlarged (SCALE, default 3) in a
        bevelled inset at the top right, for the clock's styles
    store-pictures.py logo OUT.png [SIZE]
        the small picture of the entry: a launcher tile with the console's
        menu icon filling it, no text, legible at 70 px (needs PySide6)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = str(ROOT / "fonts/IBMPlex/IBMPlexSansCondensed-SemiBold.otf")
TEAL, DEEP, PANEL, INK, COPPER = (8, 104, 117), (16, 38, 43), (201, 222, 219), (16, 38, 43), (232, 135, 79)
LIGHT, DARK = (232, 241, 240), (118, 142, 140)


# --- gif -------------------------------------------------------------------

def label(im, text):
    """The label in the top-right corner; "<" before the text puts it top
    left, "_" bottom right (where the console does not sit)."""
    k = im.width / 1280   # the label grows with the frame
    corner, text = (text[0], text[1:]) if text[:1] in ("<", "_") else ("", text)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, round(22 * k))
    w = draw.textlength(text, font=font); h = round(30 * k); pad = round(12 * k)
    x1, y0 = im.width - round(16 * k), round(16 * k)
    if corner == "<":
        x1 = round(16 * k) + w + 2 * pad
    elif corner == "_":
        y0 = im.height - round(16 * k) - h - pad
    x0 = x1 - w - 2 * pad
    draw.rectangle((x0, y0, x1, y0 + h + pad), fill=PANEL, outline=INK, width=2)
    draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + round(7 * k)), fill=COPPER)
    draw.text((x0 + pad, y0 + pad), text, font=font, fill=INK)
    return im


def shared(out, images, ms):
    """Frames on the same desktop: each frame after the first leaves the
    pixels unchanged from the frame before transparent (index 255), which
    LZW stores almost for free, and draws its palette of 254 colours from
    the part that changed, so a small inset keeps its own colours."""
    import numpy as np
    rgbs = [np.asarray(im) for im in images]
    frames = []
    for i, im in enumerate(images):
        same = (rgbs[i] == rgbs[i - 1]).all(axis=2) if i else np.zeros(rgbs[i].shape[:2], bool)
        ys, xs = np.nonzero(~same)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else (0, 0, 1, 1)
        pal = im.crop(box).quantize(colors=254, method=Image.Quantize.MEDIANCUT)
        idx = np.asarray(im.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG)).copy()
        idx[same] = 255
        q = Image.fromarray(idx, "P")
        q.putpalette(pal.getpalette()[:254 * 3] + [0, 0, 0] * 2)
        q.info["transparency"] = 255
        frames.append(q)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0,
                   optimize=False, transparency=255, disposal=1)


def gif(out, args):
    ms, one = 2500, False
    while args[:1] in (["--ms"], ["--shared"]):
        if args[0] == "--ms":
            ms, args = int(args[1]), args[2:]
        else:
            one, args = True, args[1:]
    images = []
    for path, text in zip(args[::2], args[1::2]):
        path, _, part = path.partition("@")
        im = Image.open(path).convert("RGB")
        if part:
            im = inset(im, *[int(v) for v in part.split(",")])
        images.append(label(im, text))
    if one:
        shared(out, images, ms)
    else:
        frames = [im.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for im in images]
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=False)
    print(out, len(images), "frames")


# --- overview --------------------------------------------------------------

def coeffs(src, dst):
    import numpy as np
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return tuple(np.linalg.solve(np.array(A, float), np.array(B, float)))

def warp(im, quad, size):
    w, h = im.size
    c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], quad)
    return im.transform(size, Image.Transform.PERSPECTIVE, c, Image.Resampling.BICUBIC)

def frame(im, border=6):
    out = Image.new("RGBA", (im.width + 2 * border, im.height + 2 * border), DEEP + (255,))
    out.paste(im.convert("RGBA"), (border, border))
    return out

def overview(out, back, mid, front):
    W, H = 1600, 900
    bg = Image.new("RGB", (W, H), TEAL)
    d = ImageDraw.Draw(bg)
    # a soft copper glow at the bottom right, a dark fall-off at the top left
    glow = Image.new("RGB", (W, H), TEAL); g = ImageDraw.Draw(glow)
    g.ellipse((W * 0.45, H * 0.35, W * 1.3, H * 1.4), fill=(60, 120, 120))
    g.ellipse((-W * 0.3, -H * 0.5, W * 0.5, H * 0.5), fill=DEEP)
    bg = Image.blend(bg, glow.filter(ImageFilter.GaussianBlur(160)), 0.75)
    canvas = bg.convert("RGBA")
    layers = [(back, [(60, 80), (900, 30), (900, 560), (60, 470)], 0.72),
              (mid, [(420, 150), (1240, 110), (1240, 650), (420, 560)], 0.86),
              (front, [(700, 240), (1560, 210), (1560, 790), (700, 700)], 1.0)]
    for path, quad, alpha in layers:
        im = frame(Image.open(path).convert("RGB"))
        layer = warp(im, quad, (W, H))
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        mask = layer.split()[3]
        shadow.paste((0, 0, 0, 150), (18, 24), mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        canvas = Image.alpha_composite(canvas, shadow)
        if alpha < 1:
            layer.putalpha(layer.split()[3].point(lambda a: int(a * alpha)))
        canvas = Image.alpha_composite(canvas, layer)
    canvas.convert("RGB").save(out, quality=92)
    print(out, canvas.size)



# --- logo ------------------------------------------------------------------

def icon(size):
    import tempfile
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    tmp = Path(tempfile.gettempdir()) / f"cde-menu-{size}.png"
    app = QGuiApplication(sys.argv)
    r = QSvgRenderer(str(ROOT / "build/icons/CDECopper/scalable/all/cde-menu.svg"))
    im = QImage(size, size, QImage.Format_ARGB32); im.fill(QColor(0, 0, 0, 0))
    p = QPainter(im); r.render(p, QRectF(0, 0, size, size)); p.end()
    im.save(str(tmp))
    return Image.open(str(tmp))

def logo(out, size=512):
    """The store's product logo: it is shown at about 70 px and cropped to
    whatever box the page has, so the menu icon's drawing sits in the
    middle half of a plain teal square, with room on every side."""
    im = Image.new("RGB", (size, size), TEAL)
    ic = icon(size * 2); ic = ic.crop(ic.getbbox())
    side = int(size * 0.5)
    ic = ic.resize((side, int(side * ic.height / ic.width)), Image.Resampling.LANCZOS)
    im.paste(ic, (size // 2 - ic.width // 2, size // 2 - ic.height // 2), ic)
    im.save(out)
    print(out, im.size)


# --- zoom ------------------------------------------------------------------

def inset(im, x0, y0, x1, y1, scale=3):
    part = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.Resampling.LANCZOS)
    border = 6
    px, py = im.width - part.width - 2 * border - 40, round(80 * im.width / 1280)
    d = ImageDraw.Draw(im)
    d.rectangle((px - border, py - border, px + part.width + border - 1, py + part.height + border - 1), fill=PANEL)
    for i in range(3):
        d.line((px - border + i, py - border + i, px + part.width + border - 1 - i, py - border + i), fill=LIGHT)
        d.line((px - border + i, py - border + i, px - border + i, py + part.height + border - 1 - i), fill=LIGHT)
        d.line((px - border + i, py + part.height + border - 1 - i, px + part.width + border - 1 - i, py + part.height + border - 1 - i), fill=DARK)
        d.line((px + part.width + border - 1 - i, py - border + i, px + part.width + border - 1 - i, py + part.height + border - 1 - i), fill=DARK)
    im.paste(part, (px, py))
    return im

def zoom(out, src, x0, y0, x1, y1, scale=3):
    im = inset(Image.open(src).convert("RGB"), x0, y0, x1, y1, scale)
    im.save(out)
    print(out, "inset", (x1 - x0) * scale, (y1 - y0) * scale)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    what, out, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    if what == "gif":
        gif(out, rest)
    elif what == "overview":
        overview(out, *rest[:3])
    elif what == "zoom":
        zoom(out, rest[0], *[int(v) for v in rest[1:5]], int(rest[5]) if len(rest) > 5 else 3)
    elif what == "logo":
        logo(out, int(rest[0]) if rest else 512)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
