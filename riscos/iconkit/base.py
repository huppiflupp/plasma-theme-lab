"""The bodies most icons are built on: RISC OS's folder, its file (a page
with the corner folded down at the top right), the emblem plaque, the
device case, and the coloured tile actions sit on."""
from glyphs import glyph


def folder(c, emblem=None, color=None, open_=False, emblem_color=None):
    front = c.grad(color if color else c["folder"])
    back = c.grad(c.darken(color[0], 0.15), c.darken(color[1], 0.15)) if color else c.grad(c["folder_back"])
    c.path("M4 12 h14 l4 4 h22 v24 a2 2 0 0 1 -2 2 h-36 a2 2 0 0 1 -2 -2 z", back)
    if open_:
        c.path("M8 20 h37 l-4 20 a2 2 0 0 1 -2 2 h-33 a2 2 0 0 1 -2 -2 z", front)
    else:
        c.path("M4 20 h40 v20 a2 2 0 0 1 -2 2 h-36 a2 2 0 0 1 -2 -2 z", front)
        if not c.small:
            c.line("M6 22.5 h36", c["folder_line"], 1)
    if emblem:
        ink = emblem_color or c.darken(color[1] if color else c["folder"][1], 0.55)
        glyph(c, emblem, 15, 22, 18 if not c.small else 20, ink)
    return True

def page(c, label=None, label_color=None, emblem=None, emblem_color=None, lines=False, top=None):
    """A RISC OS file. label: the type written on a coloured band at the
    bottom (as RISC OS 5's JPEG, PDF, …); emblem: a glyph on the page."""
    c.path("M9 5 h22 l9 9 v28 a2 2 0 0 1 -2 2 h-27 a2 2 0 0 1 -2 -2 v-35 a2 2 0 0 1 2 -2 z", c.grad(c["page"]))
    c.path("M31 5 v7 a2 2 0 0 0 2 2 h7", c["page_fold"])
    band = label is not None and not (c.small and len(label) > 4)
    if lines and not c.small:
        for i in range(4 if band else 6):
            c.line(f"M12 {16 + i * 4} h{20 if i % 3 != 2 else 14}", "#7a8699", 1.4)
    if emblem:
        y = 12 if band else 16
        glyph(c, emblem, 13, y, 20 if band else 22, emblem_color or c["ink"])
    if band:
        c.path("M7 31 h33 v11 a2 2 0 0 1 -2 2 h-29 a2 2 0 0 1 -2 -2 z", label_color or c["blue"])
        size = 9 if len(label) <= 4 else 7.5 if len(label) <= 6 else 6
        if not c.small:                       # at 16/22 px the band alone
            c.text(23.5, 40.5, label, size, c["label_text"])
    elif label and c.small:
        # Too long for 16 px: a coloured corner instead of the word.
        c.path("M7 34 h12 l-12 9 z", label_color or c["blue"], None)
    return True

def plaque(c, name, color, x=27, y=27, size=18, fill="#ffffff"):
    """An emblem in a round plaque at the lower right (status, overlays)."""
    r = size / 2
    c.circle(x + r, y + r, r, fill, width=1.1)
    glyph(c, name, x + size * 0.18, y + size * 0.18, size * 0.64, color)
    return True

def case(c, x=6, y=12, w=36, h=24, depth=6):
    """A RISC PC style box: beige/grey front with a lit top."""
    c.path(f"M{x} {y + depth} l{depth} -{depth} h{w - depth} v{h - depth} l-{depth} {depth} z", c["case_dark"])
    c.rect(x, y + depth, w - depth, h - depth, c.grad(c["case"]), 1.5)
    c.path(f"M{x} {y + depth} l{depth} -{depth} h{w - depth} l-{depth} {depth} z", c.grad(c["case_top"]))
    return True

def tile(c, color, glyph_name=None, glyph_color="#ffffff", r=7):
    """A rounded square in a colour, a glyph on it (RISC OS 5's !Help)."""
    c.rect(6, 6, 36, 36, c.grad(c.lighten(color, 0.25), c.darken(color, 0.2)), r)
    if not c.small:
        c.path("M10 9 h28 a4 4 0 0 1 4 4 v4 c-10 -3 -26 -3 -36 0 v-4 a4 4 0 0 1 4 -4 z", "#ffffff", None, opacity=0.25)
    if glyph_name:
        glyph(c, glyph_name, 12, 12, 24, glyph_color)
    return True

def disc(c, color, glyph_name=None, glyph_color="#ffffff"):
    """A round badge (the error box's symbols, status)."""
    c.circle(24, 24, 19, c.grad(c.lighten(color, 0.3), c.darken(color, 0.15)))
    if glyph_name:
        glyph(c, glyph_name, 12, 12, 24, glyph_color)
    return True


ACCENTS = ("blue", "red", "green", "yellow", "orange", "cyan", "violet", "brown", "grey")


def action(c, name, accent=None, badge=None, badge_color=None, fill=None):
    """A toolbar action as RISC OS 5's toolbars draw them: the glyph large
    in the outline colour, optionally a filled accent shape behind it
    (fill: a glyph name drawn in the accent, lighter, slightly larger),
    and a badge at the lower right (plus, minus, cross, check, …) in a
    small round plaque of the badge colour."""
    from glyphs import glyph as g
    if fill:
        g(c, fill, 6, 6, 36, c.lighten(c[accent or "blue"], 0.55), width=6 if not c.small else 7)
    g(c, name, 6, 6, 36, c[accent] if accent and not fill else c["ink"], width=None if not c.small else 3.0)
    if badge:
        col = c[badge_color or "green"]
        c.circle(36, 36, 9 if not c.small else 10.5, col, width=1.1)
        g(c, badge, 29.5, 29.5, 13, "#ffffff", width=3.2 if not c.small else 4)
    return True


def overlay(c, name, color="green", x=26, y=26, size=20):
    """A plaque with a glyph over another drawing (status, emblems)."""
    from glyphs import glyph as g
    r = size / 2
    c.circle(x + r, y + r, r, c[color], width=1.1)
    g(c, name, x + size * 0.2, y + size * 0.2, size * 0.6, "#ffffff", width=3.2)
    return True
