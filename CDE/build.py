#!/usr/bin/env python3
"""Build CDE / Copper from vector sources. Run in the lab VM."""
import argparse
import importlib.util
import json
import re
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
VERSION = "0.9.5"
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
              "Header": ("auswahl", "auswahl_text")}
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
    write(f"plasma/desktoptheme/{theme}/widgets/glowbar.svg", glowbar(P), base)
    description = "Motif surfaces in teal and copper" if theme == "cde-copper" else f"Motif surfaces, {name}"
    write(f"plasma/desktoptheme/{theme}/metadata.json", json.dumps(metadata(theme, name, description), indent=2), base)
    write(f"plasma/desktoptheme/{theme}/plasmarc", "[Settings]\nFallbackTheme=default\n[ContrastEffect]\nenabled=false\n[BlurBehindEffect]\nenabled=false\n", base)


def glowbar(P):
    """KWin's mark at a screen edge with a hidden panel (its screenedge
    effect reads widgets/glowbar): a copper bar, raised as in Motif, instead
    of a soft glow. Each element is named for the side it extends to ("top"
    lies along the bottom edge). KWin shares the corners between two edges
    each, so they stay empty: the bar has no end caps."""
    import palettes
    copper = P["kopf_aktiv"]
    light, dark = palettes.mix(copper, "#ffffff", 0.45), palettes.mix(copper, "#000000", 0.35)

    def bar(near, far):
        # Drawn lying along the bottom: ink towards the screen, then the
        # bevel, the screen edge at the bottom row.
        rows = [P["rahmen"], near, copper, copper, copper, copper, far, far]
        return "".join(f'<rect x="0" y="{4 + i}" width="12" height="1" fill="{c}"/>' for i, c in enumerate(rows))
    # Light from the top left, whichever way the bar is turned.
    lit = {"top": bar(light, dark), "left": bar(light, dark), "bottom": bar(dark, light), "right": bar(dark, light)}
    turn = {"top": 0, "right": 90, "bottom": 180, "left": 270}
    at = {"top": (22, 10), "left": (10, 22), "right": (34, 22), "bottom": (22, 34), "center": (22, 22),
          "topleft": (10, 10), "topright": (34, 10), "bottomleft": (10, 34), "bottomright": (34, 34)}
    parts = [f'<g id="{name}" transform="translate({at[name][0]},{at[name][1]})">'
             f'<g transform="rotate({angle} 6 6)">{lit[name]}</g></g>' for name, angle in turn.items()]
    parts.append(f'<g id="center" transform="translate(22,22)"><rect width="12" height="12" fill="{copper}"/></g>')
    parts += [f'<g id="{name}" transform="translate({at[name][0]},{at[name][1]})">'
              f'<rect width="12" height="12" fill="none"/></g>' for name in ("topleft", "topright", "bottomleft", "bottomright")]
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56">\n'
            '<rect id="hint-glow-radius" width="5" height="5" x="0" y="0" fill="#ff6600"/>\n'
            + "\n".join(parts) + "\n</svg>\n")


# The start-up screen's stage pictures (lookandfeel/contents/splash).
SPLASH_ICONS = {"display": "computer", "window": "window", "plasma": "cde-menu",
                "settings": "preferences-system", "session": "user-home", "desktop": "folder-desktop"}


def splash_colours(P):
    """Colours.qml of the start-up screen, from a palette's colours."""
    values = {"desktop": P["desktop"], "face": P["flaeche"], "light": P["hell"], "dark": P["dunkel"],
              "ink": P["text"], "accent": P["kopf_aktiv"], "title": P["kopf_aktiv"],
              "titleText": P["kopf_aktiv_text"], "trough": P["rille"], "field": P["fenster"]}
    lines = "\n".join(f'    readonly property color {key}: "{value}"' for key, value in values.items())
    return f"import QtQuick\n\n// Written by CDE Copper for the palette in use.\nQtObject {{\n{lines}\n}}\n"


def decoration():
    """The Motif frame is a QML Aurorae decoration; it reads its colours from
    the active colour scheme, so it needs no per-palette build."""
    base = f"kwin/decorations/{DECORATION}/"
    shutil.copytree(ROOT / "decoration/contents", OUT / base / "contents", dirs_exist_ok=True)
    # Named "CDE": the frame follows whichever palette is applied.
    meta = metadata(DECORATION, "CDE", "Motif window frame after mwm; follows the colour scheme")
    meta["KPackageStructure"] = "KWin/Decoration"
    write(base + "metadata.json", json.dumps(meta, indent=2))


def tabbox():
    """The Alt+Tab switcher: a KWin window switcher package in Motif style."""
    base = "kwin/tabbox/org.cde.copper.switcher/"
    shutil.copytree(ROOT / "tabbox/contents", OUT / base / "contents", dirs_exist_ok=True)
    shutil.copy2(ROOT / "tabbox/metadata.json", OUT / base / "metadata.json")


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


def backdrops_plugin():
    """The "CDE Backdrop" wallpaper type, with CDE's patterns in Copper's
    workspace colours as its packaged set."""
    import backdrops
    import palettes
    base = "plasma/wallpapers/org.cde.copper.backdrop/"
    shutil.copytree(ROOT / "backdrop/contents", OUT / base / "contents", dirs_exist_ok=True)
    backdrops.write_all(palettes.copper_desktop(), OUT / base / "contents/images/Copper")
    # The material tiles in natural colour, and Copper's tinted set as fallback.
    shutil.copytree(ROOT / "wallpapers/tiles", OUT / base / "contents/images/tiles", dirs_exist_ok=True)
    backdrops.write_tiles(palettes.copper_desktop(), OUT / base / "contents/images/Copper", ROOT / "wallpapers/tiles")
    write(base + "contents/ui/backdrops.js",
          "// Generated by build.py from backdrops/cde, wallpapers/tiles and PICTURES.\n.pragma library\n\nconst NAMES = "
          + json.dumps(backdrops.names()) + ";\n\nconst TILES = "
          + json.dumps([{"key": key, "name": name} for key, name in backdrops.TILES]) + ";\n\nconst PICTURES = "
          + json.dumps([{"key": key, "name": name, "palette": picture_palette(description)}
                        for key, name, description in PICTURES], indent=1) + ";\n")
    meta = metadata("org.cde.copper.backdrop", "CDE Backdrop",
                    "CDE's backdrop patterns, tiled pixel for pixel in the palette's colours")
    meta["KPackageStructure"] = "Plasma/Wallpaper"
    write(base + "metadata.json", json.dumps(meta, indent=2))


# Picture wallpapers (see wallpapers/README.md): key, display name, description.
LOWPOLY = "Low-poly landscape in Copper colours"
PICTURES = (
    ("altai", "Copper Altai", LOWPOLY), ("canopee", "Copper Canopée", LOWPOLY), ("cluster", "Copper Cluster", LOWPOLY),
    ("fluss", "Copper Fluss", LOWPOLY), ("kaskade", "Copper Kaskade", LOWPOLY),
    ("monolith", "CDE Monolith", "Retro ray-traced desert, Default palette"),
    ("polarlicht", "CDE Polarlicht", "Aurora over a low-poly fjord, NorthernSky palette"),
    ("mesa", "CDE Mesa", "Paper-cut desert, Arizona palette"),
    ("riff", "CDE Riff", "Coral reef, Urchin palette"),
    ("origami", "CDE Origami", "Folded paper lilies, Lilac palette"),
    ("bauhaus", "CDE Bauhaus", "Bauhaus poster, Golden palette"),
    ("weinberg", "CDE Weinberg", "Isometric vineyard, Cabernet palette"),
    ("orbit", "CDE Orbit", "Ringed planet in glass, Neptune palette"),
    ("chipstadt", "CDE Chipstadt", "Miniature city built from workstation chips, Default palette"),
    ("cad", "CDE CAD", "Gear assembly in wireframe and solid, SoftBlue palette"),
    ("molekuel", "CDE Molekül", "Protein ribbons and atoms, Crimson palette"),
    ("sequenz", "CDE Sequenz", "Sequencing gel and chromatogram, Golden palette"),
    ("druckvorstufe", "CDE Druckvorstufe", "Desktop publishing proofs, PBNJ palette"),
    ("schnittplatz", "CDE Schnittplatz", "Film, tapes and a vectorscope, SkyRed palette"),
    ("mrt", "CDE MRT", "MRI films on a lightbox, Alpine palette"),
    ("mischpult", "CDE Mischpult", "Analog mixing console, Tundra palette"),
    ("vlsi", "CDE VLSI", "Chip layout layers, Summer palette"),
    ("stroemung", "CDE Strömung", "Computed flow around an airfoil, Delphinium palette"),
    ("kristall", "CDE Kristall", "Crystal mosaic in Copper colours"),
    ("marmor", "CDE Marmor", "Marbled ink, Crimson palette"),
    ("duene", "CDE Düne", "Dunes with a lone workstation, Copper colours"),
    ("aquarell", "CDE Aquarell", "Late-1990s watercolour, a workstation sending windows"),
    ("panorama", "CDE Panorama", "Late-1990s gouache landscape with a paper plane"),
    # One panorama split across two screens (wallpapers/gen/span.py): left 32", right 27", top-aligned.
    ("duene-links", "CDE Düne links", "Left half of a dune panorama for a 32-inch screen beside a 27-inch one"),
    ("duene-rechts", "CDE Düne rechts", "Right half of a dune panorama for a 27-inch screen beside a 32-inch one"),
    ("weltraum-links", "CDE Weltraum links", "Left half of a space panorama for a 32-inch screen beside a 27-inch one"),
    ("weltraum-rechts", "CDE Weltraum rechts", "Right half of a space panorama for a 27-inch screen beside a 32-inch one"),
    # Landscape photographs, by day and by night.
    ("alpen", "CDE Alpen", "Alpine peak and mountain lake, Alpine palette"),
    ("dolomiten", "CDE Dolomiten", "Dolomite towers above meadows, Desert palette"),
    ("elbsandstein", "CDE Elbsandstein", "Sandstone pillars above morning fog, Sand palette"),
    ("fjord", "CDE Fjord", "Norwegian fjord, aurora at night, NorthernSky palette"),
    ("island", "CDE Island", "Basalt columns on a black beach, Charcoal palette"),
    ("schwarzwald", "CDE Schwarzwald", "Fir valley in fog, Grass palette"),
    ("toskana", "CDE Toskana", "Wheat hills and cypresses, Wheat palette"),
    ("watt", "CDE Watt", "Wadden Sea at low tide, SeaFoam palette"),
)


def picture_palette(description):
    """The palette a picture was painted for, from its description."""
    match = re.search(r"(\w+) palette", description)
    return match.group(1) if match else "Copper"


def pictures():
    """Picture wallpapers, light and dark; images_dark is picked by Plasma
    under a dark colour scheme."""
    for key, name, description in PICTURES:
        base = f"wallpapers/org.cde.copper.{key}/"
        for sub, suffix in (("images", ""), ("images_dark", "-dark")):
            target = OUT / base / "contents" / sub
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f"wallpapers/images/{key}{suffix}.jpg", target / "3840x2160.jpg")
        write(base + "metadata.json", json.dumps(metadata(f"org.cde.copper.{key}", name, description + ", light and dark"), indent=2))


def palette_schemes():
    """Every CDE palette as a colour scheme, so System Settings lists them;
    the console completes the switch (Kvantum, Plasma surfaces, backdrop)."""
    import palettes
    swatches = [{"name": "Copper", "colours": [P["panel"], P["flaeche"], P["fenster"], P["kopf_aktiv"], P["kopf_inaktiv"], P["desktop"]]}]
    for name in palettes.names():
        colours = palettes.theme(name)
        colors(colours, "CDE" + name, "CDE " + name)
        swatches.append({"name": name, "colours": [colours["panel"], colours["flaeche"], colours["fenster"],
                                                   colours["kopf_aktiv"], colours["kopf_inaktiv"], colours["desktop"]]})
    # For the style manager (and the console's old Style page while it exists).
    import backdrops
    script = ("// Generated by build.py: console, window, field, active, inactive, desktop.\n.pragma library\n\nconst PALETTES = "
              + json.dumps(swatches, indent=1) + ";\n\nconst BACKDROPS = " + json.dumps(backdrops.names())
              + ";\n\n// The pictures, each with the palette it was painted for.\nconst PICTURES = "
              + json.dumps([{"key": key, "name": name, "palette": picture_palette(description)}
                            for key, name, description in PICTURES], indent=1) + ";\n")
    write("plasma/plasmoids/org.cde.copper.stylemanager/contents/ui/palettes.js", script)
    if (ROOT / "frontpanel/contents/ui/configStyle.qml").exists():
        write("plasma/plasmoids/org.cde.copper.frontpanel/contents/ui/palettes.js", script)


def build_palette(name, base, tools=ROOT / "tools", progress="outlined"):
    """Colour scheme, Plasma surfaces and Kvantum style for one CDE palette.

    Run by manage.py when a palette is applied, not by the release build:
    37 palettes times two generated sets would only bloat build/. The colour
    schemes themselves are built for all palettes (palette_schemes)."""
    import palettes
    from kvantum import build_kvantum
    colours = palettes.theme(name)
    ident = "CDE" + name
    display = f"CDE {name}"
    plasma(tools, colours, "cde-" + name.lower(), display, base)
    build_kvantum(base, colours, ident, f"Motif controls, CDE palette {name}", progress)
    return {"colors": ident, "plasma": "cde-" + name.lower(), "kvantum": ident, "desktop": colours["desktop"],
            "targets": ["plasma/desktoptheme/cde-" + name.lower()],
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
widgetStyle=kvantum
[kdeglobals][Icons]
Theme=CDECopper
[kcminputrc][Mouse]
cursorTheme=CDECopperCursors
[ksplashrc][KSplash]
Engine=KSplashQML
Theme=org.cde.copper.desktop
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
    # System Settings › Application Style lists Qt style plugins by key and
    # takes names from kstyle/themes/*.themerc. Kvantum brings none, so its
    # keys show as "kvantum" and "kvantum-dark"; the second only differs for
    # Kvantum themes with a dark variant, which CDE's palettes are not.
    write("kstyle/themes/kvantum.themerc", "[KDE]\nWidgetStyle=kvantum\n\n[Misc]\nName=CDE\n"
          "Comment=Motif controls in the CDE palette (Kvantum)\n")
    write("kstyle/themes/kvantum-dark.themerc", "[Desktop Entry]\nHidden=true\n\n[KDE]\nWidgetStyle=kvantum-dark\n\n[Misc]\nName=CDE (dark)\n")
    shutil.copytree(ROOT / "frontpanel", OUT / "plasma/plasmoids/org.cde.copper.frontpanel", dirs_exist_ok=True)
    # The style manager, a window of its own (plasmawindowed); it shares the
    # console's Motif bevel and shading.
    manager = OUT / "plasma/plasmoids/org.cde.copper.stylemanager"
    shutil.copytree(ROOT / "stylemanager", manager, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("Bevel.qml", "motif.js"):
        shutil.copy2(ROOT / "frontpanel/contents/ui" / name, manager / "contents/ui" / name)
    # The backdrop plugin's list of material tiles, for the Backdrop dialog.
    shutil.copy2(OUT / "plasma/wallpapers/org.cde.copper.backdrop/contents/ui/backdrops.js", manager / "contents/ui/backdrops.js")
    # IBM Plex Sans Condensed and IBM Plex Mono (SIL OFL 1.1), installed per user.
    shutil.copytree(ROOT / "fonts/IBMPlex", OUT / "fonts/CDECopper", dirs_exist_ok=True)
    # Plasma reads a global theme's desktop layout from exactly this path;
    # without it, choosing the theme with its layout falls back to Plasma's
    # default panel (Kickoff, task manager, clock) drawn in CDE's surfaces.
    (OUT / lnf / "contents/layouts").mkdir(parents=True, exist_ok=True)
    # Plasma looks for <shell>-layout.js of the shell it runs: Plasma's own,
    # or CDE Copper's (its lock screen). Without the second, applying the
    # theme with its layout under CDE's shell left a desktop without panels.
    for shell in ("org.kde.plasma.desktop", "org.cde.copper.shell"):
        shutil.copy2(ROOT / "layout.js", OUT / lnf / f"contents/layouts/{shell}-layout.js")
    # Start-up, lock and logout screens; the start-up screen tiles a backdrop
    # and shows the console's logo.
    shutil.copytree(ROOT / "lookandfeel/contents", OUT / lnf / "contents", dirs_exist_ok=True)
    images = OUT / lnf / "contents/splash/images"
    images.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT / "plasma/wallpapers/org.cde.copper.backdrop/contents/images/Copper/Lattice.png", images / "backdrop.png")
    shutil.copy2(OUT / "icons/CDECopper/scalable/all/cde-menu.svg", images / "logo.svg")
    for part, icon in SPLASH_ICONS.items():
        shutil.copy2(OUT / f"icons/CDECopper/22/all/{icon}.svg" if (OUT / f"icons/CDECopper/22/all/{icon}.svg").exists()
                     else OUT / f"icons/CDECopper/scalable/all/{icon}.svg", images / f"{part}.svg")
    write(lnf + "contents/splash/Colours.qml", splash_colours(P))
    # The lock screen: a shell package of its own (see shell/), with the same
    # colours, tile and logo.
    shell = "plasma/shells/org.cde.copper.shell/"
    shutil.copytree(ROOT / "shell", OUT / shell, dirs_exist_ok=True)
    meta = json.loads((ROOT / "shell/metadata.json").read_text())
    meta["KPlugin"]["Version"] = VERSION
    write(shell + "metadata.json", json.dumps(meta, indent=2))
    write(shell + "contents/lockscreen/Colours.qml", splash_colours(P))
    (OUT / shell / "contents/lockscreen/images").mkdir(parents=True, exist_ok=True)
    for name in ("backdrop.png", "logo.svg"):
        shutil.copy2(images / name, OUT / shell / "contents/lockscreen/images" / name)
    (OUT / lnf / "contents/previews").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "screenshots/splash-1920.png", OUT / lnf / "contents/previews/splash.png")
    # Shown in System Settings › Global Theme.
    for name in ("preview.png", "fullscreenpreview.png"):
        target = OUT / lnf / "contents/previews" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "screenshots/desktop-arranged-1920.png", target)
    night_theme(lnf)


# Plasma's day/night switching (Quick Settings, kdeglobals [KDE]
# DefaultLightLookAndFeel/DefaultDarkLookAndFeel) swaps global themes; the
# night one is CDE's darkest palette. Its colour scheme set, the console
# turns the rest (Kvantum, Plasma surfaces, backdrop) to that palette.
NIGHT = ("org.cde.copper.night", "CDE Night", "NorthernSky")


def night_theme(day):
    ident, name, palette = NIGHT
    lnf = f"plasma/look-and-feel/{ident}/"
    shutil.rmtree(OUT / lnf, ignore_errors=True)
    shutil.copytree(OUT / day, OUT / lnf)
    meta = metadata(ident, name, f"CDE Copper at night: the {palette} palette, for Plasma's day/night switching")
    meta["KPackageStructure"] = "Plasma/LookAndFeel"
    write(lnf + "metadata.json", json.dumps(meta, indent=2))
    # Only what differs from the day theme; the plasma theme follows when the
    # console applies the palette, and the backdrop stays as it is.
    defaults = (OUT / day / "contents/defaults").read_text()
    defaults = defaults.replace("ColorScheme=CDECopper", f"ColorScheme=CDE{palette}")
    defaults = defaults.split("[plasmarc][Theme]")[0] + defaults.split("[plasmarc][Theme]")[1].split("\n", 2)[2]
    defaults = defaults.split("[Wallpaper]")[0]
    write(lnf + "contents/defaults", defaults)
    import palettes
    write(lnf + "contents/splash/Colours.qml", splash_colours(palettes.theme(palette)))
    # Its own preview, so System Settings' day and night choice differ.
    for name in ("preview.png", "fullscreenpreview.png"):
        shutil.copy2(ROOT / "screenshots/desktop-night-1920.png", OUT / lnf / "contents/previews" / name)


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
    tabbox()
    arrange()
    backdrops_plugin()
    pictures()
    from i18n import compile_translations
    compile_translations(OUT)
    from icons import build_icons
    build_icons(OUT)
    from cursors import build_cursors
    build_cursors(OUT)
    from gtktheme import build_gtk
    build_gtk(OUT, P)
    from systemparts import build_system
    build_system(OUT, P)
    from kvantum import build_kvantum
    build_kvantum(OUT, P)
    other_assets()
    palette_schemes()
    print(f"CDE Copper {VERSION}: {sum(1 for p in OUT.rglob('*') if p.is_file())} files in {OUT}")


if __name__ == "__main__":
    main()
