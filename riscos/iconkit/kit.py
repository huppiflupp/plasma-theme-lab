"""Drawing kit for RISC Legacy's icons (DESIGN.md §8).

Every icon is drawn on a 48 x 48 grid into a Canvas, which collects the
SVG elements and gradient definitions (ids unique per icon). Two colour
worlds, from RISC OS's own sprites:

  ro4   RISC OS 4 (Sprites-RO400): pale green folders, grey cases, black
        outlines, flat colour with one highlight; for classic, 4 and the
        palettes
  ro5   RISC OS 5 (Sprites-Iyonix): blue folders, saturated colours, a
        blue-black outline, soft top-lit gradients; for 2026

Each drawing runs twice: large (the scalable file, 32 px and up) and
small (16 and 22 px): thicker lines, details left out where a drawing
asks `c.small`.

Only what QtSvg draws: paths, rects, circles, linear gradients, text
(TeX Gyre Heros, installed with the theme). No filters, no masks.
"""
import itertools

WORLDS = {
    "ro4": dict(
        ink="#000000", outline=1.3,
        folder=("#a9e8a0", "#7fc777"), folder_back=("#8fd486", "#5eaa57"), folder_line="#d8f7d2",
        page=("#ffffff", "#eef3f3"), page_fold="#c7d2d2",
        case=("#e6e6e6", "#b9b9b9"), case_top=("#f6f6f6", "#d6d6d6"), case_dark="#8c8c8c",
        screen=("#5a7fd8", "#1f3f9a"), metal=("#d9d9d9", "#8f8f8f"),
        blue="#1c4fd0", red="#dd0000", green="#00b000", yellow="#eedd00", orange="#ff9900",
        cyan="#00aadd", violet="#7a3fbf", brown="#9a5b21", grey="#777777", white="#ffffff",
        light="#ffffff", led="#00dd00", label_text="#ffffff", gradient=0.55,
    ),
    "ro5": dict(
        ink="#1b2230", outline=1.4,
        folder=("#8fd0ff", "#3d97e6"), folder_back=("#5fb4f0", "#2a7fd0"), folder_line="#ffffff",
        page=("#ffffff", "#dfe9f5"), page_fold="#c4d4e8",
        case=("#f3efe2", "#cfc8b2"), case_top=("#fffdf5", "#e6e0cc"), case_dark="#9a937c",
        screen=("#5fb4f0", "#174f9a"), metal=("#d6dbe2", "#7d8590"),
        blue="#2a7fd0", red="#d32f2f", green="#2f9e3a", yellow="#ffd75a", orange="#ef7d00",
        cyan="#1fb5d6", violet="#7b3fbf", brown="#b5651d", grey="#7d8590", white="#ffffff",
        light="#ffffff", led="#3ddc5a", label_text="#ffffff", gradient=1.0,
    ),
}
FONT = "TeX Gyre Heros,Helvetica,Arial,sans-serif"


def _mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


class Canvas:
    _ids = itertools.count()

    def __init__(self, world, small=False):
        self.w = WORLDS[world] if isinstance(world, str) else world
        self.world = world
        self.small = small
        self.parts = []
        self.defs = []
        self.tag = f"i{next(self._ids)}"
        self.lw = self.w["outline"] * (2.0 if small else 1.0)

    # ---- colours ----------------------------------------------------
    def __getitem__(self, key):
        return self.w[key]

    def grad(self, top, bottom=None, horizontal=False):
        """A top-lit gradient; ro4 flattens it towards one colour."""
        if isinstance(top, tuple):
            top, bottom = top
        if bottom is None:
            bottom = _mix(top, "#000000", 0.28)
        g = self.w["gradient"]
        top = _mix(bottom, top, g) if g < 1 else top
        id_ = f"{self.tag}g{len(self.defs)}"
        x2, y2 = (1, 0) if horizontal else (0, 1)
        self.defs.append(f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                         f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
                         f'</linearGradient>')
        return f"url(#{id_})"

    def lighten(self, color, t=0.35):
        return _mix(color, "#ffffff", t)

    def darken(self, color, t=0.3):
        return _mix(color, "#000000", t)

    # ---- primitives ---------------------------------------------------
    def _stroke(self, stroke, width):
        if stroke is None:
            return ""
        stroke = self.w["ink"] if stroke == "ink" else stroke
        width = self.lw if width is None else width * (1.6 if self.small else 1.0)
        return (f' stroke="{stroke}" stroke-width="{width:g}" stroke-linejoin="round"'
                f' stroke-linecap="round"')

    def path(self, d, fill="none", stroke="ink", width=None, opacity=None):
        o = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(f'<path d="{d}" fill="{fill}"{self._stroke(stroke, width)}{o}/>')

    def rect(self, x, y, w, h, fill, r=0, stroke="ink", width=None):
        self.parts.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" '
                          f'fill="{fill}"{self._stroke(stroke, width)}/>')

    def circle(self, cx, cy, r, fill, stroke="ink", width=None):
        self.parts.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}"{self._stroke(stroke, width)}/>')

    def ellipse(self, cx, cy, rx, ry, fill, stroke="ink", width=None):
        self.parts.append(f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" fill="{fill}"'
                          f'{self._stroke(stroke, width)}/>')

    def line(self, d, color="ink", width=1.6):
        self.path(d, "none", color, width)

    def text(self, x, y, s, size, fill, weight="bold", anchor="middle", italic=False):
        if self.small and size < 9:
            return                       # unreadable at 16 px: left out
        style = ' font-style="italic"' if italic else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        self.parts.append(f'<text x="{x:g}" y="{y:g}" font-family="{FONT}" font-size="{size:g}" '
                          f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{style}>{s}</text>')

    def group(self, transform, draw):
        """Draw into a translated/scaled group: draw(canvas)."""
        start = len(self.parts)
        draw(self)
        inner = self.parts[start:]
        del self.parts[start:]
        self.parts.append(f'<g transform="{transform}">' + "".join(inner) + "</g>")

    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.parts)}</svg>\n')
