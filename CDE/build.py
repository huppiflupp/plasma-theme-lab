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
VERSION = "0.1.0"
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
         dunkel="#41646a", rahmen="#10262b", karo="#afc2c2")


def write(path, content):
    path = OUT / path
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


def colors():
    def rgb(value):
        return ",".join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
    lines = ["[General]", "Name=CDE Copper", "ColorScheme=CDECopper", "shadeSortColumn=true", "", "[KDE]", "contrast=7"]
    groups = {"Window": ("flaeche", "text"), "Button": ("flaeche", "text"),
              "View": ("fenster", "text"), "Selection": ("auswahl", "text"),
              "Tooltip": ("fenster", "text"), "Complementary": ("panel", "hell"),
              "Header": ("flaeche", "text")}
    for group, (bg, fg) in groups.items():
        lines += ["", f"[Colors:{group}]"]
        for key, value in {"BackgroundNormal": bg, "BackgroundAlternate": bg,
                           "ForegroundNormal": fg, "ForegroundInactive": "text2",
                           "ForegroundActive": fg, "ForegroundLink": "desktop",
                           "ForegroundVisited": "dunkel", "ForegroundNegative": "fehler",
                           "ForegroundNeutral": "warnung", "ForegroundPositive": "positiv",
                           "DecorationFocus": "auswahl", "DecorationHover": "panel"}.items():
            lines.append(f"{key}={rgb(P[value])}")
    lines += ["", "[WM]", f"activeBackground={rgb(P['kopf_aktiv'])}",
              f"activeForeground={rgb(P['text'])}", f"inactiveBackground={rgb(P['kopf_inaktiv'])}",
              f"inactiveForeground={rgb(P['text'])}", "", "[ColorEffects:Disabled]",
              "Color=111,133,136", "ColorEffect=0", "ContrastEffect=1", "ContrastAmount=0.55",
              "IntensityEffect=0", "", "[ColorEffects:Inactive]", "Enable=false"]
    write("color-schemes/CDECopper.colors", "\n".join(lines) + "\n")


def plasma(tools):
    mod = load(tools / "gen-plasma-svg.py", "plasma_svg")
    generator = mod.Generator(P, rahmen=1, aussenrahmen=1, rundung=0)
    for name, spec in mod.WIDGETS.items():
        svg = generator.erzeuge(name, spec)
        path = f"{spec.get('ordner', 'widgets')}/{spec.get('datei', name)}.svg"
        write(f"plasma/desktoptheme/cde-copper/{path}", svg)
        if name in ("panel-background", "background", "background-dialog", "tooltip"):
            for mode in ("solid", "opaque", "translucent"):
                write(f"plasma/desktoptheme/cde-copper/{mode}/{path}", svg)
    write("plasma/desktoptheme/cde-copper/metadata.json", json.dumps(metadata(
        "cde-copper", "CDE Copper", "Motif surfaces in teal and copper"), indent=2))
    write("plasma/desktoptheme/cde-copper/plasmarc", "[Settings]\nFallbackTheme=default\n[ContrastEffect]\nenabled=false\n[BlurBehindEffect]\nenabled=false\n")


def decoration(tools):
    mod = load(tools / "gen-aurorae.py", "aurorae_svg")
    class Motif(mod.Aurorae):
        def _symbol(self, art, m, n, s, sw, color):
            if art in ("menu", "minimize", "maximize"):
                width = 5 if art == "minimize" else 12
                height = 5 if art != "maximize" else 12
                x, y = m - width / 2, n - height / 2
                return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}"/>'
                        f'<path d="M{x+1} {y+height-1}V{y+1}H{x+width-1}" fill="none" stroke="#f0b184"/>')
            return super()._symbol(art, m, n, s, sw, color)

    deco = Motif(P, titelhoehe=34, rahmen=6, aussen=1, bevel=1, buttongroesse=24)
    base = "aurorae/themes/CDECopper/"
    ns = "{http://www.w3.org/2000/svg}"
    ET.register_namespace("", ns[1:-1])
    svg = ET.fromstring(deco.decoration())
    # Motif title rails and corner grips stay inside the native nine-patch IDs.
    for group in svg.findall(f"{ns}g"):
        id_ = group.get("id", "")
        rect = group.find(f"{ns}rect")
        if rect is None:
            continue
        x, y, w, h = [float(rect.get(k)) for k in ("x", "y", "width", "height")]
        if id_.endswith("-top"):
            for dy, fill in ((h-2, P["dunkel"]), (h-1, P["hell"]), (4, P["hell"])):
                ET.SubElement(group, f"{ns}rect", dict(x=str(x), y=str(y+dy), width=str(w), height="1", fill=fill))
        if id_.endswith(("-topleft", "-topright")):
            ET.SubElement(group, f"{ns}rect", dict(x=str(x+1), y=str(y+22), width=str(w-2), height="1", fill=P["rahmen"]))
    write(base + "decoration.svg", ET.tostring(svg, encoding="unicode"))
    for button in mod.BUTTONS:
        svg = ET.fromstring(deco.button(button))
        for group in svg.findall(f"{ns}g"):
            state = group.get("id", "").split("-")[0]
            rect = group.find(f"{ns}rect")
            if rect is not None:
                rect.set("fill", P["kopf_inaktiv"] if state == "inactive" else P["kopf_aktiv"])
        write(base + button + ".svg", ET.tostring(svg, encoding="unicode"))
    rc = deco.rc("CDECopper").replace("TitleAlignment=Left", "TitleAlignment=Center")
    rc = rc.replace("InactiveTextColor=196,210,208", "InactiveTextColor=16,38,43")
    rc = rc.replace("Shadow=true", "Shadow=false")
    write(base + "CDECopperrc", rc)
    write(base + "metadata.desktop", deco.metadata("CDECopper", "CDE Copper", "Motif workstation decoration", "CDE Copper contributors", "GPL-2.0-or-later", VERSION))


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
theme=__aurorae__svg__CDECopper
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
    colors()
    plasma(args.tools)
    decoration(args.tools)
    from icons import build_icons
    build_icons(OUT)
    from kvantum import build_kvantum
    build_kvantum(OUT, P)
    other_assets()
    print(f"CDE Copper {VERSION}: {sum(1 for p in OUT.rglob('*') if p.is_file())} files in {OUT}")


if __name__ == "__main__":
    main()
