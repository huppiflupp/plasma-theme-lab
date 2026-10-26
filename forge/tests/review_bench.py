#!/usr/bin/env python3
"""Calibration of the wallpaper review (forge/review.py) on known pictures.

Good wallpapers shipped with the themes in this repository must get no major
issue; bad ones, made here with PIL, must get a major issue of the right kind:

    busy        confetti over the whole picture        → icon_zone
    lettering   a calm gradient with large lettering    → lettering
    watermark   a good picture under a faint watermark  → lettering
    colours     candy pastels for a dark red variant    → colours

    tests/review_bench.py [-n 2]     each case n times (the model is sampled)

Prints a table and exits with 1 if any case went wrong. Needs the LLM with
vision (FORGE_VISION or FORGE_LLM).
"""
import argparse
import os
import random
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
from forge import review  # noqa: E402

FONT = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"

RISC = {"request": "RISC OS 3 and 4 desktop (Acorn, 1990s): grey windows, cream titles, calm stone backdrops",
        "name": "RISC Legacy", "description": "RISC OS for Plasma: the iconbar, Wimp colours, stone backdrops"}
WARP = {"request": "OS/2 Warp 4 (IBM, 1996) with 1990s raytraced chrome spheres on a chessboard",
        "name": "Warp Legacy", "description": "OS/2 Warp 4 for Plasma with raytraced 1990s wallpapers"}
IRON = {"request": "Red Alert 2 (real-time strategy, Westwood 2000): Soviets",
        "name": "Iron Front", "description": "A heavy industrial theme in blood red and oxidised steel"}


def variant(name, mode, lead, look):
    return {"id": name.lower().split()[0], "name": name, "mode": mode, "lead": lead, "look": look}


V_RISC_LIGHT = variant("Classic", "light", "#eeeebb", "light grey windows, a cream title, a calm pale stone backdrop")
V_RISC_DARK = variant("Graphite", "dark", "#eeeebb", "dark grey windows, a cream title, dark slate")
V_WARP = variant("Classic", "light", "#000080", "Warp 4 grey and blue, raytraced chrome spheres on a chessboard")
V_SOVIET = variant("Soviet Steel", "dark", "#800000", "dark industrial, blood red accents on oxidised steel")


def spec_of(theme):
    return {"name": theme["name"], "description": theme["description"], "_meta": {"request": theme["request"]}}


def make_bad(tmp):
    rnd = random.Random(7)
    out = {}
    # busy: confetti of small contrasty rectangles everywhere
    im = Image.new("RGB", (1920, 1080), "#200808")
    d = ImageDraw.Draw(im)
    for _ in range(9000):
        x, y = rnd.randrange(1920), rnd.randrange(1080)
        c = rnd.choice(["#ff2020", "#ffffff", "#000000", "#ffcc00", "#801010"])
        d.rectangle([x, y, x + rnd.randrange(4, 18), y + rnd.randrange(4, 18)], fill=c)
    out["busy"] = f"{tmp}/busy.jpg"
    im.save(out["busy"], quality=92)
    # lettering: a calm dark red gradient with large words on it
    im = Image.new("RGB", (1920, 1080))
    for y in range(1080):
        ImageDraw.Draw(im).line([(0, y), (1920, y)], fill=(40 + y // 30, 10, 10))
    d = ImageDraw.Draw(im)
    d.text((960, 420), "IRON FRONT", font=ImageFont.truetype(FONT, 180), fill="#d02020", anchor="mm")
    d.text((960, 620), "www.example.com — download now", font=ImageFont.truetype(FONT, 60), fill="#e0e0e0",
           anchor="mm")
    out["lettering"] = f"{tmp}/lettering.jpg"
    im.save(out["lettering"], quality=92)
    # watermark: a good picture under a faint, repeated stock-photo mark
    im = Image.open(f"{REPO}/riscos/wallpapers/kalkstein.jpg").convert("RGBA")
    mark = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(mark)
    f = ImageFont.truetype(FONT, 64)
    for y in range(80, 1080, 260):
        for x in range(-200, 1920, 640):
            d.text((x + (y // 260) * 160, y), "© STOCKPHOTO", font=f, fill=(255, 255, 255, 110))
    im = Image.alpha_composite(im, mark).convert("RGB")
    out["watermark"] = f"{tmp}/watermark.jpg"
    im.save(out["watermark"], quality=92)
    # colours: soft candy pastels — calm, no text, but nothing of a dark red variant
    im = Image.new("RGB", (1920, 1080), "#c8f7d0")
    d = ImageDraw.Draw(im)
    for _ in range(14):
        x, y, r = rnd.randrange(1920), rnd.randrange(1080), rnd.randrange(150, 420)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.choice(["#ffd1ec", "#b8f2ff", "#fff3b0", "#d6c7ff"]))
    im = im.filter(ImageFilter.GaussianBlur(60))
    out["colours"] = f"{tmp}/colours.jpg"
    im.save(out["colours"], quality=92)
    return out


def cases(tmp):
    bad = make_bad(tmp)
    w = f"{REPO}/riscos/wallpapers"
    o = f"{REPO}/os2-warp/wallpapers"
    return [
        ("good", "kalkstein", f"{w}/kalkstein.jpg", RISC, V_RISC_LIGHT, None),
        ("good", "marmor", f"{w}/marmor.jpg", RISC, V_RISC_LIGHT, None),
        ("good", "schiefer-dark", f"{w}/schiefer-dark.jpg", RISC, V_RISC_DARK, None),
        ("good", "fenland", f"{w}/fenland.jpg", RISC, V_RISC_LIGHT, None),
        ("good", "raytracing-chrome", f"{o}/raytracing-chrome.jpg", WARP, V_WARP, None),
        ("good", "raytracing-singularity", f"{o}/raytracing-singularity.jpg", WARP, V_WARP, None),
        ("bad", "busy", bad["busy"], IRON, V_SOVIET, "icon_zone"),
        ("bad", "lettering", bad["lettering"], IRON, V_SOVIET, "lettering"),
        ("bad", "watermark", bad["watermark"], RISC, V_RISC_LIGHT, "lettering"),
        ("bad", "colours", bad["colours"], IRON, V_SOVIET, "colours"),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=1)
    a = ap.parse_args()
    rows, wrong = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        for kind, name, path, theme, v, want in cases(tmp):
            for run in range(a.n):
                verdict = review.look("wallpaper", path, spec_of(theme), v, log=lambda m: None)
                major = sorted({i["target"] for i in verdict["issues"] if i["severity"] == "major"})
                good = (not major) if kind == "good" else (want in major)
                wrong += not good
                rows.append((kind, name, run, verdict["metrics"]["icon_zone_edges"], ", ".join(major) or "—",
                             "ok" if good else "WRONG"))
    print(f"| case | picture | run | icon-zone edges | major issues | result |\n|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print(f"\n{len(rows) - wrong}/{len(rows)} as expected")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
