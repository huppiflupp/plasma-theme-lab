"""fam_categories.py: the application categories, each as a RISC OS style
object of its own (no tiles): !Configure's cogs for the system, !Paint's
palette and brush for graphics, a page and pen for the office, …"""
import math

from glyphs import glyph


def cog_path(cx, cy, ro, ri, teeth=8, hole=None):
    pts = []
    n = teeth * 4
    for i in range(n):
        a = (i - 0.5) * 2 * math.pi / n
        r = ro if (i % 4) in (0, 1) else ri
        pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    d = "M" + " L".join(pts) + " Z"
    if hole:
        d += (f" M{cx + hole:.2f} {cy:.2f} A{hole} {hole} 0 1 0 {cx - hole:.2f} {cy:.2f}"
              f" A{hole} {hole} 0 1 0 {cx + hole:.2f} {cy:.2f} Z")
    return d


def cog(c, cx, cy, ro, col, teeth=8):
    c.parts.append(f'<path d="{cog_path(cx, cy, ro, ro * 0.76, teeth, ro * 0.3)}" fill="{c.grad(col)}" '
                   f'fill-rule="evenodd" stroke="{c["ink"]}" stroke-width="{c.lw:g}" stroke-linejoin="round"/>')


def sheet(c, x, y, w, h, fold=7):
    c.path(f"M{x} {y} h{w - fold} l{fold} {fold} v{h - fold} h-{w} z", c.grad(c["page"]))
    c.path(f"M{x + w - fold} {y} v{fold} h{fold}", c["page_fold"])


def pen(c, x1, y1, x2, y2, col, w=5):
    """A pen from (x1, y1) (the nib) to (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy * w / 2, ux * w / 2
    t = 7                                   # nib length
    bx, by = x1 + ux * t, y1 + uy * t
    c.path(f"M{bx + px:.2f} {by + py:.2f} L{x2 + px:.2f} {y2 + py:.2f} L{x2 - px:.2f} {y2 - py:.2f} "
           f"L{bx - px:.2f} {by - py:.2f} Z", c.grad(c.lighten(col, 0.25), c.darken(col, 0.2)))
    c.path(f"M{x1:.2f} {y1:.2f} L{bx + px:.2f} {by + py:.2f} L{bx - px:.2f} {by - py:.2f} Z", c.grad(c["metal"]))


import names as _names
MINE = frozenset(_names.names()["categories"])


def draw(name, c):
    if name not in MINE:
        return None
    if not name.startswith("applications-"):
        return None
    n = name[13:]
    ink = c["ink"]
    if n == "all":
        c.circle(14, 14, 9, c.grad(c.lighten(c["red"], 0.3), c["red"]))
        c.rect(26, 5, 17, 17, c.grad(c.lighten(c["blue"], 0.3), c["blue"]), 2)
        c.path("M14 26 L23 42 H5 Z", c.grad(c.lighten(c["green"], 0.3), c["green"]))
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 10 if i % 2 == 0 else 4.3
            pts.append(f"{34.5 + r * math.cos(a):.2f} {35 + r * math.sin(a):.2f}")
        c.path("M" + " L".join(pts) + " Z", c.grad(c.lighten(c["yellow"], 0.3), c["orange"]))
        return True
    if n == "development":
        sheet(c, 6, 4, 28, 36)
        glyph(c, "code", 9, 12, 22, c["violet"], width=2.6 if not c.small else 3.4)
        # a spanner across the lower right
        c.path("M22 44 L36 30", "none", ink, 7.5 if not c.small else 5)
        c.path("M22 44 L36 30", "none", c.lighten(c["metal"][1], 0.2), 5 if not c.small else 3)
        c.path("M33 27 a8 8 0 1 1 8 8 l-2 -4 l3 -3 l-1.5 -3.5 l-3.5 -1.5 l-3 3 z", c.grad(c["metal"]))
        return True
    if n == "education":
        c.path("M7 30 h34 v10 h-34 z", c.grad(c.lighten(c["red"], 0.2), c.darken(c["red"], 0.1)))
        c.path("M9 32 h30 v6 h-30", c["page"][0], width=1)
        c.path("M13 22 v6 c0 3 22 3 22 0 v-6", c.grad(c.lighten(ink, 0.35), ink))
        c.path("M24 8 L45 17 L24 26 L3 17 Z", c.grad(c.lighten(ink, 0.4), c.lighten(ink, 0.15)))
        c.line("M24 17 L40 21 V31", c["yellow"], 1.8)
        c.circle(40, 32, 2.3, c["yellow"], width=1)
        return True
    if n == "education-language":
        c.path("M18 6 h22 a4 4 0 0 1 4 4 v12 a4 4 0 0 1 -4 4 h-3 v6 l-7 -6 h-12 a4 4 0 0 1 -4 -4 v-12 a4 4 0 0 1 4 -4 z",
               c.grad(c.lighten(c["yellow"], 0.3), c["yellow"]))
        c.path("M8 18 h20 a4 4 0 0 1 4 4 v12 a4 4 0 0 1 -4 4 h-12 l-7 6 v-6 h-1 a4 4 0 0 1 -4 -4 v-12 a4 4 0 0 1 4 -4 z",
               c.grad(c.lighten(c["blue"], 0.3), c["blue"]))
        glyph(c, "language", 8, 18, 20, "#ffffff", width=2.4 if not c.small else 3.2)
        if not c.small:
            c.text(30, 20, "Ä", 10, ink)
        return True
    if n == "education-mathematics":
        tri = c.grad(c.lighten(c["yellow"], 0.4), c["yellow"])
        c.parts.append(f'<path d="M5 43 V5 L43 43 Z M11 37 H28 L11 20 Z" fill="{tri}" fill-rule="evenodd" '
                       f'stroke="{ink}" stroke-width="{c.lw:g}" stroke-linejoin="round"/>')
        if not c.small:
            c.line("M5 11 h3 M5 17 h3 M5 23 h3 M5 29 h3 M11 43 v-3 M17 43 v-3 M23 43 v-3 M29 43 v-3", "ink", 1)
        # dividers
        c.path("M34 6 L26 30 M34 6 L42 30", "none", c.darken(c["metal"][1], 0.25), 3.2 if not c.small else 2.4)
        c.path("M34 6 L26 30 M34 6 L42 30", "none", c["metal"][0], 1.4 if not c.small else 1)
        c.circle(34, 6, 3, c.grad(c["metal"]), width=1)
        return True
    if n == "education-science":
        c.path("M18 5 h12 M20 5 v12 l-12 21 a3 3 0 0 0 3 5 h26 a3 3 0 0 0 3 -5 l-12 -21 v-12", c.grad(c["page"]))
        c.path("M13.5 29 h21 l6 10 a2 2 0 0 1 -2 3 h-29 a2 2 0 0 1 -2 -3 z",
               c.grad(c.lighten(c["green"], 0.3), c["green"]), None)
        c.path("M18 5 h12 M20 5 v12 l-12 21 a3 3 0 0 0 3 5 h26 a3 3 0 0 0 3 -5 l-12 -21 v-12", "none")
        c.circle(21, 35, 2.2, "#ffffff", None)
        c.circle(28, 32, 1.6, "#ffffff", None)
        c.circle(27, 38, 1.4, "#ffffff", None)
        return True
    if n == "engineering":
        c.rect(4, 6, 40, 34, c.grad(c.lighten(c["blue"], 0.15), c.darken(c["blue"], 0.15)), 1.5)
        if not c.small:
            for i in range(1, 5):
                c.line(f"M{4 + i * 8} 7 V39 M5 {6 + i * 7} H43", "#ffffff", 0.4)
        glyph(c, "gear", 7, 9, 22, "#ffffff", width=2.0 if not c.small else 2.8)
        c.circle(18, 20, 3, "none", "#ffffff", 1.2)
        c.parts.append(f'<path d="M24 42 V20 L44 42 Z M29 38 H35 L29 31 Z" fill="{c.grad(c.lighten(c["orange"], 0.3), c["orange"])}" '
                       f'fill-rule="evenodd" stroke="{ink}" stroke-width="{c.lw:g}" stroke-linejoin="round"/>')
        return True
    if n == "games":
        case = c.grad(c.lighten(ink, 0.35), ink)
        c.path("M6 34 l5 -5 h28 l5 5 v6 a2 2 0 0 1 -2 2 h-34 a2 2 0 0 1 -2 -2 z", case)
        c.path("M6 34 h38", "none", c.lighten(ink, 0.5), 1)
        c.path("M22 31 l1 -18 h2 l1 18 z", c.grad(c["metal"], horizontal=True), width=1.1)
        c.circle(24, 11, 7, c.grad(c.lighten(c["red"], 0.35), c["red"]))
        if not c.small:
            c.circle(21.5, 8.5, 2, "#ffffff", None)
        c.ellipse(36, 31, 3.5, 1.8, c["red"], width=1)
        c.ellipse(12, 31, 3.5, 1.8, c["yellow"], width=1)
        return True
    if n == "graphics":
        wood = c.grad(c.lighten(c["brown"], 0.45), c.lighten(c["brown"], 0.1))
        c.parts.append(f'<path d="M24 6 C38 6 45 15 44 24 C43 31 36 30 33 33 C30 36 34 42 26 42 C12 42 4 34 4 23 C4 13 13 6 24 6 Z '
                       f'M14 31 a3.5 3.5 0 1 0 0.01 0 Z" fill="{wood}" fill-rule="evenodd" stroke="{ink}" '
                       f'stroke-width="{c.lw:g}" stroke-linejoin="round"/>')
        for (x, y), col in zip(((14, 16), (23, 12), (32, 14), (37, 22)), ("red", "yellow", "green", "blue")):
            c.circle(x, y, 3.6, c[col], width=1)
        pen(c, 21, 30, 44, 44, c["violet"], 4)
        c.path("M21 30 c-4 -1 -6 2 -5 5 c3 0 6 -1 7 -3 z", c["red"], width=1)
        return True
    if n == "internet":
        c.circle(24, 24, 19, c.grad(c.lighten(c["blue"], 0.35), c.darken(c["blue"], 0.1)))
        land = c.grad(c.lighten(c["green"], 0.3), c["green"])
        c.path("M12 11 c4 -2 9 -1 10 2 c1 3 -3 4 -2 7 c1 3 5 3 4 7 c-1 3 -5 2 -6 5 c-2 2 -5 -1 -5 -5 "
               "c0 -4 -4 -5 -5 -8 c-1 -3 1 -6 4 -8 z", land, width=1.1)
        c.path("M30 9 c4 1 8 4 9 8 c-3 0 -4 2 -3 4 c2 1 4 0 5 2 c0 5 -2 10 -6 13 c-2 -2 -1 -6 -3 -8 "
               "c-2 -2 -5 -1 -5 -4 c0 -3 3 -3 3 -6 c0 -3 -3 -4 0 -9 z", land, width=1.1)
        if not c.small:
            c.ellipse(24, 24, 8, 19, "none", "#ffffff", 0.7)
            c.line("M5 24 H43 M8 14 H40 M8 34 H40", "#ffffff", 0.7)
        c.circle(24, 24, 19, "none")
        return True
    if n == "multimedia":
        c.path("M5 18 h30 v22 a2 2 0 0 1 -2 2 h-26 a2 2 0 0 1 -2 -2 z", c.grad(c.lighten(ink, 0.35), ink))
        c.path("M4 10 l29 -6 l1.5 7 l-29 6 z", c.grad(c.lighten(ink, 0.35), ink))
        if not c.small:
            for i in range(4):
                c.path(f"M{9 + i * 7} {9.2 - i * 1.45} l5 -1.05 l-2 7.2 l-5 1.05 z", "#ffffff", None)
            c.line("M8 25 H32", "#ffffff", 1)
        glyph(c, "music", 22, 20, 24, c["yellow"], width=2.6)
        return True
    if n == "network":
        def mon(x, y):
            c.rect(x, y, 15, 11, c.grad(c["case"]), 1.5)
            c.rect(x + 2, y + 2, 11, 7, c.grad(c["screen"]), 0.5, width=0.8)
            c.path(f"M{x + 5} {y + 11} h5 l1 3 h-7 z", c.grad(c["case"]), width=1)
        c.path("M24 16 V26 M12 33 H36 M24 26 L12 33 M24 26 L36 33", "none", c["green"], 2.4)
        c.circle(24, 27, 3, c["green"], width=1)
        mon(16.5, 2)
        mon(2, 28)
        mon(31, 28)
        return True
    if n == "office":
        sheet(c, 8, 4, 30, 38)
        if not c.small:
            for i in range(5):
                c.line(f"M12 {12 + i * 4} h{20 if i % 2 == 0 else 15}", "#7a8699", 1.3)
        else:
            c.line("M12 13 h18 M12 19 h14", "#7a8699", 1.3)
        c.circle(16, 35, 7, c.grad(c.lighten(c["blue"], 0.3), c["blue"]), width=1.1)
        c.path("M16 35 V28 A7 7 0 0 1 22.5 37.5 Z", c.grad(c.lighten(c["orange"], 0.3), c["orange"]), width=1.1)
        pen(c, 27, 34, 44, 12, c["red"], 5)
        return True
    if n == "other":
        board = c.grad(c.lighten(c["brown"], 0.5), c.lighten(c["brown"], 0.15))
        c.path("M5 16 L24 9 L43 16 V36 L24 43 L5 36 Z", board)
        c.path("M5 16 L24 23 L43 16 M24 23 V43", "none")
        c.path("M5 16 L24 9 L43 16 L24 23 Z", c.lighten(c["brown"], 0.55))
        glyph(c, "question", 26, 21, 17, c.darken(c["brown"], 0.4), width=3.2)
        return True
    if n == "science":
        orbit = c.darken(c["violet"], 0.05)
        for rot in (0, 60, 120):
            c.parts.append(f'<ellipse cx="24" cy="24" rx="20" ry="7.5" fill="none" stroke="{c["ink"]}" '
                           f'stroke-width="{c.lw + 2.6:g}" transform="rotate({rot} 24 24)"/>')
            c.parts.append(f'<ellipse cx="24" cy="24" rx="20" ry="7.5" fill="none" stroke="{orbit}" '
                           f'stroke-width="{2.6 if not c.small else 2.2:g}" transform="rotate({rot} 24 24)"/>')
        c.circle(24, 24, 5, c.grad(c.lighten(c["red"], 0.35), c["red"]))
        c.circle(44, 24, 2.6, c["cyan"], width=1)
        return True
    if n == "system":
        cog(c, 18, 19, 14, c["metal"], 9)
        cog(c, 34, 34, 10, (c.lighten(c["orange"], 0.3), c["orange"]), 7)
        return True
    if n == "utilities":
        red = c.grad(c.lighten(c["red"], 0.25), c.darken(c["red"], 0.1))
        c.path("M15 14 v-5 a2 2 0 0 1 2 -2 h14 a2 2 0 0 1 2 2 v5", "none", "ink", 3.6 if not c.small else 2.6)
        c.path("M15 14 v-5 a2 2 0 0 1 2 -2 h14 a2 2 0 0 1 2 2 v5", "none", c.grad(c["metal"]), 1.8 if not c.small else 1.2)
        # a screwdriver sticking out
        c.path("M36 3 l3 1 l-3 13 l-3 -1 z", c.grad(c["metal"]), width=1)
        c.rect(4, 14, 40, 9, red, 1.5)
        c.path("M5 23 h38 v17 a2 2 0 0 1 -2 2 h-34 a2 2 0 0 1 -2 -2 z", red)
        c.rect(20, 20, 8, 6, c.grad(c["metal"]), 1, width=1)
        if not c.small:
            c.line("M8 32 H40", c.darken(c["red"], 0.3), 1)
        return True
    return None
