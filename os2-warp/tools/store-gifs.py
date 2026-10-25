#!/usr/bin/env python3
"""The GIFs of the KDE Store entry (and the README), from the screenshots
in screenshots/ and screenshots/gallery/ (taken in the VM with
tools/demo-scene.sh): each frame labelled, 1920x1080, a few seconds each.

    tools/store-gifs.py [OUT_DIR]       default screenshots/store/

The label sits in the free band at the top of the screen, between the
desktop objects and the compact box; on the screenshots with the Warp Bar
along the top it moves below the bar.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
GALLERY = SHOTS / "gallery"
FONT = str(ROOT / "fonts/IBMPlex/IBMPlexSansCondensed-SemiBold.otf")
NAVY, CYAN, PINK, LIGHT = (10, 18, 64), (58, 208, 255), (255, 79, 216), (232, 246, 255)

# The GIFs, one folder per KDE Store entry (STORE.md): file, then
# (picture, label); a picture of the screenshots folder carries the Warp
# Bar, so its label goes lower.
GIFS = {
    "classic/1-warp-legacy.gif": [
        ("warp-classic-2026-10.png", "Warp Legacy: OS/2 Warp 4's grey and blue"),
        ("gallery/classic-taskbar-box.jpg", "Taskbar and the compact box: weather, clock, gauges"),
        ("gallery/classic-taskbar-strip.jpg", "Or the full Control Strip: workspaces, launchers, gauges"),
        ("gallery/classic-warp3-tuerkis-diamond-buttons.jpg", "Warp 3's turquoise, diamond buttons"),
        ("gallery/classic-marmorpapier-corners-buttons.jpg", "Marbled paper, window-corner buttons"),
    ],
    "neon/1-neon-and-neon-blue.gif": [
        ("warp-neon-2026-10.png", "Warp Legacy Neon: navy, cyan and violet"),
        ("warp-neon-blue-2026-10.png", "Warp Legacy Neon Blue: the night in blue"),
        ("gallery/neon-blue-taskbar-box.jpg", "Taskbar and the compact box: weather, clock, gauges"),
        ("gallery/neon-blue-taskbar-strip.jpg", "Or the full Control Strip: workspaces, launchers, gauges"),
        ("gallery/neon-taskbar-box.jpg", "Neon: taskbar and compact box"),
        ("gallery/neon-taskbar-strip.jpg", "Neon: taskbar and full Control Strip"),
    ],
    "neon/2-neon-dark.gif": [
        ("gallery/neon-dunkel-horizont-pink-warp4-buttons.jpg", "Neon on a pink horizon"),
        ("gallery/neon-dunkel-rauch-pink-tube-buttons.jpg", "Pink smoke, neon-tube buttons"),
        ("gallery/neon-dunkel-nebel-indigo-diamond-buttons.jpg", "Indigo nebula, diamond buttons"),
        ("gallery/neon-dunkel-wirbel-neon-warp4-buttons.jpg", "Neon swirl"),
        ("gallery/neon-dunkel-seide-violett-corners-buttons.jpg", "Violet silk, window-corner buttons"),
        ("gallery/neon-dunkel-orbit-violett-tile-buttons.jpg", "Violet orbit, tile buttons"),
        ("gallery/neon-neon-gitter-tube-buttons.jpg", "Neon grid, neon-tube buttons"),
    ],
    "neon/3-neon-blue-dark.gif": [
        ("gallery/neon-blue-dunkel-horizont-cyan-warp4-buttons.jpg", "Neon Blue on a cyan horizon"),
        ("gallery/neon-blue-dunkel-polarlicht-cyan-tube-buttons.jpg", "Cyan aurora, neon-tube buttons"),
        ("gallery/neon-blue-dunkel-orbit-cyan-tile-buttons.jpg", "Cyan orbit, tile buttons"),
        ("gallery/neon-blue-dunkel-wellen-schwarz-warp4-buttons.jpg", "Black waves"),
        ("gallery/neon-blue-dunkel-wellen-cyan-tube-buttons.jpg", "Cyan waves, neon-tube buttons"),
        ("gallery/neon-blue-dunkel-schiefer-neon-diamond-buttons.jpg", "Neon slate, diamond buttons"),
        ("gallery/neon-blue-neon-polarlicht-glyphs-buttons.jpg", "Aurora, glyph buttons"),
    ],
}


def label(im, text, top):
    """A navy plate with a cyan rim and a pink line on top, centred."""
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 30)
    w = draw.textlength(text, font=font)
    pad, h = 18, 44
    x0 = round((im.width - w) / 2) - pad
    x1 = x0 + w + 2 * pad
    draw.rectangle((x0, top, x1, top + h + 8), fill=NAVY, outline=CYAN, width=2)
    draw.rectangle((x0 + 2, top + 2, x1 - 2, top + 5), fill=PINK)
    draw.text((x0 + pad, top + 10), text, font=font, fill=LIGHT)
    return im


def make(out, frames, ms=3000):
    images = []
    for name, text in frames:
        im = Image.open(SHOTS / name).convert("RGB")
        images.append(label(im, text, 36 if "/" not in name else 14))
    pal = [im.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
           for im in images]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=False)
    print(f"{out.name}: {len(images)} frames, {out.stat().st_size / 1e6:.1f} MB")


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else SHOTS / "store"
    out.mkdir(parents=True, exist_ok=True)
    for name, frames in GIFS.items():
        (out / name).parent.mkdir(exist_ok=True)
        make(out / name, frames)


if __name__ == "__main__":
    main()
