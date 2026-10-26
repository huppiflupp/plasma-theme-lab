"""Checks on the finished package — what a generator can silently get wrong."""
import json
import os
import re
import subprocess
import sys

from . import aurorae, frames
from .palette import contrast

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECO_IDS = [f"{p}-{part}" for p in ("decoration", "decoration-inactive") for part in frames.PARTS] + \
    ["decoration-maximized-center", "decoration-maximized-inactive-center"]


def run(pkg, variants):
    errors, notes = [], []
    lint = subprocess.run([sys.executable, f"{HERE}/tools/lint-plasma-svg.py"] +
                          [f"{pkg}/plasma/desktoptheme/{v.id}" for v in variants],
                          capture_output=True, text=True)
    if lint.returncode != 0:
        errors.append("lint-plasma-svg: " + (lint.stdout + lint.stderr).strip()[-1500:])
    # Generated scripts: syntax and no control characters (a "\1" in a
    # Python template once silently became the byte 0x01 — sed then replaced wrongly).
    for sh in ("install.sh", "uninstall.sh", "install-system.sh"):
        text = open(f"{pkg}/{sh}", encoding="utf-8").read()
        if any(ord(ch) < 32 and ch not in "\n\t" for ch in text):
            errors.append(f"{sh}: contains control characters")
        r = subprocess.run(["bash", "-n", f"{pkg}/{sh}"], capture_output=True, text=True)
        if r.returncode != 0:
            errors.append(f"{sh}: Syntaxfehler {r.stderr.strip()[:200]}")
    for v in variants:
        P = v.P
        base = f"{pkg}/aurorae/themes/{v.camel}"
        r = frames.renderer(open(f"{base}/decoration.svg").read())
        missing = [i for i in DECO_IDS if not r.elementExists(i)]
        if missing:
            errors.append(f"{v.id}: Aurorae ids missing: {missing}")
        for b in aurorae.BUTTONS:
            rb = frames.renderer(open(f"{base}/{b}.svg").read())
            miss = [s for s in aurorae.BUTTON_STATES if not rb.elementExists(f"{s}-center")]
            if miss:
                errors.append(f"{v.id}: Knopf {b} ohne {miss}")
        for path in [f"{pkg}/color-schemes/{v.camel}.colors", f"{pkg}/konsole/{v.camel}.colorscheme",
                     f"{pkg}/plasma/look-and-feel/{v.lnf}/contents/defaults",
                     f"{pkg}/plasma/look-and-feel/{v.lnf}/contents/splash/Splash.qml",
                     f"{pkg}/wallpapers/{v.id}/contents/images/1920x1080.jpg",
                     f"{pkg}/system/plymouth/{v.id}/{v.id}.script",
                     f"{pkg}/system/grub/{v.camel}/theme.txt"]:
            if not os.path.exists(path):
                errors.append(f"fehlt: {os.path.relpath(path, pkg)}")
        for jf in [f"{pkg}/plasma/look-and-feel/{v.lnf}/metadata.json",
                   f"{pkg}/plasma/desktoptheme/{v.id}/metadata.json",
                   f"{pkg}/wallpapers/{v.id}/metadata.json"]:
            try:
                json.load(open(jf))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{os.path.relpath(jf, pkg)}: {e}")
        theme = open(f"{pkg}/system/grub/{v.camel}/theme.txt").read()
        for img in re.findall(r'"([\w*.-]+\.png)"', theme):
            if "*" not in img and not os.path.exists(f"{pkg}/system/grub/{v.camel}/{img}"):
                errors.append(f"GRUB: picture {img} missing")
        if theme.count(".pf2") or not re.search(r'item_font = "[^"]+ \d+"', theme):
            errors.append("GRUB: implausible item_font name")
        # Contrasts on the finished palette (after derivation)
        # hard = error, soft = note (panel text comes from the colour scheme
        # and is not always the text colour on light panels).
        for fg, bg, need, hard in [("text", "surface", 4.5, True), ("text", "window", 4.5, True),
                                   ("selection_text", "selection", 4.5, True),
                                   ("title_active_text", "title_active", 4.5, True),
                                   ("title_inactive_text", "title_inactive", 3.0, True),
                                   ("text2", "surface", 3.0, True), ("link", "window", 4.5, True),
                                   ("text", "panel", 4.5, True), ("text", "hover", 4.5, True)]:
            k = contrast(P[fg], P[bg])
            if k < need:
                (errors if hard else notes).append(f"{v.id}: {fg} auf {bg} {k:.1f}:1 (Soll {need})")
        # icon theme complete? (only when built)
        ibase = f"{pkg}/icons/{v.camel}Icons"
        if os.path.isdir(ibase):
            from . import iconset
            for size in iconset.SIZES:
                for icon, (ctx, _, aliases) in iconset.ICONS.items():
                    for n in [icon] + aliases:
                        if not os.path.exists(f"{ibase}/{size}x{size}/{ctx}/{n}.png"):
                            errors.append(f"{v.id}: icon missing {size}x{size}/{ctx}/{n}.png")
                            break
            if not os.path.exists(f"{ibase}/index.theme"):
                errors.append(f"{v.id}: index.theme missing")
        # rough check of the splash QML: balanced braces
        qml = open(f"{pkg}/plasma/look-and-feel/{v.lnf}/contents/splash/Splash.qml").read()
        if qml.count("{") != qml.count("}"):
            errors.append(f"{v.id}: Splash.qml braces unbalanced")
    return errors, notes
