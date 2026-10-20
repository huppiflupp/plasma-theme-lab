#!/usr/bin/env python3
"""Warp Legacy icon set, the classic light variant (DESIGN.md §9).

Own drawings in the manner of the OS/2 Warp 4 pictograms: pale yellow
folders and grey devices with a black outline and fixed 3D edges (white top
left, dark bottom right), a limited palette (VGA colours, greys, Warp blue
#2400a8, teal #00a0a0), hard edges, no glow. Nothing is traced from IBM's
icons or the user's concepts (§1); names and tables come from the Neon set
(icons_neon.py), so both variants cover the same icons.

Every icon is one function over a 32-unit grid (a classic 32x32 OS/2 icon)
drawing into a pixel canvas `P`:

- Coordinates snap to the target pixel grid, so straight edges are crisp
  at every size. Outlines and bevels are measured in device pixels (1 px up
  to 32, growing slowly above), not scaled with the drawing.
- 16, 22, 24 (and their @2 twins) are drawn without anti-aliasing, as
  pixel art, and the icon functions switch to a simplified layout there
  (`p.small`). From 32 on the canvas is supersampled for clean diagonals,
  and larger sizes add detail (`p.big`).
- Only fixed bitmaps are written (Type=Fixed in every size Dolphin offers,
  16..32 also @2): KIconLoader ignores Type=Scalable directories here
  (Dolphin blew the 32 px PNG up to 64, 20.10.2026; NT Legacy 6fc33663).

Status and action icons are light or coloured glyphs with a black outline,
so they read on the #cccccc surface and on the #2400a8 selection alike;
their -symbolic aliases point to the same drawings. Only the plain black
glyphs (MONO: window buttons, media keys, menu arrows) go out as SVG with
Breeze's colour-scheme stylesheet, still in the Fixed directories, so
KIconLoader paints them in the text colour (FollowsColorScheme=true).

    build_icons(out_dir)        -> out_dir/WarpLegacy/{index.theme, NxN/...}
    python3 icons_classic.py    -> build-icons-preview-classic/ (contact sheets)
"""
import io
import math
import multiprocessing
import os
import pathlib
import re
import shutil
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# same icon names, contexts and aliases as the Neon set (read only)
from icons_neon import CONTEXTS, ICON_CONTEXT, all_aliases  # noqa: E402

FIXED = (16, 22, 24, 32)        # each also as @2
LARGE = (48, 64, 96, 128, 256)
SMALL = 24                      # sizes <= SMALL: pixel-art layout, no AA
# outline/bevel width in device pixels per logical size
THICK = {16: 1, 22: 1, 24: 1, 32: 1, 48: 1, 64: 2, 96: 2, 128: 3, 256: 5}


def _c(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# palette: VGA colours, greys, Warp blue and teal
BLACK, WHITE = _c("000000"), _c("ffffff")
SURF, SILVER, LGREY = _c("cccccc"), _c("c0c0c0"), _c("e4e4e4")
DGREY, CHAR = _c("808080"), _c("404040")
WBLUE, BLUE, NAVY = _c("2400a8"), _c("0000ff"), _c("000080")
TEAL, CYAN, LCYAN = _c("00a0a0"), _c("00ffff"), _c("a0ffff")
RED, DRED, PINK = _c("ff0000"), _c("a00000"), _c("ff8080")
GREEN, DGREEN, LIME = _c("00b000"), _c("007000"), _c("00ff00")
YELLOW, GOLD, OLIVE = _c("ffff00"), _c("e0b000"), _c("808000")
ORANGE, BROWN, TAN = _c("ff8000"), _c("8a5a00"), _c("d8b070")
MAGENTA, PURPLE = _c("ff00ff"), _c("800080")
FOLD, FOLDB = _c("fff080"), _c("e8c840")     # folder front / back
PAPER = WHITE
SKY = _c("4080ff")

# fixed edge pairs (light, dark) for the main fills; others are derived
EDGES = {
    SURF: (WHITE, DGREY), SILVER: (WHITE, DGREY), LGREY: (WHITE, DGREY),
    DGREY: (SILVER, CHAR), FOLD: (_c("ffffd0"), _c("c8a020")),
    FOLDB: (_c("fff0a0"), _c("a88010")), WHITE: (WHITE, SILVER),
    WBLUE: (_c("6a50ff"), NAVY), TEAL: (CYAN, _c("006060")),
}


def _mix(a, b, f):
    return tuple(round(x + (y - x) * f) for x, y in zip(a[:3], b[:3])) + (255,)


def edges(c):
    return EDGES.get(c) or (_mix(c, WHITE, 0.55), _mix(c, BLACK, 0.45))


# --------------------------------------------------------------------------
# Masks (boolean arrays on the canvas)

def _shift(a, dy, dx):
    """out[y, x] = a[y - dy, x - dx], False outside."""
    out = np.zeros_like(a)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def erode(a, r, round_=True):
    """r steps of a cross erosion, alternating with a square one when
    round_: an octagon, so diagonal outlines are not thicker than straight."""
    for i in range(r):
        b = a & _shift(a, 1, 0) & _shift(a, -1, 0) & _shift(a, 0, 1) & _shift(a, 0, -1)
        if round_ and i % 2 == 1:
            b &= (_shift(a, 1, 1) & _shift(a, -1, -1) & _shift(a, 1, -1) & _shift(a, -1, 1))
        a = b
    return a


def dilate(a, r, round_=True):
    for i in range(r):
        b = a | _shift(a, 1, 0) | _shift(a, -1, 0) | _shift(a, 0, 1) | _shift(a, 0, -1)
        if round_ and i % 2 == 1:
            b |= (_shift(a, 1, 1) | _shift(a, -1, -1) | _shift(a, 1, -1) | _shift(a, -1, 1))
        a = b
    return a


def _band(a, b, sign):
    """Pixels of a within b pixels of its top/left (sign 1) or bottom/right
    (sign -1) edge: where the light or dark edge goes."""
    keep = a.copy()
    for i in range(1, b + 1):
        keep &= _shift(a, sign * i, 0) & _shift(a, 0, sign * i)
    return a & ~keep


class P:
    """Pixel canvas for one icon at one size.

    n is the logical size (decides the layout), px the device size (n or
    2n). Drawing coordinates are units of a 32 grid, mapped through a stack
    of (offset, scale) for emblems drawn on their own small grid.
    """

    def __init__(self, n, px=None):
        self.n = n
        self.px = px or n
        self.sc = self.px // n                 # 1 or 2 (@2)
        self.small = n <= SMALL
        self.big = n >= 64
        self.ss = 1 if self.small else (4 if self.px <= 128 else 2)
        self.N = self.px * self.ss
        self.kp = self.px / 32                 # device px per unit
        self.t = THICK[n] * self.sc            # outline in device px
        self.r = self.t * self.ss              # outline in canvas px
        self.img = np.zeros((self.N, self.N, 4), np.uint8)
        self.mono = np.zeros((self.N, self.N), bool)   # what etch() drew
        self.tf = [(0.0, 0.0, 1.0)]
        yy, xx = np.mgrid[0:self.N, 0:self.N]
        self.yc = (yy + 0.5) / self.ss         # pixel centres, device px
        self.xc = (xx + 0.5) / self.ss

    # -- mapping
    def at(self, ox, oy, s):
        """Context: draw on a sub-grid placed at (ox, oy), s units per unit."""
        p = self

        class _Ctx:
            def __enter__(self_):
                x0, y0, s0 = p.tf[-1]
                p.tf.append((x0 + ox * s0, y0 + oy * s0, s0 * s))

            def __exit__(self_, *e):
                p.tf.pop()
        return _Ctx()

    def X(self, x, snap=True):
        ox, _, s = self.tf[-1]
        v = (ox + x * s) * self.kp
        return math.floor(v + 0.5) if snap else v

    def Y(self, y, snap=True):
        _, oy, s = self.tf[-1]
        v = (oy + y * s) * self.kp
        return math.floor(v + 0.5) if snap else v

    def L(self, d):
        """A length in units as device px (unsnapped)."""
        return d * self.tf[-1][2] * self.kp

    def dev(self, k):
        """k logical device pixels, in device px (2 per pixel at @2)."""
        return k * self.sc

    def empty(self):
        return np.zeros((self.N, self.N), bool)

    # -- shapes -> masks
    def rect(self, x0, y0, x1, y1):
        m = self.empty()
        a, b = self.X(x0) * self.ss, self.X(x1) * self.ss
        c, d = self.Y(y0) * self.ss, self.Y(y1) * self.ss
        if b <= a:
            b = a + self.ss
        if d <= c:
            d = c + self.ss
        m[max(c, 0):max(d, 0), max(a, 0):max(b, 0)] = True
        return m

    def rectpx(self, x0, y0, wpx, hpx):
        """A rectangle w x h device pixels (logical) from a snapped corner."""
        m = self.empty()
        a, c = self.X(x0) * self.ss, self.Y(y0) * self.ss
        w, h = self.dev(wpx) * self.ss, self.dev(hpx) * self.ss
        m[c:c + h, a:a + w] = True
        return m

    def poly(self, pts, snap=True):
        """Even-odd fill sampled at pixel centres; several rings allowed
        (a list of point lists)."""
        rings = pts if isinstance(pts[0][0], (list, tuple)) else [pts]
        edges_ = []
        for ring in rings:
            q = [(self.X(x, snap), self.Y(y, snap)) for x, y in ring]
            edges_ += list(zip(q, q[1:] + q[:1]))
        allx = [v[0] for e in edges_ for v in e]
        ally = [v[1] for e in edges_ for v in e]
        m = self.empty()
        r0 = max(0, int(min(ally) * self.ss) - 1)
        r1 = min(self.N, int(max(ally) * self.ss) + 2)
        c0 = max(0, int(min(allx) * self.ss) - 1)
        c1 = min(self.N, int(max(allx) * self.ss) + 2)
        if r1 <= r0 or c1 <= c0:
            return m
        yc = (np.arange(r0, r1) + 0.5) / self.ss
        xc = (np.arange(c0, c1) + 0.5) / self.ss
        cnt = np.zeros((r1 - r0, c1 - c0), np.int16)
        for (xa, ya), (xb, yb) in edges_:
            if ya == yb:
                continue
            lo, hi = min(ya, yb), max(ya, yb)
            rows = (yc >= lo) & (yc < hi)
            if not rows.any():
                continue
            xi = xa + (yc[rows] - ya) * (xb - xa) / (yb - ya)
            cnt[rows] += (xc[None, :] < xi[:, None])
        m[r0:r1, c0:c1] = (cnt % 2) == 1
        return m

    def ellipse(self, x0, y0, x1, y1, snap=True):
        a, b = self.X(x0, snap), self.X(x1, snap)
        c, d = self.Y(y0, snap), self.Y(y1, snap)
        cx, cy, rx, ry = (a + b) / 2, (c + d) / 2, max((b - a) / 2, 0.5), max((d - c) / 2, 0.5)
        return ((self.xc - cx) / rx) ** 2 + ((self.yc - cy) / ry) ** 2 <= 1.0

    def circle(self, cx, cy, r):
        return self.ellipse(cx - r, cy - r, cx + r, cy + r)

    def seg(self, x0, y0, x1, y1, w=None, wpx=None):
        """A stroke with round ends, w units or wpx device pixels wide."""
        ww = self.dev(wpx) if wpx is not None else max(self.L(w), 1)
        if self.small:
            # pixel strokes: snap the ends to pixel centres
            ax, ay = self.X(x0, False), self.Y(y0, False)
            bx, by = self.X(x1, False), self.Y(y1, False)
            off = 0.5 if round(ww) % 2 else 0.0
            ax, ay = math.floor(ax) + off, math.floor(ay) + off
            bx, by = math.floor(bx) + off, math.floor(by) + off
        else:
            ax, ay, bx, by = (self.X(x0, False), self.Y(y0, False),
                              self.X(x1, False), self.Y(y1, False))
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((self.xc - ax) * dx + (self.yc - ay) * dy) / L2, 0, 1)
        ex, ey = self.xc - (ax + t * dx), self.yc - (ay + t * dy)
        lim = ww / 2
        if self.small and ww < 1.6:
            # one-pixel pen: exactly one pixel per column (or row), as a
            # pixel artist draws a line
            if abs(dx) >= abs(dy):
                if dx == 0:
                    return (np.abs(self.xc - ax) <= 0.5) & (np.abs(self.yc - ay) <= 0.5)
                yl = ay + (self.xc - ax) * dy / dx
                off = self.yc - yl
                return (off > -0.5) & (off <= 0.5) & (self.xc >= min(ax, bx) - 0.5) & \
                    (self.xc <= max(ax, bx) + 0.5)
            xl = ax + (self.yc - ay) * dx / dy
            off = self.xc - xl
            return (off > -0.5) & (off <= 0.5) & (self.yc >= min(ay, by) - 0.5) & \
                (self.yc <= max(ay, by) + 0.5)
        return ex * ex + ey * ey <= lim * lim

    def lines(self, pts, w=None, wpx=None):
        m = self.empty()
        for a, b in zip(pts, pts[1:]):
            m |= self.seg(*a, *b, w=w, wpx=wpx)
        return m

    def arc(self, cx, cy, r, a0, a1, w=None, wpx=None, steps=None):
        """Polyline arc, angles in degrees, 0 = right, clockwise (y down)."""
        steps = steps or max(6, int(abs(a1 - a0) / 10))
        pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
                cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
               for i in range(steps + 1)]
        return self.lines(pts, w=w, wpx=wpx)

    def ring(self, cx, cy, r, w):
        return self.circle(cx, cy, r) & ~self.circle(cx, cy, r - w)

    # -- painting
    def fill(self, m, col):
        self.img[m] = col

    def solid(self, m, fill, ol=BLACK, bev=True, light=None, dark=None, olw=None):
        """Body with an inner outline and the fixed OS/2 3D edges.
        bev: True raised, "sunk" sunken, False flat."""
        r = self.r if olw is None else olw * self.sc * self.ss
        inner = erode(m, r, not self.small) if ol else m
        if ol:
            self.img[m & ~inner] = ol
        self.img[inner] = fill
        if bev:
            lt, dk = edges(fill)
            lt, dk = light or lt, dark or dk
            if bev == "sunk":
                lt, dk = dk, lt
            b = self.r
            # light first, the dark edge wins in the two odd corners
            self.img[_band(inner, b, 1)] = lt
            self.img[_band(inner, b, -1)] = dk
        return inner

    def glyph(self, m, fill, ol=BLACK, olw=None):
        """Mark with an outline outside it (strokes keep their weight)."""
        r = self.r if olw is None else olw * self.sc * self.ss
        if ol:
            self.img[dilate(m, r, not self.small) & ~m] = ol
        self.img[m] = fill

    def etch(self, m, col=BLACK, sh=WHITE):
        """Dark mark with a white shadow one pixel down right: OS/2's
        etched look, and it keeps the mark visible on the blue selection."""
        d = self.sc * self.ss
        self.img[_shift(m, d, d) & ~m] = sh
        self.img[m] = col
        self.mono |= m

    def edge(self, m, col, side=1, width=None):
        """Paint only the light (side 1) or dark (-1) band of mask m."""
        self.img[_band(m, width or self.r, side)] = col

    def dots(self, m, col, step):
        """Regular dot texture, step device pixels apart, rows staggered
        (the dithered look of Warp's yellow folders)."""
        d = self.ss * self.sc
        yy, xx = np.mgrid[0:self.N, 0:self.N]
        yd, xd = yy // d, xx // d
        pat = (yd % step == 0) & ((xd + (yd // step % 2) * (step // 2)) % step == 0)
        self.img[m & pat] = col

    def image(self):
        im = Image.fromarray(self.img, "RGBA")
        if self.ss > 1:
            im = im.convert("RGBa").resize((self.px, self.px), Image.BOX).convert("RGBA")
        return im


# --------------------------------------------------------------------------
# Motifs

def folder(p, em=None, open_=False):
    """Warp folder: tabbed back, lighter front; emblem as a badge in front."""
    tab = [(1, 4), (12, 4), (15, 8), (31, 8), (31, 28), (1, 28)]
    if open_:
        tab = [(1, 4), (11, 4), (14, 7), (27, 7), (27, 28), (1, 28)]
    if p.small and not open_:
        m = p.solid(p.poly(tab), FOLD)
    else:
        p.solid(p.poly(tab), FOLDB)
        if open_:
            p.solid(p.rect(5, 6 if not p.small else 9, 25, 20), WHITE, bev=False)
            if not p.small:
                for y in (9.5, 12.5, 15.5):
                    p.fill(p.rect(8, y, 22, y + 0.6), DGREY)
            front = p.poly([(6, 13), (31, 13), (27, 28), (1, 28)])
        else:
            front = p.rect(1, 11, 31, 28)
        m = p.solid(front, FOLD)
        if p.n >= 32 and p.n <= 48:
            p.dots(erode(m, p.r), _c("e8d060"), 2 if p.n == 32 else 3)
    if em:
        if p.small:
            with p.at(13, 11, 19 / 16):
                em(p)
        else:
            with p.at(14, 12, 17 / 16):
                em(p)
    return m


def box3d(p, x0, y0, x1, y1, dx, dy, front=SILVER, top=LGREY, side=DGREY):
    """A box seen from front-left above: top face, front face, right side."""
    p.solid(p.poly([(x0, y0), (x1, y0), (x1 + dx, y0 - dy), (x0 + dx, y0 - dy)]), top, bev=False)
    p.solid(p.poly([(x1, y0), (x1 + dx, y0 - dy), (x1 + dx, y1 - dy), (x1, y1)]), side, bev=False)
    return p.solid(p.rect(x0, y0, x1, y1), front)


def monitor(p, x0=5, y0=2, x1=27, y1=20, screen=WBLUE, stand=True):
    if stand:
        p.solid(p.rect((x0 + x1) / 2 - 3, y1 - 1, (x0 + x1) / 2 + 3, y1 + 2), SILVER, bev=False)
    p.solid(p.rect(x0, y0, x1, y1), SILVER)
    i = 3
    sc = p.solid(p.rect(x0 + i, y0 + i, x1 - i, y1 - i - (1 if not p.small else 0)),
                 screen, bev=False)
    if not p.small and screen == WBLUE:
        p.edge(sc, _c("6a50ff"), 1, max(1, p.r))
    return sc


# --------------------------------------------------------------------------
# Icons

def i_folder(p): folder(p)
def i_folder_open(p): folder(p, open_=True)


def i_computer(p):
    """'OS/2 System': monitor on a flat desktop case (no lettering)."""
    case = p.solid(p.rect(1, 20, 31, 29), SILVER)
    p.fill(p.rect(17, 23, 27, 24.6 if not p.small else 25), BLACK)
    p.fill(p.rect(4, 24, 7, 26), LIME)
    monitor(p, 6, 2, 26, 19)


def i_drive_harddisk(p):
    if p.small:
        box3d(p, 1, 14, 25, 27, 6, 6)
        p.fill(p.rect(5, 19, 15, 21), DGREY)
        p.fill(p.rect(19, 19, 22, 22), LIME)
        return
    box3d(p, 2, 16, 25, 25, 5, 5)
    p.fill(p.rect(5, 19, 16, 20.5), DGREY)
    p.fill(p.rect(20, 19, 22.5, 21.5), LIME)
    if p.big:
        for x in range(4, 24, 2):
            p.fill(p.rect(x, 23, x + 1, 24), DGREY)


def i_user_trash(p): shredder(p, False)
def i_user_trash_full(p): shredder(p, True)


def shredder(p, full):
    """OS/2's shredder instead of a waste basket."""
    if full:
        sh = p.poly([(9, 1), (22, 0), (24, 13), (10, 14)])
        p.solid(sh, WHITE, bev=False)
        if not p.small:
            for i in range(3):
                p.fill(p.seg(12, 4 + 3 * i, 20, 3.4 + 3 * i, wpx=1), DGREY)
    p.solid(p.rect(2, 10, 30, 21), SILVER)
    p.fill(p.rect(6, 12, 26, 13.5 if not p.small else 14), BLACK)
    p.fill(p.rect(25, 16, 27.5, 18.5), RED if full else LIME)
    if p.small:
        k = 6 if p.n == 16 else 8
        x0, x1 = p.X(4), p.X(28)
        y0, y1 = p.Y(21), p.Y(31 if full else 25)
        m = p.empty()
        ss = p.ss
        m[y0 * ss:y1 * ss, x0 * ss:x1 * ss] = True
        p.fill(m, BLACK)
        cols = np.arange(p.N) // (p.ss * p.sc)
        white = m & ((cols - x0 // p.sc) % 2 == 1)[None, :]
        white &= (np.arange(p.N) // ss < y1 - p.sc)[:, None]
        p.fill(white, WHITE)
        return
    n = 7
    for i in range(n):
        x = 4.5 + i * 3.4
        ln = (7 + (i * 5) % 4) if full else 3
        p.solid(p.rect(x, 20, x + 2.4, 20 + ln), WHITE, bev=False)



def rot(pts, deg, cx=16, cy=16):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca)
            for x, y in pts]


def star_pts(cx, cy, R, r, n=5, a0=-90):
    return [(cx + (R if i % 2 == 0 else r) * math.cos(math.radians(a0 + 180 * i / n)),
             cy + (R if i % 2 == 0 else r) * math.sin(math.radians(a0 + 180 * i / n)))
            for i in range(2 * n)]


OCEAN = _c("1860e0")
LAND = _c("00b000")
SKIN = _c("ffc890")

_AMERICA = [(-0.75, -0.45), (-0.25, -0.75), (0.0, -0.45), (-0.3, -0.15), (-0.15, 0.3),
            (-0.35, 0.85), (-0.6, 0.35), (-0.85, 0.0)]
_EURAFRICA = [(0.15, -0.8), (0.7, -0.55), (0.9, -0.05), (0.55, 0.05), (0.5, 0.6),
              (0.25, 0.8), (0.1, 0.35), (0.25, 0.0), (0.05, -0.35)]


def globe(p, cx, cy, r, ocean=OCEAN):
    """Blue ocean, green land, black outline; the WebExplorer globe."""
    inner = p.solid(p.circle(cx, cy, r), ocean, bev=False)
    for cont in (_AMERICA, _EURAFRICA):
        land = p.poly([(cx + x * r, cy + y * r) for x, y in cont])
        p.fill(land & inner, LAND)
        if not p.small:
            p.edge(land & inner, _c("70ff70"), 1, max(1, p.r // 2 or 1))
    if not p.small:
        p.fill(p.arc(cx, cy, r * 0.78, 195, 245, wpx=max(1, p.t)) & inner, WHITE)
    return inner


def person(p, cx, top, h, shirt=BLUE):
    """Head and shoulders."""
    body = p.ellipse(cx - 0.42 * h, top + 0.48 * h, cx + 0.42 * h, top + 1.5 * h) & \
        p.rect(cx - h, top, cx + h, top + h)
    p.solid(body, shirt, bev=not p.small)
    p.solid(p.circle(cx, top + 0.25 * h, 0.24 * h), SKIN, bev=not p.small)


GEAR = _c("a0a0a0")   # small gears: silver would vanish into the #cccccc surface


def gear_mask(p, cx, cy, R, n=8, hole=0.3):
    prof = ((-0.28, 0.72), (-0.16, 1.0), (0.16, 1.0), (0.28, 0.72))
    if p.small:
        # pixel gear: a disc and eight square-cut teeth; tapered teeth
        # turn to noise at 16 px
        w = 0.24 * R
        m = p.circle(cx, cy, 0.72 * R) | p.rect(cx - w, cy - R, cx + w, cy + R) | \
            p.rect(cx - R, cy - w, cx + R, cy + w)
        for deg in (45, -45):
            m |= p.poly(rot([(cx - w, cy - R * 0.92), (cx + w, cy - R * 0.92),
                             (cx + w, cy + R * 0.92), (cx - w, cy + R * 0.92)], deg, cx, cy))
        return m & ~p.circle(cx, cy, R * 0.26) if hole else m
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for da, rr in prof:
            aa = a + da * 2 * math.pi / n
            pts.append((cx + R * rr * math.cos(aa), cy + R * rr * math.sin(aa)))
    m = p.poly(pts)
    if hole:
        m &= ~p.circle(cx, cy, R * hole)
    return m


def doc(p, x0=6, y0=2, x1=26, y1=30, ear=7, fill=PAPER):
    """Data file: white sheet with a folded top-right corner."""
    if p.small:
        ear = max(ear * 0.8, 5)
    m = p.poly([(x0, y0), (x1 - ear, y0), (x1, y0 + ear), (x1, y1), (x0, y1)])
    inner = p.solid(m, fill, bev=False)
    p.solid(p.poly([(x1 - ear, y0), (x1, y0 + ear), (x1 - ear, y0 + ear)]), SILVER, bev=False)
    return inner


def doc_lines(p, inner, col=DGREY, x0=9, x1=23, ys=None):
    ys = ys or ((10, 14, 18, 22, 26) if not p.small else (12, 17, 22, 27))
    for y in ys:
        p.fill(p.rectpx(x0, y, max(1, round(p.L(x1 - x0))), max(1, THICK[p.n])) & inner, col)


def window(p, x0, y0, x1, y1, body=WHITE, title=WBLUE):
    """An OS/2 window: grey frame, blue title bar, client area."""
    p.solid(p.rect(x0, y0, x1, y1), SURF)
    f = 1.5 if not p.small else 2
    th = 4 if not p.small else 5
    p.fill(p.rect(x0 + f, y0 + f, x1 - f, y0 + f + th - (0.5 if not p.small else 1)), title)
    c = p.rect(x0 + f, y0 + f + th, x1 - f, y1 - f)
    p.fill(c, BLACK)
    inner = erode(c, max(1, p.r // 2) if not p.small else p.r, False)
    p.fill(inner, body)
    return inner


def mini_pc(p, x, y, s=1.0, screen=TEAL):
    with p.at(x, y, s):
        p.solid(p.rect(0, 9, 14, 13), SILVER, bev=not p.small)
        p.solid(p.rect(2, 0, 12, 9), SILVER, bev=False)
        p.fill(p.rect(3.5, 1.5, 10.5, 7.5), screen)


def floppy(p, x0=3, y0=3, x1=29, y1=29, body=SILVER):
    m = p.poly([(x0, y0), (x1 - 3, y0), (x1, y0 + 3), (x1, y1), (x0, y1)])
    p.solid(m, body)
    w = x1 - x0
    p.solid(p.rect(x0 + w * 0.25, y0, x0 + w * 0.72, y0 + (y1 - y0) * 0.33), WHITE if body != WHITE else SILVER,
            bev=False)
    p.fill(p.rect(x0 + w * 0.55, y0 + 2, x0 + w * 0.65, y0 + (y1 - y0) * 0.26), DGREY)
    lab = p.solid(p.rect(x0 + w * 0.15, y0 + (y1 - y0) * 0.5, x1 - w * 0.15, y1 - 0.5), WHITE, bev=False)
    if not p.small:
        p.fill(p.rect(x0 + w * 0.15, y0 + (y1 - y0) * 0.5, x1 - w * 0.15,
                      y0 + (y1 - y0) * 0.5 + 2) & lab, BLUE)


def cd(p, cx=16, cy=16, r=13):
    m = p.circle(cx, cy, r) & ~p.circle(cx, cy, r * 0.18)
    inner = p.solid(m, LGREY, bev=False)
    if not p.small:
        # three 16-colour sheen wedges instead of a gradient
        for a0, col in ((200, LCYAN), (250, _c("ffb0ff")), (20, _c("ffffa0"))):
            wedge = p.poly([(cx, cy)] + [(cx + r * 1.2 * math.cos(math.radians(a)),
                                          cy + r * 1.2 * math.sin(math.radians(a)))
                                         for a in range(a0, a0 + 41, 8)])
            p.fill(wedge & inner, col)
    p.fill(p.ring(cx, cy, r * 0.4, max(r * 0.12, 1.2)) & inner, SILVER)
    p.solid(p.ring(cx, cy, r * 0.32, r * 0.12), DGREY, ol=False, bev=False)


# -- folder emblems, on a 16 grid -------------------------------------------

def em_house(p):
    p.solid(p.rect(2.5, 7, 13.5, 16), WHITE, bev=False)
    p.solid(p.poly([(0, 8.5), (8, 0.5), (16, 8.5)]), RED, bev=False)
    if not p.small:
        p.solid(p.rect(6.5, 10.5, 9.5, 16), BROWN, bev=False)


def em_monitor(p):
    p.solid(p.rect(5, 11, 11, 15), SILVER, bev=False)
    p.solid(p.rect(0, 1, 16, 13), SILVER, bev=False)
    p.fill(p.rect(2.5, 3.5, 13.5, 10.5), TEAL)


def em_doc(p):
    inner = doc(p, 2, 0, 15, 16, 5)
    if not p.small:
        doc_lines(p, inner, BLUE, 4.5, 12, (6, 9, 12))


def em_down(p):
    p.solid(p.poly([(5, 0), (11, 0), (11, 7), (16, 7), (8, 16), (0, 7), (5, 7)]), GREEN)


def em_note(p):
    if p.small:
        m = p.ellipse(1, 9, 10, 16) | p.rect(7, 0, 10, 13) | p.poly([(7, 0), (15, 4), (15, 8), (10, 5)])
        p.solid(m, BLUE, bev=False)
        return
    m = p.ellipse(0, 10, 7, 16) | p.ellipse(9, 8, 16, 14)
    m |= p.rect(4.5, 2, 7, 13) | p.rect(13.5, 0, 16, 11) | p.poly([(4.5, 2), (16, 0), (16, 3.5), (4.5, 5.5)])
    p.solid(m, BLUE, bev=False)


def em_picture(p):
    inner = p.solid(p.rect(0, 1, 16, 15), WHITE, bev=False)
    pic = erode(inner, p.dev(1) * p.ss, False) if not p.small else inner
    p.fill(pic, SKY)
    p.fill(p.poly([(0, 15), (6, 6), (11, 12), (13, 10), (16, 13), (16, 15)]) & pic, GREEN)
    p.fill(p.circle(11.5, 5, 2) & pic, YELLOW)


def em_play(p):
    inner = p.solid(p.rect(0, 2, 16, 15), CHAR, bev=False)
    for i in range(4):
        p.fill(p.rect(1.5 + i * 4, 3, 3 + i * 4, 4.5) & inner, WHITE)
        p.fill(p.rect(1.5 + i * 4, 12.5, 3 + i * 4, 14) & inner, WHITE)
    p.fill(p.poly([(6, 5.5), (11.5, 8.5), (6, 11.5)]) & inner, LIME)


def em_template(p):
    doc(p, 4, 0, 16, 13, 4)
    inner = doc(p, 0, 3, 12, 16, 4)
    if not p.small:
        doc_lines(p, inner, DGREY, 2, 8, (9, 12))


def em_share(p):
    if p.small:
        person(p, 8, 0, 13, BLUE)
        return
    person(p, 5, 1, 9, GREEN)
    person(p, 11, 4, 10, BLUE)


def em_globe(p): globe(p, 8, 8, 8)


def em_root(p):
    box3d(p, 0, 8, 12, 15, 4, 4)
    p.fill(p.rect(9, 10.5, 10.5, 12), LIME)


def em_clock(p):
    inner = p.solid(p.circle(8, 8, 8), WHITE, bev=False)
    m = p.seg(8, 8, 8, 3, wpx=1) | p.seg(8, 8, 11.5, 9.5, wpx=1)
    p.fill(m & inner, BLACK)
    if not p.small:
        p.fill(p.circle(8, 8, 1) & inner, RED)


def em_star(p):
    p.solid(p.poly(star_pts(8, 8.8, 8.5, 3.6)), YELLOW, bev=False)


def em_cloud(p):
    m = p.ellipse(0, 7, 9, 15) | p.ellipse(4, 2, 13, 12) | p.ellipse(8, 6, 16, 15) | p.rect(4, 10, 12, 15)
    p.solid(m, WHITE, bev=False)


def em_code(p):
    inner = p.solid(p.rect(0, 1, 16, 15), NAVY, bev=False)
    w = max(1, THICK[p.n])
    m = p.lines([(6, 4.5), (3, 8), (6, 11.5)], wpx=w) | p.lines([(10, 4.5), (13, 8), (10, 11.5)], wpx=w)
    p.fill(m & inner, LIME)


def em_lock(p):
    p.solid(p.arc(8, 6.5, 4, 180, 360, wpx=max(2, p.t + 1)) | p.rect(3.6, 6.5, 5.2, 8) |
            p.rect(10.8, 6.5, 12.4, 8), SILVER, bev=False, olw=1)
    p.solid(p.rect(1, 7.5, 15, 16), GOLD)
    p.fill(p.rect(7, 10, 9, 14), BLACK)


def i_user_home(p): folder(p, em_house)
def i_user_desktop(p): folder(p, em_monitor)
def i_folder_documents(p): folder(p, em_doc)
def i_folder_download(p): folder(p, em_down)
def i_folder_music(p): folder(p, em_note)
def i_folder_pictures(p): folder(p, em_picture)
def i_folder_videos(p): folder(p, em_play)
def i_folder_templates(p): folder(p, em_template)
def i_folder_publicshare(p): folder(p, em_share)
def i_folder_remote(p): folder(p, em_globe)
def i_folder_root(p): folder(p, em_root)
def i_folder_recent(p): folder(p, em_clock)
def i_folder_favorites(p): folder(p, em_star)
def i_folder_cloud(p): folder(p, em_cloud)
def i_folder_development(p): folder(p, em_code)
def i_folder_locked(p): folder(p, em_lock)


def i_network_workgroup(p):
    """'Connections': two machines joined by a green cable."""
    m = p.lines([(8, 15), (8, 21), (22, 21), (22, 18)], wpx=max(1, p.t))
    p.glyph(m, LIME, olw=1)
    mini_pc(p, 1, 2, 1.0)
    mini_pc(p, 16, 16, 1.0, BLUE)


def i_start_here(p):
    """Our own start mark: a blue disc with a white sweep and a yellow spark."""
    inner = p.solid(p.circle(16, 16, 14.5), WBLUE, bev=False)
    p.fill(p.ring(16, 16, 14.5, 3.2) & inner, TEAL)
    sweep = p.arc(16, 18, 7.5, 170, 330, w=3.2 if not p.small else 3.5)
    p.glyph(sweep, WHITE, ol=False)
    p.solid(p.poly(star_pts(21.5, 10.5, 5.5, 2.2, 4, -90)), YELLOW, bev=False, olw=1)


PARAM = {"start-here-kde": i_start_here}


# -- devices ----------------------------------------------------------------

def i_computer_laptop(p):
    p.solid(p.poly([(5, 3), (27, 3), (27, 20), (5, 20)]), SILVER)
    p.fill(p.rect(8, 6, 24, 17.5), WBLUE)
    p.solid(p.poly([(5, 20), (27, 20), (31, 27), (1, 27)]), LGREY, bev=False)
    if not p.small:
        for y in (22, 24):
            p.fill(p.rect(8, y, 24, y + 1), DGREY)


def i_network_server(p):
    p.solid(p.rect(8, 1, 24, 31), SILVER)
    for y in (4, 9, 14):
        p.solid(p.rect(11, y, 21, y + 3.5), LGREY, bev="sunk" if not p.small else False,
                ol=BLACK if not p.small else False)
        if p.small:
            p.fill(p.rect(11, y, 21, y + 2), DGREY)
    p.fill(p.rect(11, 22, 13.5, 24.5), LIME)
    p.fill(p.rect(15, 22, 17.5, 24.5), ORANGE)
    if not p.small:
        for y in (26.5, 28):
            p.fill(p.rect(11, y, 21, y + 0.6), DGREY)


def i_drive_optical(p):
    if p.small:
        box3d(p, 1, 14, 25, 27, 6, 6)
        p.fill(p.rect(4, 19, 16, 21), BLACK)
        p.fill(p.rect(19, 21, 22, 24), ORANGE)
        return
    box3d(p, 2, 16, 25, 25, 5, 5)
    p.fill(p.rect(5, 19, 18, 20.5), BLACK)
    p.fill(p.rect(20, 21, 22.5, 23.5), ORANGE)
    if not p.small:
        cd(p, 22, 8, 6.5)


def i_drive_removable_media(p):
    p.solid(p.rect(11, 2, 21, 10), SILVER, bev=False)
    p.fill(p.rect(13, 4, 15, 6.5) | p.rect(17, 4, 19, 6.5), BLACK)
    p.solid(p.rect(8, 9, 24, 30), TEAL)
    p.fill(p.rect(14.5, 24, 17.5, 27), LIME)


def i_media_optical(p): cd(p)


def i_printer(p):
    p.solid(p.poly([(9, 2), (23, 2), (23, 12), (9, 12)]), WHITE, bev=False)
    box3d(p, 2, 13, 26, 24, 4, 4)
    p.fill(p.rect(5, 16, 13, 17.5 if not p.small else 18), BLACK)
    p.fill(p.rect(20, 16, 22.5, 18.5), LIME)
    out = p.solid(p.rect(6, 22, 22, 30), WHITE, bev=False)
    if not p.small:
        doc_lines(p, out, DGREY, 8, 20, (25, 27.5))


def i_scanner(p):
    p.solid(p.poly([(6, 9), (30, 9), (27, 15), (2, 15)]), _c("606060"), bev=False)
    box3d(p, 2, 15, 26, 25, 4, 6)
    p.fill(p.rect(5, 19, 20, 20.5 if not p.small else 21), TEAL)
    p.fill(p.rect(21, 21, 23.5, 23.5), LIME)


def i_input_keyboard(p):
    body = p.poly([(5, 10), (27, 10), (31, 24), (1, 24)])
    p.solid(body, SILVER)
    if p.small:
        for y, xs in ((14, (6, 10, 14, 18, 22)), (18, (5, 9, 13, 17, 21, 25))):
            for x in xs:
                p.fill(p.rectpx(x, y, 1, 1), BLACK)
        p.fill(p.rect(9, 20.5, 23, 21.5), BLACK)
        return
    for r, y in enumerate((13, 16, 19)):
        x = 6.5 - r
        while x < 25 + r:
            p.solid(p.rect(x, y, x + 2.2, y + 2.2), WHITE, ol=DGREY, bev=False, olw=1)
            x += 3
    p.solid(p.rect(9, 21.6, 23, 23), WHITE, ol=DGREY, bev=False, olw=1)


def i_input_mouse(p):
    p.glyph(p.lines([(16, 7), (16, 3), (22, 1)], wpx=max(1, p.t)), CHAR, ol=False)
    body = p.ellipse(8, 6, 24, 30)
    inner = p.solid(body, LGREY)
    p.fill(p.rectpx(16, 6, max(1, THICK[p.n]), round(p.L(9))) & inner, BLACK)
    p.fill(p.rect(8, 14.5, 24, 15.5 if not p.small else 16) & inner, BLACK)


def i_input_gaming(p):
    m = p.ellipse(1, 10, 13, 26) | p.ellipse(19, 10, 31, 26) | p.rect(7, 10, 25, 21)
    p.solid(m, DGREY)
    p.fill(p.rect(5, 15, 10, 17), BLACK)
    p.fill(p.rect(6.5, 13.5, 8.5, 18.5), BLACK)
    p.fill(p.circle(23, 14.5, 1.6), RED)
    p.fill(p.circle(26, 17.5, 1.6), LIME)
    if not p.small:
        p.fill(p.circle(20, 17.5, 1.6), YELLOW)
        p.fill(p.circle(23, 20.5, 1.6), BLUE)


def i_audio_card(p):
    p.solid(p.rect(1, 7, 31, 22), DGREEN, bev=False)
    p.fill(p.rect(4, 22, 28, 26), GOLD)
    if not p.small:
        for x in range(5, 28, 2):
            p.fill(p.rect(x, 22.5, x + 1, 26), OLIVE)
    p.solid(p.rect(5, 10, 13, 18), CHAR, bev=False, olw=1)
    p.solid(p.rect(16, 10, 21, 15), CHAR, bev=False, olw=1)
    p.solid(p.rect(24, 9, 29, 19), SILVER, bev=False, olw=1)


def i_audio_headphones(p):
    band = p.arc(16, 17, 11, 180, 360, wpx=max(2, 2 * p.t))
    p.glyph(band, DGREY, olw=1)
    p.solid(p.rect(2, 16, 9, 29), CHAR)
    p.solid(p.rect(23, 16, 30, 29), CHAR)
    if not p.small:
        p.fill(p.rect(4, 19, 7, 26) | p.rect(25, 19, 28, 26), DGREY)


def i_audio_input_microphone(p):
    p.glyph(p.arc(16, 13, 8.5, 0, 180, wpx=max(1, p.t)) | p.seg(16, 21.5, 16, 27, wpx=max(1, p.t)),
            CHAR, ol=False)
    p.solid(p.rect(9, 28, 23, 31), CHAR, bev=False)
    m = p.ellipse(11, 2, 21, 12) | p.rect(11, 7, 21, 15) | p.ellipse(11, 10, 21, 20)
    inner = p.solid(m, SILVER)
    if not p.small:
        for y in (5, 8, 11, 14):
            p.fill(p.rect(13, y, 19, y + 0.8) & inner, DGREY)


def i_video_display(p):
    monitor(p, 2, 3, 30, 24)
    p.solid(p.rect(8, 26, 24, 29), SILVER, bev=False)


def i_smartphone(p):
    p.solid(p.rect(9, 1, 23, 31), CHAR, bev=False)
    p.fill(p.rect(11, 4, 21, 26), TEAL)
    if not p.small:
        p.fill(p.rect(11, 4, 21, 8), WBLUE)
        p.fill(p.circle(16, 28.5, 1), SILVER)


def i_camera_photo(p):
    p.solid(p.rect(10, 6, 19, 11), DGREY, bev=False)
    p.solid(p.rect(1, 9, 31, 27), CHAR, light=DGREY, dark=BLACK)
    p.solid(p.circle(16, 18, 7.5), SILVER, bev=False)
    p.solid(p.circle(16, 18, 4.5), NAVY, bev=False)
    if not p.small:
        p.fill(p.circle(14.5, 16.5, 1.3), WHITE)
        p.fill(p.rect(25, 12, 28, 14), YELLOW)


def i_cpu(p):
    m = p.empty()
    for i in range(5):
        o = 8 + i * 4
        m |= p.rect(o, 2, o + 1.6, 30) | p.rect(2, o, 30, o + 1.6)
    p.fill(m, SILVER if p.small else _c("b0b0b0"))
    p.solid(p.rect(6, 6, 26, 26), CHAR, light=DGREY, dark=BLACK)
    p.solid(p.rect(11, 11, 21, 21), SILVER, bev=False, olw=1)


def i_memory(p):
    p.solid(p.rect(1, 9, 31, 22), DGREEN, bev=False)
    p.fill(p.rect(3, 22, 29, 25), GOLD)
    if not p.small:
        for x in range(4, 29, 2):
            p.fill(p.rect(x, 22.5, x + 1, 25), OLIVE)
    for x in (3, 10.5, 18, 25.5):
        p.fill(p.rect(x, 12, x + 4.5, 19.5), BLACK)


def i_network_wired(p):
    """Network card: a board with the RJ-45 socket and two lights."""
    p.solid(p.rect(4, 8, 28, 24), SILVER)
    p.solid(p.poly([(9, 11), (23, 11), (23, 19), (19, 19), (19, 21), (13, 21), (13, 19), (9, 19)]),
            BLACK, bev=False)
    if not p.small:
        for x in (12, 14.5, 17, 19.5):
            p.fill(p.rect(x, 12, x + 1, 14.5), GOLD)
    p.fill(p.rect(6, 11, 8, 13), LIME)
    p.fill(p.rect(24, 11, 26, 13), ORANGE)


def i_network_wireless(p):
    for i, r in enumerate((6, 11, 16)):
        p.glyph(p.arc(16, 24, r, 220, 320, wpx=max(1, p.t + (1 if p.big else 0))), TEAL, olw=1)
    p.solid(p.rect(14, 20, 18, 31), DGREY, bev=False)
    p.solid(p.circle(16, 21, 3), RED, bev=False)


def i_battery(p): battery(p, 70, False, device=True)


# -- glyph shapes -------------------------------------------------------------

def quad(p, a, b, w):
    """A straight strip from a to b, w units wide (square ends)."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
    return p.poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)],
                  snap=False)


def qmark(p, cx, top, h, w):
    """Question mark mask, h units high, strokes w units."""
    r = h * 0.24
    m = p.arc(cx, top + r + w / 2, r, 180, 405, w=w)
    ex, ey = cx + r * math.cos(math.radians(45)), top + r + w / 2 + r * math.sin(math.radians(45))
    m |= quad(p, (ex, ey), (cx, top + h * 0.62), w)
    m |= p.rect(cx - w / 2, top + h * 0.55, cx + w / 2, top + h * 0.74)
    m |= p.rect(cx - w / 2, top + h - w * 1.1, cx + w / 2, top + h)
    return m


def pencil(p, a, b, w=4.5, body=YELLOW):
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    tip = (x1 - ux * w * 1.2, y1 - uy * w * 1.2)
    nx, ny = -uy * w / 2, ux * w / 2
    p.solid(p.poly([(tip[0] + nx, tip[1] + ny), (x1, y1), (tip[0] - nx, tip[1] - ny)], snap=False),
            TAN, bev=False)
    p.solid(quad(p, a, tip, w), body, bev=False)
    if not p.small:
        p.fill(quad(p, a, (x0 + ux * w * 0.7, y0 + uy * w * 0.7), w * 0.7), PINK)


def speaker(p, x=0, y=0, s=1.0, body=SILVER):
    with p.at(x, y, s):
        p.solid(p.rect(2, 11, 9, 21), body, bev=False)
        p.solid(p.poly([(8, 11), (16, 4), (16, 28), (8, 21)]), CHAR, bev=False)


def waves(p, n_lit, n=3, cx=15, cy=16, col=BLACK, dim=DGREY):
    if p.small:
        # three outlined arcs do not fit in 16 px: two, wider apart
        n_lit = {0: 0, 1: 1, 2: 1, 3: 2}[n_lit]
        n = 2
    for i in range(n):
        r = 5.5 + 4.6 * i if not p.small else 7.5 + 6.5 * i
        a = 48 if not p.small else 40
        m = p.arc(cx, cy, r, -a, a, wpx=max(1, p.t + (1 if p.big else 0)))
        # light strokes with a black outline: they read on grey and blue
        p.glyph(m, WHITE if i < n_lit else DGREY, olw=1)


def magnifier(p, cx, cy, r, handle=BROWN):
    a = math.radians(45)
    p.solid(quad(p, (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)),
                 (cx + r * 2.0 * math.cos(a), cy + r * 2.0 * math.sin(a)), r * 0.6), handle, bev=False)
    inner = p.solid(p.circle(cx, cy, r), SILVER, bev=False)
    glass = p.circle(cx, cy, r * 0.68)
    p.solid(glass & inner, LCYAN, bev=False, olw=1)
    if not p.small:
        p.fill(p.arc(cx, cy, r * 0.45, 200, 250, wpx=p.t) & glass, WHITE)


def red_slash(p, a=(4, 28), b=(28, 4)):
    p.glyph(quad(p, a, b, 3.2 if not p.small else 3.6), RED)


def padlock(p, x=0, y=0, s=1.0, body=GOLD):
    with p.at(x, y, s):
        sh = p.arc(16, 13, 7, 180, 360, w=3.2 if not p.small else 3.6) | \
            p.rect(7.4, 13, 10.6, 16) | p.rect(21.4, 13, 24.6, 16)
        p.solid(sh, SILVER, bev=False)
        p.solid(p.rect(4, 15, 28, 30), body)
        p.solid(p.circle(16, 21, 2.2) | p.rect(15, 21, 17, 26.5), BLACK, ol=False, bev=False)


def torch(p):
    """WarpCenter's Find: a torch throwing a yellow beam to the top right."""
    def R(pts):
        return rot(pts, -40, 16, 16)
    p.solid(p.poly(R([(19, 11.5), (32, 6), (32, 26), (19, 20.5)])), _c("ffff80"), ol=OLIVE,
            bev=False)
    p.solid(p.poly(R([(1, 13), (14, 13), (14, 19), (1, 19)])), CHAR, light=DGREY, dark=BLACK)
    p.solid(p.poly(R([(13, 11), (20, 9.5), (20, 22.5), (13, 21)])), SILVER, bev=False)
    if not p.small:
        p.fill(p.poly(R([(6, 14.5), (9, 14.5), (9, 17.5), (6, 17.5)])), RED)


def bell_mask(p, x=0, y=0, s=1.0):
    with p.at(x, y, s):
        m = p.ellipse(9, 4, 23, 18) | p.poly([(9, 11), (23, 11), (25, 22), (28, 25), (4, 25), (7, 22)])
        m |= p.circle(16, 26.5, 2.6)
        m |= p.circle(16, 3.5, 1.6)
        return m


def bell(p, x=0, y=0, s=1.0):
    p.solid(bell_mask(p, x, y, s), YELLOW)


def clock(p, cx=16, cy=16, r=14):
    inner = p.solid(p.circle(cx, cy, r), SILVER, bev=False)
    face = p.circle(cx, cy, r - (2 if not p.small else 2.5))
    p.solid(face & inner, WHITE, bev=False, olw=1)
    if not p.small:
        for k in range(12):
            a = math.radians(k * 30)
            p.fill(p.circle(cx + (r - 4.5) * math.cos(a), cy + (r - 4.5) * math.sin(a), 0.6), BLACK)
    m = p.seg(cx, cy, cx, cy - r * 0.62, wpx=max(1, p.t)) | p.seg(cx, cy, cx + r * 0.42, cy + r * 0.2,
                                                                   wpx=max(1, p.t))
    p.fill(m, BLACK)
    if not p.small:
        p.fill(p.seg(cx, cy, cx - r * 0.3, cy + r * 0.55, wpx=1), RED)


def battery_shape(p, level, charging, device=False):
    if p.small:
        body = p.rect(1, 8, 27, 25)
        p.solid(p.rect(26, 12, 31, 21), DGREY, bev=False)
    else:
        body = p.rect(2, 9, 27, 23)
        p.solid(p.rect(26, 13, 30, 19), DGREY, bev=False)
    inner = p.solid(body, WHITE, bev=False)
    inner2 = erode(inner, p.sc * p.ss * (1 if p.small else max(1, THICK[p.n])), False)
    col = RED if level <= 10 else YELLOW if level <= 20 else LIME
    if device:
        col = LIME
    w = (p.X(25) - p.X(4)) * level / 100
    if level > 0:
        m = inner2.copy()
        cols = np.arange(p.N) / p.ss
        m &= (cols < p.X(4 if not p.small else 3) + max(w, p.sc))[None, :]
        p.solid(m, col, ol=False, bev=not p.small)
    if charging:
        bolt = [(17, 5), (9, 17), (15, 17), (13, 27), (22, 14), (16, 14), (19, 5)]
        p.solid(p.poly(bolt), YELLOW, bev=False)


def battery(p, level, charging, device=False):
    battery_shape(p, level, charging, device)


# -- apps -------------------------------------------------------------------

def i_system_file_manager(p):
    """'Drives': a drive in front of an open folder."""
    with p.at(0, -2, 1.0):
        folder(p, open_=True)
    box3d(p, 6, 23, 26, 30, 4, 4)
    p.fill(p.rect(20, 25.5, 22.5, 27.5), LIME)


def i_utilities_terminal(p):
    inner = window(p, 1, 3, 31, 29, body=BLACK)
    w = max(1, THICK[p.n]) * (1 if p.small else 1)
    m = p.lines([(6, 14), (10, 18), (6, 22)], wpx=w + (1 if p.big else 0))
    m |= p.rect(13, 21, 19, 22.5 if not p.small else 23)
    p.fill(m & inner, WHITE)


def i_internet_web_browser(p): globe(p, 16, 16, 14.5)


def i_internet_mail(p):
    inner = p.solid(p.rect(1, 7, 31, 26), WHITE, bev=False)
    p.fill(p.lines([(1.5, 7.5), (16, 18), (30.5, 7.5)], wpx=max(1, THICK[p.n])) & inner, BLACK)
    if not p.small:
        p.fill(p.lines([(1.5, 25.5), (12, 15.5)], wpx=1) | p.lines([(30.5, 25.5), (20, 15.5)], wpx=1), DGREY)
        p.solid(p.rect(24, 9.5, 29, 14.5) & inner, RED, bev=False, olw=1)


def i_preferences_system(p):
    p.solid(gear_mask(p, 16, 16, 15, 8, 0.32), GEAR if p.small else SILVER, bev=not p.small)
    if not p.small:
        p.solid(p.ring(16, 16, 7.5, 2.3), TEAL, bev=False, olw=1)


def i_systemsettings(p):
    """'System Setup': a monitor with a gear in front."""
    monitor(p, 1, 2, 25, 20)
    p.solid(p.rect(8, 22, 18, 25), SILVER, bev=False)
    p.solid(gear_mask(p, 23, 23, 8.5, 8, 0.32), GEAR if p.small else SILVER, bev=not p.small)


def i_accessories_text_editor(p):
    inner = doc(p, 4, 2, 24, 30)
    doc_lines(p, inner, BLUE, 7, 20)
    pencil(p, (29, 6), (14, 26), 5 if not p.small else 5.5)


def i_accessories_calculator(p):
    p.solid(p.rect(5, 1, 27, 31), DGREY, light=SILVER, dark=CHAR)
    p.solid(p.rect(8, 4, 24, 10), _c("a0d0a0"), bev="sunk" if not p.small else False, olw=1)
    for r in range(4 if not p.small else 3):
        for c in range(3 if not p.small else 3):
            y = 12.5 + r * (4.5 if not p.small else 6)
            x = 8 + c * 6
            col = ORANGE if (c == 2 and r == 3) or (p.small and c == 2 and r == 2) else WHITE
            if p.small:
                p.fill(p.rect(x, y, x + 3.5, y + 3.5), col)
            else:
                p.solid(p.rect(x, y, x + 4.5, y + 3.5), col, bev=False, olw=1)


def i_accessories_screenshot(p):
    inner = window(p, 1, 4, 27, 26)
    p.fill(p.rect(5, 13, 22, 23) & inner, SKY if not p.small else TEAL)
    p.solid(p.rect(15, 18, 31, 30), CHAR, light=DGREY, dark=BLACK)
    p.solid(p.circle(23, 24, 3.6), TEAL, bev=False, olw=1)


def i_office_calendar(p):
    inner = p.solid(p.rect(3, 4, 29, 30), WHITE, bev=False)
    p.fill(p.rect(3, 4, 29, 11) & inner, RED)
    if not p.small:
        for x in (8, 15.5, 23):
            p.solid(p.rect(x, 1.5, x + 1.8, 7), SILVER, bev=False, olw=1)
    step = 4.5 if not p.small else 6
    k = 0
    for r in range(4 if not p.small else 3):
        for c in range(5 if not p.small else 3):
            x = 6 + c * step if not p.small else 6.5 + c * 7
            y = 13.5 + r * 4 if not p.small else 14 + r * 5
            col = RED if k == 7 else DGREY
            p.fill(p.rect(x, y, x + 2.5, y + 2.5) & inner, col)
            k += 1


def i_multimedia_volume_control(p):
    speaker(p, 0, 0, 1.0)
    waves(p, 3, 3, 15, 16)


def landscape(p, inner, x0, y0, x1, y1):
    p.fill(p.rect(x0, y0, x1, y1) & inner, SKY)
    w, h = x1 - x0, y1 - y0
    p.fill(p.poly([(x0, y1), (x0 + w * 0.35, y0 + h * 0.35), (x0 + w * 0.6, y0 + h * 0.7),
                   (x0 + w * 0.75, y0 + h * 0.55), (x1, y0 + h * 0.85), (x1, y1)]) & inner, GREEN)
    p.fill(p.circle(x0 + w * 0.78, y0 + h * 0.28, max(h * 0.14, 1.1)) & inner, YELLOW)


def i_image_viewer(p):
    inner = p.solid(p.rect(1, 4, 31, 28), GOLD)
    pic = p.rect(4, 7, 28, 25)
    p.fill(pic, BLACK)
    landscape(p, erode(pic, p.sc * p.ss, False), 4, 7, 28, 25)


def i_document_viewer(p):
    inner = doc(p, 3, 1, 23, 29)
    doc_lines(p, inner, DGREY, 6, 19)
    magnifier(p, 20, 19, 6.5)


def i_utilities_system_monitor(p):
    sc = monitor(p, 2, 3, 30, 24, screen=BLACK)
    pts = [(5, 15), (9, 15), (11, 9), (14, 19), (17, 12), (19, 15), (27, 15)]
    p.fill(p.lines(pts, wpx=max(1, THICK[p.n])) & sc, LIME)
    p.solid(p.rect(8, 26, 24, 29), SILVER, bev=False)


def cardboard(p, x0=3, y0=14, x1=25, y1=30, dx=5, dy=5):
    box3d(p, x0, y0, x1, y1, dx, dy, front=TAN, top=_c("f0d098"), side=_c("a07838"))
    if not p.small:
        p.fill(p.rect((x0 + x1) / 2 - 1.5, y0, (x0 + x1) / 2 + 1.5, y1 - 0.5), _c("c09050"))


def i_system_software_install(p):
    cardboard(p, 3, 15, 25, 30, 5, 5)
    p.solid(p.poly([(12, 1), (20, 1), (20, 9), (25, 9), (16, 18), (7, 9), (12, 9)]), GREEN)


def i_help_browser(p):
    """Help: a book with a yellow question mark (Warp's help object)."""
    p.solid(p.rect(8, 4, 29, 30), WHITE, bev=False)
    cov = p.solid(p.rect(4, 2, 25, 28), TEAL)
    if not p.small:
        p.fill(p.rect(4, 2, 7, 28) & cov, _c("007878"))
    q = qmark(p, 15.5, 5.5, 19, 3.6 if not p.small else 4)
    p.glyph(q, YELLOW, olw=1)


def i_applications_games(p):
    """Joystick (the Games object)."""
    p.solid(p.poly([(4, 22), (28, 22), (30, 29), (2, 29)]), DGREY, light=SILVER, dark=CHAR)
    p.solid(quad(p, (16, 23), (14, 9), 3), CHAR, bev=False)
    p.solid(p.circle(13.5, 7, 5), RED)
    p.fill(p.rect(22, 24, 26, 26), RED)


def i_applications_multimedia(p):
    cd(p, 20, 14, 11)
    speaker(p, -2, 4, 0.85)


def i_applications_office(p):
    inner = doc(p, 4, 1, 26, 31)
    if p.small:
        p.fill(p.rect(8, 19, 11, 27) & inner, RED)
        p.fill(p.rect(13, 13, 16, 27) & inner, GREEN)
        p.fill(p.rect(18, 16, 21, 27) & inner, BLUE)
        return
    doc_lines(p, inner, DGREY, 8, 18, (7, 10))
    for x, top, col in ((8, 19, RED), (13, 14, GREEN), (18, 17, BLUE)):
        p.solid(p.rect(x, top, x + 4, 27.5), col, bev=False, olw=1)


def i_applications_internet(p):
    globe(p, 18, 13, 12)
    mini_pc(p, 1, 17, 1.0)


def i_applications_utilities(p):
    """Toolbox."""
    p.solid(p.arc(16, 11, 5.5, 180, 360, w=2.6) | p.rect(9.2, 10, 11.8, 12) | p.rect(20.2, 10, 22.8, 12),
            DGREY, bev=False)
    p.solid(p.rect(2, 12, 30, 29), RED)
    p.fill(p.rect(2, 17, 30, 18.5 if not p.small else 19), BLACK)
    p.solid(p.rect(13.5, 16, 18.5, 20), SILVER, bev=False, olw=1)


def i_applications_system(p):
    i_computer(p)
    p.solid(gear_mask(p, 25, 25, 7, 8, 0.32), YELLOW, bev=not p.small)


def i_applications_development(p):
    inner = window(p, 1, 2, 31, 28, body=NAVY)
    w = max(1, THICK[p.n]) + (1 if p.big else 0)
    m = p.lines([(11, 11), (6, 16), (11, 21)], wpx=w) | p.lines([(21, 11), (26, 16), (21, 21)], wpx=w)
    if not p.small:
        m |= quad(p, (18, 9.5), (14, 22.5), 1.6)
    p.fill(m & inner, LIME)


def i_applications_education(p):
    p.solid(p.rect(4, 20, 28, 30), RED)
    p.fill(p.rect(6, 27, 26, 28.5 if not p.small else 29), WHITE)
    p.solid(p.poly([(8, 13), (24, 13), (24, 20), (8, 20)]), CHAR, bev=False)
    p.solid(p.poly([(16, 4), (31, 10), (16, 16), (1, 10)]), CHAR, light=DGREY, dark=BLACK)
    p.glyph(p.lines([(16, 10), (27, 12), (27, 19)], wpx=max(1, THICK[p.n])), GOLD, ol=False)


def i_applications_graphics(p):
    m = p.ellipse(1, 5, 29, 29) & ~p.circle(20, 21, 3.2)
    inner = p.solid(m, TAN)
    for (x, y), col in zip(((8, 13), (14, 9.5), (21, 10.5), (8, 21)), (RED, YELLOW, BLUE, GREEN)):
        p.solid(p.circle(x, y, 2.6), col, bev=False, olw=1)
    pencil(p, (31, 1), (17, 18), 3.5 if not p.small else 4, body=BROWN)


def i_applications_science(p):
    m = p.poly([(12, 2), (20, 2), (20, 11), (29, 28), (29, 30), (3, 30), (3, 28), (12, 11)])
    inner = p.solid(m, WHITE, bev=False)
    p.fill(p.poly([(9, 19), (23, 19), (29, 29), (3, 29)]) & inner, LIME)
    if not p.small:
        p.fill((p.circle(14, 24, 1.3) | p.circle(19, 22, 1)) & inner, WHITE)


def i_applications_other(p):
    """'Programs': a few coloured objects, as on Warp's Programs folder."""
    p.solid(p.poly([(9, 1), (17, 9), (9, 17), (1, 9)]), BLUE)
    p.solid(p.circle(23, 11, 7.5), RED)
    p.solid(p.poly([(11, 13), (21, 31), (1, 31)]), YELLOW)
    p.solid(p.rect(19, 20, 31, 31), GREEN)


def i_system_shutdown(p):
    i_computer(p)
    red_slash(p)


def i_system_reboot(p):
    i_computer(p)
    inner = p.solid(p.circle(23, 23, 8.5), WHITE, bev=False)
    w = 2.4 if not p.small else 3
    m = p.arc(23, 23, 4.6, 300, 600, w=w) | p.poly([(25, 15.5), (30, 19.5), (24, 22)])
    p.fill(m & inner, GREEN)


def i_system_log_out(p):
    p.solid(p.rect(4, 2, 22, 30), DGREY)
    inner = p.solid(p.poly([(6, 4), (16, 6), (16, 31), (6, 28)]), BROWN, bev=False)
    p.fill(p.circle(13.5, 18, 1.2), GOLD)
    p.solid(p.poly([(16, 13), (24, 13), (24, 8), (31, 16.5), (24, 25), (24, 20), (16, 20)]), GREEN)


def i_system_suspend(p):
    sc = monitor(p, 2, 3, 30, 24, screen=NAVY)
    moon = p.circle(14, 13, 6) & ~p.circle(17, 11, 5.2)
    p.fill(moon & sc, YELLOW)
    if not p.small:
        p.fill((p.circle(22, 8, 0.7) | p.circle(24, 16, 0.7)) & sc, WHITE)
    p.solid(p.rect(8, 26, 24, 29), SILVER, bev=False)


def i_system_switch_user(p):
    person(p, 9, 2, 13, GREEN)
    person(p, 23, 2, 13, BLUE)
    a = [(3, 26), (10, 21), (10, 24), (22, 24), (22, 21), (29, 26), (22, 31), (22, 28), (10, 28),
         (10, 31)]
    p.solid(p.poly(a), YELLOW, bev=False)


def i_system_users(p):
    person(p, 10, 3, 13, GREEN)
    person(p, 20, 8, 16, BLUE)


def i_system_lock_screen(p): padlock(p)
def i_system_search(p): torch(p)


def i_preferences_desktop(p):
    sc = monitor(p, 2, 3, 30, 24, screen=TEAL)
    if not p.small:
        for x, y in ((6, 7), (6, 13)):
            p.fill(p.rect(x, y, x + 4, y + 3) & sc, YELLOW)
    p.solid(p.rect(8, 26, 24, 29), SILVER, bev=False)


def i_preferences_desktop_display(p):
    sc = monitor(p, 2, 3, 30, 24, screen=BLACK)
    cols = (WHITE, YELLOW, CYAN, LIME, MAGENTA, RED, BLUE)
    for i, c in enumerate(cols):
        p.fill(p.rect(5 + i * 3.15, 5, 5 + (i + 1) * 3.15, 19) & sc, c)
    p.solid(p.rect(8, 26, 24, 29), SILVER, bev=False)


def i_preferences_desktop_theme_global(p):
    window(p, 1, 2, 25, 22)
    m = p.ellipse(10, 13, 31, 31) & ~p.circle(24, 25, 2.2)
    p.solid(m, TAN)
    for (x, y), col in zip(((15, 19), (20, 16.5), (25.5, 17.5)), (RED, YELLOW, BLUE)):
        p.solid(p.circle(x, y, 2), col, bev=False, olw=1)


def letter_a(p, x0, y0, x1, y1, w):
    xm = (x0 + x1) / 2
    m = quad(p, (x0 + w / 2, y1), (xm, y0 + w / 2), w) | quad(p, (xm, y0 + w / 2), (x1 - w / 2, y1), w)
    yb = y0 + (y1 - y0) * 0.62
    m |= p.rect(x0 + (x1 - x0) * 0.25, yb, x1 - (x1 - x0) * 0.25, yb + w * 0.8)
    return m


def i_preferences_desktop_font(p):
    inner = doc(p, 4, 1, 28, 31)
    p.fill(letter_a(p, 7, 6, 25, 27, 4.2 if not p.small else 4) & inner, NAVY)


def i_preferences_desktop_locale(p):
    globe(p, 13, 18, 12)
    p.fill(p.rect(20, 2, 21.8, 20), CHAR)
    p.solid(p.rect(21, 3, 31, 10), RED, bev=False)
    p.fill(p.rect(21, 5.5, 31, 7.5), WHITE)


def i_preferences_desktop_notification_bell(p): bell(p)


def i_preferences_desktop_accessibility(p):
    inner = p.solid(p.circle(16, 16, 14.5), BLUE)
    w = 2.6 if not p.small else 3
    fig = p.circle(16, 8.5, 2.6) | p.rect(8, 12, 24, 12 + w) | p.rect(16 - w / 2, 12, 16 + w / 2, 20)
    fig |= quad(p, (16, 19), (11.5, 26), w) | quad(p, (16, 19), (20.5, 26), w)
    p.fill(fig & inner, WHITE)


def i_preferences_desktop_effects(p):
    window(p, 1, 6, 25, 30)
    p.solid(p.poly(star_pts(22, 9, 9, 3, 4, -90)), YELLOW, bev=False)
    if not p.small:
        p.solid(p.poly(star_pts(10, 20, 4.5, 1.6, 4, -90)), YELLOW, bev=False, olw=1)


def i_preferences_desktop_virtual(p):
    """Control Strip desktops: four tiles, the current one marked red."""
    for i, (x, y) in enumerate(((1, 2), (17, 2), (1, 17), (17, 17))):
        sc = p.solid(p.rect(x, y, x + 14, y + 11), TEAL if i else SKY, bev=False)
        if not p.small:
            p.fill(p.rect(x + 3, y + 3, x + 9, y + 7) & sc, WHITE)
        p.fill(p.rect(x, y + 11.5, x + 14, y + 13.5), RED if i == 0 else BLACK)


SHIELD = [(16, 1), (29, 5), (29, 15), (26, 23), (16, 31), (6, 23), (3, 15), (3, 5)]


def i_preferences_security(p):
    inner = p.solid(p.poly(SHIELD), GOLD)
    core = erode(inner, p.sc * p.ss * (2 if not p.small else 1), not p.small)
    p.fill(core, BLUE)
    p.fill(core & p.rect(16, 0, 32, 32) & ~p.rect(0, 16, 32, 32), WHITE)
    p.fill(core & p.rect(0, 16, 16, 32), WHITE)


def bt_rune(p, cx=16, cy=16, h=20, w=None):
    """Short-range radio, not the Bluetooth rune: that is a registered
    trademark (DESIGN.md §1; the Neon set draws a neutral sign as well).
    A dot with two arcs of waves to its right."""
    import math
    w = w or 2.2
    x0 = cx - h * 0.28
    dot = p.circle(x0, cy, max(1.5, h * 0.1))
    shape = dot
    for r in (h * 0.3, h * 0.55):
        pts = [(x0 + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-55, 56, 11)]
        arc = p.lines(pts, wpx=1) if p.small else p.lines(pts, w=w)
        shape = shape | arc
    return shape


def i_preferences_system_bluetooth(p):
    inner = p.solid(p.ellipse(5, 1, 27, 31), BLUE)
    p.fill(bt_rune(p, 16, 16, 21) & inner, WHITE)


def i_preferences_system_time(p): clock(p)


def i_preferences_system_windows(p):
    window(p, 1, 1, 21, 19, title=DGREY)
    window(p, 9, 11, 31, 31)


# -- mimetypes --------------------------------------------------------------

def i_text_plain(p):
    doc_lines(p, doc(p))


def badge_doc(p, fn, lines=True):
    """A data file with a picture in its lower half."""
    inner = doc(p)
    if lines and not p.small:
        doc_lines(p, inner, DGREY, 9, 23, (8, 11))
    fn(p, inner)


def i_text_html(p):
    inner = doc(p)
    doc_lines(p, inner, DGREY, 9, 18, (9, 13) if not p.small else (11,))
    globe(p, 19, 22, 8.5)


def i_text_x_script(p):
    inner = doc(p)
    t = p.solid(p.rect(8, 13 if not p.small else 12, 24, 27), BLACK, bev=False)
    m = p.lines([(11, 16), (14, 19), (11, 22)], wpx=max(1, THICK[p.n])) | p.rect(16, 21.5, 21, 23)
    p.fill(m & t, LIME)
    if not p.small:
        doc_lines(p, inner, DGREY, 9, 18, (7,))


def i_text_x_csrc(p):
    inner = doc(p)
    w = max(1, THICK[p.n]) + (1 if p.big else 0)
    m = p.lines([(14, 8), (12, 8), (11, 10), (11, 14), (9, 16), (11, 18), (11, 22), (12, 24), (14, 24)],
                wpx=w)
    m |= p.lines([(18, 8), (20, 8), (21, 10), (21, 14), (23, 16), (21, 18), (21, 22), (20, 24), (18, 24)],
                 wpx=w)
    p.fill(m & inner, BLUE)


def i_text_markdown(p):
    inner = doc(p)
    w = max(1, THICK[p.n]) + (1 if p.big else 0)
    m = p.lines([(9, 22), (9, 11), (13, 16), (17, 11), (17, 22)], wpx=w)
    m |= p.rect(20.5, 11, 22, 18) | p.poly([(18.5, 17), (24, 17), (21.25, 21.5)])
    p.fill(m & inner, BLACK)


def i_x_office_document(p):
    inner = doc(p)
    p.fill(p.rect(9, 7, 19, 9.5 if not p.small else 10) & inner, BLUE)
    doc_lines(p, inner, DGREY, 9, 23, (13, 17, 21, 25) if not p.small else (14, 19, 24))


def i_x_office_spreadsheet(p):
    inner = doc(p)
    g_ = p.rect(8, 10, 24, 27)
    p.fill(g_ & inner, _c("d0ffd0"))
    m = p.empty()
    for x in (8, 13.5, 19, 24) if not p.small else (8, 16, 24):
        m |= p.rectpx(x, 10, 1, round(p.L(17)) + 1)
    for y in (10, 14.5, 19, 23.5, 27) if not p.small else (10, 16, 22, 27):
        m |= p.rectpx(8, y, round(p.L(16)) + 1, 1)
    p.fill(m & inner, DGREEN)


def i_x_office_presentation(p):
    inner = p.solid(p.rect(1, 4, 31, 24), WHITE, bev=False)
    p.fill(p.rect(1, 4, 31, 8) & inner, ORANGE)
    pie = p.circle(11, 16, 5.5)
    p.solid(pie, BLUE, bev=False, olw=1)
    p.fill(p.poly([(11, 16), (11, 9), (18, 9), (18, 16)]) & erode(pie, p.sc * p.ss, False), RED)
    for i, h in enumerate((4, 7, 5)):
        p.fill(p.rect(20 + i * 3, 21 - h, 22 + i * 3, 21) & inner, GREEN)
    p.fill(p.rect(15, 24, 17, 29), DGREY)
    p.fill(p.rect(10, 28, 22, 30), DGREY)


def i_x_office_drawing(p):
    doc(p)
    p.solid(p.circle(13, 13, 4.5), RED, bev=False, olw=1)
    p.solid(p.rect(15, 15, 23, 22), BLUE, bev=False, olw=1)
    p.solid(p.poly([(13, 19), (18, 27), (8, 27)]), YELLOW, bev=False, olw=1)


def i_x_office_address_book(p):
    inner = p.solid(p.rect(5, 2, 29, 30), _c("ffe8a0"))
    if not p.small:
        for y in (6, 12, 18, 24):
            p.solid(p.rect(2.5, y, 7.5, y + 2), SILVER, bev=False, olw=1)
    person(p, 17.5, 7, 14, BLUE)


def i_application_pdf(p):
    inner = doc(p)
    p.fill(p.rect(6, 20, 26, 27) & inner, RED)
    doc_lines(p, inner, DGREY, 9, 21, (8, 12, 16) if not p.small else (10, 15))
    if not p.small:
        p.fill(p.rect(9, 22.5, 22, 24.5) & inner, WHITE)


def i_image_x_generic(p):
    inner = doc(p)
    pic = p.rect(8, 11, 24, 26)
    p.fill(pic & inner, BLACK)
    landscape(p, erode(pic, p.sc * p.ss, False) & inner, 8, 11, 24, 26)


def i_image_svg_xml(p):
    inner = doc(p)
    pts = [(9 + 14 * t, 24 - 26 * t * (1 - t) * 1.3 + 2 * t) for t in [i / 12 for i in range(13)]]
    p.fill(p.lines(pts, wpx=max(1, THICK[p.n])) & inner, BLUE)
    for x, y in ((9, 24), (23, 26)):
        p.solid(p.rect(x - 1.8, y - 1.8, x + 1.8, y + 1.8), WHITE, bev=False, olw=1)
    if not p.small:
        p.fill(p.seg(9, 24, 14, 10, wpx=1) | p.seg(23, 26, 19, 10, wpx=1), DGREY)
        for x, y in ((14, 10), (19, 10)):
            p.solid(p.circle(x, y, 1.6), RED, bev=False, olw=1)


def i_audio_x_generic(p):
    doc(p)
    with p.at(8, 11, 1.0):
        em_note(p)


def i_video_x_generic(p):
    doc(p)
    with p.at(8, 11, 1.0):
        em_play(p)


def i_font_x_generic(p):
    inner = doc(p)
    p.fill(letter_a(p, 9, 9, 23, 27, 3.6) & inner, BLACK)


def i_application_x_archive(p):
    """Compressed files: a strapped bundle of sheets."""
    for i, y in enumerate((5, 9, 13)):
        p.solid(p.rect(4 + i, y, 24 + i, y + 16), WHITE if i < 2 else LGREY, bev=False)
    p.solid(p.rect(14, 4, 19, 30), BROWN, bev=False)
    p.solid(p.rect(12.5, 18, 20.5, 23), GOLD, bev=False, olw=1)


def i_package_x_generic(p):
    cardboard(p, 3, 11, 25, 29, 5, 6)


def i_application_x_cd_image(p):
    doc(p, 2, 2, 22, 28)
    cd(p, 20, 20, 10.5)


def i_application_x_executable(p):
    """An OS/2 program object: an empty window frame."""
    inner = window(p, 1, 3, 31, 29, body=SURF)
    if not p.small:
        p.fill(p.rect(4, 11, 28, 12) & inner, DGREY)


def i_application_x_desktop(p):
    window(p, 1, 2, 27, 24)
    p.solid(p.rect(14, 16, 31, 31), WHITE, bev=False)
    m = p.lines([(18, 28), (18, 22), (26, 22)], wpx=max(1, THICK[p.n]) + (1 if p.big else 0))
    m |= p.poly([(24, 19), (28.5, 22), (24, 25)])
    p.fill(m, BLACK)


def i_application_x_sqlite3(p):
    """Database: a stacked drum, three bands."""
    def half(y, ry, top):
        a0, a1 = (180, 360) if top else (0, 180)
        return [(16 + 11 * math.cos(math.radians(a)), y + ry * math.sin(math.radians(a)))
                for a in range(a0, a1 + 1, 10)]
    body = p.rect(5, 6, 27, 27) | p.ellipse(5, 23.5, 27, 30.5)
    inner = p.solid(body, SILVER)
    p.solid(p.ellipse(5, 2.5, 27, 9.5), LGREY, bev=False)
    w = max(1, THICK[p.n])
    for y in (13.5, 20.5) if not p.small else (15.5,):
        p.fill(p.lines(half(y, 3.5, False), wpx=w) & body, BLACK)


def i_application_certificate(p):
    inner = doc(p, 3, 2, 29, 24, 5)
    doc_lines(p, inner, DGREY, 7, 21, (7, 11, 15))
    p.solid(p.poly([(17, 22), (21, 22), (23, 31), (21, 29.5), (19, 31)]), BLUE, bev=False, olw=1)
    p.solid(p.poly([(21, 22), (25, 22), (27, 31), (25, 29.5), (23, 31)]), BLUE, bev=False, olw=1)
    p.solid(p.circle(21.5, 20, 5), RED)


def i_unknown(p):
    inner = doc(p)
    p.fill(qmark(p, 16, 8, 18, 3.4 if not p.small else 4) & inner, BLUE)


# -- actions ----------------------------------------------------------------
# Coloured marks with a black outline, or black marks with a white etch:
# both read on #cccccc and on the #2400a8 selection.

ARROW = [(3, 12.5), (16, 12.5), (16, 5), (29, 16), (16, 27), (16, 19.5), (3, 19.5)]
CHEV = [(10, 6), (22, 16), (10, 26)]


def arrow(p, deg, col=GREEN):
    p.solid(p.poly(rot(ARROW, deg)), col, bev=not p.small)


def tri(p, deg):
    pts = rot([(11, 7), (23, 16), (11, 25)], deg)
    p.etch(p.poly(pts))


def i_go_next(p): arrow(p, 0)
def i_go_previous(p): arrow(p, 180)
def i_go_up(p): arrow(p, -90)
def i_go_down(p): arrow(p, 90)
def i_arrow_right(p): tri(p, 0)
def i_arrow_left(p): tri(p, 180)
def i_arrow_up(p): tri(p, -90)
def i_arrow_down(p): tri(p, 90)


def i_go_home(p):
    p.solid(p.rect(6, 15, 26, 29), WHITE)
    p.solid(p.poly([(1, 17), (16, 3), (31, 17)]), RED)
    p.solid(p.rect(13, 20, 19, 29), BROWN, bev=False)


def star_badge(p, x=0, y=0, s=1.0):
    with p.at(x, y, s):
        p.solid(p.poly(star_pts(8, 8, 8, 3.2, 8, -90)), YELLOW, bev=False, ol=_c("c06000"))


def i_document_new(p):
    doc_lines(p, doc(p, 7, 3, 27, 31))
    star_badge(p, 0, 0, 0.9)


def i_document_open(p): folder(p, open_=True)


def i_document_save(p): floppy(p, 2, 2, 30, 30)


def i_document_print(p): i_printer(p)


def i_document_open_recent(p):
    doc_lines(p, doc(p, 3, 1, 23, 27), DGREY, 6, 18)
    with p.at(15, 15, 1.0):
        em_clock(p)


def i_document_edit(p):
    inner = doc(p, 3, 1, 23, 31)
    doc_lines(p, inner, DGREY, 6, 18)
    pencil(p, (30, 4), (14, 26), 5 if not p.small else 5.5)


def i_edit_copy(p):
    doc_lines(p, doc(p, 2, 1, 19, 22, 5), DGREY, 5, 15, (8, 12, 16) if not p.small else (9, 14))
    doc_lines(p, doc(p, 12, 9, 30, 31, 5), DGREY, 15, 26, (16, 20, 24, 28) if not p.small else (18, 24))


def i_edit_cut(p):
    p.solid(quad(p, (9, 2), (20, 20), 3.2), SILVER, bev=False)
    p.solid(quad(p, (23, 2), (12, 20), 3.2), SILVER, bev=False)
    for cx in (9, 23):
        p.solid(p.circle(cx, 24, 5.8) & ~p.circle(cx, 24, 2.6 if not p.small else 2.2), RED, bev=False)
    p.fill(p.circle(16, 15, 1), BLACK)


def i_edit_paste(p):
    p.solid(p.rect(4, 4, 26, 31), BROWN)
    inner = doc(p, 8, 9, 22, 28, 4)
    if not p.small:
        doc_lines(p, inner, DGREY, 10, 18, (14, 18, 22))
    p.solid(p.rect(10, 2, 20, 7), SILVER, bev=False)
    with p.at(14, 14, 1.1):
        doc_lines(p, doc(p, 2, 1, 15, 16, 4), DGREY, 4, 11, (7, 10, 13) if not p.small else (8, 12))


def big_x(p, col=RED, w=5.5, a=6, b=26):
    m = quad(p, (a, a), (b, b), w) | quad(p, (b, a), (a, b), w)
    p.solid(m, col, bev=False)


def i_edit_delete(p): big_x(p)


def undo_mask(p, mirror=False):
    """A U-turn: head pointing left at the top, bow on the right."""
    w = 4 if not p.small else 5
    m = p.rect(11, 9 - w / 2, 19, 9 + w / 2)
    m |= p.arc(19, 17, 8, 270, 450, w=w)
    m |= p.rect(10, 25 - w / 2, 19, 25 + w / 2)
    m |= p.poly([(2, 9), (11, 2), (11, 16)])
    if mirror:
        m = m[:, ::-1].copy()
    return m


def i_edit_undo(p): p.solid(undo_mask(p), _c("40e0e0"), bev=False)
def i_edit_redo(p): p.solid(undo_mask(p, True), _c("40e0e0"), bev=False)


def i_edit_clear(p):
    pts = rot([(3, 11), (29, 11), (29, 22), (3, 22)], -35)
    p.solid(p.poly(pts), PINK)
    half = rot([(3, 11), (12, 11), (12, 22), (3, 22)], -35)
    p.solid(p.poly(half), WHITE, bev=False)


def i_edit_select_all(p):
    m = p.empty()
    step = 4
    for x in range(3, 29, step):
        m |= p.rect(x, 3, x + 2, 4.8) | p.rect(x, 27.2, x + 2, 29)
    for y in range(3, 29, step):
        m |= p.rect(3, y, 4.8, y + 2) | p.rect(27.2, y, 29, y + 2)
    p.glyph(m, BLACK, ol=WHITE, olw=1)
    p.solid(p.rect(9, 9, 23, 23), _c("8080ff"), bev=False)


def i_edit_find(p): magnifier(p, 13, 13, 9.5)


def zoom(p, plus):
    magnifier(p, 13, 13, 9.5)
    w = 2 if not p.small else 2
    m = p.rect(8.5, 13 - w / 2, 17.5, 13 + w / 2)
    if plus:
        m |= p.rect(13 - w / 2, 8.5, 13 + w / 2, 17.5)
    p.fill(m, BLACK)


def i_zoom_in(p): zoom(p, True)
def i_zoom_out(p): zoom(p, False)


def plus_mask(p, w=7):
    a, b = 16 - w / 2, 16 + w / 2
    return p.rect(4, a, 28, b) | p.rect(a, 4, b, 28)


def i_list_add(p): p.solid(plus_mask(p), GREEN, bev=not p.small)
def i_list_remove(p): p.solid(p.rect(4, 12.5, 28, 19.5), RED, bev=not p.small)


def i_view_refresh(p):
    w = 3.8 if not p.small else 5
    m = p.arc(16, 16, 10, 200, 340, w=w) | p.arc(16, 16, 10, 20, 160, w=w)
    m |= p.poly([(22, 2), (30, 10), (21, 12)]) | p.poly([(10, 30), (2, 22), (11, 20)])
    p.solid(m, GREEN, bev=False)


def list_panel(p):
    return p.solid(p.rect(2, 3, 30, 29), WHITE, bev=False)


def i_view_list_details(p):
    inner = list_panel(p)
    for y in (7, 13, 19, 25) if not p.small else (8, 15, 22):
        p.fill(p.rect(5, y, 9, y + 2.5) & inner, BLUE)
        p.fill(p.rect(11, y + 0.5, 27, y + 2) & inner, BLACK)


def i_view_list_icons(p):
    inner = list_panel(p)
    for x in (6, 18):
        for y in (7, 18):
            p.solid(p.rect(x, y, x + 8, y + 7), FOLD, bev=False, olw=1)


def i_view_list_tree(p):
    inner = list_panel(p)
    w = max(1, THICK[p.n])
    m = p.rectpx(8, 9, w, round(p.L(16))) | p.rectpx(8, 15, round(p.L(5)), w) | \
        p.rectpx(8, 24, round(p.L(5)), w)
    p.fill(m & inner, DGREY)
    for x, y in ((5, 6), (13, 13), (13, 22)):
        p.solid(p.rect(x, y, x + 6, y + 5), FOLD, bev=False, olw=1)
    p.fill(p.rect(21, 14.5, 27, 16) & inner | p.rect(21, 23.5, 27, 25) & inner, BLACK)


EYE_TOP = [(1, 16), (8, 9), (16, 7), (24, 9), (31, 16), (24, 23), (16, 25), (8, 23)]


def i_view_visible(p):
    inner = p.solid(p.poly(EYE_TOP), WHITE, bev=False)
    p.solid(p.circle(16, 16, 6.5) & inner, BLUE, bev=False, olw=1)
    p.fill(p.circle(16, 16, 2.6) & inner, BLACK)
    if not p.small:
        p.fill(p.circle(14, 14, 1.2), WHITE)


def i_view_hidden(p):
    i_view_visible(p)
    red_slash(p, (4, 27), (28, 5))


def i_view_fullscreen(p):
    window(p, 1, 3, 31, 29)
    w = 2.6 if not p.small else 3
    m = p.empty()
    for (ax, ay), (bx, by) in (((10, 14), (5, 10)), ((22, 14), (27, 10)),
                               ((10, 22), (5, 26)), ((22, 22), (27, 26))):
        m |= quad(p, (ax, ay), (bx, by), w)
    p.glyph(m & p.rect(2, 8, 30, 28), GREEN, olw=1)


def i_view_split_left_right(p):
    inner = window(p, 1, 3, 31, 29)
    p.fill(p.rect(15.5, 8, 17, 28) & inner, BLACK)
    p.fill(p.rect(3, 8, 15.5, 28) & inner, LCYAN)


def i_configure(p):
    if p.small:
        p.solid(gear_mask(p, 16, 16, 15, 8, 0.32), GEAR, bev=False)
        return
    p.solid(gear_mask(p, 13, 13, 11.5, 8, 0.35), GEAR if p.small else SILVER, bev=not p.small)
    p.solid(quad(p, (17, 17), (24, 24), 2.6), SILVER, bev=False)
    p.solid(quad(p, (23, 23), (30.5, 30.5), 5), RED, bev=False)


def bars(p, rows, w=None):
    m = p.empty()
    for y in rows:
        m |= p.rect(5, y, 27, y + (w or 3.5))
    p.etch(m)


def i_application_menu(p): bars(p, (7, 14.25, 21.5))


def i_overflow_menu(p):
    m = p.empty()
    for y in (6, 14, 22):
        m |= p.rect(14, y, 18.5, y + 4.5)
    p.etch(m)


def i_window_close(p):
    w = 4 if not p.small else 4.4
    p.etch(quad(p, (8, 8), (24, 24), w) | quad(p, (24, 8), (8, 24), w))


def i_window_minimize(p):
    """OS/2's hide button: a small square."""
    m = p.rect(11, 11, 21, 21) & ~p.rect(13.5, 15, 18.5, 18.5)
    p.etch(m)


def i_window_maximize(p):
    m = p.rect(5, 5, 27, 27) & ~p.rect(7.5, 10.5, 24.5, 24.5)
    p.etch(m)


def i_window_restore(p):
    m = p.rect(11, 4, 28, 20) & ~p.rect(13, 8.5, 26, 18)
    m &= ~p.rect(4, 12, 21, 28)
    m |= p.rect(4, 12, 21, 28) & ~p.rect(6, 16.5, 19, 26)
    p.etch(m)


def i_window_pin(p):
    p.solid(quad(p, (16, 18), (16, 30), 2.2 if not p.small else 2), SILVER, bev=False)
    p.solid(p.rect(8, 15, 24, 19), DRED, bev=False)
    p.solid(p.rect(11, 3, 21, 16), RED)


def i_folder_new(p):
    with p.at(2, 2, 15 / 16):
        folder(p)
    star_badge(p, 0, 0, 0.9)


def i_bookmarks(p):
    p.solid(p.poly(star_pts(16, 17, 15, 6)), YELLOW, ol=_c("000000"))


def check_mask(p):
    w = 4.4 if not p.small else 4.8
    return quad(p, (4, 16), (12, 24), w) | quad(p, (12, 24), (28, 7), w)


def i_dialog_ok(p): p.solid(check_mask(p), LIME, bev=False)


def i_dialog_cancel(p):
    inner = p.solid(p.circle(16, 16, 14), RED)
    w = 3.4 if not p.small else 3.6
    p.fill((quad(p, (10, 10), (22, 22), w) | quad(p, (22, 10), (10, 22), w)) & inner, WHITE)


def i_help_about(p): info(p)


def info(p):
    inner = p.solid(p.circle(16, 16, 14.5), BLUE)
    w = 4 if not p.small else 4
    p.fill((p.rect(16 - w / 2, 13, 16 + w / 2, 25) | p.circle(16, 8.5, w * 0.6)) & inner, WHITE)


def i_media_playback_start(p): p.etch(p.poly([(9, 5), (26, 16), (9, 27)]))
def i_media_playback_pause(p): p.etch(p.rect(8, 6, 14, 26) | p.rect(18, 6, 24, 26))
def i_media_playback_stop(p): p.etch(p.rect(7, 7, 25, 25))
def i_media_skip_forward(p): p.etch(p.poly([(4, 6), (19, 16), (4, 26)]) | p.rect(21, 6, 26, 26))
def i_media_skip_backward(p): p.etch(p.poly([(28, 6), (13, 16), (28, 26)]) | p.rect(6, 6, 11, 26))
def i_media_eject(p): p.etch(p.poly([(16, 5), (28, 18), (4, 18)]) | p.rect(4, 21, 28, 26))


# -- status -----------------------------------------------------------------

def volume(p, level):
    speaker(p, 0, 0, 1.0)
    if level == "muted":
        p.solid(quad(p, (19, 11), (29, 21), 3.4) | quad(p, (29, 11), (19, 21), 3.4), RED, bev=False)
        return
    waves(p, {"low": 1, "medium": 2, "high": 3}[level], 3, 15, 16)


def mic(p, level):
    i_audio_input_microphone(p)
    if level == "muted":
        red_slash(p)
        return
    lit = {"low": 1, "medium": 2, "high": 3}[level]
    for i in range(3):
        p.solid(p.rect(26, 22 - i * 7, 31, 27 - i * 7), LIME if i < lit else WHITE, bev=False, olw=1)


def wifi(p, lit, off=False):
    """Signal bars instead of arcs: they sit on the pixel grid."""
    if p.small:
        # four bars three pixels wide; five would leave no colour inside
        lit = round(lit * 4 / 5)
        for i in range(4):
            x = 1 + i * 8
            p.solid(p.rect(x, 22 - i * 6, x + 6, 30), LIME if i < lit else WHITE, bev=False)
    for i in range(5 if not p.small else 0):
        x = 2 + i * 6
        top = 25 - (i + 1) * 4.4
        p.solid(p.rect(x, top, x + 4.5, 29), LIME if i < lit else WHITE, bev=False)
    if off:
        red_slash(p)


def plug(p):
    p.solid(p.rect(13, 22, 19, 31), CHAR, bev=False)
    p.solid(p.rect(7, 9, 25, 23), SILVER)
    p.solid(p.rect(10, 1, 13, 9) | p.rect(19, 1, 22, 9), GOLD, bev=False)


def i_network_wired_activated(p):
    plug(p)
    p.solid(p.circle(25, 25, 5), LIME, bev=False)


def i_network_wired_disconnected(p):
    plug(p)
    red_slash(p)


def i_network_offline(p):
    globe(p, 16, 16, 13)
    red_slash(p)


def i_battery_missing(p):
    battery_shape(p, 0, False)
    p.solid(qmark(p, 15, 10, 12, 2.6 if not p.small else 3), RED, bev=False, olw=1)


def link(p, state):
    col = BLUE if state != "inactive" else DGREY
    inner = p.solid(p.ellipse(5, 1, 27, 31), col)
    p.fill(bt_rune(p, 16, 16, 21) & inner, WHITE)
    if state == "activated":
        p.solid(p.circle(26, 6, 4.5), LIME, bev=False)
    if state == "inactive":
        red_slash(p)


def bell_state(p, state):
    bell(p)
    if state == "active":
        p.solid(p.circle(25, 7, 5.5), RED)
    if state == "disabled":
        red_slash(p)


def i_dialog_warning(p):
    inner = p.solid(p.poly([(16, 1), (31, 29), (1, 29)]), YELLOW, bev=False)
    w = 3.6 if not p.small else 4
    p.fill((p.rect(16 - w / 2, 9, 16 + w / 2, 21) | p.rect(16 - w / 2, 23, 16 + w / 2, 26.5)) & inner, BLACK)


def i_dialog_error(p):
    inner = p.solid(p.circle(16, 16, 14.5), RED)
    w = 3.6 if not p.small else 4
    p.fill((quad(p, (10, 10), (22, 22), w) | quad(p, (22, 10), (10, 22), w)) & inner, WHITE)


def i_dialog_question(p):
    inner = p.solid(p.circle(16, 16, 14.5), TEAL)
    p.fill(qmark(p, 16, 5, 22, 3.8 if not p.small else 4) & inner, WHITE)


def i_dialog_positive(p):
    inner = p.solid(p.circle(16, 16, 14.5), GREEN)
    w = 3.8 if not p.small else 4
    p.fill((quad(p, (8.5, 16), (14, 21.5), w) | quad(p, (14, 21.5), (23.5, 10), w)) & inner, WHITE)


PARAM.update({
    "dialog-information": info,
    "network-bluetooth": lambda p: link(p, "on"),
    "network-bluetooth-activated": lambda p: link(p, "activated"),
    "network-bluetooth-inactive": lambda p: link(p, "inactive"),
    "notifications": lambda p: bell_state(p, "on"),
    "notification-active": lambda p: bell_state(p, "active"),
    "notifications-disabled": lambda p: bell_state(p, "disabled"),
    "network-wireless-disconnected": lambda p: wifi(p, 0, True),
})
for _lv in ("high", "medium", "low", "muted"):
    PARAM[f"audio-volume-{_lv}"] = (lambda lv: lambda p: volume(p, lv))(_lv)
    PARAM[f"microphone-sensitivity-{_lv}"] = (lambda lv: lambda p: mic(p, lv))(_lv)
for _i, _n in enumerate((0, 20, 40, 60, 80, 100)):
    PARAM[f"network-wireless-{_n}"] = (lambda k: lambda p: wifi(p, k))(_i)
for _n in range(0, 101, 10):
    PARAM[f"battery-{_n:03d}"] = (lambda n: lambda p: battery(p, n, False))(_n)
    PARAM[f"battery-{_n:03d}-charging"] = (lambda n: lambda p: battery(p, n, True))(_n)


def icon_fn(name):
    return PARAM.get(name) or globals()["i_" + re.sub(r"[-+.]", "_", name)]


# Plain black glyphs (window buttons, media keys, menu arrows): written as
# SVG with Breeze's colour-scheme stylesheet, so KIconLoader paints them in
# the text colour, white on the #2400a8 selection. A fixed colour cannot
# read on both grounds without an outline that looks wrong on grey.
MONO = {"arrow-left", "arrow-right", "arrow-up", "arrow-down", "application-menu",
        "overflow-menu", "window-close", "window-minimize", "window-maximize",
        "window-restore", "media-playback-start", "media-playback-pause",
        "media-playback-stop", "media-skip-forward", "media-skip-backward",
        "media-eject"}
SCHEME = ('<style type="text/css" id="current-color-scheme">'
          '.ColorScheme-Text{color:#000000;}</style>')


def render(name, n, px=None):
    """PIL image of icon `name`, laid out for size n, px device pixels."""
    p = P(n, px)
    icon_fn(name)(p)
    return p.image()


def mono_svg(name, n, px=None):
    """The glyph's pixel mask as SVG rectangles on the canvas grid: crisp
    at its own size, anti-aliased like the PNGs from 32 on."""
    p = P(n, px)
    icon_fn(name)(p)
    m = p.mono
    rects, open_ = [], {}
    for y in range(p.N + 1):
        runs = set()
        if y < p.N:
            row = np.concatenate(([False], m[y], [False]))
            d = np.flatnonzero(row[1:] != row[:-1])
            runs = set(zip(d[::2].tolist(), d[1::2].tolist()))
        # merge a run with the identical run of the rows above it
        for r in list(open_):
            if r not in runs:
                rects.append((r[0], open_.pop(r), r[1] - r[0], y))
        for r in runs:
            open_.setdefault(r, y)
    d = "".join(f"M{x},{y0}h{w}V{y1}h-{w}z" for x, y0, w, y1 in rects)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {p.N} {p.N}" '
            f'width="{n}" height="{n}">{SCHEME}<path class="ColorScheme-Text" '
            f'fill="currentColor" d="{d}"/></svg>')


def ext(name):
    return "svg" if name in MONO else "png"


# --------------------------------------------------------------------------
# Theme

def _fixed_dir(s, scale):
    return f"{s}x{s}" + ("@2" if scale == 2 else "")


def _png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _build_one(job):
    """Worker: all bitmaps of one icon as {relative path: bytes}."""
    ctx, n = job
    files = {}
    jobs = [(s, sc) for s in FIXED for sc in (1, 2)] + [(s, 1) for s in LARGE]
    for s, sc in jobs:
        f = f"{_fixed_dir(s, sc)}/{ctx}/{n}.{ext(n)}"
        if n in MONO:
            files[f] = mono_svg(n, s, s * sc).encode()
        else:
            files[f] = _png(render(n, s, s * sc))
    return files


def build_icons(out, name="WarpLegacy"):
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
    for files in results:
        for rel, data in files.items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
    dirs = [(_fixed_dir(s, sc), s, sc) for sc in (1, 2) for s in FIXED]
    dirs += [(_fixed_dir(s, 1), s, 1) for s in LARGE]
    for (ctx, alias), (tctx, target) in all_aliases().items():
        for dn, _, _ in dirs:
            d = root / dn / ctx
            d.mkdir(parents=True, exist_ok=True)
            e = ext(target)
            rel = f"{target}.{e}" if tctx == ctx else f"../{tctx}/{target}.{e}"
            os.symlink(rel, d / f"{alias}.{e}")
    ctxs = sorted(CONTEXTS)
    plain = [f"{dn}/{c}" for dn, _, sc in dirs if sc == 1 for c in ctxs]
    scaled = [f"{dn}/{c}" for dn, _, sc in dirs if sc == 2 for c in ctxs]
    lines = ["[Icon Theme]", "Name=Warp Legacy",
             "Comment=Classic light icons in the manner of OS/2 Warp 4",
             "Inherits=breeze,hicolor", "Example=folder", "DisplayDepth=32",
             # KIconLoader recolours the MONO glyph SVGs (not the PNGs)
             "FollowsColorScheme=true",
             "Directories=" + ",".join(plain),
             # Scale>1 directories also go here, so loaders without HiDPI
             # support skip them (as Breeze does)
             "ScaledDirectories=" + ",".join(scaled), ""]
    for dn, s, sc in dirs:
        for c in ctxs:
            lines += [f"[{dn}/{c}]", f"Size={s}"] + (
                [f"Scale={sc}"] if sc > 1 else []) + [
                f"Context={CONTEXTS[c]}", "Type=Fixed", ""]
    (root / "index.theme").write_text("\n".join(lines))
    return root


# --------------------------------------------------------------------------
# Preview

SHEET_SIZES = (16, 22, 32, 48, 128)


_QT = None


def qt_svg(path_, px, color):
    """Rasterise an SVG with QtSvg (what KIconLoader uses), the scheme
    colour replaced as KIconLoader would."""
    global _QT
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    _QT = _QT or QGuiApplication.instance() or QGuiApplication([])
    data = pathlib.Path(path_).read_text().replace("color:#000000", f"color:{color}")
    r = QSvgRenderer(QByteArray(data.encode()))
    im = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
    im.fill(0)
    pa = QPainter(im)
    r.render(pa)
    pa.end()
    im = im.convertToFormat(QImage.Format_RGBA8888)
    return Image.frombytes("RGBA", (px, px), bytes(im.constBits()))


def load_icon(root, s, ctx, n, bg=(0xcc, 0xcc, 0xcc)):
    f = root / f"{s}x{s}" / ctx / f"{n}.{ext(n)}"
    if f.suffix == ".svg":
        return qt_svg(f, s, "#000000" if sum(bg) > 300 else "#ffffff")
    return Image.open(f).convert("RGBA")


def contact_sheet(root, dest, names, bg, sizes=SHEET_SIZES, cols=4, zoom=1):
    """Every icon in the given sizes, read back from the built theme."""
    pad, gap = 12, 10
    cw = (sum(sizes) + gap * (len(sizes) - 1)) * zoom + 2 * pad
    ch = max(sizes) * zoom + 2 * pad + 16
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), bg + (255,))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    dr = ImageDraw.Draw(sheet)
    ink = (0, 0, 0) if sum(bg) > 300 else (255, 255, 255)
    for i, (ctx, n) in enumerate(names):
        x0, y0 = (i % cols) * cw + pad, (i // cols) * ch + pad
        x = x0
        for s in sizes:
            im = load_icon(root, s, ctx, n, bg)
            if zoom > 1:
                im = im.resize((s * zoom, s * zoom), Image.NEAREST)
            sheet.alpha_composite(im, (x, y0 + (max(sizes) - s) * zoom // 2))
            x += (s + gap) * zoom
        dr.text((x0, y0 + max(sizes) * zoom + 3), n, fill=ink, font=font)
    sheet.convert("RGB").save(dest)


def check_theme(root):
    """Broken symlinks and index.theme directories that do not exist."""
    broken = [str(f.relative_to(root)) for f in root.rglob("*")
              if f.is_symlink() and not f.exists()]
    txt = (root / "index.theme").read_text()
    dirs = re.search(r"^Directories=(.*)$", txt, re.M).group(1).split(",")
    dirs += re.search(r"^ScaledDirectories=(.*)$", txt, re.M).group(1).split(",")
    missing = [d for d in dirs if f"[{d}]" not in txt or not (root / d).is_dir()]
    return broken, missing


if __name__ == "__main__":
    prev = HERE / "build-icons-preview-classic"
    prev.mkdir(exist_ok=True)
    t = time.time()
    root = build_icons(prev)
    took = time.time() - t
    for ctx, ns in ICON_CONTEXT.items():
        names = [(ctx, n) for n in ns]
        contact_sheet(root, prev / f"kontakt-{ctx}-grau.png", names, (0xcc, 0xcc, 0xcc))
        contact_sheet(root, prev / f"kontakt-{ctx}-weiss.png", names, (0xff, 0xff, 0xff))
        if ctx in ("actions", "status"):
            # the menu selection colour, where light glyphs must still read
            contact_sheet(root, prev / f"kontakt-{ctx}-auswahl.png", names, (0x24, 0x00, 0xa8),
                          sizes=(16, 22, 32))
    allnames = [(c, n) for c, ns in ICON_CONTEXT.items() for n in ns]
    contact_sheet(root, prev / "uebersicht.png", allnames, (0xcc, 0xcc, 0xcc),
                  sizes=(16, 32, 64), cols=8)
    broken, missing = check_theme(root)
    nfiles = sum(1 for f in root.rglob("*") if f.is_file() and not f.is_symlink())
    print(f"{len(allnames)} icons, {len(all_aliases())} aliases, {nfiles} files -> {root} "
          f"({took:.1f} s build)")
    if broken or missing:
        print("broken links:", broken[:10], "missing dirs:", missing[:10], file=sys.stderr)
        sys.exit(1)
