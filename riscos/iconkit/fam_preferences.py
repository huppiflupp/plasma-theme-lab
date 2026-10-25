"""fam_preferences.py: the preferences category, after RISC OS's !Configure
plug-ins: every setting is an object, not a tile.

A family shares a body and differs by a secondary element:

  preferences-desktop-*        a monitor; what is set is shown on its screen
  hardware settings            the device itself (keyboard, mouse, …)
  preferences-system-*         !Configure's red cog with the subject on a plaque
  preferences-system-network-* a globe with the subject on a plaque
  …-network-server-*           a server tower with the subject on a plaque
  preferences-security-*       a shield
  preferences-web-browser-*    a browser window (a window with a globe)
  preferences-system-windows-* a RISC OS window
  preferences-virtualization-* a RISC PC case

The family's base setting carries a small green cog (the "settings" mark)
where its relatives carry a plaque.
"""
import math

from base import case as risc_case, page
from glyphs import glyph, reg, S, D, O


# ---- helpers ---------------------------------------------------------------
def G(c, name, x, y, size, col=None, small_w=None):
    """A glyph with a heavier line at 16/22 px."""
    w = None
    if c.small:
        w = small_w or (3.4 if size >= 18 else 4.4)
    glyph(c, name, x, y, size, col or c["ink"], width=w)


def cog_path(cx, cy, r, teeth=8):
    ri = r * 0.74
    w = math.pi / teeth
    pts = []
    for i in range(teeth):
        a = i * 2 * w - math.pi / 2
        for ang, rad in ((a - w * 0.62, ri), (a - w * 0.38, r), (a + w * 0.38, r), (a + w * 0.62, ri)):
            pts.append(f"{cx + rad * math.cos(ang):.2f} {cy + rad * math.sin(ang):.2f}")
    return "M" + " L".join(pts) + " Z"


def cog(c, cx, cy, r, col, teeth=8, hub=True):
    w = (0.75 if c.small else 1.1) if r < 10 else None
    c.path(cog_path(cx, cy, r, teeth), c.grad(c.lighten(col, 0.35), c.darken(col, 0.12)), width=w)
    if hub:
        c.circle(cx, cy, r * 0.3, "#ffffff")


def marker(c):
    """The settings mark: a small green cog at the lower right."""
    cog(c, 39, 39, 9.5 if c.small else 8.5, c["green"])
    return True


def plaque(c, name, col=None, cx=34, cy=34):
    """The subject on a white round plaque at the lower right."""
    r = 13.5 if c.small else 12.5
    c.circle(cx, cy, r, "#ffffff")
    s = 17 if c.small else 15.5
    if callable(name):
        name(c, cx, cy, s)
    else:
        col = c[col] if col in c.w else (col or c["ink"])
        glyph(c, name, cx - s / 2, cy - s / 2, s, col, width=4.0 if c.small else 2.5)
    return True


def scaled(c, x, y, k, fn):
    c.group(f"translate({x:g} {y:g}) scale({k:g})", fn)


# ---- bodies ----------------------------------------------------------------
def monitor_body(c):
    c.path("M18 35 h12 l2 5 h-16 z", c["case_dark"])
    c.rect(10, 39, 28, 5, c.grad(c["case"]), 2)
    c.rect(3, 4, 42, 32, c.grad(c["case_top"][0], c["case"][1]), 3)
    c.rect(7, 8, 34, 24, c.grad(c["screen"]), 1.5)


def monitor(c, content=None):
    monitor_body(c)
    if isinstance(content, str):
        G(c, content, 14, 10, 20, "#ffffff")
    elif isinstance(content, tuple):
        G(c, content[0], 14, 10, 20, c[content[1]])
    elif content:
        content(c)
    return marker(c)


def globe(c, cx=20, cy=20, r=17):
    c.circle(cx, cy, r, c.grad(c.lighten(c["cyan"], 0.25), c.darken(c["blue"], 0.1)))
    lc = c.lighten(c["cyan"], 0.75)
    w = 1.2 if not c.small else 1.0
    c.ellipse(cx, cy, r * 0.42, r, "none", lc, w)
    c.line(f"M{cx - r} {cy} H{cx + r}", lc, w)
    if not c.small:
        c.line(f"M{cx - r * 0.86} {cy - r * 0.5} H{cx + r * 0.86} M{cx - r * 0.86} {cy + r * 0.5} H{cx + r * 0.86}", lc, w)
    c.circle(cx, cy, r, "none")


def tower(c):
    c.rect(7, 2, 24, 42, c.grad(c["case"]), 2.5)
    c.rect(7, 2, 24, 4, c.grad(c["case_top"]), 2)
    for y in (9, 16):
        c.rect(10, y, 18, 5, c.grad(c["case_top"]), 1, width=0.9)
        if not c.small:
            c.line(f"M12 {y + 2.5} H20", c["case_dark"], 1.2)
    if not c.small:
        c.line("M11 26 H20 M11 29 H20 M11 32 H20", c["case_dark"], 1.2)
    c.circle(12, 39, 1.8, c["led"], width=0.8)


def window_body(c, x=3, y=4, w=36, h=32):
    c.rect(x, y, w, h, c.grad(c["page"]), 1.5)
    c.rect(x, y, w, 7, c.grad(c["case_top"]), 1.5)
    if not c.small:
        c.rect(x + 1.5, y + 1.5, 4, 4, c["case"][0], 0.5, width=0.8)
        c.rect(x + 6.5, y + 1.5, 4, 4, c["case"][0], 0.5, width=0.8)
        c.rect(x + w - 5.5, y + 1.5, 4, 4, c["case"][0], 0.5, width=0.8)
    c.rect(x + w - 5, y + 7, 5, h - 7, c.grad(c["case"], horizontal=True), 0, width=1)
    c.rect(x + w - 4, y + 10, 3, 9, c.grad(c.lighten(c["blue"], 0.45), c["blue"]), 1, width=0.8)
    c.rect(x, y, w, h, "none", 1.5)


def browser(c):
    window_body(c)
    globe(c, 17, 21, 9)


def shield(c, col=None):
    col = col or c["blue"]
    c.path("M20 3 L36 9 V20 C36 30 29 36 20 41 C11 36 4 30 4 20 V9 Z",
           c.grad(c.lighten(col, 0.35), c.darken(col, 0.15)))
    if not c.small:
        c.path("M20 6 L33 11 V16 C25 14 15 14 7 16 V11 Z", "#ffffff", None, opacity=0.25)


def cogbody(c):
    cog(c, 18, 18, 16, c["red"], 10)


def pc_case(c):
    risc_case(c, 2, 8, 40, 26, 7)
    c.rect(6, 22, 12, 7, c.grad(c["screen"]), 1, width=0.9)
    c.rect(8, 23.5, 8, 4, "none", 0, "#ffffff", 0.9)
    c.line("M22 25 H31", c["case_dark"], 1.6)
    c.circle(31, 29, 1.4, c["led"], width=0.7)


def container(c):
    c.rect(3, 10, 36, 24, c.grad(c.lighten(c["orange"], 0.2), c.darken(c["orange"], 0.15)), 1.5)
    rib = c.darken(c["orange"], 0.35)
    for x in range(7, 37, 4 if not c.small else 6):
        c.line(f"M{x} 13 V31", rib, 1.4)
    c.rect(3, 10, 36, 3, c.darken(c["orange"], 0.2), 1, width=1)


def harddisk(c):
    risc_case(c, 2, 12, 40, 22, 7)
    if not c.small:
        for x in range(6, 22, 3):
            c.line(f"M{x} 24 V30", c["case_dark"], 1.1)
    else:
        c.line("M6 27 H20", c["case_dark"], 2)
    c.circle(29, 27, 2, c["orange"], width=0.8)


def chip(c, cx=21, cy=21):
    m = c["metal"][1]
    pins = ""
    for i in range(4):
        p = cx - 7.5 + i * 5
        pins += f"M{p} {cy - 15} V{cy - 11} M{p} {cy + 11} V{cy + 15} M{cx - 15} {p - cx + cy} H{cx - 11} M{cx + 11} {p - cx + cy} H{cx + 15} "
    c.line(pins, m, 2.4)
    c.rect(cx - 12, cy - 12, 24, 24, c.grad(c.lighten("#30343b", 0.2), "#30343b"), 2.5)
    c.rect(cx - 7, cy - 7, 14, 14, c.grad(c["metal"]), 1.5, width=0.9)
    c.text(cx, cy + 2.6, "CPU", 7.5, "#30343b")


def optical(c, cx=21, cy=21):
    c.circle(cx, cy, 17, c.grad(c.lighten(c["cyan"], 0.75), c["metal"][1]))
    if not c.small:
        c.path(f"M{cx - 11} {cy - 8} A13.5 13.5 0 0 1 {cx + 4} {cy - 13}", "none", c.lighten(c["violet"], 0.4), 3)
        c.path(f"M{cx + 11} {cy + 8} A13.5 13.5 0 0 1 {cx - 4} {cy + 13}", "none", c.lighten(c["yellow"], 0.2), 3)
    c.circle(cx, cy, 6, "#ffffff", width=1)
    c.circle(cx, cy, 2.5, c["case"][1], width=1)


def page_body(c, lines=True):
    page(c, lines=lines)


# ---- devices drawn for the hardware settings --------------------------------
def keyboard(c):
    c.rect(2, 14, 44, 20, c.grad(c["case"]), 3)
    c.path("M5 14 L8 10 H40 L43 14 Z", c.grad(c["case_top"]))
    key = c["case_top"][0]
    if not c.small:
        for row, y in enumerate((17, 21.5, 26)):
            for i in range(9):
                c.rect(4.5 + row * 0.8 + i * 4.3, y, 3.4, 3.4, key, 0.6, width=0.6)
        c.rect(12, 30.5, 20, 2.3, key, 0.6, width=0.6)
        c.rect(34, 30.5, 3.4, 2.3, c["red"], 0.6, width=0.6)
    else:
        for y in (18, 25):
            for i in range(5):
                c.rect(5 + i * 7.6, y, 5.6, 4.6, key, 0.8, width=0.6)


def keycaps(c):
    for x, label in ((2, "Ctrl"), (23, "C")):
        c.rect(x, 9, 19, 20, c["case_dark"], 3.5)
        c.rect(x + 2, 9.5, 15, 15, c.grad(c["case_top"]), 2.5, width=0.9)
        c.text(x + 9.5, 20.5 if label == "C" else 19.5, label, 11 if label == "C" else 7, c["ink"])


def mouse(c):
    c.path("M8 30 C8 40 34 40 34 30 V17 C34 9 8 9 8 17 Z", c.grad(c["case"]))
    c.path("M8 20 V17 C8 9 34 9 34 17 V20 Z", c.grad(c["metal"]))
    c.line("M17.5 10.6 V20 M24.5 10.6 V20", c["ink"], 1.3)
    c.path("M8 30 C8 40 34 40 34 30 V17 C34 9 8 9 8 17 Z", "none")
    c.line("M21 10 C21 5 25 2 31 3", "ink", 1.6)


def touchpad(c):
    c.rect(3, 6, 38, 32, c.grad(c["metal"]), 3)
    c.rect(8, 9, 28, 18, c.grad(c.lighten(c["metal"][1], 0.25), c["metal"][1]), 2, width=1)
    c.rect(8, 29.5, 13.5, 5, c.lighten(c["metal"][1], 0.4), 1.5, width=1)
    c.rect(22.5, 29.5, 13.5, 5, c.lighten(c["metal"][1], 0.4), 1.5, width=1)


def gtablet(c):
    dark = c.darken(c["metal"][1], 0.45)
    c.rect(2, 12, 38, 26, c.grad(c.darken(c["metal"][0], 0.45), dark), 3)
    c.rect(7, 16, 26, 18, c.grad(c.darken(c["metal"][0], 0.2), c.darken(c["metal"][1], 0.25)), 1.5, width=1)
    c.path("M36 3 L41 8 L25 24 L19 26 L21 20 Z", c.grad(c.lighten(c["blue"], 0.3), c["blue"]))
    c.path("M21 20 L25 24", "none")


def touchscreen(c):
    dark = c.darken(c["metal"][1], 0.45)
    c.rect(8, 2, 26, 40, c.grad(c.darken(c["metal"][0], 0.35), dark), 4)
    c.rect(11, 6, 20, 30, c.grad(c["screen"]), 1.5, width=1)
    G(c, "touch", 12, 13, 20, "#ffffff")


def speaker(c):
    c.rect(8, 2, 26, 40, c.grad(c.lighten(c["brown"], 0.3), c.darken(c["brown"], 0.1)), 2.5)
    c.circle(21, 11, 4.5, c.grad(c["metal"]))
    c.circle(21, 28, 10, c.grad(c.darken(c["metal"][0], 0.2), c.darken(c["metal"][1], 0.3)))
    c.circle(21, 28, 3.5, c.grad(c["metal"]), width=1)


def joystick(c):
    c.path("M6 38 L9 28 H33 L36 38 Z", c.grad(c.darken(c["metal"][0], 0.3), c.darken(c["metal"][1], 0.4)))
    c.ellipse(21, 28, 7, 2.5, c["metal"][1], width=1)
    c.rect(19.3, 12, 3.4, 16, c.grad(c["metal"], horizontal=True), 1, width=1)
    c.circle(21, 10, 6.5, c.grad(c.lighten(c["red"], 0.3), c.darken(c["red"], 0.1)))
    c.ellipse(12.5, 28.5, 3, 1.6, c["red"], width=0.9)


def printer(c):
    c.rect(12, 3, 18, 14, c.grad(c["page"]), 0.5, width=1)
    c.rect(3, 14, 36, 16, c.grad(c["case"]), 2.5)
    c.rect(3, 14, 36, 4, c.grad(c["case_top"]), 2, width=1)
    c.path("M9 30 H33 L35 37 H7 Z", c.grad(c["page"]))
    if not c.small:
        c.line("M12 33 H28", "#7a8699", 1.2)
    c.circle(33, 22, 1.6, c["led"], width=0.7)


def scanner(c):
    c.path("M2 22 L8 14 H40 L34 22 Z", c.grad(c["case_top"]))
    c.rect(2, 22, 32, 10, c.grad(c["case"]), 1.5)
    c.path("M34 22 L40 14 V24 L34 32 Z", c["case_dark"])
    c.line("M10 18 H34", c["cyan"], 2.2 if not c.small else 1.6)
    c.circle(29, 27, 1.5, c["led"], width=0.7)


def clock(c):
    c.circle(9, 9, 5, c.grad(c.lighten(c["yellow"], 0.3), c.darken(c["yellow"], 0.2)))
    c.circle(33, 9, 5, c.grad(c.lighten(c["yellow"], 0.3), c.darken(c["yellow"], 0.2)))
    c.line("M11 37 L8 42 M31 37 L34 42", "ink", 2)
    c.circle(21, 24, 16, c.grad(c.lighten(c["blue"], 0.3), c.darken(c["blue"], 0.1)))
    c.circle(21, 24, 12, "#ffffff", width=1)
    if not c.small:
        for i in range(12):
            a = i * math.pi / 6
            c.line(f"M{21 + 10 * math.cos(a):.2f} {24 + 10 * math.sin(a):.2f} L{21 + 11.3 * math.cos(a):.2f} {24 + 11.3 * math.sin(a):.2f}", "ink", 1)
    c.line("M21 24 V15.5 M21 24 L27 27", "ink", 1.8)
    c.line("M21 24 L15 30", c["red"], 1)


def usbstick(c):
    def body(cv):
        cv.rect(14, 4, 12, 11, cv.grad(cv["metal"], horizontal=True), 1)
        cv.rect(16.5, 7, 2.5, 2.5, cv.darken(cv["metal"][1], 0.3), 0, None)
        cv.rect(21, 7, 2.5, 2.5, cv.darken(cv["metal"][1], 0.3), 0, None)
        cv.rect(12, 14, 16, 26, cv.grad(cv.lighten(cv["blue"], 0.3), cv.darken(cv["blue"], 0.1)), 3)
        cv.circle(20, 34, 2, cv["led"], width=0.7)
    c.group("rotate(-30 20 22)", body)


def calendar(c):
    c.rect(4, 6, 34, 32, c.grad(c["page"]), 2)
    c.rect(4, 6, 34, 9, c.grad(c.lighten(c["red"], 0.2), c["red"]), 2)
    c.line("M12 3 V9 M30 3 V9", "ink", 2)
    step = 7 if not c.small else 9
    for y in range(19, 36, step):
        for x in range(9, 36, step):
            c.rect(x, y, 3.5 if not c.small else 5, 3, c.lighten(c["ink"], 0.55), 0.5, None)


def cloud(c):
    c.path("M10 32 A7 7 0 0 1 9 18 A10 10 0 0 1 28 14 A8.5 8.5 0 0 1 32 32 Z",
           c.grad("#ffffff", c.lighten(c["blue"], 0.45)))


def phone(c):
    dark = c.darken(c["metal"][1], 0.45)
    c.rect(10, 2, 21, 38, c.grad(c.darken(c["metal"][0], 0.35), dark), 4)
    c.rect(12.5, 7, 16, 26, c.grad(c["screen"]), 1, width=0.9)
    c.circle(20.5, 36.5, 1.6, c["metal"][0], width=0.6)


def scrollbar(c):
    c.rect(13, 2, 15, 41, c.grad(c["case"], horizontal=True), 1.5)
    for y, d in ((2, "M20.5 4.5 L24.5 9 H16.5 Z"), (35, "M20.5 40.5 L24.5 36 H16.5 Z")):
        c.rect(13, y, 15, 8, c.grad(c["case_top"]), 1.5, width=1)
        c.path(d, c["ink"], None)
    c.rect(14.5, 14, 12, 14, c.grad(c.lighten(c["blue"], 0.45), c["blue"]), 2, width=1)


def tabs(c):
    for x in (15, 27):
        c.rect(x, 6, 12, 7, c.grad(c["case"]), 1.5, width=1)
    c.rect(3, 12, 38, 26, c.grad(c["page"]), 1.5)
    c.rect(3, 5, 12.5, 8, "#ffffff", 1.5, width=1)
    c.line("M4.2 12 H14.3", "#ffffff", 2.2)
    if not c.small:
        c.line("M7 18 H30 M7 22 H26 M7 26 H28", "#7a8699", 1.4)
    else:
        c.line("M7 19 H28 M7 25 H24", "#7a8699", 1.4)


def device_tree(c):
    c.line("M10 13 V35 H18 M10 22 H18", "ink", 1.8)
    c.rect(3, 4, 14, 9, c.grad(c.lighten(c["blue"], 0.3), c["blue"]), 1.5)
    c.rect(18, 17.5, 16, 9, c.grad(c["case"]), 1.5)
    c.rect(18, 30.5, 11, 9, c.grad(c.lighten(c["green"], 0.3), c["green"]), 1.5)
    if not c.small:
        c.line("M21 22 H30", c["case_dark"], 1.3)


def search_bar(c):
    c.rect(2, 6, 44, 14, c.grad(c["page"]), 7)
    G(c, "magnifier", 5, 7.5, 11, c["ink"])
    c.line("M19 10 V16", c["blue"], 1.6)
    c.rect(6, 22, 36, 21, c.grad(c["page"]), 2)
    for i, col in enumerate(("blue", "green", "orange")):
        y = 25 + i * 6
        c.rect(9, y, 4.5, 4.5, c[col], 1, None)
        if not c.small:
            c.line(f"M16 {y + 2.2} H{36 - i * 4}", "#7a8699", 1.4)
        else:
            c.line(f"M16 {y + 2.2} H32", "#7a8699", 1.4)


def two_windows(c):
    scaled(c, 8, 10, 0.95, lambda cv: window_body(cv))
    scaled(c, 1, 1, 0.95, lambda cv: window_body(cv))


def configure(c):
    """RISC OS's !Configure: red and green cogs, a blue one, a spanner."""
    cog(c, 30, 30, 13, c["green"], 9)
    cog(c, 15, 17, 12, c["red"], 8)
    if not c.small:
        cog(c, 36, 11, 7, c["blue"], 7)
    k = 1.6
    w = c.lw / k / (1.6 if c.small else 1)
    scaled(c, 2, 4, k, lambda cv: cv.path(
        "M14 4 A5 5 0 0 0 10.5 11 L4 17.5 L6.5 20 L13 13.5 A5 5 0 0 0 20 10 L17 11 L14 10 L13 7 Z",
        cv.grad(cv["metal"]), "ink", w))


# ---- screen contents (preferences-desktop-*) -----------------------------
def scr_desk(c):
    for y in (11, 19):
        c.path(f"M10 {y} h3 l1 1 h5 v5 h-9 z", c.grad(c["folder"]), "ink", 0.8)
    c.rect(24, 11, 13, 11, "#ffffff", 0.8, width=0.8)
    c.rect(24, 11, 13, 2.5, c["case_top"][1], 0.5, width=0.8)
    c.rect(7, 27, 34, 5, c.grad(c["case_top"]), 0, width=0.8)
    for x, col in ((11, "blue"), (16, "green"), (21, "red")):
        c.rect(x, 28, 3, 3, c[col], 0.5, None)


def scr_widgets(c):
    c.circle(16, 19, 6.5, "#ffffff", width=1)
    c.line("M16 19 V15 M16 19 L19 20.5", "ink", 1.2)
    c.rect(25, 12, 11, 14, c.lighten(c["yellow"], 0.4), 1, width=1)
    if not c.small:
        c.line("M27 16 H34 M27 19 H34 M27 22 H32", "#7a8699", 1)


def scr_palette(c):
    c.path("M24 11 C31 11 35 14 35 18 C35 21 32 22 29 21.5 C27 21.3 26 23 27 25 C28 27 26 29 22 29 "
           "C16 29 13 25 13 20 C13 15 17 11 24 11 Z", "#ffffff", "ink", 1)
    for x, y, col in ((18, 17, "red"), (23, 14.5, "yellow"), (29, 16, "green"), (18, 23, "blue")):
        c.circle(x, y, 2.4 if not c.small else 2.8, c[col], None)


def scr_bars(c):
    cols = ("red", "orange", "yellow", "green", "cyan", "blue", "violet")
    for i, col in enumerate(cols):
        c.rect(9 + i * 4, 10, 4, 20, c[col], 0, None)


def scr_rainbow(c):
    for i, col in enumerate(("red", "orange", "yellow", "green", "blue")):
        r = 13 - i * 2.4
        c.path(f"M{24 - r} 29 A{r} {r} 0 0 1 {24 + r} 29", "none", c[col], 2.4)


def scr_plasma_theme(c):
    c.rect(7, 26, 34, 6, c.grad(c.lighten(c["violet"], 0.3), c["violet"]), 0, width=0.8)
    G(c, "brush", 15, 7, 18, "#ffffff")


def scr_pointer(c):
    c.path("M17 10 L17 29 L21.5 25 L25 31.5 L28 30 L24.5 23.5 L30 23 Z", "#ffffff")


def scr_apps(c):
    for i, (x, y) in enumerate(((13, 11), (24, 11), (13, 21), (24, 21))):
        c.rect(x, y, 8, 8, c["yellow"] if i == 0 else "#ffffff", 1.5, width=0.9)
    G(c, "check", 13, 11, 8, c["ink"], 4)


def scr_anim(c):
    for x, o in ((14, 0.3), (20, 0.6)):
        c.parts.append(f'<circle cx="{x}" cy="20" r="5" fill="#ffffff" opacity="{o}"/>')
    c.circle(28, 20, 5.5, "#ffffff", width=1)
    c.line("M9 17 H14 M8 23 H13", "#ffffff", 1.4)


def scr_font(c):
    c.text(23, 27, "Aa", 16, "#ffffff")


def scr_landscape(c):
    c.circle(33, 14, 3.5, c["yellow"], None)
    c.path("M7 32 V24 C13 18 19 25 25 21 C31 17 36 21 41 19 V30.5 A1.5 1.5 0 0 1 39.5 32 H8.5 A1.5 1.5 0 0 1 7 30.5 Z",
           c.grad(c.lighten(c["green"], 0.3), c["green"]), None)


def scr_icons(c):
    c.path("M10 14 h4 l1.5 1.5 h6.5 v7.5 h-12 z", c.grad(c["folder"]), "ink", 1)
    c.path("M26 12 h6 l3 3 v10 h-9 z", "#ffffff", "ink", 1)
    c.path("M32 12 v3 h3", "none", "ink", 0.8)


def scr_winmini(c):
    c.rect(11, 11, 24, 18, "#ffffff", 1, width=1)
    c.rect(11, 11, 24, 4, c["case_top"][1], 1, width=1)
    c.rect(14, 18, 9, 4, c["blue"], 1.5, width=0.8)
    c.rect(14, 24, 3, 3, "#ffffff", 0.5, width=0.8)
    if not c.small:
        c.line("M19 25.5 H31", "#7a8699", 1)


def scr_decor(c):
    c.rect(9, 11, 30, 9, c.grad(c["case_top"]), 1, width=1)
    for x, col in ((11, c["red"]), (17, c["case"][1]), (33, c["case"][1])):
        c.rect(x, 12.5, 5, 5, col, 0.8, width=0.8)
    c.rect(9, 20, 30, 10, "#ffffff", 0, width=1)


def scr_edges(c):
    c.rect(7, 8, 4, 24, c["yellow"], 1.5, None)
    G(c, "arrow-right", 15, 11, 18, "#ffffff")


def scr_tts(c):
    G(c, "lines", 9, 11, 16, "#ffffff")
    c.path("M28 15 A6 6 0 0 1 28 25 M32 12 A10 10 0 0 1 32 28", "none", "#ffffff", 1.6)


def scr_password(c):
    c.rect(10, 15, 26, 10, "#ffffff", 2, width=1)
    for i in range(4):
        c.circle(15 + i * 5, 20, 1.7, c["ink"], None)


def scr_menuedit(c):
    G(c, "menu", 10, 10, 18, "#ffffff")
    G(c, "pencil", 22, 12, 16, c["yellow"])


def scr_baloo(c):
    G(c, "pages", 10, 9, 18, "#ffffff")
    G(c, "magnifier", 22, 14, 14, c["yellow"])


def scr_smile(c):
    c.circle(24, 20, 8.5, c["yellow"])
    c.circle(21, 18, 1.2, c["ink"], None)
    c.circle(27, 18, 1.2, c["ink"], None)
    c.path("M19.5 22 Q24 26.5 28.5 22", "none", "ink", 1.3)


def scr_screensaver(c):
    c.rect(7, 8, 34, 24, c.darken(c["screen"][1], 0.55), 1.5)
    G(c, "moon", 14, 10, 18, c["yellow"])
    for x, y in ((30, 13), (34, 22), (12, 26)):
        c.circle(x, y, 1, "#ffffff", None)


def randr(c):
    scaled(c, 0, 12, 0.6, monitor_body)
    scaled(c, 18, 3, 0.65, monitor_body)
    G(c, "arrow-right", 6, 15, 12, "#ffffff", 4.4)
    marker(c)


# ---- the table -------------------------------------------------------------
DESKTOP = {
    "preferences-desktop": scr_desk,
    "preferences-desktop-accessibility": "accessibility",
    "preferences-desktop-activities": "activities",
    "preferences-desktop-animations": scr_anim,
    "preferences-desktop-baloo": scr_baloo,
    "preferences-desktop-color": scr_palette,
    "preferences-desktop-cryptography": ("key", "yellow"),
    "preferences-desktop-cursors": scr_pointer,
    "preferences-desktop-default-applications": scr_apps,
    "preferences-desktop-display": "fullscreen",
    "preferences-desktop-display-color": scr_bars,
    "preferences-desktop-effects": ("wand", "yellow"),
    "preferences-desktop-emoticons": scr_smile,
    "preferences-desktop-feedback": "comment",
    "preferences-desktop-filter": "filter",
    "preferences-desktop-font": scr_font,
    "preferences-desktop-gestures-screenedges": scr_edges,
    "preferences-desktop-gestures-touch": "gesture",
    "preferences-desktop-icons": scr_icons,
    "preferences-desktop-launch-feedback": ("hourglass", "yellow"),
    "preferences-desktop-locale": "language",
    "preferences-desktop-menu-edit": scr_menuedit,
    "preferences-desktop-multimedia": "film",
    "preferences-desktop-navigation": "compass",
    "preferences-desktop-notification-bell": ("bell", "yellow"),
    "preferences-desktop-plasma": scr_widgets,
    "preferences-desktop-plasma-theme": scr_plasma_theme,
    "preferences-desktop-screensaver": scr_screensaver,
    "preferences-desktop-search": "magnifier",
    "preferences-desktop-text-to-speech": scr_tts,
    "preferences-desktop-theme-applications": scr_winmini,
    "preferences-desktop-theme-global": scr_rainbow,
    "preferences-desktop-theme-windowdecorations": scr_decor,
    "preferences-desktop-thunderbolt": ("lightning", "yellow"),
    "preferences-desktop-user": "user",
    "preferences-desktop-user-password": scr_password,
    "preferences-desktop-virtual": "workspaces",
    "preferences-desktop-wallpaper": scr_landscape,
}

# A device with the settings cog.
DEVICE = {
    "preferences-desktop-keyboard": keyboard,
    "preferences-desktop-keyboard-shortcut": keycaps,
    "preferences-desktop-mouse": mouse,
    "preferences-desktop-touchpad": touchpad,
    "preferences-desktop-tablet": gtablet,
    "preferences-desktop-touchscreen": touchscreen,
    "preferences-desktop-sound": speaker,
    "preferences-desktop-gaming": joystick,
    "preferences-desktop-display-randr": None,
    "preferences-devices-cpu": chip,
    "preferences-devices-printer": printer,
    "preferences-devices-scanner": scanner,
    "preferences-devices-tree": device_tree,
    "preferences-system-disks": harddisk,
    "preferences-system-time": clock,
    "preferences-system-windows": window_body,
    "preferences-system-network": globe,
    "preferences-system-network-server": tower,
    "preferences-virtualization-container": container,
    "preferences-virtualization-vm": pc_case,
    "preferences-document": page_body,
    "preferences-scroll": scrollbar,
    "preferences-tabs": tabs,
}

# A body with the subject on a plaque: name -> (body, glyph, colour).
PLAQUE = {
    # !Configure's red cog: system settings
    "preferences-other": (cogbody, "more", "ink"),
    "preferences-system-backup": (cogbody, "history", "blue"),
    "preferences-system-bluetooth": (cogbody, "bluetooth", "blue"),
    "preferences-system-linux": (cogbody, "atom", "violet"),
    "preferences-system-login": (cogbody, "login", "ink"),
    "preferences-system-power-management": (cogbody, "battery-charge", "green"),
    "preferences-system-services": (cogbody, "list-bullet", "ink"),
    "preferences-system-session-services": (cogbody, "play", "green"),
    "preferences-system-splash": (cogbody, "picture", "blue"),
    "preferences-system-startup": (cogbody, "power", "red"),
    "preferences-system-user-sudo": (cogbody, "hash", "red"),
    "yast-users": (cogbody, "users", "ink"),
    "yast-autoyast": (cogbody, "robot", "ink"),
    "yast-software-group": (cogbody, "box", "brown"),
    "yast-support": (cogbody, "help", "blue"),
    "yast-support-group": (cogbody, "people", "blue"),
    "yast-sw_source": (cogbody, "server", "ink"),
    "yast-sysconfig": (cogbody, "terminal", "ink"),
    "yast-system-group": (cogbody, "monitor", "ink"),
    "yast-update": (cogbody, "refresh", "green"),
    # the globe: network settings
    "preferences-system-network-dsl": (globe, "modem", "ink"),
    "preferences-system-network-ethernet": (globe, "ethernet", "ink"),
    "preferences-system-network-iscsi": (globe, "harddisk", "ink"),
    "preferences-system-network-ldap": (globe, "tree", "ink"),
    "preferences-system-network-nis": (globe, "list", "ink"),
    "preferences-system-network-ntp": (globe, "clock", "blue"),
    "preferences-system-network-proxy": (globe, "filter", "ink"),
    "preferences-system-network-remote": (globe, "monitor", "ink"),
    "preferences-system-network-share-windows": (globe, "folder", "blue"),
    "preferences-system-network-sharing": (globe, "share", "green"),
    "preferences-system-network-vpn": (globe, "vpn", "green"),
    "preferences-system-network-wakeonlan": (globe, "power", "red"),
    "yast-network-group": (globe, "network", "ink"),
    # the server tower
    "preferences-system-network-server-boot": (tower, "restart", "green"),
    "preferences-system-network-server-dhcp": (tower, "tag", "orange"),
    "preferences-system-network-server-dns": (tower, "sign", "ink"),
    "preferences-system-network-server-ftp": (tower, "download", "blue"),
    "preferences-system-network-server-installation": (tower, "disc", "ink"),
    "preferences-system-network-server-iscsi": (tower, "harddisk", "ink"),
    "preferences-system-network-server-kerberos": (tower, "ticket", "orange"),
    "preferences-system-network-server-ldap": (tower, "tree", "ink"),
    "preferences-system-network-server-mail": (tower, "envelope", "blue"),
    "preferences-system-network-server-nis": (tower, "list", "ink"),
    "preferences-system-network-server-share": (tower, "share", "green"),
    "preferences-system-network-server-share-windows": (tower, "folder", "blue"),
    "preferences-system-network-server-slp": (tower, "location", "red"),
    "preferences-system-network-server-web": (tower, "globe", "blue"),
    # the shield
    "preferences-security-apparmor": (shield, "window", "ink"),
    "preferences-security-firewall": (shield, "flame", "red"),
    "preferences-security-kerberos": (shield, "ticket", "orange"),
    # the window
    "preferences-system-windows-actions": (window_body, "menu", "ink"),
    "preferences-system-windows-behavior": (window_body, "cursor", "ink"),
    "preferences-system-windows-move": (window_body, "move", "ink"),
    "preferences-gtk-config": (window_body, "brush", "violet"),
    # the browser window
    "preferences-web-browser-adblock": (browser, "forbidden", "red"),
    "preferences-web-browser-cache": (browser, "database", "ink"),
    "preferences-web-browser-cookies": (browser, "pref-cookie", "brown"),
    "preferences-web-browser-identification": (browser, "id-card", "ink"),
    "preferences-web-browser-shortcuts": (browser, "link", "ink"),
    "preferences-web-browser-ssl": (browser, "lock", "green"),
    "preferences-web-browser-stylesheets": (browser, "brush", "violet"),
    # the RISC PC case: virtual machines
    "preferences-virtualization-vm-install": (pc_case, "download", "blue"),
    "preferences-virtualization-vm-migrate": (pc_case, "forward", "orange"),
    "preferences-virtualization-vm-new": (pc_case, "plus", "green"),
    # devices with a subject
    "preferences-devices-drive-optical-check": (optical, "check", "green"),
    "yast-hwinfo": (lambda c: chip(c), "info", "blue"),
    "yast-disk": (harddisk, "partition", "ink"),
    "preferences-smart-status": (harddisk, "heart", "red"),
    # pages
    "preferences-desktop-filetype-association": (page_body, "link", "blue"),
    "preferences-log": (page_body, "log", "ink"),
    "preferences-releasenotes": (page_body, "star", "orange"),
    # odd ones
    "preferences-kde-connect": (phone, "laptop", "ink"),
    "preferences-online-accounts": (cloud, "user", "blue"),
    "device-notifier": (usbstick, "bell", "orange"),
    "financial-schedule": (calendar, "money", "green"),
}


@reg("pref-cookie")
def _cookie(c, k):
    O(c, 12, 12, 8.5, k)
    for x, y in ((9, 9), (15, 10), (10, 15), (15.5, 15)):
        D(c, x, y, 1.5, k)


def big(c, name, accent):
    """The subject drawn large with a light fill behind it, and the cog."""
    glyph(c, name, 2, 2, 36, c.lighten(c[accent], 0.55), width=6 if not c.small else 7)
    glyph(c, name, 2, 2, 36, c["ink"], width=None if not c.small else 3.0)
    return marker(c)


def draw(name, c):
    try:
        if name == "preferences":
            configure(c)
            return True
        if name in DESKTOP:
            return monitor(c, DESKTOP[name])
        if name == "preferences-desktop-display-randr":
            randr(c)
            return True
        if name in DEVICE:
            DEVICE[name](c)
            return marker(c)
        if name == "preferences-security":
            shield(c)
            G(c, "lock", 11, 12, 18, "#ffffff")
            return marker(c)
        if name in PLAQUE:
            body, g, col = PLAQUE[name]
            body(c)
            return plaque(c, g, col)
        if name == "preferences-git":
            return big(c, "branch", "orange")
        if name == "preferences-plugin":
            return big(c, "puzzle", "green")
        if name == "plasma-search":
            search_bar(c)
            return True
        if name == "podcast-amarok":
            c.circle(24, 24, 19, c.grad(c.lighten(c["violet"], 0.3), c.darken(c["violet"], 0.15)))
            G(c, "podcast", 11, 11, 26, "#ffffff")
            return True
        if name == "window-duplicate":
            two_windows(c)
            return True
    except Exception:  # noqa: BLE001  never raise into the build
        return None
    return None
