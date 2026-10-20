#!/usr/bin/env python3
"""Build Warp Legacy (OS/2 Warp 4 for Plasma 6) into build/.

build/ mirrors ~/.local/share, build/config ~/.config: install.sh copies
them there. Everything is generated from this file and the sources beside
it; the theme shares nothing with CDE/ or nt-legacy/ (see the repository's
CLAUDE.md).

Two variants from the same building blocks (DESIGN.md §2 and §9a): the
classic Warp 4 grey, and Neon, OS/2 at night after the user's concept.
"""
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
VERSION = "0.1.0"
# IBM Plex Sans Condensed (SIL OFL 1.1, fonts/IBMPlex, copied from CDE
# Copper's): IBM's typeface of today, narrow as Warp 4's WarpSans, which is
# IBM's and not free. Bold titles, as Warp 4's. Qt 6 font strings.
UI_FONT = "IBM Plex Sans Condensed,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
TITLE_FONT = "IBM Plex Sans Condensed,10,-1,5,700,0,0,0,0,0,0,0,0,0,0,1"
MONO_FONT = "IBM Plex Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"

# The Warp 4 default scheme, measured from the reference screenshots
# (DESIGN.md §2). Keys as tools/gen-plasma-svg.py and kvantum.py read them.
CLASSIC = dict(surface="#cccccc", window="#ffffff", panel="#cccccc",
               light="#ffffff", dark="#808080", border="#000000", checker="#fefefe",
               text="#000000", text2="#404040", inactive_text="#808080",
               title_active="#2400a8", title_active_text="#ffffff",
               title_inactive="#808080", title_inactive_text="#cccccc",
               active="#2400a8", selection="#2400a8", selection_text="#ffffff",
               hover="#d8d8d8", link="#2400a8", visited="#600080",
               warning="#a85400", error="#a80000", positive="#00802a",
               desktop="#00a0a0", panel_text="#000000",
               # Complementary: the lock screen, OSDs; OS/2's Lockup was dark.
               complementary="#101010", complementary_text="#ffffff",
               # Kvantum: OS/2 has no hover colour, pressed keeps the face.
               window_text="#000000", alt_window="#f4f4f4", button_hover="#cccccc",
               button_pressed="#cccccc", groove="#b8b8b8")

# Neon (DESIGN.md §9a): OS/2's light edge becomes cyan, the dark edge
# violet; surfaces deep navy. Measured from reference/neon-2026.png.
NEON = dict(surface="#0c1438", window="#060b24", panel="#0a1232",
            light="#48cffe", dark="#7a4dff", border="#020617", checker="#1a2a66",
            text="#e8f0ff", text2="#9fb4e0", inactive_text="#5a6a9a",
            title_active="#06123f", title_active_text="#ffffff",
            title_inactive="#0b1430", title_inactive_text="#7f8fbf",
            active="#1a6fe0", selection="#1a6fe0", selection_text="#ffffff",
            hover="#16245c", link="#3ad0ff", visited="#b48cff",
            warning="#ffb347", error="#ff5a7a", positive="#3ddc97",
            desktop="#0a152e", panel_text="#e8f0ff",
            complementary="#060b24", complementary_text="#e8f0ff",
            window_text="#e8f0ff", alt_window="#0a1230", button_hover="#16245c",
            button_pressed="#0a1232", groove="#0a1232")

# id suffix, display name, palette, decoration style, description
VARIANTS = [
    dict(key="", name="Warp Legacy", P=CLASSIC,
         style=dict(light="#ffffff", dark="#808080", ink="#000000", glyph="#000000", glow="#000000", glowWidth=0),
         wallpaper=("org.warplegacy.teal", "Warp Teal", "Warp 3's plain teal desktop"),
         picture="warp4-wirbel-violett",
         # Named, not left out: a global theme only writes the keys it
         # carries, and Neon's icons stayed after switching back.
         icons="breeze",
         description="OS/2 Warp 4: grey 3D surfaces, blue title bars"),
    dict(key="neon", name="Warp Legacy Neon", P=NEON,
         style=dict(light="#48cffe", dark="#7a4dff", ink="#020617", glyph="#ffffff", glow="#2a5cff", glowWidth=8),
         wallpaper=("org.warplegacy.neon", "Warp Night", "Deep navy for the Neon variant"),
         picture="neon-horizont", icons="WarpLegacyNeon2026",
         description="OS/2 Warp at night: navy surfaces, cyan and violet glowing edges"),
]


def ids(v):
    """Package and file names of a variant: WarpLegacy / WarpLegacyNeon …"""
    k = v["key"]
    return dict(scheme="WarpLegacy" + k.capitalize(),
                theme="warp-legacy" + (f"-{k}" if k else ""),
                lnf="org.warplegacy" + (f".{k}" if k else "") + ".desktop",
                decoration="kwin4_decoration_qml_warplegacy" + k)


def write(path, content):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata(id_, name, description, structure=None):
    plugin = {"Id": id_, "Name": name, "Description": description,
              "Version": VERSION, "License": "GPL-2.0-or-later",
              "Authors": [{"Name": "Warp Legacy contributors"}],
              "Website": "https://github.com/huppiflupp/plasma-theme-lab"}
    meta = {"KPlugin": plugin}
    if structure:
        meta["KPackageStructure"] = structure
    return meta


def rgb(value):
    return ",".join(str(int(value[i:i + 2], 16)) for i in (1, 3, 5))


def colors(v):
    P, scheme = v["P"], ids(v)["scheme"]
    lines = ["[General]", f"Name={v['name']}", f"ColorScheme={scheme}", "shadeSortColumn=false",
             "", "[KDE]", "contrast=7"]
    groups = {"Window": ("surface", "text"), "Button": ("surface", "text"),
              "View": ("window", "text"), "Selection": ("selection", "selection_text"),
              "Tooltip": ("window", "text"), "Complementary": ("complementary", "complementary_text"),
              "Header": ("surface", "text")}
    for group, (bg, fg) in groups.items():
        lines += ["", f"[Colors:{group}]"]
        for key, value in {"BackgroundNormal": bg, "BackgroundAlternate": bg,
                           "ForegroundNormal": fg, "ForegroundInactive": "text2",
                           "ForegroundActive": fg, "ForegroundLink": "link",
                           "ForegroundVisited": "visited", "ForegroundNegative": "error",
                           "ForegroundNeutral": "warning", "ForegroundPositive": "positive",
                           "DecorationFocus": "selection", "DecorationHover": "dark"}.items():
            lines.append(f"{key}={rgb(P[value])}")
    lines += ["", "[WM]",
              f"activeBackground={rgb(P['title_active'])}", f"activeForeground={rgb(P['title_active_text'])}",
              f"activeBlend={rgb(P['title_active'])}",
              f"inactiveBackground={rgb(P['title_inactive'])}", f"inactiveForeground={rgb(P['title_inactive_text'])}",
              f"inactiveBlend={rgb(P['title_inactive'])}",
              "", "[ColorEffects:Disabled]", f"Color={rgb(P['inactive_text'])}", "ColorEffect=0",
              "ContrastEffect=1", "ContrastAmount=0.5", "IntensityEffect=0",
              "", "[ColorEffects:Inactive]", "Enable=false"]
    write(f"color-schemes/{scheme}.colors", "\n".join(lines) + "\n")


def plasma(v):
    """The Plasma style: the variant's surfaces with button edges outside."""
    mod = load(ROOT / "tools/gen-plasma-svg.py", "plasma_svg")
    generator = mod.Generator(v["P"], border=1, outer_border=1, radius=0)
    theme = ids(v)["theme"]
    base = f"plasma/desktoptheme/{theme}/"
    for widget, spec in mod.WIDGETS.items():
        svg = generator.generate(widget, spec)
        path = f"{spec.get('folder', 'widgets')}/{spec.get('file', widget)}.svg"
        write(base + path, svg)
        if widget in ("panel-background", "background", "background-dialog", "tooltip"):
            for mode in ("solid", "opaque", "translucent"):
                write(f"{base}{mode}/{path}", svg)
    write(base + "metadata.json", json.dumps(metadata(theme, v["name"], v["description"]), indent=2))
    write(base + "plasmarc", "[Settings]\nFallbackTheme=default\n[ContrastEffect]\nenabled=false\n"
          "[BlurBehindEffect]\nenabled=false\n")
    # The style's own colours: the lock screen greeter took Complementary's
    # text from the style, black on the black Lockup, while kdeglobals had
    # white (VM, 20.10.2026). colors() runs first and wrote the scheme.
    shutil.copy2(OUT / f"color-schemes/{ids(v)['scheme']}.colors", OUT / base / "colors")


def decoration(v):
    """The window frame is a QML Aurorae decoration. The title colours come
    from the colour scheme; the edges and the glow, which a colour scheme
    has no words for, from Style.qml, written here per variant."""
    name = ids(v)["decoration"]
    base = f"kwin/decorations/{name}/"
    shutil.copytree(ROOT / "decoration/contents", OUT / base / "contents", dirs_exist_ok=True)
    s = v["style"]
    props = "\n".join(f'    readonly property color {k}: "{s[k]}"' for k in ("light", "dark", "ink", "glyph", "glow"))
    write(base + "contents/ui/Style.qml",
          f"import QtQuick\n\n// Written by build.py for {v['name']}.\nQtObject {{\n{props}\n"
          f"    readonly property int glowWidth: {s['glowWidth']}\n}}\n")
    write(base + "metadata.json", json.dumps(
        metadata(name, v["name"], "OS/2 Warp window frame: icon menu, inset title, close beside hide and maximize",
                 "KWin/Decoration"), indent=2))


def wallpaper(v):
    """A plain colour for now; the generated pictures follow (plan step 11)."""
    id_, name, description = v["wallpaper"]
    base = f"wallpapers/{id_}/"
    write(base + "metadata.json", json.dumps(metadata(id_, name, description), indent=2))
    write(base + "contents/images/3840x2160.svg",
          f'<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">'
          f'<rect width="3840" height="2160" fill="{v["P"]["desktop"]}"/></svg>\n')


# Generated pictures (wallpapers/, made by tools/make-wallpapers.py from the
# image model's output; prompt and seed in the JSON beside each):
# file stem, name, German name, description.
PICTURES = (
    ("warp4-wirbel-violett", "Warp Swirl Violet", "Warp-Wirbel Violett", "Soft lavender spiral in the manner of Warp 4"),
    ("warp4-wirbel-blau", "Warp Swirl Blue", "Warp-Wirbel Blau", "Silky cornflower-blue swirl"),
    ("warp3-tuerkis", "Warp Teal Felt", "Warp Türkisfilz", "Warp 3's teal as a quiet felt texture"),
    ("warp-antrieb", "Warp Drive", "Warp-Antrieb", "Star streaks at warp speed, deep blue"),
    ("neon-roehren", "Neon Tubes", "Neonröhren", "Red, blue and yellow neon tube on black"),
    ("raytracing-chrom", "Chrome Spheres", "Chromkugeln", "Ray-traced chrome spheres on a chessboard, 1990s style"),
    ("marmorpapier", "Marbled Paper", "Marmorpapier", "Grey-blue marbled paper"),
    ("stillleben-90er", "Desk, 1996", "Schreibtisch 1996", "Gouache of a 1990s desk with a CRT monitor"),
    ("wirbel-nacht-indigo", "Night Swirl Indigo", "Nachtwirbel Indigo", "Dark silk spiral in night blue and indigo"),
    ("wirbel-nacht-aubergine", "Night Swirl Aubergine", "Nachtwirbel Aubergine", "Dark smoke spiral in aubergine and plum"),
    ("wirbel-nacht-marine", "Night Swirl Navy", "Nachtwirbel Marine", "Dark navy spiral with a cyan shimmer"),
    ("neon-horizont", "Neon Horizon", "Neon-Horizont", "Planet horizon with a cyan rim of light on navy"),
    ("neon-gitter", "Neon Grid", "Neon-Gitter", "Blue perspective grid under a dark sky"),
    ("neon-polarlicht", "Neon Aurora", "Neon-Polarlicht", "Cyan and violet bands of light on navy"),
    ("neon-glasfaser", "Neon Fibres", "Neon-Glasfaser", "A fan of glowing optical fibres"),
    ("schiefer-warp", "Warp in Slate", "Warp in Schiefer", "The word Warp chiselled into dark slate"),
)


def pictures():
    for stem, name, name_de, description in PICTURES:
        id_ = f"org.warplegacy.{stem}"
        meta = metadata(id_, name, description)
        meta["KPlugin"]["Name[de]"] = name_de
        write(f"wallpapers/{id_}/metadata.json", json.dumps(meta, indent=2, ensure_ascii=False))
        target = OUT / f"wallpapers/{id_}/contents/images/3840x2160.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f"wallpapers/{stem}.jpg", target)


def icons():
    """The Neon icons: WarpLegacyNeon (icons_neon.py), drawn anew: PNGs with
    their own detail for 16-32 px, above that SVG bodies over a small
    embedded glow picture, as QtSvg draws no SVG filters; and WarpLegacyNeon2026
    (icons_neon2026.py), taken one to one from the user's concept
    (reference/neon-2026.png) and inheriting the rest from the first set."""
    sys.path.insert(0, str(ROOT))
    from icons_neon2026 import build_icons as build_2026
    build_2026(OUT / "icons")
    # WARP_SKIP_ICONS=1: leave the first set out of a quick test build (it
    # takes a while, and is reworked on its own).
    if os.environ.get("WARP_SKIP_ICONS"):
        return
    from icons_neon import build_icons
    build_icons(OUT / "icons")


def fonts():
    """Installed per user into ~/.local/share/fonts/WarpLegacy."""
    shutil.copytree(ROOT / "fonts/IBMPlex", OUT / "fonts/WarpLegacy", dirs_exist_ok=True)


def plasmoids():
    """The panels: one plasmoid each, shared by both variants (they take
    their edge colours from the colour scheme's brightness). The pieces in
    common/ (edges, buttons, launching, the window list) go into each, as a
    plasmoid can only import files of its own package."""
    for source, id_ in (("launchpad", "org.warplegacy.launchpad"), ("warpbar", "org.warplegacy.warpbar"),
                       ("controlstrip", "org.warplegacy.controlstrip"), ("tablauncher", "org.warplegacy.tablauncher")):
        target = OUT / f"plasma/plasmoids/{id_}"
        shutil.copytree(ROOT / source, target, dirs_exist_ok=True)
        shutil.copytree(ROOT / "common", target / "contents/ui", dirs_exist_ok=True)


def kvantum(v):
    """The widget style for programs. Goes to ~/.config/Kvantum, so it is
    built beside the data tree, in build/config. install.sh chooses it."""
    sys.path.insert(0, str(ROOT))
    from kvantum import build_kvantum
    build_kvantum(OUT / "config", v["P"], name=ids(v)["scheme"], comment=v["description"])


def lookandfeel(v):
    i = ids(v)
    base = f"plasma/look-and-feel/{i['lnf']}/"
    write(base + "metadata.json", json.dumps(metadata(i["lnf"], v["name"], v["description"], "Plasma/LookAndFeel"), indent=2))
    # OS/2 puts close left of hide and maximize (DESIGN.md §3): X I A.
    # Plasma takes only library, theme and BorderSize from here; install.sh
    # writes the button order and the widget style itself.
    icons = f"[kdeglobals][Icons]\nTheme={v['icons']}\n" if v.get("icons") else ""
    write(base + "contents/defaults", f"""[kdeglobals][General]
ColorScheme={i['scheme']}
font={UI_FONT}
menuFont={UI_FONT}
toolBarFont={UI_FONT}
fixed={MONO_FONT}
[kdeglobals][WM]
activeFont={TITLE_FONT}
[kdeglobals][KDE]
widgetStyle=kvantum
{icons}[plasmarc][Theme]
name={i['theme']}
[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme={i['decoration']}
ButtonsOnLeft=M
ButtonsOnRight=XIA
BorderSize=Normal
[kwinrc][Desktops]
Number=4
Rows=1
[Wallpaper]
Image=org.warplegacy.{v['picture']}
""")


def layout(v):
    """The desktop layout (layout.js) for Plasma's own shell, with the
    variant's wallpaper."""
    script = (ROOT / "layout.js").read_text().replace("@PICTURE@", f"org.warplegacy.{v['picture']}")
    write(f"plasma/look-and-feel/{ids(v)['lnf']}/contents/layouts/org.kde.plasma.desktop-layout.js", script)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for v in VARIANTS:
        colors(v)
        plasma(v)
        decoration(v)
        wallpaper(v)
        kvantum(v)
        lookandfeel(v)
        layout(v)
    pictures()
    from i18n import compile_translations
    compile_translations(OUT)
    icons()
    fonts()
    plasmoids()
    print(f"Warp Legacy {VERSION} ({', '.join(v['name'] for v in VARIANTS)}) built in {OUT}")


if __name__ == "__main__":
    main()
