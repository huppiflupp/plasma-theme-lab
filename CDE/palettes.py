#!/usr/bin/env python3
"""CDE colour palettes, shaded the way Motif shades them.

The .dp files in palettes/cde/ come unchanged from the CDE source tree
(programs/palettes, LGPL-2.0-or-later, see palettes/README.md). Each holds
eight colour sets as 16-bit X colours. dtwm and Motif give them fixed roles
(Motif lib/Xm/ColorObj.c, dtwm Dtwm.defs):

    1 active window frame       5 primary: window and dialog surfaces
    2 inactive window frame     6 secondary: menu bars, menus, dialogs
    3 workspace / backdrop      7 (further workspace buttons)
    4 text and list areas       8 front panel

Foreground, select, top-shadow and bottom-shadow colours are not stored in
the palette; Motif derives them from the background. calculate() is a
transcription of CalculateColorsRGB() from Motif lib/Xm/Color.c with the
default thresholds (dark 20, light 93, foreground 70).

    python3 palettes.py            # list the palettes
    python3 palettes.py Alpine     # print the derived theme colours
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "palettes" / "cde"
MAX = 65535
PERCENTILE = MAX // 100
LITE_THRESHOLD, DARK_THRESHOLD, FG_THRESHOLD = 93 * PERCENTILE, 20 * PERCENTILE, 70 * PERCENTILE


def brightness(c):
    r, g, b = c
    intensity = (r + g + b) // 3
    luminosity = int(0.30 * r + 0.59 * g + 0.11 * b)
    light = (min(c) + max(c)) // 2
    return (intensity * 75 + light * 0 + luminosity * 25) // 100


def calculate(bg):
    """Return fg, select, top shadow and bottom shadow for a 16-bit colour."""
    level = brightness(bg)
    fg = (0, 0, 0) if level > FG_THRESHOLD else (MAX, MAX, MAX)
    if level < DARK_THRESHOLD:
        sel = tuple(v + 15 * (MAX - v) // 100 for v in bg)
        bs = tuple(v + 30 * (MAX - v) // 100 for v in bg)
        ts = tuple(v + 50 * (MAX - v) // 100 for v in bg)
    elif level > LITE_THRESHOLD:
        sel = tuple(v - v * 15 // 100 for v in bg)
        bs = tuple(v - v * 40 // 100 for v in bg)
        ts = tuple(v - v * 20 // 100 for v in bg)
    else:
        # C division truncates towards zero; Python's // would floor the
        # negative bottom-shadow term and darken by one percent too much.
        f_sel = 15 + int(level * (15 - 15) / MAX)
        f_bs = 60 + int(level * (40 - 60) / MAX)
        f_ts = 50 + int(level * (60 - 50) / MAX)
        sel = tuple(v - v * f_sel // 100 for v in bg)
        bs = tuple(v - v * f_bs // 100 for v in bg)
        ts = tuple(v + f_ts * (MAX - v) // 100 for v in bg)
    return fg, sel, ts, bs


def hex8(c):
    return "#" + "".join(f"{v >> 8:02x}" for v in c)


def luminance(color):
    """WCAG relative luminance of #rrggbb."""
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(color[i:i+2], 16)) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable(bg):
    """Black or white, whichever reads better on bg.

    Motif decides by a fixed brightness threshold (70 %) and puts white text
    on many mid-tone CDE surfaces, often below 3:1. The shadows stay Motif's;
    only the text colour is chosen by measured contrast."""
    return "#000000" if contrast(bg, "#000000") >= contrast(bg, "#ffffff") else "#ffffff"


def legible(color, bg, toward, target=4.5):
    """Move color toward `toward` until it reaches target contrast on bg."""
    for step in range(21):
        candidate = mix(color, toward, step / 20)
        if contrast(candidate, bg) >= target:
            return candidate
    return toward


def mix(a, b, t):
    """Blend two #rrggbb colours, t=0 gives a."""
    pa = [int(a[i:i+2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def names():
    # Black, White, BlackWhite and WhiteBlack are the monochrome palettes of
    # CDE's black-and-white mode; they hold colour names, not eight sets.
    return sorted(p.stem for p in SOURCE.glob("*.dp") if p.read_text().lstrip().startswith("#"))


def load(name):
    path = SOURCE / f"{name}.dp"
    if path.parent != SOURCE or not path.is_file():
        raise KeyError(f"Unknown CDE palette {name!r}; available: {', '.join(names())}")
    sets = []
    for line in path.read_text().split():
        value = line.strip().lstrip("#")
        if len(value) == 12:
            sets.append(tuple(int(value[i:i+4], 16) for i in (0, 4, 8)))
    if len(sets) < 8:
        raise ValueError(f"{path} holds {len(sets)} colour sets, expected 8")
    return [colour_set(bg) for bg in sets[:8]]


def colour_set(bg):
    """Background (16-bit tuple or #rrggbb) with Motif's derived colours."""
    if isinstance(bg, str):
        bg = tuple(int(bg[i:i+2], 16) * 257 for i in (1, 3, 5))
    fg, sel, ts, bs = calculate(bg)
    return {"bg": hex8(bg), "fg": readable(hex8(bg)), "motif_fg": hex8(fg),
            "sel": hex8(sel), "ts": hex8(ts), "bs": hex8(bs)}


def copper_desktop():
    """The workspace colour set of CDE Copper: its desktop teal."""
    return colour_set("#086875")


# CDE's front panel gives every workspace button its own colour: One to
# Four take colour sets 3, 5, 6 and 7 of the palette (checked against a
# screenshot of CDE 2.x with the Default palette). Further workspaces repeat
# them. CDE Copper's four follow the same pattern from its own colours.
WORKSPACE_SETS = (3, 5, 6, 7)
COPPER_WORKSPACES = ("#649099", "#c4d2d0", "#2e7180", "#e8874f")


def workspace_colours(name):
    if name == "Copper":
        return [colour_set(c) for c in COPPER_WORKSPACES]
    sets = load(name)
    return [sets[i - 1] for i in WORKSPACE_SETS]


def theme(name):
    """Map a CDE palette onto the colour keys the CDE Copper generators use."""
    s = load(name)
    active, inactive, desk, text, primary, secondary, _, panel = s
    return dict(
        flaeche=primary["bg"], hell=primary["ts"], dunkel=primary["bs"], text=primary["fg"],
        text2=legible(mix(primary["fg"], primary["bg"], 0.4), primary["bg"], primary["fg"]),
        link=legible(desk["bg"], primary["bg"], primary["fg"]),
        rahmen=mix(primary["bs"], "#000000", 0.55),
        karo=mix(primary["bg"], primary["ts"], 0.5),
        fenster=text["bg"], fenster_text=text["fg"],
        menue=secondary["bg"], menue_text=secondary["fg"],
        panel=panel["bg"], panel_text=panel["fg"], panel_hell=panel["ts"], panel_dunkel=panel["bs"],
        kopf_aktiv=active["bg"], kopf_aktiv_text=active["fg"],
        kopf_inaktiv=inactive["bg"], kopf_inaktiv_text=inactive["fg"],
        aktiv=active["bg"], auswahl=active["bg"], auswahl_text=active["fg"], hover=active["ts"],
        desktop=desk["bg"],
        warnung="#aa571b", fehler="#a32626", positiv="#24643d",
        knopf_hover=mix(primary["bg"], primary["ts"], 0.3),
        knopf_gedrueckt=primary["sel"],
        rille=mix(primary["bg"], primary["bs"], 0.3),
        inaktiv_text=mix(primary["fg"], primary["bg"], 0.55),
        alt_fenster=mix(text["bg"], text["sel"], 0.35),
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n".join(names()))
    else:
        for key, value in theme(sys.argv[1]).items():
            print(f"{key:18} {value}")
