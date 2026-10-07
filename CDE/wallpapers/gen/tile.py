#!/usr/bin/env python3
"""Seamless material tiles and their palette tint.

seamless: the picture is blended with a copy shifted by half its size. The
blend mask is 1 in the middle and 0 at the borders, where the shifted copy
wraps around continuously; a band of low-frequency noise makes the mask
irregular so no straight blend lines show. Works for irregular materials
(moss, wool, stone), not for regular grids. Before blending, flatten()
removes vignette and lighting gradients, which would otherwise repeat as a
visible checkerboard.

tint: the luminance of the tile is mapped through three colours of a CDE
colour set (bottom shadow, background, top shadow), the way CDE draws its
backdrops in the workspace colours.

lochblech: perforated brushed aluminium, computed rather than generated,
because a regular hole grid cannot survive the blend.

Usage: tile.py seamless <in> <out> [--size 1024]
       tile.py lochblech - <out>
       tile.py tint <in> <out> --palette Copper|<CDE palette>"""
import argparse
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter


def flatten(a, size):
    """Remove vignette and lighting gradients: divide by a heavy blur,
    keep the mean colour, so only the fine structure repeats."""
    blur = np.stack([np.asarray(Image.fromarray(a[..., c].astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(size / 6))).astype(np.float32) for c in range(3)], -1)
    mean = a.reshape(-1, 3).mean(0)
    return np.clip(a / np.maximum(blur, 1) * mean, 0, 255)


def seamless(im, size=1024, seed=0):
    im = im.convert("RGB").resize((size, size), Image.LANCZOS)
    a = flatten(np.asarray(im).astype(np.float32), size)
    b = np.roll(a, (size // 2, size // 2), axis=(0, 1))
    y, x = np.mgrid[0:size, 0:size] / (size - 1)
    edge = np.minimum(np.minimum(x, 1 - x), np.minimum(y, 1 - y))     # 0 at border, 0.5 centre
    rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((size // 32, size // 32)) * 255).astype(np.uint8))
    noise = np.asarray(noise.resize((size, size), Image.BICUBIC).filter(ImageFilter.GaussianBlur(size / 40))) / 255.0
    w = np.clip((edge - 0.10 + (noise - 0.5) * 0.12) / 0.22, 0, 1)
    w = w * w * (3 - 2 * w)                                            # smoothstep
    out = a * w[..., None] + b * (1 - w[..., None])
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def lochblech(size=1024, pitch=32, hole=0.24, seed=0):
    """Perforated brushed aluminium, computed: a hole grid that divides the
    tile exactly and horizontally brushed noise that wraps around."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (size, size)).astype(np.float32)
    # brushing: blur along x only, with wrap-around so the tile stays seamless
    k = 61
    n = sum(np.roll(n, i, axis=1) for i in range(-(k // 2), k // 2 + 1)) / np.sqrt(k)
    n += np.roll(rng.normal(0, 0.4, (size, 1)).astype(np.float32), 0, axis=0)
    metal = 170 + n * 14
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    off = (np.floor(y / pitch) % 2) * pitch / 2             # staggered rows
    dx = ((x + off) % pitch) - pitch / 2
    dy = (y % pitch) - pitch / 2
    r = np.sqrt(dx * dx + dy * dy) / pitch
    edge = np.clip((r - hole) / 0.04, 0, 1)                  # 0 inside the hole
    rim = np.exp(-((r - hole - 0.02) / 0.025) ** 2) * np.clip(-dy / pitch * 4, -1, 1) * 22
    v = metal * edge + 28 * (1 - edge) + rim * edge
    rgb = np.stack([v, v * 1.005, v * 1.02], -1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def hexrgb(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def tint(im, colours):
    """colours: (dark, middle, light) as #rrggbb."""
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    L = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lo, hi = np.percentile(L, 2), np.percentile(L, 98)
    t = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)[..., None]
    d, m, l = (hexrgb(c) for c in colours)
    out = np.where(t < 0.5, d + (m - d) * (t * 2), m + (l - m) * (t * 2 - 1))
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def palette_colours(name):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import palettes
    s = palettes.copper_desktop() if name == "Copper" else palettes.load(name)[2]
    return s["bs"], s["bg"], s["ts"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("seamless", "tint", "lochblech"))
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--palette", default="Copper")
    a = ap.parse_args()
    if a.mode == "lochblech":
        lochblech(a.size).save(a.dst)
        return
    im = Image.open(a.src)
    out = seamless(im, a.size) if a.mode == "seamless" else tint(im, palette_colours(a.palette))
    out.save(a.dst)


if __name__ == "__main__":
    main()
