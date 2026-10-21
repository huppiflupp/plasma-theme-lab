#!/usr/bin/env python3
"""Warp Legacy Neon icon set (DESIGN.md §9a).

Own drawings in the manner of the user's concept reference/neon-2026.png:
glossy blue/cyan/violet pictograms with a light rim (cyan top left, violet
bottom right, the OS/2 light rule at night) and an outer glow, a few orange
accents. Nothing is traced from the concept or taken from IBM (§1).

Every icon is drawn as SVG on a 256 grid. Two outputs per icon:

- 16..256 px: PNG in every size Dolphin offers (16, 22, 24, 32, 48, 64,
  96, 128, 256; up to 32 with @2 HiDPI twins), rendered with cairosvg, glow
  added in PIL. Up to SMALL a simplified drawing with heavier edges.
  KDE programs load icons through KIconLoader, which here never takes the
  scalable/ directory: Dolphin showed the 32 px PNG blown up to 64 px
  (measured in the VM, 20.10.2026), as NT Legacy found in 6fc33663. Fixed
  bitmaps at every size do not depend on any weighting.
- scalable/ (33..512 px): SVG for QtSvg, for programs using Qt's own
  loader. QtSvg draws no filters and no
  clip paths, so the drawings avoid clipping and the glow travels as a small
  embedded PNG (<image>, SVG Tiny 1.2) under the vector body. A blur has no
  fine detail, so 128 px of it upscale to 512 without visible loss; stacked
  strokes were tried as well and band visibly from 2x on.

Status and action icons are plain glowing tubes (cyan, orange/red accents),
the rest are glossy bodies.

    build_icons(out_dir)          -> out_dir/WarpLegacyNeon/{index.theme, ...}
    python3 icons_neon.py         -> build-icons-preview/ (contact sheets)
"""
import base64
import io
import math
import multiprocessing
import re
import os
import pathlib
import shutil
import sys
import time

import cairosvg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FIXED = (16, 22, 24, 32)        # small PNG sizes; each also as @2
LARGE = (48, 64, 96, 128, 256)  # large PNG sizes, the rest of Dolphin's zoom steps
SMALL = 24                      # sizes <= SMALL get the simplified drawing
SVG_MIN, SVG_MAX = 33, 512      # the scalable SVGs take over above FIXED
GLOW_RES = 128                  # pixel size of the glow embedded in each SVG
GLOW = (0x2a, 0x5c, 0xff)       # wide outer glow (§9a "glow around frames")
HALO = (0x48, 0xcf, 0xfe)       # tight cyan halo just outside the rim
BG = (0x0c, 0x14, 0x38)         # preview background (window body)

CONTEXTS = {"places": "Places", "devices": "Devices", "apps": "Applications",
            "mimetypes": "MimeTypes", "actions": "Actions", "status": "Status"}


# --------------------------------------------------------------------------
# SVG plumbing

def _grad(gid, stops, x1=0, y1=0, x2=1, y2=1, user=False):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>'
                for o, c, a in ((st + (1,))[:3] for st in stops))
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    return (f'<linearGradient id="{gid}"{u} x1="{x1}" y1="{y1}" x2="{x2}" '
            f'y2="{y2}">{s}</linearGradient>')


# Every gradient runs top left -> bottom right in the shape's own box, so the
# light falls from the top left on every part without per-shape tuning.
_GRADS = [
    _grad("body", [(0, "#5cc4ff"), (0.4, "#1f6ae8"), (1, "#1a1f8e")]),
    _grad("cyan", [(0, "#d8faff"), (0.5, "#48cffe"), (1, "#1a6fe0")]),
    _grad("violet", [(0, "#c9adff"), (0.55, "#7a4dff"), (1, "#3a1f9e")]),
    _grad("magenta", [(0, "#ffc4ff"), (0.5, "#e04dff"), (1, "#7a2ad0")]),
    _grad("orange", [(0, "#ffe7a6"), (0.5, "#ff9a3c"), (1, "#d4501c")]),
    _grad("yellow", [(0, "#fff0a0"), (0.55, "#ffb43c"), (1, "#d8701a")]),
    _grad("green", [(0, "#b0ffd0"), (0.5, "#2fd08a"), (1, "#127a6a")]),
    _grad("red", [(0, "#ffc0a0"), (0.45, "#ff5a3c"), (1, "#a01a20")]),
    _grad("metal", [(0, "#ffffff"), (0.5, "#a9bbe6"), (1, "#5a68a8")]),
    _grad("paper", [(0, "#ffffff"), (1, "#bcd4ff")]),
    _grad("glass", [(0, "#3a78f0"), (0.55, "#13309a"), (1, "#0a1650")]),
    _grad("dark", [(0, "#24399a"), (1, "#0a1240")]),
    _grad("page", [(0, "#3f86f6"), (0.6, "#1d48c8"), (1, "#18258a")]),
    _grad("screen", [(0, "#7fd8ff"), (0.35, "#2a8cf4"), (1, "#1a2fb0")]),
    _grad("disc", [(0, "#d0f6ff"), (0.25, "#48cffe"), (0.45, "#7a4dff"),
                   (0.6, "#ffb46a"), (0.72, "#48cffe"), (1, "#2236b8")]),
    _grad("rim", [(0, "#f0fdff"), (0.3, "#5ad8ff"), (0.7, "#48a8ff"), (1, "#9a6dff")]),
    _grad("rimm", [(0, "#ffd0ff"), (0.4, "#e04dff"), (1, "#7a4dff")]),
    # 0.25, not 0.6: a strong gloss washed the bodies out to a milky blue
    # and they read soft beside the concept's saturated set (Dolphin, VM).
    _grad("gloss", [(0, "#ffffff", 0.25), (0.5, "#ffffff", 0)], 0, 0, 0, 1),
    # tubes: in user space, as a straight line has an empty bounding box
    _grad("tube", [(0, "#b4f8ff"), (0.45, "#48cffe"), (1, "#8f86ff")],
          32, 32, 224, 224, user=True),
]
GRADS = {re.search(r'id="([^"]+)"', x).group(1): x for x in _GRADS}

INK = "#0b1a5c"   # dark line inside light emblems, keeps them apart at 16 px


def _a(attrs):
    return " ".join(f'{k.rstrip("_").replace("_", "-")}="{v}"'
                    for k, v in attrs.items() if v is not None)


def rect(x, y, w, h, r=0, **a):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" {_a(a)}/>'


def circle(cx, cy, r, **a):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" {_a(a)}/>'


def ellipse(cx, cy, rx, ry, **a):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {_a(a)}/>'


def path(d, **a):
    return f'<path d="{d}" {_a(a)}/>'


def line(x1, y1, x2, y2, stroke, w, **a):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{w}" stroke-linecap="round" {_a(a)}/>')


def g(content, transform=None, **a):
    t = f' transform="{transform}"' if transform else ""
    return f"<g{t} {_a(a)}>{content}</g>"


def poly(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


class D:
    """Detail level for one target size."""

    def __init__(self, size):
        self.size = size
        self.small = size <= SMALL
        # Edges aim at ~1 px at the small sizes, where a 5-unit rim would
        # vanish into the glow.
        self.k = max(1.0, 256 / size / 5) if self.small else 1.0
        # tube width for the line icons: ~1.4 px at 16, ~2.6 px at 48
        self.t = {16: 22, 22: 19, 24: 18, 32: 16}.get(size, 14)

    def w(self, x):
        """Rim and hairline widths: ~1 px at the small sizes."""
        return round(x * self.k, 2)

    def b(self, x):
        """Glyph strokes that are already bold: heavier, but capped."""
        return x * 1.4 if self.small else x


def solid(mk, fill, d, rw=6, gloss=True, rim="rim"):
    """A filled shape with the two-colour rim and an optional top sheen.

    mk is a callable building the element from extra attributes, so the same
    outline serves for body, sheen and rim.
    """
    out = mk(fill=f"url(#{fill})" if not fill.startswith("#") else fill)
    if gloss:
        out += mk(fill="url(#gloss)")
    if rw:
        out += mk(fill="none", stroke=f"url(#{rim})", stroke_width=d.w(rw),
                  stroke_linejoin="round")
    return out


def emblem(fn, d, cx, cy, s):
    """Place an emblem drawn on a 0..100 box centred at (cx, cy), s wide."""
    body = fn(d)
    if d.small:
        # six pixels of emblem only read as a flat bright shape
        for grad in ("url(#cyan)", "url(#paper)"):
            body = body.replace(grad, "#ffffff")
    return g(body, f"translate({cx - s / 2} {cy - s / 2}) scale({s / 100})")


# --------------------------------------------------------------------------
# Emblems (0..100 box): light shapes with a dark line, drawn on blue fronts

def _es(d, w=4):
    # at the small sizes a dark line only muddies the emblem; brightness
    # against the darker small-size front carries it instead
    if d.small:
        return dict(stroke="none")
    return dict(stroke=INK, stroke_width=w, stroke_linejoin="round")


def em_house(d):
    return (path("M8,52 L50,12 L92,52 Z", fill="url(#orange)", **_es(d)) +
            rect(22, 48, 56, 44, 3, fill="url(#paper)", **_es(d)) +
            ("" if d.small else rect(42, 64, 16, 28, 2, fill="url(#body)")))


def em_monitor(d):
    return (rect(8, 12, 84, 58, 6, fill="url(#paper)", **_es(d)) +
            rect(18, 22, 64, 38, 2, fill="url(#screen)") +
            path("M38,70 H62 L68,88 H32 Z", fill="url(#paper)", **_es(d)))


def em_doc(d):
    lines = "".join(line(28, y, 72, y, "#3a78f0", 6)
                    for y in ((38, 52, 66, 80) if not d.small else (40, 60)))
    return path("M18,4 H64 L82,22 V96 H18 Z", fill="url(#paper)",
                **_es(d)) + lines


def em_down(d):
    return (path("M38,6 H62 V46 H84 L50,86 L16,46 H38 Z", fill="url(#cyan)",
                 **_es(d)) +
            rect(14, 88, 72, 10, 4, fill="url(#orange)", **_es(d, 3)))


def em_note(d):
    return (path("M34,78 V22 L84,10 V66", fill="none", stroke=INK,
                 stroke_width=18, stroke_linejoin="round") +
            path("M34,78 V22 L84,10 V66", fill="none", stroke="url(#cyan)",
                 stroke_width=9, stroke_linejoin="round") +
            ellipse(24, 80, 16, 12, fill="url(#cyan)", **_es(d)) +
            ellipse(74, 68, 16, 12, fill="url(#cyan)", **_es(d)))


def em_picture(d):
    return (rect(6, 12, 88, 76, 6, fill="url(#screen)", **_es(d)) +
            circle(70, 34, 10, fill="url(#orange)") +
            path("M10,84 L36,46 L56,70 L68,58 L90,84 Z", fill="url(#green)"))


def em_play(d):
    return (rect(6, 12, 88, 76, 10, fill="url(#violet)", **_es(d)) +
            path("M38,30 L70,50 L38,70 Z", fill="url(#paper)", **_es(d, 3)))


def em_template(d):
    return (path("M18,4 H64 L82,22 V96 H18 Z", fill="url(#paper)",
                 fill_opacity=0.35, stroke="#ffffff", stroke_width=6,
                 stroke_dasharray="10 7", stroke_linejoin="round") +
            rect(30, 40, 40, 30, 3, fill="url(#orange)", **_es(d, 3)))


def em_share(d):
    pts = ((26, 50), (74, 22), (74, 78))
    out = "".join(line(26, 50, x, y, INK, 14) + line(26, 50, x, y, "#e8f0ff", 7)
                  for x, y in pts[1:])
    return out + "".join(circle(x, y, 16, fill="url(#orange)" if i == 0
                                else "url(#cyan)", **_es(d))
                         for i, (x, y) in enumerate(pts))


def em_globe(d):
    edge = "" if d.small else circle(50, 50, 42, fill="none", stroke=INK,
                                      stroke_width=4)
    return globe(d, 50, 50, 42, lines=not d.small, rw=0) + edge


def em_grid(d):
    return "".join(rect(8 + 32 * i, 8 + 32 * j, 26, 26, 5,
                        fill="url(#orange)" if (i, j) == (2, 0) else "url(#cyan)",
                        **_es(d, 3))
                   for i in range(3) for j in range(3))


# --------------------------------------------------------------------------
# Building blocks on the 256 grid; drawings stay inside ~26..230 so the
# glow has room to fade out before the icon's edge.

FOLDER_BACK = ("M30,64 Q30,54 40,54 H94 Q101,54 105,60 L113,72 H216 "
               "Q226,72 226,82 V196 Q226,206 216,206 H40 Q30,206 30,196 Z")
FOLDER_FRONT = ("M30,112 Q30,102 40,102 H216 Q226,102 226,112 V196 "
                "Q226,206 216,206 H40 Q30,206 30,196 Z")
FOLDER_OPEN = "M26,128 Q26,120 34,120 H222 Q230,120 228,128 L218,198 Q216,206 208,206 H48 Q40,206 38,198 Z"


def folder(d, em=None, open_=False):
    out = path(FOLDER_BACK, fill="url(#yellow)", stroke="#b8561a",
               stroke_width=d.w(3), stroke_linejoin="round")
    if not d.small:
        out += rect(46, 80, 164, 56, 4, fill="url(#paper)",
                    transform="rotate(-3 128 108)" if open_ else None)
        if open_:
            out += rect(54, 70, 150, 60, 4, fill="url(#paper)",
                        transform="rotate(4 128 100)", opacity=0.85)
    front = FOLDER_OPEN if open_ else FOLDER_FRONT
    # small sizes: a darker front so the light emblem keeps its contrast
    fill = "page" if (d.small and em) else "body"
    out += solid(lambda **a: path(front, **a), fill, d, rw=5)
    if em:
        s = 96 if d.small else 86
        out += emblem(em, d, 128, 162 if open_ else 156, s)
    return out


def monitor(d, screen="", x=34, y=40, w=188, h=132):
    """Bezel, glossy screen with optional content, neck and foot."""
    sx, sy, sw, sh = x + 13, y + 13, w - 26, h - 26
    cx = x + w / 2
    out = path(f"M{cx - 16},{y + h - 2} H{cx + 16} L{cx + 24},{y + h + 26} "
               f"H{cx - 24} Z", fill="url(#metal)")
    out += solid(lambda **a: rect(cx - 52, y + h + 22, 104, 16, 8, **a),
                 "body", d, rw=3, gloss=False)
    out += solid(lambda **a: rect(x, y, w, h, 12, **a), "dark", d, gloss=False)
    # screen content must stay inside the screen: QtSvg ignores clipping
    out += (rect(sx, sy, sw, sh, 0, fill="url(#screen)") + screen +
            path(f"M{sx},{sy} H{sx + sw * 0.62} L{sx + sw * 0.3},{sy + sh} "
                 f"H{sx} Z", fill="#ffffff", opacity=0.16))
    return out


def document(d, content="", fold="violet", dashed=False):
    page = "M62,26 H160 L198,64 V222 Q198,230 190,230 H70 Q62,230 62,222 V34 Q62,26 70,26 Z"
    if dashed:
        out = path(page, fill="url(#page)", opacity=0.55)
        out += path(page, fill="none", stroke="url(#rim)", stroke_width=d.w(6),
                    stroke_dasharray="18 12", stroke_linejoin="round")
    else:
        out = solid(lambda **a: path(page, **a), "page", d)
    out += path("M160,26 V56 Q160,64 168,64 H198 Z", fill=f"url(#{fold})",
                stroke="url(#rim)", stroke_width=d.w(3), stroke_linejoin="round")
    return out + content


def doc_lines(d, x0=84, x1=176, ys=None, color="#bfefff"):
    ys = ys or ((96, 136, 176) if d.small else (88, 112, 136, 160, 184, 208))
    return "".join(line(x0, y, x1 - (24 if i % 3 == 2 else 0), y, color,
                        d.w(9) if d.small else 9)
                   for i, y in enumerate(ys))


def gear_d(cx, cy, R, r, n, hole):
    step = 2 * math.pi / n
    pts = []
    for i in range(n):
        a = i * step - math.pi / 2
        for da, rad in ((-0.28, r), (-0.16, R), (0.16, R), (0.28, r)):
            pts.append((cx + rad * math.cos(a + da * step),
                        cy + rad * math.sin(a + da * step)))
    return (poly(pts) + f" M{cx + hole},{cy} A{hole},{hole} 0 1 0 {cx - hole},{cy}"
            f" A{hole},{hole} 0 1 0 {cx + hole},{cy} Z")


def gear(d, cx, cy, R, fill="body", n=8):
    gd = gear_d(cx, cy, R, R * 0.78, n, R * 0.32)
    out = solid(lambda **a: path(gd, fill_rule="evenodd", **a), fill, d)
    if not d.small:
        out += circle(cx, cy, R * 0.5, fill="none", stroke="#bff2ff",
                      stroke_width=R * 0.08, opacity=0.8)
    return out


def globe(d, cx, cy, R, lines=True, rw=5):
    out = solid(lambda **a: circle(cx, cy, R, **a), "body", d, rw=rw,
                gloss=False)
    # everything stays inside the disc by construction (QtSvg cannot clip)
    grid = ""
    if lines:
        c, sw = "#bff2ff", max(R * 0.05, d.w(3))
        grid += ellipse(cx, cy, R * 0.42, R, fill="none", stroke=c, stroke_width=sw)
        grid += ellipse(cx, cy, R * 0.82, R, fill="none", stroke=c, stroke_width=sw)
        grid += line(cx, cy - R, cx, cy + R, c, sw)
        for f in (-0.5, 0, 0.5):
            h = R * math.sqrt(1 - f * f) - sw / 2
            grid += line(cx - h, cy + f * R, cx + h, cy + f * R, c, sw)
        grid = g(grid, opacity=0.45)
    # land masses as soft blobs: reads as "earth" without any real map
    land = (ellipse(cx - R * 0.32, cy - R * 0.18, R * 0.3, R * 0.4,
                    fill="url(#green)", opacity=0.75,
                    transform=f"rotate(-20 {cx} {cy})") +
            ellipse(cx + R * 0.4, cy + R * 0.32, R * 0.28, R * 0.2,
                    fill="url(#green)", opacity=0.7))
    sheen = ellipse(cx - R * 0.3, cy - R * 0.42, R * 0.42, R * 0.24,
                    fill="#ffffff", opacity=0.35,
                    transform=f"rotate(-30 {cx - R * 0.3} {cy - R * 0.42})")
    return out + land + grid + sheen


def orbit(d, cx, cy, rx, ry, rot, front):
    """Half of a tilted ring: back half before the globe, front half after."""
    sweep = 1 if front else 0
    dd = f"M{cx - rx},{cy} A{rx},{ry} 0 0 {1 - sweep} {cx + rx},{cy}"
    return path(dd, fill="none", stroke="url(#violet)" if not front else "url(#cyan)",
                stroke_width=14 if d.small else 9, stroke_linecap="round",
                transform=f"rotate({rot} {cx} {cy})")


def box3d(d, x, y, w, h, dx, dy, front="body"):
    """Oblique box: lit top, body front, violet right side (light top left)."""
    top = poly([(x, y), (x + w, y), (x + w + dx, y - dy), (x + dx, y - dy)])
    side = poly([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy),
                 (x + w, y + h)])
    out = solid(lambda **a: path(side, **a), "violet", d, gloss=False)
    out += solid(lambda **a: path(top, **a), "cyan", d, gloss=False)
    out += solid(lambda **a: rect(x, y, w, h, 4, **a), front, d)
    return out


def tower(d, x=150, y=46, w=74, h=164):
    out = solid(lambda **a: rect(x, y, w, h, 10, **a), "body", d)
    if not d.small:
        for i in range(2):
            out += rect(x + 12, y + 20 + i * 22, w - 24, 12, 3, fill="url(#dark)",
                        stroke="#9fe8ff", stroke_width=2)
    out += circle(x + w / 2, y + h - 34, d.w(9), fill="url(#cyan)")
    out += rect(x + 14, y + h - 14, 16, d.w(4), 2, fill="#ff9a3c")
    return out


# --------------------------------------------------------------------------
# Icons. Each returns the SVG body for its detail level.

def i_folder(d): return folder(d)
def i_folder_open(d): return folder(d, open_=True)
def i_user_home(d): return folder(d, em_house)
def i_user_desktop(d): return folder(d, em_monitor)
def i_folder_documents(d): return folder(d, em_doc)
def i_folder_download(d): return folder(d, em_down)
def i_folder_music(d): return folder(d, em_note)
def i_folder_pictures(d): return folder(d, em_picture)
def i_folder_videos(d): return folder(d, em_play)
def i_folder_templates(d): return folder(d, em_template)
def i_folder_publicshare(d): return folder(d, em_share)
def i_folder_remote(d): return folder(d, em_globe)


def shredder(d, full):
    """OS/2's shredder instead of a waste basket."""
    out = ""
    if full:
        sheet = "M86,30 H170 V96 H86 Z"
        out += path(sheet, fill="url(#paper)", stroke=INK, stroke_width=d.w(2),
                    transform="rotate(-6 128 70)")
        if not d.small:
            out += g("".join(line(98, y, 156, y, "#3a78f0", 5)
                             for y in (46, 60, 74)), "rotate(-6 128 70)")
    binp = "M50,134 H206 L192,220 Q191,228 182,228 H74 Q65,228 64,220 Z"
    out += solid(lambda **a: path(binp, **a), "glass", d, gloss=False)
    if full:
        strips = ""
        n = 7 if d.small else 13
        for i in range(n):
            x = 76 + i * (104 / (n - 1))
            top = 150 + (i * 37 % 23)
            col = "url(#paper)" if i % 3 else "url(#orange)"
            strips += rect(x - 4, top, 8 if not d.small else 12, 218 - top,
                           3, fill=col, transform=f"rotate({(i % 3 - 1) * 4} {x} 200)")
        out += strips       # strips stay inside the bin: QtSvg cannot clip
    elif not d.small:
        out += "".join(line(x, 148, x - (x - 128) * 0.1, 214, "#48cffe", 3,
                            opacity=0.45) for x in (88, 128, 168))
    out += solid(lambda **a: rect(36, 80, 184, 58, 14, **a), "body", d)
    out += rect(62, 98, 132, d.b(10), 4, fill="#060b24")
    out += rect(66, 104 + d.w(1), 124, d.w(3), 1.5, fill="#ff9a3c")
    if not d.small:
        out += circle(204, 98, 6, fill="url(#cyan)")
    return out


def i_user_trash(d): return shredder(d, False)
def i_user_trash_full(d): return shredder(d, True)


def i_network_workgroup(d):
    out = globe(d, 128, 128, 96, lines=not d.small)
    nodes = ((84, 92), (170, 80), (176, 164), (100, 176), (128, 128))
    edges = ((0, 4), (1, 4), (2, 4), (3, 4), (0, 1), (2, 3))
    if d.small:
        nodes = ((78, 84), (178, 84), (128, 176), (128, 120))
        edges = ((0, 3), (1, 3), (2, 3))
    w = d.w(6)
    for a, b in edges:
        out += line(*nodes[a], *nodes[b], "#e8f0ff", w, opacity=0.9)
    for i, (x, y) in enumerate(nodes):
        out += circle(x, y, d.b(10) if d.small else 13,
                      fill="url(#orange)" if i == 4 else "url(#cyan)",
                      stroke=INK, stroke_width=d.w(3))
    return out


def i_start_here(d):
    out = solid(lambda **a: circle(128, 128, 92, **a), "violet", d, gloss=False)
    out += circle(128, 128, 92, fill="url(#gloss)")
    # abstract four-point spark crossed by an orbit: a "start", no logo
    out += orbit(d, 128, 128, 104, 34, -28, False)
    s = "M128,48 Q138,118 208,128 Q138,138 128,208 Q118,138 48,128 Q118,118 128,48 Z"
    out += path(s, fill="url(#paper)", stroke="url(#cyan)", stroke_width=d.w(4))
    out += circle(128, 128, 14, fill="url(#orange)")
    out += orbit(d, 128, 128, 104, 34, -28, True)
    return out


def i_computer(d):
    out = tower(d)
    out += monitor(d, x=30, y=60, w=146, h=106)
    return out


def i_drive_harddisk(d):
    out = box3d(d, 32, 114, 172, 66, 22, 36)
    if not d.small:
        out += "".join(line(50, y, 120, y, "#bff2ff", 5, opacity=0.8)
                       for y in (136, 150, 164))
    out += circle(184, 150, d.w(8) if d.small else 9, fill="url(#orange)",
                  stroke="#ffe7a6", stroke_width=d.w(2))
    return out


def i_drive_optical(d):
    out = box3d(d, 32, 114, 172, 66, 22, 36)
    out += rect(48, 132, 140, d.b(10), 4, fill="#060b24", stroke="#48cffe",
                stroke_width=d.w(2))
    out += path("M60,170 L74,154 L88,170 Z", fill="#e8f0ff")
    out += circle(184, 164, d.w(7), fill="url(#orange)")
    return out


def i_drive_removable_media(d):
    body = (solid(lambda **a: rect(104, 40, 48, 60, 6, **a), "metal", d,
                  gloss=False, rw=3) +
            (rect(114, 56, 10, 12, 2, fill="#0a1240") +
             rect(132, 56, 10, 12, 2, fill="#0a1240")) +
            solid(lambda **a: rect(88, 94, 80, 132, 18, **a), "body", d) +
            circle(128, 196, d.w(8), fill="url(#orange)"))
    return g(body, "rotate(28 128 132)")


def i_media_optical(d):
    hole = 16
    dd = (f"M220,128 A92,92 0 1 0 36,128 A92,92 0 1 0 220,128 Z "
          f"M{128 + hole},128 A{hole},{hole} 0 1 1 {128 - hole},128 "
          f"A{hole},{hole} 0 1 1 {128 + hole},128 Z")
    out = solid(lambda **a: path(dd, fill_rule="evenodd", **a), "disc", d,
                gloss=False)
    out += circle(128, 128, 36, fill="none", stroke="url(#metal)",
                  stroke_width=d.b(14), opacity=0.8)
    if not d.small:
        out += path("M128,128 L60,52 A100,100 0 0 1 104,38 Z", fill="#ffffff",
                    opacity=0.3)
    return out


def i_printer(d):
    out = solid(lambda **a: rect(76, 32, 104, 64, 4, **a), "paper", d,
                rw=2, gloss=False)
    out += solid(lambda **a: rect(30, 86, 196, 88, 18, **a), "body", d)
    out += rect(56, 150, 144, d.b(10), 4, fill="#060b24")
    out += circle(200, 112, d.w(7) if d.small else 8, fill="url(#orange)")
    paper = "M64,158 H192 L200,222 Q200,228 194,228 H62 Q56,228 56,222 Z"
    out += path(paper, fill="url(#paper)", stroke=INK, stroke_width=d.w(2))
    if not d.small:
        out += "".join(line(80, y, 176, y, "#3a78f0", 5) for y in (182, 198, 214))
    return out


def i_input_keyboard(d):
    body = "M48,96 H208 L226,178 Q228,190 216,190 H40 Q28,190 30,178 Z"
    out = solid(lambda **a: path(body, **a), "dark", d)
    rows = 2 if d.small else 4
    cols = (4 if d.small else 10)
    for r in range(rows):
        t0 = (r + 0.25) / rows
        t1 = (r + 0.85) / rows
        ya, yb = 104 + t0 * 70, 104 + t1 * 70
        xl0, xr0 = 54 - t0 * 18, 202 + t0 * 18
        xl1, xr1 = 54 - t1 * 18, 202 + t1 * 18
        n = cols if (r < rows - 1 or d.small) else 3
        for c in range(n):
            if r == rows - 1 and not d.small and c == 1:
                f0, f1 = 0.22, 0.78      # space bar
            elif r == rows - 1 and not d.small:
                f0, f1 = (0.02, 0.18) if c == 0 else (0.82, 0.98)
            else:
                f0, f1 = (c + 0.1) / n, (c + 0.9) / n
            pts = [(xl0 + (xr0 - xl0) * f0, ya), (xl0 + (xr0 - xl0) * f1, ya),
                   (xl1 + (xr1 - xl1) * f1, yb), (xl1 + (xr1 - xl1) * f0, yb)]
            out += path(poly(pts), fill="url(#cyan)",
                        stroke_linejoin="round", opacity=0.95)
    return out


def i_input_mouse(d):
    out = path("M128,62 C128,30 168,40 176,24", fill="none", stroke="url(#metal)",
               stroke_width=d.w(6), stroke_linecap="round")
    body = g(solid(lambda **a: ellipse(128, 144, 60, 86, **a), "body", d) +
             line(128, 60, 128, 130, "#bff2ff", d.w(4)) +
             path("M70,130 Q128,146 186,130", fill="none", stroke="#bff2ff",
                  stroke_width=d.w(4)) +
             rect(120, 84, 16, 30, 8, fill="url(#orange)"),
             "rotate(-16 128 144)")
    return out + body


def i_audio_card(d):
    out = solid(lambda **a: rect(30, 50, 14, 160, 4, **a), "metal", d,
                gloss=False, rw=2)
    out += solid(lambda **a: rect(40, 62, 188, 112, 8, **a), "dark", d,
                 gloss=False)
    n = 6 if d.small else 12
    for i in range(n):
        x = 70 + i * (130 / n)
        out += rect(x, 174, 130 / n * 0.6, 18, 2, fill="url(#orange)")
    out += solid(lambda **a: rect(116, 86, 64, 56, 6, **a), "body", d, rw=3)
    for cy in (90, 130):
        out += circle(37, cy, d.w(5), fill="url(#cyan)")
    if not d.small:
        out += em_wave(d, 66, 114)
    return out


def em_wave(d, x, y):
    pts = " ".join(f"{x - 16 + i * 4},{y + 14 * math.sin(i * 0.9)}"
                   for i in range(9))
    return f'<polyline points="{pts}" fill="none" stroke="#48cffe" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'


def i_video_display(d): return monitor(d)


def i_network_wired(d):
    # three stations on a cable: reads as "wired network" at every size
    out = ""
    w = d.b(10)
    out += line(128, 108, 128, 150, "#e8f0ff", w)
    out += line(66, 150, 190, 150, "#e8f0ff", w)
    out += line(66, 150, 66, 168, "#e8f0ff", w) + line(190, 150, 190, 168, "#e8f0ff", w)
    for x, y, f in ((128, 70, "body"), (66, 190, "body"), (190, 190, "body")):
        out += solid(lambda **a: rect(x - 38, y - 30, 76, 58, 10, **a), f, d)
        out += rect(x - 26, y - 18, 52, 30, 3, fill="url(#screen)")
    out += circle(128, 150, d.b(12), fill="url(#orange)", stroke=INK,
                  stroke_width=d.w(2))
    return out


def i_network_wireless(d):
    out = ""
    radii = (64, 112) if d.small else (52, 88, 124)
    for i, r in enumerate(radii):
        a0, a1 = math.radians(-135), math.radians(-45)
        cx, cy = 128, 204
        dd = (f"M{cx + r * math.cos(a0)},{cy + r * math.sin(a0)} "
              f"A{r},{r} 0 0 1 {cx + r * math.cos(a1)},{cy + r * math.sin(a1)}")
        w = d.b(16) if d.small else 18
        out += path(dd, fill="none", stroke="url(#cyan)" if i % 2 == 0
                    else "url(#violet)", stroke_width=w, stroke_linecap="round")
    out += circle(128, 204, 18, fill="url(#orange)", stroke=INK,
                  stroke_width=d.w(3))
    return out


def i_battery(d):
    out = solid(lambda **a: rect(204, 106, 22, 44, 6, **a), "metal", d,
                gloss=False, rw=2)
    out += solid(lambda **a: rect(30, 78, 176, 100, 16, **a), "glass", d,
                 gloss=False)
    out += solid(lambda **a: rect(44, 92, 112, 72, 8, **a), "cyan", d, rw=0)
    out += path("M134,92 L98,134 H124 L112,170 L156,122 H128 Z",
                fill="url(#orange)", stroke=INK, stroke_width=d.w(3),
                stroke_linejoin="round")
    out += rect(36, 84, 164, 30, 12, fill="url(#gloss)")
    return out


def i_system_file_manager(d):
    """A filing cabinet with a folder tab peeking out: files, not a folder."""
    out = solid(lambda **a: rect(52, 32, 152, 196, 14, **a), "body", d)
    for i, y in enumerate((48, 140)):
        out += solid(lambda **a: rect(66, y, 124, 74, 8, **a), "dark", d,
                     gloss=False, rw=3)
        out += rect(106, y + 32, 44, d.b(10), 4, fill="url(#metal)")
    out += path("M84,52 H120 L128,40 H168 V58 H84 Z", fill="url(#yellow)",
                stroke="#b8561a", stroke_width=d.w(2))
    return out


def i_utilities_terminal(d):
    out = solid(lambda **a: rect(28, 46, 200, 164, 14, **a), "#060b24", d,
                gloss=False, rw=6)
    out += path("M28,60 Q28,46 42,46 H214 Q228,46 228,60 V76 H28 Z",
                fill="url(#body)")
    w = d.b(12) if d.small else 14
    out += path("M62,106 L100,136 L62,166", fill="none", stroke="#48cffe",
                stroke_width=w, stroke_linecap="round", stroke_linejoin="round")
    out += line(116, 170, 168, 170, "#e8f0ff", w)
    return out


def i_internet_web_browser(d):
    rx = 100 if d.small else 108
    return (orbit(d, 128, 128, rx, 34, -22, False) +
            globe(d, 128, 128, 86, lines=not d.small) +
            orbit(d, 128, 128, rx, 34, -22, True))


def i_preferences_system(d): return gear(d, 128, 128, 100)


def i_systemsettings(d):
    return gear(d, 104, 104, 76) + gear(d, 178, 178, 48, "violet", n=7)


def i_accessories_text_editor(d):
    out = document(d, doc_lines(d))
    pen = (solid(lambda **a: rect(116, 40, 28, 130, 4, **a), "orange", d, rw=3) +
           rect(116, 40, 28, 22, 4, fill="url(#violet)") +
           path("M116,170 H144 L130,204 Z", fill="url(#paper)", stroke=INK,
                stroke_width=d.w(2)) + path("M124,190 H136 L130,204 Z", fill=INK))
    return out + g(pen, "rotate(38 130 130) translate(36 0)")


def i_accessories_calculator(d):
    out = solid(lambda **a: rect(54, 26, 148, 204, 18, **a), "body", d)
    out += rect(70, 42, 116, 44, 6, fill="#060b24", stroke="#48cffe",
                stroke_width=d.w(2))
    if not d.small:
        out += "".join(rect(x, 56, 16, 16, 2, fill="#48cffe", opacity=0.85)
                       for x in (118, 140, 162))
    cols, rows = (2, 2) if d.small else (4, 4)
    kw, kh = 116 / cols, 118 / rows
    for r in range(rows):
        for c in range(cols):
            fill = "url(#orange)" if (r == rows - 1 and c == cols - 1) else "url(#paper)"
            out += rect(70 + c * kw + 3, 100 + r * kh + 3, kw - 6, kh - 6, 4,
                        fill=fill, stroke=INK, stroke_width=d.w(1.5))
    return out


def _digits26(sw):
    # the "26" of the concept's calendar, drawn as strokes (no font)
    two = "M0,14 Q0,0 18,0 Q36,0 36,16 Q36,28 22,38 L0,58 H38"
    six = "M36,6 Q30,0 20,0 Q2,0 2,30 V40 Q2,58 20,58 Q38,58 38,42 Q38,26 20,26 Q6,26 2,36"
    st = (f'fill="none" stroke-width="{sw}" stroke-linecap="round" '
          f'stroke-linejoin="round"')
    return (f'<path d="{two}" stroke="#e8f0ff" {st}/>'
            f'<path d="{six}" transform="translate(50 0)" stroke="#e8f0ff" {st}/>')


def i_office_calendar(d):
    out = solid(lambda **a: rect(36, 50, 184, 176, 18, **a), "dark", d,
                gloss=False)
    out += path("M36,68 Q36,50 54,50 H202 Q220,50 220,68 V94 H36 Z",
                fill="url(#body)")
    out += path("M36,68 Q36,50 54,50 H202 Q220,50 220,68 V94 H36 Z",
                fill="url(#gloss)")
    for x in (82, 174):
        out += solid(lambda **a: rect(x - 8, 30, 16, 40, 8, **a), "metal", d,
                     gloss=False, rw=2)
    if d.small:
        for r in range(2):
            for c in range(3):
                out += rect(62 + c * 46, 118 + r * 46, 34, 32, 4,
                            fill="url(#orange)" if (r, c) == (1, 1) else "url(#cyan)")
    else:
        out += g(_digits26(11), "translate(84 118) scale(1.0 1.32)")
    return out


def i_multimedia_volume_control(d):
    out = solid(lambda **a: path("M34,98 H74 L124,54 V202 L74,158 H34 Z", **a),
                "body", d)
    radii = (52, 92) if d.small else (40, 70, 100)
    for r in radii:
        a = math.radians(48)
        cx, cy = 128, 128
        dd = (f"M{cx + r * math.cos(-a)},{cy + r * math.sin(-a)} "
              f"A{r},{r} 0 0 1 {cx + r * math.cos(a)},{cy + r * math.sin(a)}")
        out += path(dd, fill="none", stroke="url(#magenta)",
                    stroke_width=d.b(14) if d.small else 14, stroke_linecap="round")
    return out


def i_applications_games(d):
    out = solid(lambda **a: path("M40,182 L64,160 H192 L216,182 V198 Q216,214 200,214 "
                                 "H56 Q40,214 40,198 Z", **a), "violet", d)
    out += ellipse(128, 166, 40, 10, fill="#060b24", opacity=0.7)
    out += solid(lambda **a: rect(118, 86, 20, 84, 8, **a), "metal", d,
                 gloss=False, rw=2)
    out += solid(lambda **a: circle(128, 72, 36, **a), "red", d)
    out += circle(178, 180, d.w(8) if d.small else 10, fill="url(#orange)")
    return out


def i_applications_multimedia(d):
    out = solid(lambda **a: rect(30, 52, 196, 152, 12, **a), "violet", d)
    if not d.small:
        for i in range(8):
            for y in (60, 186):
                out += rect(44 + i * 22, y, 12, 10, 2, fill="#060b24")
    out += rect(46, 78, 164, 100, 6, fill="url(#screen)")
    out += path("M94,96 L144,128 L94,160 Z", fill="url(#paper)",
                stroke=INK, stroke_width=d.w(3), stroke_linejoin="round")
    if not d.small:
        out += emblem(em_note, d, 182, 168, 70)
    return out


def i_applications_office(d):
    out = document(d)
    out += circle(128, 112, 40, fill="url(#cyan)", stroke=INK,
                  stroke_width=d.w(3))
    out += path("M128,112 V72 A40,40 0 0 1 166,124 Z", fill="url(#orange)",
                stroke=INK, stroke_width=d.w(3), stroke_linejoin="round")
    out += doc_lines(d, ys=(180, 206) if not d.small else (192,))
    return out


def i_applications_internet(d):
    out = globe(d, 116, 116, 88, lines=not d.small)
    env = (solid(lambda **a: rect(136, 150, 92, 64, 8, **a), "paper", d,
                 rw=3, gloss=False) +
           path("M140,156 L182,186 L224,156", fill="none", stroke="url(#orange)",
                stroke_width=d.w(6), stroke_linejoin="round"))
    return out + env


def i_applications_utilities(d):
    # wrench: open ring head, jaw facing away from the handle
    hx, hy, R, r = 168, 84, 40, 16
    gap = math.radians(32)
    base = math.radians(-45)
    pts = [(hx + R * math.cos(base + gap + t * (2 * math.pi - 2 * gap) / 24),
            hy + R * math.sin(base + gap + t * (2 * math.pi - 2 * gap) / 24))
           for t in range(25)]
    pts += [(hx + r * math.cos(base - gap * 0.9), hy + r * math.sin(base - gap * 0.9)),
            (hx + r * math.cos(base + gap * 0.9), hy + r * math.sin(base + gap * 0.9))]
    out = line(56, 196, 196, 56, INK, 1, opacity=0)  # keep bbox stable
    driver = (line(64, 64, 150, 150, "url(#metal)", d.b(10)) +
              path("M56,56 L70,48 L62,70 Z", fill="url(#metal)") +
              g(solid(lambda **a: rect(-16, 0, 32, 74, 12, **a), "orange", d),
                "translate(150 150) rotate(-45)"))
    wrench = (line(70, 182, 150, 102, INK, 36) +
              line(70, 182, 150, 102, "url(#metal)", 26) +
              solid(lambda **a: path(poly(pts), **a), "metal", d, rw=4))
    return out + driver + wrench


def i_applications_system(d):
    return (solid(lambda **a: rect(58, 30, 140, 196, 16, **a), "body", d) +
            (rect(76, 48, 104, 14, 4, fill="url(#dark)") if not d.small else "") +
            rect(80, 204, 22, d.w(5), 2, fill="#ff9a3c") +
            g(gear(d, 128, 130, 52, "cyan", n=8), ""))


def i_help_browser(d):
    out = circle(128, 128, 72, fill="none", stroke="url(#body)", stroke_width=44)
    circ = 2 * math.pi * 72
    out += circle(128, 128, 72, fill="none", stroke="url(#orange)",
                  stroke_width=44, stroke_dasharray=f"{circ / 8:.2f} {circ / 8:.2f}",
                  stroke_dashoffset=f"{circ / 16:.2f}")
    out += circle(128, 128, 94, fill="none", stroke="url(#rim)", stroke_width=d.w(5))
    out += circle(128, 128, 50, fill="none", stroke="url(#rim)", stroke_width=d.w(5))
    out += path("M60,92 A80,80 0 0 1 92,60", fill="none", stroke="#ffffff",
                stroke_width=8, stroke_linecap="round", opacity=0.6)
    return out


def i_system_shutdown(d):
    out = solid(lambda **a: rect(38, 38, 180, 180, 34, **a), "#14103a", d,
                gloss=False, rw=4 if d.small else 7, rim="rimm")
    out += rect(42, 42, 172, 80, 30, fill="url(#gloss)", opacity=0.5)
    w = d.b(16) if d.small else 18
    out += path("M96,90 A52,52 0 1 0 160,90", fill="none",
                stroke="#ffc4ff" if d.small else "url(#magenta)",
                stroke_width=w, stroke_linecap="round")
    out += line(128, 70, 128, 126, "#ffc4ff" if d.small else "#f39cff", w)
    return out


def i_system_lock_screen(d):
    out = path("M86,122 V92 A42,42 0 0 1 170,92 V122", fill="none",
               stroke=INK, stroke_width=d.b(28) if d.small else 30)
    out += path("M86,122 V92 A42,42 0 0 1 170,92 V122", fill="none",
                stroke="url(#metal)", stroke_width=d.b(20) if d.small else 22)
    out += solid(lambda **a: rect(52, 112, 152, 114, 18, **a), "body", d)
    out += circle(128, 156, d.b(14) if d.small else 16, fill="url(#orange)")
    out += path("M120,160 H136 L142,196 H114 Z", fill="url(#orange)")
    return out


def i_system_search(d):
    out = line(160, 160, 202, 202, INK, 34 if d.small else 38)
    out += line(160, 160, 202, 202, "url(#violet)", 26 if d.small else 28)
    out += circle(108, 108, 70, fill="url(#cyan)", opacity=0.35)
    out += ellipse(86, 82, 34, 20, fill="#ffffff", opacity=0.45,
                   transform="rotate(-35 86 82)")
    out += circle(108, 108, 70, fill="none", stroke="url(#metal)",
                  stroke_width=d.b(18) if d.small else 18)
    out += circle(108, 108, 79, fill="none", stroke="url(#rim)", stroke_width=d.w(3))
    return out


def _landscape(x, y, w, h):
    return (circle(x + w * 0.74, y + h * 0.3, h * 0.14, fill="url(#orange)") +
            path(f"M{x},{y + h} L{x + w * 0.3},{y + h * 0.45} L{x + w * 0.52},"
                 f"{y + h * 0.75} L{x + w * 0.68},{y + h * 0.58} L{x + w},"
                 f"{y + h} Z", fill="url(#violet)"))


def i_preferences_desktop(d):
    return monitor(d, _landscape(47, 53, 162, 106))


def i_preferences_desktop_display(d):
    a = ""
    w = d.b(10) if d.small else 10
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = 128 + sx * 54, 106 + sy * 30
        a += path(f"M{cx - sx * 22},{cy} H{cx} V{cy - sy * 18}", fill="none",
                  stroke="#e8f0ff", stroke_width=w, stroke_linecap="round",
                  stroke_linejoin="round")
    return monitor(d, a)


def i_text_plain(d): return document(d, doc_lines(d))


def i_application_x_executable(d):
    out = solid(lambda **a: rect(30, 46, 196, 164, 14, **a), "dark", d,
                gloss=False)
    out += path("M30,60 Q30,46 44,46 H212 Q226,46 226,60 V78 H30 Z",
                fill="url(#body)")
    if not d.small:
        out += "".join(circle(x, 62, 6, fill="#e8f0ff") for x in (190, 208))
    return out + gear(d, 128, 144, 52, "cyan", n=8)


def i_image_x_generic(d):
    return document(d, rect(80, 86, 100, 112, 6, fill="url(#screen)",
                            stroke=INK, stroke_width=d.w(3)) +
                    _landscape(80, 86, 100, 112), fold="orange")


def i_video_x_generic(d):
    return document(d, emblem(em_play, d, 130, 146, 104 if not d.small else 116))


def i_audio_x_generic(d):
    return document(d, emblem(em_note, d, 128, 146, 96 if not d.small else 110))


def i_application_pdf(d):
    # a printed page: picture block, lines and a red band; no curl, which
    # would read as a vendor's mark
    band = rect(62, 176, 136, 30, 0, fill="url(#red)")
    pic = rect(84, 84, 48, 40, 4, fill="url(#screen)", stroke="#bfefff",
               stroke_width=d.w(3))
    lines = doc_lines(d, ys=(144,) if d.small else (88, 104, 120, 144, 160),
                      x0=84 if d.small else 142)
    if not d.small:
        lines = doc_lines(d, ys=(90, 106, 122), x0=144) + doc_lines(
            d, ys=(144, 160), x0=84)
    return document(d, band + (pic if not d.small else "") + lines, fold="red")


def i_application_x_archive(d):
    out = document(d)
    teeth = ""
    step = 16 if not d.small else 24
    for i, y in enumerate(range(40, 200, step)):
        x = 122 if i % 2 else 134
        teeth += rect(x - 10, y, 20, step * 0.6, 2, fill="url(#orange)")
    out += teeth
    out += solid(lambda **a: rect(108, 168, 40, 52, 8, **a), "metal", d,
                 gloss=False, rw=3)
    out += rect(120, 186, 16, 20, 3, fill="#0a1240")
    return out


def i_unknown(d):
    out = document(d, dashed=True)
    out += circle(130, 140, 36, fill="none", stroke="#bff2ff",
                  stroke_width=d.w(8) if d.small else 10,
                  stroke_dasharray="14 10", opacity=0.9)
    out += circle(130, 140, 10, fill="url(#orange)")
    return out


# --------------------------------------------------------------------------
# More glossy icons: places, devices, apps, mimetypes

def em_star(d):
    pts = [(50 + (46 if i % 2 == 0 else 20) * math.cos(math.radians(-90 + i * 36)),
            54 + (46 if i % 2 == 0 else 20) * math.sin(math.radians(-90 + i * 36)))
           for i in range(10)]
    return path(poly(pts), fill="url(#orange)", **_es(d))


def em_cloud(d):
    c = ("M24,80 Q4,80 6,60 Q8,42 28,42 Q32,18 56,18 Q78,18 84,40 "
         "Q98,40 98,60 Q98,80 78,80 Z")
    return path(c, fill="url(#paper)", **_es(d))


def em_code(d):
    dd = "M34,22 L8,50 L34,78 M66,22 L92,50 L66,78"
    out = ("" if d.small else
           path(dd, fill="none", stroke=INK, stroke_width=20,
                stroke_linecap="round", stroke_linejoin="round"))
    out += path(dd, fill="none", stroke="url(#cyan)", stroke_width=11,
                stroke_linecap="round", stroke_linejoin="round")
    return out + line(58, 14, 42, 86, "#ff9a3c", 10)


def em_lock(d):
    return (path("M30,48 V34 A20,20 0 0 1 70,34 V48", fill="none", stroke=INK,
                 stroke_width=16) +
            path("M30,48 V34 A20,20 0 0 1 70,34 V48", fill="none",
                 stroke="url(#paper)", stroke_width=9) +
            rect(16, 44, 68, 48, 8, fill="url(#orange)", **_es(d)))


def em_root(d):
    return (line(70, 8, 30, 92, INK, 22) + line(70, 8, 30, 92, "url(#orange)", 13))


def em_clock(d):
    return (circle(50, 50, 44, fill="url(#paper)", **_es(d)) +
            path("M50,22 V50 L70,62", fill="none", stroke=INK, stroke_width=9,
                 stroke_linecap="round", stroke_linejoin="round"))


def i_folder_root(d): return folder(d, em_root)
def i_folder_recent(d): return folder(d, em_clock)
def i_folder_favorites(d): return folder(d, em_star)
def i_folder_cloud(d): return folder(d, em_cloud)
def i_folder_development(d): return folder(d, em_code)
def i_folder_locked(d): return folder(d, em_lock)


def i_network_server(d):
    out = ""
    for i, y in enumerate((36, 102, 168)):
        out += solid(lambda **a: rect(48, y, 160, 54, 10, **a), "body", d)
        out += circle(184, y + 27, d.w(8) if d.small else 8,
                      fill="url(#orange)" if i == 0 else "url(#cyan)")
        if not d.small:
            out += "".join(line(68, y + 18 + k * 9, 140, y + 18 + k * 9,
                                "#060b24", 4) for k in range(3))
    return out


def i_computer_laptop(d):
    out = solid(lambda **a: rect(52, 44, 152, 132, 10, **a), "dark", d,
                gloss=False)
    out += rect(64, 56, 128, 106, 3, fill="url(#screen)")
    out += path("M64,56 H144 L104,162 H64 Z", fill="#ffffff", opacity=0.16)
    out += solid(lambda **a: path("M24,180 H232 L218,206 Q214,214 204,214 H52 "
                                  "Q42,214 38,206 Z", **a), "metal", d, rw=3)
    if not d.small:
        out += rect(108, 186, 40, 6, 3, fill="#5a68a8")
    return out


def i_smartphone(d):
    out = solid(lambda **a: rect(76, 22, 104, 212, 20, **a), "dark", d,
                gloss=False)
    out += rect(88, 46, 80, 160, 4, fill="url(#screen)")
    out += path("M88,46 H150 L108,206 H88 Z", fill="#ffffff", opacity=0.16)
    out += rect(112, 30, 32, d.w(6), 3, fill="#5a68a8")
    out += circle(128, 220, d.w(6), fill="url(#cyan)")
    return out


def i_camera_photo(d):
    out = solid(lambda **a: path("M84,78 L102,50 H154 L172,78 Z", **a), "metal",
                d, gloss=False, rw=3)
    out += solid(lambda **a: rect(26, 74, 204, 138, 18, **a), "body", d)
    out += circle(128, 144, 54, fill="url(#metal)", stroke=INK,
                  stroke_width=d.w(3))
    out += circle(128, 144, 38, fill="url(#glass)", stroke="url(#rim)",
                  stroke_width=d.w(3))
    out += ellipse(116, 130, 14, 9, fill="#ffffff", opacity=0.5,
                   transform="rotate(-30 116 130)")
    out += rect(182, 90, 30, d.b(14), 4, fill="url(#orange)")
    return out


def i_audio_headphones(d):
    band = "M52,156 V128 A76,76 0 0 1 204,128 V156"
    out = path(band, fill="none", stroke=INK, stroke_width=d.b(26) if d.small else 26)
    out += path(band, fill="none", stroke="url(#metal)",
                stroke_width=d.b(16) if d.small else 16)
    for x in (30, 178):
        out += solid(lambda **a: rect(x, 132, 48, 90, 18, **a), "body", d)
        out += rect(x + (34 if x < 128 else 0), 144, 14, 66, 6,
                    fill="url(#violet)")
    return out


def i_audio_input_microphone(d):
    hold = "M66,112 V124 A62,62 0 0 0 190,124 V112"
    out = path(hold, fill="none", stroke=INK, stroke_width=d.b(22) if d.small else 22)
    out += path(hold, fill="none", stroke="url(#body)",
                stroke_width=d.b(13) if d.small else 13)
    out += line(128, 188, 128, 212, "url(#metal)", d.b(14) if d.small else 14)
    out += solid(lambda **a: rect(80, 210, 96, 18, 9, **a), "body", d, rw=3)
    out += solid(lambda **a: rect(94, 24, 68, 132, 34, **a), "metal", d)
    if not d.small:
        out += "".join(line(108, y, 148, y, "#5a68a8", 5) for y in (56, 74, 92))
    return out


def i_input_gaming(d):
    body = ("M66,82 H190 Q232,82 238,146 L242,182 Q244,214 216,214 Q198,214 186,192 "
            "L176,174 H80 L70,192 Q58,214 40,214 Q12,214 14,182 L18,146 Q24,82 66,82 Z")
    out = solid(lambda **a: path(body, **a), "violet", d)
    w = d.b(14) if d.small else 14
    out += line(56, 130, 100, 130, "#e8f0ff", w) + line(78, 108, 78, 152, "#e8f0ff", w)
    out += circle(176, 116, d.b(12) if d.small else 12, fill="url(#orange)")
    out += circle(202, 142, d.b(12) if d.small else 12, fill="url(#cyan)")
    return out


def i_cpu(d):
    out = ""
    n = 4 if d.small else 6
    for i in range(n):
        p = 76 + i * (104 / (n - 1))
        w = d.b(10) if d.small else 9
        out += line(p, 34, p, 222, "url(#metal)", w) + line(34, p, 222, p, "url(#metal)", w)
    out += solid(lambda **a: rect(58, 58, 140, 140, 16, **a), "dark", d, gloss=False)
    out += solid(lambda **a: rect(90, 90, 76, 76, 8, **a), "body", d, rw=3)
    out += circle(74, 74, d.w(6), fill="url(#orange)")
    return out


def i_memory(d):
    out = solid(lambda **a: path("M20,88 H236 V172 H140 V160 H116 V172 H20 Z", **a),
                "green", d)
    n = 4 if d.small else 4
    for i in range(n):
        out += rect(34 + i * 52, 102, 38, 46, 4, fill="url(#dark)",
                    stroke="#9fe8ff", stroke_width=d.w(2))
    if not d.small:
        for i in range(16):
            x = 30 + i * 13 + (12 if i >= 8 else 0)
            out += rect(x, 176, 7, 18, 1, fill="url(#orange)")
    else:
        out += rect(28, 176, 200, d.w(12), 2, fill="url(#orange)")
    return out


def i_scanner(d):
    out = solid(lambda **a: path("M40,128 L64,52 H192 L216,128 Z", **a), "dark", d,
                gloss=False)
    out += solid(lambda **a: rect(26, 128, 204, 76, 14, **a), "body", d)
    out += rect(46, 140, 164, d.b(12), 4, fill="url(#cyan)")
    out += circle(204, 184, d.w(7), fill="url(#orange)")
    return out


def _gloss_tile(d, x, y, w, h, fill):
    return solid(lambda **a: rect(x, y, w, h, 16, **a), fill, d)


def i_applications_development(d):
    out = solid(lambda **a: rect(28, 46, 200, 164, 14, **a), "#060b24", d,
                gloss=False, rw=6)
    out += path("M28,60 Q28,46 42,46 H214 Q228,46 228,60 V76 H28 Z",
                fill="url(#body)")
    w = d.b(12) if d.small else 14
    st = dict(fill="none", stroke_width=w, stroke_linecap="round",
              stroke_linejoin="round")
    out += path("M92,108 L60,142 L92,176", stroke="#48cffe", **st)
    out += path("M164,108 L196,142 L164,176", stroke="#48cffe", **st)
    out += line(140, 102, 116, 182, "#ff9a3c", w)
    return out


def i_applications_education(d):
    out = solid(lambda **a: path("M20,74 V206 Q80,198 128,222 Q176,198 236,206 V74 "
                                 "Q176,66 128,90 Q80,66 20,74 Z", **a), "body", d)
    for s in (1, -1):
        pg = (f"M128,92 Q{128 - s * 46},64 {128 - s * 94},74 V190 "
              f"Q{128 - s * 46},184 128,206 Z")
        out += path(pg, fill="url(#paper)", stroke=INK, stroke_width=d.w(2))
        if not d.small:
            out += "".join(line(128 - s * 24, y, 128 - s * 74, y - 6, "#3a78f0", 5)
                           for y in (114, 138, 162))
    return out


def i_applications_graphics(d):
    pal = ("M128,36 C200,36 236,84 228,132 C222,168 188,156 170,172 "
           "C152,188 178,222 132,222 C70,222 28,182 28,126 C28,74 72,36 128,36 Z")
    out = solid(lambda **a: path(pal, **a), "metal", d)
    for (x, y), c in zip(((84, 92), (128, 70), (174, 88), (72, 144), (118, 180)),
                         ("red", "orange", "green", "cyan", "violet")):
        out += circle(x, y, d.b(17) if d.small else 17, fill=f"url(#{c})",
                      stroke=INK, stroke_width=d.w(2))
    return out


def i_applications_science(d):
    flask = ("M104,30 H152 M112,30 V98 L50,202 Q42,224 66,224 H190 Q214,224 206,202 "
             "L144,98 V30")
    body = ("M112,30 V98 L50,202 Q42,224 66,224 H190 Q214,224 206,202 L144,98 V30 Z")
    out = path(body, fill="url(#glass)", opacity=0.9)
    out += path("M84,150 H172 L206,202 Q214,224 190,224 H66 Q42,224 50,202 Z",
                fill="url(#green)")
    if not d.small:
        out += circle(116, 186, 9, fill="#e8fff4", opacity=0.8)
        out += circle(144, 170, 6, fill="#e8fff4", opacity=0.8)
    out += path(flask, fill="none", stroke="url(#rim)", stroke_width=d.w(7),
                stroke_linecap="round", stroke_linejoin="round")
    return out


def i_applications_other(d):
    out = ""
    for (x, y), c in zip(((36, 36), (136, 36), (36, 136), (136, 136)),
                         ("cyan", "violet", "orange", "green")):
        out += _gloss_tile(d, x, y, 84, 84, c)
    return out


def i_preferences_desktop_theme_global(d):
    sw = ""
    for i, c in enumerate(("cyan", "violet", "orange")):
        sw += rect(47 + i * 54, 53, 54, 106, 0, fill=f"url(#{c})")
    return monitor(d, sw)


def i_preferences_desktop_font(d):
    a = "M56,214 L128,42 L200,214 M86,152 H170"
    w = d.b(30) if d.small else 30
    out = path(a, fill="none", stroke=INK, stroke_width=w + 10,
               stroke_linecap="round", stroke_linejoin="round")
    out += path(a, fill="none", stroke="url(#cyan)", stroke_width=w,
                stroke_linecap="round", stroke_linejoin="round")
    return out


def i_preferences_desktop_locale(d):
    b1 = "M30,52 Q30,36 46,36 H150 Q166,36 166,52 V114 Q166,130 150,130 H80 L52,156 V130 H46 Q30,130 30,114 Z"
    b2 = "M226,118 Q226,102 210,102 H106 Q90,102 90,118 V180 Q90,196 106,196 H176 L204,222 V196 H210 Q226,196 226,180 Z"
    out = solid(lambda **a: path(b1, **a), "body", d)
    out += solid(lambda **a: path(b2, **a), "orange", d)
    if not d.small:
        out += path("M74,108 L98,58 L122,108 M84,90 H112", fill="none",
                    stroke="#e8f0ff", stroke_width=9, stroke_linecap="round",
                    stroke_linejoin="round")
        out += "".join(line(116, y, 200 - (30 if y > 150 else 0), y, INK, 8)
                       for y in (132, 152, 172))
    return out


BELL = ("M128,34 Q82,34 78,96 L72,156 L46,190 H210 L184,156 L178,96 "
        "Q174,34 128,34 Z")


def i_preferences_desktop_notification_bell(d):
    out = solid(lambda **a: path(BELL, **a), "yellow", d)
    out += solid(lambda **a: circle(128, 206, 20, **a), "metal", d, gloss=False, rw=3)
    return out


def i_system_users(d):
    out = solid(lambda **a: path("M40,226 Q40,146 128,146 Q216,146 216,226 Z", **a),
                "body", d)
    out += solid(lambda **a: circle(128, 90, 50, **a), "cyan", d)
    return out


def i_preferences_desktop_accessibility(d):
    out = solid(lambda **a: circle(128, 128, 100, **a), "body", d)
    w = d.b(16) if d.small else 16
    st = dict(fill="none", stroke="#e8f0ff", stroke_width=w,
              stroke_linecap="round", stroke_linejoin="round")
    out += circle(128, 72, d.b(16) if d.small else 16, fill="url(#orange)")
    out += path("M70,106 H186 M128,106 V148 M128,148 L96,198 M128,148 L160,198",
                **st)
    return out


def i_preferences_desktop_effects(d):
    out = line(54, 210, 150, 114, INK, d.b(26) if d.small else 26)
    out += line(54, 210, 150, 114, "url(#violet)", d.b(18) if d.small else 18)
    out += line(134, 130, 150, 114, "#e8f0ff", d.b(18) if d.small else 18)
    s = "M180,30 Q186,74 226,80 Q186,86 180,130 Q174,86 134,80 Q174,74 180,30 Z"
    out += path(s, fill="url(#orange)", stroke=INK, stroke_width=d.w(3))
    if not d.small:
        out += path("M88,52 Q91,72 108,74 Q91,76 88,96 Q85,76 68,74 Q85,72 88,52 Z",
                    fill="url(#cyan)")
        out += circle(210, 164, 8, fill="url(#cyan)")
    return out


def i_preferences_desktop_virtual(d):
    out = ""
    for i, (x, y) in enumerate(((28, 44), (134, 44), (28, 136), (134, 136))):
        out += solid(lambda **a: rect(x, y, 94, 76, 10, **a), "dark", d,
                     gloss=False, rw=4)
        out += rect(x + 10, y + 10, 74, 56, 3,
                    fill="url(#screen)" if i == 0 else "url(#glass)")
    return out


SHIELD = "M128,26 L210,56 V124 Q210,192 128,230 Q46,192 46,124 V56 Z"


def i_preferences_security(d):
    out = solid(lambda **a: path(SHIELD, **a), "body", d)
    w = d.b(18) if d.small else 20
    ck = "M90,130 L118,158 L170,100"
    out += path(ck, fill="none", stroke=INK, stroke_width=w + 10,
                stroke_linecap="round", stroke_linejoin="round")
    out += path(ck, fill="none", stroke="url(#green)", stroke_width=w,
                stroke_linecap="round", stroke_linejoin="round")
    return out


def _link(d, a, b, w):
    # two rounded links along the diagonal: a generic "paired" mark
    out = ""
    for x, c in ((34, a), (114, b)):
        r = rect(x, 100, 108, 56, 28, fill="none", stroke=c, stroke_width=w)
        out += r
    return g(out, "rotate(-45 128 128)")


def i_preferences_system_bluetooth(d):
    w = d.b(22) if d.small else 24
    return (_link(d, INK, INK, w + 12) + _link(d, "url(#cyan)", "url(#violet)", w))


def i_preferences_system_time(d):
    out = solid(lambda **a: circle(128, 128, 100, **a), "body", d)
    out += circle(128, 128, 78, fill="url(#glass)", stroke="url(#rim)",
                  stroke_width=d.w(3))
    if not d.small:
        for i in range(12):
            a = math.radians(i * 30)
            r0 = 62 if i % 3 else 56
            out += line(128 + r0 * math.cos(a), 128 + r0 * math.sin(a),
                        128 + 70 * math.cos(a), 128 + 70 * math.sin(a), "#9fe8ff", 4)
    w = d.b(12) if d.small else 12
    out += line(128, 128, 128, 74, "#e8f0ff", w) + line(128, 128, 166, 150, "url(#orange)", w)
    out += circle(128, 128, d.b(9) if d.small else 9, fill="#e8f0ff")
    return out


def _window(d, x, y, w, h, fill):
    out = solid(lambda **a: rect(x, y, w, h, 12, **a), "dark", d, gloss=False)
    out += path(f"M{x},{y + 12} Q{x},{y} {x + 12},{y} H{x + w - 12} Q{x + w},{y} "
                f"{x + w},{y + 12} V{y + 30} H{x} Z", fill=f"url(#{fill})")
    return out


def i_preferences_system_windows(d):
    out = _window(d, 78, 34, 150, 116, "violet")
    out += _window(d, 28, 100, 160, 122, "body")
    out += rect(42, 144, 132, 64, 3, fill="url(#screen)")
    return out


def i_utilities_system_monitor(d):
    pts = (47, 140), (75, 120), (98, 130), (124, 82), (150, 112), (176, 96), (209, 108)
    gr = "".join(line(47, y, 209, y, "#bff2ff", 2, opacity=0.35)
                 for y in (80, 106, 132)) if not d.small else ""
    pl = " ".join(f"{x},{y}" for x, y in pts)
    gr += (f'<polyline points="{pl}" fill="none" stroke="#ff9a3c" '
           f'stroke-width="{d.b(10) if d.small else 8}" stroke-linecap="round" '
           f'stroke-linejoin="round"/>')
    return monitor(d, gr)


def i_system_software_install(d):
    out = box3d(d, 46, 128, 136, 88, 34, 38)
    arr = "M110,22 H146 V66 H172 L128,112 L84,66 H110 Z"
    out += path(arr, fill="url(#orange)", stroke=INK, stroke_width=d.w(4),
                stroke_linejoin="round")
    return out


def _photo(d, x, y, w, h, rot):
    out = solid(lambda **a: rect(x, y, w, h, 6, **a), "paper", d, gloss=False, rw=3)
    out += rect(x + 12, y + 12, w - 24, h - 34, 2, fill="url(#screen)")
    out += _landscape(x + 12, y + 12, w - 24, h - 34)
    return g(out, f"rotate({rot} {x + w / 2} {y + h / 2})")


def i_image_viewer(d):
    return _photo(d, 70, 32, 150, 128, 8) + _photo(d, 32, 90, 160, 136, -5)


def i_document_viewer(d):
    return document(d, doc_lines(d)) + g(i_system_search(d),
                                          "translate(98 98) scale(0.6)")


def i_accessories_screenshot(d):
    out = rect(64, 74, 128, 104, 3, fill="url(#screen)") + _landscape(64, 74, 128, 104)
    c = ("M30,92 V50 H72 M184,50 H226 V92 M226,162 V204 H184 M72,204 H30 V162")
    w = d.b(16) if d.small else 16
    out += path(c, fill="none", stroke=INK, stroke_width=w + 10,
                stroke_linecap="round", stroke_linejoin="round")
    out += path(c, fill="none", stroke="url(#paper)", stroke_width=w,
                stroke_linecap="round", stroke_linejoin="round")
    return out


def i_internet_mail(d):
    out = solid(lambda **a: rect(26, 60, 204, 140, 14, **a), "paper", d, rw=4)
    out += path("M34,70 L128,142 L222,70", fill="none", stroke="url(#body)",
                stroke_width=d.b(12) if d.small else 12, stroke_linejoin="round",
                stroke_linecap="round")
    return out


def power_tile(d, glyph):
    """The rounded magenta-rimmed tile of system-shutdown with any glyph."""
    out = solid(lambda **a: rect(38, 38, 180, 180, 34, **a), "#14103a", d,
                gloss=False, rw=4 if d.small else 7, rim="rimm")
    out += rect(42, 42, 172, 80, 30, fill="url(#gloss)", opacity=0.5)
    w = d.b(16) if d.small else 18
    col = "#ffc4ff" if d.small else "url(#magenta)"
    return out + path(glyph, fill="none", stroke=col, stroke_width=w,
                      stroke_linecap="round", stroke_linejoin="round")


def arc(cx, cy, r, a0, a1):
    """Arc path from angle a0 to a1 (degrees, clockwise on screen)."""
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (f"M{p0[0]:.1f},{p0[1]:.1f} A{r},{r} 0 {large} 1 "
            f"{p1[0]:.1f},{p1[1]:.1f}")


def arrow_head(cx, cy, r, a, size):
    """Open head at angle a of a clockwise arc."""
    x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
    t = math.radians(a + 90)            # direction of travel
    out = []
    for s in (150, -150):
        b = t + math.radians(s)
        out.append((x + size * math.cos(b), y + size * math.sin(b)))
    return (f"M{out[0][0]:.1f},{out[0][1]:.1f} L{x:.1f},{y:.1f} "
            f"L{out[1][0]:.1f},{out[1][1]:.1f}")


def i_system_reboot(d):
    return power_tile(d, arc(128, 128, 50, -40, 250) + arrow_head(128, 128, 50, 250, 26))


def i_system_log_out(d):
    return power_tile(d, "M120,80 H84 V176 H120 M112,128 H176 M152,104 L176,128 L152,152")


def i_system_suspend(d):
    return power_tile(d, "M146,78 A54,54 0 1 0 178,150 A44,44 0 0 1 146,78 Z")


def i_system_switch_user(d):
    return power_tile(d, "M104,104 m-20,0 a20,20 0 1 0 40,0 a20,20 0 1 0 -40,0 "
                         "M68,172 Q68,140 104,140 Q140,140 140,172 "
                         "M156,90 m-16,0 a16,16 0 1 0 32,0 a16,16 0 1 0 -32,0 "
                         "M160,124 Q188,124 188,152")


# mimetypes ----------------------------------------------------------------

def _strokes(dd, d, col, w, ink=True):
    st = dict(fill="none", stroke_linecap="round", stroke_linejoin="round")
    out = path(dd, stroke=INK, stroke_width=w + 8, **st) if (ink and not d.small) else ""
    return out + path(dd, stroke=col, stroke_width=w, **st)


def i_text_html(d):
    w = d.b(14) if d.small else 14
    return document(d, _strokes("M108,110 L76,146 L108,182 M152,110 L184,146 L152,182",
                                d, "#7fe6ff", w) +
                    _strokes("M140,100 L120,192", d, "#ff9a3c", w), fold="cyan")


def i_text_x_script(d):
    w = d.b(14) if d.small else 14
    return document(d, _strokes("M86,112 L118,142 L86,172", d, "#7fe6ff", w) +
                    _strokes("M132,178 H174", d, "#e8f0ff", w), fold="green")


def i_text_x_csrc(d):
    w = d.b(12) if d.small else 12
    br = ("M112,94 Q94,94 94,112 V128 Q94,142 80,144 Q94,146 94,160 V176 "
          "Q94,194 112,194 M148,94 Q166,94 166,112 V128 Q166,142 180,144 "
          "Q166,146 166,160 V176 Q166,194 148,194")
    return document(d, _strokes(br, d, "#7fe6ff", w) +
                    circle(130, 144, d.b(10) if d.small else 10, fill="url(#orange)"),
                    fold="cyan")


def i_text_markdown(d):
    w = d.b(13) if d.small else 13
    h = "M110,96 L98,196 M156,96 L144,196 M84,124 H176 M80,168 H172"
    return document(d, _strokes(h, d, "#e8f0ff", w), fold="orange")


def i_x_office_document(d):
    c = rect(84, 84, 92, d.b(14) if d.small else 14, 4, fill="url(#orange)")
    c += doc_lines(d, ys=(150, 186) if d.small else (118, 140, 162, 184, 206))
    return document(d, c, fold="cyan")


def i_x_office_spreadsheet(d):
    c = rect(80, 84, 100, 128, 4, fill="#0a1650", stroke="#bfefff",
             stroke_width=d.w(3))
    c += rect(80, 84, 100, 28, 4, fill="url(#green)")
    rows = (112, 150, 188) if d.small else (112, 132, 152, 172, 192)
    c += "".join(line(80, y, 180, y, "#bfefff", d.w(3)) for y in rows[1:])
    c += line(124, 84, 124, 212, "#bfefff", d.w(3))
    return document(d, c, fold="green")


def i_x_office_presentation(d):
    out = line(128, 186, 128, 226, "url(#metal)", d.b(12) if d.small else 12)
    out += line(128, 196, 92, 228, "url(#metal)", d.b(10) if d.small else 10)
    out += line(128, 196, 164, 228, "url(#metal)", d.b(10) if d.small else 10)
    out += solid(lambda **a: rect(24, 44, 208, 146, 10, **a), "page", d)
    for i, (h, c) in enumerate(((44, "cyan"), (74, "orange"), (60, "green"), (92, "violet"))):
        out += rect(60 + i * 38, 168 - h, 24, h, 3, fill=f"url(#{c})")
    out += line(48, 170, 208, 170, "#e8f0ff", d.w(4))
    return out


def i_x_office_drawing(d):
    c = circle(108, 120, 28, fill="url(#orange)", stroke=INK, stroke_width=d.w(3))
    c += path("M150,104 L182,160 H118 Z", fill="url(#cyan)", stroke=INK,
              stroke_width=d.w(3), stroke_linejoin="round")
    c += rect(86, 164, 52, 44, 4, fill="url(#violet)", stroke=INK,
              stroke_width=d.w(3))
    return document(d, c, fold="orange")


def i_x_office_address_book(d):
    out = ""
    for y in (70, 112, 154):
        out += rect(196, y, 26, 30, 6, fill="url(#orange)")
    out += solid(lambda **a: rect(34, 36, 172, 188, 14, **a), "page", d)
    out += circle(96, 106, 26, fill="url(#cyan)", stroke=INK, stroke_width=d.w(3))
    out += path("M56,170 Q56,138 96,138 Q136,138 136,170 Z", fill="url(#cyan)",
                stroke=INK, stroke_width=d.w(3))
    if not d.small:
        out += line(146, 100, 186, 100, "#bfefff", 8) + line(146, 128, 180, 128, "#bfefff", 8)
        out += line(56, 196, 186, 196, "#bfefff", 8)
    return out


def i_font_x_generic(d):
    w = d.b(18) if d.small else 18
    return document(d, _strokes("M84,206 L130,92 L176,206 M102,164 H158", d,
                                "#e8f0ff", w), fold="orange")


def i_package_x_generic(d):
    x, y, w, h, dx, dy = 42, 116, 140, 96, 36, 42
    top = poly([(x, y), (x + w, y), (x + w + dx, y - dy), (x + dx, y - dy)])
    side = poly([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy),
                 (x + w, y + h)])
    out = solid(lambda **a: path(side, **a), "red", d, gloss=False)
    out += solid(lambda **a: path(top, **a), "yellow", d, gloss=False)
    out += solid(lambda **a: rect(x, y, w, h, 4, **a), "orange", d)
    tw = d.b(16) if d.small else 18
    out += path(poly([(x + w / 2 - tw / 2, y), (x + w / 2 + tw / 2, y),
                      (x + w / 2 + dx + tw / 2, y - dy), (x + w / 2 + dx - tw / 2, y - dy)]),
                fill="url(#paper)")
    out += rect(x + w / 2 - tw / 2, y, tw, 40, 0, fill="url(#paper)")
    return out


def i_application_x_cd_image(d):
    return document(d, g(i_media_optical(d), "translate(62 80) scale(0.52)"),
                    fold="cyan")


def i_application_x_desktop(d):
    c = rect(80, 92, 100, 80, 6, fill="url(#dark)", stroke="#bfefff",
             stroke_width=d.w(3))
    c += rect(80, 92, 100, 18, 4, fill="url(#body)")
    c += _strokes("M112,206 Q112,166 152,160 M136,142 L156,160 L138,180", d,
                  "#ff9a3c", d.b(11) if d.small else 11)
    return document(d, c, fold="orange")


def i_image_svg_xml(d):
    c = line(84, 196, 96, 120, "#e8f0ff", d.w(3)) + line(176, 108, 162, 184, "#e8f0ff", d.w(3))
    c += _strokes("M84,196 C96,120 162,184 176,108", d, "#7fe6ff",
                  d.b(10) if d.small else 10, ink=False)
    for x, y in ((84, 196), (176, 108)):
        c += rect(x - 11, y - 11, 22, 22, 3, fill="url(#orange)", stroke=INK,
                  stroke_width=d.w(2))
    if not d.small:
        for x, y in ((96, 120), (162, 184)):
            c += circle(x, y, 8, fill="#e8f0ff")
    return document(d, c, fold="orange")


def i_application_x_sqlite3(d):
    out = ""
    for k, y in enumerate((172, 128, 84)):
        out += solid(lambda **a: path(f"M56,{y - 30} V{y + 22} A72,26 0 0 0 200,{y + 22} "
                                      f"V{y - 30} Z", **a), "body", d, gloss=False, rw=4)
        out += ellipse(128, y - 30, 72, 26, fill="url(#cyan)", stroke="url(#rim)",
                       stroke_width=d.w(4))
    return out


def i_application_certificate(d):
    c = doc_lines(d, ys=(92, 116) if not d.small else (100,))
    c += path("M132,170 L118,224 L136,212 L150,226 L152,172 Z", fill="url(#red)")
    c += circle(140, 160, 34, fill="url(#orange)", stroke=INK, stroke_width=d.w(3))
    if not d.small:
        c += circle(140, 160, 20, fill="none", stroke="#ffe7a6", stroke_width=4)
    return document(d, c, fold="orange")


# --------------------------------------------------------------------------
# Program motifs that no generic icon covered (bug report, chat, emoji
# picker, disk usage). Generic on purpose: no program's logo.

def i_tools_report_bug(d):
    """A beetle: crash reporters, debug settings."""
    legs = ("M86,118 L42,98 M80,154 L34,156 M88,190 L48,218 "
            "M170,118 L214,98 M176,154 L222,156 M168,190 L208,218")
    if not d.small:
        legs += " M114,60 Q104,34 80,28 M142,60 Q152,34 176,28"
    w = d.b(12) if d.small else 12
    out = path(legs, fill="none", stroke=INK, stroke_width=w + 8,
               stroke_linecap="round", stroke_linejoin="round")
    out += path(legs, fill="none", stroke="#8fe6ff", stroke_width=w,
                stroke_linecap="round", stroke_linejoin="round")
    out += solid(lambda **a: circle(128, 80, 32, **a), "body", d)
    out += solid(lambda **a: ellipse(128, 156, 64, 78, **a), "violet", d)
    out += line(128, 84, 128, 230, INK, d.w(5))
    if not d.small:
        for x, y, r in ((100, 132, 12), (156, 132, 12), (104, 184, 10), (152, 184, 10)):
            out += circle(x, y, r, fill="url(#orange)", stroke=INK, stroke_width=3)
    return out


def _bubble(x, y, w, h, r, t1, t2, tip):
    """Rounded speech bubble; the tail leaves the bottom edge between
    t1 < t2 and ends at tip."""
    return (f"M{x + r},{y} H{x + w - r} Q{x + w},{y} {x + w},{y + r} "
            f"V{y + h - r} Q{x + w},{y + h} {x + w - r},{y + h} H{t2} "
            f"L{tip[0]},{tip[1]} L{t1},{y + h} H{x + r} Q{x},{y + h} {x},{y + h - r} "
            f"V{y + r} Q{x},{y} {x + r},{y} Z")


def i_internet_chat(d):
    """Two speech bubbles: messengers, IRC, Matrix, SMS."""
    back = _bubble(98, 30, 136, 100, 26, 184, 210, (226, 168))
    front = _bubble(22, 86, 156, 112, 28, 54, 86, (40, 230))
    out = solid(lambda **a: path(back, **a), "violet", d)
    out += solid(lambda **a: path(front, **a), "paper", d, rw=4)
    for x in (62, 100, 138):
        out += circle(x, 142, d.b(13) if d.small else 13, fill="url(#body)")
    return out


def i_preferences_desktop_emoticons(d):
    """A smiling face: the emoji picker."""
    out = solid(lambda **a: circle(128, 128, 100, **a), "yellow", d)
    out += ellipse(94, 100, 13, 20, fill=INK) + ellipse(162, 100, 13, 20, fill=INK)
    out += path("M70,148 Q128,212 186,148", fill="none", stroke=INK,
                stroke_width=d.b(14) if d.small else 14, stroke_linecap="round")
    return out


def i_office_chart_pie(d):
    """A pie with one slice pulled out: disk usage, statistics."""
    cx, cy, r = 116, 140, 92
    p30 = (cx + r * math.cos(math.radians(30)), cy + r * math.sin(math.radians(30)))
    p150 = (cx + r * math.cos(math.radians(150)), cy + r * math.sin(math.radians(150)))
    rest = f"M{cx},{cy} L{p30[0]:.1f},{p30[1]:.1f} A{r},{r} 0 1 1 {cx},{cy - r} Z"
    part = f"M{cx},{cy} L{p150[0]:.1f},{p150[1]:.1f} A{r},{r} 0 0 1 {cx},{cy - r} Z"
    sx, sy = cx + 16, cy - 10
    q30 = (sx + r * math.cos(math.radians(30)), sy + r * math.sin(math.radians(30)))
    slice_ = f"M{sx},{sy} L{sx},{sy - r} A{r},{r} 0 0 1 {q30[0]:.1f},{q30[1]:.1f} Z"
    out = solid(lambda **a: path(rest, **a), "body", d)
    out += solid(lambda **a: path(part, **a), "cyan", d, gloss=False, rw=4)
    out += solid(lambda **a: path(slice_, **a), "orange", d)
    return out


# --------------------------------------------------------------------------
# Tube icons (status, actions): one glowing line in cyan, accents orange/red.
# Drawn on the same 256 grid; d.t is the tube width for the target size.

NEON = "url(#tube)"
ORANGE = "#ffa046"
RED = "#ff5468"
GREEN = "#3ee0a0"
CORE = {NEON: "#effdff", ORANGE: "#fff1dc", RED: "#ffe3e6", GREEN: "#e6fff4"}
DIM = 0.28
BG_CUT = "#0c1438"   # cuts a gap under slashes; the set targets this ground


def tube(dd, d, col=NEON, w=None, core=True, **a):
    w = w or d.t
    st = dict(fill="none", stroke_linecap="round", stroke_linejoin="round")
    out = path(dd, stroke=col, stroke_width=w, **st, **a)
    if core and d.size >= 48 and col in CORE:
        # a pale core makes the big sizes read as a lit tube
        rest = {k: v for k, v in a.items() if k != "opacity"}
        out += path(dd, stroke=CORE[col], stroke_width=round(w * 0.34, 2),
                    opacity=round(0.85 * float(a.get("opacity", 1)), 3), **st, **rest)
    return out


def dot(cx, cy, r, col=NEON, **a):
    return circle(cx, cy, r, fill=col, **a)


def slash(d, col=ORANGE):
    dd = "M52,52 L204,204"
    return (tube(dd, d, BG_CUT, w=d.t * 2.2, core=False) + tube(dd, d, col))


def rot(body, deg):
    return g(body, f"rotate({deg} 128 128)")


ARROW = "M44,128 H204 M140,64 L204,128 L140,192"
CHEVRON = "M92,52 L168,128 L92,204"


def i_go_next(d): return tube(ARROW, d)
def i_go_previous(d): return rot(tube(ARROW, d), 180)
def i_go_up(d): return rot(tube(ARROW, d), -90)
def i_go_down(d): return rot(tube(ARROW, d), 90)
def i_arrow_right(d): return tube(CHEVRON, d)
def i_arrow_left(d): return rot(tube(CHEVRON, d), 180)
def i_arrow_up(d): return rot(tube(CHEVRON, d), -90)
def i_arrow_down(d): return rot(tube(CHEVRON, d), 90)


def i_go_home(d):
    return tube("M36,124 L128,44 L220,124 M68,100 V214 H188 V100 "
                "M110,214 V160 H146 V214", d)


def i_document_new(d):
    return (tube("M128,30 H62 V226 H118 M128,30 L192,94 V124 M128,30 V94 H192", d) +
            tube("M184,148 V224 M146,186 H222", d, ORANGE))


def i_document_open(d):
    return tube("M36,200 V56 H100 L122,78 H196 V112 M36,200 L70,120 H230 L196,200 Z", d)


def i_document_save(d):
    return tube("M44,40 H176 L216,80 V216 H44 Z M88,40 V92 H164 V40 "
                "M84,216 V150 H176 V216", d)


def i_document_print(d):
    out = tube("M80,100 V36 H176 V100 M76,180 H40 V100 H216 V180 H180 "
               "M80,148 H176 V224 H80 Z", d)
    return out + dot(190, 126, d.t * 0.7, ORANGE)


def i_document_open_recent(d):
    return tube(arc(128, 128, 92, 0, 359.9) + " Z", d) + tube("M128,72 V128 L170,154", d)


def i_document_edit(d):
    return tube("M48,208 L62,156 L172,46 L210,84 L100,194 Z M148,70 L186,108", d)


def i_edit_copy(d):
    return tube("M96,84 V36 H212 V176 H164 M44,84 H164 V224 H44 Z", d)


def i_edit_cut(d):
    return tube("M104,160 L186,36 M152,160 L70,36", d) + tube(
        arc(80, 190, 32, 0, 359.9) + arc(176, 190, 32, 0, 359.9), d, ORANGE)


def i_edit_paste(d):
    out = tube("M88,54 H60 V228 H196 V54 H168", d)
    out += tube("M100,36 H156 V74 H100 Z", d, ORANGE)
    return out + tube("M92,126 H164 M92,174 H140", d)


def i_edit_delete(d):
    return tube("M40,68 H216 M100,68 V40 H156 V68 M64,68 L80,226 H176 L192,68 "
                "M110,108 V188 M146,108 V188", d)


UNDO = "M78,96 H156 A56,56 0 0 1 156,208 H104 M120,52 L76,96 L120,140"


def i_edit_undo(d): return tube(UNDO, d)
def i_edit_redo(d): return g(tube(UNDO, d), "translate(256 0) scale(-1 1)")


def i_edit_clear(d):
    return (tube("M90,56 H218 V200 H90 L30,128 Z", d) +
            tube("M126,96 L182,160 M182,96 L126,160", d, ORANGE))


def i_edit_select_all(d):
    return (tube("M40,40 H216 V216 H40 Z", d, stroke_dasharray="30 26") +
            tube("M96,96 H160 V160 H96 Z", d, ORANGE))


def _lens(d, extra=""):
    return tube(arc(110, 110, 70, 0, 359.9) + " Z" + extra, d) + tube(
        "M162,162 L218,218", d, w=d.t * 1.5)


def i_edit_find(d): return _lens(d)
def i_zoom_in(d): return _lens(d, " M110,80 V140 M80,110 H140")
def i_zoom_out(d): return _lens(d, " M80,110 H140")
def i_list_add(d): return tube("M128,40 V216 M40,128 H216", d)
def i_list_remove(d): return tube("M40,128 H216", d)


def i_view_refresh(d):
    return tube(arc(128, 128, 84, -30, 240) + arrow_head(128, 128, 84, 240, 56), d)


def i_view_list_details(d):
    out = ""
    for y in (60, 128, 196):
        out += dot(52, y, d.t * 0.95) + tube(f"M96,{y} H216", d)
    return out


def i_view_list_icons(d):
    return tube("".join(f"M{x},{y} h68 v68 h-68 Z" for x in (40, 148)
                        for y in (40, 148)), d)


def i_view_list_tree(d):
    return tube("M40,32 H100 V76 H40 Z M70,76 V192 M70,132 H122 M70,192 H122 "
                "M136,112 H216 V152 H136 Z M136,172 H216 V212 H136 Z", d)


EYE = "M22,128 Q128,24 234,128 Q128,232 22,128 Z"


def i_view_visible(d):
    return tube(EYE, d) + dot(128, 128, 30)


def i_view_hidden(d):
    return tube(EYE, d) + dot(128, 128, 30) + slash(d)


def i_view_fullscreen(d):
    return tube("M40,96 V40 H96 M160,40 H216 V96 M216,160 V216 H160 M96,216 H40 V160", d)


def i_view_split_left_right(d):
    return tube("M32,48 H224 V208 H32 Z M128,48 V208", d)


def i_configure(d):
    n = 6 if d.small else 8
    return tube(gear_d(128, 128, 100, 74, n, 30), d)


def i_application_menu(d):
    return tube("M44,68 H212 M44,128 H212 M44,188 H212", d)


def i_overflow_menu(d):
    return "".join(dot(128, y, d.t * 1.0) for y in (56, 128, 200))


def i_window_close(d): return tube("M60,60 L196,196 M196,60 L60,196", d)
def i_window_minimize(d): return tube("M52,190 H204", d)
def i_window_maximize(d): return tube("M48,48 H208 V208 H48 Z", d)


def i_window_restore(d):
    return tube("M96,96 V40 H216 V160 H160 M40,96 H160 V216 H40 Z", d)


def i_window_pin(d):
    return tube("M88,40 H168 M106,40 V102 L72,142 H184 L150,102 V40 M128,142 V226", d)


def i_folder_new(d):
    return (tube("M28,204 V54 H96 L118,76 H228 V122 M28,204 H130", d) +
            tube("M186,140 V224 M144,182 H228", d, ORANGE))


def _star(cx, cy, R, r):
    pts = [(cx + (R if i % 2 == 0 else r) * math.cos(math.radians(-90 + i * 36)),
            cy + (R if i % 2 == 0 else r) * math.sin(math.radians(-90 + i * 36)))
           for i in range(10)]
    return poly(pts)


def i_bookmarks(d): return tube(_star(128, 136, 104, 44), d)
def i_dialog_ok(d): return tube("M40,134 L100,194 L218,70", d, GREEN)


def i_dialog_cancel(d):
    return tube(arc(128, 128, 90, 0, 359.9) + " Z M64,192 L192,64", d, RED)


def i_media_playback_start(d): return tube("M76,46 L206,128 L76,210 Z", d)
def i_media_playback_pause(d): return tube("M88,52 V204 M168,52 V204", d)
def i_media_playback_stop(d): return tube("M58,58 H198 V198 H58 Z", d)
def i_media_skip_forward(d): return tube("M48,56 L150,128 L48,200 Z M200,56 V200", d)


def i_media_skip_backward(d):
    return g(i_media_skip_forward(d), "translate(256 0) scale(-1 1)")


def i_media_eject(d): return tube("M128,46 L210,142 H46 Z M46,202 H210", d)


def _ring(d, col=NEON):
    return tube(arc(128, 128, 96, 0, 359.9) + " Z", d, col)


def i_help_about(d):
    return _ring(d) + dot(128, 76, d.t * 0.9) + tube("M128,118 V190", d)


def i_dialog_warning(d):
    return (tube("M128,30 L230,212 H26 Z", d, ORANGE) + tube("M128,96 V146", d, ORANGE) +
            dot(128, 182, d.t * 0.8, ORANGE))


def i_dialog_error(d):
    return _ring(d, RED) + tube("M88,88 L168,168 M168,88 L88,168", d, RED)


def i_dialog_question(d):
    return (_ring(d) + tube("M96,100 Q96,64 128,64 Q162,64 162,98 Q162,120 140,132 "
                            "Q128,140 128,156", d) + dot(128, 190, d.t * 0.8))


def i_dialog_positive(d):
    return _ring(d, GREEN) + tube("M80,132 L114,166 L176,96", d, GREEN)


# status ---------------------------------------------------------------------

SPEAKER = "M28,100 H64 L112,58 V198 L64,156 H28 Z"


def volume(d, level):
    out = tube(SPEAKER, d)
    if level == "muted":
        return out + tube("M154,98 L214,158 M214,98 L154,158", d, RED)
    lit = {"low": 1, "medium": 2, "high": 3}[level]
    for i, r in enumerate((46, 82, 118)):
        out += tube(arc(110, 128, r, -48, 48), d, opacity=1 if i < lit else DIM)
    return out


def mic(d, level):
    out = tube("M98,58 A30,30 0 0 1 158,58 V118 A30,30 0 0 1 98,118 Z", d)
    out += tube("M62,112 V124 A66,66 0 0 0 194,124 V112 M128,190 V226 M90,226 H166", d)
    if level == "muted":
        return out + slash(d, RED)
    frac = {"low": 0.34, "medium": 0.67, "high": 1.0}[level]
    top = 136 - frac * 78
    out += path(f"M112,{top:.0f} H144 V128 A16,16 0 0 1 112,128 Z", fill=NEON)
    return out


def wifi(d, lit):
    """Dot plus four arcs; lit = how many of the five are bright."""
    out = dot(128, 204, d.t * 1.1, opacity=1 if lit >= 1 else DIM)
    for i, r in enumerate((46, 84, 122, 160)):
        out += tube(arc(128, 214, r, -128, -52), d, opacity=1 if lit >= i + 2 else DIM)
    return out


PLUG = "M80,40 H176 V140 H80 Z M108,140 V172 H148 V140"


def i_network_wired_activated(d):
    out = tube(PLUG + " M128,172 V228", d)
    if not d.small:
        out += tube("M106,40 V76 M128,40 V76 M150,40 V76", d, ORANGE, w=d.t * 0.6)
    return out


def i_network_wired_disconnected(d):
    return tube(PLUG + " M128,172 V228", d, opacity=0.55) + slash(d)


def i_network_offline(d):
    out = tube(arc(128, 128, 94, 0, 359.9) + " Z M34,128 H222", d)
    out += tube("M128,34 Q66,128 128,222 Q190,128 128,34", d)
    return out + slash(d)


def battery(d, level, charging):
    out = tube("M30,80 H198 V176 H30 Z", d)
    out += rect(204, 108, 20, 40, 6, fill=NEON)
    col = RED if level <= 10 else ORANGE if level <= 20 else NEON
    inner = 198 - 30 - 2 * d.t - 16
    wfill = max(0, inner * level / 100)
    if level > 0:
        out += rect(30 + d.t + 8, 80 + d.t + 8, max(wfill, 10),
                    96 - 2 * d.t - 16, 4, fill=col)
    if charging:
        # inside the frame, so the cut around it never breaks the outline
        bolt = "M124,88 L94,134 H116 L108,170 L142,120 H120 Z"
        out += path(bolt, fill=BG_CUT, stroke=BG_CUT, stroke_width=d.t * 1.1,
                    stroke_linejoin="round")
        out += path(bolt, fill=ORANGE, stroke=ORANGE, stroke_width=d.t * 0.4,
                    stroke_linejoin="round")
    return out


def i_battery_missing(d):
    return (tube("M30,80 H198 V176 H30 Z", d, opacity=0.55) +
            rect(204, 108, 20, 40, 6, fill=NEON, opacity=0.55) +
            tube("M90,104 L138,152 M138,104 L90,152", d, RED))


def link(d, state):
    w = d.t
    out = _link(d, NEON, NEON, w)
    if state == "inactive":
        return g(out, opacity=0.55) + slash(d)
    if state == "activated":
        out += dot(206, 50, d.t * 1.1, ORANGE)
    return out


def bell(d, state):
    out = tube(BELL, d)
    out += tube("M106,210 Q128,232 150,210", d)
    if state == "active":
        out += dot(204, 58, d.t * 1.4, ORANGE)
    if state == "disabled":
        out += slash(d)
    return out


# --------------------------------------------------------------------------
# Catalogue

# name -> context; the drawing is i_<name> (- and + as _) or a PARAM entry
ICON_CONTEXT = {
    "places": ["folder", "folder-open", "user-home", "user-desktop",
               "folder-documents", "folder-download", "folder-music",
               "folder-pictures", "folder-videos", "folder-templates",
               "folder-publicshare", "folder-remote", "folder-root",
               "folder-recent", "folder-favorites", "folder-cloud",
               "folder-development", "folder-locked", "user-trash",
               "user-trash-full", "network-workgroup", "start-here-kde"],
    "devices": ["computer", "computer-laptop", "network-server",
                "drive-harddisk", "drive-removable-media", "drive-optical",
                "media-optical", "printer", "scanner", "input-keyboard",
                "input-mouse", "input-gaming", "audio-card",
                "audio-headphones", "audio-input-microphone", "video-display",
                "smartphone", "camera-photo", "cpu", "memory", "network-wired",
                "network-wireless", "battery"],
    "apps": ["system-file-manager", "utilities-terminal",
             "internet-web-browser", "internet-mail", "preferences-system",
             "systemsettings", "accessories-text-editor",
             "accessories-calculator", "accessories-screenshot",
             "office-calendar", "multimedia-volume-control", "image-viewer",
             "document-viewer", "utilities-system-monitor",
             "system-software-install", "help-browser",
             "applications-games", "applications-multimedia",
             "applications-office", "applications-internet",
             "applications-utilities", "applications-system",
             "applications-development", "applications-education",
             "applications-graphics", "applications-science",
             "applications-other",
             "system-shutdown", "system-reboot", "system-log-out",
             "system-suspend", "system-switch-user", "system-lock-screen",
             "system-search", "system-users",
             "preferences-desktop", "preferences-desktop-display",
             "preferences-desktop-theme-global", "preferences-desktop-font",
             "preferences-desktop-locale",
             "preferences-desktop-notification-bell",
             "preferences-desktop-accessibility", "preferences-desktop-effects",
             "preferences-desktop-virtual", "preferences-security",
             "preferences-system-bluetooth", "preferences-system-time",
             "preferences-system-windows",
             "tools-report-bug", "internet-chat", "preferences-desktop-emoticons",
             "office-chart-pie"],
    "mimetypes": ["text-plain", "text-html", "text-x-script", "text-x-csrc",
                  "text-markdown", "x-office-document", "x-office-spreadsheet",
                  "x-office-presentation", "x-office-drawing",
                  "x-office-address-book", "application-pdf",
                  "image-x-generic", "image-svg+xml", "audio-x-generic",
                  "video-x-generic", "font-x-generic",
                  "application-x-archive", "package-x-generic",
                  "application-x-cd-image", "application-x-executable",
                  "application-x-desktop", "application-x-sqlite3",
                  "application-certificate", "unknown"],
    "actions": ["go-previous", "go-next", "go-up", "go-down", "go-home",
                "arrow-left", "arrow-right", "arrow-up", "arrow-down",
                "document-new", "document-open", "document-save",
                "document-print", "document-open-recent", "document-edit",
                "edit-copy", "edit-cut", "edit-paste", "edit-delete",
                "edit-undo", "edit-redo", "edit-clear", "edit-select-all",
                "edit-find", "zoom-in", "zoom-out", "list-add", "list-remove",
                "view-refresh", "view-list-details", "view-list-icons",
                "view-list-tree", "view-visible", "view-hidden",
                "view-fullscreen", "view-split-left-right", "configure",
                "application-menu", "overflow-menu", "window-close",
                "window-minimize", "window-maximize", "window-restore",
                "window-pin", "folder-new", "bookmarks", "dialog-ok",
                "dialog-cancel", "help-about", "media-playback-start",
                "media-playback-pause", "media-playback-stop",
                "media-skip-forward", "media-skip-backward", "media-eject"],
    "status": ["audio-volume-high", "audio-volume-medium", "audio-volume-low",
               "audio-volume-muted", "microphone-sensitivity-high",
               "microphone-sensitivity-medium", "microphone-sensitivity-low",
               "microphone-sensitivity-muted"] +
              [f"network-wireless-{n}" for n in (0, 20, 40, 60, 80, 100)] +
              ["network-wireless-disconnected", "network-wired-activated",
               "network-wired-disconnected", "network-offline"] +
              [f"battery-{n:03d}{c}" for n in range(0, 101, 10)
               for c in ("", "-charging")] +
              ["battery-missing", "network-bluetooth",
               "network-bluetooth-activated", "network-bluetooth-inactive",
               "notifications", "notification-active", "notifications-disabled",
               "dialog-information", "dialog-warning", "dialog-error",
               "dialog-question", "dialog-positive"],
}
# drawn as tubes: these also get <name>-symbolic aliases
TUBE_CONTEXTS = ("actions", "status")

PARAM = {"start-here-kde": i_start_here,
         "dialog-information": i_help_about,
         "network-bluetooth": lambda d: link(d, "on"),
         "network-bluetooth-activated": lambda d: link(d, "activated"),
         "network-bluetooth-inactive": lambda d: link(d, "inactive"),
         "notifications": lambda d: bell(d, "on"),
         "notification-active": lambda d: bell(d, "active"),
         "notifications-disabled": lambda d: bell(d, "disabled")}
for _lv in ("high", "medium", "low", "muted"):
    PARAM[f"audio-volume-{_lv}"] = (lambda lv: lambda d: volume(d, lv))(_lv)
    PARAM[f"microphone-sensitivity-{_lv}"] = (lambda lv: lambda d: mic(d, lv))(_lv)
for _i, _n in enumerate((0, 20, 40, 60, 80, 100)):
    PARAM[f"network-wireless-{_n}"] = (lambda k: lambda d: wifi(d, k))(_i)
PARAM["network-wireless-disconnected"] = lambda d: wifi(d, 0) + slash(d)
for _n in range(0, 101, 10):
    PARAM[f"battery-{_n:03d}"] = (lambda n: lambda d: battery(d, n, False))(_n)
    PARAM[f"battery-{_n:03d}-charging"] = (lambda n: lambda d: battery(d, n, True))(_n)

# (context, alias) -> target name; the target's context is looked up
_A = {
    "places": {
        "start-here": "start-here-kde", "folder-downloads": "folder-download",
        "folder-image": "folder-pictures", "folder-images": "folder-pictures",
        "folder-video": "folder-videos", "folder-sound": "folder-music",
        "folder-text": "folder-documents", "folder-network": "folder-remote",
        "folder-home": "user-home", "desktop": "user-desktop",
        "folder-drag-accept": "folder-open", "folder-open-recent": "folder-recent",
        "folder-bookmark": "folder-favorites", "folder-favorite": "folder-favorites",
        "folder-encrypted": "folder-locked", "folder-cloud-services": "folder-cloud",
        "folder-script": "folder-development", "folder-public": "folder-publicshare",
        "network-server": "network-server", "user-bookmarks": "folder-favorites",
        "user-trash-symbolic": "user-trash", "folder-symbolic": "folder",
        "folder-root-symbolic": "folder-root",
    },
    "devices": {
        "drive-removable-media-usb": "drive-removable-media",
        "drive-removable-media-usb-pendrive": "drive-removable-media",
        "drive-removable-media-symbolic": "drive-removable-media",
        "media-flash": "drive-removable-media", "media-removable": "drive-removable-media",
        "drive-harddisk-root": "drive-harddisk", "drive-harddisk-solidstate": "drive-harddisk",
        "drive-multidisk": "drive-harddisk", "drive-harddisk-system": "drive-harddisk",
        "drive-partition": "drive-harddisk", "computer-symbolic": "computer",
        "audio-speakers": "multimedia-volume-control", "audio-headset": "audio-headphones",
        "audio-input-microphone-symbolic": "audio-input-microphone",
        "network-wireless-connected": "network-wireless", "network-card": "network-wired",
        "phone": "smartphone", "camera-web": "camera-photo", "input-touchpad": "input-mouse",
        "input-gamepad": "input-gaming", "display": "video-display", "monitor": "video-display",
        "printer-symbolic": "printer", "network-wired-symbolic": "network-wired",
        "media-optical-audio": "media-optical", "media-optical-cd": "media-optical",
        "media-optical-dvd": "media-optical", "drive-optical-symbolic": "drive-optical",
        "battery-symbolic": "battery",
    },
    "apps": {
        "org.kde.dolphin": "system-file-manager", "org.kde.konsole": "utilities-terminal",
        "org.kde.kcalc": "accessories-calculator", "org.kde.kate": "accessories-text-editor",
        "org.kde.kwrite": "accessories-text-editor", "kate": "accessories-text-editor",
        "org.kde.okular": "document-viewer", "okular": "document-viewer",
        "org.kde.gwenview": "image-viewer", "gwenview": "image-viewer",
        "org.kde.spectacle": "accessories-screenshot", "spectacle": "accessories-screenshot",
        "org.kde.ark": "application-x-archive", "ark": "application-x-archive",
        "utilities-file-archiver": "application-x-archive",
        "org.kde.discover": "system-software-install", "plasmadiscover": "system-software-install",
        "system-software-update": "system-software-install",
        "org.kde.plasma-systemmonitor": "utilities-system-monitor",
        "ksysguard": "utilities-system-monitor", "org.kde.systemsettings": "systemsettings",
        "org.kde.kinfocenter": "help-browser", "web-browser": "internet-web-browser",
        "mail-client": "internet-mail", "internet-mail": "internet-mail",
        "applications-all": "applications-other", "applications-accessories": "applications-utilities",
        "applications-engineering": "applications-science",
        "applications-education-science": "applications-science",
        "applications-education-mathematics": "applications-education",
        "applications-education-language": "applications-education",
        "applications-network": "applications-internet",
        "preferences-system-windows-actions": "preferences-system-windows",
        "preferences-system-windows-effect": "preferences-system-windows",
        "preferences-desktop-theme-windowdecorations": "preferences-system-windows",
        "preferences-system-tabbox": "preferences-system-windows", "kwin": "preferences-system-windows",
        "preferences-desktop-theme": "preferences-desktop-theme-global",
        "preferences-desktop-plasma-theme": "preferences-desktop-theme-global",
        "preferences-desktop-theme-applications": "preferences-desktop-theme-global",
        "preferences-desktop-color": "preferences-desktop-theme-global",
        "preferences-desktop-wallpaper": "preferences-desktop",
        "preferences-desktop-icons": "applications-other",
        "preferences-desktop-font-installer": "preferences-desktop-font",
        "preferences-desktop-keyboard": "input-keyboard",
        "preferences-desktop-keyboard-shortcut": "input-keyboard",
        "preferences-desktop-peripherals": "input-keyboard",
        "preferences-desktop-mouse": "input-mouse", "preferences-desktop-touchpad": "input-mouse",
        "preferences-desktop-cursors": "input-mouse",
        "preferences-desktop-sound": "multimedia-volume-control",
        "preferences-desktop-multimedia": "multimedia-volume-control",
        "preferences-desktop-notification": "preferences-desktop-notification-bell",
        "preferences-desktop-user": "system-users", "preferences-system-users": "system-users",
        "preferences-desktop-user-password": "system-users", "user-identity": "system-users",
        "preferences-system-login": "system-users",
        "preferences-desktop-animations": "preferences-desktop-effects",
        "preferences-desktop-activities": "preferences-desktop-virtual",
        "preferences-desktop-display-randr": "preferences-desktop-display",
        "preferences-desktop-gaming": "applications-games",
        "preferences-desktop-default-applications": "applications-other",
        "preferences-system-network": "network-workgroup",
        "preferences-system-network-connection": "network-workgroup",
        "preferences-system-network-proxy": "network-workgroup",
        "preferences-system-network-remote": "network-workgroup",
        "preferences-system-network-sharing": "network-workgroup",
        "preferences-online-accounts": "applications-internet",
        "preferences-system-power-management": "battery",
        "preferences-system-disks": "drive-harddisk", "preferences-devices-printer": "printer",
        "preferences-devices-cpu": "cpu", "preferences-desktop-search": "system-search",
        "plasma-search": "system-search", "krunner": "system-search",
        "preferences-system-session-services": "applications-system",
        "preferences-system-splash": "start-here-kde", "preferences-other": "preferences-system",
        "preferences-system-bluetooth-activated": "preferences-system-bluetooth",
        "bluetooth": "preferences-system-bluetooth", "clock": "preferences-system-time",
        "preferences-system-windows": "preferences-system-windows",
        "utilities-system-monitor": "utilities-system-monitor",
        "system-run": "application-x-executable",
    },
    "actions": {
        "system-shutdown": "system-shutdown", "system-reboot": "system-reboot",
        "system-log-out": "system-log-out", "system-suspend": "system-suspend",
        "system-hibernate": "system-suspend", "system-suspend-hibernate": "system-suspend",
        "system-switch-user": "system-switch-user", "system-lock-screen": "system-lock-screen",
        "system-search": "system-search", "help-contents": "help-browser",
        "search": "edit-find", "edit-find-replace": "edit-find", "find-location": "edit-find",
        "document-save-as": "document-save", "document-properties": "configure",
        "settings-configure": "configure", "configure-shortcuts": "configure",
        "view-history": "document-open-recent", "document-edit-sign": "document-edit",
        "edit-rename": "document-edit", "edit-entry": "document-edit",
        "edit-clear-history": "edit-delete", "edit-clear-all": "edit-delete",
        "edit-delete-remove": "edit-delete", "edit-clear-locationbar-rtl": "edit-clear",
        "edit-clear-locationbar-ltr": "edit-clear", "edit-paste-in-place": "edit-paste",
        "open-menu": "application-menu", "hamburger-menu": "application-menu",
        "overflow-menu-left": "overflow-menu", "overflow-menu-right": "overflow-menu",
        "view-more-symbolic": "overflow-menu", "view-more-horizontal-symbolic": "overflow-menu",
        "view-grid": "view-list-icons", "view-list-text": "view-list-details",
        "view-split-top-bottom": "view-split-left-right",
        "view-restore": "window-restore", "view-close": "window-close",
        "dialog-close": "window-close", "tab-close": "window-close",
        "window-unpin": "window-pin", "pin": "window-pin", "window-new": "document-new",
        "tab-new": "list-add", "bookmark-new": "bookmarks", "bookmarks-organize": "bookmarks",
        "favorite": "bookmarks", "emblem-favorite": "bookmarks", "starred": "bookmarks",
        "dialog-ok-apply": "dialog-ok", "dialog-apply": "dialog-ok", "checkmark": "dialog-ok",
        "process-stop": "dialog-cancel", "go-top": "go-up", "go-bottom": "go-down",
        "go-previous-view": "go-previous", "go-next-view": "go-next",
        "go-parent-folder": "go-up", "user-home": "user-home",
        "media-playback-playing": "media-playback-start",
        "media-playback-paused": "media-playback-pause",
        "media-playback-stopped": "media-playback-stop",
        "media-seek-forward": "media-skip-forward", "media-seek-backward": "media-skip-backward",
        "file-new": "document-new", "document-open-folder": "document-open",
        "folder-open-symbolic": "document-open", "go-jump": "go-next",
        "list-add-user": "system-switch-user", "application-exit": "system-log-out",
        "edit-copy-path": "edit-copy", "edit-select": "edit-select-all",
    },
    "status": {
        "audio-volume-high-danger": "audio-volume-high",
        "audio-volume-high-warning": "audio-volume-high",
        "audio-volume-off": "audio-volume-muted",
        "audio-volume-muted-blocking": "audio-volume-muted",
        "microphone-sensitivity-off": "microphone-sensitivity-muted",
        "network-wireless-signal-none": "network-wireless-0",
        "network-wireless-signal-weak": "network-wireless-40",
        "network-wireless-signal-ok": "network-wireless-60",
        "network-wireless-signal-good": "network-wireless-80",
        "network-wireless-signal-excellent": "network-wireless-100",
        "network-wireless-acquiring": "network-wireless-0",
        "network-wireless-off": "network-wireless-disconnected",
        "network-wireless-on": "network-wireless-100",
        "network-wireless-available": "network-wireless-100",
        "network-wireless": "network-wireless-100",
        "network-wired-activated-limited": "network-wired-activated",
        "network-wired-activated-locked": "network-wired-activated",
        "network-wired-available": "network-wired-activated",
        "network-wired-unavailable": "network-wired-disconnected",
        "network-wired": "network-wired-activated",
        "network-connect": "network-wired-activated",
        "network-disconnect": "network-wired-disconnected",
        "network-unavailable": "network-offline", "network-limited": "network-offline",
        "network-bluetooth-activated-locked": "network-bluetooth-activated",
        "notification-inactive": "notifications", "notification-empty": "notifications",
        "notification-disabled": "notifications-disabled",
        "notification-new": "notification-active",
        "klipper": "edit-paste", "edit-paste": "edit-paste",
        "state-ok": "dialog-positive", "state-warning": "dialog-warning",
        "state-error": "dialog-error", "state-information": "dialog-information",
        "dialog-password": "system-lock-screen",
        "battery-missing": "battery-missing", "user-trash-full": "user-trash-full",
        "media-playback-playing": "media-playback-start",
        "media-playback-paused": "media-playback-pause",
        "media-playback-stopped": "media-playback-stop",
    },
}
for _word, _lvl in (("full", 100), ("good", 70), ("low", 30), ("caution", 10),
                   ("empty", 0)):
    _A["status"][f"battery-{_word}"] = f"battery-{_lvl:03d}"
    _A["status"][f"battery-{_word}-charging"] = f"battery-{_lvl:03d}-charging"
for _n in range(0, 101, 10):
    for _p in ("balanced", "performance", "powersave"):
        _A["status"][f"battery-{_n:03d}-profile-{_p}"] = f"battery-{_n:03d}"
        _A["status"][f"battery-{_n:03d}-charging-profile-{_p}"] = f"battery-{_n:03d}-charging"
for _n, _t in ((0, 0), (20, 20), (25, 40), (40, 40), (50, 60), (60, 60), (75, 80),
               (80, 80), (100, 100)):
    _A["status"][f"network-wireless-connected-{_n:02d}"] = f"network-wireless-{_t}"
for _n in (0, 20, 40, 60, 80, 100):
    for _s in ("locked", "limited"):
        _A["status"][f"network-wireless-{_n}-{_s}"] = f"network-wireless-{_n}"

# Program icons: the Icon= names of the .desktop files the menus and the tab
# launcher show (Fedora KDE as installed in the lab VM, plus the KDE/GNOME
# programs Breeze carries an apps/ icon for), each on the drawn motif of its
# kind. Brand programs (Firefox, Thunderbird, LibreOffice, GIMP, ...) get the
# generic motif, never a traced logo. "+name" stands for name and
# org.kde.name. Existing entries above win (setdefault).
_PROGRAMS = {
    "internet-web-browser":
        "firefox org.mozilla.firefox firefox-esr +falkon qupzilla rekonq konqueror "
        "+konqueror +angelfish chromium chromium-browser org.chromium.Chromium "
        "google-chrome com.google.Chrome brave-browser com.brave.Browser "
        "microsoft-edge vivaldi opera epiphany org.gnome.Epiphany "
        "librewolf io.gitlab.librewolf-community plasma-browser-integration",
    "internet-mail":
        "kmail kmail2 org.kde.kmail2 +kontact thunderbird org.mozilla.Thunderbird "
        "net.thunderbird.Thunderbird evolution org.gnome.Evolution geary "
        "org.gnome.Geary kube-mail ktnef +ktnef sieveeditor +sieveeditor "
        "kontact-import-wizard +akonadiimportwizard +pimdataexporter akonadiconsole "
        "+headerthemeeditor trojita claws-mail mail-notification",
    "applications-internet":
        "+akregator +alligator liferea rssguard +ktrip itinerary +itinerary "
        "+kweather +kongress",
    "internet-chat":
        "+konversation +neochat +kopete telepathy-kde internet-telephony im-user "
        "kde-im-log-viewer choqok +tokodon polari org.gnome.Polari pidgin hexchat "
        "org.kde.kdeconnect.sms",
    "smartphone":
        "kdeconnect +kdeconnect org.kde.kdeconnect.app org.kde.kdeconnect.nonplasma "
        "kdeconnectindicator kdeconnectindicatordark plasma-mobile-phone",
    "computer":
        "+krdc remmina org.remmina.Remmina org.gnome.Connections gnome-connections "
        "vinagre virt-manager org.virt_manager.virt-manager gnome-boxes "
        "org.gnome.Boxes virtualbox VirtualBox qemu",
    "network-workgroup":
        "+krfb smb4k +smb4k network-manager nm-connection-editor "
        "preferences-system-network-share",
    "folder-remote": "knetattach +knetattach",
    "folder-download":
        "+ktorrent +kget transmission transmission-qt transmission-gtk "
        "com.transmissionbt.Transmission qbittorrent org.qbittorrent.qBittorrent "
        "deluge",
    "x-office-address-book":
        "kaddressbook +kaddressbook office-address-book contacts org.gnome.Contacts "
        "+contactthemeeditor +contactprintthemeeditor",
    "office-calendar":
        "korganizer +korganizer korgac korg-todo +merkuro org.kde.merkuro.calendar "
        "calindori +calindori zanshin +zanshin +kalarm org.gnome.Calendar "
        "gnome-calendar plan planwork planner calligraplan calligraplanwork kplato "
        "+plan",
    "preferences-system-time":
        "+ktimer +kteatime +kronometer +ktimetracker +kclock org.gnome.clocks "
        "gnome-clocks alarm-clock",
    "x-office-document":
        "libreoffice-writer org.libreoffice.LibreOffice.writer calligrawords words "
        "kword libreoffice-math org.libreoffice.LibreOffice.math abiword",
    "x-office-spreadsheet":
        "libreoffice-calc org.libreoffice.LibreOffice.calc calligrasheets sheets "
        "kspread kchart +kmymoney +skrooge skrooge homebank gnucash org.gnucash.GnuCash "
        "gnumeric",
    "x-office-presentation":
        "libreoffice-impress org.libreoffice.LibreOffice.impress calligrastage "
        "stage kpresenter",
    "x-office-drawing":
        "libreoffice-draw org.libreoffice.LibreOffice.draw karbon calligrakarbon "
        "inkscape org.inkscape.Inkscape",
    "application-x-sqlite3":
        "libreoffice-base org.libreoffice.LibreOffice.base kexi calligrakexi "
        "sqlitebrowser org.sqlitebrowser.sqlitebrowser",
    "applications-office":
        "libreoffice-startcenter libreoffice-main org.libreoffice.LibreOffice "
        "onlyoffice-desktopeditors calligra",
    "document-viewer":
        "graphics-viewer-document evince org.gnome.Evince org.gnome.Papers atril "
        "zathura qpdfview",
    "accessories-text-editor":
        "kwrite +kwrite gedit org.gnome.gedit org.gnome.TextEditor "
        "gnome-text-editor mousepad org.xfce.mousepad featherpad +kile kile "
        "+knotes knotes +kjots kjots +marknote",
    "accessories-calculator":
        "kcalc gnome-calculator org.gnome.Calculator galculator qalculate-qt "
        "+kalk",
    "preferences-desktop-font":
        "accessories-character-map kcharselect +kcharselect kfontview +kfontview "
        "org.gnome.font-viewer gnome-font-viewer gucharmap",
    "accessories-screenshot":
        "accessories-screenshot-tool ksnapshot org.xfce.screenshooter "
        "org.gnome.Screenshot gnome-screenshot flameshot",
    "application-x-archive":
        "file-roller org.gnome.FileRoller xarchiver engrampa",
    "user-trash": "sweeper +sweeper bleachbit",
    "office-chart-pie":
        "filelight +filelight baobab org.gnome.baobab disk-usage-analyzer "
        "qdirstat kdf +kdf",
    "drive-harddisk":
        "partitionmanager +partitionmanager gparted org.gnome.DiskUtility "
        "gnome-disks kfloppy +kfloppy ntfs-config kup +kup deja-dup "
        "org.gnome.DejaDup timeshift backintime",
    "drive-removable-media":
        "usb-creator-kde org.fedoraproject.MediaWriter mediawriter "
        "+isoimagewriter isoimagewriter",
    "system-search":
        "kfind +kfind catfish baloo kmag +kmag org.gnome.Characters",
    "folder-locked":
        "kwalletmanager kwalletmanager2 org.kde.kwalletmanager5 "
        "+kwalletmanager plasmavault seahorse org.gnome.seahorse.Application "
        "keepassxc org.keepassxc.KeePassXC",
    "application-certificate":
        "+kleopatra kgpg +kgpg +kwatchgnupg kwatchgnupg gpa",
    "preferences-security":
        "firewall-config firewall-applet setroubleshoot_icon setroubleshoot "
        "selinux fingerprint-gui",
    "system-users": "kuser +kuser",
    "utilities-system-monitor":
        "ksysguardd gnome-system-monitor org.gnome.SystemMonitor htop btop "
        "utilities-energy-monitor",
    "help-browser":
        "hwinfo kinfocenter khelpcenter +khelpcenter system-help ktip assistant",
    "text-plain":
        "utilities-log-viewer ksystemlog +ksystemlog +kjournaldbrowser "
        "org.gnome.Logs gnome-logs",
    "tools-report-bug":
        "debug-run +kdebugsettings org.freedesktop.GnomeAbrt abrt drkonqi "
        "+drkonqi tools-report-bug-symbolic",
    "system-software-install":
        "muondiscover muon apper org.gnome.Software gnome-software dnfdragora "
        "calamares ubiquity-kde anaconda liveinst",
    "utilities-terminal":
        "konsole yakuake +yakuake xterm org.gnome.Terminal gnome-terminal "
        "org.gnome.Console kgx foot kitty Alacritty xfce4-terminal",
    "system-file-manager":
        "dolphin krusader_user krusader_root +krusader org.gnome.Nautilus "
        "nautilus thunar org.xfce.thunar pcmanfm-qt pcmanfm",
    "applications-multimedia":
        "+elisa elisa +juk juk +amarok amarok +vvave vvave rhythmbox "
        "org.gnome.Rhythmbox3 audacious strawberry clementine lollypop +kasts kasts "
        "kwave +kwave audacity org.audacityteam.Audacity +minuet",
    "video-x-generic":
        "dragonplayer +dragonplayer +haruna haruna vlc org.videolan.VLC mpv smplayer "
        "totem org.gnome.Totem celluloid io.github.celluloid_player.Celluloid "
        "kaffeine +kaffeine kmplayer +kmplayer plasma-media-center "
        "org.gnome.Showtime parole +kdenlive kdenlive shotcut org.shotcut.Shotcut "
        "openshot org.openshot.OpenShot pitivi subtitlecomposer +subtitlecomposer "
        "obs com.obsproject.Studio",
    "multimedia-volume-control":
        "kmix +kmix pavucontrol org.pulseaudio.pavucontrol phonon-gstreamer "
        "easyeffects com.github.wwmm.easyeffects",
    "camera-photo":
        "kamoso +kamoso cheese org.gnome.Cheese org.gnome.Snapshot guvcview "
        "qrca +qrca digikam +digikam kphotoalbum +kphotoalbum shotwell "
        "org.gnome.Shotwell photolayoutseditor",
    "media-optical":
        "k3b +k3b gcdmaster brasero org.gnome.Brasero xfburn",
    "scanner":
        "skanpage +skanpage skanlite +skanlite simple-scan org.gnome.SimpleScan "
        "xsane",
    "image-viewer":
        "showfoto +showfoto eog org.gnome.eog org.gnome.Loupe loupe ristretto "
        "nomacs +koko koko photoqt",
    "applications-graphics":
        "+kolourpaint kolourpaint krita +krita gimp org.gimp.GIMP pinta mypaint "
        "+kxstitch kxstitch kimagemapeditor symboleditor +kcolorchooser "
        "kcolorchooser blender org.blender.Blender +kontrast",
    "applications-utilities":
        "+kruler kruler +krename krename +kbackup",
    "input-mouse": "kmousetool +kmousetool",
    "input-keyboard": "+ktouch ktouch",
    "preferences-desktop-accessibility":
        "kmouth +kmouth orca org.gnome.Orca",
    "preferences-desktop-locale":
        "im-chooser crow-translate org.kde.CrowTranslate +kiten kiten "
        "system-config-language",
    "preferences-desktop-theme-global":
        "kvantum kvantummanager breeze-settings qt5ct qt6ct",
    "preferences-desktop": "latte-dock plank",
    "preferences-desktop-emoticons": "+plasma.emojier",
    "application-x-desktop": "kmenuedit +kmenuedit alacarte",
    "start-here-kde":
        "start-here-kde-plasma +plasma-welcome kde kdeapp kde-frameworks planetkde",
    "printer": "system-config-printer +print-manager printer-settings",
    "applications-other": "+iconexplorer cuttlefish +Ikona",
    "applications-games":
        " ".join("+" + n for n in (
            "kmahjongg kmines kpat ksudoku knights kreversi kblocks kbounce "
            "kbreakout kdiamond kfourinline kapman katomic kblackbox bomber bovo "
            "granatier kiriki kjumpingcube klines kolf kshisen ksirk kspaceduel "
            "ksquares ktuberling kubrick lskat palapeli picmi killbots kgoldrunner "
            "klickety knavalbattle knetwalk kollision konquest ksnakeduel "
            "skladnik kajongg fifteenpuzzle").split()) +
        " kpatience org.gnome.Mines gnome-mines aisleriot sol gnome-chess "
        "org.gnome.Chess steam com.valvesoftware.Steam lutris net.lutris.Lutris "
        "heroic com.heroicgameslauncher.hgl",
    "applications-science":
        "+kalzium kalzium +kstars kstars +step step +kmplot kmplot +kalgebra "
        "kalgebra +kig kig +rocs rocs +cantor cantor +labplot2 labplot2 labplot "
        "+labplot octave",
    "applications-education":
        "+kgeography kgeography +kbruch kbruch +kturtle kturtle +kwordquiz "
        "+parley parley +khangman khangman +kanagram kanagram +artikulate "
        "artikulate +blinken blinken gcompris gcompris-qt +klettres +marble marble",
    "applications-development":
        "+kdevelop kdevelop kapptemplate +umbrello umbrello kompare +kompare "
        "kdiff3 +kdiff3 meld org.gnome.Meld cervisia kdesvn +lokalize lokalize "
        "+okteta okteta kcachegrind +kcachegrind massif-visualizer "
        "+massif-visualizer kuiviewer +kuiviewer designer qtcreator "
        "org.qt-project.qtcreator code com.visualstudio.code codium gitg "
        "kdesrc-build kde-builder +heaptrack linguist kirigami-gallery "
        "+kirigami2.gallery",
}
for _pt, _pns in _PROGRAMS.items():
    for _pn in _pns.split():
        for _pa in ((_pn[1:], "org.kde." + _pn[1:]) if _pn.startswith("+") else (_pn,)):
            if _pa != _pt:
                _A["apps"].setdefault(_pa, _pt)


def _mime_target(n):
    """Map a mimetype icon name onto one of the drawn generic ones."""
    rules = (
        (r"^(inode-directory)$", "folder"),
        (r"(x-trash)$", "user-trash"),
        (r"^(unknown|none|application-octet-stream|application-x-zerosize|"
         r"application-x-partial-download)$", "unknown"),
        (r"(svg|x-eps|illustrator|x-wmf|x-emf|image-x-xfig|vnd\.dgn|vnd\.dwg)",
         "image-svg+xml"),
        (r"^image-", "image-x-generic"),
        (r"^(audio-|audiobook|podcast|x-media-podcast|application-ogg|application-x-cda)",
         "audio-x-generic"),
        (r"^(video-|application-x-flash-video|application-vnd\.rn-realmedia|"
         r"application-x-mplayer2|application-x-kdenlive)", "video-x-generic"),
        (r"(font|fonts-package)", "font-x-generic"),
        (r"(pgp|pkcs|x509|pem-key|certificate|pkix|encrypted|keygroup)",
         "application-certificate"),
        (r"(spreadsheet|excel|calc|xls|xlt|gnumeric|text-csv|quattropro|"
         r"opendocument\.chart|kmymoney|skg)", "x-office-spreadsheet"),
        (r"(presentation|powerpoint|impress|ppt|pot)", "x-office-presentation"),
        (r"(drawing|draw|graphics|visio|opendocument\.image|kontour|tgif|scribus|"
         r"publisher|krita|blender)", "x-office-drawing"),
        (r"(sqlite|database|ms-access|kexi|application-sql|text-x-sql|rdata)",
         "application-x-sqlite3"),
        (r"(vcard|address|contact|text-directory|distribution-list|ldif)",
         "x-office-address-book"),
        (r"(calendar|vcalendar)", "office-calendar"),
        (r"(rpm|deb|flatpak|snap|appimage|android|xz-pkg|msi|xpinstall|"
         r"extension|package)", "package-x-generic"),
        (r"(cd-image|iso|raw-disk-image|qemu-disk|vdi|virtualbox|cue|"
         r"apple-diskimage|ms-wim|squashfs)", "application-x-cd-image"),
        (r"(zip|rar|7z|tar|gzip|bzip|xz|lzma|compress|cpio|-ar$|arj|lha|zoo|ace|"
         r"-arc$|jar|java-archive|lzop|tzo|pak|archive|mimearchive)",
         "application-x-archive"),
        (r"(pdf|postscript|viewps|dvi|djvu|chm)", "application-pdf"),
        (r"(desktop|ms-shortcut|mswinurl|kexiproject-shortcut|x-theme|x-plasma)",
         "application-x-desktop"),
        (r"(executable$|ms-dos-executable|msdownload|sharedlib|x-object|x-core|"
         r"python-bytecode|nes-rom|gba-rom|n64-rom|gameboy|gamecube|nintendo|snes)",
         "application-x-executable"),
        (r"(shellscript|executable-script|perl|ruby|awk|m4|tcl|text-x-script|"
         r"makefile|cmake|dockerfile|rpm-spec|php)", "text-x-script"),
        (r"(html|xml|xsd|xslt|rss|atom|mathml|relaxng|dtd|sgml|rdf|opml|wml|"
         r"xliff|kml|vnd\.nokia)", "text-html"),
        (r"(markdown|text-wiki)", "text-markdown"),
        (r"(src|hdr|java|javascript|python|rust|text-x-go|csharp|kotlin|scala|"
         r"haskell|lua|nim|pascal|fortran|qml|text-x-r$|sass|scss|text-css|json|"
         r"toml|gdscript|godot|designer|adasrc|typst|text-x-objc|kcsrc|linguist)",
         "text-x-csrc"),
        (r"(msword|ms-word|wordprocessing|opendocument\.text|writer|wps-office\.do|"
         r"rtf|abiword|kword|mswrite|wordperfect|enriched|epub|fictionbook|lyx|"
         r"text-x-tex|bibtex|texinfo|libreoffice-(oasis-)?(text|master)|"
         r"x-office-document|odf|formula|math|lilypond|vnd\.abc|msonenote)",
         "x-office-document"),
        (r"^(text-|message|application-x-gettext|application-x-troff|"
         r"application-x-srt|application-x-subrip)", "text-plain"),
    )
    for rx, target in rules:
        if re.search(rx, n):
            return target
    return None


def _mime_aliases():
    # Breeze's mimetype names (names only), so Dolphin finds ours before
    # falling through to Breeze Dark for a specific type
    f = pathlib.Path(__file__).resolve().parent / "icons-neon" / "mimetype-names.txt"
    out = {}
    drawn = set(ICON_CONTEXT["mimetypes"])
    for n in f.read_text().split():
        if n in drawn:
            continue
        t = _mime_target(n)
        if t:
            out[n] = t
    return out


def all_aliases():
    """(context, alias) -> (target context, target)."""
    where = {n: c for c, ns in ICON_CONTEXT.items() for n in ns}
    res = {}
    al = {c: dict(v) for c, v in _A.items()}
    al["mimetypes"] = _mime_aliases()
    for ctx, m in al.items():
        for a, t in m.items():
            if a in where and where[a] == ctx:
                continue                # drawn here already
            if t not in where:
                raise KeyError(f"alias {a} -> {t}: no such icon")
            res[(ctx, a)] = (where[t], t)
    # -symbolic twins for the tube icons and their aliases
    for (ctx, a), tgt in list(res.items()):
        if tgt[0] in TUBE_CONTEXTS and not a.endswith("-symbolic"):
            res.setdefault((ctx, a + "-symbolic"), tgt)
    for ctx in TUBE_CONTEXTS:
        for n in ICON_CONTEXT[ctx]:
            res.setdefault((ctx, n + "-symbolic"), (ctx, n))
    # names in two contexts would be ambiguous for the loader
    names = {}
    for (ctx, a) in list(res):
        if a in where or a in names:
            del res[(ctx, a)]
        else:
            names[a] = ctx
    return res


# drawings that reach too far out for the glow: shrunk about the centre
FIT = {"input-gaming": 0.88, "memory": 0.9, "audio-input-microphone": 0.92,
       "smartphone": 0.92, "accessories-screenshot": 0.92,
       "system-software-install": 0.92, "applications-education": 0.9,
       "x-office-presentation": 0.92, "view-visible": 0.9, "view-hidden": 0.9,
       "tools-report-bug": 0.9, "internet-chat": 0.92, "office-chart-pie": 0.92}


def icon_fn(name):
    fn = PARAM.get(name) or globals()["i_" + re.sub(r"[-+.]", "_", name)]
    if name in FIT:
        k = FIT[name]
        return lambda d: g(fn(d), f"translate({128 * (1 - k):.1f} {128 * (1 - k):.1f}) "
                                  f"scale({k})")
    return fn


def svg_doc(body, glow=None):
    """A complete SVG; glow is an optional PNG (bytes) laid under the body."""
    ids = sorted(set(re.findall(r"url\(#([\w-]+)\)", body)))
    defs = "".join(GRADS[i] for i in ids if i in GRADS)
    img = ""
    if glow:
        img = ('<image x="0" y="0" width="256" height="256" xlink:href="data:image/png;base64,'
               + base64.b64encode(glow).decode() + '"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 256 256" '
            f'width="256" height="256"><defs>{defs}</defs>{img}{body}</svg>')


# --------------------------------------------------------------------------
# Raster + glow

def _tint(alpha, rgb, sigma, gain, fade=0):
    a = alpha.filter(ImageFilter.GaussianBlur(sigma))
    a = a.point(lambda v: min(255, int(v * gain)))
    if fade:
        # fade the glow out over the outer `fade` pixels, so a tail never
        # ends abruptly at the icon's edge
        m = Image.new("L", a.size, 0)
        ImageDraw.Draw(m).rectangle((fade, fade, a.width - fade - 1,
                                     a.height - fade - 1), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(fade / 2))
        a = Image.composite(a, Image.new("L", a.size, 0), m)
    layer = Image.new("RGBA", alpha.size, rgb + (0,))
    layer.putalpha(a)
    return layer


def _raster(svg, S):
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=S, output_height=S)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def _big_glow(alpha, S):
    out = Image.new("RGBA", alpha.size, (0, 0, 0, 0))
    out.alpha_composite(_tint(alpha, GLOW, 0.03 * S, 2.2))
    # The tight cyan halo kept narrow and faint: a bright one right at the
    # rim melted the edge into the glow.
    out.alpha_composite(_tint(alpha, HALO, 0.006 * S, 0.7))
    return out


def render(name, size, px=None):
    """PNG image of icon `name` drawn for `size`, rendered at px pixels."""
    px = px or size
    f = 4 if px <= 128 else 2       # supersampling
    S = px * f
    hi = _raster(svg_doc(icon_fn(name)(D(size))), S)
    alpha = hi.getchannel("A")
    if size <= SMALL:
        # a hint of glow only; at 16 px a wide halo just blurs the outline
        out = _tint(alpha, GLOW, 0.04 * S, 0.55, fade=f * px // size)
    else:
        out = _big_glow(alpha, S)
    out.alpha_composite(hi)
    img = out.resize((px, px), Image.LANCZOS)
    if size <= SMALL:
        # restore the edge contrast LANCZOS took off the heavier outlines
        rgb = img.convert("RGB").filter(ImageFilter.UnsharpMask(1, 60, 2))
        rgb.putalpha(img.getchannel("A"))
        img = rgb
    return img


def scalable_svg(name):
    """Vector body plus the same glow as the PNGs, as an embedded image."""
    body = icon_fn(name)(D(256))
    S = GLOW_RES * 2
    alpha = _raster(svg_doc(body), S).getchannel("A")
    glow = _big_glow(alpha, S).resize((GLOW_RES, GLOW_RES), Image.LANCZOS)
    buf = io.BytesIO()
    glow.save(buf, "PNG", optimize=True)
    return svg_doc(body, buf.getvalue()), edge_alpha(glow)


def edge_alpha(img):
    """Highest alpha on the outermost pixel ring (clipped glow check)."""
    a = img.getchannel("A")
    w, h = a.size
    ring = [a.getpixel((x, y)) for x in range(w) for y in (0, h - 1)]
    ring += [a.getpixel((x, y)) for y in range(h) for x in (0, w - 1)]
    return max(ring)


def _fixed_dir(s, scale):
    return f"{s}x{s}" + ("@2" if scale == 2 else "")


def _build_one(job):
    """Worker: all files of one icon as {relative path: bytes}."""
    ctx, n = job
    files, clipped = {}, []
    for s in FIXED:
        for scale in (1, 2):
            img = render(n, s, s * scale)
            if scale == 1 and edge_alpha(img) > 24:
                clipped.append(f"{n}@{s}")
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            files[f"{_fixed_dir(s, scale)}/{ctx}/{n}.png"] = buf.getvalue()
    for s in LARGE:
        img = render(n, s)
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        files[f"{_fixed_dir(s, 1)}/{ctx}/{n}.png"] = buf.getvalue()
    svg, edge = scalable_svg(n)
    if edge > 24:
        clipped.append(f"{n}@svg")
    files[f"scalable/{ctx}/{n}.svg"] = svg.encode()
    return files, clipped


# --------------------------------------------------------------------------
# Theme

def build_icons(out, name="WarpLegacyNeon"):
    """Write a complete freedesktop icon theme to out/<name>/.

    Returns the theme directory. Existing content of out/<name> is replaced.
    """
    out = pathlib.Path(out)
    root = out / name
    if root.exists():
        shutil.rmtree(root)
    jobs = [(c, n) for c, ns in ICON_CONTEXT.items() for n in ns]
    # fork: workers need the module as loaded, also when build.py put it on
    # sys.path by hand
    with multiprocessing.get_context("fork").Pool(os.cpu_count() or 2) as pool:
        results = pool.map(_build_one, jobs, chunksize=2)
    clipped = []
    for files, cl in results:
        clipped += cl
        for rel, data in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    aliases = all_aliases()
    dirs = [(_fixed_dir(s, sc), s, sc) for sc in (1, 2) for s in FIXED]
    dirs += [(_fixed_dir(s, 1), s, 1) for s in LARGE]
    for (ctx, alias), (tctx, target) in aliases.items():
        for dname, ext in [(dn, "png") for dn, _, _ in dirs] + [("scalable", "svg")]:
            d = root / dname / ctx
            d.mkdir(parents=True, exist_ok=True)
            rel = (f"{target}.{ext}" if tctx == ctx
                   else f"../{tctx}/{target}.{ext}")
            os.symlink(rel, d / f"{alias}.{ext}")
    ctxs = sorted(CONTEXTS)
    plain = [f"{dn}/{c}" for dn, _, sc in dirs if sc == 1 for c in ctxs]
    plain += [f"scalable/{c}" for c in ctxs]
    scaled = [f"{dn}/{c}" for dn, _, sc in dirs if sc == 2 for c in ctxs]
    lines = ["[Icon Theme]", "Name=Warp Legacy Neon",
             "Comment=Glowing night-time icons for Warp Legacy Neon",
             "Inherits=breeze-dark,hicolor", "Example=folder",
             "DisplayDepth=32",
             "Directories=" + ",".join(plain),
             # Scale>1 directories also go here, so loaders without HiDPI
             # support skip them (as Breeze does)
             "ScaledDirectories=" + ",".join(scaled), ""]
    for dn, s, sc in dirs:
        for c in ctxs:
            lines += [f"[{dn}/{c}]", f"Size={s}"] + (
                [f"Scale={sc}"] if sc > 1 else []) + [
                f"Context={CONTEXTS[c]}", "Type=Fixed", ""]
    for c in ctxs:
        lines += [f"[scalable/{c}]", "Size=64", f"MinSize={SVG_MIN}",
                  f"MaxSize={SVG_MAX}", f"Context={CONTEXTS[c]}",
                  "Type=Scalable", ""]
    (root / "index.theme").write_text("\n".join(lines))
    if clipped:
        print("warning: glow touches the edge:", ", ".join(clipped),
              file=sys.stderr)
    return root


# --------------------------------------------------------------------------
# Preview

def _qt_renderer():
    """QSvgRenderer-based rasteriser (what Plasma uses), or None."""
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QByteArray
        from PySide6.QtGui import QGuiApplication, QImage, QPainter
        from PySide6.QtSvg import QSvgRenderer
    except ImportError:
        return None
    app = QGuiApplication.instance() or QGuiApplication([])

    def rast(path_, px):
        r = QSvgRenderer(QByteArray(pathlib.Path(path_).read_bytes()))
        im = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
        im.fill(0)
        p = QPainter(im)
        r.render(p)
        p.end()
        im = im.convertToFormat(QImage.Format_RGBA8888)
        return Image.frombytes("RGBA", (px, px), bytes(im.constBits()))
    rast.app = app
    return rast


def _cairo_svg(path_, px):
    return _raster(pathlib.Path(path_).read_text(), px)


def contact_sheet(root, dest, names, rast, sizes=(16, 22, 32, 48, 96), cols=4):
    """PNGs up to 32, the scalable SVG (through rast) above."""
    pad, gap = 12, 10
    cw = sum(sizes) + gap * (len(sizes) - 1) + 2 * pad
    ch = max(sizes) + 2 * pad + 16
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), BG + (255,))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    dr = ImageDraw.Draw(sheet)
    for i, (ctx, n) in enumerate(names):
        x0, y0 = (i % cols) * cw + pad, (i // cols) * ch + pad
        x = x0
        for s in sizes:
            if s in FIXED:
                im = Image.open(root / f"{s}x{s}" / ctx / f"{n}.png")
            else:
                im = rast(root / "scalable" / ctx / f"{n}.svg", s)
            sheet.alpha_composite(im, (x, y0 + (max(sizes) - s) // 2))
            x += s + gap
        dr.text((x0, y0 + max(sizes) + 3), n, fill=(0xe8, 0xf0, 0xff), font=font)
    sheet.convert("RGB").save(dest)


def qt_compare(root, dest, rast, names, sizes=(48, 64, 128, 256)):
    """Old all-PNG pipeline vs the scalable SVG through QtSvg, side by side.
    Returns the mean absolute difference per channel (0..255)."""
    tile = sum(sizes) + 10 * len(sizes)
    sheet = Image.new("RGBA", (2 * tile + 30, len(names) * 266), BG + (255,))
    diffs = []
    for r, (ctx, n) in enumerate(names):
        x = 10
        for s in sizes:
            a = render(n, s)
            b = rast(root / "scalable" / ctx / f"{n}.svg", s)
            sheet.alpha_composite(a, (x, r * 266 + 5))
            sheet.alpha_composite(b, (tile + 20 + x, r * 266 + 5))
            x += s + 10
            fa, fb = Image.new("RGBA", a.size, BG + (255,)), Image.new("RGBA", a.size, BG + (255,))
            fa.alpha_composite(a)
            fb.alpha_composite(b)
            pa, pb = fa.convert("RGB").tobytes(), fb.convert("RGB").tobytes()
            diffs.append(sum(abs(p - q) for p, q in zip(pa, pb)) / len(pa))
    sheet.convert("RGB").save(dest)
    return sum(diffs) / len(diffs), max(diffs)


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    prev = here / "build-icons-preview"
    prev.mkdir(exist_ok=True)
    t = time.time()
    root = build_icons(prev)
    took = time.time() - t
    qt = _qt_renderer()
    rast = qt or _cairo_svg
    for ctx, ns in ICON_CONTEXT.items():
        contact_sheet(root, prev / f"kontakt-{ctx}.png", [(ctx, n) for n in ns], rast)
    allnames = [(c, n) for c, ns in ICON_CONTEXT.items() for n in ns]
    contact_sheet(root, prev / "uebersicht.png", allnames, rast,
                  sizes=(16, 32, 64), cols=8)
    if qt:
        sample = [("places", "folder-pictures"), ("devices", "computer"),
                  ("apps", "internet-web-browser"), ("places", "user-trash-full"),
                  ("status", "network-wireless-80"), ("actions", "edit-paste")]
        mean, worst = qt_compare(root, prev / "qt-vergleich.png", qt, sample)
        print(f"QtSvg vs PNG pipeline: mean abs diff {mean:.2f}, worst {worst:.2f}")
    n = len(allnames)
    print(f"{n} icons, {len(all_aliases())} aliases -> {root} ({took:.1f} s build)"
          f" [{'QtSvg' if qt else 'cairosvg'} preview]")
