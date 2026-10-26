"""Aurorae window decoration from a palette (after tools/gen-aurorae.py).

Theme Forge's own version: palette, corner shape, button shape, title
alignment and description are parameters. The element ids are the contract
with KWin — if one is missing, KWin draws nothing there, without a message.

Two rules from the lab (guide/01) that apply here:
* The center area is NOT transparent: when the user turns the border width
  up, the difference falls into center — transparent, one would see the
  desktop shine through there.
* Buttons consist of only one center element per state, the symbol lies
  inside it (Aurorae supports no borders on buttons).
"""
import math

from . import material
from .palette import readable, luminance, mix, on, shift
from .plasmasvg import corner_polygons

BUTTON_STATES = ["active", "inactive", "hover", "pressed", "deactivated"]
BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]


def _rgb(h):
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


class Aurorae:
    def __init__(self, palette, title_height=24, border=4, outer=1, bevel=1,
                 button_size=16, corner_style="square", radius=0, glow=0,
                 button_shape="square", title_align="left", textures=None):
        self.p = palette
        # Material mode: {"title_active", "title_inactive", "frame"} → tinted
        # sheets (PIL). Then: texture in the fields, rivets, title channel,
        # buttons as metal plates with a glowing symbol.
        self.tex = textures
        self.th = title_height
        self.cs = corner_style if radius > 0 else "square"
        self.radius = radius
        self.outer, self.bevel, self.glow = outer, bevel, glow
        # The corner must fit into the corner field: bevel/rounding plus lines.
        self.border = max(border, radius + 1) if self.cs != "square" else border
        self.bg = button_size
        self.button_shape = button_shape
        self.title_align = title_align

    def _patch(self, prefix, ox, oy, width, height, title):
        r, a, b, g = self.border, self.outer, self.bevel, self.glow
        P = self.p
        surface = P["surface"]
        t = []

        def rect(x, y, w, h, colour):
            if w > 0 and h > 0:
                t.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{colour}"/>')

        tex = None
        if self.tex:
            tex = self.tex["title_active" if prefix == "decoration" else "title_inactive"]

        def textured(x, y, w, h, img, vertical=False, offset=0):
            if img is None or w <= 0 or h <= 0:
                return
            piece = material.strip(img, max(8, int(w)) if not vertical else max(8, int(h)),
                                   int(h) if not vertical else max(4, int(w)), vertical, offset)
            if vertical:
                piece = piece.rotate(-90, expand=True)
            t.append(f'    <image x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" preserveAspectRatio="none" '
                     f'xlink:href="{material.data_uri(piece)}"/>')

        def rivet(cx, cy, ground):
            rr = max(1.6, min(3.2, r / 3))
            t.append(f'    <circle cx="{cx:g}" cy="{cy:g}" r="{rr:g}" fill="{shift(ground, -0.22)}"/>')
            t.append(f'    <circle cx="{cx - 0.4:g}" cy="{cy - 0.4:g}" r="{rr * 0.62:g}" fill="{shift(ground, 0.22)}"/>')

        def field(name, x, y, w, h, ground, edges):
            t.append(f'  <g id="{prefix}-{name}">')
            layers = [(a, P["border"], P["border"]), (b, P["light"], P["light"]),
                      (g, P["glow"], P["glow"])]
            if len(edges) == 2 and self.cs != "square":
                hcol = P["light"] if "t" in edges else P["dark"]
                vcol = P["light"] if "l" in edges else P["dark"]
                layers[1] = (b, hcol, vcol)
                t.extend(corner_polygons(self.cs, self.radius, x, y, w, h, edges,
                                         f'fill="{ground}"', layers))
                if self.tex:
                    inset = a + b + (self.glow or 0)
                    cx = x + inset + (w - inset) / 2 if "l" in edges else x + (w - inset) / 2
                    cy = y + h / 2 if "t" in edges else y + (h - inset) / 2
                    rivet(cx, cy, ground)
                t.append('  </g>')
                return
            rect(x, y, w, h, ground)
            if self.tex:
                title_row = y < oy + self.th
                img = tex if title_row else self.tex["frame"]
                textured(x, y, w, h, img, vertical=(not title_row and edges in ("l", "r")),
                         offset=int(x - ox) * 3)
                if name == "top":
                    # A sunken channel for the title text, like the label strips
                    # in the game: darker with light text, lighter with dark.
                    dl = -0.07 if luminance(on(ground)) > 0.5 else 0.07
                    ch_top, ch_bot = y + round(h * 0.24), y + h - round(h * 0.2)
                    t.append(f'    <rect x="{x:g}" y="{ch_top:g}" width="{w:g}" height="{ch_bot - ch_top:g}" '
                             f'fill="{shift(ground, dl)}" opacity="0.55"/>')
                    rect(x, ch_top, w, 1, shift(ground, -0.2))
                    rect(x, ch_bot - 1, w, 1, shift(ground, 0.14))
            off = 0
            for width_, col in [(a, None), (b, None), (g, P["glow"])]:
                if width_ <= 0:
                    continue
                for side in edges:
                    c = col or (P["border"] if off == 0 and a > 0 else
                                (P["light"] if side in "tl" else P["dark"]))
                    il = off if "l" in edges else 0
                    ir = off if "r" in edges else 0
                    it = off if "t" in edges else 0
                    ib = off if "b" in edges else 0
                    if side == "t": rect(x + il, y + off, w - il - ir, width_, c)
                    if side == "b": rect(x + il, y + h - off - width_, w - il - ir, width_, c)
                    if side == "l": rect(x + off, y + it, width_, h - it - ib, c)
                    if side == "r": rect(x + w - off - width_, y + it, width_, h - it - ib, c)
                off += width_
            if self.tex and len(edges) == 2:
                inset = a + b + (self.glow or 0)
                cx = x + inset + (w - inset) / 2 if "l" in edges else x + (w - inset) / 2
                cy = y + h / 2 if "t" in edges else (y + (h - inset) / 2 if "b" in edges else y + h / 2)
                rivet(cx, cy, ground)
            t.append('  </g>')

        th = self.th
        mid_h = height - th - r
        field("topleft", ox, oy, r, th, title, "tl")
        field("top", ox + r, oy, width - 2 * r, th, title, "t")
        field("topright", ox + width - r, oy, r, th, title, "tr")
        field("left", ox, oy + th, r, mid_h, surface, "l")
        t.append(f'  <g id="{prefix}-center">')
        t.append(f'    <rect x="{ox + r:g}" y="{oy + th:g}" width="{width - 2 * r:g}" '
                 f'height="{mid_h:g}" fill="{surface}"/>')
        t.append('  </g>')
        field("right", ox + width - r, oy + th, r, mid_h, surface, "r")
        field("bottomleft", ox, oy + height - r, r, r, surface, "bl")
        field("bottom", ox + r, oy + height - r, width - 2 * r, r, surface, "b")
        field("bottomright", ox + width - r, oy + height - r, r, r, surface, "br")
        return t

    def decoration(self):
        w, h, gap = 200, 120, 20
        parts = []
        parts += self._patch("decoration", gap, gap, w, h, self.p["title_active"])
        parts += self._patch("decoration-inactive", gap, gap + h + gap, w, h, self.p["title_inactive"])
        for name, colour, oy in [
            ("decoration-maximized-center", self.p["title_active"], gap + 2 * (h + gap)),
            ("decoration-maximized-inactive-center", self.p["title_inactive"],
             gap + 2 * (h + gap) + self.th + gap)]:
            parts.append(f'  <g id="{name}">')
            parts.append(f'    <rect x="{gap}" y="{oy}" width="{w}" height="{self.th}" fill="{colour}"/>')
            if self.glow:
                parts.append(f'    <rect x="{gap}" y="{oy + self.th - self.outer - self.glow}" '
                             f'width="{w}" height="{self.glow}" fill="{self.p["glow"]}"/>')
            parts.append(f'    <rect x="{gap}" y="{oy + self.th - self.outer}" width="{w}" '
                         f'height="{self.outer}" fill="{self.p["border"]}"/>')
            parts.append('  </g>')
        total_h = gap + 2 * (h + gap) + 2 * (self.th + gap)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{w + 2 * gap}" height="{total_h}" '
                f'viewBox="0 0 {w + 2 * gap} {total_h}">\n'
                '  <!-- Generated by Theme Forge. The IDs are the contract with KWin. -->\n'
                + "\n".join(parts) + '\n</svg>\n')

    def _outline(self, ox, oy, size, inset):
        """The button outline as a polygon, shrunk by `inset` (convex shapes)."""
        c = size / 2
        r = c - inset
        cx, cy = ox + c, oy + c
        if self.button_shape == "round":
            pts = [(cx + r * math.cos(math.radians(k)), cy + r * math.sin(math.radians(k)))
                   for k in range(0, 360, 12)]
        elif self.button_shape == "diamond":
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        elif self.button_shape == "chamfer":
            k = r * 0.45
            pts = [(cx - r + k, cy - r), (cx + r - k, cy - r), (cx + r, cy - r + k), (cx + r, cy + r - k),
                   (cx + r - k, cy + r), (cx - r + k, cy + r), (cx - r, cy + r - k), (cx - r, cy - r + k)]
        else:
            pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
        return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)

    def button(self, kind):
        g, a, b = self.bg, self.outer, max(1, self.bevel)
        gap = 6
        P = self.p
        parts = ['  <defs>']
        for name, top, bottom in [("up", P["light"], P["dark"]), ("down", P["dark"], P["light"])]:
            parts.append(f'    <linearGradient id="bevel-{name}" x1="0" y1="0" x2="0" y2="1">'
                         f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
                         '</linearGradient>')
        parts.append('  </defs>')
        for i, state in enumerate(BUTTON_STATES):
            ox, oy = gap + i * (g + gap), gap
            pressed = state == "pressed"
            ground = P["surface"]
            if state == "hover":
                ground = P["error"] if kind == "close" else P["hover"]
            elif state == "pressed":
                ground = shift(P["surface"], -0.06)
            elif state in ("inactive", "deactivated"):
                ground = mix(P["surface"], P["title_inactive"], 0.5)
            symbol = on(ground) if state == "hover" else P["text"]
            if self.tex:
                # A metal plate like the sidebar buttons in the game: ground in
                # frame metal, the symbol glows in the glow colour.
                metal = mix(P["title_active"], P["surface"], 0.45)
                ground = {"hover": shift(metal, 0.08), "pressed": shift(metal, -0.08)}.get(state, metal)
                if state in ("inactive", "deactivated"):
                    ground = mix(metal, P["title_inactive"], 0.6)
                symbol = P["glow"] if state != "hover" else mix(P["glow"], "#ffffff", 0.45)
                if kind == "close" and state == "hover":
                    symbol = mix(P["error"], "#ffffff", 0.3)
                if state in ("inactive", "deactivated"):
                    # Quieter than active, but at least 3:1 (WCAG for controls): mixed
                    # 55 % into the ground, the inactive close button vanished
                    # (visual review, 26.10.2026).
                    symbol = readable(mix(P["glow"], ground, 0.45), ground, 3.0)
            if state == "deactivated":
                symbol = mix(symbol, ground, 0.6)
            parts.append(f'  <g id="{state}-center">')
            # An invisible rectangle over the whole cell: so the element's
            # bounding box is always g×g, also for diamond and circle — else
            # KWin stretches the shape to the button size and distorts it.
            parts.append(f'    <rect x="{ox}" y="{oy}" width="{g}" height="{g}" fill="{ground}" opacity="0.004"/>')
            parts.append(f'    <polygon points="{self._outline(ox, oy, g, 0)}" fill="{P["border"]}"/>')
            parts.append(f'    <polygon points="{self._outline(ox, oy, g, a)}" '
                         f'fill="url(#bevel-{"down" if pressed else "up"})"/>')
            parts.append(f'    <polygon points="{self._outline(ox, oy, g, a + b)}" fill="{ground}"/>')
            v = 1 if pressed else 0
            s = (g - 2 * (a + b)) * (0.5 if self.button_shape in ("diamond", "round") else 0.62) / 2
            sw = max(1.5, g * 0.1)
            if self.tex and state not in ("inactive", "deactivated"):
                # Halo: a wider, half-transparent copy under the symbol
                parts.append('    <g opacity="0.35">')
                parts.append(self._symbol(kind, ox + g / 2 + v, oy + g / 2 + v, s, sw * 2.4, symbol))
                parts.append('    </g>')
            parts.append(self._symbol(kind, ox + g / 2 + v, oy + g / 2 + v, s, sw, symbol))
            parts.append('  </g>')
        width = gap + len(BUTTON_STATES) * (g + gap)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{g + 2 * gap}" '
                f'viewBox="0 0 {width} {g + 2 * gap}">\n' + "\n".join(parts) + '\n</svg>\n')

    def _symbol(self, kind, m, n, s, sw, colour):
        if kind == "close":
            return (f'    <path d="M{m-s:g},{n-s:g} L{m+s:g},{n+s:g} M{m+s:g},{n-s:g} L{m-s:g},{n+s:g}" '
                    f'stroke="{colour}" stroke-width="{sw:g}" stroke-linecap="square"/>')
        if kind == "maximize":
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" height="{2*s:g}" fill="none" '
                    f'stroke="{colour}" stroke-width="{sw:g}"/>')
        if kind == "minimize":
            return f'    <rect x="{m-s:g}" y="{n+s-sw:g}" width="{2*s:g}" height="{sw:g}" fill="{colour}"/>'
        if kind == "restore":
            return (f'    <rect x="{m-s:g}" y="{n-s+sw:g}" width="{2*s-sw:g}" height="{2*s-sw:g}" fill="none" '
                    f'stroke="{colour}" stroke-width="{sw*0.8:g}"/>\n'
                    f'    <path d="M{m-s+sw:g},{n-s+sw:g} L{m-s+sw:g},{n-s:g} L{m+s:g},{n-s:g} '
                    f'L{m+s:g},{n+s-sw:g}" fill="none" stroke="{colour}" stroke-width="{sw*0.8:g}"/>')
        if kind == "shade":
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" height="{sw:g}" fill="{colour}"/>\n'
                    f'    <path d="M{m:g},{n+s:g} L{m-s*0.6:g},{n:g} L{m+s*0.6:g},{n:g} Z" fill="{colour}"/>')
        if kind == "keepabove":
            return (f'    <path d="M{m:g},{n-s:g} L{m-s:g},{n+s*0.3:g} L{m+s:g},{n+s*0.3:g} Z" fill="{colour}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n+s*0.6:g}" width="{2*s:g}" height="{sw:g}" fill="{colour}"/>')
        if kind == "keepbelow":
            return (f'    <path d="M{m:g},{n+s:g} L{m-s:g},{n-s*0.3:g} L{m+s:g},{n-s*0.3:g} Z" fill="{colour}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" height="{sw:g}" fill="{colour}"/>')
        if kind == "alldesktops":
            q = s * 0.8
            return "\n".join(f'    <rect x="{m + dx*q - q*0.85:g}" y="{n + dy*q - q*0.85:g}" '
                             f'width="{q*0.7:g}" height="{q*0.7:g}" fill="{colour}"/>'
                             for dx in (0, 1) for dy in (0, 1))
        if kind == "help":
            return (f'    <path d="M{m-s*0.6:g},{n-s*0.4:g} Q{m-s*0.6:g},{n-s:g} {m:g},{n-s:g} '
                    f'Q{m+s*0.6:g},{n-s:g} {m+s*0.6:g},{n-s*0.4:g} Q{m+s*0.6:g},{n:g} {m:g},{n+s*0.1:g} '
                    f'L{m:g},{n+s*0.4:g}" fill="none" stroke="{colour}" stroke-width="{sw:g}"/>\n'
                    f'    <rect x="{m-sw/2:g}" y="{n+s*0.7:g}" width="{sw:g}" height="{sw:g}" fill="{colour}"/>')
        if kind == "menu":
            return "\n".join(f'    <rect x="{m-s:g}" y="{n + (k-1)*s*0.75 - sw/2:g}" width="{2*s:g}" '
                             f'height="{sw:g}" fill="{colour}"/>' for k in range(3))
        return f'    <rect x="{m-s:g}" y="{n-sw/2:g}" width="{2*s:g}" height="{sw:g}" fill="{colour}"/>'

    def rc(self):
        r = self.border
        return f"""[General]
ActiveTextColor={_rgb(self.p["title_active_text"])}
InactiveTextColor={_rgb(self.p["title_inactive_text"])}
TitleAlignment={self.title_align.capitalize()}
TitleVerticalAlignment=Center
UseTextShadow=false
Animation=0
Shadow=true

[Layout]
BorderLeft={r}
BorderRight={r}
BorderBottom={r}
TitleHeight={self.th}
TitleEdgeTop=0
TitleEdgeTopMaximized=0
TitleEdgeBottom=0
TitleEdgeBottomMaximized=0
TitleEdgeLeft={r}
TitleEdgeLeftMaximized=2
TitleEdgeRight={r}
TitleEdgeRightMaximized=2
TitleBorderLeft=6
TitleBorderRight=6
ButtonWidth={self.bg}
ButtonHeight={self.bg}
ButtonSpacing=3
ButtonMarginTop={max(0, (self.th - self.bg) // 2)}
ExplicitButtonSpacer=6
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
"""

    @staticmethod
    def metadata(name, display_name, description, version):
        # metadata.desktop is Aurorae's intended format; the prefix
        # __aurorae__svg__ plus the folder name is required.
        return f"""[Desktop Entry]
Name={display_name}
Comment={description}
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__{name}
X-KDE-PluginInfo-Author=Theme Forge
X-KDE-PluginInfo-License=GPL-2.0-or-later
X-KDE-PluginInfo-Version={version}
"""
