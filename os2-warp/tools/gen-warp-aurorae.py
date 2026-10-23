#!/usr/bin/env python3
"""Warp Legacy's window frame as an SVG Aurorae theme, for the KDE Store.

Copied from CDE/tools/gen-motif-aurorae.py (CDE Copper, as of e976e470)
and drawn anew for OS/2's edges; nothing is imported from CDE/ (the
repository's CLAUDE.md: the themes share no files).

The theme's own frame is a QML decoration (decoration/), with six button
looks, the window's icon as the window menu and Neon's glow. The KDE
Store's "Window Decorations" category only installs SVG themes
(aurorae/themes/), so the store edition gets this approximation, drawn
for one variant at a time:

- the grey (Neon: navy) sizing border with OS/2's fixed edges: white and
  grey outside, grey and white inside (Neon: cyan and violet, the right
  corners pink);
- the title bar in the title colour between the buttons, a line below it;
- the buttons in Warp 4's look: raised squares with a black outline,
  cross, small and large square; Neon the glyphs cyan, close pink;
- Neon's glow as rings in the padding around the frame.

What it cannot do: the other five button looks, the gradients of Neon's
frame line and the glow of the glyphs (QtSvg draws no filters), a gap of
surface between the buttons and the title bar wider than one pixel, and
following another colour scheme (the colours are fixed when generated).

    store.py calls write_theme() once per variant.
"""
from pathlib import Path

BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]
STATES = ["active", "inactive", "hover", "pressed", "deactivated"]


class Frame:
    def __init__(self, palette, style, title=20, edge=4):
        P, s = palette, style
        self.th, self.e = title, edge
        self.g = s["glowWidth"]
        self.surface = P["surface"]
        self.light, self.dark, self.ink = s["light"], s["dark"], s["ink"]
        self.accent = s["accent"] if s["glowWidth"] else None   # Neon only
        self.glow = s["glow"]
        self.neon = self.accent is not None
        self.look = {
            "active": {"title": P["title_active"], "text": P["title_active_text"]},
            "inactive": {"title": P["title_inactive"], "text": P["title_inactive_text"]},
        }
        # the glyph colours: Neon's tube colours, classic black
        self.glyph_ink = s["light"] if self.neon else s["glyph"]
        self.close = self.accent if self.neon else s["glyph"]

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
            extra = f' fill-opacity="{opacity:.3f}"' if opacity is not None else ""
            out.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{extra}/>')
        return "".join(out)

    def lines(self, x, y, w, h, first, second, opacity=None):
        """One line round a rectangle: first at the top and left, second at
        the bottom and right (Bevel.qml)."""
        return (self.box(x, y, w - 1, 1, first, opacity) + self.box(x, y, 1, h - 1, first, opacity)
                + self.box(x, y + h - 1, w, 1, second, opacity) + self.box(x + w - 1, y, 1, h, second, opacity))

    def bevel(self, x, y, w, h, face, sunken=False):
        """OS/2's raised button (Bevel.qml, kind "button")."""
        light, dark, ink = self.light, self.dark, self.ink
        rings = [(ink, light), (dark, face)] if sunken else [(light, ink), (face, dark)]
        out = self.box(x, y, w, h, face)
        for i, (a, b) in enumerate(rings):
            out += self.lines(x + i, y + i, w - 2 * i, h - 2 * i, a, b)
        return out

    # -- the frame --------------------------------------------------------
    def art(self, look, width, height):
        """The whole frame at (0, 0), glow included."""
        e, th, g = self.e, self.th, self.g
        fw, fh = width - 2 * g, height - 2 * g          # the frame without glow
        out = []
        for i in range(g):                               # rings fading outwards
            n = i + 1
            out += self.lines(g - n, g - n, fw + 2 * n, fh + 2 * n, self.glow, self.glow,
                              0.55 * (1 - i / g) ** 2)
        out += self.box(g, g, fw, fh, self.surface)
        out += self.lines(g, g, fw, fh, self.light, self.dark)
        out += self.lines(g + e - 1, g + e - 1, fw - 2 * (e - 1), fh - 2 * (e - 1), self.dark, self.light)
        out += self.box(g + e, g + e, fw - 2 * e, th, look["title"])
        out += self.box(g + e, g + e + th, fw - 2 * e, 1, self.dark)
        return out

    def frame(self, prefix, look, ox, oy, width, height):
        """One nine-patch, drawn whole and cut into the nine cells, so the
        edges meet exactly at the cell borders."""
        e, th, g = self.e, self.th, self.g
        top, side = g + e + th + 1, g + e
        art = self.art(look, width, height)
        cells = {
            "topleft": (0, 0, side, top), "top": (side, 0, width - 2 * side, top),
            "topright": (width - side, 0, side, top),
            "left": (0, top, side, height - top - side), "center": (side, top, width - 2 * side, height - top - side),
            "right": (width - side, top, side, height - top - side),
            "bottomleft": (0, height - side, side, side), "bottom": (side, height - side, width - 2 * side, side),
            "bottomright": (width - side, height - side, side, side),
        }
        out = []
        for name, (cx, cy, cw, ch) in cells.items():
            piece = []
            for x, y, w, h, fill, opacity in art:
                x0, y0 = max(x, cx), max(y, cy)
                x1, y1 = min(x + w, cx + cw), min(y + h, cy + ch)
                if x1 > x0 and y1 > y0:
                    # Neon: both right corners glow pink (NeonFrame.qml).
                    if self.neon and name in ("topright", "bottomright") and fill in (self.light, self.dark):
                        fill = self.accent
                    piece.append((ox + x0, oy + y0, x1 - x0, y1 - y0, fill, opacity))
            # A transparent rectangle the size of the cell gives Aurorae its size.
            out.append(f'<g id="{prefix}-{name}"><rect x="{ox + cx}" y="{oy + cy}" width="{cw}" height="{ch}" '
                       f'fill="#000000" fill-opacity="0"/>{self.write(piece)}</g>')
        return out

    def maximized(self, prefix, look, ox, oy, width):
        """Maximized: no frame and no glow, the title row alone."""
        th = self.th
        art = (self.box(ox, oy, width, th + 1, self.surface) + self.box(ox, oy, width, th, look["title"])
               + self.box(ox, oy + th, width, 1, self.dark))
        return [f'<g id="{prefix}-center">{self.write(art)}</g>']

    def decoration(self):
        width, height, gap = 160 + 2 * self.g, 120 + 2 * self.g, 20
        parts = []
        parts += self.frame("decoration", self.look["active"], gap, gap, width, height)
        parts += self.frame("decoration-inactive", self.look["inactive"], gap, 2 * gap + height, width, height)
        y = 3 * gap + 2 * height
        parts += self.maximized("decoration-maximized", self.look["active"], gap, y, width)
        parts += self.maximized("decoration-maximized-inactive", self.look["inactive"], gap, y + self.th + 1 + gap, width)
        return self.svg(width + 2 * gap, y + 2 * (self.th + 1 + gap), parts)

    # -- buttons ----------------------------------------------------------
    def glyph(self, kind, x, y, s, pressed):
        """Warp 4's glyphs (WarpButton.qml, look 0)."""
        d = 1 if pressed else 0
        x, y = x + d, y + d
        ink = self.close if kind == "close" else self.glyph_ink

        def square(bx, by, w, top):
            return (self.box(bx, by, w, top, ink) + self.box(bx, by + w - 1, w, 1, ink)
                    + self.box(bx, by, 1, w, ink) + self.box(bx + w - 1, by, 1, w, ink))
        if kind == "close":
            c, r, t = s / 2, round(s * 0.25), max(2, round(s / 9))
            path = (f'M{x + c - r:g},{y + c - r:g} L{x + c + r:g},{y + c + r:g} '
                    f'M{x + c + r:g},{y + c - r:g} L{x + c - r:g},{y + c + r:g}')
            # Neon: a wider faint stroke under the line stands in for the glow.
            halo = (f'<path d="{path}" stroke="{ink}" stroke-opacity="0.35" stroke-width="{t + 3}" '
                    f'fill="none" stroke-linecap="round"/>') if self.neon else ""
            return (f'<g shape-rendering="geometricPrecision">{halo}<path d="{path}" stroke="{ink}" '
                    f'stroke-width="{t}" fill="none"/></g>')
        if kind == "minimize":
            w = max(4, round(s * 0.3))
            return self.write(square(x + round((s - w) / 2), y + round((s - w) / 2), w, 2))
        if kind == "maximize":
            w = round(s * 0.6)
            return self.write(square(x + round((s - w) / 2), y + round((s - w) / 2), w, 2))
        if kind == "restore":
            w = round(s * 0.42)
            o = round((s - w) / 2)
            back = square(x + o + 2, y + o - 2, w, 2)
            front = self.box(x + o - 2, y + o + 2, w, w, self.surface) + square(x + o - 2, y + o + 2, w, 2)
            return self.write(back + front)
        if kind == "menu":
            return ""                                    # Aurorae shows the window's icon
        text = {"alldesktops": "▣", "keepabove": "▴", "keepbelow": "▾", "shade": "‒", "help": "?"}.get(kind, "")
        return (f'<text x="{x + s / 2:g}" y="{y + s * 0.72:g}" font-size="{round(s * 0.55)}" font-weight="bold" '
                f'font-family="sans-serif" text-anchor="middle" fill="{ink}">{text}</text>')

    def button(self, kind):
        """A cell the title's height: surface, and the raised square one
        pixel inside it (the gap to the title bar)."""
        cell, gap = self.th, 4
        s = cell - 2
        parts = []
        for i, state in enumerate(STATES):
            x0, y0 = gap + i * (cell + gap), gap
            art = self.box(x0, y0, cell, cell, self.surface)
            if kind != "menu":
                art += self.bevel(x0 + 1, y0 + 1, s, s, self.surface, sunken=state == "pressed")
            glyph = self.glyph(kind, x0 + 1, y0 + 1, s, state == "pressed")
            if state in ("deactivated", "inactive") and glyph:
                glyph = f'<g opacity="{0.4 if state == "deactivated" else 0.7}">{glyph}</g>'
            parts.append(f'<g id="{state}-center">{self.write(art)}{glyph}</g>')
        return self.svg(gap + len(STATES) * (cell + gap), cell + 2 * gap, parts)

    @staticmethod
    def svg(width, height, parts):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">\n'
                '<!-- Generated by os2-warp/tools/gen-warp-aurorae.py; the ids are KWin\'s contract. -->\n'
                + "\n".join(parts) + "\n</svg>\n")

    def rc(self):
        def triple(h):
            return ",".join(str(int(h[i:i + 2], 16)) for i in (1, 3, 5))
        e, th, g = self.e, self.th, self.g
        return f"""[General]
ActiveTextColor={triple(self.look["active"]["text"])}
InactiveTextColor={triple(self.look["inactive"]["text"])}
TitleAlignment=Left
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
TitleEdgeBottom=1
TitleEdgeBottomMaximized=1
TitleEdgeLeft={e}
TitleEdgeLeftMaximized=0
TitleEdgeRight={e}
TitleEdgeRightMaximized=0
TitleBorderLeft=6
TitleBorderRight=6
TitleHeight={th}
ButtonWidth={th}
ButtonHeight={th}
ButtonSpacing=0
ButtonMarginTop=0
ExplicitButtonSpacer={th // 2}
PaddingTop={g}
PaddingBottom={g}
PaddingLeft={g}
PaddingRight={g}
"""


def write_theme(target, name, title, version, palette, style):
    """The theme folder target/name: decoration.svg, the buttons, the rc
    file and metadata.desktop."""
    frame = Frame(palette, style)
    target = Path(target) / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "decoration.svg").write_text(frame.decoration(), encoding="utf-8")
    for kind in BUTTONS:
        (target / f"{kind}.svg").write_text(frame.button(kind), encoding="utf-8")
    (target / f"{name}rc").write_text(frame.rc(), encoding="utf-8")
    (target / "metadata.desktop").write_text(f"""[Desktop Entry]
Name={title}
Comment=OS/2 Warp window frame (SVG edition of Warp Legacy's frame)
X-KDE-PluginInfo-Author=Warp Legacy contributors
X-KDE-PluginInfo-Name={name}
X-KDE-PluginInfo-Version={version}
X-KDE-PluginInfo-License=GPL-2.0-or-later
X-KDE-PluginInfo-Website=https://github.com/huppiflupp/warp-legacy
X-KDE-PluginInfo-Category=
""", encoding="utf-8")
    return target
