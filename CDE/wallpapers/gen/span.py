#!/usr/bin/env python3
"""Split one wide picture across two monitors of different size.

The picture is treated as a canvas in millimetres: the left screen's width,
the bezel gap, the right screen's width; as tall as the taller screen. The
screens are top-aligned. Each screen gets the part of the canvas it covers,
scaled to its own output size, so lines run straight across the bezel even
though the pixel densities differ. The strip behind the bezels is dropped.

Usage: span.py <wide image> <left.jpg> <right.jpg>
               [--left 698x393] [--right 597x336] [--gap 20] [--size 3840x2160]
Sizes are the visible image areas in mm (kscreen-doctor -j, "sizeMM")."""
import argparse
from PIL import Image


def mm(text):
    w, h = text.lower().split("x")
    return float(w), float(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wide")
    ap.add_argument("left_out")
    ap.add_argument("right_out")
    ap.add_argument("--left", type=mm, default=(698, 393))
    ap.add_argument("--right", type=mm, default=(597, 336))
    ap.add_argument("--gap", type=float, default=20)
    ap.add_argument("--size", type=mm, default=(3840, 2160))
    a = ap.parse_args()

    (lw, lh), (rw, rh) = a.left, a.right
    canvas_w, canvas_h = lw + a.gap + rw, max(lh, rh)
    im = Image.open(a.wide).convert("RGB")
    # Fit the canvas into the picture: crop the picture to the canvas aspect.
    scale = min(im.width / canvas_w, im.height / canvas_h)       # px per mm
    ox = (im.width - canvas_w * scale) / 2
    oy = (im.height - canvas_h * scale) / 2
    out_w, out_h = int(a.size[0]), int(a.size[1])
    for x0, w, h, path in ((0, lw, lh, a.left_out), (lw + a.gap, rw, rh, a.right_out)):
        box = (ox + x0 * scale, oy, ox + (x0 + w) * scale, oy + h * scale)
        part = im.resize((out_w, out_h), Image.LANCZOS, box=box)
        part.save(path, quality=90, optimize=True, subsampling=0)
        print(f"{path}: {w:g}x{h:g} mm aus {box[2] - box[0]:.0f}x{box[3] - box[1]:.0f} px")


if __name__ == "__main__":
    main()
