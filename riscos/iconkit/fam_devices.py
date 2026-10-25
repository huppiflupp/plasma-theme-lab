"""fam_devices.py: devices, drawn as the physical objects: RISC PC style
beige/grey cases, monitors showing RISC OS's desktop, discs, cards and
input devices. Variants of one object differ by a plaque (base.overlay),
a tint or a lit LED."""
import math

from base import case, overlay
from glyphs import glyph


# ---- small parts --------------------------------------------------------
def _g(c, col, t=0.3):
    """A lit gradient of one world colour."""
    return c.grad(c.lighten(col, t), c.darken(col, 0.12))


def _dark(c):
    return c.grad(c.lighten(c["ink"], 0.35), c["ink"])


def _led(c, x, y, on=True, col=None, r=1.6):
    c.circle(x, y, r if not c.small else r * 1.3, (col or c["led"]) if on else c.lighten(c["grey"], 0.4), width=0.8)


def _evenodd(c, d, fill, width=None):
    w = c.lw if width is None else width * (1.6 if c.small else 1)
    c.parts.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="{c["ink"]}" stroke-width="{w:g}" '
                   f'stroke-linejoin="round"/>')


def _ring(cx, cy, r):
    return f"M{cx + r:g} {cy:g} A{r:g} {r:g} 0 1 0 {cx - r:g} {cy:g} A{r:g} {r:g} 0 1 0 {cx + r:g} {cy:g} Z"


def _desktop(c, x, y, w, h):
    """A screen showing RISC OS's desktop: blue, a window, the iconbar."""
    c.rect(x, y, w, h, c.grad(c["screen"]), 1, width=1)
    if not c.small:
        c.rect(x + w * 0.18, y + h * 0.15, w * 0.5, h * 0.45, "#ffffff", 0.5, width=0.6)
        c.rect(x + w * 0.18, y + h * 0.15, w * 0.5, h * 0.1, c["cream"] if "cream" in c.w else c["yellow"], 0, width=0.6)
    c.rect(x + 0.6, y + h - h * 0.2, w - 1.2, h * 0.2 - 0.6, c.lighten(c["grey"], 0.55), 0, None)


def monitor(c, x=4, y=5, w=40, h=29, stand=True, screen=None):
    """A beige monitor; screen(c, x, y, w, h) fills the glass."""
    if stand:
        c.path(f"M{x + w / 2 - 5} {y + h} h10 l3 6 h-16 z", c.grad(c["case"]))
        c.rect(x + w / 2 - 11, y + h + 6, 22, 3.5, c.grad(c["case_top"]), 1.2)
    c.rect(x, y, w, h, c.grad(c["case"]), 2.5)
    (screen or _desktop)(c, x + 3.5, y + 3.5, w - 7, h - 8)
    if not c.small:
        _led(c, x + w - 5, y + h - 2.3, r=1.0)


def drive(c, x=4, y=12, w=40, h=24, light=True):
    """A hard disc unit: a box with a front strip and a green light."""
    case(c, x, y, w, h, 6)
    fx, fy, fw, fh = x, y + 6, w - 6, h - 6
    c.rect(fx + 3, fy + fh / 2 - 2, fw - 14, 4, c.darken(c["case"][1], 0.15), 1, width=0.9)
    _led(c, fx + fw - 6, fy + fh / 2, light, r=2)


def disc(c, tint=None, label=None):
    """A compact disc: silver (or tinted), a hub ring, the hole."""
    t = tint or c["metal"][1]
    _evenodd(c, _ring(24, 24, 20) + " " + _ring(24, 24, 3.2), c.grad(c.lighten(t, 0.75), c.lighten(t, 0.15)))
    if not c.small:
        c.path("M10 16 A16 16 0 0 1 18 9", "none", c.lighten(c["cyan"], 0.3), 2.2)
        c.path("M38 32 A16 16 0 0 1 30 39", "none", c.lighten(c["violet"], 0.35), 2.2)
    _evenodd(c, _ring(24, 24, 8) + " " + _ring(24, 24, 3.2), c.lighten(t, 0.85), 1)
    if label and not c.small:
        c.text(24, 39.5, label, 7.5, c.darken(t, 0.45))


def card(c):
    """An expansion card: green board, gold fingers, metal bracket left."""
    pcb = c.grad(c.lighten(c["green"], 0.1), c.darken(c["green"], 0.3))
    c.path("M10 12 h34 v20 h-6 v3 h-22 v-3 h-6 z", pcb)
    if not c.small:
        for i in range(10):
            c.rect(17 + i * 2.1, 32, 1.3, 2.6, c["yellow"], 0, None)
    c.rect(22, 16, 10, 9, _dark(c), 1, width=1)
    if not c.small:
        c.line("M24 16 v-2 M27 16 v-2 M30 16 v-2 M24 25 v2 M27 25 v2 M30 25 v2", c["metal"][0], 0.9)
        c.line("M34 20 h7 M34 23 h5", c.lighten(c["green"], 0.4), 0.8)
    c.path("M5 6 h6 v34 l-3 4 h-3 z", c.grad(c["metal"], horizontal=True))


def printer_body(c, laser=False):
    if laser:
        case(c, 5, 6, 38, 34, 7)
        c.rect(5, 13, 31, 4, c.darken(c["case"][1], 0.2), 0, width=0.9)            # paper exit
        c.path("M9 13 l3 -4 h18 l-1 4 z", c.grad(c["page"]), width=1)
        c.rect(8, 28, 25, 8, c.grad(c["case_top"]), 1, width=1)                   # tray
        c.line("M16 32 h9", "ink", 1.6)
        c.rect(24, 19, 9, 5, c.grad(c["screen"]), 0.5, width=0.8)
        _led(c, 10, 21.5, col=c["green"])
        return
    c.path("M13 4 h20 l2 14 h-24 z", c.grad(c["page"]))                           # paper in
    if not c.small:
        c.line("M16 8 h14 M16 11 h12", "#7a8699", 1)
    case(c, 3, 16, 42, 18, 6)
    c.path("M10 30 h22 l3 14 h-28 z", c.grad(c["page"]))                           # page out
    c.rect(11.5, 34, 7, 6, c["red"], 0, width=0.6)
    c.rect(18.5, 34, 7, 6, c["yellow"], 0, width=0.6)
    c.rect(25.5, 34, 6, 6, c["blue"], 0, width=0.6)
    _led(c, 33, 26, col=c["green"])


def phone(c, x=13, y=3, w=22, h=42, home=True, col=None):
    body = _g(c, col) if col else _dark(c)
    c.rect(x, y, w, h, body, 4.5)
    c.rect(x + 2, y + 5, w - 4, h - 12, c.grad(c["screen"]), 0.8, width=0.8)
    if not c.small:
        c.rect(x + 4, y + 8, w - 8, 3, "#ffffff", 0.5, None)
        for i in range(3):
            for j in range(2):
                c.rect(x + 4 + j * 8, y + 14 + i * 7, 5, 5, c.lighten(c["screen"][0], 0.4), 1, None)
    if home:
        c.circle(x + w / 2, y + h - 3.5, 2 if not c.small else 2.4, c.lighten(c["grey"], 0.3), width=0.8)
    else:
        c.line(f"M{x + 5} {y + h - 3.5} h2 M{x + w / 2 - 1} {y + h - 3.5} h2 M{x + w - 7} {y + h - 3.5} h2",
               c.lighten(c["grey"], 0.5), 1.6)


def key(c, x, y, w, h, pressed=False, fill=None):
    """A key cap in perspective: darker sides, lit top."""
    c.rect(x, y, w, h, c.darken((fill or c["case"])[1] if isinstance(fill or c["case"], tuple) else fill, 0.2), 4)
    top = c.grad(c["case_top"]) if fill is None else fill
    d = 2 if pressed else 0
    c.rect(x + 3, y + 2 + d, w - 6, h - 8 - (0 if pressed else 0), top, 3, width=1)


def wireless(c, level, col=None, empty=None):
    """Signal arcs filled up to level (0..4) above a dot."""
    on = col or c["blue"]
    off = empty or c.lighten(c["grey"], 0.6)
    w = 4.2 if not c.small else 3.4
    for i, r in enumerate((10, 18, 26, 34)):
        a = math.radians(45)
        x1, y1 = 24 - r * math.sin(a), 41 - r * math.cos(a)
        x2 = 24 + r * math.sin(a)
        d = f"M{x1:.2f} {y1:.2f} A{r} {r} 0 0 1 {x2:.2f} {y1:.2f}"
        c.parts.append(f'<path d="{d}" fill="none" stroke="{c["ink"]}" stroke-width="{w + c.lw * 1.6:g}" stroke-linecap="round"/>')
        c.parts.append(f'<path d="{d}" fill="none" stroke="{on if i < level else off}" stroke-width="{w:g}" stroke-linecap="round"/>')
    c.circle(24, 41, 4, on if level > 0 else off)


def mouse(c, cable=True):
    if cable:
        c.path("M24 10 C24 4 32 2 38 4", "none", "ink", 1.6)
    c.path("M12 22 C12 12 16 9 24 9 C32 9 36 12 36 22 V34 C36 41 31 44 24 44 C17 44 12 41 12 34 Z", c.grad(c["case"]))
    c.path("M12 23 C12 12 16 9 24 9 C32 9 36 12 36 23 Z", c.grad(c["case_top"]))
    c.path("M20 9.6 V23", "none", "ink", 1.2)
    c.path("M28 9.6 V23", "none", "ink", 1.2)
    c.path("M20 9.6 C22 9.1 26 9.1 28 9.6 V23 H20 Z", c.lighten(c["grey"], 0.35), "ink", 1.2)
    if not c.small:
        c.line("M16 38 h16", c["case_dark"], 1)


def keyboard(c, x=2, y=14, w=44, h=24, virtual=False):
    if virtual:
        c.rect(x, y, w, h, c.grad(c["screen"]), 2.5)
        keycol, fcol = "#ffffff", c.lighten(c["screen"][0], 0.3)
    else:
        c.path(f"M{x} {y + h} l4 -{h} h{w - 8} l4 {h} z", c.grad(c["case"]))
        keycol, fcol = c["case_top"][0], c["red"]
    rows = 4 if not c.small else 3
    kw = 4.2 if not c.small else 6.5
    for r in range(rows):
        yy = y + 3 + r * ((h - 6) / rows)
        hh = (h - 6) / rows - 1.4
        inset = 6 - r * 0.9 if not virtual else 3
        n = int((w - 2 * inset) // (kw + 1.2))
        for i in range(n):
            col = fcol if (r == 0 and not virtual and 2 <= i <= n - 3) else keycol
            c.rect(x + inset + i * (kw + 1.2), yy, kw, hh, col, 0.7, width=0.7 if not c.small else 0.5)


# ---- the devices ------------------------------------------------------------
import names as _names
MINE = frozenset(_names.names()["devices"])


def draw(name, c):
    if name not in MINE:
        return None
    try:
        return _draw(name, c)
    except KeyError:
        return None


def _draw(name, c):
    ink = c["ink"]
    if name == "audio-card":
        card(c)
        for y, col in ((14, c["green"]), (22, c["red"]), (30, c["blue"])):
            c.circle(8, y, 2.5, c.lighten(col, 0.25), width=1)
            c.circle(8, y, 0.9, ink, None)
        glyph(c, "note", 33, 3, 13, c["yellow"], width=2.6)
        return True
    if name == "network-card":
        card(c)
        c.rect(5.5, 17, 5, 7, _dark(c), 0.5, width=0.8)
        _led(c, 8, 28, col=c["green"], r=1.2)
        _led(c, 8, 32, col=c["orange"], r=1.2)
        glyph(c, "network", 31, 1, 14, c["cyan"], width=2.6)
        return True
    if name in ("audio-headphones", "audio-headset"):
        c.path("M8 30 V22 A16 16 0 0 1 40 22 V30", "none", "ink", 6 if not c.small else 4.5)
        c.path("M8 30 V22 A16 16 0 0 1 40 22 V30", "none", c.grad(c["metal"]), 3.6 if not c.small else 2.4)
        cup = _g(c, c["red"]) if name == "audio-headphones" else _g(c, c["blue"])
        for x in (4, 34):
            c.rect(x, 25, 10, 17, cup, 4)
            c.rect(x + (7 if x < 20 else -1), 27, 4, 13, c.lighten(c["grey"], 0.3), 2, width=1)
        if name == "audio-headset":
            c.path("M9 40 C10 45 18 46 24 44", "none", "ink", 2.2)
            c.ellipse(26, 44, 3.5, 2.6, _dark(c), width=1)
        return True
    if name == "audio-input-microphone":
        c.path("M14 22 A10 10 0 0 0 34 22", "none", "ink", 2.2)
        c.line("M24 32 V41 M16 43 H32", "ink", 2.6)
        c.rect(17, 4, 14, 24, c.grad(c["metal"], horizontal=True), 7)
        if not c.small:
            c.line("M19 10 H29 M18 14 H30 M18 18 H30 M19 22 H29", c.darken(c["metal"][1], 0.2), 1)
        return True
    if name == "audio-radio":
        c.line("M30 14 L40 3", "ink", 1.8)
        c.circle(40, 3, 1.6, c["metal"][1], width=0.8)
        c.rect(3, 14, 42, 28, c.grad(c.lighten(c["brown"], 0.45), c["brown"]), 4)
        c.circle(15, 28, 9, c.grad(c.lighten(c["grey"], 0.4), c.darken(c["grey"], 0.1)))
        if not c.small:
            for yy in (23, 26, 29, 32, 35):
                c.line(f"M9 {yy} H21", c.darken(c["grey"], 0.35), 1)
        c.rect(27, 19, 14, 8, c.lighten(c["yellow"], 0.55), 1, width=1)
        c.line("M33 19 V27", c["red"], 1.4)
        c.circle(30, 34, 3, c.grad(c["metal"]), width=1)
        c.circle(38, 34, 3, c.grad(c["metal"]), width=1)
        return True
    if name == "audio-speakers":
        for x, y in ((3, 8), (25, 12)):
            c.rect(x, y, 20, 32, c.grad(c["case"]), 2)
            c.circle(x + 10, y + 9, 4, _dark(c), width=1)
            c.circle(x + 10, y + 21, 7, _dark(c), width=1)
            c.circle(x + 10, y + 21, 2.4, c["metal"][1], None)
        return True
    if name == "auth-sim":
        c.path("M8 5 h24 l8 8 v28 a2 2 0 0 1 -2 2 h-30 a2 2 0 0 1 -2 -2 v-34 a2 2 0 0 1 2 -2 z", c.grad(c["page"]))
        c.rect(13, 18, 20, 16, c.grad(c.lighten(c["yellow"], 0.3), c.darken(c["yellow"], 0.15)), 2.5)
        if not c.small:
            c.line("M13 23.5 H20 V28.5 H13 M33 23.5 H26 V28.5 H33 M20 18 V23.5 M26 18 V23.5 M20 28.5 V34 M26 28.5 V34",
                   c.darken(c["yellow"], 0.45), 1)
        return True
    if name == "battery":
        c.rect(40, 19, 4, 10, c.grad(c["metal"]), 1)
        c.rect(4, 14, 37, 20, c.grad(c["metal"]), 3)
        c.rect(4, 14, 24, 20, _g(c, c["green"]), 3)
        c.line("M33 24 h5 M35.5 21.5 v5", "ink", 1.6)
        return True
    if name == "battery-ups":
        case(c, 8, 4, 32, 40, 6)
        c.rect(12, 14, 18, 8, c.grad(c["screen"]), 1, width=0.9)
        glyph(c, "lightning", 13, 23, 16, c["orange"], width=2.4)
        for i in range(3):
            c.rect(14 + i * 5, 39, 3.6, 2, c["green"], 0, width=0.5)
        c.circle(29, 31, 2.5, _g(c, c["red"]), width=1)
        return True
    if name == "camera-photo":
        c.rect(5, 13, 38, 26, c.grad(c["metal"]), 3)
        c.path("M15 13 l3 -5 h12 l3 5 z", c.grad(c["metal"]))
        c.rect(5, 18, 38, 15, _dark(c), 0, width=1)
        c.circle(24, 26, 10, c.grad(c["metal"]))
        c.circle(24, 26, 6.5, c.grad(c.lighten(c["screen"][0], 0.1), c["ink"]))
        if not c.small:
            c.circle(22, 24, 1.8, "#ffffff", None)
        c.rect(34, 9, 6, 4, c["red"], 1, width=1)
        c.rect(8, 15, 6, 2.5, c.lighten(c["yellow"], 0.4), 0.5, width=0.7)
        return True
    if name == "camera-video":
        c.rect(3, 16, 30, 20, c.grad(c["metal"]), 4)
        c.path("M33 21 l10 -5 v20 l-10 -5 z", c.grad(c["metal"]))
        c.rect(6, 10, 14, 6, _dark(c), 1, width=1)
        c.rect(7, 20, 11, 9, c.grad(c["screen"]), 1, width=1)
        c.circle(26, 26, 4, _dark(c), width=1)
        _led(c, 29, 19, col=c["red"], r=1.4)
        return True
    if name == "camera-web":
        c.path("M18 36 h12 l4 7 h-20 z", c.grad(c["case"]))
        c.circle(24, 20, 16, c.grad(c["case"]))
        c.circle(24, 20, 8, _dark(c))
        c.circle(24, 20, 4, c.grad(c.lighten(c["screen"][0], 0.2), c["screen"][1]), width=0.8)
        if not c.small:
            c.circle(22.5, 18.5, 1.3, "#ffffff", None)
        _led(c, 24, 8, col=c["green"], r=1.4)
        return True
    if name == "computer":
        monitor(c, 7, 2, 34, 24, stand=False)
        c.path("M20 26 h8 v2 h-8 z", c.grad(c["case"]), width=1)
        case(c, 3, 26, 42, 18, 5)
        c.line("M3 37 H40", c["case_dark"], 1)
        c.rect(6, 34, 12, 2, c.darken(c["case"][1], 0.2), 0.5, width=0.7)
        _led(c, 36, 40, col=c["green"])
        return True
    if name == "computer-laptop":
        c.path("M8 6 h32 a2 2 0 0 1 2 2 v24 h-36 v-24 a2 2 0 0 1 2 -2 z", _dark(c))
        _desktop(c, 9, 9, 30, 20)
        c.path("M6 32 h36 l4 7 a1.5 1.5 0 0 1 -1.5 2 h-41 a1.5 1.5 0 0 1 -1.5 -2 z", c.grad(c["metal"]))
        if not c.small:
            c.line("M9 35 H39 M8 37.5 H40", c.darken(c["metal"][1], 0.15), 1)
        return True
    if name == "cpu":
        if not c.small:
            for i in range(6):
                p = 11.5 + i * 5
                c.line(f"M{p} 4 v6 M{p} 38 v6 M4 {p} h6 M38 {p} h6", c.darken(c["metal"][1], 0.1), 2)
        else:
            c.line("M14 4 v6 M24 4 v6 M34 4 v6 M14 38 v6 M24 38 v6 M34 38 v6 "
                   "M4 14 h6 M4 24 h6 M4 34 h6 M38 14 h6 M38 24 h6 M38 34 h6", "ink", 2)
        c.rect(9, 9, 30, 30, _dark(c), 2.5)
        c.rect(16, 16, 16, 16, c.grad(c.lighten(c["yellow"], 0.3), c.darken(c["yellow"], 0.2)), 1.5)
        c.circle(13, 13, 1.2, c["metal"][0], None)
        return True
    if name == "memory":
        pcb = c.grad(c.lighten(c["green"], 0.1), c.darken(c["green"], 0.3))
        c.path("M3 14 h42 v18 h-20 v-2 h-2 v2 h-20 z", pcb)
        for i in range(4):
            c.rect(6 + i * 9.6, 17, 7, 9, _dark(c), 0.8, width=0.9)
        if not c.small:
            for i in range(19):
                if 9 <= i <= 10:
                    continue
                c.rect(4.5 + i * 2.1, 32, 1.3, 3, c["yellow"], 0, None)
        else:
            c.line("M5 33 H21 M27 33 H43", c["yellow"], 2)
        return True
    if name in ("printer", "cups", "cupsprinter"):
        printer_body(c)
        if name == "cups":
            overlay(c, "network", "blue", 27, 2, 19)
        elif name == "cupsprinter":
            overlay(c, "gear", "violet", 27, 2, 19)
        return True
    if name == "printer-laser":
        printer_body(c, laser=True)
        return True
    if name == "scanner":
        c.path("M6 28 L14 6 h28 l-6 22 z", c.grad(c["case_top"]))
        c.path("M10 26 L16 9 h22 l-4 17 z", c.grad(c.lighten(c["grey"], 0.5), c["grey"]), width=1)
        case(c, 2, 26, 44, 16, 5)
        c.rect(5, 35, 20, 3, c.lighten(c["green"], 0.3), 1, width=0.8)
        _led(c, 37, 36.5, col=c["green"])
        return True
    if name.startswith("drive-"):
        return _drives(name[6:], c)
    if name.startswith("media-optical") or name.startswith("media-write"):
        return _optical(name, c)
    if name == "media-flash-memory-stick":
        c.path("M6 14 h34 l3 3 v14 l-3 3 h-34 a2 2 0 0 1 -2 -2 v-16 a2 2 0 0 1 2 -2 z",
               c.grad(c.lighten(c["violet"], 0.25), c.darken(c["violet"], 0.2)))
        c.rect(10, 18, 18, 12, c.lighten(c["violet"], 0.7), 1, width=0.9)
        for i in range(4):
            c.rect(32 + i * 2.4, 18, 1.5, 12, c["yellow"], 0, None if c.small else 0.4)
        if not c.small:
            c.line("M13 22 h12 M13 26 h8", c.darken(c["violet"], 0.2), 1.2)
        return True
    if name == "media-flash-sd-mmc":
        c.path("M14 4 h22 a2 2 0 0 1 2 2 v36 a2 2 0 0 1 -2 2 h-24 a2 2 0 0 1 -2 -2 v-34 z",
               c.grad(c.lighten(c["blue"], 0.25), c.darken(c["blue"], 0.2)))
        for i in range(5):
            c.rect(16 + i * 4, 6, 2.4, 6, c["yellow"], 0.4, None if c.small else 0.5)
        c.rect(13, 18, 22, 21, "#ffffff", 1.5, width=0.9)
        c.path("M10 16 h-1.5 v5 h1.5", "none", "ink", 1)
        if not c.small:
            c.text(24, 32, "SD", 9, c["blue"])
        return True
    if name == "media-floppy":
        body = c.grad(c.lighten(c["grey"], 0.05), c.darken(c["grey"], 0.45))
        c.path("M6 4 h33 l3 3 v35 a2 2 0 0 1 -2 2 h-34 a2 2 0 0 1 -2 -2 v-36 a2 2 0 0 1 2 -2 z", body)
        c.rect(14, 4, 20, 13, c.grad(c["metal"], horizontal=True), 1)
        c.rect(27, 6.5, 4, 8, body, 0.5, width=0.8)
        c.rect(10, 23, 28, 21, "#ffffff", 1.5)
        if not c.small:
            c.line("M13 29 H35 M13 33 H35 M13 37 H30", c["red"], 1)
        return True
    if name == "input-dialpad":
        c.rect(8, 3, 32, 42, c.grad(c["case"]), 4)
        for r in range(4):
            for i in range(3):
                col = c.grad(c["case_top"]) if r < 3 else c.lighten(c["grey"], 0.4)
                c.rect(12 + i * 9, 6 + r * 9.6, 6.5, 7, col, 1.5, width=1)
        return True
    if name == "input-gaming":
        c.path("M14 13 h20 c7 0 10 6 11 14 c1 8 -2 12 -6 12 c-3 0 -5 -4 -8 -6 h-14 c-3 2 -5 6 -8 6 "
               "c-4 0 -7 -4 -6 -12 c1 -8 4 -14 11 -14 z", c.grad(c["metal"]))
        c.path("M11 20 h4 v4 h4 v4 h-4 v4 h-4 v-4 h-4 v-4 h4 z", _dark(c), width=1)
        for (x, y), col in zip(((35, 20), (39, 25), (31, 25), (35, 30)), ("green", "red", "blue", "yellow")):
            c.circle(x, y, 2.4, c[col], width=0.9)
        return True
    if name == "input-keyboard":
        keyboard(c)
        return True
    if name == "input-keyboard-virtual":
        keyboard(c, 3, 8, 42, 30, virtual=True)
        glyph(c, "touch", 28, 25, 20, ink, width=2.0)
        return True
    if name == "input-mouse":
        mouse(c)
        return True
    if name == "input-mouse-battery":
        mouse(c, cable=False)
        overlay(c, "battery", "green", 26, 26, 20)
        return True
    if name == "input-tablet":
        c.path("M3 14 h38 l4 26 h-38 z", _dark(c))
        c.path("M10 19 h26 l2.8 16 h-26 z", c.lighten(c["grey"], 0.35), width=0.9)
        c.path("M44 4 l3 3 l-18 19 l-5 2 l2 -5 z", c.grad(c.lighten(c["blue"], 0.3), c["blue"]), width=1.1)
        return True
    if name == "input-touchpad":
        c.rect(5, 6, 38, 36, c.grad(c["metal"]), 3)
        c.rect(9, 9, 30, 22, c.grad(c.lighten(c["grey"], 0.6), c.lighten(c["grey"], 0.3)), 2, width=1)
        c.rect(9, 33, 14.5, 6, c.grad(c["case_top"]), 1.5, width=1)
        c.rect(24.5, 33, 14.5, 6, c.grad(c["case_top"]), 1.5, width=1)
        if not c.small:
            c.path("M18 24 C20 19 26 17 30 16", "none", c["blue"], 1.4)
            c.circle(30, 16, 2, c["blue"], None)
        return True
    if name == "input-touchscreen":
        c.rect(4, 6, 40, 30, _dark(c), 3)
        c.rect(7, 9, 34, 24, c.grad(c["screen"]), 1, width=0.9)
        c.circle(22, 18, 5, "none", "#ffffff", 1.4)
        glyph(c, "touch", 14, 14, 30, ink, width=2.0)
        return True
    if name == "input-tvremote":
        c.rect(15, 3, 18, 42, _dark(c), 6)
        c.circle(24, 8, 2.4, c["red"], width=0.8)
        c.circle(24, 18, 5.5, c.lighten(c["grey"], 0.3), width=1)
        c.circle(24, 18, 2, _dark(c), None)
        for r in range(3):
            for i in range(3):
                c.rect(18 + i * 4.5, 27 + r * 4.5, 3, 3, c.lighten(c["grey"], 0.5), 0.8, None)
        c.rect(18, 40, 3, 2, c["green"], 0.5, None)
        c.rect(22.5, 40, 3, 2, c["yellow"], 0.5, None)
        c.rect(27, 40, 3, 2, c["blue"], 0.5, None)
        return True
    if name.startswith("keyboard-caps-"):
        state = name[14:]
        key(c, 5, 7, 38, 36, pressed=(state == "locked"))
        d = 2 if state == "locked" else 0
        glyph(c, "caps", 12, 10 + d, 22, c["ink"] if state != "disabled" else c.lighten(c["grey"], 0.25),
              width=2.4 if not c.small else 3.0)
        _led(c, 35, 13 + d, state != "disabled", r=2.6)
        if state == "locked":
            overlay(c, "lock", "orange", 27, 27, 20)
        return True
    if name == "keyboard-enter":
        c.path("M18 5 h24 v38 h-38 v-18 h14 z", c.darken(c["case"][1], 0.2))
        c.path("M21 7 h18 v30 h-32 v-10 h14 z", c.grad(c["case_top"]), width=1)
        glyph(c, "enter-key", 13, 15, 22, ink, width=2.6 if not c.small else 3.2)
        return True
    if name == "keyboard-spacebar":
        key(c, 2, 14, 44, 22)
        glyph(c, "spacebar", 12, 10, 24, ink, width=2.4 if not c.small else 3.0)
        return True
    if name == "multimedia-player-ipod-mini-blue":
        c.rect(12, 3, 24, 42, c.grad(c.lighten(c["blue"], 0.35), c.darken(c["blue"], 0.15)), 5)
        c.rect(15, 7, 18, 12, c.lighten(c["grey"], 0.6), 1, width=1)
        if not c.small:
            c.line("M17 11 h12 M17 14 h9", c["grey"], 1)
        c.circle(24, 32, 9, c.lighten(c["blue"], 0.75), width=1)
        c.circle(24, 32, 3.5, c.lighten(c["blue"], 0.35), width=1)
        return True
    if name == "network-bluetooth":
        c.rect(9, 3, 30, 42, _g(c, c["blue"]), 15)
        glyph(c, "bluetooth", 8, 8, 32, "#ffffff", width=2.8 if not c.small else 3.4)
        return True
    if name == "network-modem":
        c.line("M36 18 L40 4", "ink", 2)
        case(c, 3, 16, 42, 20, 6)
        for i, col in enumerate(("green", "green", "yellow", "orange", "green")):
            _led(c, 8 + i * 5, 29, col=c[col], r=1.5)
        c.rect(32, 27, 5, 4, _dark(c), 0.5, width=0.7)
        glyph(c, "phone", 2, 2, 14, c["blue"], width=2.6)
        return True
    if name in ("network-rj11-female", "network-rj45-female"):
        rj45 = "rj45" in name
        c.rect(5, 5, 38, 38, c.grad(c["case"]), 4)
        if not c.small:
            c.circle(24, 9, 1.4, c["case_dark"], width=0.8)
            c.circle(24, 39, 1.4, c["case_dark"], width=0.8)
        w = 24 if rj45 else 16
        x = 24 - w / 2
        c.path(f"M{x} 14 h{w} v16 h-{w / 2 - 4} v4 h-8 v-4 h-{w / 2 - 4} z", _dark(c))
        n = 8 if rj45 else 4
        for i in range(n):
            xx = 24 - (n - 1) * 1.4 + i * 2.8 if rj45 else 24 - (n - 1) * 1.8 + i * 3.6
            c.line(f"M{xx:.2f} 15.5 v6", c["yellow"], 1.1 if rj45 else 1.6)
        return True
    if name == "network-vpn":
        c.path("M24 3 L41 9 V22 C41 33 33 41 24 45 C15 41 7 33 7 22 V9 Z", _g(c, c["green"]))
        glyph(c, "lock", 12, 12, 24, "#ffffff", width=2.8 if not c.small else 3.4)
        return True
    if name in ("network-wired-activated", "network-wired-unavailable"):
        c.path("M24 30 V36 C24 42 30 44 36 44", "none", "ink", 5 if not c.small else 3.5)
        c.path("M24 30 V36 C24 42 30 44 36 44", "none", c["blue"], 3 if not c.small else 1.8)
        c.path("M13 6 h22 v18 l-4 6 h-14 l-4 -6 z", c.grad(c.lighten(c["page"][1], 0.3), c.darken(c["page"][1], 0.1)))
        for i in range(8 if not c.small else 4):
            step = 2.4 if not c.small else 4.4
            xx = 24 - (7 if not c.small else 3) * step / 2 + i * step
            c.line(f"M{xx:.2f} 7 v6", c["yellow"], 1 if not c.small else 1.4)
        c.rect(19, 24, 10, 3, c.lighten(c["grey"], 0.3), 0.5, width=0.8)
        if name.endswith("activated"):
            overlay(c, "check", "green", 28, 2, 18)
        else:
            overlay(c, "cross", "red", 28, 2, 18)
        return True
    if name.startswith("network-wireless-connected-"):
        wireless(c, int(name.rsplit("-", 1)[1]) // 25)
        return True
    if name == "network-wireless-disconnected":
        wireless(c, 0)
        overlay(c, "cross", "red", 27, 25, 20)
        return True
    if name == "network-wireless-hotspot":
        for r in (8, 15):
            for s in (-1, 1):
                d = f"M{24 + s * r * 0.6:.2f} {16 - r * 0.8:.2f} A{r} {r} 0 0 {1 if s > 0 else 0} {24 + s * r * 0.6:.2f} {16 + r * 0.8:.2f}"
                c.parts.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{3.6 + c.lw * 1.6:g}" stroke-linecap="round"/>')
                c.parts.append(f'<path d="{d}" fill="none" stroke="{c["blue"]}" stroke-width="3.6" stroke-linecap="round"/>')
        c.line("M24 16 V32", "ink", 2.2)
        c.circle(24, 16, 3.5, c["blue"])
        case(c, 8, 30, 32, 14, 4)
        for i in range(3):
            _led(c, 14 + i * 5, 38.5, col=c["green"], r=1.4)
        return True
    if name == "phone-apple-iphone":
        phone(c, home=True)
        return True
    if name == "smartphone":
        phone(c, home=False, col=c["grey"])
        return True
    if name == "phone-battery":
        phone(c, 6, 3, home=False, col=c["grey"])
        overlay(c, "battery", "green", 26, 26, 20)
        return True
    if name == "tablet":
        c.rect(2, 7, 44, 34, _dark(c), 4)
        _desktop(c, 6, 10, 34, 28)
        c.circle(43, 24, 1.5, c.lighten(c["grey"], 0.3), width=0.7)
        return True
    if name == "uav-quadcopter":
        c.line("M11 11 L37 37 M37 11 L11 37", "ink", 4 if not c.small else 3)
        c.line("M11 11 L37 37 M37 11 L11 37", c["metal"][1], 2 if not c.small else 1.2)
        for x, y in ((10, 10), (38, 10), (10, 38), (38, 38)):
            c.circle(x, y, 8, c.lighten(c["grey"], 0.65), width=1)
            if not c.small:
                c.line(f"M{x - 6} {y + 1} L{x + 6} {y - 1}", c["ink"], 1.4)
            c.circle(x, y, 2, _dark(c), width=0.6)
        c.rect(17, 17, 14, 14, _g(c, c["red"]), 3)
        c.circle(24, 24, 2.6, _dark(c), width=0.8)
        return True
    if name == "video-display":
        monitor(c)
        return True
    if name == "video-display-brightness":
        def sun(cv, x, y, w, h):
            cv.rect(x, y, w, h, cv.grad(cv["screen"]), 1, width=1)
            glyph(cv, "sun", x + w / 2 - 9, y + h / 2 - 9, 18, cv["yellow"], width=2.8 if not cv.small else 3.4)
        monitor(c, screen=sun)
        return True
    if name == "video-television":
        c.line("M18 9 L12 2 M30 9 L36 2", "ink", 1.8)
        c.rect(3, 9, 42, 30, c.grad(c.lighten(c["brown"], 0.4), c["brown"]), 4)
        c.rect(7, 13, 26, 22, c.grad(c["screen"]), 4, width=1)
        if not c.small:
            c.path("M10 17 q4 -2 8 -1", "none", "#ffffff", 1.2)
        c.circle(39, 18, 2.6, c.grad(c["metal"]), width=0.9)
        c.circle(39, 26, 2.6, c.grad(c["metal"]), width=0.9)
        c.line("M10 39 l-2 5 M38 39 l2 5", "ink", 2.4)
        return True
    return None


def _drives(n, c):
    if n == "multidisk":
        drive(c, 4, 4, 40, 20)
        drive(c, 4, 22, 40, 20)
        return True
    if n == "optical":
        drive(c, 4, 6, 40, 24, light=False)
        c.path("M4 30 h34 l-2 8 h-30 z", c.grad(c["case_top"]))
        c.ellipse(21, 34, 12, 3.2, c.grad(c.lighten(c["metal"][1], 0.6), c["metal"][1]), width=1)
        c.ellipse(21, 34, 3, 0.9, c["case_dark"], None)
        glyph(c, "eject", 31, 18, 7, c["ink"], width=2.4)
        return True
    if n == "removable-media":
        c.rect(3, 18, 11, 12, c.grad(c["metal"]), 1)
        if not c.small:
            c.rect(5, 21, 3, 2, c["ink"], 0, None)
            c.rect(5, 25, 3, 2, c["ink"], 0, None)
        c.rect(13, 14, 32, 20, _g(c, c["blue"]), 5)
        c.rect(20, 18, 16, 12, c.lighten(c["blue"], 0.6), 1.5, width=0.9)
        _led(c, 40.5, 24, col=c["red"], r=1.5)
        return True
    drive(c)
    plaque = {"harddisk": None, "harddisk-encrypted": ("lock", "violet"), "harddisk-root": ("hash", "red"),
              "partition": ("partition", "cyan"), "multipartition": ("multipartition", "orange")}
    if n not in plaque:
        return None
    if plaque[n]:
        overlay(c, plaque[n][0], plaque[n][1], 26, 26, 20)
    return True


OPTICAL = {   # name: (tint, word on the disc, plaque glyph, plaque colour)
    "media-optical": (None, None, None, None),
    "media-optical-audio": (None, None, "music", "red"),
    "media-optical-blu-ray": ("blue", "BD", None, None),
    "media-optical-data": ("yellow", None, "pages", "blue"),
    "media-optical-dvd": ("violet", "DVD", None, None),
    "media-optical-mixed-cd": (None, None, "multipartition", "orange"),
    "media-optical-recordable": ("green", "R", None, None),
    "media-optical-video": (None, None, "film", "violet"),
    "media-write-cd": ("green", None, "pencil", "red"),
    "media-write-dvd": ("violet", None, "pencil", "red"),
}


def _optical(name, c):
    if name not in OPTICAL:
        return None
    tint, word, g, col = OPTICAL[name]
    disc(c, c[tint] if tint else None, word)
    if name == "media-optical-mixed-cd":
        overlay(c, "music", "red", 26, 26, 20)
        overlay(c, "pages", "blue", 2, 26, 20)
        return True
    if g:
        overlay(c, g, col, 26, 26, 20)
    return True
