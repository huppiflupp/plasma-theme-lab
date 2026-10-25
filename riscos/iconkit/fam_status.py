"""fam_status.py: status icons (the system tray's world, 16-22 px).

Levels are filled segments or a fill height (battery, wireless fan,
mobile bars, volume waves, microphone, thermometer, quota); states are a
round plaque at the lower right (base.overlay) with their own glyph and
colour. Input methods show what they really show: their letter, on a
key cap (fcitx-*) or a round badge (ime-*). Programs with a logo of
their own (chat clients, file sync, torrent …) get a generic object with
their state instead.
"""
import math

from base import action, disc
from base import overlay as _overlay
from glyphs import D, F, O, S, glyph, reg

# ---- own glyphs -------------------------------------------------------------


@reg("status-wall")
def _(c, k): S(c, "M3 5 H21 V19 H3 Z M3 9.7 H21 M3 14.3 H21 M9 5 V9.7 M15 5 V9.7 M6 9.7 V14.3 M12 9.7 V14.3 M18 9.7 V14.3 M9 14.3 V19 M15 14.3 V19", k)


@reg("status-handset")
def _(c, k): F(c, "M5 3 L9 3 L11 8 L8.5 10 C9.5 12.5 11.5 14.5 14 15.5 L16 13 L21 15 V19 A2 2 0 0 1 19 21 C10 21 3 14 3 5 A2 2 0 0 1 5 3 Z", k)


@reg("status-waveform")
def _(c, k): S(c, "M3 12 H5 M7 8 V16 M10 4 V20 M13 7 V17 M16 10 V14 M19 6 V18 M21 12 H22", k)


@reg("status-halfmoon")
def _(c, k): O(c, 12, 12, 7.5, k); F(c, "M12 4.5 A7.5 7.5 0 0 0 12 19.5 Z", k)


@reg("status-fullmoon")
def _(c, k): D(c, 12, 12, 8.5, k)


@reg("status-transfer")
def _(c, k): S(c, "M8 3 V19 M4 15 L8 19 L12 15 M16 21 V5 M12 9 L16 5 L20 9", k)


@reg("status-vault")
def _(c, k): S(c, "M3 4 H21 V19 H3 Z M6 19 V21 M18 19 V21", k); O(c, 12, 11.5, 4, k); S(c, "M12 7.5 V9 M12 14 V15.5 M8 11.5 H9.5 M14.5 11.5 H16", k)


@reg("status-gpu")
def _(c, k): S(c, "M2 6 H22 V17 H2 Z M5 17 V20 H13 V17", k); O(c, 15, 11.5, 3.5, k); S(c, "M5 9 H9 M5 13 H9", k)


@reg("status-devices")
def _(c, k): S(c, "M2 7 H13 V16 H2 Z M0.5 19 H14.5 M16 5 H22 V20 H16 Z M18 17.5 H20", k)


@reg("status-mesh")
def _(c, k):
    S(c, "M5 6 L19 6 L12 19 Z", k)
    for x, y in ((5, 6), (19, 6), (12, 19)):
        D(c, x, y, 3, k)


# ---- plaque glyphs for 16/22 px: few strokes, filled where possible -----------


def _star_d(cx=12, cy=12.5, r1=9.5, r2=4):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = r1 if i % 2 == 0 else r2
        pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


@reg("status-s-clock")
def _(c, k): S(c, "M12 4.5 V12.5 L17.5 16", k)            # the plaque is the face
@reg("status-s-lock")
def _(c, k): F(c, "M5 11 H19 V21 H5 Z", k); S(c, "M8.5 11 V8 A3.5 3.5 0 0 1 15.5 8 V11", k, 3.2)
@reg("status-s-hourglass")
def _(c, k): F(c, "M5 3 H19 L12 12 Z M12 12 L19 21 H5 Z", k)
@reg("status-s-moon")
def _(c, k): F(c, "M14 3 A9 9 0 1 0 21 15 A7 7 0 1 1 14 3 Z", k)
@reg("status-s-star")
def _(c, k): F(c, _star_d(), k)
@reg("status-s-ring")
def _(c, k): O(c, 12, 12, 6.5, k, w=3.4)                   # invisible: hollow
@reg("status-s-envelope")
def _(c, k): S(c, "M3 6 H21 V18 H3 Z M3 6 L12 13 L21 6", k, 2.8)
@reg("status-s-speaker-off")
def _(c, k): F(c, "M2 8.5 H7 L12 4 V20 L7 15.5 H2 Z", k); S(c, "M15 9 L21 15 M21 9 L15 15", k, 3)
@reg("status-s-battery")
def _(c, k): F(c, "M2 7 H19 V17 H2 Z M19 10 H22 V14 H19 Z", k)
@reg("status-s-sun")
def _(c, k): D(c, 12, 12, 5, k); S(c, "M12 1.5 V4 M12 20 V22.5 M1.5 12 H4 M20 12 H22.5", k, 3)
@reg("status-s-palette")
def _(c, k): F(c, "M12 3 C7 9 5 12 5 15 A7 7 0 0 0 19 15 C19 12 17 9 12 3 Z", k)
@reg("status-s-globe")
def _(c, k): O(c, 12, 12, 8, k, w=2.8); S(c, "M4 12 H20 M12 4 V20", k, 2.6)
@reg("status-s-calendar")
def _(c, k): F(c, "M4 5 H20 V9 H4 Z", k); S(c, "M4 9 V20 H20 V9", k, 2.8)
@reg("status-s-bell")
def _(c, k): F(c, "M5 17 C7 15 7 13 7 10 A5 5 0 0 1 17 10 C17 13 17 15 19 17 Z M10 19 H14 A2 2 0 0 1 10 19 Z", k)
@reg("status-s-shield")
def _(c, k): F(c, "M12 2.5 L20 6 V11 C20 16 17 19.5 12 21.5 C7 19.5 4 16 4 11 V6 Z", k)
@reg("status-s-camera")
def _(c, k): F(c, "M2 7 H7 L9 4 H15 L17 7 H22 V20 H2 Z", k)
@reg("status-s-keyboard")
def _(c, k): S(c, "M2 7 H22 V17 H2 Z M7 13 H17", k, 2.8)
@reg("status-s-flame")
def _(c, k): F(c, "M12 2 C14 7 19 9 19 15 A7 7 0 0 1 5 15 C5 11 8 10 9 6 C10 9 11 10 12 10 C12 7 11 5 12 2 Z", k)
@reg("status-s-leaf")
def _(c, k): F(c, "M4 20 C4 9 10 3 21 3 C21 14 15 20 4 20 Z", k)
@reg("status-s-z")
def _(c, k): S(c, "M6 5 H18 L6 19 H18", k, 3.4)
@reg("status-s-bluetooth")
def _(c, k): S(c, "M6 8 L17 16 L12 20.5 V3.5 L17 8 L6 16", k, 2.8)
@reg("status-s-eye-off")
def _(c, k): O(c, 12, 12, 6.5, k, w=3.4)


# glyph name -> (the plaque's glyph at 16/22 px, its line width)
SMALL_PLAQUE = {
    "clock": ("status-s-clock", 4.2), "lock": ("status-s-lock", 3.2), "hourglass": ("status-s-hourglass", 3),
    "moon": ("status-s-moon", 3), "star": ("status-s-star", 3), "eye-off": ("status-s-ring", 3.4),
    "envelope": ("status-s-envelope", 2.8), "speaker-off": ("status-s-speaker-off", 3),
    "battery": ("status-s-battery", 3), "sun": ("status-s-sun", 3), "palette": ("status-s-palette", 3),
    "globe": ("status-s-globe", 2.8), "calendar": ("status-s-calendar", 2.8), "bell": ("status-s-bell", 3),
    "shield": ("status-s-shield", 3), "camera": ("status-s-camera", 3), "keyboard": ("status-s-keyboard", 2.8),
    "flame": ("status-s-flame", 3), "leaf": ("status-s-leaf", 3), "zzz": ("status-s-z", 3.4),
    "bluetooth": ("status-s-bluetooth", 2.8), "repeat": ("repeat", 3.2), "sync": ("sync", 3.2),
    "power": ("power", 3.6), "download": ("download", 3.8), "forbidden": ("forbidden", 3.4),
    "question": ("question", 3), "info": ("info", 3), "exclamation": ("exclamation", 3),
}


# ---- helpers ------------------------------------------------------------------


def _sector(cx, cy, r1, r2, a1, a2):
    def p(r, a):
        return f"{cx + r * math.cos(math.radians(a)):.2f} {cy + r * math.sin(math.radians(a)):.2f}"
    if r1 <= 0:
        return f"M{cx} {cy} L{p(r2, a1)} A{r2} {r2} 0 0 1 {p(r2, a2)} Z"
    return (f"M{p(r2, a1)} A{r2} {r2} 0 0 1 {p(r2, a2)} L{p(r1, a2)} "
            f"A{r1} {r1} 0 0 0 {p(r1, a1)} Z")


def overlay(c, name, color="green", x=26, y=26, size=20):
    """base.overlay, but at 16/22 px larger and bolder so the state reads."""
    if not c.small:
        return _overlay(c, name, color, x, y, size)
    s2 = 25
    x2 = min(x, 48 - s2) if x > 12 else 0
    y2 = min(y, 48 - s2)
    r = s2 / 2
    c.circle(x2 + r, y2 + r, r, c[color], width=0.9)
    g, w = SMALL_PLAQUE.get(name, (name, 4.2))
    glyph(c, g, x2 + s2 * 0.15, y2 + s2 * 0.15, s2 * 0.7, "#ffffff", width=w)
    return True


def _off(c):
    return c.lighten(c["grey"], 0.6)


def _slash(c, color=None):
    """A red bar across the drawing: switched off."""
    col = color or c["red"]
    c.line("M9 9 L39 39", "#ffffff", 7)
    c.line("M9 9 L39 39", col, 4)


def obj(c, g, accent="blue", badge=None, badge_color="green", grey=False):
    """A thing drawn large (action style, accent halo), optional badge."""
    if grey:
        glyph(c, g, 6, 6, 36, _off(c), width=6 if not c.small else 7)
        glyph(c, g, 6, 6, 36, c["grey"], width=None if not c.small else 3.0)
        if badge:
            overlay(c, badge, badge_color)
        return True
    action(c, g, accent, None, fill=g)
    if badge:
        overlay(c, badge, badge_color)
    return True


def _bolt(c, x, y, s):
    c.group(f"translate({x:g} {y:g}) scale({s:g})",
            lambda cv: cv.path("M13 3 L5 13 H11 L10 21 L19 10 H13 Z", "#ffffff", "ink", 1.4 / s))


# ---- battery ------------------------------------------------------------------

PROFILE = {"performance": ("flame", "red"), "balanced": ("equals", "blue"), "powersave": ("leaf", "green")}


def battery(c, level=None, charging=False, profile=None, missing=False):
    y0 = 5 if profile else 13
    c.rect(41, y0 + 7, 4, 8, c.grad(c["metal"]), 1)
    c.rect(3, y0, 38, 22, c.grad(c["page"]) if not missing else _off(c), 3)
    if level is not None:
        if level == 0:
            c.rect(6, y0 + 3, 32, 16, c.lighten(c["red"], 0.75), 1.5, None)
        else:
            col = c["red"] if level <= 10 else c["orange"] if level <= 30 else c["green"]
            w = 32 * level / 100
            c.rect(6, y0 + 3, w, 16, c.grad(c.lighten(col, 0.3), col), 1.5, None)
            if not c.small and level < 100:
                c.line(f"M{6 + w:g} {y0 + 3} v16", c.darken(col, 0.3), 1)
    if missing:
        c.line(f"M14 {y0 + 4} L30 {y0 + 18} M30 {y0 + 4} L14 {y0 + 18}", c["red"], 3.4)
    if charging:
        _bolt(c, 10, y0 - 1.5, 1.05)
    if profile:
        g, col = PROFILE[profile]
        overlay(c, g, col, x=25, y=25, size=22)
    return True


def battery_name(name):
    if name == "battery-missing":
        return dict(missing=True)
    parts = name.split("-")[1:]
    d = {}
    if parts and parts[0].isdigit():
        d["level"] = int(parts.pop(0))
    if parts and parts[0] == "charging":
        d["charging"] = True
        parts.pop(0)
    if parts[:1] == ["profile"] and len(parts) == 2 and parts[1] in PROFILE:
        d["profile"] = parts[1]
        parts = []
    return d if not parts else None


# ---- wireless fan -----------------------------------------------------------------

FAN = [(0, 5), (8.5, 13), (16, 20.5), (23.5, 28), (31, 35.5)]


def fan(c, lit, color=None, cx=24, cy=42, unlit=None):
    """The wireless fan: 5 segments, `lit` of them in colour."""
    col = color or c["blue"]
    for i, (r1, r2) in enumerate(FAN):
        fill = c.grad(c.lighten(col, 0.3), col) if i < lit else (unlit or _off(c))
        c.path(_sector(cx, cy, r1, r2, -132, -48), fill, "ink", 0.9)


def wireless(name, c):
    rest = name[len("network-wireless-"):]
    parts = rest.split("-")
    state = None
    if parts[0] == "connected":
        parts.pop(0)
        state = "connected"
    if parts[0].isdigit():
        lvl = int(parts[0]) // 20
        st = parts[1] if len(parts) > 1 else state
        if len(parts) > 2 or st not in (None, "limited", "locked", "connected"):
            return None
        if st is None:
            fan(c, lvl)
            return True
        fan(c, lvl, cx=21, cy=40)
        g, col = {"limited": ("exclamation", "orange"), "locked": ("lock", "green"),
                  "connected": ("check", "blue")}[st]
        return overlay(c, g, col, x=27, y=27, size=19)
    if rest == "acquiring":
        fan(c, 0, unlit=c.lighten(c["blue"], 0.6))
        return overlay(c, "hourglass", "orange", x=27, y=27, size=19)
    if rest == "available":
        fan(c, 0, cx=21, cy=40)
        return overlay(c, "plus", "blue", x=27, y=27, size=19)
    if rest == "off":
        fan(c, 0, cx=21, cy=40)
        return overlay(c, "cross", "red", x=27, y=27, size=19)
    if rest == "on":
        fan(c, 5, c["green"])
        return True
    if rest == "bluetooth":
        fan(c, 5, c["cyan"], cx=21, cy=40)
        return overlay(c, "bluetooth", "blue", x=26, y=26, size=20)
    return None


# ---- mobile bars --------------------------------------------------------------------

TECH = {"5g": "5G", "edge": "E", "gprs": "G", "umts": "3G", "lte": "4G", "hspa": "H", "hsdpa": "H", "hsupa": "H"}


def bars(c, lit, color=None):
    col = color or c["blue"]
    for i in range(5):
        x = 19 + i * 5.6
        h = 8 + i * 7.5
        fill = c.grad(c.lighten(col, 0.3), col) if i < lit else _off(c)
        c.rect(x, 43 - h, 4.6, h, fill, 0.8, "ink", 0.8)


def mobile(name, c):
    rest = name[len("network-mobile-"):]
    if rest == "available":
        bars(c, 0)
        return overlay(c, "plus", "blue", x=1, y=24, size=19)
    if rest == "off":
        bars(c, 0)
        return overlay(c, "cross", "red", x=1, y=24, size=19)
    parts = rest.split("-")
    if not parts[0].isdigit():
        return None
    lvl = int(parts.pop(0)) // 20
    locked = parts[-1:] == ["locked"]
    if locked:
        parts.pop()
    tech = parts[0] if parts else None
    if len(parts) > 1 or (tech and tech not in TECH):
        return None
    bars(c, lvl)
    if tech:
        word = TECH[tech]
        hplus = tech in ("hsdpa", "hsupa", "hspa")
        size = (17 if len(word) == 1 else 14) * (1.3 if c.small else 1)
        tx = (7 if c.small else 7.5) if hplus else (9 if c.small else 10)
        c.text(tx, 18 if not c.small else 19, word, size, c["ink"])
        if hplus:
            # the H+ variants: down, up or both directions beside the H
            ax = 17 if c.small else 16
            d = {"hsdpa": f"M{ax} 3 v9 M{ax - 3} 9 l3 3.5 l3 -3.5",
                 "hsupa": f"M{ax} 12.5 v-9 M{ax - 3} 6.5 l3 -3.5 l3 3.5",
                 "hspa": f"M{ax} 4 v8 M{ax - 3.5} 8 h7"}[tech]
            c.path(d, "none", "ink", 1.8)
    if locked:
        overlay(c, "lock", "green", x=1, y=26, size=18)
    return True


# ---- speaker, microphone ---------------------------------------------------------------


def speaker(c, waves, color=None, x=0):
    c.path(f"M{4 + x} 18 H{12 + x} L{22 + x} 9 V39 L{12 + x} 30 H{4 + x} Z", c.grad(c["metal"]))
    col = color or c["ink"]
    for i, r in enumerate((7, 13, 19)):
        if waves is None:
            break
        c.path(f"M{24 + x + r * 0.62:.2f} {24 - r * 0.78:.2f} A{r} {r} 0 0 1 {24 + x + r * 0.62:.2f} {24 + r * 0.78:.2f}",
               "none", col if i < waves else _off(c), 3.4)


def mic(c, fill_level=None, body=None, x=0):
    """A microphone; fill_level: the capsule filled from below (0..1)."""
    c.path(f"M{11 + x} 22 A13 13 0 0 0 {37 + x} 22 M{24 + x} 35 V42 M{16 + x} 43 H{32 + x}", "none", "ink", 2.6)
    c.rect(17 + x, 4, 14, 26, body or c.grad(c["metal"], horizontal=True), 7)
    if fill_level:
        h = 26 * fill_level
        top = 30 - h
        col = c["green"] if fill_level < 0.9 else c["orange"]
        if h >= 19:
            c.path(f"M{17 + x} {top + 7 if h >= 26 else top} "
                   + (f"A7 7 0 0 1 {31 + x} {top + 7} " if h >= 26 else f"H{31 + x} ")
                   + f"V23 A7 7 0 0 1 {17 + x} 23 Z", c.grad(c.lighten(col, 0.3), col))
        else:
            c.path(f"M{17 + x} {top} H{31 + x} V23 A7 7 0 0 1 {17 + x} 23 Z", c.grad(c.lighten(col, 0.3), col))


# ---- people, chat -----------------------------------------------------------------------

PRESENCE = {"available": ("check", "green"), "online": ("dot", "green"), "away": ("clock", "orange"),
            "busy": ("minus", "red"), "idle": ("moon", "violet"), "invisible": ("eye-off", "grey"),
            "offline": ("cross", "grey")}


def person(c, faded=False, hollow=False):
    fill = c.grad(c.lighten(c["blue"], 0.35), c["blue"]) if not faded else _off(c)
    if hollow:
        fill = "#ffffff"
    c.circle(20, 13, 8, fill)
    c.path("M5 42 C5 30 11 25 20 25 C29 25 35 30 35 42 Z", fill)


def bubble(c, faded=False):
    c.path("M4 6 H40 A3 3 0 0 1 43 9 V29 A3 3 0 0 1 40 32 H20 L10 41 V32 H7 A3 3 0 0 1 4 29 V9 A3 3 0 0 1 7 6 Z",
           c.grad(c["page"]) if not faded else _off(c))
    if not c.small:
        c.line("M10 14 H34 M10 21 H28", c["grey"], 2)


# ---- input methods ----------------------------------------------------------------------

CJK = "Noto Sans CJK SC,Noto Sans CJK JP,Noto Sans CJK KR,Noto Serif CJK SC,sans-serif"

IM = {"anthy": "あ", "libkkc": "か", "libskk": "ス", "bopomofo": "ㄅ", "chewing": "酷", "cangjie": "倉",
      "erbi": "二", "hangul": "한", "pinyin": "拼", "quanpin": "全", "shuangpin": "双", "sunpinyin": "S",
      "googlepinyin": "G", "rime": "中", "unikey": "Vi", "wubi": "五", "wbpy": "五拼", "wubipinyin": "五拼",
      "ziranma": "自", "chinese-simplified": "简", "chinese-traditional": "繁",
      "punctuation-fullwidth": "，。", "punctuation-halfwidth": ",."}


def _chars(c, s, x, y, col, size=None):
    latin = all(ord(ch) < 0x2000 for ch in s)
    size = size or ((24 if len(s) == 1 else 17) if latin else (25 if len(s) == 1 else 17))
    fam = "TeX Gyre Heros,Helvetica,Arial,sans-serif" if latin else CJK
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    c.parts.append(f'<text x="{x:g}" y="{y + size * 0.36:g}" font-family="{fam}" font-size="{size:g}" '
                   f'font-weight="bold" text-anchor="middle" fill="{col}">{s}</text>')


def keycap(c, faded=False):
    c.rect(5, 5, 38, 38, c["case_dark"] if not faded else c["grey"], 6)
    c.rect(5, 5, 38, 34, c.grad(c["case_top"]) if not faded else _off(c), 6)


def badge_disc(c, faded=False):
    c.circle(24, 24, 20, c.grad(c.lighten(c["blue"], 0.25), c.darken(c["blue"], 0.15)) if not faded else _off(c))


def libmark(c):
    """libpinyin variants: a green corner on the cap."""
    c.path("M5 18 V11 A6 6 0 0 1 11 5 H18 Z", c["green"], "ink", 0.9)


def input_method(name, c):
    fc = name.startswith("fcitx")
    rest = name[6:] if fc else name[4:]
    if fc and name == "fcitx":
        keycap(c)
        glyph(c, "language", 12, 9, 24, c["ink"], width=2.2 if not c.small else 3.2)
        return True
    lib = False
    if rest.endswith("-libpinyin"):
        rest, lib = rest[:-10], True
    if rest.startswith("libpinyin-"):
        rest, lib = rest[10:], True
    state = None
    for suf in ("-active", "-inactive", "-on", "-off"):
        if rest.endswith(suf):
            rest, state = rest[:-len(suf)], suf[1:]
    faded = state in ("inactive", "off")
    base = keycap if fc else badge_disc
    ink = (c["ink"] if not faded else c["grey"]) if fc else ("#ffffff" if not faded else c["grey"])
    cy = 21 if fc else 24
    if rest in IM and state is None:
        base(c)
        if lib:
            libmark(c)
        _chars(c, IM[rest], 24, cy, ink)
        return True
    if lib:
        return None
    glyphs = {"chttrans": None, "fullwidth": "status-fullmoon", "halfwidth": "status-halfmoon",
              "handwriting": "pen", "punc": None, "remind": "lightbulb", "vk": "keyboard", "kbd": "keyboard",
              "emoji": "smile"}
    if fc and rest == "chttrans" and state:
        base(c, faded)
        _chars(c, "繁" if state == "active" else "简", 24, cy, ink)
        return True
    if fc and rest == "punc" and state:
        base(c, faded)
        _chars(c, "，。", 24, cy, ink)
        return True
    if fc and rest == "fullwidth" and state:
        base(c, faded)
        glyph(c, "status-fullmoon" if state == "active" else "status-halfmoon", 12, cy - 12, 24, ink, width=2.4)
        return True
    if rest in ("fullwidth", "halfwidth") and not fc and state is None:
        base(c)
        glyph(c, glyphs[rest], 12, 12, 24, ink, width=2.4)
        return True
    if rest in glyphs and glyphs[rest] and (state is not None or rest in ("kbd", "emoji")):
        if rest == "vk":
            # the virtual keyboard: a keyboard on a screen
            base(c, faded)
            c.rect(9, 10, 30, 20, c.grad(c["screen"]) if not faded else c["grey"], 2, "ink", 0.9)
            glyph(c, "keyboard", 12, 8, 24, "#ffffff", width=2.2)
            return True
        base(c, faded)
        glyph(c, glyphs[rest], 12, cy - 12, 24, ink, width=2.2 if not c.small else 3.0)
        return True
    return None


# ---- the table of simple ones ---------------------------------------------------------------
# name: (kind, args)   kind: obj (glyph, accent, badge, badge colour) | disc (colour, glyph)

SIMPLE = {
    # data, state, security
    "data-error": ("obj", "database", "blue", "cross", "red"),
    "data-information": ("obj", "database", "blue", "info", "blue"),
    "data-question": ("obj", "database", "blue", "question", "violet"),
    "data-success": ("obj", "database", "blue", "check", "green"),
    "data-warning": ("obj", "database", "blue", "exclamation", "orange"),
    "state-download": ("disc", "blue", "download"),
    "state-error": ("disc", "red", "cross"),
    "state-information": ("disc", "blue", "info"),
    "state-offline": ("disc", "grey", "power"),
    "state-ok": ("disc", "green", "check"),
    "state-pause": ("disc", "orange", "pause"),
    "state-sync": ("disc", "cyan", "sync"),
    "state-warning": ("disc", "yellow", "exclamation"),
    "firewall-applet": ("obj", "status-wall", "brown"),
    "firewall-applet-error": ("obj", "status-wall", "brown", "cross", "red"),
    "firewall-applet-panic": ("obj", "status-wall", "red", "forbidden", "red"),
    "firewall-applet-shields_up": ("obj", "status-wall", "brown", "shield", "green"),
    # updates and software
    "software-updates-additional": ("obj", "box", "brown", "plus", "blue"),
    "software-updates-important": ("obj", "box", "brown", "exclamation", "orange"),
    "software-updates-inactive": ("grey", "box"),
    "software-updates-release": ("obj", "box", "brown", "arrow-up-double", "violet"),
    "software-updates-security": ("obj", "box", "brown", "shield", "red"),
    "software-updates-updates": ("obj", "box", "brown", "arrow-down", "green"),
    "kpackagekit-important": ("obj", "bag", "orange", "exclamation", "red"),
    "kpackagekit-inactive": ("grey", "bag"),
    "kpackagekit-security": ("obj", "bag", "orange", "lock", "red"),
    "kpackagekit-updates": ("obj", "bag", "orange", "download", "blue"),
    "update-none": ("disc", "grey", "check"),
    "update-low": ("disc", "green", "arrow-down"),
    "update-medium": ("disc", "orange", "arrow-down"),
    "update-high": ("disc", "red", "arrow-down-double"),
    "update-busy": ("disc", "blue", "refresh"),
    "install": ("act", "box", "green", "plus"),
    "uninstall": ("act", "box", "red", "minus"),
    # tasks, appointments
    "task-complete": ("obj", "clipboard-check", "green"),
    "task-recurring": ("obj", "repeat", "cyan"),
    "task-reminder": ("obj", "bell", "yellow"),
    "appointment-recurring": ("obj", "calendar", "blue", "repeat", "cyan"),
    "appointment-reminder": ("obj", "calendar", "blue", "bell", "orange"),
    "meeting-organizer": ("obj", "users", "blue", "calendar", "violet"),
    "kalarm-disabled": ("grey", "alarm", "cross", "red"),
    "kalarm-partdisabled": ("obj", "alarm", "orange", "minus", "orange"),
    # devices and inputs
    "camera-on": ("obj", "video-camera", "green", "dot", "green"),
    "camera-off": ("grey", "video-camera", "cross", "red"),
    "camera-ready": ("obj", "video-camera", "blue", "check", "blue"),
    "input-keyboard-battery": ("obj", "keyboard", "blue", "battery", "green"),
    "input-keyboard-brightness": ("obj", "keyboard", "blue", "sun", "orange"),
    "input-keyboard-color": ("obj", "keyboard", "blue", "palette", "violet"),
    "input-keyboard-virtual-on": ("obj", "tablet", "blue", "keyboard", "green"),
    "input-keyboard-virtual-off": ("grey", "tablet", "keyboard", "red"),
    "input-touchpad-on": ("obj", "touchpad", "blue", "check", "green"),
    "input-touchpad-off": ("grey", "touchpad", "cross", "red"),
    "keyboard-layout": ("obj", "keyboard", "blue", "globe", "blue"),
    "auth-sim-locked": ("obj", "simcard", "orange", "lock", "red"),
    "auth-sim-missing": ("grey", "simcard", "question", "red"),
    "printer-error": ("obj", "printer", "blue", "cross", "red"),
    "printer-warning": ("obj", "printer", "blue", "exclamation", "orange"),
    "network-wired-available": ("obj", "ethernet", "blue", "plus", "blue"),
    "network-wired-activated-limited": ("obj", "ethernet", "blue", "exclamation", "orange"),
    "network-wired-activated-locked": ("obj", "ethernet", "blue", "lock", "green"),
    "network-limited": ("obj", "network", "blue", "exclamation", "orange"),
    "network-unavailable": ("grey", "network", "cross", "red"),
    "network-bluetooth-activated": ("disc", "blue", "bluetooth"),
    "video-card-inactive": ("grey", "status-gpu"),
    "video-off": ("grey", "video-camera", None, None, "slash"),
    "waveform-off": ("grey", "status-waveform", None, None, "slash"),
    "media-playback-playing": ("obj", "music", "blue", "play", "green"),
    "media-playback-paused": ("obj", "music", "blue", "pause", "orange"),
    "media-playback-stopped": ("obj", "music", "blue", "stop", "grey"),
    # mail, chat, programs
    "mail-unread": ("obj", "envelope", "yellow"),
    "mail-unread-new": ("obj", "envelope", "yellow", "star", "red"),
    "telegram-panel": ("disc", "cyan", "send"),
    "irc-channel-joined": ("obj", "hash", "blue", "arrow-right", "green"),
    "irc-channel-parted": ("obj", "hash", "blue", "arrow-left", "red"),
    "dropboxstatus-logo": ("disc", "blue", "box"),
    "dropboxstatus-idle": ("obj", "box", "blue", "check", "green"),
    "dropboxstatus-busy": ("obj", "box", "blue", "sync", "blue"),
    "dropboxstatus-x": ("obj", "box", "blue", "cross", "red"),
    "cloudstatus": ("obj", "cloud", "cyan", "check", "green"),
    "crow-translate-tray": ("disc", "violet", "language"),
    "org.kde.CrowTranslate-tray": ("obj", "language", "violet"),
    "flameshot-tray": ("obj", "selection", "red", "camera", "red"),
    "kdeconnect-tray": ("obj", "status-devices", "blue"),
    "transmission-tray-icon": ("disc", "red", "status-transfer"),
    "haguichi-connected": ("obj", "status-mesh", "green", "check", "green"),
    "haguichi-disconnected": ("grey", "status-mesh", "cross", "red"),
    "apport": ("obj", "crash", "orange"),
    "script-error": ("obj", "terminal", "grey", "exclamation", "red"),
    "plasmavault_error": ("obj", "status-vault", "violet", "cross", "red"),
    "image-missing": ("grey", "picture", "question", "red"),
    "showinfo": ("tile", "blue", "info"),
    "dialog-password": ("obj", "key", "yellow", "lock", "blue"),
    "system-suspend-inhibited": ("obj", "moon", "violet", "forbidden", "red"),
    "system-suspend-uninhibited": ("obj", "moon", "violet", "zzz", "blue"),
    "redshift-status-day": ("obj", "sun", "yellow"),
    "redshift-status-on": ("obj", "night", "orange"),
    "redshift-status-off": ("grey", "sun", None, None, "slash"),
    "flightmode-on": ("obj", "airplane-mode", "orange"),
    "flightmode-off": ("grey", "airplane-mode", None, None, "slash"),
    "input-caps-on": ("cap", "caps"),
    "input-num-on": ("captext", "1"),
    "input-combo-on": ("cap", "plus"),
}


def simple(name, c):
    e = SIMPLE.get(name)
    if not e:
        return None
    kind = e[0]
    if kind == "obj":
        g, acc = e[1], e[2]
        badge, bc = (e[3], e[4]) if len(e) > 3 else (None, None)
        return obj(c, g, acc, badge, bc)
    if kind == "grey":
        g = e[1]
        badge, bc = (e[2], e[3]) if len(e) > 3 else (None, None)
        obj(c, g, grey=True, badge=badge, badge_color=bc)
        if len(e) > 4 and e[4] == "slash":
            _slash(c)
        return True
    if kind == "disc":
        col = c[e[1]]
        disc(c, col, e[2], "#ffffff" if e[1] != "yellow" else c["ink"])
        return True
    if kind == "tile":
        from base import tile
        return tile(c, c[e[1]], e[2])
    if kind == "act":
        return action(c, e[1], None, "arrow-down" if e[3] == "plus" else "cross", e[2])
    if kind == "cap":
        keycap(c)
        glyph(c, e[1], 12, 9, 24, c["ink"], width=2.4 if not c.small else 3.2)
        c.circle(36, 12, 4, c["led"], width=0.8)
        return True
    if kind == "captext":
        keycap(c)
        _chars(c, e[1], 24, 21, c["ink"], size=24)
        c.circle(36, 12, 4, c["led"], width=0.8)
        return True
    return None


# ---- draw -------------------------------------------------------------------------------------


def draw(name, c):
    try:
        return _draw(name, c)
    except Exception as e:  # noqa: BLE001 - never raise into the builder
        import sys
        print(f"  fam_status: {name}: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def _draw(name, c):
    if name.startswith("battery-"):
        if name.startswith("battery-profile-"):
            p = name[16:]
            if p not in PROFILE:
                return None
            g, col = PROFILE[p]
            disc(c, c[col], g)
            return True
        d = battery_name(name)
        return battery(c, **d) if d is not None else None
    if name.startswith("network-wireless-"):
        return wireless(name, c)
    if name.startswith("network-mobile-"):
        return mobile(name, c)
    if name.startswith("fcitx") or name.startswith("ime-"):
        return input_method(name, c)
    if name.startswith("audio-volume-"):
        lvl = name[13:]
        if lvl == "muted":
            speaker(c, None)
            c.line("M28 17 L42 31 M42 17 L28 31", c["red"], 3.6)
            return True
        waves = {"low": 1, "medium": 2, "high": 3, "high-warning": 3, "high-danger": 3}.get(lvl)
        if waves is None:
            return None
        col = {"high-warning": c["orange"], "high-danger": c["red"]}.get(lvl)
        speaker(c, waves, col)
        if lvl == "high-danger":
            c.circle(41, 8, 5, c["red"], width=0.9)
            if not c.small:
                c.line("M41 5 v3.5", "#ffffff", 1.8)
                c.circle(41, 10.8, 0.9, "#ffffff", None)
        return True
    if name in ("audio-on", "audio-ready"):
        speaker(c, 2, x=-2)
        return overlay(c, "power" if name == "audio-on" else "check", "green" if name == "audio-on" else "blue",
                       x=27, y=27, size=19)
    if name.startswith("microphone-sensitivity-"):
        lvl = name[23:]
        if lvl == "muted":
            mic(c, x=-3)
            return overlay(c, "cross", "red", x=27, y=27, size=19)
        f = {"low": 0.35, "medium": 0.65, "high": 1.0}.get(lvl)
        if f is None:
            return None
        mic(c, f)
        return True
    if name == "mic-on":
        mic(c, body=c.grad(c.lighten(c["red"], 0.3), c["red"]))
        return True
    if name == "mic-ready":
        mic(c, x=-3)
        return overlay(c, "check", "blue", x=27, y=27, size=19)
    if name == "mic-off":
        mic(c, body=_off(c))
        _slash(c)
        return True
    if name.startswith("user-"):
        st = name[5:]
        if st not in PRESENCE:
            return None
        g, col = PRESENCE[st]
        person(c, faded=st in ("offline",), hollow=st == "invisible")
        return overlay(c, g, col, x=25, y=25, size=21)
    if name.startswith("pidgin-tray-"):
        st = name[12:]
        g, col = {"available": ("check", "green"), "away": ("clock", "orange"), "busy": ("minus", "red"),
                  "email": ("envelope", "blue"), "invisible": ("eye-off", "grey"),
                  "offline": ("power", "grey")}.get(st, (None, None))
        if not g:
            return None
        bubble(c, faded=st == "offline")
        return overlay(c, g, col, x=25, y=25, size=21)
    if name in ("konv_message", "quassel_message", "quassel_inactive", "telegram-attention-panel",
                "telegram-mute-panel"):
        if name.startswith("telegram"):
            disc(c, c["cyan"], "send")
            if name.endswith("attention-panel"):
                return overlay(c, "exclamation", "red", x=27, y=27, size=19)
            return overlay(c, "speaker-off", "grey", x=27, y=27, size=19)
        bubble(c, faded=name == "quassel_inactive")
        if name == "konv_message":
            return overlay(c, "star", "orange", x=25, y=25, size=21)
        if name == "quassel_message":
            return overlay(c, "dot", "red", x=25, y=25, size=21)
        return True
    if name.startswith("haguichi-connecting-"):
        n = int(name[-1])
        obj(c, "status-mesh", "yellow")
        for i in range(3):
            c.circle(30 + i * 6, 41, 2.6, c["orange"] if i < n else _off(c), width=0.8)
        return True
    if name.startswith("task-process-"):
        n = int(name[-1])
        c.circle(24, 24, 18, _off(c) if n < 4 else c.grad(c.lighten(c["green"], 0.3), c["green"]))
        if 0 < n < 4:
            a = -90 + 90 * n
            large = 1 if n > 2 else 0
            ex, ey = 24 + 18 * math.cos(math.radians(a)), 24 + 18 * math.sin(math.radians(a))
            c.path(f"M24 24 V6 A18 18 0 {large} 1 {ex:.2f} {ey:.2f} Z", c.grad(c.lighten(c["blue"], 0.3), c["blue"]))
        if n == 0:
            c.circle(24, 24, 4, c["grey"], None)
        return True
    if name.startswith("disk-quota"):
        lvl = {"disk-quota": 0.5, "disk-quota-low": 0.25, "disk-quota-high": 0.75, "disk-quota-critical": 0.96}.get(name)
        if lvl is None:
            return None
        col = {"disk-quota": c["blue"], "disk-quota-low": c["green"], "disk-quota-high": c["orange"],
               "disk-quota-critical": c["red"]}[name]
        c.rect(4, 8, 40, 18, c.grad(c["case"]), 2.5)
        c.circle(36, 17, 2.5, c["led"] if name != "disk-quota-critical" else c["red"], width=0.8)
        if not c.small:
            c.line("M9 17 H26", c["case_dark"], 2)
        c.rect(4, 31, 40, 10, _off(c), 2)
        c.rect(4, 31, 40 * lvl, 10, c.grad(c.lighten(col, 0.3), col), 2)
        return True
    if name.startswith("temperature-"):
        lvl = {"cold": (0.2, "blue"), "normal": (0.5, "green"), "warm": (0.85, "red")}.get(name[12:])
        if not lvl:
            return None
        f, col = lvl
        col = c[col]
        c.path("M18 31 V9 A6 6 0 0 1 30 9 V31 A10 10 0 1 1 18 31 Z", "#ffffff")
        c.circle(24, 38, 6.5, col, None)
        top = 33 - 24 * f
        c.rect(21, top, 6, 36 - top, col, 1.5, None)
        if not c.small:
            for y in (12, 18, 24):
                c.line(f"M31 {y} h4", c["ink"], 1.2)
        return True
    if name.startswith("rotation-"):
        st = name[9:]
        if st == "allowed":
            c.rect(16, 6, 16, 28, c.grad(c["case"]), 3)
            c.rect(19, 10, 10, 18, c.grad(c["screen"]), 1, None)
            c.path("M8 30 A17 17 0 0 0 40 30", "none", c["blue"], 3)
            c.path("M35 25 L41 31 L33 33 Z", c["blue"], None)
            return True
        if st == "locked-landscape":
            c.rect(3, 12, 32, 18, c.grad(c["case"]), 3)
            c.rect(7, 15, 24, 12, c.grad(c["screen"]), 1, None)
        elif st == "locked-portrait":
            c.rect(10, 3, 18, 32, c.grad(c["case"]), 3)
            c.rect(13, 7, 12, 24, c.grad(c["screen"]), 1, None)
        else:
            return None
        return overlay(c, "lock", "orange", x=26, y=26, size=20)
    if name in ("starred", "semi-starred", "non-starred"):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 20 if i % 2 == 0 else 8.5
            pts.append(f"{24 + r * math.cos(a):.2f} {25 + r * math.sin(a):.2f}")
        d = "M" + " L".join(pts) + " Z"
        if name == "starred":
            c.path(d, c.grad(c.lighten(c["yellow"], 0.3), c["yellow"]))
        elif name == "semi-starred":
            c.path(d, "#ffffff")
            # the left half filled (from the star's points left of the middle)
            c.path(f"M24 5 L{pts[9]} L{pts[8]} L{pts[7]} L{pts[6]} L24 {25 + 8.5:.2f} Z", c["yellow"], None)
            c.path(d, "none")
        else:
            c.path(d, "#ffffff")
        return True
    if name in ("call-incoming", "call-missed", "call-outgoing"):
        col = {"call-incoming": "green", "call-missed": "red", "call-outgoing": "blue"}[name]
        glyph(c, "status-handset", 4, 10, 34, c.grad(c.lighten(c[col], 0.2), c.darken(c[col], 0.15)))
        arrow = {"call-incoming": "M44 4 L30 18 M30 9 V18 H39", "call-outgoing": "M30 18 L44 4 M35 4 H44 V13",
                 "call-missed": "M29 6 L36 13 L44 5 M44 11 V5 H38"}[name]
        c.path(arrow, "none", c[col], 3.2)
        return True
    if name.startswith("security-"):
        lv = {"high": ("green", "check"), "medium": ("yellow", "exclamation"), "low": ("red", "cross")}.get(name[9:])
        if not lv:
            return None
        col, g = lv
        c.path("M24 4 L40 10 V22 C40 32 33 39 24 44 C15 39 8 32 8 22 V10 Z",
               c.grad(c.lighten(c[col], 0.3), c.darken(c[col], 0.1)))
        glyph(c, g, 13, 12, 22, c["ink"] if col == "yellow" else "#ffffff", width=3.2)
        return True
    if name in ("network-flightmode-on", "network-flightmode-off"):
        # the radio side of flight mode: the signal bars, the plane over them
        on = name.endswith("on")
        bars(c, 0 if on else 5)
        glyph(c, "airplane-mode", 1, 1, 30, c["ink"], width=7 if c.small else 5.5)
        glyph(c, "airplane-mode", 1, 1, 30, c["orange"] if on else "#ffffff", width=3.6 if c.small else 2.6)
        return True
    if name in ("touchpad_enabled", "touchpad_disabled"):
        # the pad itself, solid, with its two buttons; a finger on it when on
        on = name.endswith("enabled")
        body = c.grad(c["case"]) if on else _off(c)
        c.rect(5, 5, 38, 38, body, 4)
        c.rect(9, 9, 30, 21, c.grad(c["metal"]) if on else c["grey"], 2)
        c.rect(9, 33, 14.5, 6, c["case_dark"], 1.5)
        c.rect(24.5, 33, 14.5, 6, c["case_dark"], 1.5)
        if on:
            c.circle(28, 19, 5, c["green"], width=1.2)
        else:
            _slash(c)
        return True
    if name == "network-bluetooth-activated-locked":
        disc(c, c["blue"], "bluetooth")
        return overlay(c, "lock", "green", x=27, y=27, size=19)
    return simple(name, c)
