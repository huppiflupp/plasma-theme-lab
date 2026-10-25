"""fam_apps.py: applications.

RISC OS draws an application as an object on its own (!Edit a pen and a
page, !Paint a palette and a brush, !Configure cogs and a spanner), never
on a tile. Every program here is drawn the same way: what it is or does as
a coloured object, often a second, smaller object overlapping at the lower
right. Programs of the same kind (browsers, players, editors) differ by the
object, its colour and the secondary element; a word is the last resort.

The objects ("props") are drawn on the 48 grid; at() places one scaled
(and rotated) elsewhere and keeps its outline as heavy as the rest.
"""
import math

from base import folder, page
from glyphs import glyph
from kit import Canvas

WHITE = "#ffffff"


# ---- placing ----------------------------------------------------------------
def _prep(c):
    if "_stroke" not in c.__dict__:
        c._ws = 1.0
        orig = Canvas._stroke

        def stroke(st, width, c=c, orig=orig):
            return orig(c, st, None if width is None else width * c._ws)
        c._stroke = stroke


def at(c, x, y, s, fn, *a, _rot=0, **k):
    """Draw prop fn (48 grid) into the box (x, y, 48*s), rotated by _rot
    degrees around its centre; outlines keep their weight."""
    _prep(c)
    lw, ws = c.lw, c._ws
    c.lw, c._ws = lw / s, ws / s
    start = len(c.parts)
    try:
        fn(c, *a, **k)
    finally:
        c.lw, c._ws = lw, ws
    inner = c.parts[start:]
    del c.parts[start:]
    if _rot:
        h = 24 * s
        t = f"translate({x + h:g} {y + h:g}) rotate({_rot:g}) translate({-h:g} {-h:g}) scale({s:g})"
    else:
        t = f"translate({x:g} {y:g}) scale({s:g})"
    c.parts.append(f'<g transform="{t}">' + "".join(inner) + "</g>")
    return True


def sec(c, fn, *a, **k):
    """The secondary object at the lower right."""
    return at(c, 23, 23, 0.52, fn, *a, **k)


def gl(c, name, x, y, size, col, w=None):
    """A glyph whose line weight survives at()."""
    k = size / 24.0
    base = w if w is not None else (max(1.6, 2.2 / max(k, 0.5)) if size < 24 else 1.8)
    glyph(c, name, x, y, size, col, width=base * getattr(c, "_ws", 1.0) * (1.4 if c.small else 1.0))


# ---- helpers ----------------------------------------------------------------
def G(c, col, t=0.35, d=0.15):
    return c.grad(c.lighten(col, t), c.darken(col, d))


def tube(c, d, col, w):
    """A thick stroke with an outline (handles, wires, frames)."""
    c.path(d, "none", "ink", w + 2.4)
    c.path(d, "none", col, w)


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _n(p, q, w):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1
    return -dy / L * w / 2, dx / L * w / 2


def quad(p, q, w):
    nx, ny = _n(p, q, w)
    return (f"M{p[0] + nx:.2f} {p[1] + ny:.2f} L{q[0] + nx:.2f} {q[1] + ny:.2f} "
            f"L{q[0] - nx:.2f} {q[1] - ny:.2f} L{p[0] - nx:.2f} {p[1] - ny:.2f} Z")


def arc(cx, cy, r, a0, a1):
    """An arc from angle a0 to a1 (degrees, clockwise on screen)."""
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f} {y0:.2f} A{r:g} {r:g} 0 {large} 1 {x1:.2f} {y1:.2f}"


def sector(cx, cy, r, a0, a1):
    return arc(cx, cy, r, a0, a1).replace("M", f"M{cx:g} {cy:g} L", 1) + " Z"


def blob(c, cx, cy, rx, ry, fill=WHITE, opacity=0.45):
    c.path(f"M{cx - rx:g} {cy:g} a{rx:g} {ry:g} 0 1 0 {2 * rx:g} 0 a{rx:g} {ry:g} 0 1 0 {-2 * rx:g} 0 z",
           fill, None, opacity=opacity)


def shine(c, d, opacity=0.45):
    if not c.small:
        c.path(d, "none", WHITE, 1.4, opacity=opacity)


def star_d(cx, cy, r, n=5, inner=0.45):
    pts = []
    for i in range(n * 2):
        a = -math.pi / 2 + i * math.pi / n
        rr = r if i % 2 == 0 else r * inner
        pts.append(f"{cx + rr * math.cos(a):.2f} {cy + rr * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


def skin(c):
    return c.lighten(c["orange"], 0.55)


def dark(c):
    return c.lighten(c["ink"], 0.18)


# ---- props ------------------------------------------------------------------
def pencil(c, col=None, tip=(7, 41), end=(41, 7), w=8.5):
    col = col or c["yellow"]
    a, e, f = lerp(tip, end, 0.25), lerp(tip, end, 0.84), lerp(tip, end, 0.9)
    nx, ny = _n(tip, end, w)
    c.path(quad(a, e, w), G(c, col))
    c.path(quad(f, end, w), G(c, c.lighten(c["red"], 0.45)))
    c.path(quad(e, f, w + 0.6), c.grad(c["metal"]))
    c.path(f"M{tip[0]} {tip[1]} L{a[0] + nx:.2f} {a[1] + ny:.2f} L{a[0] - nx:.2f} {a[1] - ny:.2f} Z",
           c.lighten(c["brown"], 0.55))
    g = lerp(tip, a, 0.38)
    c.path(f"M{tip[0]} {tip[1]} L{g[0] + nx * .4:.2f} {g[1] + ny * .4:.2f} L{g[0] - nx * .4:.2f} {g[1] - ny * .4:.2f} Z",
           c["ink"], None)
    if not c.small:
        p, q = lerp(a, e, 0.05), lerp(a, e, 0.95)
        c.path(f"M{p[0] + nx * .45:.2f} {p[1] + ny * .45:.2f} L{q[0] + nx * .45:.2f} {q[1] + ny * .45:.2f}",
               "none", WHITE, 1.2, opacity=0.5)
    return True


def pen(c, col=None, tip=(7, 41), end=(41, 7), w=9):
    col = col or c["blue"]
    a = lerp(tip, end, 0.32)
    nx, ny = _n(tip, end, w)
    c.circle(end[0], end[1], w / 2, G(c, col))
    c.path(quad(a, end, w), G(c, col))
    c.path(quad(lerp(tip, end, 0.3), lerp(tip, end, 0.38), w + 1), c.grad(c["metal"]))
    c.path(f"M{tip[0]} {tip[1]} L{a[0] + nx * .8:.2f} {a[1] + ny * .8:.2f} L{a[0] - nx * .8:.2f} {a[1] - ny * .8:.2f} Z",
           c.grad(c["metal"]))
    m = lerp(tip, a, 0.6)
    c.line(f"M{tip[0] + 1} {tip[1] - 1} L{m[0]:.2f} {m[1]:.2f}", "ink", 1)
    if not c.small:
        p, q = lerp(a, end, 0.15), lerp(a, end, 0.95)
        c.path(f"M{p[0] + nx * .45:.2f} {p[1] + ny * .45:.2f} L{q[0] + nx * .45:.2f} {q[1] + ny * .45:.2f}",
               "none", WHITE, 1.3, opacity=0.5)
    return True


def brush(c, paint=None, tip=(7, 41), end=(42, 6), w=6.5):
    paint = paint or c["red"]
    a, b = lerp(tip, end, 0.3), lerp(tip, end, 0.44)
    nx, ny = _n(tip, end, w)
    c.path(quad(b, end, w * 0.75), G(c, c["brown"]))
    m = lerp(tip, a, 0.45)
    c.path(f"M{a[0] + nx:.2f} {a[1] + ny:.2f} L{m[0] + nx * 1.2:.2f} {m[1] + ny * 1.2:.2f} L{tip[0]} {tip[1]} "
           f"L{m[0] - nx * 1.2:.2f} {m[1] - ny * 1.2:.2f} L{a[0] - nx:.2f} {a[1] - ny:.2f} Z", G(c, paint))
    c.path(quad(a, b, w + 0.5), c.grad(c["metal"]))
    return True


def monitor(c, content=None):
    c.path("M19 34 h10 l2 6 h-14 z", c.grad(c["case"]))
    c.rect(11, 39, 26, 5, c.grad(c["case"]), 2)
    c.rect(4, 5, 40, 30, c.grad(c["case"]), 3)
    c.rect(8, 9, 32, 22, c.grad(c["screen"]), 1.5)
    if not c.small:
        c.circle(38, 33, 0.9, c["led"], None)
    if content:
        content(c)
    return True


def globe(c, sea=None, land=None, grid=True):
    sea, land = sea or c["blue"], land or c["green"]
    c.circle(24, 24, 18, G(c, sea, 0.45, 0.1))
    lf = G(c, land, 0.25, 0.1)
    c.path("M12 14 c4 -4 10 -3 11 1 c1 4 -4 5 -3 9 c1 4 -3 7 -6 5 c-3 -2 -2 -6 -5 -8 c-2 -2 0 -5 3 -7 z", lf, width=0.9)
    c.path("M29 9 c5 0 10 5 11 10 c1 5 -2 9 -5 12 c-2 2 -5 1 -4 -2 c1 -3 3 -5 1 -8 c-2 -3 -6 -3 -6 -6 c0 -4 1 -6 3 -6 z",
           lf, width=0.9)
    c.path("M20 36 c3 -2 7 -1 7 2 c0 2 -3 3 -6 3 z", lf, width=0.9)
    if grid and not c.small:
        c.path("M24 6 a8 18 0 0 0 0 36 a8 18 0 0 0 0 -36 M6 24 h36 M9 15 h30 M9 33 h30", "none", WHITE, 0.8,
               opacity=0.4)
    blob(c, 17, 14, 6, 3.5, WHITE, 0.35)
    c.circle(24, 24, 18, "none")
    return True


def magnifier(c, inner=None, glass=None):
    c.path("M27.5 30.5 L30.5 27.5 L42.5 39.5 a2.12 2.12 0 0 1 -3 3 z", G(c, c["brown"], 0.25, 0.2))
    c.circle(19, 19, 12, glass or c.lighten(c["cyan"], 0.75), None)
    if inner:
        inner(c)
    c.circle(19, 19, 12, "none", "ink", 5)
    c.circle(19, 19, 12, "none", c.lighten(c["metal"][1], 0.15), 2.6)
    shine(c, "M12.5 16 a7 7 0 0 1 5.5 -5.5", 0.7)
    return True


def window(c, x=5, y=7, w=38, h=32, body=None, title=None):
    c.rect(x, y, w, h, c.grad(c["page"]), 1.5)
    c.rect(x, y, w, 7, title or c.grad(c.lighten(c["yellow"], 0.6), c.lighten(c["yellow"], 0.15)), 1.5)
    if not c.small:
        c.rect(x + 1.5, y + 1.5, 4, 4, c.lighten(c["metal"][1], 0.4), 0.5, width=0.8)
        c.rect(x + w - 5.5, y + 1.5, 4, 4, c.lighten(c["metal"][1], 0.4), 0.5, width=0.8)
    if body:
        body(c)
    return True


def cog(c, cx, cy, r, col, n=8, hole=True):
    step = 2 * math.pi / n
    ri = r * 0.75
    pts = []
    for i in range(n):
        a = i * step
        for rr, da in ((ri, -0.32), (r, -0.17), (r, 0.17), (ri, 0.32)):
            pts.append(f"{cx + rr * math.cos(a + da * step):.2f} {cy + rr * math.sin(a + da * step):.2f}")
    c.path("M" + " L".join(pts) + " Z", G(c, col))
    if hole:
        c.circle(cx, cy, r * 0.3, c.lighten(col, 0.8))
    return True


def wrench(c, col=None):
    """A spanner lying from lower left to upper right (local horizontal)."""
    m = col or c.grad(c["metal"])

    def w(cv):
        cv.rect(9, 21.5, 26, 5, m, 1)
        cv.circle(9, 24, 5.5, m)
        cv.circle(9, 24, 2.2, cv.lighten(cv["metal"][0], 0.6))
        cv.path("M44.55 28.59 A8 8 0 1 1 44.55 19.41 L39.5 21 L39.5 27 Z", m)
    return at(c, 0, 0, 1, w, _rot=-45)


def clock_face(c, cx, cy, r, ring):
    c.circle(cx, cy, r, G(c, ring))
    c.circle(cx, cy, r * 0.78, c.grad(c["page"]))
    if not c.small:
        for i in range(12):
            a = i * math.pi / 6
            r1 = r * (0.6 if i % 3 == 0 else 0.68)
            c.line(f"M{cx + r1 * math.cos(a):.2f} {cy + r1 * math.sin(a):.2f} "
                   f"L{cx + r * .74 * math.cos(a):.2f} {cy + r * .74 * math.sin(a):.2f}", "ink", 0.9)
    c.line(f"M{cx} {cy} V{cy - r * 0.55:.2f}", "ink", 2)
    c.line(f"M{cx} {cy} L{cx + r * 0.42:.2f} {cy + r * 0.12:.2f}", "ink", 2)
    c.circle(cx, cy, 1.5, c["red"], None)
    return True


def alarm_clock(c, ring=None):
    ring = ring or c["blue"]
    tube(c, "M15 37 l-5 6 M33 37 l5 6", c["metal"][1], 2.4)
    c.circle(11, 11, 7, G(c, ring))
    c.circle(37, 11, 7, G(c, ring))
    tube(c, "M14 6 L34 6", c["metal"][1], 1.6)
    clock_face(c, 24, 27, 16, ring)
    return True


def music_note(c, col=None):
    col = col or c["ink"]
    c.path("M27 34 V7 c2 7 12 8 12 17 c0 3 -1 5 -2 6 c1 -6 -5 -9 -7 -10 V34 z", G(c, col))
    c.ellipse(21, 35, 8, 6, G(c, col))
    return True


def cd(c, ring=None):
    c.circle(24, 24, 19, c.grad(c["metal"]))
    for col, a0, a1 in ((c["cyan"], 200, 260), (c["yellow"], 20, 80), (c["violet"], 280, 320),
                        (c["red"], 100, 140)):
        c.path(arc(24, 24, 13, a0, a1), "none", col, 7, opacity=0.6)
    if ring:
        c.circle(24, 24, 9, ring, None)
    c.circle(24, 24, 6, c.lighten(c["metal"][0], 0.5))
    c.circle(24, 24, 2.4, c["metal"][1])
    c.circle(24, 24, 19, "none")
    return True


def vinyl(c, label=None):
    c.circle(24, 24, 19, dark(c))
    if not c.small:
        for r in (16, 13, 10.5):
            c.circle(24, 24, r, "none", c.lighten(c["ink"], 0.35), 0.7)
    c.path(arc(24, 24, 15, 200, 250), "none", WHITE, 2, opacity=0.35)
    c.circle(24, 24, 7, G(c, label or c["red"]))
    c.circle(24, 24, 1.6, dark(c), None)
    return True


def clapper(c):
    d = dark(c)
    c.rect(6, 20, 36, 22, d, 2)
    if not c.small:
        c.line("M10 28 H38 M10 34 H38", c.lighten(c["ink"], 0.5), 1)
    c.path("M5 18 L38 6 L40.5 12.5 L7.5 24.5 Z", d)
    for i in range(4):
        x = 9 + i * 8
        y = 17.5 - i * 2.9
        c.path(f"M{x:.1f} {y:.1f} l4 -1.45 l3.6 4.5 l-4 1.45 z", WHITE, None)
    c.circle(7, 21, 1.6, c.grad(c["metal"]), width=0.8)
    return True


def camera(c, band=None):
    c.path("M5 16 h9 l3 -5 h14 l3 5 h9 v24 h-38 z", c.grad(c["metal"]))
    c.rect(5, 22, 38, 12, band or dark(c), 0, None)
    c.path("M5 16 h9 l3 -5 h14 l3 5 h9 v24 h-38 z", "none")
    c.circle(24, 28, 10, dark(c))
    c.circle(24, 28, 6.5, c.grad(c["screen"]))
    blob(c, 21.5, 25.5, 2.2, 1.5, WHITE, 0.7)
    c.rect(34, 13, 6, 3, c.lighten(c["yellow"], 0.5), 0.5, width=0.8)
    return True


def bubble(c, x, y, w, h, col, tail=1):
    r = 3
    if tail > 0:
        tx1, tx2, tip = x + 6, x + 13, (x + 3, y + h + 7)
        tailp = f"H{tx2} L{tip[0]} {tip[1]} L{tx1} {y + h}"
    else:
        tx1, tx2, tip = x + w - 13, x + w - 6, (x + w - 3, y + h + 7)
        tailp = f"H{tx2} L{tip[0]} {tip[1]} L{tx1} {y + h}"
    d = (f"M{x + r} {y} H{x + w - r} A{r} {r} 0 0 1 {x + w} {y + r} V{y + h - r} "
         f"A{r} {r} 0 0 1 {x + w - r} {y + h} {tailp} H{x + r} A{r} {r} 0 0 1 {x} {y + h - r} "
         f"V{y + r} A{r} {r} 0 0 1 {x + r} {y} Z")
    c.path(d, G(c, col, 0.5, 0.05))
    return True


def calculator(c):
    c.rect(10, 4, 28, 40, c.grad(c["case"]), 3)
    c.rect(13.5, 7.5, 21, 8, c.lighten(c["green"], 0.6), 1)
    if not c.small:
        c.text(33, 14, "123", 7, c["ink"], anchor="end")
        for r in range(4):
            for k in range(4):
                col = c["orange"] if k == 3 else (c["red"] if r == 0 and k == 0 else c.lighten(c["metal"][1], 0.5))
                c.rect(13.5 + k * 5.4, 19 + r * 6, 4, 4.4, col, 0.8, width=0.7)
    else:
        for r in range(3):
            for k in range(3):
                c.rect(13.5 + k * 7.5, 19.5 + r * 7.8, 5, 5, c["orange"] if k == 2 else c.lighten(c["metal"][1], 0.4),
                       0.5, None)
    return True


def keyboard(c, hl=()):
    c.rect(3, 14, 42, 24, c.grad(c["case"]), 3)
    if c.small:
        for r in range(2):
            for k in range(5):
                col = c["green"] if (r, k) in hl else WHITE
                c.rect(6.5 + k * 7.2, 17.5 + r * 7, 6, 5.5, col, 1, None)
        c.rect(13, 31.5, 22, 3.5, WHITE, 1, None)
    else:
        for r in range(3):
            for k in range(9):
                col = c["green"] if (r, k // 2) in hl else WHITE
                c.rect(6 + k * 4.1, 17 + r * 5, 3.3, 3.8, col, 0.6, width=0.6)
        c.rect(12, 32, 24, 3.4, WHITE, 0.6, width=0.6)
    return True


PIPS = {1: [(24, 24)], 2: [(14, 14), (34, 34)], 3: [(14, 14), (24, 24), (34, 34)],
        4: [(14, 14), (34, 14), (14, 34), (34, 34)], 5: [(14, 14), (34, 14), (24, 24), (14, 34), (34, 34)],
        6: [(14, 13), (34, 13), (14, 24), (34, 24), (14, 35), (34, 35)]}


def die(c, n=5, col=None, pip=None):
    c.rect(5, 5, 38, 38, G(c, col or WHITE, 0.2, 0.08) if col else c.grad(c["page"]), 8)
    for x, y in PIPS[n]:
        c.circle(x, y, 4, pip or c["ink"], None)
    return True


SUITS = {
    "heart": "M24 32 C14 25 14 16 19.5 16 C22 16 24 18 24 20 C24 18 26 16 28.5 16 C34 16 34 25 24 32 Z",
    "diamond": "M24 13 L31.5 23 L24 33 L16.5 23 Z",
    "spade": "M24 13 C34 21 34 29 28.5 29 C26 29 24.5 27.5 24 26 C23.5 27.5 22 29 19.5 29 C14 29 14 21 24 13 Z "
             "M24 26 L27 33 H21 Z",
    "club": "M24 13 a4.5 4.5 0 0 1 3.5 7.4 a4.5 4.5 0 1 1 -1 6.6 L27 33 H21 L22 27 a4.5 4.5 0 1 1 -1 -6.6 "
            "A4.5 4.5 0 0 1 24 13 Z",
}


def card(c, suit="heart", letter="A"):
    c.rect(11, 5, 26, 38, c.grad(c["page"]), 3)
    col = c["red"] if suit in ("heart", "diamond") else c["ink"]
    c.path(SUITS[suit], col, None)
    if not c.small:
        c.text(15.5, 13, letter, 8, col)
    return True


def ivory(c):
    return c.lighten(c["yellow"], 0.82)


def mahjong(c, kind="dots"):
    c.rect(12, 7, 26, 36, G(c, c["green"]), 3)
    c.rect(9, 4, 26, 36, ivory(c), 3)
    if kind == "dots":
        for x, y, col in ((15, 11, c["blue"]), (22, 22, c["red"]), (29, 33, c["green"])):
            c.circle(x, y, 4.2, col, width=0.8)
    elif kind == "bamboo":
        for x in (15, 22, 29):
            c.rect(x - 1.8, 9, 3.6, 12, c["green"], 1.5, width=0.7)
            c.rect(x - 1.8, 23, 3.6, 12, c["green"], 1.5, width=0.7)
    elif kind == "char":
        c.line("M14 12 H30 M22 9 V20 M15 17 H29 M16 26 C20 24 25 24 29 26 M18 31 L15 36 M26 31 L29 36",
               c["red"], 2.6)
    elif kind == "wind":
        c.line("M14 12 H30 M22 12 V34 M14 22 H30 M16 34 H28", c["blue"], 2.6)
    return True


def ball(c, cx, cy, r, col):
    c.circle(cx, cy, r, G(c, col, 0.45, 0.2))
    blob(c, cx - r * 0.3, cy - r * 0.35, r * 0.35, r * 0.22, WHITE, 0.7)
    return True


def key(c, col=None):
    col = col or c["yellow"]
    c.rect(20, 21.5, 24, 5, G(c, col), 1)
    c.path("M35 26 h3 v6 h-3 z M40 26 h3 v4 h-3 z", G(c, col))
    c.circle(13, 24, 9, G(c, col))
    c.circle(13, 24, 3.5, c.grad(c["page"]))
    return True


def padlock(c, col=None):
    tube(c, "M15 22 V15 a9 9 0 0 1 18 0 V22", c["metal"][1], 4)
    c.rect(9, 21, 30, 22, G(c, col or c["yellow"]), 3)
    c.circle(24, 30, 3, c["ink"], None)
    c.path("M22.5 31 h3 l1 6 h-5 z", c["ink"], None)
    return True


def calendar(c, col=None, txt="31"):
    c.rect(6, 9, 36, 34, c.grad(c["page"]), 2.5)
    c.rect(6, 9, 36, 10, G(c, col or c["red"]), 2.5)
    tube(c, "M15 5 v8 M33 5 v8", c["metal"][0], 2)
    if txt:
        c.text(24, 38, txt, 15, c["ink"])
    return True


def floppy(c, col=None):
    c.rect(6, 6, 36, 36, G(c, col or c["blue"]), 2.5)
    c.rect(15, 6, 18, 13, c.grad(c["metal"]), 1)
    c.rect(26, 8.5, 4, 8, dark(c), 0.5, None)
    c.rect(11, 25, 26, 15, c.grad(c["page"]), 1.5)
    if not c.small:
        c.line("M14 30 H34 M14 35 H30", c.lighten(c["ink"], 0.5), 1)
    return True


def box(c, col=None, tape=True):
    col = col or c.lighten(c["brown"], 0.25)
    c.path("M6 18 L24 26 V44 L6 36 Z", G(c, col, 0.15, 0.05))
    c.path("M24 26 L42 18 V36 L24 44 Z", G(c, c.darken(col, 0.2), 0.1, 0.05))
    c.path("M6 18 L24 10 L42 18 L24 26 Z", G(c, col, 0.4, 0.0))
    if tape:
        c.line("M15 14 L33 22", c.lighten(col, 0.6), 2.4)
    return True


def shield(c, col=None):
    c.path("M24 4 L40 10 V22 C40 33 33 40 24 44 C15 40 8 33 8 22 V10 Z", G(c, col or c["blue"]))
    c.path("M24 6.5 V41.5 C16 38 10.5 31.5 10.5 22 V11.5 Z", WHITE, None, opacity=0.25)
    return True


def harddisk(c):
    c.path("M4 22 L14 14 H44 L34 22 Z", c.grad(c["case_top"]))
    c.path("M34 22 L44 14 V30 L34 38 Z", c["case_dark"])
    c.rect(4, 22, 30, 16, c.grad(c["case"]), 1)
    for i in range(4):
        c.rect(8 + i * 4, 31, 2.6, 2, dark(c), 0.4, None)
    c.circle(29, 32, 1.6, c["orange"], width=0.7)
    return True


def chart(c):
    c.rect(12, 24, 7, 16, G(c, c["red"]), 0.5)
    c.rect(21, 13, 7, 27, G(c, c["green"]), 0.5)
    c.rect(30, 19, 7, 21, G(c, c["blue"]), 0.5)
    c.line("M7 6 V40 H43", "ink", 2.2)
    return True


def mug(c, col=None, steam=True):
    col = col or c["red"]
    tube(c, "M33 21 h3 a5 5 0 0 1 0 10 h-3", col, 3)
    c.path("M10 16 h23 v19 a7 7 0 0 1 -7 7 h-9 a7 7 0 0 1 -7 -7 z", G(c, col))
    c.ellipse(21.5, 16.5, 11, 2.6, c.darken(c["brown"], 0.1), width=1)
    if steam:
        c.line("M16 11 c-2 -3 2 -4 0 -8 M23 11 c-2 -3 2 -4 0 -8", c["grey"], 1.6)
    return True


def stopwatch(c, ring=None):
    c.rect(20.5, 3, 7, 4, c.grad(c["metal"]), 1)
    tube(c, "M24 7 v3 M35 11 l2.5 -2.5", c["metal"][1], 2)
    clock_face(c, 24, 27, 17, ring or c["green"])
    return True


def phone(c, content=None):
    c.rect(12, 3, 24, 42, c.grad(c.lighten(c["ink"], 0.35), c["ink"]), 4)
    c.rect(14.5, 8, 19, 30, c.grad(c["screen"]), 1)
    c.circle(24, 41.5, 1.6, c.lighten(c["ink"], 0.5), None)
    if content:
        content(c)
    return True


def handset(c, col=None):
    col = col or c["red"]
    c.path("M8 42 L13 24 H35 L40 42 Z", G(c, col))
    c.circle(24, 33, 5.5, c.grad(c["page"]))
    if not c.small:
        for i in range(8):
            a = i * math.pi / 4
            c.circle(24 + 3.6 * math.cos(a), 33 + 3.6 * math.sin(a), 0.8, c["ink"], None)
    c.path("M5 18 C5 10 14 8 24 8 C34 8 43 10 43 18 L35 20 L33 15 C27 14 21 14 15 15 L13 20 Z", G(c, col))
    return True


def printer(c):
    c.path("M14 18 V5 H32 L36 9 V18", c.grad(c["page"]))
    if not c.small:
        c.line("M18 10 H30 M18 14 H28", c["grey"], 1)
    c.path("M4 22 L12 16 H44 L36 22 Z", c.grad(c["case_top"]))
    c.path("M36 22 L44 16 V32 L36 38 Z", c["case_dark"])
    c.rect(4, 22, 32, 16, c.grad(c["case"]), 1)
    c.rect(8, 27, 24, 3, dark(c), 0.5, None)
    c.circle(32, 34, 1.3, c["led"], None)
    return True


def scanner(c):
    c.path("M10 24 L16 6 H46 L42 24 Z", c.grad(c["case_top"]))
    c.path("M4 30 L10 24 H44 L38 30 Z", c.grad(c["screen"]))
    c.path("M38 30 L44 24 V34 L38 40 Z", c["case_dark"])
    c.rect(4, 30, 34, 10, c.grad(c["case"]), 1)
    c.line("M20 30 L26 24", c.lighten(c["cyan"], 0.5), 2)
    c.circle(33, 35, 1.3, c["led"], None)
    return True


def tv(c, content=None):
    tube(c, "M24 12 L15 3 M24 12 L33 3", c["metal"][1], 1.5)
    c.rect(4, 12, 40, 28, G(c, c["brown"], 0.25, 0.1), 3)
    c.rect(8, 16, 26, 20, c.grad(c["screen"]), 3)
    c.circle(39, 22, 2, c.grad(c["metal"]), width=0.8)
    c.circle(39, 30, 2, c.grad(c["metal"]), width=0.8)
    c.line("M10 40 l-2 4 M38 40 l2 4", "ink", 2)
    if content:
        content(c)
    return True


def webcam(c):
    c.path("M16 38 h16 l3 6 h-22 z", c.grad(c["case"]))
    c.rect(22, 30, 4, 9, c.grad(c["metal"]), 0)
    c.circle(24, 19, 14, c.grad(c["case"]))
    c.circle(24, 19, 7.5, dark(c))
    c.circle(24, 19, 4.5, c.grad(c["screen"]))
    blob(c, 22.5, 17.5, 1.6, 1.1, WHITE, 0.8)
    c.circle(33, 10, 1.4, c["led"], None)
    return True


def headphones(c, col=None):
    col = col or c["violet"]
    tube(c, "M10 30 V24 a14 14 0 0 1 28 0 V30", c.lighten(c["ink"], 0.3), 3.5)
    c.rect(5, 25, 11, 18, G(c, col), 4)
    c.rect(32, 25, 11, 18, G(c, col), 4)
    return True


def mic(c):
    tube(c, "M12 19 v3 a12 12 0 0 0 24 0 v-3 M24 34 v7", c["metal"][1], 2.2)
    c.rect(15, 41, 18, 3.5, c.grad(c["metal"]), 1.5)
    c.rect(17, 3, 14, 26, c.grad(c["metal"]), 7)
    if not c.small:
        c.line("M19 10 H29 M18 15 H30 M18 20 H30", c.darken(c["metal"][1], 0.2), 1)
    return True


def palette(c):
    c.path("M24 6 C36 6 44 13 44 22 C44 30 38 32 33 31 C29 30 27 33 29 37 C31 42 26 44 21 43 "
           "C11 42 4 34 4 24 C4 14 13 6 24 6 Z", G(c, c.lighten(c["brown"], 0.45), 0.3, 0.05))
    c.ellipse(17, 33, 3.5, 2.6, c.darken(c["brown"], 0.1), width=1)
    for (x, y), col in zip(((13, 21), (19, 13), (28, 11), (36, 16), (37, 24)),
                           (c["red"], c["yellow"], c["green"], c["blue"], c["violet"])):
        c.circle(x, y, 3.6, col, width=1)
    return True


def bucket(c, col=None):
    col = col or c["red"]
    tube(c, "M9 18 C9 2 39 2 39 18", c["metal"][1], 1.6)
    c.path("M9 17 h30 l-3 25 h-24 z", c.grad(c["metal"]))
    c.ellipse(24, 17, 15, 4, G(c, col))
    c.path("M33 19 v10 a2 2 0 0 1 -4 0 v-8 z", col, None)
    return True


def golf(c):
    c.ellipse(24, 38, 21, 6.5, G(c, c["green"]))
    c.ellipse(31, 38, 3, 1.2, c["ink"], None)
    tube(c, "M31 38 V6", WHITE, 1.4)
    c.path("M32 6 L45 11 L32 16 Z", G(c, c["red"]))
    ball(c, 14, 36, 4, WHITE)
    return True


def bomb(c):
    tube(c, "M31 15 C33 8 38 9 39 5", c["brown"], 1.6)
    c.rect(26, 12, 8, 6, c.grad(c["metal"]), 1)
    c.circle(22, 29, 15, c.grad(c.lighten(c["ink"], 0.45), c["ink"]))
    blob(c, 16, 23, 4, 2.5, WHITE, 0.4)
    c.path(star_d(40, 5, 5, 8, 0.4), c["yellow"], c["orange"], 1)
    return True


def plane(c, col=None):
    col = col or c["grey"]
    c.path("M4 26 C4 22 10 21 16 21 H37 L43 12 H47 L45 25 C45 28 41 29 37 29 H10 C6 29 4 28 4 26 Z",
           G(c, c.lighten(col, 0.4)))
    c.path("M18 25 L31 25 L22 37 H17 Z", G(c, col))
    if not c.small:
        for x in (12, 17, 22, 27, 32):
            c.circle(x, 24, 0.9, c["blue"], None)
    return True


def board(c, n=6, col=None):
    c.rect(4, 4, 40, 40, G(c, col or c.lighten(c["brown"], 0.45), 0.2, 0.05), 2)
    if not c.small or n <= 4:
        step = 40 / n
        d = "".join(f"M{4 + i * step:.2f} 4 V44 M4 {4 + i * step:.2f} H44 " for i in range(1, n))
        c.line(d, c.darken(c["brown"], 0.1), 0.8)
    return True


def bulb(c):
    c.path("M24 4 a13 13 0 0 1 8 23 c-2 2 -3 4 -3 7 h-10 c0 -3 -1 -5 -3 -7 a13 13 0 0 1 8 -23 z",
           G(c, c["yellow"], 0.55, 0.0))
    c.line("M20 28 L22 18 L24 22 L26 18 L28 28", c["orange"], 1.2)
    c.rect(19, 34, 10, 8, c.grad(c["metal"]), 1.5)
    c.line("M19 37 H29 M19 39.5 H29", c.darken(c["metal"][1], 0.2), 0.8)
    blob(c, 18, 11, 3, 2, WHITE, 0.6)
    return True


def lifebuoy(c):
    c.circle(24, 24, 14, "none", "ink", 13)
    c.circle(24, 24, 14, "none", WHITE, 10.6)
    for a in (0, 90, 180, 270):
        c.path(arc(24, 24, 14, a + 20, a + 70), "none", c["red"], 10.6 / 1.0)
    c.circle(24, 24, 14, "none", c.lighten(c["ink"], 0.6), 0.8)
    return True


def coins(c):
    for i in range(4):
        y = 38 - i * 5
        c.path(f"M8 {y} v3 a12 4 0 0 0 24 0 v-3", c.darken(c["yellow"], 0.2))
        c.ellipse(20, y, 12, 4, G(c, c["yellow"], 0.35, 0.05))
    return True


def banknote(c):
    c.rect(4, 12, 40, 24, G(c, c["green"], 0.5, 0.05), 2)
    c.rect(7, 15, 34, 18, "none", 0.5, c.darken(c["green"], 0.1), 0.8)
    c.circle(24, 24, 6, c.lighten(c["green"], 0.7), c.darken(c["green"], 0.2), 1)
    return True


def wallet(c, col=None):
    col = col or c["brown"]
    c.rect(6, 12, 36, 28, G(c, col, 0.25, 0.1), 4)
    c.path("M28 20 h16 v13 h-16 a3 3 0 0 1 -3 -3 v-7 a3 3 0 0 1 3 -3 z", G(c, c.darken(col, 0.15), 0.2, 0.0))
    c.circle(31, 26.5, 2, c.grad(c["metal"]), width=0.8)
    return True


def piggy(c, col=None):
    col = col or c.lighten(c["red"], 0.45)
    c.rect(12, 34, 5, 9, G(c, col), 1)
    c.rect(29, 34, 5, 9, G(c, col), 1)
    c.ellipse(23, 28, 18, 13, G(c, col, 0.3, 0.1))
    c.path("M14 17 L13 9 L20 15 Z", G(c, col))
    c.ellipse(41, 29, 4, 5, G(c, col, 0.1, 0.1))
    c.circle(33, 23, 1.4, c["ink"], None)
    c.line("M19 17 H27", "ink", 2)
    c.ellipse(23, 9, 6, 2.2, G(c, c["yellow"]), width=1)
    return True


def gantt(c):
    c.rect(4, 7, 40, 34, c.grad(c["page"]), 2)
    c.rect(4, 7, 40, 7, c.lighten(c["metal"][1], 0.4), 2)
    if not c.small:
        c.line("M14 14 V41 M24 14 V41 M34 14 V41", c.lighten(c["metal"][1], 0.4), 0.8)
    c.rect(7, 17, 15, 5, G(c, c["blue"]), 1)
    c.rect(16, 25, 17, 5, G(c, c["green"]), 1)
    c.rect(27, 33, 14, 5, G(c, c["orange"]), 1)
    return True


def sticky(c, col=None):
    col = col or c["yellow"]
    c.path("M7 8 h34 v24 l-9 9 h-25 z", G(c, c.lighten(col, 0.3), 0.3, 0.0))
    c.path("M41 32 h-7 a2 2 0 0 0 -2 2 v7", c.darken(col, 0.1))
    if not c.small:
        c.line("M12 18 H36 M12 24 H36 M12 30 H27", c.darken(col, 0.45), 1.2)
    c.circle(24, 9, 3, G(c, c["red"]))
    return True


def cert(c):
    c.rect(4, 8, 40, 28, c.grad(c["page"]), 1.5)
    c.rect(7, 11, 34, 22, "none", 0.5, c["blue"], 0.9)
    if not c.small:
        c.line("M12 17 H36 M12 22 H30", c.lighten(c["ink"], 0.5), 1.2)
    c.path("M30 34 l-3 10 l4 -2 l2 4 l2 -11 z M38 34 l3 10 l-4 -2 l-2 4 l-2 -11 z", G(c, c["red"]))
    c.circle(34, 31, 7, G(c, c["red"]))
    return True


def mouse(c):
    tube(c, "M24 6 C24 1 31 3 33 0", c.lighten(c["ink"], 0.4), 1.2)
    c.path("M11 18 a13 13 0 0 1 26 0 v10 a13 13 0 0 1 -26 0 z", c.grad(c["case"]))
    c.path("M11 18 H37", "none")
    c.path("M19.7 5.8 V18 M28.3 5.8 V18", "none")
    c.path("M19.7 5.8 a13 13 0 0 1 8.6 0 V18 h-8.6 z", c.lighten(c["metal"][1], 0.35), None)
    c.path("M11 18 a13 13 0 0 1 26 0 v10 a13 13 0 0 1 -26 0 z M11 18 H37 M19.7 5.8 V18 M28.3 5.8 V18", "none")
    return True


def usbstick(c, col=None):
    def s(cv):
        cv.rect(34, 18, 10, 12, cv.grad(cv["metal"]), 0.5)
        cv.rect(37, 21, 2.5, 2, dark(cv), 0, None)
        cv.rect(40.5, 21, 2.5, 2, dark(cv), 0, None)
        cv.rect(4, 15, 31, 18, G(cv, col or cv["blue"]), 3)
        cv.rect(9, 19, 16, 10, cv.grad(cv["page"]), 1, width=0.8)
    return at(c, 0, 0, 1, s, _rot=-40)


def battery(c, col=None):
    c.rect(40, 19, 4, 10, c.grad(c["metal"]), 1)
    c.rect(4, 14, 36, 20, c.grad(c["page"]), 3)
    c.rect(4, 14, 24, 20, G(c, col or c["green"]), 3)
    c.rect(4, 14, 36, 20, "none", r=3)
    return True


def train(c, col=None):
    col = col or c["red"]
    c.line("M10 46 L16 40 M38 46 L32 40", "ink", 2)
    c.rect(9, 5, 30, 35, G(c, col), 7)
    c.rect(13, 10, 22, 13, c.grad(c["screen"]), 2)
    c.circle(16, 32, 2.6, c.lighten(c["yellow"], 0.3))
    c.circle(32, 32, 2.6, c.lighten(c["yellow"], 0.3))
    c.rect(20, 30, 8, 4, dark(c), 1, None)
    return True


def drone(c):
    c.line("M12 12 L36 36 M36 12 L12 36", "ink", 3.4)
    c.line("M12 12 L36 36 M36 12 L12 36", c["metal"][1], 1.6)
    for x, y in ((11, 11), (37, 11), (11, 37), (37, 37)):
        c.ellipse(x, y, 9, 3, c.lighten(c["cyan"], 0.6), width=1)
        c.circle(x, y, 1.8, dark(c), None)
    c.rect(17, 17, 14, 14, G(c, c["red"]), 4)
    c.circle(24, 24, 3, dark(c), None)
    return True


def flame(c, col=None):
    c.path("M24 2 C28 10 37 14 37 26 A13 13 0 0 1 11 26 C11 19 14 16 17 11 C18 16 20 18 22 18 "
           "C22 12 21 7 24 2 Z", c.grad(c["orange"], c["red"]))
    c.path("M24 20 C26 25 31 27 31 32 A7 7 0 0 1 17 32 C17 28 20 27 21 24 C22 26 23 26 24 20 Z",
           c["yellow"], None)
    return True


def fat_arrow(c, col=None):
    c.path("M17 4 h14 v16 h9 l-16 19 l-16 -19 h9 z", G(c, col or c["green"]))
    return True


def cycle(c, col=None):
    col = col or c["green"]
    for a0 in (200, 20):
        a1 = a0 + 135
        tube(c, arc(24, 24, 14, a0, a1), col, 4.5)
        ex, ey = 24 + 14 * math.cos(math.radians(a1)), 24 + 14 * math.sin(math.radians(a1))
        tx, ty = -math.sin(math.radians(a1)), math.cos(math.radians(a1))
        nx, ny = math.cos(math.radians(a1)), math.sin(math.radians(a1))
        c.path(f"M{ex + nx * 6:.2f} {ey + ny * 6:.2f} L{ex + tx * 8:.2f} {ey + ty * 8:.2f} "
               f"L{ex - nx * 6:.2f} {ey - ny * 6:.2f} Z", col)
    return True


def cube(c, col, letter=None):
    c.path("M6 14 L14 6 H42 L34 14 Z", G(c, col, 0.5, 0.0))
    c.path("M34 14 L42 6 V34 L34 42 Z", c.darken(col, 0.25))
    c.rect(6, 14, 28, 28, G(c, col, 0.2, 0.1), 1)
    if letter:
        c.text(20, 36, letter, 21, WHITE)
    return True


def person(c, col=None):
    c.path("M8 44 C8 32 14 27 24 27 C34 27 40 32 40 44 Z", G(c, col or c["blue"]))
    c.circle(24, 15, 9, G(c, skin(c), 0.3, 0.05))
    return True


def page_lines(c, cols=None):
    page(c)
    cols = cols or [c["ink"]] * 6
    for i, col in enumerate(cols):
        if c.small and i % 2:
            continue
        w = (24, 18, 22, 14, 20, 16)[i % 6]
        c.line(f"M12 {16 + i * 4} h{w}", col, 1.6 if not c.small else 1.4)
    return True


def envelope(c, col=None, stamp=True):
    c.rect(4, 11, 40, 27, c.grad(col or c["page"]), 2)
    c.path("M4.5 12 L24 27 L43.5 12", "none")
    c.path("M4.5 37 L18 23 M43.5 37 L30 23", "none", c.lighten(c["ink"], 0.5), 1)
    if stamp:
        c.rect(34, 14, 7, 8, G(c, c["red"]), 0.5, width=0.8)
    return True


def photo(c, sky=None):
    c.rect(5, 8, 38, 30, WHITE, 1.5)
    c.rect(8, 11, 32, 24, G(c, sky or c["cyan"], 0.5, 0.0), 0, None)
    c.path("M8 35 L18 22 L25 30 L30 25 L40 35 Z", G(c, c["green"]), None)
    c.circle(33, 17, 3, c["yellow"], None)
    c.rect(8, 11, 32, 24, "none", 0.5, "ink", 0.8)
    return True


def frame(c):
    c.rect(4, 6, 40, 36, G(c, c["brown"], 0.3, 0.1), 1)
    c.rect(9, 11, 30, 26, G(c, c["cyan"], 0.5, 0.0), 0)
    c.path("M9 37 L18 24 L25 32 L30 27 L39 37 Z", G(c, c["green"]), None)
    c.circle(32, 18, 3.2, c["yellow"], None)
    c.rect(9, 11, 30, 26, "none", 0.5, "ink", 0.9)
    return True


def notebook(c, col=None):
    c.rect(11, 4, 30, 40, G(c, col or c["green"]), 2)
    c.rect(17, 10, 18, 8, c.grad(c["page"]), 1, width=0.8)
    for y in (9, 17, 25, 33, 41) if not c.small else (10, 22, 34):
        tube(c, f"M7 {y} h7", c["metal"][0], 1.4)
    return True


def book(c, col=None, ribbon=True):
    col = col or c["red"]
    c.path("M10 6 h28 v36 h-28 z", c.grad(c["page"]))
    c.rect(8, 4, 28, 36, G(c, col), 2)
    c.rect(8, 4, 4, 36, c.darken(col, 0.2), 1)
    if ribbon:
        c.path("M28 40 v6 l2 -2 l2 2 v-6 z", c["yellow"], width=0.8)
    return True


def chip(c, col=None):
    if not c.small:
        for i in range(5):
            o = 13 + i * 5.5
            c.line(f"M{o} 5 v4 M{o} 39 v4 M5 {o} h4 M39 {o} h4", c["metal"][1], 2)
    else:
        for o in (16, 24, 32):
            c.line(f"M{o} 5 v4 M{o} 39 v4 M5 {o} h4 M39 {o} h4", c["metal"][1], 2)
    c.rect(9, 9, 30, 30, c.grad(c.lighten(c["ink"], 0.35), c["ink"]), 2)
    c.rect(15, 15, 18, 18, col or c.lighten(c["metal"][1], 0.25), 1, None)
    return True


def disc_badge(c, col, gname):
    c.circle(24, 24, 19, G(c, col, 0.35, 0.1))
    gl(c, gname, 11, 11, 26, WHITE, w=3)
    return True


def play_disc(c, col=None):
    c.circle(24, 24, 19, G(c, col or c["green"], 0.35, 0.1))
    c.path("M18 13 L35 24 L18 35 Z", WHITE, None)
    return True


def ghost(c, col=None):
    c.path("M8 42 V22 a16 16 0 0 1 32 0 V42 l-5.3 -5 l-5.3 5 l-5.3 -5 l-5.3 5 l-5.3 -5 z", G(c, col or c["red"]))
    for x in (18, 30):
        c.circle(x, 22, 4.5, WHITE)
        c.circle(x + 1.5, 23, 2, c["blue"], None)
    return True


def graph_paper(c):
    c.rect(4, 4, 40, 40, c.grad(c["page"]), 2)
    if not c.small:
        c.line("M12 4 V44 M20 4 V44 M28 4 V44 M36 4 V44 M4 12 H44 M4 20 H44 M4 28 H44 M4 36 H44",
               c.lighten(c["cyan"], 0.5), 0.6)
    c.line("M24 6 V42 M6 24 H42", "ink", 1.2)
    return True


def compass(c):
    tube(c, "M24 10 L12 42 M24 10 L36 42", c["metal"][1], 2.4)
    c.path("M34 38 l4 6 l1 -7 z", c.lighten(c["brown"], 0.5))
    c.circle(24, 10, 5, G(c, c["red"]))
    tube(c, "M24 5 V1", c["metal"][1], 1.5)
    return True


def remote(c):
    c.rect(16, 3, 16, 42, c.grad(c.lighten(c["ink"], 0.35), c["ink"]), 4)
    c.circle(24, 10, 3, c["red"], None)
    for r in range(3):
        for k in range(2):
            c.rect(19 + k * 6.5, 17 + r * 7, 4, 4, c.lighten(c["metal"][1], 0.3), 1, None)
    return True


def reel(c):
    c.path("M30 36 L46 40 L44 46 L28 42 Z", dark(c))
    c.circle(22, 22, 18, c.grad(c["metal"]))
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        c.circle(22 + 10 * math.cos(a), 22 + 10 * math.sin(a), 4, dark(c), None)
    c.circle(22, 22, 2.5, dark(c), None)
    return True


def cassette(c, col=None):
    c.rect(4, 9, 40, 30, c.grad(c.lighten(c["ink"], 0.35), c["ink"]), 3)
    c.rect(8, 12, 32, 16, G(c, col or c["orange"]), 1.5)
    c.rect(14, 16, 20, 8, c.lighten(c["ink"], 0.3), 4, None)
    c.circle(18, 20, 3, WHITE, None)
    c.circle(30, 20, 3, WHITE, None)
    c.path("M12 39 L15 32 H33 L36 39", c.lighten(c["ink"], 0.2))
    return True


def jukebox(c):
    c.path("M7 44 V20 A17 15 0 0 1 41 20 V44 Z", G(c, c["red"]))
    c.path("M12 30 V21 A12 10 0 0 1 36 21 V30 Z", G(c, c.lighten(c["yellow"], 0.4), 0.3, 0.05))
    if not c.small:
        c.line("M15 25 H33 M15 28 H33", c["orange"], 1)
    c.rect(13, 33, 22, 8, dark(c), 1)
    if not c.small:
        c.line("M16 35.5 H32 M16 38.5 H32", c.lighten(c["ink"], 0.5), 0.9)
    c.path("M7 44 V20 A17 15 0 0 1 41 20 V44 Z", "none")
    c.line("M9.5 42 V21 A14.5 13 0 0 1 38.5 21 V42", c["yellow"], 1.2)
    return True


def menu(c):
    c.rect(9, 4, 30, 40, c.grad(c["page"]), 2)
    c.rect(9, 4, 30, 7, c.lighten(c["yellow"], 0.4), 2)
    for i, col in enumerate((c["red"], c["blue"], c["green"], c["orange"])):
        y = 15 + i * 7
        c.rect(12, y, 5, 5, col, 1, None)
        c.line(f"M20 {y + 2.5} H34", c.lighten(c["ink"], 0.4), 1.6)
    return True


def newspaper(c):
    c.rect(5, 6, 34, 36, c.grad(c["page"]), 1.5)
    c.rect(9, 10, 26, 5, c["ink"], 0.5, None)
    c.rect(9, 18, 11, 10, c.lighten(c["cyan"], 0.4), 0, None)
    if not c.small:
        c.line("M23 19 H35 M23 23 H35 M23 27 H35 M9 32 H35 M9 36 H30", c.lighten(c["ink"], 0.45), 1.2)
    else:
        c.line("M23 20 H35 M9 33 H35", c.lighten(c["ink"], 0.45), 1.2)
    return True


def feed_disc(c):
    c.circle(24, 24, 19, G(c, c["orange"]))
    c.path(arc(13, 35, 12, 270, 360), "none", WHITE, 4)
    c.path(arc(13, 35, 21, 270, 360), "none", WHITE, 4)
    c.circle(15, 33, 3, WHITE, None)
    return True


def target(c):
    for r, col in ((19, c["red"]), (14, WHITE), (9, c["red"]), (4, WHITE)):
        c.circle(24, 24, r, col, width=1)
    return True


def check_disc(c):
    c.circle(24, 24, 19, G(c, c["green"]))
    c.line("M14 24 L21 31 L35 16", WHITE, 5.5)
    return True


def tag(c, col=None, text=None):
    c.path("M6 10 H28 L42 24 L28 38 H6 Z", G(c, col or c["yellow"], 0.4, 0.05))
    c.circle(12, 24, 2.5, c.grad(c["page"]))
    if text:
        c.text(25, 28.5, text, 11, c["ink"])
    return True


def database(c, col=None):
    col = col or c["blue"]
    c.path("M8 10 V38 A16 5 0 0 0 40 38 V10 Z", G(c, col, 0.3, 0.15))
    c.path("M8 19.5 A16 5 0 0 0 40 19.5 M8 29 A16 5 0 0 0 40 29", "none", c.lighten(col, 0.6), 1.2)
    c.path("M8 10 V38 A16 5 0 0 0 40 38 V10", "none")
    c.ellipse(24, 10, 16, 5, G(c, col, 0.6, 0.0))
    return True


def gem(c, col):
    c.path("M10 16 L16 8 H32 L38 16 L24 40 Z", G(c, col, 0.45, 0.1))
    c.path("M10 16 H38 M16 8 L20 16 L24 40 L28 16 L32 8", "none", c.lighten(col, 0.6), 1)
    c.path("M10 16 L16 8 H32 L38 16 L24 40 Z", "none")
    return True


def foldmap(c):
    cols = (c.lighten(c["cyan"], 0.4), c.lighten(c["green"], 0.4), c.lighten(c["cyan"], 0.25))
    xs = (4, 17, 30, 44)
    for i in range(3):
        y0, y1 = (6, 10) if i % 2 == 0 else (10, 6)
        c.path(f"M{xs[i]} {y0} L{xs[i + 1]} {y1} V{y1 + 32} L{xs[i]} {y0 + 32} Z", cols[i])
    c.path("M8 14 c4 -2 7 2 9 6 c3 4 9 0 12 4 c2 3 6 1 10 3 L39 36 c-4 -2 -9 1 -13 -1 c-4 -3 -10 2 -13 -2 "
           "c-2 -3 -4 -1 -5 -1 z", G(c, c["green"], 0.2, 0.0), None)
    return True


def pin(c, col=None):
    c.path("M24 44 C18 32 10 26 10 18 A14 14 0 0 1 38 18 C38 26 30 32 24 44 Z", G(c, col or c["red"]))
    c.circle(24, 18, 5, WHITE)
    return True


def letter_tile(c, letter, col=None):
    c.rect(6, 6, 36, 36, G(c, col or ivory(c), 0.3, 0.05), 4)
    c.text(24, 34, letter, 24, c["ink"])
    return True


def speaker(c, col=None):
    c.path("M6 17 H14 L26 7 V41 L14 31 H6 Z", c.grad(c["metal"]))
    c.path(arc(26, 24, 9, -50, 50), "none", col or c["ink"], 2.6)
    c.path(arc(26, 24, 16, -50, 50), "none", col or c["ink"], 2.6)
    return True


def plug(c):
    tube(c, "M24 30 V38 C24 44 34 44 40 42", c.lighten(c["ink"], 0.3), 2.5)
    c.rect(17, 3, 4, 10, c.grad(c["metal"]), 1)
    c.rect(27, 3, 4, 10, c.grad(c["metal"]), 1)
    c.path("M12 12 H36 V20 A12 12 0 0 1 12 20 Z", G(c, c.lighten(c["ink"], 0.4), 0.2, 0.0))
    return True


def knight(c, col=None):
    col = col or c.lighten(c["metal"][0], 0.3)
    c.rect(10, 38, 28, 6, G(c, col), 2)
    c.path("M14 38 C14 30 20 28 20 24 C17 25 13 27 11 26 C9 25 9 22 11 20 C15 15 18 11 22 8 L22 4 L26 8 "
           "C34 10 38 18 36 38 Z", G(c, col, 0.3, 0.1))
    c.circle(21, 14, 1.6, c["ink"], None)
    return True


def hoop(c):
    c.circle(24, 24, 18, c.lighten(c["page"][0], 0), "ink", None)
    c.circle(24, 24, 18, "none", "ink", 6.4)
    c.circle(24, 24, 18, "none", c.lighten(c["brown"], 0.45), 4)
    c.rect(20, 2, 8, 5, c.grad(c["metal"]), 1)
    for (x, y), col in zip(((16, 18), (22, 18), (16, 24), (22, 24), (28, 24), (22, 30), (28, 30)),
                           (c["red"], c["red"], c["red"], c["green"], c["red"], c["green"], c["green"])):
        c.line(f"M{x - 2} {y - 2} l4 4 M{x + 2} {y - 2} l-4 4", col, 1.8)
    return True


def dock(c, col, items=None):
    c.path("M2 34 L8 26 H40 L46 34 Z", G(c, col, 0.5, 0.05))
    c.rect(2, 34, 44, 4, c.darken(col, 0.2), 1)
    for i, it in enumerate(items or (c["red"], c["green"], c["blue"], c["yellow"])):
        ball(c, 10 + i * 9.3, 21, 4.4, it)
    return True


def piano(c):
    c.rect(4, 16, 40, 26, WHITE, 1.5)
    c.line("M10.7 16 V42 M17.4 16 V42 M24 16 V42 M30.7 16 V42 M37.4 16 V42", "ink", 1)
    for x in (8.5, 15.2, 28.5, 35.2):
        c.rect(x, 16, 4.2, 15, c["ink"], 0.5, None)
    c.rect(4, 16, 40, 26, "none", r=1.5)
    return True


def bag(c, col=None):
    col = col or c["orange"]
    c.path("M4 18 H44 L40 44 H8 Z", G(c, col))
    c.path("M4 18 H44 L42 23 H6 Z", c.darken(col, 0.2))
    tube(c, "M14 21 C14 8 22 8 22 21 M26 21 C26 8 34 8 34 21", c.darken(col, 0.35), 1.4)
    return True


def glasses(c):
    tube(c, "M20 24 C22 21 26 21 28 24 M4 22 L2 14 M44 22 L46 14", dark(c), 1.8)
    for x in (12, 36):
        c.circle(x, 25, 8.5, c.lighten(c["cyan"], 0.7), "ink", None)
        c.circle(x, 25, 8.5, "none", "ink", 4)
        c.circle(x, 25, 8.5, "none", dark(c), 2)
    return True


def safe(c):
    c.rect(5, 5, 38, 38, c.grad(c["metal"]), 3)
    c.rect(9, 9, 30, 30, c.grad(c.lighten(c["metal"][0], 0.2), c["metal"][1]), 2)
    c.circle(24, 24, 8, G(c, c["grey"], 0.5, 0.1))
    if not c.small:
        for i in range(8):
            a = i * math.pi / 4
            c.line(f"M{24 + 6 * math.cos(a):.2f} {24 + 6 * math.sin(a):.2f} L{24 + 8 * math.cos(a):.2f} "
                   f"{24 + 8 * math.sin(a):.2f}", "ink", 0.8)
    c.line("M24 24 L24 18", c["red"], 2)
    c.rect(36, 18, 3, 12, dark(c), 1, None)
    return True


def crate(c, col=None):
    col = col or c.lighten(c["brown"], 0.3)
    c.rect(6, 6, 36, 36, G(c, col, 0.25, 0.1), 1)
    c.rect(10, 10, 28, 28, "none", 0.5, c.darken(col, 0.35), 1.2)
    c.line("M10 10 L38 38 M38 10 L10 38", c.darken(col, 0.35), 1.6)
    return True


def screen_stand(c, content=None):
    tube(c, "M24 34 V44 M24 36 L14 45 M24 36 L34 45", c["metal"][1], 1.8)
    c.rect(3, 3, 42, 4, c.grad(c["metal"]), 2)
    c.rect(5, 7, 38, 27, WHITE, 0)
    if content:
        content(c)
    return True


def pendulum(c):
    c.rect(6, 4, 36, 4, G(c, c["brown"]), 1)
    if not c.small:
        c.path(arc(24, 8, 30, 70, 110), "none", c["grey"], 1, opacity=0.8)
    c.line("M24 8 L33 34", "ink", 1.6)
    ball(c, 34, 36, 7, c["red"])
    if not c.small:
        c.line("M24 8 L15 34", c.lighten(c["ink"], 0.6), 1)
        c.circle(14, 36, 6, "none", c.lighten(c["ink"], 0.6), 1)
    return True


def scroll(c):
    c.rect(10, 8, 28, 32, c.grad(c["page"]), 0)
    c.ellipse(10, 24, 3.5, 16, c.lighten(c["yellow"], 0.7))
    c.ellipse(38, 24, 3.5, 16, c.lighten(c["yellow"], 0.55))
    c.path("M10 8 H38 M10 40 H38", "none")
    for i in range(5) if not c.small else range(0, 5, 2):
        c.line(f"M16 {14 + i * 5} h{16 if i % 2 == 0 else 12}", c.lighten(c["ink"], 0.4), 1.4)
    return True


def feather(c, col=None):
    col = col or c["blue"]
    c.path("M8 42 C12 28 22 12 42 5 C40 20 30 34 14 38 Z", G(c, c.lighten(col, 0.4), 0.4, 0.0))
    c.line("M7 44 L36 12", c.darken(col, 0.2), 1.6)
    if not c.small:
        c.line("M18 31 L14 26 M24 24 L22 17 M30 18 L30 11 M20 30 L27 33 M26 23 L34 25", c.darken(col, 0.1), 0.9)
    return True


def pointer(c):
    c.path("M10 4 L10 38 L18 30 L24 43 L30 40 L24 28 L35 28 Z", WHITE)
    return True


def clipboard(c):
    c.rect(8, 6, 32, 38, G(c, c["brown"], 0.3, 0.1), 3)
    c.rect(12, 11, 24, 29, c.grad(c["page"]), 0.5)
    if not c.small:
        c.line("M15 20 H33 M15 25 H33 M15 30 H28", c.lighten(c["ink"], 0.45), 1.2)
    c.rect(17, 3, 14, 8, c.grad(c["metal"]), 2)
    return True


def uml(c):
    c.line("M16 20 V28 M16 28 H32 V30 M16 28 V30", "ink", 1.4)
    for x, y, w in ((8, 4, 18), (4, 30, 16), (26, 30, 18)):
        c.rect(x, y, w, 14, c.lighten(c["yellow"], 0.7), 0.5)
        c.line(f"M{x} {y + 5} h{w}", "ink", 1)
    return True


def nodes(c):
    pts = ((10, 12), (36, 9), (24, 26), (8, 38), (39, 36))
    c.line("M10 12 L36 9 L24 26 L10 12 M24 26 L8 38 M24 26 L39 36 L36 9", "ink", 1.6)
    for (x, y), col in zip(pts, (c["red"], c["blue"], c["green"], c["yellow"], c["violet"])):
        ball(c, x, y, 5.5, col)
    return True


def chain(c):
    tube(c, "M6 30 L14 22 a5 5 0 0 1 7 7 L13 37 a5 5 0 0 1 -7 -7", c["metal"][1], 3)
    tube(c, "M22 26 L30 18 a5 5 0 0 1 7 7 L29 33 a5 5 0 0 1 -7 -7", c["metal"][0], 3)
    return True


def speech_waves(c, col=None):
    col = col or c["blue"]
    for r in (6, 12, 18):
        c.path(arc(4, 24, r, -40, 40), "none", col, 2.6)
    return True


def kanji_wen(c, col):
    c.line("M24 9 V13 M13 14 H35 M18 18 C20 26 26 32 35 37 M30 18 C28 26 22 32 13 37", col, 3)
    return True


# ---- screen contents (screen 8..40 x 9..31) ---------------------------------------
def scr_prompt(c):
    c.line("M12 14 l4.5 4 l-4.5 4", WHITE, 2.4)
    c.line("M19 23 h9", WHITE, 2.4)


def scr_graph(c):
    c.line("M10 26 l5 -4 l4 3 l5 -10 l5 7 l4 -5 l5 3", c["led"], 2.4)


def scr_code(c):
    c.line("M15 14 l-4 6 l4 6 M33 14 l4 6 l-4 6 M26 13 l-4 14", WHITE, 2.2)


def scr_film(c):
    c.rect(10, 13, 28, 14, dark(c), 0, None)
    for x in (12, 18, 24, 30):
        c.rect(x + 0.5, 15.5, 4.5, 9, c.lighten(c["cyan"], 0.6), 0.5, None)


def scr_x(c):
    c.line("M15 12 L33 28 M33 12 L15 28", WHITE, 4)


# ---- the programs -------------------------------------------------------------------
APPS = {}


def app(*names):
    def deco(fn):
        for n in names:
            APPS[n] = fn
        return fn
    return deco


@app("accessories-calculator")
def _(c): calculator(c)


@app("accessories-character-map")
def _(c):
    window(c, 6, 3, 36, 26)
    c.text(24, 25, "é?", 16, c["ink"])
    c.text(22, 44, "åß", 15, c["ink"])
    c.line("M38 32 V45 M36 32 h4 M36 45 h4", c["red"], 1.6)


@app("akregator")
def _(c): newspaper(c); sec(c, feed_disc)


@app("alligator")
def _(c):
    phone(c, lambda cv: (cv.path(arc(17, 32, 8, 270, 360), "none", cv["orange"], 2.6),
                         cv.path(arc(17, 32, 14, 270, 360), "none", cv["orange"], 2.6),
                         cv.circle(18.5, 30.5, 2, cv["orange"], None)))


@app("amarok")
def _(c): at(c, 0, 6, 0.85, vinyl, c["blue"]); at(c, 20, -1, 0.6, music_note, c["blue"])


@app("ark")
def _(c):
    box(c, tape=False)
    c.path("M10 16 L28 24 V42", "none", c["red"], 3)
    c.path("M28 24 L38 19.5", "none", c["red"], 3)


@app("artikulate")
def _(c):
    at(c, -7, 2, 0.9, mic)
    bubble(c, 22, 3, 22, 15, c["yellow"], -1)
    c.text(33, 15, "a", 13, c["ink"])


@app("baloo")
def _(c):
    for i, col in enumerate((c["blue"], c["green"], c["orange"])):
        x, y = 3 + i * 5, 6 + i * 5
        c.rect(x, y, 28, 20, c.grad(c["page"]), 1.5)
        c.rect(x, y, 28, 5, col, 1.5)
    sec(c, magnifier)


@app("blinken")
def _(c):
    for (a0, col) in ((180, c["green"]), (270, c["red"]), (0, c["blue"]), (90, c["yellow"])):
        c.path(sector(24, 24, 19, a0 + 4, a0 + 86), G(c, col, 0.35, 0.1))
    c.circle(24, 24, 7, dark(c))


@app("bomber")
def _(c):
    for x, h, col in ((6, 14, c["grey"]), (16, 22, c["brown"]), (28, 10, c["grey"]), (36, 18, c["brown"])):
        c.rect(x, 44 - h, 9, h, G(c, col), 0.5)
    at(c, 0, -4, 0.75, plane, c["blue"])
    c.circle(20, 24, 2.4, c["ink"], None)


@app("bovo")
def _(c):
    board(c, 6)
    for x, y in ((10.7, 10.7), (24, 24), (30.7, 30.7)):
        c.line(f"M{x - 4} {y - 4} l8 8 M{x + 4} {y - 4} l-8 8", c["red"], 2.6)
    for x, y in ((17.4, 30.7), (30.7, 17.4)):
        c.circle(x, y, 4.2, "none", c["blue"], 2.6)


@app("breeze-settings")
def _(c):
    window(c, 3, 4, 36, 30, lambda cv: [cv.rect(7 + i * 8, 16, 6, 12, col, 1, width=0.8)
                                        for i, col in enumerate((cv["blue"], cv["cyan"], cv["violet"], cv["grey"]))])
    sec(c, brush, c["blue"])


@app("buho")
def _(c): at(c, -2, 0, 0.9, notebook, c["green"]); sec(c, pencil)


@app("calamares")
def _(c): at(c, 0, 12, 0.8, harddisk); at(c, 16, -2, 0.55, fat_arrow, c["green"])


@app("ubiquity-kde")
def _(c):
    at(c, 0, 0, 0.55, cd)
    at(c, 12, 10, 0.4, fat_arrow, c["orange"], _rot=-60)
    at(c, 14, 20, 0.7, harddisk)


@app("calindori")
def _(c):
    def s(cv):
        cv.rect(16, 11, 16, 15, WHITE, 1, width=0.8)
        cv.rect(16, 11, 16, 4.5, cv["red"], 1, None)
        if not cv.small:
            cv.text(24, 24, "7", 8, cv["ink"])
    phone(c, s)


@app("cantor")
def _(c): page(c, emblem="sigma", emblem_color=c["blue"])


@app("cervisia")
def _(c): page(c, emblem="branch", emblem_color=c["green"])


@app("choqok")
def _(c):
    bubble(c, 3, 4, 36, 24, c["cyan"])
    if not c.small:
        c.line("M9 12 H33 M9 18 H27", c.darken(c["cyan"], 0.4), 1.6)
    sec(c, globe)


@app("crow-translate")
def _(c):
    bubble(c, 2, 3, 24, 20, c.lighten(c["blue"], 0.5))
    c.text(14, 19, "A", 15, c["ink"])
    bubble(c, 20, 19, 26, 20, c["yellow"], -1)
    at(c, 21, 17, 0.5, kanji_wen, c["red"])


@app("cuttlefish")
def _(c):
    shapes = ((c["red"], "c"), (c["blue"], "s"), (c["green"], "t"), (c["yellow"], "s"), (c["violet"], "t"),
              (c["orange"], "c"), (c["cyan"], "t"), (c["grey"], "c"), (c["brown"], "s"))
    for i, (col, sh) in enumerate(shapes):
        x, y = 3 + (i % 3) * 11, 3 + (i // 3) * 11
        if sh == "c":
            c.circle(x + 4.5, y + 4.5, 4.2, G(c, col), width=0.9)
        elif sh == "s":
            c.rect(x + 0.5, y + 0.5, 8, 8, G(c, col), 1.5, width=0.9)
        else:
            c.path(f"M{x + 4.5} {y} L{x + 9} {y + 9} H{x} Z", G(c, col), width=0.9)
    sec(c, magnifier)


@app("digikam")
def _(c):
    at(c, 4, -2, 0.62, photo, c["blue"])
    at(c, -2, 2, 0.62, photo)
    at(c, 14, 15, 0.7, camera)


@app("dragonplayer")
def _(c): at(c, 0, 0, 0.85, reel); sec(c, play_disc, c["blue"])


@app("elisa")
def _(c): headphones(c); at(c, 13, 10, 0.5, music_note, c["blue"])


@app("falkon")
def _(c): globe(c, c["cyan"], c["green"]); sec(c, feather, c["orange"])


@app("fifteenpuzzle")
def _(c):
    c.rect(3, 3, 42, 42, G(c, c["brown"], 0.2, 0.1), 3)
    n = 0
    for r in range(4):
        for k in range(4):
            n += 1
            if n == 16:
                continue
            x, y = 5.5 + k * 9.5, 5.5 + r * 9.5
            c.rect(x, y, 8.5, 8.5, ivory(c) if (r + k) % 2 else c.lighten(c["red"], 0.5), 1, width=0.8)
            if not c.small:
                c.text(x + 4.25, y + 6.6, str(n), 6.5 if n > 9 else 7, c["ink"])


@app("filelight")
def _(c):
    segs = [(10, 15, ((0, 140, c["blue"]), (140, 250, c["green"]), (250, 360, c["red"]))),
            (15, 20, ((0, 70, c["cyan"]), (70, 140, c.lighten(c["blue"], 0.4)), (140, 200, c["yellow"]),
                      (250, 320, c["orange"])))]
    c.circle(24, 24, 9, c.grad(c["page"]))
    for r0, r1, parts in segs:
        r = (r0 + r1) / 2
        for a0, a1, col in parts:
            c.path(arc(24, 24, r, a0 - 90, a1 - 90), "none", "ink", r1 - r0 + 1.6)
            c.path(arc(24, 24, r, a0 - 90 + 1.5, a1 - 90 - 1.5), "none", col, r1 - r0 - 0.6)


@app("fingerprint-gui")
def _(c):
    c.rect(9, 4, 30, 40, c.grad(c["metal"]), 7)
    c.rect(13, 9, 22, 30, c.grad(c["screen"]), 5)
    gl(c, "fingerprint", 12, 12, 24, WHITE, w=2.2)


@app("firewall-config")
def _(c):
    def wall(cv):
        cv.rect(4, 22, 40, 22, G(cv, cv["red"], 0.2, 0.15), 1)
        m = cv.lighten(cv["grey"], 0.6)
        cv.line("M4 29.3 H44 M4 36.6 H44 M14 22 V29.3 M30 22 V29.3 M22 29.3 V36.6 M38 29.3 V36.6 "
                "M14 36.6 V44 M30 36.6 V44", m, 1.2)
        cv.rect(4, 22, 40, 22, "none", r=1)
    at(c, 14, -2, 0.55, flame)
    wall(c)


@app("gcompris-qt")
def _(c):
    at(c, 0, 20, 0.55, cube, c["red"], "A")
    at(c, 21, 20, 0.55, cube, c["blue"], "B")
    at(c, 10, 0, 0.55, cube, c["green"], "C")


@app("granatier")
def _(c): bomb(c)


@app("gwenview")
def _(c): frame(c)


@app("homerun")
def _(c): menu(c)


@app("kmenuedit")
def _(c): at(c, -4, 0, 1, menu); sec(c, pencil)


@app("hwinfo")
def _(c): at(c, 0, 0, 0.85, chip); sec(c, lambda cv: (cv.circle(24, 24, 19, G(cv, cv["blue"])), cv.text(24, 35, "i", 30, WHITE)))


@app("internet-web-browser")
def _(c): globe(c); at(c, 22, 18, 0.6, pointer)


@app("juk")
def _(c): jukebox(c)


@app("juliabackend")
def _(c): page(c, "JL", c["violet"], emblem="pi", emblem_color=c["violet"])


@app("octave")
def _(c):
    page(c, "OCT", c["orange"])
    c.line("M14 13 h-3 v15 h3 M30 13 h3 v15 h-3", c["ink"], 2)
    if not c.small:
        c.text(17, 19, "1", 6, c["ink"]); c.text(25, 19, "0", 6, c["ink"])
        c.text(17, 26, "0", 6, c["ink"]); c.text(25, 26, "1", 6, c["ink"])
    else:
        c.circle(17, 18, 1.6, c["ink"], None); c.circle(26, 25, 1.6, c["ink"], None)


@app("k3b")
def _(c): at(c, 0, 0, 0.9, cd); sec(c, flame)


@app("kaffeine")
def _(c): tv(c, lambda cv: cv.path("M17 20 L27 26 L17 32 Z", WHITE, None))


@app("kajongg")
def _(c): at(c, -4, 4, 0.75, mahjong, "wind"); at(c, 14, 8, 0.75, mahjong, "char")


@app("kmahjongg")
def _(c):
    at(c, -2, 14, 0.62, mahjong, "bamboo")
    at(c, 18, 14, 0.62, mahjong, "dots")
    at(c, 8, -2, 0.62, mahjong, "char")


@app("kshisen")
def _(c):
    at(c, -3, 14, 0.65, mahjong, "dots")
    at(c, 20, 14, 0.65, mahjong, "dots")
    c.line("M10 14 V5 H34 V14", c["red"], 2.4)


@app("kalarm")
def _(c): alarm_clock(c, c["red"])


@app("kalgebra")
def _(c):
    graph_paper(c)
    c.line("M10 8 C16 40 32 40 38 8", c["blue"], 2.6)
    sec(c, calculator)


@app("kmplot")
def _(c):
    graph_paper(c)
    c.line("M6 24 C10 10 14 10 18 24 C22 38 26 38 30 24 C34 10 38 10 42 24", c["red"], 2.6)
    c.line("M6 38 L42 10", c["green"], 2.2)


@app("labplot")
def _(c):
    c.rect(4, 4, 40, 40, c.grad(c["page"]), 2)
    c.line("M9 8 V39 H41", "ink", 1.6)
    c.line("M11 36 L39 12", c["red"], 1.8)
    for (x, y), col in zip(((14, 30), (18, 33), (22, 25), (27, 24), (31, 17), (35, 19), (37, 12)),
                           [c["blue"]] * 7):
        c.circle(x, y, 2.4, col, width=0.7)


@app("kig")
def _(c):
    c.path("M8 40 L40 40 L22 10 Z", "none", c["green"], 2.4)
    for x, y in ((8, 40), (40, 40), (22, 10)):
        c.circle(x, y, 3, c["red"], width=0.8)
    sec(c, compass)


@app("kalzium")
def _(c):
    # a periodic table: tall columns at both sides, the low middle block,
    # the rare earths apart below
    cw, ch = 4.4, 6.2
    for k in range(10):
        rows = range(5) if k == 0 else range(1, 5) if k in (1, 6, 7, 8, 9) else range(2, 5)
        if k == 9:
            rows = range(5)
        col = c["red"] if k == 0 else c["orange"] if k == 1 else c["green"] if k >= 6 else c["cyan"]
        if k == 9:
            col = c["yellow"]
        for r in rows:
            c.rect(2 + k * cw, 4 + r * ch, cw, ch, col, 0, "ink", 0.6)
    c.rect(11, 38, 26, 6, c.lighten(c["violet"], 0.3), 0, "ink", 0.6)


@app("kamoso")
def _(c): webcam(c)


@app("kanagram")
def _(c):
    at(c, 0, 18, 0.45, letter_tile, "R")
    at(c, 16, 18, 0.45, letter_tile, "A")
    at(c, 32, 18, 0.45, letter_tile, "T")
    tube(c, arc(24, 22, 18, 200, 340), c["green"], 2.4)
    c.path("M38 9 L43 15.5 L36 17 Z", c["green"])


@app("kapman")
def _(c):
    c.rect(3, 3, 42, 42, dark(c), 3)
    c.path("M8 8 H40 V40 H8 Z M15 15 H33 V33 H15 Z", "none", c["blue"], 2.6)
    for x in (11.5, 18, 24.5, 31, 37.5):
        c.circle(x, 11.5, 1.3, c["yellow"], None)
    at(c, 15, 15, 0.38, ghost, c["red"])


@app("kapptemplate")
def _(c):
    page(c)
    c.rect(12, 15, 22, 20, "none", 0.5, c["blue"], 1.6)
    if not c.small:
        c.path("M12 15 h22 v20 h-22 z", "none", c.lighten(c["blue"], 0.4), 1)
    sec(c, cog, 24, 24, 19, c["green"])


@app("karbon")
def _(c):
    c.line("M6 38 C10 10 30 40 40 10", c["blue"], 2.8)
    c.line("M6 38 L14 18 M40 10 L34 30", c["grey"], 1)
    for x, y in ((14, 18), (34, 30)):
        c.circle(x, y, 2.2, WHITE, width=0.9)
    for x, y in ((6, 38), (40, 10)):
        c.rect(x - 2.6, y - 2.6, 5.2, 5.2, c["red"], 0, width=0.9)
    sec(c, pen, c["violet"])


@app("kate")
def _(c):
    page_lines(c, [c["blue"], c["red"], c["ink"], c["green"], c["blue"], c["ink"]])
    if c.small:
        c.line("M12 20 h18", c["red"], 1.4)


@app("kwrite")
def _(c): at(c, -2, 0, 0.9, page_lines); pen(c)


@app("katomic")
def _(c):
    c.line("M24 22 L10 36 M24 22 L38 36 M24 22 L24 8", "ink", 3.4)
    c.line("M24 22 L10 36 M24 22 L38 36 M24 22 L24 8", c["metal"][0], 1.6)
    ball(c, 24, 22, 9, c["red"])
    for x, y in ((10, 36), (38, 36), (24, 8)):
        ball(c, x, y, 6, WHITE)


@app("kblackbox")
def _(c):
    c.line("M2 14 H20", c["red"], 2.2)
    c.line("M28 34 H46", c["red"], 2.2)
    cube(c, c.lighten(c["ink"], 0.15))
    c.circle(16, 30, 3, c.lighten(c["ink"], 0.45), None)


@app("kblocks")
def _(c):
    s = 8.5
    blocks = (((0, 3), (1, 3), (2, 3), (2, 2), c["orange"]), ((3, 3), (4, 3), (4, 2), (3, 2), c["yellow"]),
              ((0, 2), (0, 1), (1, 2), (0, 0), c["cyan"]), ((2, 0), (3, 0), (4, 0), (3, 1), c["violet"]))
    for *cells, col in blocks:
        for x, y in cells:
            c.rect(3 + x * s, 9 + y * s, s, s, G(c, col, 0.35, 0.1), 1, width=0.9)


@app("kbreakout")
def _(c):
    for r, col in enumerate((c["red"], c["orange"], c["green"])):
        for k in range(4):
            c.rect(4 + k * 10, 5 + r * 6, 9, 5, G(c, col, 0.35, 0.05), 0.5, width=0.8)
    ball(c, 30, 30, 3.4, c["metal"][0])
    c.rect(12, 39, 18, 4, G(c, c["blue"]), 2)


@app("kbruch")
def _(c):
    c.path(sector(22, 26, 18, 0, 270), G(c, c["orange"]))
    c.path(sector(27, 21, 18, 270, 360), G(c, c["yellow"]))
    c.line("M22 26 V8 M22 26 L4 26", c.darken(c["orange"], 0.3), 1)


@app("kcachegrind")
def _(c):
    c.line("M14 13 V22 M14 22 L8 31 M14 22 L30 31 M30 31 V38", "ink", 1.6)
    for x, y, w, col in ((4, 6, 20, c["red"]), (2, 30, 12, c["orange"]), (22, 26, 16, c["yellow"])):
        c.rect(x, y, w, 8, G(c, col, 0.4, 0.05), 1)
    sec(c, stopwatch)


@app("kcolorchooser")
def _(c):
    cols = (c["red"], c["orange"], c["yellow"], c["green"], c["cyan"], c["blue"], c["violet"], c.lighten(c["red"], 0.3))
    for i, col in enumerate(cols):
        c.path(sector(22, 22, 18, i * 45, i * 45 + 45), col, None)
    c.circle(22, 22, 6, WHITE, None)
    c.circle(22, 22, 18, "none")
    c.circle(22, 22, 6, "none")

    def pip(cv):
        cv.path(quad((10, 38), (32, 16), 4), cv.lighten(cv["cyan"], 0.6))
        cv.path("M8 40 L10 38", "none", "ink", 2)
        cv.path(quad((30, 18), (38, 10), 7), G(cv, cv["ink"], 0.4, 0.0))
    sec(c, pip)


@app("kde-frameworks")
def _(c):
    at(c, 0, 20, 0.55, cube, c["blue"])
    at(c, 21, 20, 0.55, cube, c["cyan"])
    at(c, 10, 0, 0.55, cube, c["grey"])


@app("kde-im-log-viewer")
def _(c):
    at(c, 4, 4, 0.9, scroll)
    bubble(c, 2, 2, 22, 14, c["yellow"])


@app("kdeapp")
def _(c):
    window(c, 4, 5, 40, 34)
    cog(c, 24, 26, 10, c["blue"])


@app("kdenlive")
def _(c): at(c, -2, -2, 0.9, clapper); sec(c, lambda cv: (cv.circle(24, 24, 20, cv.grad(cv["page"])),
                                                     gl(cv, "scissors", 9, 9, 30, cv["red"], w=2.4)))


@app("kdesrc-build")
def _(c):
    page_lines(c, [c["blue"], c["ink"], c["green"], c["ink"]])

    def hammer(cv):
        cv.path(quad((8, 40), (30, 18), 5), G(cv, cv["brown"]))
        cv.path(quad((22, 10), (38, 26), 9), cv.grad(cv["metal"]))
    sec(c, hammer)


@app("kdesvn")
def _(c):
    database(c, c["cyan"])
    gl(c, "branch", 14, 16, 20, c["ink"], w=2.4)


@app("kexi")
def _(c):
    at(c, -2, -2, 0.85, database, c["green"])

    def tbl(cv):
        cv.rect(4, 6, 40, 36, cv.grad(cv["page"]), 1.5)
        cv.rect(4, 6, 40, 9, cv["green"], 1.5)
        cv.line("M4 24 H44 M4 33 H44 M18 6 V42 M31 6 V42", "ink", 1.2)
    sec(c, tbl)


@app("kdevelop")
def _(c): monitor(c, scr_code); sec(c, wrench)


@app("kdiamond")
def _(c):
    at(c, -1, 14, 0.6, gem, c["red"])
    at(c, 19, 14, 0.6, gem, c["blue"])
    at(c, 9, -2, 0.6, gem, c["green"])


@app("kdiff3")
def _(c):
    for x, mark in ((3, c["red"]), (25, c["green"])):
        c.rect(x, 5, 20, 34, c.grad(c["page"]), 1.5)
        c.line(f"M{x + 4} 12 h12 M{x + 4} 30 h12", c.lighten(c["ink"], 0.45), 1.6)
        c.rect(x + 3, 18, 14, 6, c.lighten(mark, 0.4), 0.5, None)
    c.path("M18 42 h12 l-3 -3 M30 42 l-3 3", "none", "ink", 1.6)


@app("kfind")
def _(c): at(c, -4, -2, 0.85, page_lines); at(c, 12, 12, 0.75, magnifier)


@app("kfloppy")
def _(c):
    floppy(c)

    def wand(cv):
        cv.path(quad((8, 40), (34, 14), 5), G(cv, cv["ink"], 0.45, 0.0))
        cv.path(star_d(36, 12, 10, 5, 0.45), cv["yellow"])
    sec(c, wand)


@app("kfontview")
def _(c):
    page(c)
    c.text(23, 35, "Aa", 19, c["ink"])


@app("preferences-desktop-font-installer")
def _(c):
    at(c, 4, 16, 0.65, box)
    c.text(17, 20, "Aa", 18, c["blue"])
    at(c, 26, 10, 0.45, fat_arrow, c["green"])


@app("kfourinline")
def _(c):
    c.rect(4, 6, 40, 36, G(c, c["blue"]), 3)
    grid = ("....", ".R..", "RYY.", "YRRY")
    for r, row in enumerate(grid):
        for k, ch in enumerate(row):
            col = {"R": c["red"], "Y": c["yellow"]}.get(ch, c.lighten(c["blue"], 0.75))
            c.circle(10 + k * 9.3, 12 + r * 8.5, 3.6, col, width=0.8)


@app("kgeography")
def _(c):
    foldmap(c)

    def flag(cv):
        tube(cv, "M14 44 V6", cv["brown"], 2)
        cv.path("M15 6 L40 12 L15 22 Z", G(cv, cv["red"]))
    sec(c, flag)


@app("puremaps")
def _(c):
    foldmap(c)
    c.line("M8 36 C14 30 18 32 22 24 C26 16 30 20 32 14", c["red"], 2.2)
    at(c, 22, 0, 0.45, pin, c["red"])


@app("ksirk")
def _(c): foldmap(c); sec(c, die, 6, c["red"], WHITE)


@app("kget")
def _(c): at(c, 0, 0, 0.85, globe); at(c, 22, 14, 0.6, fat_arrow, c["green"])


@app("khangman")
def _(c):
    tube(c, "M8 42 H26 M14 42 V5 H32 V11 M14 13 L21 6", c["brown"], 2.6)
    c.circle(32, 15, 4, "none", "ink", 1.8)
    c.line("M32 19 V29 M32 22 L27 26 M32 22 L37 26 M32 29 L28 36 M32 29 L36 36", "ink", 1.8)
    c.line("M28 44 H33 M37 44 H42", c["blue"], 2)


@app("kile")
def _(c):
    page(c)
    c.path("M26 12 C24 10 21 11 21 16 V30 C21 35 18 36 16 34", "none", c["ink"], 2.4)
    if not c.small:
        c.text(31, 26, "dx", 8, c["ink"], italic=True)
    sec(c, pen, c["green"])


@app("kimagemapeditor")
def _(c):
    photo(c)
    c.rect(10, 13, 13, 10, "none", 0.5, c["red"], 1.6)
    c.circle(31, 27, 5.5, "none", c["red"], 1.6)
    sec(c, lambda cv: (cv.circle(24, 24, 20, cv.grad(cv["page"])), gl(cv, "link", 10, 10, 28, cv["blue"], w=2.6)))


@app("kipi-dngconverter")
def _(c): page(c, "DNG", c["violet"], emblem="camera", emblem_color=c["ink"])


@app("kipi-expoblending")
def _(c):
    at(c, -3, -3, 0.75, photo, c.darken(c["blue"], 0.3))
    at(c, 7, 7, 0.75, photo, c.lighten(c["cyan"], 0.3))
    at(c, 28, 0, 0.42, lambda cv: (cv.path(star_d(24, 24, 22, 12, 0.7), cv["yellow"]),
                                   cv.circle(24, 24, 12, G(cv, cv["orange"], 0.5, 0))))


@app("kipi-panorama")
def _(c):
    d = "M3 14 Q24 8 45 14 V36 Q24 30 3 36 Z"
    c.path(d, G(c, c["cyan"], 0.5, 0.0))
    c.path("M3 36 V28 L10 20 L17 27 L24 18 L32 26 L38 21 L45 28 V36 Q24 30 3 36 Z", G(c, c["green"]), None)
    c.circle(36, 16, 2.6, c["yellow"], None)
    c.path(d, "none")


@app("kirigami-gallery")
def _(c):
    def s(cv):
        cv.rect(16.5, 11, 15, 4, WHITE, 1, None)
        cv.rect(16.5, 17.5, 15, 4, cv.lighten(cv["blue"], 0.6), 1, None)
        cv.line("M17 27 H31", WHITE, 1.6)
        cv.circle(21, 27, 2.2, cv["orange"], None)
        cv.rect(16.5, 31, 6, 4, cv["green"], 1, None)
    phone(c, s)


@app("kiriki")
def _(c):
    c.rect(18, 3, 26, 34, c.grad(c["page"]), 1.5)
    if not c.small:
        c.line("M22 10 H40 M22 15 H40 M22 20 H40 M22 25 H40 M31 7 V30", c.lighten(c["ink"], 0.5), 0.9)
    at(c, 0, 16, 0.5, die, 6)
    at(c, 14, 24, 0.5, die, 3, c["red"], WHITE)


@app("kirogi")
def _(c): drone(c)


@app("kiten")
def _(c):
    book(c, c["blue"])
    c.rect(16, 12, 14, 18, "none", 0.5, WHITE, 2.4)
    c.line("M16 21 H30", WHITE, 2.4)


@app("kjumpingcube")
def _(c):
    cells = "RRBRBBRBB"
    for i, ch in enumerate(cells):
        x, y = 4 + (i % 3) * 13.5, 4 + (i // 3) * 13.5
        col = c["red"] if ch == "R" else c["blue"]
        c.rect(x, y, 13, 13, G(c, col, 0.4, 0.05), 1.5, width=0.9)
        for dx, dy in ((4, 4), (9, 9))[: 1 + i % 2]:
            c.circle(x + dx + (2.5 if i % 2 == 0 else 0), y + dy + (2.5 if i % 2 == 0 else 0), 1.6, WHITE, None)


@app("kleopatra")
def _(c): at(c, 0, -2, 0.95, cert); at(c, -2, 24, 0.5, key)


@app("klines")
def _(c):
    board(c, 5, c.lighten(c["grey"], 0.4))
    for k, col in enumerate((c["red"], c["red"], c["red"], c["red"])):
        ball(c, 8 + k * 8, 32, 3.4, col)
    ball(c, 16, 16, 3.4, c["blue"])
    ball(c, 32, 8, 3.4, c["green"])
    ball(c, 40, 24, 3.4, c["yellow"])


@app("klipper")
def _(c): clipboard(c)


@app("kmag")
def _(c):
    def px(cv):
        for i in range(4):
            for k in range(4):
                if (i + k) % 2 == 0:
                    cv.rect(11 + i * 4, 11 + k * 4, 4, 4, cv.lighten(cv["blue"], 0.25), 0, None)
                elif (i * k) % 3 == 1:
                    cv.rect(11 + i * 4, 11 + k * 4, 4, 4, cv["orange"], 0, None)
    magnifier(c, px)


@app("kmix")
def _(c):
    c.rect(4, 4, 40, 40, c.grad(c["case"]), 3)
    for i, (y, col) in enumerate(((26, c["green"]), (14, c["yellow"]), (32, c["red"]))):
        x = 13 + i * 11
        c.line(f"M{x} 9 V39", dark(c), 2.4)
        c.rect(x - 4.5, y - 2.5, 9, 5, G(c, col), 1, width=0.9)


@app("multimedia-volume-control")
def _(c): speaker(c, c["blue"])


@app("kmousetool")
def _(c): at(c, -4, 0, 1, mouse); sec(c, clock_face, 24, 24, 19, c["orange"])


@app("kmouth")
def _(c):
    c.path("M30 44 V36 C24 36 20 34 20 30 L15 29 L19 24 L16 22 C16 12 20 6 28 5 C38 4 44 10 44 20 "
           "C44 28 40 32 40 44 Z", G(c, skin(c), 0.3, 0.05))
    c.circle(27, 15, 1.6, c["ink"], None)
    at(c, -2, 4, 0.7, lambda cv: speech_waves(cv, cv["blue"]), _rot=180)


@app("kmplayer")
def _(c): monitor(c, scr_film)


@app("kmymoney")
def _(c): at(c, -2, -2, 0.9, banknote); sec(c, coins)


@app("skrooge")
def _(c): piggy(c)


@app("skrooge-black")
def _(c): piggy(c, c.lighten(c["ink"], 0.3))


@app("knetattach")
def _(c): folder(c); sec(c, plug)


@app("smb4k")
def _(c):
    at(c, -2, 0, 0.55, folder)
    at(c, 22, 22, 0.55, folder)
    tube(c, "M14 22 V36 H24", c["orange"], 2)


@app("knights")
def _(c): at(c, 0, 0, 1, board, 4, c.lighten(c["grey"], 0.5)); at(c, 6, 4, 0.8, knight)


@app("knotes")
def _(c): sticky(c)


@app("kolf")
def _(c): golf(c)


@app("kolourpaint")
def _(c): palette(c); at(c, 14, 0, 0.75, brush, c["blue"])


@app("konqueror")
def _(c): globe(c, c["blue"], c["green"]); sec(c, folder)


@app("qupzilla")
def _(c):
    globe(c, c["violet"], c["green"])
    sec(c, lambda cv: cv.path(star_d(24, 25, 20), G(cv, cv["yellow"], 0.4, 0.05)))


@app("rekonq")
def _(c):
    globe(c, c["cyan"], c["yellow"])
    sec(c, lambda cv: cv.path("M28 2 L8 26 H22 L18 46 L40 18 H26 Z", G(cv, cv["orange"], 0.5, 0.0)))


@app("kontact")
def _(c):
    at(c, 14, 0, 0.6, calendar, c["red"], "")
    at(c, -1, 8, 0.7, envelope, None, False)
    at(c, 20, 20, 0.55, person, c["green"])


@app("mail-client")
def _(c): envelope(c)


@app("kube-mail")
def _(c): at(c, -2, -4, 0.9, envelope, None, False); sec(c, cube, c["cyan"])


@app("konversation")
def _(c):
    bubble(c, 3, 4, 34, 26, c["yellow"])
    gl(c, "hash", 9, 5, 22, c["ink"], w=2.6)
    at(c, 22, 20, 0.5, lambda cv: bubble(cv, 4, 6, 40, 30, cv["blue"], -1))


@app("kopete")
def _(c):
    at(c, -4, 10, 0.75, person, c["blue"])
    at(c, 14, 14, 0.7, person, c["green"])
    bubble(c, 22, 1, 22, 12, c["yellow"], -1)


@app("korg-todo")
def _(c):
    c.rect(8, 4, 32, 40, c.grad(c["page"]), 1.5)
    for i, done in enumerate((True, True, False, False)):
        y = 9 + i * 8.5
        c.rect(12, y, 6, 6, WHITE, 1, width=1)
        if done:
            c.line(f"M12.5 {y + 3} l2.5 2.5 l5 -6", c["green"], 2.2)
        c.line(f"M22 {y + 3} H35", c.lighten(c["ink"], 0.4), 1.6)


@app("zanshin")
def _(c): at(c, 0, 0, 0.9, target); sec(c, check_disc)


@app("kpat")
def _(c):
    at(c, -6, 4, 0.8, card, "club", "K", _rot=-20)
    at(c, 6, 0, 0.8, card, "heart", "A")
    at(c, 17, 5, 0.8, card, "spade", "Q", _rot=20)


@app("kphotoalbum")
def _(c):
    book(c, c["brown"])
    at(c, 11, 10, 0.5, photo)


@app("krdc")
def _(c):
    at(c, 8, 0, 0.8, monitor, scr_prompt)
    at(c, -2, 24, 0.5, monitor)
    tube(c, "M12 28 C12 22 16 20 20 20", c["green"], 2)
    c.path("M19 16 L25 20 L19 24 Z", c["green"])


@app("krfb")
def _(c):
    at(c, 0, 6, 0.8, monitor)
    for r in (6, 11):
        c.path(arc(36, 10, r, 180, 270), "none", c["orange"], 2.4)
        c.path(arc(36, 10, r, 0, 90), "none", c["orange"], 2.4)
    c.circle(36, 10, 2.2, c["orange"], None)


@app("krename")
def _(c): at(c, -2, -2, 0.95, tag, c["yellow"], "abc"); sec(c, pencil, c["green"])


@app("kronometer")
def _(c): stopwatch(c)


@app("kruler")
def _(c):
    def r(cv):
        cv.rect(2, 17, 44, 14, G(cv, cv["yellow"], 0.35, 0.05), 1.5)
        for i in range(1, 11):
            h = 6 if i % 5 == 0 else 3.5
            if not cv.small or i % 2 == 0:
                cv.line(f"M{2 + i * 4} 17 v{h}", "ink", 1)
    at(c, 0, 0, 1, r, _rot=-35)


def _krusader(c, root):
    window(c, 3, 5, 42, 34, title=c.grad(c.lighten(c["red"], 0.3), c["red"]) if root else None)
    c.line("M24 12 V39", "ink", 1.2)
    for x in (6, 27):
        for i in range(3):
            c.line(f"M{x} {17 + i * 6} h14", c["blue"] if i == 0 else c.lighten(c["ink"], 0.4), 1.6)
    if root:
        sec(c, padlock, c["red"])


APPS["krusader_root"] = lambda c: _krusader(c, True)
APPS["krusader_user"] = lambda c: _krusader(c, False)


@app("ksnapshot")
def _(c):
    c.line("M4 12 V4 H12 M36 4 H44 V12 M44 36 V44 H36 M12 44 H4 V36", c["red"], 2.6)
    at(c, 8, 8, 0.67, camera)


@app("kstars")
def _(c):
    for x, y, r in ((8, 8, 4), (20, 4, 2.5), (40, 26, 3)):
        c.path(star_d(x, y, r, 5, 0.45), c["yellow"], c["orange"], 0.8)

    def tel(cv):
        tube(cv, "M22 26 L13 45 M22 26 L22 45 M22 26 L31 45", cv["brown"], 1.6)
        cv.path(quad((6, 34), (38, 14), 9), G(cv, cv["blue"]))
        cv.path(quad((3, 36), (8, 33), 5), cv.grad(cv["metal"]))
        cv.path(quad((36, 15.5), (41, 12.5), 11.5), cv.grad(cv["metal"]))
    tel(c)


@app("kteatime")
def _(c):
    c.ellipse(22, 40, 18, 4, c.grad(c["page"]))
    mug(c, c["green"])


@app("ktimetracker")
def _(c):
    c.rect(18, 4, 26, 34, c.grad(c["page"]), 1.5)
    for i in range(4):
        c.line(f"M22 {11 + i * 6} H40", c.lighten(c["ink"], 0.45), 1.6)
    at(c, -2, 16, 0.62, clock_face, 24, 24, 20, c["blue"])


@app("ktip")
def _(c): bulb(c)


@app("ktnef")
def _(c):
    envelope(c, None, False)
    tube(c, "M30 6 V30 a4 4 0 0 1 -8 0 V10 a2.5 2.5 0 0 1 5 0 V27", c["metal"][1], 1.6)


@app("ktorrent")
def _(c):
    c.line("M10 10 L38 14 L24 36 Z", "ink", 1.6)
    for x, y, col in ((10, 10, c["blue"]), (38, 14, c["green"]), (24, 36, c["orange"])):
        ball(c, x, y, 6.5, col)
    at(c, 26, 22, 0.45, fat_arrow, c["green"])


@app("ktouch")
def _(c):
    keyboard(c, hl={(1, 0), (1, 1), (1, 3)} if not c.small else {(1, 0), (1, 1)})
    gl(c, "touch", 24, 22, 22, c["ink"], w=2)


@app("ktrip")
def _(c): train(c)


@app("kuiviewer")
def _(c):
    window(c, 3, 3, 38, 32, lambda cv: (cv.rect(7, 14, 14, 5, cv.lighten(cv["blue"], 0.5), 1, width=0.8),
                                        cv.rect(7, 22, 26, 3, WHITE, 1, width=0.8),
                                        cv.circle(28, 16.5, 2.5, WHITE, width=0.8)))

    def eye(cv):
        cv.path("M2 24 C12 8 36 8 46 24 C36 40 12 40 2 24 Z", cv.grad(cv["page"]))
        cv.circle(24, 24, 9, G(cv, cv["blue"]))
        cv.circle(24, 24, 4, cv["ink"], None)
    sec(c, eye)


@app("kup")
def _(c): at(c, 0, 4, 0.85, harddisk); sec(c, cycle, c["green"])


@app("kuser")
def _(c): at(c, -2, 0, 0.9, person, c["blue"]); sec(c, cog, 24, 24, 19, c["grey"])


@app("kwalletmanager")
def _(c): at(c, -2, -4, 1, wallet); at(c, 14, 22, 0.55, key)


@app("kwave")
def _(c):
    window(c, 3, 6, 42, 34)
    if c.small:
        c.line("M7 26 L11 18 L15 32 L19 15 L23 34 L27 19 L31 29 L35 22 L41 26", c["blue"], 1.8)
    else:
        c.line("M7 26 L9 21 L11 31 L13 17 L15 34 L17 20 L19 30 L21 14 L23 36 L25 19 L27 30 L29 22 "
               "L31 28 L33 23 L35 27 L37 25 L41 26", c["blue"], 1.3)


@app("kwin")
def _(c):
    window(c, 3, 4, 30, 24, title=c.grad(c["page"][1], c["page_fold"]))
    window(c, 15, 18, 30, 24)


@app("wayland")
def _(c):
    window(c, 6, 3, 36, 26)
    for y in (34, 41):
        c.path(f"M3 {y} c5 -4 9 -4 14 0 c5 4 9 4 14 0 c5 -4 9 -4 14 0", "none", c["blue"], 2.6)


@app("xorg")
def _(c): monitor(c, scr_x)


@app("kxstitch")
def _(c):
    hoop(c)
    c.line("M30 38 L44 6", c["metal"][1], 1.8)


@app("symboleditor")
def _(c):
    c.rect(4, 4, 34, 34, c.grad(c["page"]), 1)
    c.line("M12.5 4 V38 M21 4 V38 M29.5 4 V38 M4 12.5 H38 M4 21 H38 M4 29.5 H38", c.lighten(c["ink"], 0.55), 0.8)
    c.path("M8.25 6 L11 11 H5.5 Z", c["red"], None)
    c.circle(16.75, 8.25, 2.6, c["blue"], None)
    c.rect(23, 14.5, 4.5, 4.5, c["green"], 0, None)
    c.path(star_d(8.25, 25.25, 3, 5, 0.45), c["violet"], None)
    sec(c, pencil, c["red"])


@app("latte-dock")
def _(c):
    dock(c, c["blue"])
    for i in range(4):
        c.circle(10 + i * 9.3, 41.5, 1.2, c["cyan"], None)


@app("plank")
def _(c): dock(c, c.lighten(c["brown"], 0.2), (c["blue"], c["orange"], c["violet"]))


@app("lokalize")
def _(c):
    at(c, -4, -2, 0.9, page_lines)
    at(c, 20, 20, 0.55, lambda cv: (bubble(cv, 2, 4, 42, 32, cv["yellow"], -1), kanji_wen(cv, cv["red"])))


@app("massif-visualizer")
def _(c):
    c.rect(4, 4, 40, 40, c.grad(c["page"]), 2)
    c.path("M8 40 L8 32 L16 26 L24 28 L32 16 L40 12 V40 Z", G(c, c["blue"], 0.4, 0.0), width=0.9)
    c.path("M8 40 L8 36 L16 32 L24 34 L32 26 L40 24 V40 Z", G(c, c["orange"], 0.4, 0.0), width=0.9)
    c.path("M8 40 L8 38 L16 37 L24 38 L32 34 L40 33 V40 Z", G(c, c["red"], 0.4, 0.0), width=0.9)


@app("minuet")
def _(c): at(c, 0, 6, 1, piano); at(c, 16, -4, 0.6, music_note, c["green"])


@app("muon")
def _(c):
    at(c, 0, 18, 0.6, box)
    at(c, 19, 18, 0.6, box, c.lighten(c["yellow"], 0.2))
    at(c, 10, 0, 0.6, box, c.lighten(c["orange"], 0.2))


@app("muondiscover")
def _(c): at(c, -2, -2, 0.9, bag, c["blue"]); sec(c, box)


@app("system-software-install")
def _(c): at(c, 0, 8, 0.85, box); at(c, 22, 0, 0.55, fat_arrow, c["green"])


@app("system-software-update")
def _(c): at(c, 0, 8, 0.85, box); sec(c, cycle, c["blue"])


@app("nota")
def _(c):
    def s(cv):
        cv.rect(16, 10, 16, 26, WHITE, 0.5, None)
        cv.line("M18 14 H30 M18 18 H30 M18 22 H26 M18 26 H30", cv.lighten(cv["ink"], 0.4), 1.4)
    phone(c, s)
    sec(c, pen, c["orange"])


@app("ntfs-config")
def _(c): at(c, 0, 4, 0.85, harddisk); sec(c, cog, 24, 24, 19, c["blue"])


@app("office-address-book")
def _(c):
    book(c, c["green"], False)
    for i, col in enumerate((c["red"], c["yellow"], c["blue"])):
        c.rect(36, 8 + i * 9, 4, 7, col, 1, width=0.8)
    at(c, 12, 10, 0.45, person, c["blue"])


@app("okteta")
def _(c):
    page(c, "HEX", c["cyan"])
    if not c.small:
        c.text(12, 18, "0F A3", 7, c["ink"], anchor="start")
        c.text(12, 26, "7B C9", 7, c["ink"], anchor="start")
    else:
        c.line("M12 16 h4 M19 16 h4 M12 23 h4 M19 23 h4", c["ink"], 1.6)


@app("okular")
def _(c): at(c, -2, -4, 0.9, page_lines); at(c, 10, 20, 0.6, glasses)


@app("org.kde.Ikona")
def _(c):
    at(c, 0, 4, 0.25, frame)
    at(c, 9, 14, 0.42, frame)
    at(c, 20, 10, 0.6, frame)


@app("org.kde.kongress")
def _(c):
    tube(c, "M12 2 L22 18 M36 2 L26 18", c["blue"], 2.4)
    c.rect(10, 16, 28, 28, c.grad(c["page"]), 2)
    c.rect(10, 16, 28, 7, c["blue"], 2)
    at(c, 14, 22, 0.42, person, c["orange"])


@app("org.kde.kontrast")
def _(c):
    c.circle(24, 24, 19, WHITE)
    c.path("M24 5 A19 19 0 0 1 24 43 Z", c["ink"], None)
    c.text(17, 30, "A", 16, c["ink"])
    c.text(31, 30, "a", 16, WHITE)
    c.circle(24, 24, 19, "none")


@app("org.kde.neochat")
def _(c):
    bubble(c, 4, 5, 40, 30, c["green"])
    c.line("M14 12 h-4 v16 h4 M34 12 h4 v16 h-4", WHITE, 2.6)
    for x in (18, 24, 30):
        c.circle(x, 20, 2, WHITE, None)


@app("parley")
def _(c):
    at(c, -2, -2, 0.75, lambda cv: (cv.rect(4, 8, 40, 30, cv.grad(cv["page"]), 2),
                                    cv.text(24, 30, "?", 20, cv["blue"])), _rot=-12)
    at(c, 12, 12, 0.75, lambda cv: (cv.rect(4, 8, 40, 30, G(cv, cv["yellow"], 0.5, 0.05), 2),
                                    cv.text(24, 30, "Ab", 18, cv["ink"])), _rot=8)


@app("partitionmanager")
def _(c):
    c.circle(24, 24, 19, c.grad(c["metal"]))
    for a0, a1, col in ((-90, 60, c["blue"]), (60, 170, c["green"]), (170, 230, c["orange"])):
        c.path(sector(24, 24, 16, a0, a1), G(c, col, 0.35, 0.05), width=0.9)
    c.circle(24, 24, 4, c.grad(c["page"]))
    c.circle(24, 24, 19, "none")


@app("phonon-gstreamer")
def _(c): speaker(c, c["orange"]); sec(c, cog, 24, 24, 19, c["green"])


@app("photolayoutseditor")
def _(c):
    at(c, -3, -2, 0.55, photo, _rot=-8)
    at(c, 19, -1, 0.55, photo, c["blue"], _rot=6)
    at(c, 6, 18, 0.62, photo, c["violet"], _rot=-3)


@app("plan")
def _(c): calendar(c)


@app("planetkde")
def _(c):
    tube(c, "M3 26 A21 7 0 0 1 45 26", c["orange"], 2.2)
    c.circle(24, 24, 14, G(c, c["blue"], 0.45, 0.1))
    blob(c, 19, 17, 4, 2.5, WHITE, 0.4)
    tube(c, "M45 26 A21 7 0 0 1 3 26", c["orange"], 2.2)


@app("planwork")
def _(c): gantt(c)


@app("plasma-mobile-phone")
def _(c): handset(c, c["green"])


@app("plasma-nano")
def _(c):
    c.path("M18 36 L14 44 H34 L30 36 Z", c.grad(c["case"]))
    c.rect(8, 10, 32, 28, c.grad(c.lighten(c["ink"], 0.35), c["ink"]), 4)
    c.rect(11, 13, 26, 22, c.grad(c["screen"]), 2)
    c.text(24, 28.5, "12:00", 8, WHITE)
    if c.small:
        c.line("M16 24 H32", WHITE, 2)


@app("plasmavault")
def _(c): safe(c)


@app("rocs")
def _(c): nodes(c)


@app("sharedlib")
def _(c): at(c, -2, -2, 0.8, cog, 24, 24, 20, c["violet"]); sec(c, chain)


@app("sheets")
def _(c):
    c.rect(4, 6, 40, 36, c.grad(c["page"]), 1.5)
    c.rect(4, 6, 40, 7, G(c, c["green"]), 1.5)
    c.rect(4, 6, 8, 36, c.lighten(c["green"], 0.6), 1.5)
    c.line("M4 20 H44 M4 27 H44 M4 34 H44 M12 6 V42 M23 6 V42 M34 6 V42", c.darken(c["green"], 0.1), 0.9)
    c.rect(23, 20, 11, 7, "none", 0.5, c["ink"], 1.8)


@app("showfoto")
def _(c): at(c, -2, -2, 0.95, photo); sec(c, brush, c["violet"])


@app("skanlite")
def _(c): scanner(c)


@app("skanpage")
def _(c):
    at(c, -2, 6, 0.8, scanner)

    def pg(cv):
        cv.group("translate(-5 -4)", lambda x: page(x))
        page(cv, lines=True)
    sec(c, pg)


@app("skladnik")
def _(c):
    c.rect(2, 40, 44, 4, c.grad(c["metal"]), 0)
    at(c, 18, 12, 0.6, crate)
    c.circle(10, 16, 4, G(c, skin(c), 0.3, 0.05))
    c.path("M6 22 H14 L18 28 H20 V31 H16 L14 28 V40 H11 V32 H9 V40 H6 Z", G(c, c["blue"]))


@app("stage")
def _(c):
    def ch(cv):
        cv.rect(10, 22, 6, 8, cv["red"], 0, width=0.8)
        cv.rect(19, 15, 6, 15, cv["green"], 0, width=0.8)
        cv.rect(28, 18, 6, 12, cv["blue"], 0, width=0.8)
        cv.line("M37 12 l2 4", "ink", 1)
    screen_stand(c, ch)


@app("step")
def _(c): pendulum(c)


@app("subtitlecomposer")
def _(c):
    c.rect(3, 6, 42, 36, dark(c), 2)
    c.rect(8, 10, 32, 20, G(c, c["cyan"], 0.4, 0.0), 1)
    c.path("M8 30 L18 18 L26 26 L30 22 L40 30 Z", G(c, c["green"]), None)
    c.rect(10, 33, 28, 3, c["yellow"], 1, None)
    c.rect(14, 37.5, 20, 2.5, c["yellow"], 1, None)
    if not c.small:
        for y in (8, 40):
            for x in range(6, 44, 6):
                c.rect(x, y - 1, 2.5, 2, WHITE, 0, None)


@app("sweeper")
def _(c):
    tube(c, "M42 4 L22 26", c["brown"], 3)
    c.path("M16 22 L28 32 L18 44 C10 42 6 38 4 32 Z", G(c, c.lighten(c["orange"], 0.3), 0.3, 0.05))
    c.line("M13 32 L8 37 M17 35 L12 41 M10 29 L6 33", c.darken(c["orange"], 0.2), 1)
    c.path(quad((16, 22), (28, 32), 4), G(c, c["red"]))


@app("system-file-manager")
def _(c): folder(c); sec(c, magnifier)


@app("system-help")
def _(c): lifebuoy(c)


@app("system-run")
def _(c): at(c, -2, -2, 0.85, cog, 24, 24, 20, c["blue"]); sec(c, play_disc)


@app("systemsettings")
def _(c):
    cog(c, 15, 15, 12, c["red"])
    cog(c, 33, 18, 10, c["blue"])
    cog(c, 18, 34, 10, c["green"])
    wrench(c)


@app("telepathy-kde")
def _(c):
    bubble(c, 3, 4, 34, 26, c.lighten(c["blue"], 0.3))
    if not c.small:
        c.line("M9 12 H31 M9 18 H25", c.darken(c["blue"], 0.3), 1.6)
    sec(c, nodes)


@app("umbrello")
def _(c): uml(c)


@app("usb-creator-kde")
def _(c): at(c, -2, -2, 0.9, usbstick); sec(c, cd)


@app("utilities-energy-monitor")
def _(c):
    at(c, -2, -4, 0.95, battery)
    sec(c, lambda cv: (cv.circle(24, 24, 20, G(cv, cv["yellow"], 0.4, 0.05)),
                       cv.path("M27 6 L12 27 H22 L19 42 L35 20 H25 Z", cv["ink"], None)))


@app("utilities-log-viewer")
def _(c): scroll(c)


@app("utilities-system-monitor")
def _(c): monitor(c, scr_graph)


@app("utilities-terminal")
def _(c): monitor(c, scr_prompt)


@app("yakuake")
def _(c):
    c.rect(2, 3, 44, 4, c.grad(c["metal"]), 1)
    c.rect(6, 7, 36, 24, c.grad(c.lighten(c["ink"], 0.3), c["ink"]), 1.5)
    c.line("M10 12 l4 3.5 l-4 3.5", c["led"], 2.2)
    c.line("M16 20 h8", c["led"], 2.2)
    c.path("M17 34 h14 l-7 9 z", G(c, c["green"]))


@app("vvave")
def _(c): cassette(c)


@app("words")
def _(c):
    page_lines(c)
    c.rect(25, 27, 16, 16, G(c, c["blue"]), 3)
    c.text(33, 40.5, "¶", 14, WHITE)


@app("plasma-media-center")
def _(c): tv(c, lambda cv: at(cv, 13, 17, 0.35, music_note, WHITE)); sec(c, remote)


APPS["blogilo"] = lambda c: (at(c, 0, 0, 0.85, page_lines), sec(c, globe))
APPS["kblogger"] = lambda c: (at(c, -2, -2, 0.9, notebook, c["orange"]), sec(c, feed_disc))


def draw(name, c):
    fn = APPS.get(name)
    if fn is None:
        return None
    try:
        fn(c)
    except Exception as e:  # noqa: BLE001
        import sys
        print(f"  fam_apps: {name}: {type(e).__name__}: {e}", file=sys.stderr)
        return None
    return True
