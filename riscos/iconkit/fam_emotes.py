"""fam_emotes.py: emotes. Round yellow faces in RISC OS's manner (a lit
ball with an ink outline, features drawn thick enough for 22 px), and
the drink and food objects."""

def _face(c, col=None, cx=24, cy=25, r=19):
    col = col or c["yellow"]
    c.circle(cx, cy, r, c.grad(c.lighten(col, 0.45), c.darken(col, 0.12)))
    if not c.small:
        c.path(f"M{cx - r * 0.62:g} {cy - r * 0.5:g} A{r * 0.8:g} {r * 0.6:g} 0 0 1 {cx + r * 0.62:g} {cy - r * 0.5:g} "
               f"A{r * 0.9:g} {r * 0.5:g} 0 0 0 {cx - r * 0.62:g} {cy - r * 0.5:g} Z", "#ffffff", None, opacity=0.45)


def _eyes(c, lx=17, rx=31, y=20, r=None):
    r = r or (2.6 if not c.small else 3.3)
    c.circle(lx, y, r, c["ink"], None)
    c.circle(rx, y, r, c["ink"], None)


def _l(c, d, w=2.2):
    c.line(d, "ink", w)


def _closed(c, x, y, up=True):
    """A closed eye: an arc, happy (up) or sleepy (down)."""
    _l(c, f"M{x - 4} {y + 1} Q{x} {y - 3 if up else y + 4} {x + 4} {y + 1}")


def _heart(c, x, y, s, col):
    c.path(f"M{x} {y + s * 0.9} C{x - s} {y + s * 0.3} {x - s * 1.1} {y - s * 0.5} {x - s * 0.5} {y - s * 0.6} "
           f"C{x - s * 0.15} {y - s * 0.65} {x} {y - s * 0.4} {x} {y - s * 0.2} "
           f"C{x} {y - s * 0.4} {x + s * 0.15} {y - s * 0.65} {x + s * 0.5} {y - s * 0.6} "
           f"C{x + s * 1.1} {y - s * 0.5} {x + s} {y + s * 0.3} {x} {y + s * 0.9} Z", col, width=1)


def _open_mouth(c, d):
    c.path(d, c.darken(c["red"], 0.35))


def _drop(c, x, y, s=1.0):
    c.path(f"M{x} {y} q{-3 * s} {5 * s} 0 {7 * s} q{3 * s} {-2 * s} 0 {-7 * s} z", c.lighten(c["cyan"], 0.2), width=1)


def _hands(c):
    """face-hug: arms and hands reaching out to the left."""
    hand = c.grad(c.lighten(c["yellow"], 0.45), c.darken(c["yellow"], 0.12))
    c.circle(7, 22, 5, hand, width=1.2)
    c.circle(8.5, 35, 5, hand, width=1.2)
    if not c.small:
        _l(c, "M5 20 h4 M5.5 33 h4", 1.2)


def _hug(c):
    _face(c, cx=28, cy=25, r=17)
    _hands(c)
    _closed(c, 22, 21)
    _closed(c, 34, 21)
    _l(c, "M20 29 Q28 37 36 29")


import names as _names
MINE = frozenset(_names.names()["emotes"])


def draw(name, c):
    if name not in MINE:
        return None
    if name.startswith("face-"):
        return _faces(name[5:], c)
    if name == "drink-beer":
        glass = c.grad(c.lighten(c["orange"], 0.35), c["orange"])
        c.path("M33 18 h4 a5 5 0 0 1 5 5 v8 a5 5 0 0 1 -5 5 h-4", "none", width=None)
        c.path("M33 21 h3.5 a2.5 2.5 0 0 1 2.5 2.5 v7 a2.5 2.5 0 0 1 -2.5 2.5 h-3.5", "none", width=None)
        c.path("M11 14 h22 v26 a3 3 0 0 1 -3 3 h-16 a3 3 0 0 1 -3 -3 z", glass)
        if not c.small:
            c.line("M16 20 v18 M22 20 v18 M28 20 v18", "#ffffff", 1.4)
        c.path("M9 15 c0 -4 3 -6 6 -5 c1 -4 7 -5 9 -2 c3 -3 9 -1 9 3 c3 0 3 5 0 6 h-24 c-2 0 -2 -2 0 -2 z",
               c.grad("#ffffff", c["page"][1]))
        return True
    if name == "drink-martini":
        c.path("M7 8 h34 l-17 18 z", c.grad(c.lighten(c["cyan"], 0.55), c.lighten(c["cyan"], 0.1)))
        c.path("M11 12 h26", "none", "ink", 1.2)
        c.line("M24 26 v13", "ink", 2.4)
        c.ellipse(24, 41, 9, 2.5, c.grad(c["metal"]))
        c.line("M30 4 L19 18", c["brown"], 1.6)
        c.circle(21, 15, 4, c.grad(c.lighten(c["green"], 0.3), c.darken(c["green"], 0.2)), width=1.1)
        if not c.small:
            c.circle(22, 14.5, 1.3, c["red"], None)
        return True
    if name == "food-cake":
        c.path("M7 26 h34 v14 a2 2 0 0 1 -2 2 h-30 a2 2 0 0 1 -2 -2 z", c.grad(c["page"]))
        c.path("M7 26 h34 v4" + " a2.833 2.833 0 0 1 -5.667 0" * 6 + " z", c.lighten(c["red"], 0.45))
        c.line("M8 36 h32", c.lighten(c["red"], 0.3), 2)
        for x, col in ((15, c["blue"]), (24, c["green"]), (33, c["violet"])):
            c.rect(x - 1.8, 14, 3.6, 12, col, 1, width=1)
            c.path(f"M{x} 6 c-3 3 -2 6 0 6 c2 0 3 -3 0 -6 z", c["orange"], width=1)
        return True
    return None


def _faces(n, c):
    ink = c["ink"]
    if n == "angel":
        c.ellipse(24, 7, 11, 3.2, "none", c.darken(c["yellow"], 0.15), 2.6)
        _face(c, cy=28, r=17)
        _closed(c, 18, 25)
        _closed(c, 30, 25)
        _l(c, "M17 32 Q24 38 31 32")
        return True
    if n == "devilish":
        col = c.lighten(c["red"], 0.15)
        c.path("M9 16 L6 3 L17 10 Z", c.darken(c["red"], 0.2))
        c.path("M39 16 L42 3 L31 10 Z", c.darken(c["red"], 0.2))
        _face(c, col=col, cy=26, r=18)
        _l(c, "M12 16 L21 20 M36 16 L27 20")
        _eyes(c, 17, 31, 22)
        c.path("M13 29 Q24 41 35 29 Q24 33 13 29 Z", "#ffffff")
        return True
    if n == "angry":
        _face(c, col=c.lighten(c["red"], 0.35))
        _l(c, "M11 13 L21 18 M37 13 L27 18", 2.6)
        _eyes(c, 17, 31, 22)
        _l(c, "M15 35 Q24 28 33 35", 2.6)
        return True
    if n == "clown":
        _face(c)
        for x in (5, 43):
            c.circle(x, 17, 5, c["orange"], width=1)
            c.circle(x, 25, 4.5, c["orange"], width=1)
        _eyes(c, 17, 31, 18)
        c.path("M12 28 Q24 42 36 28 Q24 34 12 28 Z", c["red"])
        c.circle(24, 25, 4.5, c.grad(c.lighten(c["red"], 0.3), c["red"]), width=1.2)
        return True
    if n == "confused":
        _face(c)
        _l(c, "M12 14 L20 12 M28 16 L36 16")
        _eyes(c, 17, 31, 20)
        _l(c, "M14 33 L18 30.5 L22 33 L26 30.5 L30 33 L34 30.5")
        return True
    if n == "cool":
        _face(c)
        c.path("M8 17 H40 M10 17 h11 v3 a4.5 4.5 0 0 1 -4.5 4.5 h-2 a4.5 4.5 0 0 1 -4.5 -4.5 z "
               "M27 17 h11 v3 a4.5 4.5 0 0 1 -4.5 4.5 h-2 a4.5 4.5 0 0 1 -4.5 -4.5 z", ink, width=1.8)
        if not c.small:
            c.line("M12 19 l3 -1 M29 19 l3 -1", "#ffffff", 1)
        _l(c, "M17 31 Q26 37 33 29")
        return True
    if n == "crying":
        _face(c)
        _l(c, "M12 16 L20 14 M28 14 L36 16")
        _closed(c, 17, 21, up=False)
        _closed(c, 31, 21, up=False)
        _l(c, "M16 36 Q24 29 32 36")
        _drop(c, 15, 24, 1.3)
        _drop(c, 33, 24, 1.3)
        return True
    if n == "embarrassed":
        _face(c)
        c.ellipse(12, 28, 4.5, 2.6, c.lighten(c["red"], 0.45), None)
        c.ellipse(36, 28, 4.5, 2.6, c.lighten(c["red"], 0.45), None)
        _eyes(c, 17, 31, 21, 2.0 if not c.small else 2.8)
        _l(c, "M12 15 Q16 13 20 15 M28 15 Q32 13 36 15", 1.6)
        _l(c, "M19 33 Q21.5 31 24 33 Q26.5 35 29 33")
        return True
    if n == "glasses":
        _face(c)
        c.circle(17, 20, 6, "#ffffff", width=1.6)
        c.circle(31, 20, 6, "#ffffff", width=1.6)
        _l(c, "M23 20 Q24 18 25 20 M11 19 L6 17 M37 19 L42 17", 1.6)
        _eyes(c, 17, 31, 20, 2.0 if not c.small else 2.6)
        _l(c, "M16 30 Q24 37 32 30")
        return True
    if n == "hug-left":
        _hug(c)
        return True
    if n == "hug-right":
        c.group("matrix(-1 0 0 1 48 0)", _hug)
        return True
    if n == "in-love":
        _face(c)
        _heart(c, 17, 19, 6.5, c["red"])
        _heart(c, 31, 19, 6.5, c["red"])
        _l(c, "M15 30 Q24 38 33 30")
        return True
    if n == "kiss":
        _face(c, cx=22)
        _closed(c, 15, 21, up=False)
        _eyes(c, 29, 29, 20)
        c.path("M20 29 q3 -2 3 1 q0 3 -3 2 q3 1 3 3.5 q0 2.5 -3 1.5", "none", c.darken(c["red"], 0.1), 2.4)
        _heart(c, 40, 13, 5, c["red"])
        return True
    if n == "laughing":
        _face(c)
        _l(c, "M12 21 L17 17 L22 21 M26 21 L31 17 L36 21", 2.4)
        _open_mouth(c, "M11 26 H37 Q36 40 24 40 Q12 40 11 26 Z")
        c.path("M17 37 Q24 31 31 37 Q28 40 24 40 Q20 40 17 37 Z", c.lighten(c["red"], 0.25), None)
        return True
    if n == "ninja":
        mask = c.darken(c["grey"], 0.55)
        c.path("M40 22 l7 -3 l-2 6 z M40 25 l6 3 l-5 3 z", mask, width=1)
        c.circle(24, 25, 19, c.grad(c.lighten(mask, 0.2), mask))
        c.path("M7.3 16 H40.7 A19 19 0 0 1 43 26 H5 A19 19 0 0 1 7.3 16 Z", c.grad(c.lighten(c["yellow"], 0.4), c["yellow"]))
        _l(c, "M11 18 L21 21 M37 18 L27 21", 2.2)
        _eyes(c, 17, 31, 22.5, 2.2 if not c.small else 2.6)
        return True
    if n == "pirate":
        _face(c)
        c.path("M5.4 21 A19 19 0 0 1 42.6 21 Z", c.grad(c.lighten(c["red"], 0.2), c["red"]))
        if not c.small:
            for x, y in ((14, 14), (24, 10), (34, 14), (19, 18), (29, 18)):
                c.circle(x, y, 1.3, "#ffffff", None)
        _l(c, "M8 24 L40 15", 1.6)
        c.ellipse(31, 25, 5, 4, ink, None)
        c.circle(17, 26, 2.6 if not c.small else 3.2, ink, None)
        c.path("M15 33 Q24 39 34 32", "none", "ink", 2.2)
        return True
    if n == "plain":
        _face(c)
        _eyes(c)
        _l(c, "M16 32 H32")
        return True
    if n == "quiet":
        _face(c)
        _eyes(c)
        _l(c, "M14 32 H34")
        if not c.small:
            _l(c, "M17 29.5 v5 M21 29.5 v5 M25 29.5 v5 M29 29.5 v5", 1.3)
        else:
            _l(c, "M19 29 v6 M24 29 v6 M29 29 v6", 1.3)
        return True
    if n == "raspberry":
        _face(c)
        _eyes(c, 17, 31, 20)
        c.path("M19 31 v5 a5 5 0 0 0 10 0 v-5 z", c.lighten(c["red"], 0.2))
        _l(c, "M14 31 Q24 33 34 31")
        if not c.small:
            c.line("M24 32 v5", c.darken(c["red"], 0.2), 1.2)
        return True
    if n == "sad":
        _face(c)
        _eyes(c)
        _l(c, "M15 35 Q24 27 33 35")
        return True
    if n == "sick":
        _face(c, col=c.lighten(c["green"], 0.25))
        _l(c, "M12 19 L20 22 M12 25 L20 22 M36 19 L28 22 M36 25 L28 22", 1.8)
        _l(c, "M14 33 Q17 30 20 33 Q23 36 26 33 Q29 30 32 33 Q34 35 35 33")
        return True
    if n == "sleeping":
        _face(c, cx=22, cy=27, r=18)
        _closed(c, 15, 24, up=False)
        _closed(c, 29, 24, up=False)
        c.ellipse(22, 34, 2.5, 2, ink, None)
        c.path("M33 4 h7 l-7 7 h7 M40 13 h5 l-5 5 h5", "none", c["blue"], 1.8)
        return True
    if n == "smile-big":
        _face(c)
        _eyes(c, 17, 31, 19)
        _open_mouth(c, "M12 27 H36 Q35 39 24 39 Q13 39 12 27 Z")
        return True
    if n == "smile-grin":
        _face(c)
        _eyes(c, 17, 31, 19)
        c.path("M11 27 H37 Q36 38 24 38 Q12 38 11 27 Z", "#ffffff")
        _l(c, "M12 31.5 H36", 1.4)
        if not c.small:
            _l(c, "M18 27 V37 M24 27 V38 M30 27 V37", 1.2)
        return True
    if n == "smirk":
        _face(c)
        _l(c, "M12 19 H21 M27 18 Q31 15 36 18", 1.8)
        _eyes(c, 17, 31, 22, 2.2 if not c.small else 3)
        _l(c, "M17 33 Q27 34 33 27")
        return True
    if n == "surprise":
        _face(c)
        _l(c, "M11 13 Q16 9 21 12 M27 12 Q32 9 37 13", 1.8)
        for x in (17, 31):
            c.circle(x, 20, 4.2, "#ffffff", width=1.4)
            c.circle(x, 20, 1.8 if not c.small else 2.4, ink, None)
        c.ellipse(24, 33, 4.5, 5.5, c.darken(c["red"], 0.35))
        return True
    if n == "uncertain":
        _face(c)
        _eyes(c, 20, 34, 20)
        _l(c, "M16 34 L32 30")
        return True
    if n == "wink":
        _face(c)
        c.circle(17, 20, 2.6 if not c.small else 3.3, ink, None)
        _closed(c, 31, 21)
        _l(c, "M15 29 Q24 37 33 29")
        return True
    if n == "worried":
        _face(c)
        _l(c, "M11 16 L20 13 M28 13 L37 16", 1.8)
        _eyes(c, 17, 31, 21)
        _l(c, "M17 34 Q20 31 24 32 Q28 33 31 31")
        return True
    if n == "yawn":
        _face(c)
        _l(c, "M12 19 L21 20 M27 20 L36 19", 2.0)
        c.ellipse(24, 32, 6, 7.5, c.darken(c["red"], 0.35))
        c.ellipse(24, 36, 3.5, 2.5, c.lighten(c["red"], 0.25), None)
        return True
    return None
