#!/usr/bin/env python3
"""Generate RISC Legacy's backdrops with the image model on ai395.

Every backdrop is a pair: a day picture and a night picture of the same
scene, for Plasma's day/night switching (the wallpaper package's images/
and images_dark/, build.py). One of the two is painted from a prompt, the
other from that picture (image to image, the same composition in other
light), so the switch changes the light, not the place.

Uses Theme Forge's ComfyUI client (forge/forge/comfy.py: Krea-2 Turbo,
ai395's login) as a tool: the pictures are made here once and shipped as
JPEGs in wallpapers/ with their prompt record; nothing of forge/ goes into
the theme.

    gen-wallpapers.py [stem[-dark] ...]    the named pictures, or all missing ones

Night pictures keep the band where the desktop icons sit (the top) out of
the deepest shadows: black outlines need a background of at least ~0.04
relative luminance to show (tools/contrast-sheet.py checks the result).
"""
import base64
import json
import os
import sys
import uuid
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "forge"))
os.environ.setdefault("FORGE_COMFY", "http://192.168.178.54:8188")
from forge import comfy  # noqa: E402

OUT = ROOT / "wallpapers"
RAW = ROOT.parent / "wallpaper" / "risc-legacy"   # outside the repository
W, H = 1920, 1088

# The image model paints every word: no "icon", "screen", "logo", "text";
# brands and the raspberry logo stay out.
STYLE = ("no text, no letters, no logos, no people, calm and uncluttered, the upper third especially quiet "
         "and even, plenty of empty space")
NIGHT = ("the same scene at night in cool moonlight and soft blue dusk, dark but with clearly visible mid "
         "tones, nothing pitch black, gentle and even, ")
DAY = "the same scene in bright soft daylight, light and airy, pale even tones, "

# stem: (first, day prompt, night prompt, seed, denoise of the second).
# first = "day" or "night": which one is painted from the prompt (None:
# a picture kept from before, KEEP). The other comes from it: graded into
# the other light, then worked over by the model at `denoise`. A stone
# stays graded only (denoise None): the model would invent new veins and
# grain, and the same stone at night is the same picture, darker and
# cooler. Scenes need the model for the light in the sky.
PAIRS = {
    "kalkstein": ("day", "A close-up photograph of smooth honed pale grey limestone, an almost uniform matte "
                  "surface with very faint soft clouding, no grains, no speckles, diffuse even daylight, the "
                  "stone filling the whole frame, " + STYLE, None, 3201, None),
    "marmor": ("day", None, None, 3102, None),
    "fenland": ("day", None, "Landscape photograph of the flat English fens at late blue hour, a long "
                "drainage channel reflecting a deep blue sky with a thin warm brass glow at the horizon, "
                + NIGHT + "low horizon in the lower third, " + STYLE, 3103, 0.45),
    "himbeerlaub": ("day", None, "Soft-focus photograph of raspberry leaves at dusk, " + NIGHT
                    + "deep muted green with a few dark red berries at the right edge, the left half calm, "
                    + STYLE, 3105, 0.4),
    "iyonix-glas": ("night", None, None, 3106, None),
    "eicheln": ("day", None, "Close-up nature photograph of oak leaves and a few acorns on a mossy forest "
                "floor at dusk, " + NIGHT + "muted deep greens and browns, shallow depth of field, " + STYLE,
                3107, 0.4),
    "schiefer": ("night", None, None, 3108, None),
}
# Pictures already shipped that become one half of a pair (old name → new).
KEEP = {"marmor": "marmor", "fenland-morgen": "fenland", "himbeerlaub": "himbeerlaub", "eicheln": "eicheln",
        "iyonix-blau": "iyonix-glas-dark", "schiefer": "schiefer-dark"}
FLOOR = 0.045   # the icon band's mean relative luminance at night, at least


def upload(path):
    """Put a picture into ComfyUI's input folder (multipart, ai395's login)."""
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + path.read_bytes() + \
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n"
         f"--{boundary}--\r\n").encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    user, pw = comfy._credentials()
    if user:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
    req = urllib.request.Request(comfy.BASE + "/upload/image", data=body, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["name"]


def grade(src, dst, night):
    """The source in the other light before the model works it over: at
    image to image the model keeps the source's brightness and only
    re-textures, so the light has to be there already."""
    a = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    if night:   # darker, cooler, the mid tones kept apart
        a = (a ** 1.5) * 0.42 * np.array([0.82, 0.92, 1.12])
    else:       # lighter, airier, a little less colour
        a = 1 - (1 - a) ** 2.2
        a = a * 0.85 + 0.15
        a = a * 0.85 + a.mean(axis=2, keepdims=True) * 0.15
    Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8)).save(dst)
    return dst


def paint(prompt, seed, dst, source=None, denoise=1.0):
    """Krea-2 from the prompt, or from `source` (image to image)."""
    orig = comfy.krea2

    def graph(p, w, h, s, prefix, steps=8):
        wf = orig(p, w, h, s, prefix, steps)
        if source is not None:
            wf["20"] = {"class_type": "LoadImage", "inputs": {"image": upload(source)}}
            wf["21"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["20", 0], "vae": ["12", 0]}}
            wf["3"]["inputs"].update(latent_image=["21", 0], denoise=denoise)
            del wf["5"]
        return wf
    comfy.krea2 = graph
    try:
        comfy.generate(prompt, W, H, seed, dst, log=print)
    finally:
        comfy.krea2 = orig


def luminance(im):
    c = np.asarray(im.convert("RGB")).astype(float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def band(im):
    """The mean relative luminance where the desktop icons sit."""
    return float(luminance(im.crop((0, 0, 1400, 200))).mean())


def lift(im):
    """Lift a night picture's shadows until the icon band is light enough."""
    src = np.asarray(im).astype(float) / 255
    gamma = 1.0
    while band(im) < FLOOR and gamma > 0.5:
        gamma -= 0.05
        im = Image.fromarray((src ** gamma * 255).clip(0, 255).astype(np.uint8))
    return im


def finish(raw, stem, record):
    im = Image.open(raw).convert("RGB").crop((0, 4, 1920, 1084))
    if stem.endswith("-dark"):
        im = lift(im)
    im.save(OUT / f"{stem}.jpg", quality=90, optimize=True, progressive=True)
    (OUT / f"{stem}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"  {stem}.jpg  icon band {band(im):.3f}")


def adopt():
    """The pictures kept from before: renamed into their pair once."""
    for old, new in KEEP.items():
        for d, ext in ((OUT, ".jpg"), (OUT, ".json"), (RAW, ".png")):
            if (d / f"{old}{ext}").exists() and not (d / f"{new}{ext}").exists():
                (d / f"{old}{ext}").rename(d / f"{new}{ext}")


def main(names):
    OUT.mkdir(exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    adopt()
    todo = []
    for stem, (first, day, night, seed, denoise) in PAIRS.items():
        a, b = (stem, f"{stem}-dark") if first == "day" else (f"{stem}-dark", stem)
        prompt_a, prompt_b = (day, night) if first == "day" else (night, day)
        for s, prompt, src in ((a, prompt_a, None), (b, prompt_b, a)):
            if src is None and prompt is None:
                continue          # kept from before
            if (names and s in names) or (not names and not (OUT / f"{s}.jpg").exists()):
                todo.append((s, prompt, src, seed, denoise))
    if not todo:
        print("nothing to do")
        return 0
    for s, prompt, src, seed, denoise in todo:
        raw = RAW / f"{s}.png"
        record = {"prompt": prompt, "seed": seed, "size": [W, H], "model": "Krea-2 Turbo (ComfyUI on ai395)"}
        if src is None:
            paint(prompt, seed, raw)
        else:
            source = RAW / f"{src}.png"
            if not source.exists():   # only the shipped JPEG: back to the model's size
                Image.open(OUT / f"{src}.jpg").resize((W, H)).save(source)
            graded = grade(source, RAW / f"{s}-graded.png", s.endswith("-dark"))
            record.update(source=f"{src}.jpg", graded=True, denoise=denoise)
            if denoise is None:
                raw = graded
                record.update(prompt=None, seed=None, model=None)
            else:
                paint(prompt, seed, raw, graded, denoise)
        finish(raw, s, record)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
