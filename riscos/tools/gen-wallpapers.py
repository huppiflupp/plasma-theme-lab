#!/usr/bin/env python3
"""Generate RISC Legacy's backdrops with the local image model.

Uses Theme Forge's ComfyUI client and GPU switch (forge/forge/comfy.py,
gpu.py) as tools: the pictures are made here once and shipped as JPEGs in
wallpapers/ with their prompt record; nothing of forge/ goes into the
theme.

    gen-wallpapers.py [stem ...]    the named pictures, or all missing ones
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "forge"))
from forge import comfy, gpu  # noqa: E402

OUT = ROOT / "wallpapers"
RAW = ROOT.parent / "wallpaper" / "risc-legacy"   # outside the repository

# stem, variant key, prompt, seed. The image model paints every word: no
# "icon", "screen", "logo", "text"; brands and the raspberry logo stay out.
STYLE = "no text, no letters, no logos, no people, calm and uncluttered, plenty of quiet space"
PICTURES = [
    ("granit", "", "A seamless close-up photograph of fine grey granite, even soft light, small dark and white "
     "grains on mid grey, matte stone surface filling the whole frame, " + STYLE, 3101),
    ("marmor", "4", "A seamless close-up photograph of pale grey-white marble with faint soft grey veins, "
     "polished but matte, diffuse daylight, the stone filling the whole frame, " + STYLE, 3102),
    ("fenland-morgen", "2026", "Documentary landscape photograph of the flat English fens near Cambridge at "
     "early morning, a straight drainage channel reflecting a pale cream sky, low mist over the fields, "
     "muted slate blue and warm cream tones, wide horizon in the lower third, " + STYLE, 3103),
    ("fenland-nacht", "2026-dark", "Landscape photograph of the flat English fens at night, a long drainage "
     "channel reflecting a deep blue sky with a thin warm brass glow at the horizon, stars faint, very dark "
     "and quiet, low horizon in the lower third, " + STYLE, 3104),
    ("himbeerlaub", "pi", "Soft-focus photograph of raspberry leaves in pastel green morning light, gentle "
     "bokeh, a few ripe red berries at the right edge, the left half calm pale green, " + STYLE, 3105),
    ("iyonix-blau", "iyonix", "Abstract photograph of deep blue light falling through frosted glass in soft "
     "diagonal bands, smooth gradients from navy to steel blue, minimal, " + STYLE, 3106),
    ("eicheln", "acorn", "Close-up nature photograph of green oak leaves and a few acorns on a mossy forest "
     "floor, soft overcast light, shallow depth of field, muted greens and browns, " + STYLE, 3107),
    ("schiefer", "graphite", "A seamless close-up photograph of dark grey slate, fine layered texture, soft "
     "even light, charcoal and graphite tones filling the whole frame, " + STYLE, 3108),
]


def main(names):
    OUT.mkdir(exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    todo = [p for p in PICTURES if (p[0] in names) if names] or \
           [p for p in PICTURES if not (OUT / f"{p[0]}.jpg").exists()]
    if not todo:
        print("nothing to do")
        return 0
    try:
        for stem, key, prompt, seed in todo:
            raw = RAW / f"{stem}.png"
            comfy.generate(prompt, 1920, 1088, seed, raw, log=print)
            im = Image.open(raw).convert("RGB").crop((0, 4, 1920, 1084))
            im.save(OUT / f"{stem}.jpg", quality=90, optimize=True, progressive=True)
            (OUT / f"{stem}.json").write_text(json.dumps(
                {"prompt": prompt, "seed": seed, "size": [1920, 1088], "model": "Z-Image Turbo (local ComfyUI)",
                 "variant": key}, indent=2, ensure_ascii=False) + "\n")
            print(f"  {stem}.jpg")
    finally:
        gpu.restore(log=print)    # the LLM service back, as forge does
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
