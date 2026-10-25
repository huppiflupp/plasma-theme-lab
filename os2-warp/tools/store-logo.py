#!/usr/bin/env python3
"""The KDE Store logo of an entry (STORE.md), drawn anew: an OS/2 window
on the variant's wallpaper with the word mark inside, no IBM logo (DESIGN.md §1).

    python3 tools/store-logo.py      # screenshots/store/{classic,neon}/logo.png
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "fonts/IBMPlex/IBMPlexSansCondensed-BoldItalic.otf"
S = 512                      # the store shows it square

# Warp 4's palette (DESIGN.md §2)
GREY, WHITE, DGREY, BLACK = "#cccccc", "#ffffff", "#808080", "#000000"
TITLE = "#2400a8"


def bevel(d, x0, y0, x1, y1, w, raised=True, outline=True):
    """OS/2's edge: light top left, dark bottom right, black outside."""
    lt, dk = (WHITE, DGREY) if raised else (DGREY, WHITE)
    if outline:
        d.rectangle([x0, y0, x1, y1], outline=BLACK, width=2)
        x0, y0, x1, y1 = x0 + 2, y0 + 2, x1 - 2, y1 - 2
    for i in range(w):
        d.line([x0 + i, y1 - i, x0 + i, y0 + i, x1 - i, y0 + i], fill=lt)
        d.line([x0 + i, y1 - i, x1 - i, y1 - i, x1 - i, y0 + i], fill=dk)


def button(d, x, y, n, glyph):
    d.rectangle([x, y, x + n, y + n], fill=GREY)
    bevel(d, x, y, x + n, y + n, 3)
    c, g = x + n / 2, n * 0.22
    if glyph == "close":
        for s in (-1, 1):
            d.line([c - g, y + n / 2 - g * s, c + g, y + n / 2 + g * s], fill=BLACK, width=5)
    elif glyph == "hide":
        d.rectangle([c - 4, y + n / 2 - 4, c + 4, y + n / 2 + 4], outline=BLACK, width=3)
    else:
        d.rectangle([c - g, y + n / 2 - g, c + g, y + n / 2 + g], outline=BLACK, width=4)


def classic():
    bg = Image.open(ROOT / "wallpapers/warp4-wirbel-violett.jpg").convert("RGB")
    side = min(bg.size)
    left = (bg.width - side) // 2
    img = bg.crop((left, 0, left + side, side)).resize((S, S), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    # the window: sizing border, title bar, a white client area
    x0, y0, x1, y1 = 48, 104, 464, 408
    d.rectangle([x0 + 10, y0 + 10, x1 + 10, y1 + 10], fill="#1a0f40")   # shadow
    d.rectangle([x0, y0, x1, y1], fill=GREY)
    bevel(d, x0, y0, x1, y1, 4)
    tb = 52
    tx0, ty0, tx1 = x0 + 12, y0 + 12, x1 - 12
    d.rectangle([tx0, ty0, tx1, ty0 + tb], fill=TITLE)
    bevel(d, tx0, ty0, tx1, ty0 + tb, 2, raised=False, outline=False)
    n = tb - 10
    for i, glyph in enumerate(("close", "hide", "max")):
        button(d, tx1 - 6 - (3 - i) * (n + 4) + 4, ty0 + 5, n, glyph)
    # the program icon as window menu: a small grey folder-ish tile
    d.rectangle([tx0 + 8, ty0 + 9, tx0 + 8 + n - 8, ty0 + 9 + n - 8], fill=GREY)
    bevel(d, tx0 + 8, ty0 + 9, tx0 + 8 + n - 8, ty0 + 9 + n - 8, 2)
    d.rectangle([tx0 + 16, ty0 + 20, tx0 + n - 8, ty0 + n - 6], fill="#00a0a0", outline=BLACK, width=2)

    cx0, cy0, cx1, cy1 = x0 + 12, ty0 + tb + 10, x1 - 12, y1 - 12
    d.rectangle([cx0, cy0, cx1, cy1], fill=WHITE)
    bevel(d, cx0, cy0, cx1, cy1, 3, raised=False, outline=False)

    big = ImageFont.truetype(str(FONT), 132)
    small = ImageFont.truetype(str(FONT), 64)
    mid = (cx0 + cx1) / 2
    d.text((mid + 4, cy0 + 116 + 4), "Warp", font=big, fill="#b8b8d8", anchor="ms")
    d.text((mid, cy0 + 116), "Warp", font=big, fill=TITLE, anchor="ms")
    d.text((mid, cy1 - 24), "Legacy", font=small, fill=BLACK, anchor="ms")
    return img


# Neon's palette (build.py NEON, DESIGN.md §9a)
NAVY, NIGHT, CYAN, VIOLET, PINK = "#0c1438", "#060b24", "#48cffe", "#7a4dff", "#ff4fd8"


def glow(img, layer, radii=(18, 6)):
    """The sharp lines of layer over their blurred light, as Neon's frame."""
    for r in radii:
        img = ImageChops.screen(img, layer.filter(ImageFilter.GaussianBlur(r)))
    return ImageChops.screen(img, layer)


def gradient(mask, a, b):
    """mask filled from a (top left) to b (bottom right)."""
    w, h = mask.size
    ramp = Image.linear_gradient("L").rotate(45, expand=True).resize((w, h))
    fill = Image.composite(Image.new("RGB", (w, h), b), Image.new("RGB", (w, h), a), ramp)
    out = Image.new("RGB", (w, h))
    out.paste(fill, mask=mask)
    return out


def neon():
    bg = Image.open(ROOT / "wallpapers/dunkel-lichtbogen-rechts.jpg").convert("RGB")
    side = min(bg.size)
    left = bg.width - side
    img = bg.crop((left, 0, left + side, side)).resize((S, S), Image.LANCZOS)

    x0, y0, x1, y1 = 48, 104, 464, 408
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x1, y1], fill=NAVY)
    tb = 52
    tx0, ty0, tx1 = x0 + 12, y0 + 12, x1 - 12
    d.rectangle([tx0, ty0, tx1, ty0 + tb], fill="#06123f")
    cx0, cy0, cx1, cy1 = x0 + 12, ty0 + tb + 10, x1 - 12, y1 - 12
    d.rectangle([cx0, cy0, cx1, cy1], fill=NIGHT)

    # the light: OS/2's edges, light top left in cyan, dark bottom right in
    # violet, the window's corner pink; buttons outlined, close in pink
    light = Image.new("RGB", (S, S))
    ld = ImageDraw.Draw(light)
    ld.line([x0, y1, x0, y0, x1, y0], fill=CYAN, width=4)
    ld.line([x0, y1, x1, y1, x1, y0], fill=VIOLET, width=4)
    ld.line([x1 - 60, y1, x1, y1, x1, y1 - 60], fill=PINK, width=4)
    ld.line([cx0, cy1, cx0, cy0, cx1, cy0], fill=VIOLET, width=2)
    ld.line([cx0, cy1, cx1, cy1, cx1, cy0], fill=CYAN, width=2)
    n = tb - 10
    for i, glyph in enumerate(("close", "hide", "max")):
        bx, by = tx1 - 6 - (3 - i) * (n + 4) + 4, ty0 + 5
        col = PINK if glyph == "close" else CYAN
        ld.rectangle([bx, by, bx + n, by + n], outline=col, width=3)
        c, m, g = bx + n / 2, by + n / 2, n * 0.22
        if glyph == "close":
            for sg in (-1, 1):
                ld.line([c - g, m - g * sg, c + g, m + g * sg], fill=col, width=4)
        elif glyph == "hide":
            ld.rectangle([c - 4, m - 4, c + 4, m + 4], outline=col, width=3)
        else:
            ld.rectangle([c - g, m - g, c + g, m + g], outline=col, width=3)
    ld.rectangle([tx0 + 8, ty0 + 9, tx0 + n, ty0 + n + 1], outline=CYAN, width=3)
    ld.rectangle([tx0 + 16, ty0 + 18, tx0 + n - 8, ty0 + n - 7], fill=VIOLET)

    # the word mark: "Warp" from cyan to violet, "Neon" in pink
    big = ImageFont.truetype(str(FONT), 132)
    small = ImageFont.truetype(str(FONT), 64)
    mid = (cx0 + cx1) / 2
    mask = Image.new("L", (S, S))
    ImageDraw.Draw(mask).text((mid, cy0 + 116), "Warp", font=big, fill=255, anchor="ms")
    light = ImageChops.screen(light, gradient(mask, CYAN, VIOLET))
    ld = ImageDraw.Draw(light)
    ld.text((mid, cy1 - 24), "Neon", font=small, fill=PINK, anchor="ms")
    img = glow(img, light)
    return img


def main():
    for name, draw in (("classic", classic), ("neon", neon)):
        out = ROOT / f"screenshots/store/{name}/logo.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        draw().save(out, optimize=True)
        print(out)


if __name__ == "__main__":
    main()
