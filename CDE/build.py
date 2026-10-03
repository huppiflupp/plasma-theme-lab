#!/usr/bin/env python3
"""Build CDE / Copper from vector sources. Run in the lab VM."""
import argparse
import importlib.util
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
VERSION = "0.2.0"
# Qt 6 font strings (16 fields): family, size, pixel, hint, weight, style, ...
UI_FONT = "IBM Plex Sans Condensed,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
TITLE_FONT = "IBM Plex Sans Condensed,10,-1,5,600,0,0,0,0,0,0,0,0,0,0,1"
MONO_FONT = "IBM Plex Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
KONSOLE_FONT = "IBM Plex Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
P = dict(flaeche="#86a4aa", fenster="#c4d2d0", panel="#2e7180",
         kopf_aktiv="#e8874f", kopf_inaktiv="#649099", text="#10262b",
         text2="#38565c", aktiv="#e8874f", auswahl="#e8874f", auswahl_text="#10262b",
         hover="#f0b184", warnung="#aa571b", fehler="#a32626",
         positiv="#24643d", desktop="#086875", hell="#c9dedb",
         dunkel="#41646a", rahmen="#10262b", karo="#afc2c2",
         fenster_text="#10262b", panel_text="#c9dedb", kopf_aktiv_text="#10262b",
         kopf_inaktiv_text="#10262b", knopf_hover="#95b1b6", knopf_gedrueckt="#78969c",
         rille="#6f8f96", inaktiv_text="#6f8588", alt_fenster="#b9cac9", link="#086875")
DECORATION = "kwin4_decoration_qml_cdecopper"


def write(path, content, base=None):
    path = (base or OUT) / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata(id_, name, description):
    return {"KPlugin": {"Id": id_, "Name": name, "Description": description,
                       "Version": VERSION, "License": "GPL-2.0-or-later",
                       "Authors": [{"Name": "CDE Copper contributors"}],
                       "Website": "https://github.com/huppiflupp/plasma-theme-lab"}}


def colors(P, scheme="CDECopper", name="CDE Copper", base=None):
    def rgb(value):
        return ",".join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
    lines = ["[General]", f"Name={name}", f"ColorScheme={scheme}", "shadeSortColumn=true", "", "[KDE]", "contrast=7"]
    groups = {"Window": ("flaeche", "text"), "Button": ("flaeche", "text"),
              "View": ("fenster", "fenster_text"), "Selection": ("auswahl", "auswahl_text"),
              "Tooltip": ("fenster", "fenster_text"), "Complementary": ("panel", "panel_text"),
              "Header": ("flaeche", "text")}
    for group, (bg, fg) in groups.items():
        lines += ["", f"[Colors:{group}]"]
        for key, value in {"BackgroundNormal": bg, "BackgroundAlternate": bg,
                           "ForegroundNormal": fg, "ForegroundInactive": "text2",
                           "ForegroundActive": fg, "ForegroundLink": "link",
                           "ForegroundVisited": "dunkel", "ForegroundNegative": "fehler",
                           "ForegroundNeutral": "warnung", "ForegroundPositive": "positiv",
                           "DecorationFocus": "auswahl", "DecorationHover": "panel"}.items():
            lines.append(f"{key}={rgb(P[value])}")
    lines += ["", "[WM]", f"activeBackground={rgb(P['kopf_aktiv'])}",
              f"activeForeground={rgb(P['kopf_aktiv_text'])}", f"inactiveBackground={rgb(P['kopf_inaktiv'])}",
              f"inactiveForeground={rgb(P['kopf_inaktiv_text'])}", "", "[ColorEffects:Disabled]",
              f"Color={rgb(P['inaktiv_text'])}", "ColorEffect=0", "ContrastEffect=1", "ContrastAmount=0.55",
              "IntensityEffect=0", "", "[ColorEffects:Inactive]", "Enable=false"]
    write(f"color-schemes/{scheme}.colors", "\n".join(lines) + "\n", base)


def plasma(tools, P, theme="cde-copper", name="CDE Copper", base=None):
    mod = load(tools / "gen-plasma-svg.py", "plasma_svg")
    generator = mod.Generator(P, rahmen=1, aussenrahmen=1, rundung=0)
    for widget, spec in mod.WIDGETS.items():
        svg = generator.erzeuge(widget, spec)
        path = f"{spec.get('ordner', 'widgets')}/{spec.get('datei', widget)}.svg"
        write(f"plasma/desktoptheme/{theme}/{path}", svg, base)
        if widget in ("panel-background", "background", "background-dialog", "tooltip"):
            for mode in ("solid", "opaque", "translucent"):
                write(f"plasma/desktoptheme/{theme}/{mode}/{path}", svg, base)
    description = "Motif surfaces in teal and copper" if theme == "cde-copper" else f"Motif surfaces, {name}"
    write(f"plasma/desktoptheme/{theme}/metadata.json", json.dumps(metadata(theme, name, description), indent=2), base)
    write(f"plasma/desktoptheme/{theme}/plasmarc", "[Settings]\nFallbackTheme=default\n[ContrastEffect]\nenabled=false\n[BlurBehindEffect]\nenabled=false\n", base)


def decoration():
    """The Motif frame is a QML Aurorae decoration; it reads its colours from
    the active colour scheme, so it needs no per-palette build."""
    base = f"kwin/decorations/{DECORATION}/"
    shutil.copytree(ROOT / "decoration/contents", OUT / base / "contents", dirs_exist_ok=True)
    meta = metadata(DECORATION, "CDE Copper", "Motif window frame: corner handles, shadowed title parts")
    meta["KPackageStructure"] = "KWin/Decoration"
    write(base + "metadata.json", json.dumps(meta, indent=2))


def arrange():
    """KWin script: terminals beside the console, the main window above it."""
    base = "kwin/scripts/cde-copper-arrange/"
    shutil.copytree(ROOT / "arrange/contents", OUT / base / "contents", dirs_exist_ok=True)
    meta = metadata("cde-copper-arrange", "CDE Copper Window Arrangement",
                    "Terminals left and right of the front console, the main window above it (Meta+Ctrl+C)")
    meta["KPackageStructure"] = "KWin/Script"
    meta["X-Plasma-API"] = "javascript"
    meta["X-Plasma-MainScript"] = "code/main.js"
    meta["KPlugin"]["EnabledByDefault"] = True
    write(base + "metadata.json", json.dumps(meta, indent=2))


def backdrops_copper():
    """CDE's backdrop tiles in CDE Copper's desktop colours."""
    import backdrops
    import palettes
    backdrops.write_all(palettes.copper_desktop(), OUT / "wallpapers/CDEBackdrops")


def build_palette(name, base, tools=ROOT / "tools"):
    """Colour scheme, Plasma surfaces and Kvantum style for one CDE palette.

    Run by manage.py when a palette is applied, not by the release build:
    37 palettes times three generated sets would only bloat build/."""
    import palettes
    from kvantum import build_kvantum
    colours = palettes.theme(name)
    ident = "CDE" + name
    display = f"CDE {name}"
    colors(colours, ident, display, base)
    plasma(tools, colours, "cde-" + name.lower(), display, base)
    build_kvantum(base, colours, ident, f"Motif controls, CDE palette {name}")
    return {"colors": ident, "plasma": "cde-" + name.lower(), "kvantum": ident, "desktop": colours["desktop"],
            "targets": [f"color-schemes/{ident}.colors", "plasma/desktoptheme/cde-" + name.lower()],
            "config_targets": [f"Kvantum/{ident}"]}


def other_assets():
    lnf = "plasma/look-and-feel/org.cde.copper.desktop/"
    meta = metadata("org.cde.copper.desktop", "CDE Copper", "A contemporary Motif workstation")
    meta["KPackageStructure"] = "Plasma/LookAndFeel"
    write(lnf + "metadata.json", json.dumps(meta, indent=2))
    write(lnf + "contents/defaults", f"""[kdeglobals][General]
ColorScheme=CDECopper
font={UI_FONT}
fixed={MONO_FONT}
menuFont={UI_FONT}
toolBarFont={UI_FONT}
[kdeglobals][WM]
activeFont={TITLE_FONT}
[kdeglobals][KDE]
widgetStyle=Windows
[kdeglobals][Icons]
Theme=CDECopper
[plasmarc][Theme]
name=cde-copper
[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme={DECORATION}
ButtonsOnLeft=M
ButtonsOnRight=IAX
BorderSize=Normal
[kwinrc][Desktops]
Number=4
Rows=2
[Wallpaper]
Image=org.cde.copper
""")
    write("wallpapers/org.cde.copper/metadata.json", json.dumps(metadata("org.cde.copper", "Copper / Teal", "Quiet workstation teal"), indent=2))
    write("wallpapers/org.cde.copper/contents/images/3840x2160.svg", '''<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160"><rect width="3840" height="2160" fill="#086875"/></svg>''')
    lines = ["[General]", "Description=CDE Copper", "Opacity=1", "Blur=false", "Wallpaper=", "", "[Background]", "Color=6,28,34", "", "[Foreground]", "Color=196,210,208"]
    for i, c in enumerate(("#10262b", "#e28375", "#95bd98", "#f0b184", "#6eabbf", "#b8a3c4", "#3db5c3", "#c4d2d0")):
        rgb = ",".join(str(int(c[j:j+2], 16)) for j in (1, 3, 5))
        for suffix in ("", "Intense", "Faint"):
            lines += ["", f"[Color{i}{suffix}]", f"Color={rgb}"]
    write("konsole/CDECopper.colorscheme", "\n".join(lines) + "\n")
    write("konsole/CDE Copper.profile", "[General]\nName=CDE Copper\nParent=FALLBACK/\n[Appearance]\nColorScheme=CDECopper\nFont=" + KONSOLE_FONT + "\n[Scrolling]\nHistoryMode=1\nHistorySize=10000\n")
    shutil.copytree(ROOT / "frontpanel", OUT / "plasma/plasmoids/org.cde.copper.frontpanel", dirs_exist_ok=True)
    # IBM Plex Sans Condensed and IBM Plex Mono (SIL OFL 1.1), installed per user.
    shutil.copytree(ROOT / "fonts/IBMPlex", OUT / "fonts/CDECopper", dirs_exist_ok=True)
    shutil.copy2(ROOT / "layout.js", OUT / lnf / "contents/layout.js")


def main():
    ap = argparse.ArgumentParser()
    # CDE Copper carries its own copies of the SVG generators in tools/.
    # Never fall back to a sibling theme's tools: the two projects must not
    # influence each other (see tools/README.md).
    ap.add_argument("--tools", type=Path, default=ROOT / "tools")
    args = ap.parse_args()
    colors(P)
    plasma(args.tools, P)
    decoration()
    arrange()
    backdrops_copper()
    from icons import build_icons
    build_icons(OUT)
    from kvantum import build_kvantum
    build_kvantum(OUT, P)
    other_assets()
    print(f"CDE Copper {VERSION}: {sum(1 for p in OUT.rglob('*') if p.is_file())} files in {OUT}")


if __name__ == "__main__":
    main()
