#!/usr/bin/env python3
"""4x-UltraSharp output (7680x4352) -> 3840x2160 JPEG for the wallpaper packages.
Usage: finish.py <upscaled.png> <out.jpg>"""
import sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
w, h = 3840, round(3840 * im.height / im.width)
im = im.resize((w, h), Image.LANCZOS)
top = (h - 2160) // 2
im.crop((0, top, w, top + 2160)).save(sys.argv[2], quality=90, optimize=True, subsampling=0)
