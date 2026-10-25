#!/usr/bin/env python3
"""Build RISC Legacy (RISC OS for Plasma 6) into build/.

build/ mirrors ~/.local/share, build/config ~/.config: install.sh copies
them there. Everything is generated from this file and the sources beside
it; the theme shares nothing with CDE/, os2-warp/ or nt-legacy/ (the
repository's CLAUDE.md): tools/gen-plasma-svg.py is a copy of Warp
Legacy's, as of b7834ba1.

Four variants (DESIGN.md §2): RISC OS 3 as it was, RISC OS 4 with its
stone-textured tools, and RISC OS taken on to 2026, light and dark.
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
VERSION = "0.1.0"
# TeX Gyre Heros (GUST Font License, fonts/TeXGyreHeros): free Helvetica,
# the nearest relative of Homerton, RISC OS's desktop font. RISC OS sets
# titles in the same weight as the rest; Qt 6 font strings.
UI_FONT = "TeX Gyre Heros,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
TITLE_FONT = "TeX Gyre Heros,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
MONO_FONT = "Liberation Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"

# The Wimp's sixteen desktop colours (RISC OS 3 Style Guide; the same
# values in the sources' default palette), named as the Style Guide does.
WIMP = ["#ffffff", "#dddddd", "#bbbbbb", "#999999", "#777777", "#555555", "#333333", "#000000",
        "#004499", "#eeee00", "#00cc00", "#dd0000", "#eeeebb", "#558800", "#ffbb00", "#00bbff"]

# RISC OS 3 (DESIGN.md §2): window backgrounds colour 1, the title of the
# window with the input focus colour 12 (cream), the others colour 1;
# black lines, black menu highlight with white text. Lists select in the
# Wimp's dark blue (colour 8): the scheme's selection is Plasma's accent,
# and Breeze's folder icons take it on (all folders black with a black
# selection, VM 25.10.2026); menus keep RISC OS's black (menu_selection).
CLASSIC = dict(surface=WIMP[1], window=WIMP[0], panel=WIMP[1],
               light=WIMP[0], dark=WIMP[4], border=WIMP[7], checker=WIMP[2],
               text=WIMP[7], text2=WIMP[5], inactive_text=WIMP[4],
               title_active=WIMP[12], title_active_text=WIMP[7],
               title_inactive=WIMP[1], title_inactive_text=WIMP[7],
               active=WIMP[8], selection=WIMP[8], selection_text=WIMP[0],
               menu_selection=WIMP[7],
               hover=WIMP[2], link=WIMP[8], visited="#553399",
               warning="#bb6600", error=WIMP[11], positive="#337700",
               desktop=WIMP[4], panel_text=WIMP[7],
               complementary=WIMP[6], complementary_text=WIMP[0],
               window_text=WIMP[7], alt_window="#f4f4f4", button_hover=WIMP[1],
               button_pressed=WIMP[2], groove=WIMP[3],
               # Kvantum: progress bars in the Wimp's green, as !Configure's
               # bars; the default button's cream ring.
               progress="#22aa22", default_ring=WIMP[12])

# RISC OS 4: the same colours; the title bar's texture is sparse, so the
# title colour under it is colour 2, which with the specks reads as the
# grey stone of the screenshots.
SELECT = dict(CLASSIC, title_inactive=WIMP[2], desktop="#8a8a86")

# 2026: RISC OS's grey and cream kept, warmer and softer; the Wimp's dark
# blue as the accent for selections, as RISC OS 5's Pinboard selection.
MODERN = dict(surface="#e9e9e4", window="#ffffff", panel="#e4e4de",
              light="#ffffff", dark="#a6a69f", border="#3a3a38", checker="#d6d6cf",
              text="#1d1d1b", text2="#54544f", inactive_text="#8c8c86",
              title_active="#f1e7b4", title_active_text="#1d1d1b",
              title_inactive="#e2e2dc", title_inactive_text="#54544f",
              active="#1f5fbf", selection="#1f5fbf", selection_text="#ffffff",
              hover="#dcdcd4", link="#1f5fbf", visited="#6a4bb0",
              warning="#b86a00", error="#c42b1c", positive="#2e7d32",
              desktop="#6f8a9a", panel_text="#1d1d1b",
              complementary="#2a2c31", complementary_text="#f2f2ee",
              window_text="#1d1d1b", alt_window="#f6f6f2", button_hover="#f2f2ec",
              button_pressed="#d8d8d0", groove="#cfcfc8",
              progress="#2e9e4a", default_ring="#e8d78a", radio="#d23a2a")

# Dark: the cream becomes a dim brass for the focused title, so the
# window with the focus still carries RISC OS's colour.
DARK = dict(surface="#2b2e34", window="#1f2126", panel="#26292e",
            light="#4a4f58", dark="#15171a", border="#0b0c0e", checker="#353941",
            text="#e8e8e4", text2="#a9aca8", inactive_text="#6f737a",
            title_active="#6a5d2e", title_active_text="#f6efc8",
            title_inactive="#34373e", title_inactive_text="#a9aca8",
            active="#4d8fea", selection="#3a78d0", selection_text="#ffffff",
            hover="#383c44", link="#7fb2ff", visited="#b79cff",
            warning="#f0a63a", error="#ff6b5e", positive="#5fc46a",
            desktop="#1b2230", panel_text="#e8e8e4",
            complementary="#17191c", complementary_text="#e8e8e4",
            window_text="#e8e8e4", alt_window="#24272c", button_hover="#353941",
            button_pressed="#202227", groove="#202227",
            progress="#3fae5c", default_ring="#a8924a", radio="#ff6b5e")

# The further palettes (the user's wish for more colour plates, 25.10.2026),
# from RISC OS's later machines; each is a global theme of its own.
# Pi: RISC OS Pi's green desktop and raspberry, RISC OS 5's icons.
PI = dict(CLASSIC, desktop="#a9dba8", selection="#b8204a", active="#b8204a", link="#b8204a",
          visited="#7a2a6a", progress="#b8204a")
# Iyonix: the Iyonix's blue for selections and the focused title.
IYONIX = dict(CLASSIC, title_active="#cfe0f5", selection="#2a5fa8", active="#2a5fa8", link="#2a5fa8",
              desktop="#3a6ea5", progress="#2a5fa8", default_ring="#cfe0f5")
# Acorn: RISC OS 4's stone with Acorn's green.
ACORN = dict(SELECT, selection="#2f6b3a", active="#2f6b3a", link="#2f6b3a", desktop="#3d6b4a",
             progress="#2f6b3a")
# Graphite: classic in the Wimp's darker greys, the focus still cream.
GRAPHITE = dict(surface=WIMP[5], window=WIMP[6], panel=WIMP[5],
                light=WIMP[3], dark="#222222", border=WIMP[7], checker=WIMP[4],
                text=WIMP[0], text2=WIMP[2], inactive_text=WIMP[3],
                title_active=WIMP[12], title_active_text=WIMP[7],
                title_inactive=WIMP[4], title_inactive_text=WIMP[1],
                active=WIMP[15], selection="#0f7fb8", selection_text=WIMP[0], menu_selection=WIMP[7],
                hover=WIMP[4], link="#66ccff", visited="#c0a0ff",
                warning=WIMP[14], error="#ff5555", positive="#66cc33",
                desktop="#2c2c2c", panel_text=WIMP[0],
                complementary=WIMP[6], complementary_text=WIMP[0],
                window_text=WIMP[0], alt_window="#3a3a3a", button_hover="#5e5e5e",
                button_pressed=WIMP[4], groove=WIMP[6], progress="#33aa33",
                default_ring=WIMP[12], radio="#ff4444")

VARIANTS = [
    dict(key="", picture="granit", art="classic", name="RISC Legacy", P=CLASSIC, icons="RiscLegacy",
         description="RISC OS 3: grey windows, a cream title for the focus, the iconbar"),
    dict(key="4", picture="marmor", art="select", name="RISC Legacy 4", P=SELECT, icons="RiscLegacy", tile="tile_1",
         description="RISC OS 4: the stone-textured window tools"),
    dict(key="2026", picture="fenland-morgen", art="modern", name="RISC Legacy 2026", P=MODERN, icons="RiscLegacy2026",
         description="RISC OS taken on to 2026: the same window, smooth and warm"),
    dict(key="2026-dark", picture="fenland-nacht", art="dark", name="RISC Legacy 2026 Dark", P=DARK, icons="RiscLegacy2026",
         description="RISC OS 2026 at night, the focus in brass"),
    dict(key="pi", picture="himbeerlaub", art="classic", name="RISC Legacy Pi", P=PI, icons="RiscLegacy5",
         description="RISC OS Pi: the green desktop, raspberry for selections, RISC OS 5's icons"),
    dict(key="iyonix", picture="iyonix-blau", art="classic", name="RISC Legacy Iyonix", P=IYONIX, icons="RiscLegacy5",
         description="The Iyonix's blue for the focus and selections"),
    dict(key="acorn", picture="eicheln", art="select", name="RISC Legacy Acorn", P=ACORN, icons="RiscLegacy", tile="tile_1",
         description="RISC OS 4's stone with Acorn green"),
    dict(key="graphite", picture="schiefer", art="graphite", name="RISC Legacy Graphite", P=GRAPHITE, icons="RiscLegacy",
         description="Classic RISC OS in the darker greys, the focus still cream"),
]


def ids(v):
    """Package and file names of a variant: RiscLegacy / RiscLegacy4 …"""
    k = v["key"]
    camel = "".join(part.capitalize() for part in k.split("-"))
    return dict(scheme="RiscLegacy" + camel,
                kvantum="RiscLegacy" + camel,
                theme="risc-legacy" + (f"-{k}" if k else ""),
                lnf="org.risclegacy" + (f".{k}" if k else "") + ".desktop",
                decoration="kwin4_decoration_qml_risclegacy" + k.replace("-", ""),
                wallpaper="org.risclegacy." + v["picture"])


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
              "Authors": [{"Name": "RISC Legacy contributors"}],
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
              "Tooltip": ("title_active", "title_active_text"),
              "Complementary": ("complementary", "complementary_text"),
              "Header": ("surface", "text")}
    for group, (bg, fg) in groups.items():
        lines += ["", f"[Colors:{group}]"]
        for key, value in {"BackgroundNormal": bg, "BackgroundAlternate": bg,
                           "ForegroundNormal": fg, "ForegroundInactive": "text2",
                           "ForegroundActive": fg, "ForegroundLink": "link",
                           "ForegroundVisited": "visited", "ForegroundNegative": "error",
                           "ForegroundNeutral": "warning", "ForegroundPositive": "positive",
                           "DecorationFocus": "active", "DecorationHover": "dark"}.items():
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
    """The Plasma style: RISC OS's bevelled surfaces with a black line."""
    mod = load(ROOT / "tools/gen-plasma-svg.py", "plasma_svg")
    flat = v["art"] in ("modern", "dark")
    generator = mod.Generator(v["P"], border=1, outer_border=1, radius=3 if flat else 0)
    theme = ids(v)["theme"]
    base = f"plasma/desktoptheme/{theme}/"
    for widget, spec in mod.WIDGETS.items():
        svg = generator.generate(widget, spec)
        path = f"{spec.get('folder', 'widgets')}/{spec.get('file', widget)}.svg"
        write(base + path, svg)
        if widget in ("panel-background", "background", "background-dialog", "tooltip"):
            for mode in ("solid", "opaque", "translucent"):
                write(f"{base}{mode}/{path}", svg)
    if v.get("tile"):
        texture(OUT / base, v["tile"])
    write(base + "metadata.json", json.dumps(metadata(theme, v["name"], v["description"]), indent=2))
    write(base + "plasmarc", "[Settings]\nFallbackTheme=default\n[ContrastEffect]\nenabled=false\n"
          "[BlurBehindEffect]\nenabled=false\n")
    shutil.copy2(OUT / f"color-schemes/{ids(v)['scheme']}.colors", OUT / base / "colors")


def texture(base, tile):
    """RISC OS 4's stone: the Wimp's window tile (Sprites-RO400/tile_1,
    128 x 128) as the centre of the panel (the iconbar) and of dialogs.
    Each centre element becomes the picture at its full size; Plasma tiles
    it (the generator's hint-tile-center)."""
    import base64
    import re
    data = base64.b64encode((ROOT / "vendor/riscos-open/Sprites-RO400" / f"{tile}.png").read_bytes()).decode()
    files = [f"{mode}{name}.svg" for mode in ("", "solid/", "opaque/", "translucent/")
             for name in ("widgets/panel-background", "widgets/background", "dialogs/background")]
    for name in files:
        path = base / name
        if not path.exists():
            continue
        svg = path.read_text()
        if "xmlns:xlink" not in svg:
            svg = svg.replace('<svg xmlns="http://www.w3.org/2000/svg"',
                              '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"', 1)

        def swap(m):
            x, y = m.group(2), m.group(3)
            return (f'{m.group(1)}<image x="{x}" y="{y}" width="128" height="128" '
                    f'xlink:href="data:image/png;base64,{data}"/>')
        svg = re.sub(r'(<g id="(?:[a-z]+-)?center">\s*)<rect x="([\d.]+)" y="([\d.]+)" width="[\d.]+" height="[\d.]+" fill="[^"]+"/>',
                     swap, svg)
        path.write_text(svg)


def decoration(v):
    """The window frame: a QML decoration (decoration/), the variant's tool
    pictures (tools/toolart.py) in contents/ui/art, the line colour in
    Style.qml."""
    name = ids(v)["decoration"]
    base = OUT / f"kwin/decorations/{name}"
    shutil.copytree(ROOT / "decoration/contents", base / "contents", dirs_exist_ok=True)
    art = load(ROOT / "tools/toolart.py", "toolart")
    folder = base / "contents/ui/art"
    folder.mkdir(parents=True, exist_ok=True)
    art.VARIANTS[v["art"]](folder)
    write(f"kwin/decorations/{name}/contents/ui/Style.qml",
          f"import QtQuick\n\n// Written by build.py for {v['name']}.\nQtObject {{\n"
          f"    readonly property color line: \"{v['P']['border']}\"\n}}\n")
    write(f"kwin/decorations/{name}/metadata.json", json.dumps(
        metadata(name, v["name"], "RISC OS window frame: Back and Close, centred title, Iconise and Toggle size",
                 "KWin/Decoration"), indent=2))


def kvantum(v):
    """The widget style for programs, to ~/.config/Kvantum (build/config)."""
    load(ROOT / "kvantum.py", "kvantum").build_kvantum(OUT / "config", v["P"], name=ids(v)["kvantum"],
                                                       comment=v["description"])


# The generated backdrops (wallpapers/, tools/gen-wallpapers.py; prompt and
# seed in the JSON beside each): stem, name, description.
PICTURES = (
    ("granit", "Granite", "Fine grey granite, RISC OS 3's grey"),
    ("marmor", "Marble", "Pale marble, after RISC OS 4's stone"),
    ("fenland-morgen", "Fenland Morning", "The fens near Cambridge at dawn, where Acorn began"),
    ("fenland-nacht", "Fenland Night", "The fens at night, a brass glow on the horizon"),
    ("himbeerlaub", "Raspberry Leaves", "Raspberry leaves in pastel green"),
    ("iyonix-blau", "Iyonix Blue", "Deep blue light through frosted glass"),
    ("eicheln", "Acorns", "Oak leaves and acorns on moss"),
    ("schiefer", "Slate", "Dark slate"),
)


def wallpapers():
    """One wallpaper package per picture, all offered with every variant."""
    for stem, name, description in PICTURES:
        id_ = f"org.risclegacy.{stem}"
        write(f"wallpapers/{id_}/metadata.json", json.dumps(metadata(id_, name, description), indent=2))
        target = OUT / f"wallpapers/{id_}/contents/images/1920x1080.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f"wallpapers/{stem}.jpg", target)


def lookandfeel(v):
    i = ids(v)
    base = f"plasma/look-and-feel/{i['lnf']}/"
    write(base + "metadata.json", json.dumps(metadata(i["lnf"], v["name"], v["description"], "Plasma/LookAndFeel"), indent=2))
    # RISC OS: Back and Close on the left, Iconise and Toggle size on the
    # right (B = keep below, X, I, A). Plasma takes only library, theme and
    # BorderSize from here; install.sh writes the button order itself.
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
[kdeglobals][Icons]
Theme={v['icons']}
[plasmarc][Theme]
name={i['theme']}
[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme={i['decoration']}
ButtonsOnLeft=BX
ButtonsOnRight=IA
BorderSize=Normal
[Wallpaper]
Image={i['wallpaper']}
""")


def layout(v):
    """The desktop layout (layout.js): the iconbar, the variant's picture."""
    script = (ROOT / "layout.js").read_text().replace("@PICTURE@", ids(v)["wallpaper"])
    write(f"plasma/look-and-feel/{ids(v)['lnf']}/contents/layouts/org.kde.plasma.desktop-layout.js", script)


def plasmoids():
    """The iconbar, shared by all variants (it takes its colours from the
    colour scheme)."""
    target = OUT / "plasma/plasmoids/org.risclegacy.iconbar"
    shutil.copytree(ROOT / "iconbar", target, dirs_exist_ok=True)
    meta = json.loads((target / "metadata.json").read_text())
    meta["KPlugin"]["Version"] = VERSION
    (target / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


def icons():
    """RISC OS's own icons (tools/iconset.py), RISC OS 4's and 5's."""
    load(ROOT / "tools/iconset.py", "iconset").build(OUT / "icons")
    # 2026's own, drawn as SVG (the user's choice 25.10.2026: pixels for
    # the classic variants, smooth icons for 2026).
    load(ROOT / "tools/svgicons.py", "svgicons").build(OUT / "icons")


def variant_table():
    """For install.sh: key, global theme, Kvantum theme, icons, picture,
    decoration, colour scheme, Plasma style."""
    rows = [f"{v['key'] or 'classic'}\t{ids(v)['lnf']}\t{ids(v)['kvantum']}\t{v['icons']}\t{ids(v)['wallpaper']}"
            f"\t{ids(v)['decoration']}\t{ids(v)['scheme']}\t{ids(v)['theme']}"
            for v in VARIANTS]
    write("risc-legacy/variants", "\n".join(rows) + "\n")


def fonts():
    shutil.copytree(ROOT / "fonts", OUT / "fonts/risc-legacy", dirs_exist_ok=True)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for v in VARIANTS:
        colors(v)
        plasma(v)
        decoration(v)
        kvantum(v)
        lookandfeel(v)
        layout(v)
    wallpapers()
    plasmoids()
    icons()
    fonts()
    variant_table()
    print(f"RISC Legacy {VERSION} ({', '.join(v['name'] for v in VARIANTS)}) built in {OUT}")


if __name__ == "__main__":
    main()
