"""Spezifikation → installierbares Paket.

Alles hier ist deterministisch: dieselbe spec.json und dieselben Bilder
ergeben byte-gleich dasselbe Paket. Nur die Werkzeuge (ComfyUI, Blender)
erzeugen Bilder, und die werden in assets/ zwischengespeichert.
"""
import json
import os
import re
import shutil

from PIL import Image, ImageDraw, ImageFilter

import zlib

from . import artplan, aurorae, boot, comfy, emblem, fonts, icons, installers, material, plasmasvg
from .palette import derive, mix, on, readable, rgb, shift

VERSION = "0.1.0"
ICONS = {"dark": "breeze-dark", "light": "breeze"}
# Was in der Spezifikation als Buchstaben steht, schreibt KWin genauso
# in kwinrc (ButtonsOnLeft/Right) — die Kürzel sind KDE-eigen.


def camel(*parts):
    return "".join(w.capitalize() for p in parts for w in re.split(r"[-_ ]+", p) if w)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class Variant:
    def __init__(self, spec, v):
        self.spec, self.v = spec, v
        self.id = f"{spec['id']}-{v['id']}"            # plasma style, plymouth
        self.camel = camel(spec["id"], v["id"])         # colors, aurorae, grub
        self.name = f"{spec['name']} {v['name']}"
        self.mode = v["mode"]
        self.P = derive(v["colors"], v["mode"])
        self.lnf = f"org.themeforge.{self.id}"


# --------------------------------------------------------------------------
def colors(var, out):
    P = var.P
    def c(k): return ",".join(str(x) for x in rgb(P[k]))
    lines = ["[General]", f"Name={var.name}", f"ColorScheme={var.camel}", "shadeSortColumn=true",
             "", "[KDE]", "contrast=4"]
    groups = {"Window": ("surface", "text"), "Button": ("surface", "text"),
              "View": ("window", "text"), "Selection": ("selection", "selection_text"),
              "Tooltip": ("window", "text"), "Complementary": ("panel", "panel_text"),
              "Header": ("surface", "text")}
    P = dict(P, panel_text=on(P["panel"]) if var.mode == "light" else P["text"])
    for group, (bg, fg) in groups.items():
        lines += ["", f"[Colors:{group}]"]
        alt = mix(P[bg], P[fg], 0.04)
        for key, val in [("BackgroundNormal", c(bg)), ("BackgroundAlternate", ",".join(str(x) for x in rgb(alt))),
                         ("ForegroundNormal", c(fg)), ("ForegroundInactive", c("text2") if fg == "text" else c(fg)),
                         ("ForegroundActive", c("glow") if group != "Selection" else c(fg)),
                         ("ForegroundLink", c("link")), ("ForegroundVisited", c("visited")),
                         ("ForegroundNegative", c("error")), ("ForegroundNeutral", c("warning")),
                         ("ForegroundPositive", c("positive")), ("DecorationFocus", c("accent")),
                         ("DecorationHover", c("glow"))]:
            lines.append(f"{key}={val}")
    lines += ["", "[WM]", f"activeBackground={c('title_active')}", f"activeBlend={c('title_active')}",
              f"activeForeground={c('title_active_text')}", f"inactiveBackground={c('title_inactive')}",
              f"inactiveBlend={c('title_inactive')}", f"inactiveForeground={c('title_inactive_text')}",
              "", "[ColorEffects:Disabled]", "ColorEffect=0", "ContrastEffect=1", "ContrastAmount=0.55",
              "IntensityEffect=0", "", "[ColorEffects:Inactive]", "Enable=false"]
    write(f"{out}/color-schemes/{var.camel}.colors", "\n".join(lines) + "\n")


def konsole(var, out):
    P = var.P
    bg = P["window"]
    fg = P["text"]
    dark = var.mode == "dark"
    # ANSI-Farben: feste Töne, an den Hintergrund angepasst; Blau und Cyan
    # leiten sich von glow/accent ab, damit das Terminal zum Theme gehört.
    base = ["#000000", "#cc3333", "#44aa44", "#cc9933", P["accent"], "#aa55aa", P["glow"], "#cccccc"]
    lines = [f"[General]\nDescription={var.name}\nOpacity=1\n"]

    def entry(name, col):
        lines.append(f"[{name}]\nColor={','.join(str(x) for x in rgb(col))}\n")
    entry("Background", bg)
    entry("BackgroundIntense", shift(bg, 0.04 if dark else -0.04))
    entry("Foreground", fg)
    entry("ForegroundIntense", shift(fg, 0.1 if dark else -0.1))
    for i, col in enumerate(base):
        col = readable(col, bg, 3.0) if i not in (0, 7) else col
        if i == 0 and dark:
            col = shift(bg, 0.12)
        entry(f"Color{i}", col)
        entry(f"Color{i}Intense", shift(col, 0.15 if dark else -0.1))
    write(f"{out}/konsole/{var.camel}.colorscheme", "\n".join(lines))
    # Das Profil gehört dem Theme; Standard wird es erst durch install.sh --apply.
    write(f"{out}/konsole/{var.camel}.profile",
          f"[Appearance]\nColorScheme={var.camel}\n\n[General]\nName={var.name}\nParent=FALLBACK/\n")


def desktoptheme(var, out, spec, textures=None):
    sh = spec["shape"]
    P = var.P
    raised = sh["bevel"] == "raised"
    radius = sh["corner_size"] if sh["corner"] != "square" else 0
    g = plasmasvg.Generator(P, border=sh["bevel_width"] if raised else 0,
                            style="bevel" if raised else "flat", outer_border=sh["outer_border"],
                            corner_style=sh["corner"], radius=radius, corner=max(6, radius + 2),
                            glow=1 if sh["edge_glow"] else 0, textures=textures)
    base = f"{out}/plasma/desktoptheme/{var.id}"
    svgs = {}
    for widget, ws in plasmasvg.WIDGETS.items():
        svg = g.generate(widget, ws)
        path = f"{ws.get('folder', 'widgets')}/{ws.get('file', widget)}.svg"
        svgs[widget] = svg
        write(f"{base}/{path}", svg)
        if widget in ("panel-background", "background", "background-dialog", "tooltip"):
            variants = ("solid", "translucent") if widget == "background" else ("solid", "translucent", "opaque")
            for mode in variants:
                write(f"{base}/{mode}/{path}", svg)
    meta = {"KPlugin": {"Authors": [{"Name": "Theme Forge"}], "Description": spec["description"],
                        "EnabledByDefault": True, "Id": var.id, "License": "GPL-2.0-or-later",
                        "Name": var.name, "Version": VERSION},
            "X-Plasma-API": "5.0"}
    write(f"{base}/metadata.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    write(f"{base}/plasmarc", "[ContrastEffect]\nenabled=false\n\n[BlurBehindEffect]\nenabled=false\n\n"
                              "[AdaptiveTransparency]\nenabled=false\n")
    return svgs


def decoration(var, out, spec, textures=None):
    sh, d = spec["shape"], spec["decoration"]
    th, border, bsize = d["title_height"], d["border"], d["button_size"]
    if textures:
        # Materialmodus: wuchtige Bleche wie die Seitenleiste im Spiel
        th, border = max(th, 32), max(border, 9)
        bsize = min(max(bsize, 20), th - 8)
    a = aurorae.Aurorae(var.P, title_height=th, border=border,
                        outer=max(1, sh["outer_border"]), bevel=max(1, sh["bevel_width"]),
                        button_size=bsize, corner_style=sh["corner"], textures=textures,
                        radius=sh["corner_size"] if sh["corner"] != "square" else 0,
                        glow=1 if sh["edge_glow"] else 0, button_shape=d["button_shape"],
                        title_align=d["title_align"])
    base = f"{out}/aurorae/themes/{var.camel}"
    write(f"{base}/decoration.svg", a.decoration())
    for b in aurorae.BUTTONS:
        write(f"{base}/{b}.svg", a.button(b))
    write(f"{base}/{var.camel}rc", a.rc())
    write(f"{base}/metadata.desktop", a.metadata(var.camel, var.name, spec["description"], VERSION))
    return a


def wallpaper(var, out, assets, spec, use_comfy=True, log=print, seed=None, prompt=None, index=0, title=None):
    """Hintergrundbild: ComfyUI, sonst prozedural. Liefert den Pfad (1920×1080 JPEG)."""
    suffix = f"-{index + 1}" if index else ""
    raw = f"{assets}/wallpaper-{var.v['id']}{suffix}.png"
    prompt = prompt or var.v["wallpaper_prompt"]
    source = "cache"
    # Der Cache gilt nur für denselben Prompt — sonst blieb nach neuem Art-Plan
    # das alte Bild stehen. Prozedurale Bilder ersetzt ein späterer Lauf mit ComfyUI.
    stamp = raw[:-4] + ".prompt"
    old = open(stamp).read() if os.path.exists(stamp) else None
    if os.path.exists(raw) and (old != prompt or (old is None and use_comfy)):
        os.remove(raw)
    if not os.path.exists(raw):
        if use_comfy:
            try:
                comfy.generate(prompt, 1920, 1088,
                               seed if seed is not None else zlib.crc32(var.id.encode()) % 10**6, raw, log=log)
                source = "comfyui"
                write(stamp, prompt)
            except Exception as e:  # noqa: BLE001
                log(f"  ComfyUI nicht verfügbar ({str(e)[:160]}) — prozeduraler Hintergrund")
        if not os.path.exists(raw):
            procedural_wallpaper(var.P, raw)
            source = "procedural"
    im = Image.open(raw).convert("RGB")
    im = im.crop((0, (im.height - 1080) // 2, 1920, (im.height - 1080) // 2 + 1080)) if im.height > 1080 else im.resize((1920, 1080))
    base = f"{out}/wallpapers/{var.id}{suffix}"
    os.makedirs(f"{base}/contents/images", exist_ok=True)
    im.save(f"{base}/contents/images/1920x1080.jpg", quality=92)
    im.resize((2560, 1440), Image.LANCZOS).save(f"{base}/contents/images/2560x1440.jpg", quality=90)
    im.resize((400, 225), Image.LANCZOS).save(f"{base}/contents/screenshot.png")
    write(f"{base}/metadata.json", json.dumps(
        {"KPlugin": {"Authors": [{"Name": "Theme Forge"}], "Id": f"{var.id}{suffix}", "License": "CC-BY-SA-4.0",
                     "Name": f"{var.name} — {title}" if title else var.name}}, indent=2) + "\n")
    return f"{base}/contents/images/1920x1080.jpg", source


def procedural_wallpaper(P, dst, w=1920, h=1088):
    """Ersatz ohne Bildmodell: Verlauf, feines Raster in glow, Vignette."""
    top, bottom = rgb(shift(P["desktop"], 0.06)), rgb(P["desktop"])
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    col = rgb(P["glow"]) + (28,)
    for x in range(0, w, 64):
        g.line([(x, 0), (x, h)], fill=col)
    for y in range(0, h, 64):
        g.line([(0, y), (w, y)], fill=col)
    im = Image.alpha_composite(im.convert("RGBA"), grid)
    vign = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vign).ellipse([-w * 0.2, -h * 0.3, w * 1.2, h * 1.3], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    im = Image.composite(im, dark, vign)
    im.convert("RGB").save(dst)


def lookandfeel(var, out, spec, wall, emblem_png, font_family, icon_theme=None):
    base = f"{out}/plasma/look-and-feel/{var.lnf}"
    d = spec["decoration"]
    meta = {"KPackageStructure": "Plasma/LookAndFeel",
            "KPlugin": {"Authors": [{"Name": "Theme Forge"}], "Description": spec["description"],
                        "Id": var.lnf, "License": "GPL-2.0-or-later", "Name": var.name,
                        "Version": VERSION},
            "Keywords": "Desktop;Workspace;Appearance;Look and Feel;", "X-Plasma-APIVersion": "2"}
    write(f"{base}/metadata.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    # Jeder Schlüssel ausdrücklich — plasma-apply-lookandfeel schreibt nur,
    # was hier steht; Werte eines vorher angewandten Themes blieben sonst.
    # Dekoration: org.kde.kwin.aurorae, NICHT .v2 (bricht Plasma 6.0–6.5).
    write(f"{base}/contents/defaults", f"""[kdeglobals][KDE]
widgetStyle=Breeze

[kdeglobals][General]
ColorScheme={var.camel}

[kdeglobals][Icons]
Theme={icon_theme or ICONS[var.mode]}

[kdeglobals][WM]
activeFont={font_family},10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1

[kcminputrc][Mouse]
cursorTheme=breeze_cursors

[plasmarc][Theme]
name={var.id}

[Wallpaper]
Image={var.id}

[ksplashrc][KSplash]
Theme={var.lnf}
Engine=KSplashQML

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme=__aurorae__svg__{var.camel}
ButtonsOnLeft={d['buttons_left'].replace('_', '')}
ButtonsOnRight={d['buttons_right'].replace('_', '')}
""")
    sp = f"{base}/contents/splash"
    os.makedirs(f"{sp}/images", exist_ok=True)
    Image.open(wall).convert("RGB").resize((1920, 1080)).save(f"{sp}/images/background.jpg", quality=88)
    Image.open(emblem_png).resize((256, 256), Image.LANCZOS).save(f"{sp}/images/emblem.png")
    P = var.P
    write(f"{sp}/Splash.qml", f"""import QtQuick

// Generiert von Theme Forge. stage läuft von 1 bis 6.
Rectangle {{
    id: root
    color: "{P['desktop']}"
    property int stage

    Image {{
        anchors.fill: parent
        source: "images/background.jpg"
        fillMode: Image.PreserveAspectCrop
        opacity: 0.55
    }}
    Column {{
        anchors.centerIn: parent
        spacing: 22
        Image {{
            anchors.horizontalCenter: parent.horizontalCenter
            source: "images/emblem.png"
            width: 160; height: 160
            smooth: true
        }}
        Text {{
            anchors.horizontalCenter: parent.horizontalCenter
            text: "{spec['emblem']['label'].upper()}"
            color: "{readable(P['text'], P['desktop'])}"
            font.family: "{font_family}"
            font.pixelSize: 34
            font.letterSpacing: 4
        }}
        Rectangle {{
            anchors.horizontalCenter: parent.horizontalCenter
            width: 360; height: 12
            color: "{P['window']}"
            border.color: "{P['border']}"
            border.width: 1
            Rectangle {{
                anchors {{ left: parent.left; top: parent.top; bottom: parent.bottom; margins: 2 }}
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "{P['accent']}"
                Behavior on width {{ NumberAnimation {{ duration: 200 }} }}
            }}
        }}
    }}
}}
""")
    return base


def build(spec, out, use_comfy=True, log=print, seed=None, plan=None):
    """Baut das komplette Paket nach out/package. Liefert einen Bericht."""
    assets = f"{out}/assets"
    pkg = f"{out}/package"
    if os.path.exists(pkg):
        shutil.rmtree(pkg)
    os.makedirs(assets, exist_ok=True)
    report = {"variants": {}, "tools": {}}
    family, ttf_var = fonts.fetch(spec["font"])
    _, ttf = fonts.static(spec["font"])      # für alles Gerasterte (GRUB, Plymouth)
    os.makedirs(f"{pkg}/fonts", exist_ok=True)
    shutil.copy(ttf_var, f"{pkg}/fonts/{spec['font']}.ttf")
    pictures = None
    if plan and use_comfy:
        pictures = icons.paint_checked(plan, spec, assets, plan.get("private", False), log=log)
    for v in spec["variants"]:
        var = Variant(spec, v)
        log(f"Variante {var.name} ({var.mode})")
        colors(var, pkg)
        konsole(var, pkg)
        deco_tex = plasma_tex = None
        vplan = (plan or {}).get("variants", {}).get(v["id"])
        if vplan:
            raw = material.texture(vplan["texture"], f"{assets}/texture-{v['id']}.png", log=log) \
                if use_comfy else material.texture("", f"{assets}/texture-{v['id']}-proc.png", log=log)
            P = var.P
            deco_tex = {"title_active": material.tint(raw, P["title_active"], 0.18),
                        "title_inactive": material.tint(raw, P["title_inactive"], 0.12),
                        "frame": material.tint(raw, mix(P["title_active"], P["surface"], 0.55), 0.18)}
            plasma_tex = {"panel-background": material.tint(raw, P["panel"], 0.14),
                          "background-dialog": material.tint(raw, P["surface"], 0.08)}
        desktoptheme(var, pkg, spec, plasma_tex)
        decoration(var, pkg, spec, deco_tex)
        em = f"{assets}/emblem-{v['id']}.png"
        if os.path.exists(em):
            tool = "cache"
        else:
            em, tool = emblem.render(spec["emblem"]["shape"], spec["emblem"]["render"], var.P, em, log=log)
        if vplan:
            walls = [wallpaper(var, pkg, assets, spec, use_comfy, log, seed,
                               prompt=artplan.wallpaper_prompt(w["prompt"], spec.get("_meta", {}).get("request", ""),
                                                               plan.get("private", False)),
                               index=i, title=w["title"])
                     for i, w in enumerate(vplan["wallpapers"])]
            wall, wsrc = walls[0]
        else:
            wall, wsrc = wallpaper(var, pkg, assets, spec, use_comfy, log, seed)
        icon_theme = icons.build_theme(var, pictures, em, pkg, "breeze-dark" if var.mode == "dark" else "breeze") \
            if pictures else None
        lookandfeel(var, pkg, spec, wall, em, family, icon_theme)
        boot.plymouth(var, pkg, spec, wall, em, ttf)
        boot.grub(var, pkg, spec, wall, em, ttf)
        report["variants"][v["id"]] = {"emblem": tool, "wallpaper": wsrc, "palette": var.P}
    installers.write_all(spec, pkg, [Variant(spec, v) for v in spec["variants"]])
    write(f"{pkg}/spec.json", json.dumps({k: v for k, v in spec.items() if k != "_meta"},
                                         indent=2, ensure_ascii=False) + "\n")
    return report
