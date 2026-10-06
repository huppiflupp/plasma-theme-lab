#!/usr/bin/env python3
"""CDE Copper's window frame as an SVG Aurorae theme, for the KDE Store.

The theme's own frame is a QML decoration (decoration/), which follows the
colour scheme and draws the mwm corner handles. The KDE Store's "Window
Decorations" category only installs SVG themes (aurorae/themes/), so the
store edition gets this approximation of it, drawn for one colour scheme:

- a raised frame, two-pixel bevels when active, one when inactive (the
  focus shows in the structure, not only in the colour);
- a title bar of separately shadowed parts: window menu, title, minimize
  (small square), maximize (large square, pressed in while maximized) and
  close (a cross in the title ink); Aurorae shows the window's icon on the
  menu button instead of mwm's bar;
- the short hard shadow to the lower right, drawn in the padding.

What it cannot do: the grooves that cut mwm's corner handles off the
edges (an Aurorae frame is a nine-patch whose edges are stretched), and
following another palette (the colours are fixed when generated).

    gen-motif-aurorae.py --scheme build/color-schemes/CDECopper.colors \\
        --name CDECopper --title "CDE Copper" -o store/aurorae
"""
import argparse
import configparser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from palettes import calculate, hex8, mix  # noqa: E402

BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]
STATES = ["active", "inactive", "hover", "pressed", "deactivated"]


def rgb(text):
    return tuple(int(v) for v in text.split(",")[:3])


def shades(colour):
    """Motif's top and bottom shadow for an 8-bit colour, as #rrggbb."""
    wide = tuple(v * 257 for v in colour)
    _, _, top, bottom = calculate(wide)
    return hex8(top), hex8(bottom)


def hexrgb(colour):
    return "#%02x%02x%02x" % colour


class Frame:
    def __init__(self, scheme, title=22, edge=6, shadow=4):
        cfg = configparser.ConfigParser(interpolation=None, strict=False)
        cfg.read(scheme, encoding="utf-8")
        wm = cfg["WM"]
        self.th, self.e, self.sh = title, edge, shadow
        self.look = {}
        for state, key in (("active", "active"), ("inactive", "inactive")):
            face = hexrgb(rgb(wm[key + "Background"]))
            top, bottom = shades(rgb(wm[key + "Background"]))
            self.look[state] = {"face": face, "top": top, "bottom": bottom,
                                "ink": hexrgb(rgb(wm[key + "Foreground"])),
                                "bevel": 2 if state == "active" else 1,
                                "hover": mix(face, top, 0.22)}

    # -- drawing helpers ------------------------------------------------
    # Shapes are (x, y, w, h, fill, opacity) rectangles until written out,
    # so the frame can be cut into its nine cells by arithmetic (QtSvg's
    # support for clip paths is not to be relied on).
    @staticmethod
    def box(x, y, w, h, fill, opacity=None):
        return [(x, y, w, h, fill, opacity)] if w > 0 and h > 0 else []

    @staticmethod
    def write(shapes):
        out = []
        for x, y, w, h, fill, opacity in shapes:
            extra = f' fill-opacity="{opacity}"' if opacity is not None else ""
            out.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{extra}/>')
        return "".join(out)

    def bevel(self, x, y, w, h, face, light, dark, thickness, sunken=False):
        """A Motif shadowed rectangle, as Bevel.qml draws it."""
        first, second = (dark, light) if sunken else (light, dark)
        out = self.box(x, y, w, h, face)
        for i in range(thickness):
            out += self.box(x + i, y + i, w - 2 * i - 1, 1, first)
            out += self.box(x + i, y + i, 1, h - 2 * i - 1, first)
            out += self.box(x + i + 1, y + h - i - 1, w - 2 * i - 1, 1, second)
            out += self.box(x + w - i - 1, y + i + 1, 1, h - 2 * i - 1, second)
        return out

    # -- the frame --------------------------------------------------------
    def frame(self, prefix, look, ox, oy, width, height):
        """One nine-patch: the frame with its title bar and the shadow,
        drawn whole and cut into the nine cells, so the bevels meet exactly
        at the cell borders."""
        e, th, sh, b = self.e, self.th, self.sh, look["bevel"]
        top = e + th
        fw, fh = width - sh, height - sh            # the frame without shadow
        # The shadow, cut where the frame covers it (it is translucent).
        art = self.box(fw, sh, sh, fh, "#000000", 0.35) + self.box(sh, fh, fw - sh, sh, "#000000", 0.35)
        art += self.bevel(0, 0, fw, fh, look["face"], look["top"], look["bottom"], b)
        # The title: its own raised part between the frame's edges. Only its
        # top and bottom shadows: Aurorae stretches the top cell, and the
        # buttons cover the title's ends.
        for i in range(b):
            art += self.box(e, e + i, fw - 2 * e, 1, look["top"])
            art += self.box(e, e + th - 1 - i, fw - 2 * e, 1, look["bottom"])

        cells = {
            "topleft": (0, 0, e, top), "top": (e, 0, width - 2 * e - sh, top),
            "topright": (width - e - sh, 0, e + sh, top),
            "left": (0, top, e, height - top - e - sh), "center": (e, top, width - 2 * e - sh, height - top - e - sh),
            "right": (width - e - sh, top, e + sh, height - top - e - sh),
            "bottomleft": (0, height - e - sh, e, e + sh), "bottom": (e, height - e - sh, width - 2 * e - sh, e + sh),
            "bottomright": (width - e - sh, height - e - sh, e + sh, e + sh),
        }
        out = []
        for name, (cx, cy, cw, ch) in cells.items():
            piece = []
            for x, y, w, h, fill, opacity in art:
                x0, y0 = max(x, cx), max(y, cy)
                x1, y1 = min(x + w, cx + cw), min(y + h, cy + ch)
                if x1 > x0 and y1 > y0:
                    piece.append((ox + x0, oy + y0, x1 - x0, y1 - y0, fill, opacity))
            # A transparent rectangle the size of the cell gives Aurorae its size.
            out.append(f'<g id="{prefix}-{name}"><rect x="{ox + cx}" y="{oy + cy}" width="{cw}" height="{ch}" '
                       f'fill="#000000" fill-opacity="0"/>{self.write(piece)}</g>')
        return out

    def maximized(self, prefix, look, ox, oy, width):
        """Maximized: no frame, the title bar alone."""
        return [f'<g id="{prefix}-center">'
                + self.write(self.bevel(ox, oy, width, self.th, look["face"], look["top"], look["bottom"], look["bevel"]))
                + '</g>']

    def decoration(self):
        width, height, gap = 160, 120, 20
        parts = []
        parts += self.frame("decoration", self.look["active"], gap, gap, width, height)
        parts += self.frame("decoration-inactive", self.look["inactive"], gap, 2 * gap + height, width, height)
        y = 3 * gap + 2 * height
        parts += self.maximized("decoration-maximized", self.look["active"], gap, y, width)
        parts += self.maximized("decoration-maximized-inactive", self.look["inactive"], gap, y + self.th + gap, width)
        total_h = y + 2 * (self.th + gap)
        return self.svg(width + 2 * gap, total_h, parts)

    # -- buttons ----------------------------------------------------------
    def glyph(self, kind, x, y, s, look, pressed):
        """The mwm glyphs: raised bar, small and large squares; close and
        the rarer buttons in the title ink."""
        face, light, dark, ink = look["face"], look["top"], look["bottom"], look["ink"]
        d = 1 if pressed else 0
        x, y = x + d, y + d
        if kind == "menu":
            w, h = round(s * 0.56), max(3, round(s * 0.2))
            return self.write(self.bevel(x + round((s - w) / 2), y + round((s - h) / 2), w, h, face, light, dark, 1))
        if kind == "minimize":
            w = max(3, round(s * 0.24))
            return self.write(self.bevel(x + round((s - w) / 2), y + round((s - w) / 2), w, w, face, light, dark, 1))
        if kind in ("maximize", "restore"):
            w = round(s * 0.58)
            return self.write(self.bevel(x + round((s - w) / 2), y + round((s - w) / 2), w, w, face, light, dark, 1,
                                         sunken=kind == "restore"))
        if kind == "close":
            c, r, t = s / 2, round(s * 0.46) * 0.65, max(2, round(s / 12))
            return (f'<path d="M{x + c - r:g},{y + c - r:g} L{x + c + r:g},{y + c + r:g} '
                    f'M{x + c + r:g},{y + c - r:g} L{x + c - r:g},{y + c + r:g}" stroke="{ink}" '
                    f'stroke-width="{t}" fill="none"/>')
        text = {"alldesktops": "▣", "keepabove": "▴", "keepbelow": "▾", "shade": "‒", "help": "?"}.get(kind, "")
        return (f'<text x="{x + s / 2:g}" y="{y + s * 0.72:g}" font-size="{round(s * 0.55)}" font-weight="bold" '
                f'font-family="sans-serif" text-anchor="middle" fill="{ink}">{text}</text>')

    def button(self, kind):
        s, gap = self.th, 4
        parts = []
        for i, state in enumerate(STATES):
            look = dict(self.look["inactive" if state == "inactive" else "active"])
            pressed = state == "pressed"
            if state == "hover":
                look["face"] = look["hover"]
            x, y = gap + i * (s + gap), gap
            art = self.write(self.bevel(x, y, s, s, look["face"], look["top"], look["bottom"], look["bevel"], sunken=pressed))
            glyph = self.glyph(kind, x, y, s, dict(look, face=self.look["inactive" if state == "inactive" else "active"]["face"]), pressed)
            if state == "deactivated":
                glyph = f'<g opacity="0.45">{glyph}</g>'
            parts.append(f'<g id="{state}-center">{art}{glyph}</g>')
        return self.svg(gap + len(STATES) * (s + gap), s + 2 * gap, parts)

    @staticmethod
    def svg(width, height, parts):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">\n'
                '<!-- Generated by CDE/tools/gen-motif-aurorae.py; the ids are KWin\'s contract. -->\n'
                + "\n".join(parts) + "\n</svg>\n")

    def rc(self):
        def triple(h):
            return ",".join(str(int(h[i:i + 2], 16)) for i in (1, 3, 5))
        e, th = self.e, self.th
        return f"""[General]
ActiveTextColor={triple(self.look["active"]["ink"])}
InactiveTextColor={triple(self.look["inactive"]["ink"])}
TitleAlignment=Center
TitleVerticalAlignment=Center
UseTextShadow=false
Animation=0
Shadow=false

[Layout]
BorderLeft={e}
BorderRight={e}
BorderBottom={e}
TitleEdgeTop={e}
TitleEdgeTopMaximized=0
TitleEdgeBottom=0
TitleEdgeBottomMaximized=0
TitleEdgeLeft={e}
TitleEdgeLeftMaximized=0
TitleEdgeRight={e}
TitleEdgeRightMaximized=0
TitleBorderLeft=0
TitleBorderRight=0
TitleHeight={th}
ButtonWidth={th}
ButtonHeight={th}
ButtonSpacing=0
ButtonMarginTop=0
ExplicitButtonSpacer={th // 2}
PaddingTop=0
PaddingBottom={self.sh}
PaddingLeft=0
PaddingRight={self.sh}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scheme", type=Path, required=True, help="a .colors file; its [WM] colours are used")
    ap.add_argument("--name", required=True, help="theme directory name (Aurorae id __aurorae__svg__NAME)")
    ap.add_argument("--title", required=True, help="name shown in System Settings")
    ap.add_argument("--version", default="0.0.0")
    ap.add_argument("-o", "--output", type=Path, required=True)
    args = ap.parse_args()

    frame = Frame(args.scheme)
    target = args.output / args.name
    target.mkdir(parents=True, exist_ok=True)
    (target / "decoration.svg").write_text(frame.decoration(), encoding="utf-8")
    for kind in BUTTONS:
        (target / f"{kind}.svg").write_text(frame.button(kind), encoding="utf-8")
    (target / f"{args.name}rc").write_text(frame.rc(), encoding="utf-8")
    (target / "metadata.desktop").write_text(f"""[Desktop Entry]
Name={args.title}
Comment=Motif window frame after mwm (SVG edition of CDE Copper's frame)
X-KDE-PluginInfo-Author=CDE Copper contributors
X-KDE-PluginInfo-Name={args.name}
X-KDE-PluginInfo-Version={args.version}
X-KDE-PluginInfo-License=GPL-2.0-or-later
X-KDE-PluginInfo-Website=https://github.com/huppiflupp/plasma-theme-lab
X-KDE-PluginInfo-Category=
""", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
