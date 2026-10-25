"""fam_emblems.py: emblems, the small overlays that sit in a corner of
other icons. Each is a plaque filling most of the grid: round for the
plain emblems and packages (a parcel with a badge), a rounded square for
version control, a triangle for the warning, stars for the rating."""
import math

from glyphs import glyph

PLAIN = {   # name: (colour, glyph, glyph on ink instead of white)
    "emblem-added": ("green", "plus"),
    "emblem-checked": ("green", "check"),
    "emblem-encrypted-locked": ("violet", "lock"),
    "emblem-error": ("red", "cross"),
    "emblem-important": ("orange", "exclamation"),
    "emblem-information": ("blue", "info"),
    "emblem-locked": ("brown", "lock"),
    "emblem-mounted": ("green", "harddisk"),
    "emblem-pause": ("yellow", "pause"),
    "emblem-question": ("blue", "question"),
    "emblem-readonly": ("grey", "pencil"),
    "emblem-remove": ("red", "minus"),
    "emblem-shared": ("cyan", "share"),
    "emblem-symbolic-link": ("white", "forward"),
    "emblem-unavailable": ("grey", "forbidden"),
    "emblem-unlocked": ("green", "unlock"),
    "emblem-unmounted": ("grey", "eject"),
}
VCS = {
    "vcs-added": ("green", "plus"),
    "vcs-conflicting": ("red", "lightning"),
    "vcs-locally-modified": ("orange", "pencil"),
    "vcs-locally-modified-unstaged": ("yellow", "pencil"),
    "vcs-normal": ("green", "check"),
    "vcs-removed": ("red", "minus"),
    "vcs-update-required": ("blue", "arrow-down"),
}
PACKAGE = {  # badge colour, badge glyph, automatic
    "package-available": (None, None, False),
    "package-available-locked": ("grey", "lock", False),
    "package-downgrade": ("red", "arrow-down", False),
    "package-install-auto": ("green", "check", True),
    "package-installed-outdated": ("orange", "clock", False),
    "package-new": ("yellow", "star", False),
    "package-reinstall": ("blue", "refresh", False),
    "package-remove": ("red", "minus", False),
    "package-remove-auto": ("red", "minus", True),
    "package-upgrade": ("green", "arrow-up", False),
    "package-upgrade-auto": ("green", "arrow-up", True),
}


def _fill(c, col):
    base = "#ffffff" if col == "white" else c[col]
    if col == "white":
        return c.grad("#ffffff", c["page"][1])
    return c.grad(c.lighten(base, 0.3), c.darken(base, 0.15))


def _on(col, c):
    return c["ink"] if col in ("yellow", "white") else "#ffffff"


def _shine(c, round_=True):
    if c.small:
        return
    if round_:
        c.path("M10 17 A16 13 0 0 1 38 17 A18 9 0 0 0 10 17 Z", "#ffffff", None, opacity=0.35)
    else:
        c.path("M10 9 h28 a3 3 0 0 1 3 3 v4 c-9 -3 -25 -3 -34 0 v-4 a3 3 0 0 1 3 -3 z", "#ffffff", None, opacity=0.3)


def _glyph(c, name, col, x=11, y=11, size=26):
    glyph(c, name, x, y, size, col, width=3.0 if not c.small else 3.6)


def _gear_mark(c):
    """'automatic': a solid disc with a bold A at the top right (drawn as
    strokes, so it survives at 16/22 px where text is left out)."""
    r = 8.5 if not c.small else 9.5
    c.circle(38, 10, r, c.darken(c["blue"], 0.1), width=1.1)
    c.path("M34.2 14.6 L38 5 L41.8 14.6 M35.6 11.2 H40.4", "none", "#ffffff", 2.2 if not c.small else 1.9)


def _star_pts(cx=24, cy=25, ro=20, ri=8.4):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _poly(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


import names as _names
MINE = frozenset(_names.names()["emblems"])


def draw(name, c):
    if name not in MINE:
        return None
    if name in PLAIN:
        col, g = PLAIN[name]
        c.circle(24, 24, 20, _fill(c, col))
        _shine(c)
        _glyph(c, g, _on(col, c))
        if name == "emblem-readonly":
            c.line("M12 36 L36 12", "#ffffff", 3.2)
            c.line("M12 36 L36 12", c.darken(c["red"], 0.05), 2.0)
        return True
    if name == "emblem-warning":
        c.path("M24 4 L45 41 a1.5 1.5 0 0 1 -1.3 2 H4.3 a1.5 1.5 0 0 1 -1.3 -2 Z", _fill(c, "yellow"))
        _glyph(c, "exclamation", c["ink"], 12, 15, 24)
        return True
    if name in VCS:
        col, g = VCS[name]
        c.rect(5, 5, 38, 38, _fill(c, col), 9)
        _shine(c, False)
        _glyph(c, g, _on(col, c))
        if name == "vcs-locally-modified-unstaged":
            c.rect(9, 9, 30, 30, "none", 5, c.darken(c["yellow"], 0.45), 1.4)
        return True
    if name in PACKAGE:
        bcol, bg, auto = PACKAGE[name]
        c.circle(24, 24, 20, _fill(c, "brown"))
        _shine(c)
        if bg:
            _glyph(c, "box", "#ffffff", 7, 7, 25)
            c.circle(35, 35, 10, _fill(c, bcol), width=1.2)
            glyph(c, bg, 28, 28, 14, _on(bcol, c), width=3.0 if not c.small else 3.8)
        else:
            _glyph(c, "box", "#ffffff", 10, 10, 28)
        if auto:
            _gear_mark(c)
        return True
    if name in ("rating", "rating-half", "rating-unrated"):
        pts = _star_pts()
        gold = c.grad(c.lighten(c["yellow"], 0.3), c["orange"])
        empty = c.lighten(c["grey"], 0.75)
        c.path(_poly(pts), gold if name == "rating" else empty, width=None)
        if name == "rating-half":
            c.path(_poly(pts[5:] + pts[:1]), gold, None)
            c.path(_poly(pts), "none")
            c.line("M24 5 V34", "ink", 1.0)
        return True
    return None
