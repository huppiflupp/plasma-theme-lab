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
            # Kvantum: list and menu selection see-through, cyan-violet-pink
            selection_glow=("#3ad0ff", "#7a4dff", "#ff4fd8"),
            window_text="#e8f0ff", alt_window="#0a1230", button_hover="#16245c",
            button_pressed="#0a1232", groove="#0a1232")

# id suffix, display name, palette, decoration style, description
VARIANTS = [
    dict(key="", name="Warp Legacy", P=CLASSIC,
         style=dict(light="#ffffff", dark="#808080", ink="#000000", glyph="#000000", glow="#000000",
                    accent="#00000000", glowWidth=0),
         wallpaper=("org.warplegacy.teal", "Warp Teal", "Warp 3's plain teal desktop"),
         picture="warp4-wirbel-violett",
         # Named in both variants: a global theme only writes the keys it
         # carries, and Neon's icons stayed after switching back.
         icons="WarpLegacy",
         # System Monitor chart colours, in the order a face hands them out
         # (session/warp-legacy-sysmon): OS/2's VGA colours, dark enough for
         # lines on white; neighbours differ in hue (download blue, upload red).
         sysmon=["#2400a8", "#a80000", "#00a0a0", "#600080", "#00802a", "#a85400"],
         description="OS/2 Warp 4: grey 3D surfaces, blue title bars"),
    dict(key="neon", name="Warp Legacy Neon", P=NEON,
         style=dict(light="#48cffe", dark="#7a4dff", ink="#020617", glyph="#ffffff", glow="#2a5cff",
                    # the pink towards the frames' bottom right corner (§9a)
                    accent="#ff4fd8", glowWidth=8),
         wallpaper=("org.warplegacy.neon", "Warp Night", "Deep navy for the Neon variant"),
         # Closest to the concept's background: dark blue, streaks of light
         # at the top right only (the brighter neon-bogen-horizont before).
         picture="dunkel-lichtbogen-rechts", icons="WarpLegacyNeon2026Violett",
         # Meter cyan first (single gauges), then pink, blue, violet: the
         # concept's neon tubes, alternating warm and cold.
         sysmon=["#3ad0ff", "#ff4fd8", "#1a6fe0", "#b48cff", "#3ddc97", "#ffb347"],
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
    # The Neon frame line is shared with the plasmoids (common/).
    shutil.copy2(ROOT / "common/NeonFrame.qml", OUT / base / "contents/ui/NeonFrame.qml")
    s = v["style"]
    props = "\n".join(f'    readonly property color {k}: "{s[k]}"' for k in ("light", "dark", "ink", "glyph", "glow", "accent"))
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
    ("neon-bogen-horizont", "Neon Arc Horizon", "Neon-Bogenhorizont", "Planet horizon with a violet-pink rim and soft arcs of light"),
    ("neon-horizont-violett", "Neon Horizon Violet", "Neon-Horizont Violett", "Planet horizon in violet and pink, a soft glow instead of a sun"),
    ("neon-orbit-pink", "Neon Orbits", "Neon-Bahnen", "Pink and violet orbits on navy"),
    ("neon-polarlicht-magenta", "Neon Aurora Magenta", "Neon-Polarlicht Magenta", "Magenta and violet aurora over a dark horizon"),
    ("neon-seide", "Neon Silk", "Neon-Seide", "Translucent pink and violet ribbons"),
    ("neon-gitter-violett", "Neon Grid Violet", "Neon-Gitter Violett", "A quiet violet and pink perspective grid"),
    ("neon-nebel", "Neon Mist", "Neon-Nebel", "A soft violet-pink bank of mist under a starry sky"),
    # Darker, after the concept's background (measured mean luminance 0.046):
    # the window edges stand out against them.
    ("dunkel-lichtbogen-rechts", "Dark Light Streaks", "Dunkle Lichtstreifen", "Diagonal streaks of light at the top right, deep blue"),
    ("dunkel-horizont-boegen", "Dark Horizon Arcs", "Dunkler Horizont mit Bögen", "Horizon and arcs of light in the lower right corner"),
    ("dunkel-wirbel-neon", "Dark Neon Swirl", "Dunkler Neon-Wirbel", "Fine arcs in cyan, violet and pink"),
    ("dunkel-horizont-pink", "Dark Horizon Pink", "Dunkler Horizont Pink", "A planet's rim with a pink line of light"),
    ("dunkel-wellen-cyan", "Dark Waves Cyan", "Dunkle Wellen Cyan", "A band of glassy waves along the bottom"),
    ("dunkel-polarlicht-cyan", "Dark Aurora Cyan", "Dunkles Polarlicht Cyan", "Cyan aurora rising from the bottom edge"),
    ("dunkel-horizont-cyan", "Dark Horizon Cyan", "Dunkler Horizont Cyan", "A flat horizon with a cyan atmosphere"),
    ("dunkel-nebel-indigo", "Dark Nebula Indigo", "Dunkler Nebel Indigo", "Indigo nebula across a field of stars"),
    ("dunkel-nebel-rand", "Dark Nebula Edge", "Dunkler Nebelrand", "A swirl of gas in the lower right"),
    ("dunkel-orbit-cyan", "Dark Orbit Cyan", "Dunkler Orbit Cyan", "A single cyan arc on black"),
    ("dunkel-orbit-violett", "Dark Orbit Violet", "Dunkler Orbit Violett", "Violet arcs of orbits, almost black"),
    ("dunkel-rauch-pink", "Dark Smoke Pink", "Dunkler Rauch Pink", "A plume of smoke lit in pink"),
    ("dunkel-schiefer-neon", "Dark Slate Neon", "Dunkler Schiefer Neon", "Slate with a neon line along the floor"),
    ("dunkel-seide-violett", "Dark Silk Violet", "Dunkle Seide Violett", "Dark silk with a violet sheen"),
    ("dunkel-wellen-schwarz", "Dark Lines", "Dunkle Linien", "Thin lines of light on black"),
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
    # The classic set (icons_classic.py): Warp 4's yellow folders and grey
    # devices, fixed bitmaps in every size Dolphin offers.
    from icons_classic import build_icons as build_classic
    build_classic(OUT / "icons")
    from icons_neon2026 import build_icons as build_2026
    build_2026(OUT / "icons")
    # The same with violet light edges where the concept's icons were cyan
    # (icons-neon2026/masters-violett), to choose in System Settings.
    build_2026(OUT / "icons", name="WarpLegacyNeon2026Violett", violet=True)
    # WARP_SKIP_ICONS=1: leave the first set out of a quick test build (it
    # takes a while, and is reworked on its own).
    if os.environ.get("WARP_SKIP_ICONS"):
        return
    from icons_neon import build_icons
    build_icons(OUT / "icons")


def fonts():
    """Installed per user into ~/.local/share/fonts/WarpLegacy."""
    shutil.copytree(ROOT / "fonts/IBMPlex", OUT / "fonts/WarpLegacy", dirs_exist_ok=True)


# Konsole after the concept's "Command Prompt" (reference/neon-2026.png):
# near-black navy, cyan text, white for what stands out. Classic: OS/2's
# command window, black with light grey. The 16 ANSI colours keep their
# meaning (ls, git), shifted into each variant's world.
KONSOLE = {
    "": dict(name="Warp Legacy", background="#000000", foreground="#c0c0c0", intense="#ffffff",
             colours=["#000000", "#a80000", "#00a800", "#a85400", "#2400a8", "#a800a8", "#00a8a8", "#c0c0c0",
                      "#545454", "#fc5454", "#54fc54", "#fcfc54", "#5454fc", "#fc54fc", "#54fcfc", "#ffffff"]),
    # Black, not navy, behind the cyan: the most contrast for the text (the
    # user's choice, set in the VM 21.10.2026).
    "neon": dict(name="Warp Legacy Neon", background="#000000", foreground="#3ad0ff", intense="#e8f6ff",
                 colours=["#02060f", "#ff5a7a", "#3ddc97", "#ffb347", "#3a7bff", "#c03aff", "#3ad0ff", "#9fd8ee",
                          "#3a4a78", "#ff8aa2", "#7cf0bd", "#ffd08a", "#7aa6ff", "#ff4fd8", "#9fe9ff", "#e8f6ff"]),
}


def konsole(v):
    k = KONSOLE[v["key"]]
    konsole_files(k, ids(v)["scheme"], k["name"], opacity=1)
    # Neon also as a see-through profile over the desktop (the user's
    # setting: fully transparent, no blur).
    if v["key"] == "neon":
        konsole_files(k, ids(v)["scheme"] + "Transparent", k["name"] + " (transparent)", opacity=0)


def konsole_files(k, scheme, name, opacity):
    lines = ["[General]", f"Description={name}", f"Opacity={opacity}", "Blur=false", "Wallpaper=",
             "", "[Background]", f"Color={rgb(k['background'])}", "", "[BackgroundIntense]", f"Color={rgb(k['background'])}",
             "", "[Foreground]", f"Color={rgb(k['foreground'])}", "", "[ForegroundIntense]", f"Color={rgb(k['intense'])}"]
    for i, c in enumerate(k["colours"][:8]):
        lines += ["", f"[Color{i}]", f"Color={rgb(c)}", "", f"[Color{i}Intense]", f"Color={rgb(k['colours'][i + 8])}",
                  "", f"[Color{i}Faint]", f"Color={rgb(c)}"]
    write(f"konsole/{scheme}.colorscheme", "\n".join(lines) + "\n")
    write(f"konsole/{name}.profile", f"""[General]
Name={name}
Parent=FALLBACK/
TerminalMargin=8

[Appearance]
ColorScheme={scheme}
Font={MONO_FONT.replace(',10,', ',11,')}
UseFontLineChararacters=true

[Cursor Options]
CursorShape=2

[Scrolling]
HistoryMode=1
HistorySize=10000
""")


def session():
    """warp-legacy-sync at login (session/): the Kvantum theme, the
    button order and the System Monitor's chart colours follow the variant
    chosen in System Settings."""
    target = OUT / "warp-legacy/warp-legacy-sync"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "session/warp-legacy-sync", target)
    shutil.copy2(ROOT / "session/warp-wallpaper", target.parent / "warp-wallpaper")
    shutil.copy2(ROOT / "session/warp-legacy-sysmon", target.parent / "warp-legacy-sysmon")
    # One line per variant: the look-and-feel id, then the chart colours.
    write("warp-legacy/sysmon-colors",
          "".join(f"{ids(v)['lnf']} {' '.join(v['sysmon'])}\n" for v in VARIANTS))
    write("config/autostart/warp-legacy-sync.desktop",
          "[Desktop Entry]\nType=Application\nName=Warp Legacy\n"
          # The path is put in by install.sh: autostart does not expand
          # $HOME in Exec= (exit 127 in the VM).
          "Exec=@SYNC@\n"
          "X-KDE-autostart-phase=1\nNoDisplay=true\n")


def plasmoids():
    """The panels: one plasmoid each, shared by both variants (they take
    their edge colours from the colour scheme's brightness). The pieces in
    common/ (edges, buttons, launching, the window list) go into each, as a
    plasmoid can only import files of its own package."""
    for source, id_ in (("launchpad", "org.warplegacy.launchpad"), ("warpbar", "org.warplegacy.warpbar"),
                       ("controlstrip", "org.warplegacy.controlstrip"), ("tablauncher", "org.warplegacy.tablauncher"),
                       ("taskbar", "org.warplegacy.taskbar")):
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
    # The pictures System Settings › Global Theme shows (previews/, VM
    # screenshots of the variant with its layout).
    key = v["key"] or "classic"
    previews = OUT / base / "contents/previews"
    previews.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / f"previews/{key}.png", previews / "preview.png")
    shutil.copy2(ROOT / f"previews/{key}-full.jpg", previews / "fullscreenpreview.jpg")
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
        konsole(v)
    pictures()
    from i18n import compile_translations
    compile_translations(OUT)
    icons()
    fonts()
    session()
    plasmoids()
    print(f"Warp Legacy {VERSION} ({', '.join(v['name'] for v in VARIANTS)}) built in {OUT}")


if __name__ == "__main__":
    main()
