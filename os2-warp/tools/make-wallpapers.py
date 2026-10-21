#!/usr/bin/env python3
"""The raw 3840x2160 PNGs from the image model (wallpaper/warp-legacy/,
outside the repository) to the JPEGs the theme ships (os2-warp/wallpapers/),
with each picture's prompt record beside it. Run after a new generation."""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
RAW = HERE.parent / "wallpaper" / "warp-legacy"
OUT = HERE / "wallpapers"


def main(names=None):
    """names: the stems to take (the user's choice); none: every picture."""
    OUT.mkdir(exist_ok=True)
    for png in sorted(RAW.glob("*.png")):
        if names and png.stem not in names:
            continue
        if png.name == "uebersicht.png":
            continue
        image = Image.open(png).convert("RGB")
        assert image.size == (3840, 2160), (png, image.size)
        image.save(OUT / f"{png.stem}.jpg", quality=90, optimize=True, progressive=True)
        record = png.with_suffix(".json")
        if record.exists():
            shutil.copy2(record, OUT / record.name)
        print(f"  {png.stem}.jpg  {(OUT / f'{png.stem}.jpg').stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
