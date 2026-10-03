#!/usr/bin/env python3
"""Light wallpaper -> dark variant, same composition. Neutral areas are
gradient-mapped between two night colours of the palette; accents stay
luminous. accent="warm" keeps copper-like colours (first set), "sat" keeps
any strongly saturated colour."""
import sys
import numpy as np
from PIL import Image


def rgb(c):
    return np.array([int(c[i:i+2], 16) for i in (1, 3, 5)], np.float32) / 255


def to_dark(src, dst, lo="#051419", hi="#345c64", accent="warm", keep=0.85):
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    L = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    if accent == "none":
        w = np.zeros_like(L)
    elif accent == "warm":
        w = np.clip((a[..., 0] - a[..., 2]) * 3.0, 0, 1) * np.clip(sat * 2.5, 0, 1)
    else:
        w = np.clip((sat - 0.35) * 3.0, 0, 1) * np.clip(mx * 1.5, 0, 1)
    lo, hi = rgb(lo), rgb(hi)
    night = lo + (hi - lo) * (L ** 1.8)[..., None] + (a - L[..., None]) * 0.35
    w = w[..., None]
    out = night * (1 - w) + a * keep * w
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)


if __name__ == "__main__":
    to_dark(*sys.argv[1:3], *sys.argv[3:])
