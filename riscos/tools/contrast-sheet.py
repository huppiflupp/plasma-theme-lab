#!/usr/bin/env python3
"""How well the desktop icons stand out on each backdrop.

Puts the icons the desktop shows (DESKTOP_ICONS) at 64 px on the top left
of every picture, where Plasma's folder view lays them out, in both colour
worlds, and measures each icon: the share of its outline ring (the icon's
outermost 5 px (outline and the fill inside it)) whose contrast to the picture underneath is below 1.6:1.
An icon whose ring is mostly lost has no silhouette on that picture: the
network icon's thin black links on a night sky.

    contrast-sheet.py [--sheet out.png] [picture.jpg ...]   default: wallpapers/*.jpg

Prints one line per picture and world, the worst icons first, and exits
with 1 when an icon loses more than LIMIT of its ring. Needs the built
icon themes (build.py) and PySide6.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "build" / "icons"
WORLDS = {"ro4": "RiscLegacy", "ro5": "RiscLegacy2026"}
# What the desktop shows (the VM's desktop links, the user's usual set).
DESKTOP_ICONS = ["user-desktop", "computer", "network-workgroup", "internet-web-browser", "folder",
                 "applications-other", "folder-templates", "preferences-system", "applications-games",
                 "system-shutdown", "user-home", "user-trash"]
# LIMIT: a body with a dark rim (the shutdown button) loses up to ~65 % of
# its ring and still stands out; the bare-line icons lost 100 %.
SIZE, PITCH, LIMIT, RATIO = 64, 112, 0.7, 1.6


def rasterize(theme, name, size=SIZE):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    path = next((ICONS / theme / "scalable").glob(f"*/{name}.svg"))
    img = QImage(size, size, QImage.Format_RGBA8888)
    img.fill(0)
    p = QPainter(img)
    QSvgRenderer(str(path)).render(p, QRectF(0, 0, size, size))
    p.end()
    return Image.frombuffer("RGBA", (size, size), bytes(img.constBits()), "raw", "RGBA", 0, 1).copy()


def luminance(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def lost(icon, under):
    """The share of the icon's outline ring that disappears on `under`."""
    a = np.asarray(icon)[:, :, 3] > 128
    inner = np.asarray(Image.fromarray(a.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(11))) > 0
    ring = a & ~inner
    li = luminance(np.asarray(icon)[:, :, :3].astype(float))
    lb = luminance(np.asarray(under.convert("RGB")).astype(float))
    hi, lo = np.maximum(li, lb), np.minimum(li, lb)
    contrast = (hi + 0.05) / (lo + 0.05)
    return float((contrast[ring] < RATIO).sum() / max(1, ring.sum()))


def check(picture, icons):
    bg = Image.open(picture).convert("RGB").resize((1920, 1080))
    rows = {}
    for world, set_ in icons.items():
        res = []
        for i, (name, icon) in enumerate(set_.items()):
            x, y = 24 + i * PITCH, 16
            res.append((lost(icon, bg.crop((x, y, x + SIZE, y + SIZE))), name))
        rows[world] = sorted(res, reverse=True)
    return bg, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet")
    ap.add_argument("pictures", nargs="*")
    args = ap.parse_args()
    pictures = [Path(p) for p in args.pictures] or sorted((ROOT / "wallpapers").glob("*.jpg"))
    from PySide6.QtGui import QGuiApplication
    _app = QGuiApplication.instance() or QGuiApplication(["contrast"])  # noqa: F841
    icons = {w: {n: rasterize(t, n) for n in DESKTOP_ICONS} for w, t in WORLDS.items()}
    worst, strips = 0.0, []
    for pic in pictures:
        bg, rows = check(pic, icons)
        for world, res in rows.items():
            bad = [f"{n} {v:.0%}" for v, n in res if v > LIMIT]
            worst = max(worst, res[0][0])
            print(f"{pic.stem:24} {world}  worst {res[0][1]} {res[0][0]:.0%}" + (f"  LOST: {', '.join(bad)}" if bad else ""))
        if args.sheet:
            # The picture's top band with both worlds, as the desktop shows them.
            strip = bg.crop((0, 0, 24 + len(DESKTOP_ICONS) * PITCH, 2 * 96 + 28)).copy()
            d = ImageDraw.Draw(strip)
            for r, (world, set_) in enumerate(icons.items()):
                for i, icon in enumerate(set_.values()):
                    strip.paste(icon, (24 + i * PITCH, 16 + r * 96), icon)
            d.rectangle((0, strip.height - 18, 300, strip.height), fill=(0, 0, 0))
            d.text((6, strip.height - 15), pic.stem, fill=(255, 255, 255))
            strips.append(strip)
    if args.sheet and strips:
        sheet = Image.new("RGB", (strips[0].width, sum(s.height for s in strips)))
        y = 0
        for s in strips:
            sheet.paste(s, (0, y))
            y += s.height
        sheet.save(args.sheet)
    return 1 if worst > LIMIT else 0


if __name__ == "__main__":
    sys.exit(main())
