"""fam_actions_go.py: actions whose name starts with g ... o (toolbar icons).

Families share one body (filled in RISC OS 5's manner: chunky block arrows,
a white envelope, a yellow bell, an orange keyframe diamond, a night sky
for the planetarium, …) and differ by a badge, an arrow or an accent.
New glyphs are registered as act-go-*.
"""
from base import action
from glyphs import glyph, reg, S, F, O, D, W, GLYPHS

FIRST = set("ghijklmno")


# ---- helpers ---------------------------------------------------------------
def P(c, d, fill, k, w=None):
    """A filled path with a stroke at the glyph's line weight."""
    c.parts.append(f'<path d="{d}" fill="{fill}" stroke="{k}" stroke-width="{(w or W(c)):g}" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')


def DS(c, d, col, w=None, dash="2 2"):
    """A dashed stroke."""
    c.parts.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{(w or W(c)):g}" '
                   f'stroke-dasharray="{dash}" stroke-linecap="butt" stroke-linejoin="round"/>')


def G(c, name, x, y, size, col):
    """A glyph nested in a glyph, at the outer line weight."""
    keep = W(c)
    glyph(c, name, x, y, size, col, width=keep * 24.0 / size)
    c._gw = keep


def TX(c, x, y, s, size, col, italic=False, weight="bold"):
    c.text(x, y, s, size, col, weight=weight, italic=italic)


def grad(c, col, t=0.35):
    return c.grad(c.lighten(c[col], t), c[col])


def pale(c, col, t=0.55):
    return c.lighten(c[col], t)


def badge_glyph(c, name, color):
    """The plaque base.action draws, for drawings that do not use action()."""
    c.circle(36, 36, 9 if not c.small else 10.5, c[color], width=1.1)
    glyph(c, name, 29.5, 29.5, 13, "#ffffff", width=3.2 if not c.small else 4)


def badge_text(c, s, color, size=10):
    c.circle(36, 36, 9 if not c.small else 10.5, c[color], width=1.1)
    c.text(36, 36 + size * 0.36, s, max(size, 9), "#ffffff")


def a(g, b=None, bc="green", acc=None, halo=False):
    """An action: glyph g (ink, or tinted with acc), optional halo, badge b."""
    def f(c):
        return action(c, g, acc, b, bc, fill=(g if halo else None))
    return f


def rot(c, deg, fn):
    c.group(f"rotate({deg} 12 12)", fn)


def mirror(c, fn):
    c.group("translate(24 0) scale(-1 1)", fn)


# ---- block arrows (go-*) -----------------------------------------------------
UP = "M12 3 L20.5 11.5 H15.5 V20.5 H8.5 V11.5 H3.5 Z"
TOP = "M12 7 L20 14.5 H15.5 V21 H8.5 V14.5 H4 Z"
BAR = "M4 2.5 H20 V5 H4 Z"
SKIP = "M12 2.5 L20 10.5 V14 L12 6 L4 14 V10.5 Z M12 10.5 L20 18.5 V22 L12 14 L4 22 V18.5 Z"


def _arrow(kind, blue="blue"):
    def fn(c, k):
        fill = grad(c, blue, 0.3)

        def body(cv):
            if kind == "up":
                P(cv, UP, fill, k)
            elif kind == "top":
                P(cv, TOP, fill, k)
                P(cv, BAR, cv.darken(cv[blue], 0.2), k)
            elif kind == "skip":
                P(cv, SKIP, fill, k)
        return body
    return fn


for _deg, _dir in ((0, "up"), (90, "right"), (180, "down"), (270, "left")):
    for _kind in ("up", "top", "skip"):
        def _mk(deg=_deg, kind=_kind):
            def g(c, k):
                rot(c, deg, _arrow(kind)(c, k))
            return g
        reg(f"act-go-{_kind}-{_dir}")(_mk())


@reg("act-go-jump")
def _(c, k):
    S(c, "M4 20 C4 11 9 7.5 15 8.5", k, W(c) * 2.8)
    S(c, "M4 20 C4 11 9 7.5 15 8.5", c.lighten(c["blue"], 0.25), W(c) * 1.2)
    P(c, "M13.5 3.5 L21 9.5 L13 13.5 Z", grad(c, "blue"), k)


def _curved(c, k, color, two=False):
    S(c, "M21 20 C21 12 16 9.5 9 9.5", k, W(c) * 2.8)
    S(c, "M21 20 C21 12 16 9.5 9 9.5", c.lighten(c[color], 0.25), W(c) * 1.2)
    P(c, "M10 3.5 L2.5 9.5 L10 15.5 Z", grad(c, color), k)
    if two:
        P(c, "M15 3.5 L7.5 9.5 L15 15.5 Z", grad(c, color), k)


@reg("act-go-reply")
def _(c, k): _curved(c, k, "blue")
@reg("act-go-reply-all")
def _(c, k): _curved(c, k, "blue", True)
@reg("act-go-rf")
def _(c, k): S(c, "M2 12 H10 M5.5 8.5 L2 12 L5.5 15.5 M14 12 H22 M18.5 8.5 L22 12 L18.5 15.5", k)


@reg("act-go-house")
def _(c, k):
    P(c, "M5 11 V20.5 H19 V11", grad(c, "blue", 0.5), k)
    P(c, "M2.5 12 L12 3.5 L21.5 12", "none", k)
    P(c, "M10 20.5 V15 H14 V20.5", c.darken(c["blue"], 0.2), k)


@reg("act-go-home")
def _(c, k):
    P(c, "M15.5 4 H18.5 V9", c["brown"], k)
    P(c, "M5 11 V20.5 H19 V11", c.grad(c["case"]), k)
    P(c, "M2 12.5 L12 3.5 L22 12.5 L19.5 12.5 L12 6 L4.5 12.5 Z", grad(c, "red"), k)
    P(c, "M10 20.5 V15 H14 V20.5", grad(c, "orange"), k)


# ---- bodies ------------------------------------------------------------------
@reg("act-go-env")
def _(c, k):
    P(c, "M3 6 H21 V18 H3 Z", c.grad(c["page"]), k)
    S(c, "M3 6 L12 13 L21 6", k)


@reg("act-go-env-open")
def _(c, k):
    P(c, "M3 10 L12 4 L21 10 V20 H3 Z", c.grad(c["page"]), k)
    P(c, "M6 12 V7 H18 V12", "#ffffff", k, W(c) * 0.7)
    S(c, "M8.5 9 H15.5", k, W(c) * 0.6)
    P(c, "M3 10 L12 16 L21 10 V20 H3 Z", c.grad(c["page"]), k)


@reg("act-go-env-dot")
def _(c, k):
    P(c, "M3 6 H21 V18 H3 Z", c.grad(c["page"]), k)
    S(c, "M3 6 L12 13 L21 6", k)
    D(c, 20, 6, 3.5, c["blue"])


@reg("act-go-bell")
def _(c, k):
    P(c, "M5.5 17 C7 15 7 13 7 10 A5 5 0 0 1 17 10 C17 13 17 15 18.5 17 Z", grad(c, "yellow", 0.4), k)
    S(c, "M10 19.5 A2 2 0 0 0 14 19.5", k)


@reg("act-go-bell-dot")
def _(c, k):
    P(c, "M5.5 17 C7 15 7 13 7 10 A5 5 0 0 1 17 10 C17 13 17 15 18.5 17 Z", grad(c, "yellow", 0.4), k)
    S(c, "M10 19.5 A2 2 0 0 0 14 19.5", k)
    P(c, "M18 2.5 A3 3 0 1 1 17.99 2.5 Z", c["red"], k, W(c) * 0.7)


@reg("act-go-bell-grey")
def _(c, k):
    P(c, "M5.5 17 C7 15 7 13 7 10 A5 5 0 0 1 17 10 C17 13 17 15 18.5 17 Z", c.lighten(c["grey"], 0.55), c["grey"])
    S(c, "M10 19.5 A2 2 0 0 0 14 19.5", c["grey"])


@reg("act-go-bell-off")
def _(c, k):
    P(c, "M5.5 17 C7 15 7 13 7 10 A5 5 0 0 1 17 10 C17 13 17 15 18.5 17 Z", c.lighten(c["grey"], 0.55), k)
    S(c, "M10 19.5 A2 2 0 0 0 14 19.5", k)
    S(c, "M4 3 L20 21", c["red"], W(c) * 1.4)


@reg("act-go-bells")
def _(c, k):
    P(c, "M9 14 C10 12.5 10 11 10 8.5 A4 4 0 0 1 18 8.5 C18 11 18 12.5 19 14 Z", grad(c, "orange", 0.4), k)
    P(c, "M3.5 19 C5 17 5 15 5 12.5 A4.5 4.5 0 0 1 14 12.5 C14 15 14 17 15.5 19 Z", grad(c, "yellow", 0.4), k)
    S(c, "M7.5 21 A2 2 0 0 0 11.5 21", k)


@reg("act-go-diamond")
def _(c, k): P(c, "M12 3.5 L20.5 12 L12 20.5 L3.5 12 Z", grad(c, "orange", 0.3), k)


@reg("act-go-key-next")
def _(c, k):
    P(c, "M17 6 L23 12 L17 18 L11 12 Z", grad(c, "orange", 0.3), k)
    S(c, "M1.5 12 H8 M5 8.5 L8.5 12 L5 15.5", k)


@reg("act-go-key-prev")
def _(c, k): mirror(c, lambda cv: GLYPHS["act-go-key-next"](cv, k))


@reg("act-go-layers")
def _(c, k):
    P(c, "M12 12 L21 16.5 L12 21 L3 16.5 Z", c.darken(c["cyan"], 0.15), k)
    P(c, "M12 7.5 L21 12 L12 16.5 L3 12 Z", c["cyan"], k)
    P(c, "M12 3 L21 7.5 L12 12 L3 7.5 Z", c.lighten(c["cyan"], 0.5), k)


@reg("act-go-user")
def _(c, k):
    P(c, "M4 20.5 C5 15 8 13 12 13 C16 13 19 15 20 20.5 Z", grad(c, "blue", 0.35), k)
    P(c, "M12 3.5 A4 4 0 1 1 11.99 3.5 Z", c.lighten(c["orange"], 0.55), k)


@reg("act-go-user-dashed")
def _(c, k):
    DS(c, "M4 20.5 C5 15 8 13 12 13 C16 13 19 15 20 20.5 Z", c["grey"], dash="2.2 1.8")
    DS(c, "M12 3.5 A4 4 0 1 1 11.99 3.5 Z", c["grey"], dash="2.2 1.8")


@reg("act-go-users")
def _(c, k):
    P(c, "M13 19 C14 15 16 13 18 13 C20.5 13 22 15 22.5 19 Z", grad(c, "green", 0.4), k)
    P(c, "M18 5.5 A3 3 0 1 1 17.99 5.5 Z", c.lighten(c["orange"], 0.55), k)
    P(c, "M2 20.5 C3 15.5 6 13.5 9 13.5 C12 13.5 15 15.5 16 20.5 Z", grad(c, "blue", 0.35), k)
    P(c, "M9 4.5 A3.6 3.6 0 1 1 8.99 4.5 Z", c.lighten(c["orange"], 0.55), k)


@reg("act-go-book")
def _(c, k):
    P(c, "M5 3 H18 V18 H7 A2 2 0 0 0 7 22 H18 V18", "none", k)
    P(c, "M5 3 H18 V18 H7 A2 2 0 0 0 5 20 Z", grad(c, "orange", 0.3), k)
    S(c, "M9 7 H15 M9 10 H14", "#ffffff")


@reg("act-go-notebook")
def _(c, k):
    P(c, "M6 3 H19 V21 H6 Z", grad(c, "brown", 0.4), k)
    S(c, "M9 3 V21", k)
    S(c, "M11.5 7 H17 M11.5 10 H16", "#ffffff")
    S(c, "M4 6 H8 M4 10 H8 M4 14 H8 M4 18 H8", k, W(c) * 0.8)


@reg("act-go-page")
def _(c, k):
    P(c, "M5 2.5 H15 L19.5 7 V21.5 H5 Z", c.grad(c["page"]), k)
    S(c, "M15 2.5 V7 H19.5", k, W(c) * 0.8)


def _page(c, k):
    GLYPHS["act-go-page"](c, k)


@reg("act-go-footnote")
def _(c, k):
    _page(c, k)
    S(c, "M8 7 H13 M8 10 H16 M8 13 H16", k, W(c) * 0.8)
    S(c, "M8 16 H12", c["blue"], W(c) * 0.8)
    S(c, "M8 18.5 H16", c["blue"], W(c) * 0.6)


@reg("act-go-endnote")
def _(c, k):
    c.group("translate(-2.5 -1.5)", lambda cv: _page(cv, k))
    c.group("translate(1 0.5)", lambda cv: _page(cv, k))
    S(c, "M9 9 H17 M9 12 H17", k, W(c) * 0.8)
    P(c, "M8.5 15 H17.5 V19 H8.5 Z", pale(c, "yellow", 0.2), k, W(c) * 0.6)


@reg("act-go-hrule")
def _(c, k):
    S(c, "M4 5 H20 M4 8.5 H16 M4 15.5 H20 M4 19 H14", k, W(c) * 0.8)
    P(c, "M3 11 H21 V13 H3 Z", c["blue"], k, W(c) * 0.6)


@reg("act-go-pagebreak")
def _(c, k):
    P(c, "M5 2.5 H19 V9 H5 Z", c.grad(c["page"]), k)
    P(c, "M5 15 H19 V21.5 H5 Z", c.grad(c["page"]), k)
    DS(c, "M2.5 12 H21.5", c["blue"], dash="2.4 1.6")


@reg("act-go-moremark")
def _(c, k):
    S(c, "M4 5 H20 M4 8.5 H17", k, W(c) * 0.8)
    DS(c, "M3 12 H21", c["orange"], dash="1.6 1.6")
    D(c, 8, 17, 1.6, k); D(c, 12, 17, 1.6, k); D(c, 16, 17, 1.6, k)


@reg("act-go-textframe")
def _(c, k):
    DS(c, "M3 4 H21 V20 H3 Z", c["blue"], W(c) * 0.8)
    S(c, "M7.5 8 H16.5 M12 8 V17", k)


@reg("act-go-button")
def _(c, k):
    P(c, "M3 7 H21 A2 2 0 0 1 21 7 V17 H3 Z", c.grad(c["case"]), k)
    S(c, "M8 12 H16", k)


@reg("act-go-checkbox")
def _(c, k):
    P(c, "M3 7 H13 V17 H3 Z", "#ffffff", k)
    S(c, "M5 12 L7.5 14.5 L11.5 9", c["green"])
    S(c, "M15.5 12 H21", k)


@reg("act-go-combo")
def _(c, k):
    P(c, "M2.5 7 H21.5 V17 H2.5 Z", "#ffffff", k)
    P(c, "M15 7 H21.5 V17 H15 Z", c.grad(c["case"]), k)
    S(c, "M16.5 11 L18.25 13 L20 11", k)
    S(c, "M5 12 H11", k, W(c) * 0.8)


@reg("act-go-listbox")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", "#ffffff", k)
    c.parts.append(f'<rect x="4" y="9.5" width="12.5" height="4" fill="{c.lighten(c["blue"], 0.3)}"/>')
    S(c, "M6 7 H14 M6 11.5 H14 M6 16 H14", k, W(c) * 0.8)
    P(c, "M17 3 H21 V21 H17 Z", c.grad(c["case"]), k)
    P(c, "M17 6 H21 V11 H17 Z", c["grey"], k, W(c) * 0.6)


@reg("act-go-scrollbar")
def _(c, k):
    P(c, "M2 8 H22 V16 H2 Z", c.grad(c["case"]), k)
    P(c, "M2 8 H7 V16 H2 Z M17 8 H22 V16 H17 Z", "#ffffff", k)
    F(c, "M5.5 10 L3.5 12 L5.5 14 Z M18.5 10 L20.5 12 L18.5 14 Z", k)
    P(c, "M9 9.5 H13.5 V14.5 H9 Z", c["grey"], k, W(c) * 0.7)


@reg("act-go-spin")
def _(c, k):
    P(c, "M2.5 7 H21.5 V17 H2.5 Z", "#ffffff", k)
    P(c, "M15.5 7 H21.5 V17 H15.5 Z", c.grad(c["case"]), k)
    S(c, "M15.5 12 H21.5", k, W(c) * 0.7)
    F(c, "M16.8 10.8 L18.5 8.3 L20.2 10.8 Z M16.8 13.2 L18.5 15.7 L20.2 13.2 Z", k)
    S(c, "M5 12 H11", k, W(c) * 0.8)


@reg("act-go-obj-arrow")
def _(c, k):
    S(c, "M4 20 L17 7", k, W(c) * 2.6)
    S(c, "M4 20 L17 7", c.lighten(c["green"], 0.3), W(c) * 1.1)
    P(c, "M11 4 H20 V13 Z", grad(c, "green"), k)


@reg("act-go-obj-ellipse")
def _(c, k): P(c, "M2.5 12 A9.5 6.5 0 1 1 21.5 12 A9.5 6.5 0 1 1 2.5 12 Z", grad(c, "green", 0.5), k)
@reg("act-go-obj-rect")
def _(c, k): P(c, "M3 6 H21 V18 H3 Z", grad(c, "green", 0.5), k)


@reg("act-go-cells")
def _(c, k):
    """A spreadsheet's grid behind a border example."""
    S(c, "M4 4 H20 V20 H4 Z M4 12 H20 M12 4 V20", c.lighten(c["grey"], 0.35), W(c) * 0.6)


def _border(kind):
    def g(c, k):
        GLYPHS["act-go-cells"](c, k)
        w = W(c)
        if kind == "double-bottom":
            S(c, "M3 18.5 H21 M3 21.5 H21", c["blue"], w * 0.9)
        elif kind == "thick-bottom":
            S(c, "M3 20 H21", c["blue"], w * 2)
        elif kind == "thick-outside":
            S(c, "M4 4 H20 V20 H4 Z", c["blue"], w * 1.8)
        elif kind == "top-n-bottom":
            S(c, "M3 4 H21 M3 20 H21", c["blue"], w * 0.9)
        elif kind == "top-n-double-bottom":
            S(c, "M3 4 H21 M3 18.5 H21 M3 21.5 H21", c["blue"], w * 0.9)
        elif kind == "top-n-thick-bottom":
            S(c, "M3 4 H21", c["blue"], w * 0.9)
            S(c, "M3 20 H21", c["blue"], w * 2)
    return g


for _b in ("double-bottom", "thick-bottom", "thick-outside", "top-n-bottom", "top-n-double-bottom",
           "top-n-thick-bottom"):
    reg(f"act-go-border-{_b}")(_border(_b))


def _valign(kind):
    def g(c, k):
        P(c, "M3 2.5 H21 V21.5 H3 Z", "#ffffff", c["grey"], W(c) * 0.7)
        bl = c["blue"]
        if kind == "top":
            S(c, "M6 6 H18 M6 9.5 H14", bl)
        elif kind == "center":
            S(c, "M6 10.25 H18 M6 13.75 H14", bl)
        elif kind == "bottom":
            S(c, "M6 14.5 H18 M6 18 H14", bl)
        elif kind == "justify":
            S(c, "M6 6 H18 M6 10 H18 M6 14 H18 M6 18 H18", bl)
        elif kind == "distributed":
            S(c, "M6 6 H15 M6 12 H15 M6 18 H15", bl)
            S(c, "M18.5 5.5 V18.5 M17 7 L18.5 5.5 L20 7 M17 17 L18.5 18.5 L20 17", k, W(c) * 0.7)
        elif kind == "hdist":
            S(c, "M6 7 V14 M12 7 V14 M18 7 V14", bl)
            S(c, "M5.5 18 H18.5 M7 16.5 L5.5 18 L7 19.5 M17 16.5 L18.5 18 L17 19.5", k, W(c) * 0.7)
    return g


for _v in ("top", "center", "bottom", "justify", "distributed", "hdist"):
    reg(f"act-go-valign-{_v}")(_valign(_v))


def _zeros(c, k, n, x0=9):
    for i in range(n):
        S(c, f"M{x0 + i * 4.2:g} 8.5 a1.6 3 0 1 0 0.01 0 Z", k)


@reg("act-go-prec-up")
def _(c, k):
    D(c, 5, 14.5, 1.4, k); _zeros(c, k, 3, 8.5)
    S(c, "M5 19.5 H19 M16.5 17.5 L19 19.5 L16.5 21.5", c["green"], W(c) * 0.9)


@reg("act-go-prec-down")
def _(c, k):
    D(c, 5, 14.5, 1.4, k); _zeros(c, k, 1, 8.5)
    S(c, "M19 19.5 H5 M7.5 17.5 L5 19.5 L7.5 21.5", c["red"], W(c) * 0.9)


@reg("act-go-thousands")
def _(c, k):
    S(c, "M4 7 L5.5 5.5 V14.5", k)
    S(c, "M7.5 14 L6.5 17.5", k, W(c) * 1.2)
    _zeros(c, k, 3, 11)


@reg("act-go-fx")
def _(c, k):
    S(c, "M11 4.5 C9 3.5 7.5 4.5 7.5 7 V19 C7.5 20.5 6.5 21 5 20.5 M4.5 10 H11", k)
    S(c, "M13 10 L20 19 M20 10 L13 19", c["blue"])


@reg("act-go-slicer")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", c.grad(c["page"]), k)
    S(c, "M5.5 6.5 H18.5", k, W(c) * 0.8)
    P(c, "M5.5 9 H18.5 V12 H5.5 Z", c.lighten(c["green"], 0.3), k, W(c) * 0.6)
    P(c, "M5.5 13.5 H18.5 V16.5 H5.5 Z", "#ffffff", k, W(c) * 0.6)
    P(c, "M5.5 18 H18.5 V20 H5.5 Z", c.lighten(c["green"], 0.3), k, W(c) * 0.6)


@reg("act-go-hf")
def _(c, k):
    _page(c, k)
    c.parts.append(f'<rect x="7" y="5" width="7" height="2.4" fill="{c["blue"]}"/>')
    c.parts.append(f'<rect x="7" y="17" width="10" height="2.4" fill="{c["blue"]}"/>')
    S(c, "M7 10.5 H17 M7 13.5 H15", c.lighten(c["grey"], 0.2), W(c) * 0.6)


@reg("act-go-hf-n")
def _(c, k):
    c.group("translate(-2 -1.5)", lambda cv: _page(cv, k))
    c.group("translate(1.5 1)", lambda cv: _page(cv, k))
    c.parts.append(f'<rect x="9" y="6.5" width="7" height="2.4" fill="{c["blue"]}"/>')
    c.parts.append(f'<rect x="9" y="18" width="9" height="2.4" fill="{c["blue"]}"/>')


@reg("act-go-pivot")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", "#ffffff", k)
    c.parts.append(f'<rect x="3.5" y="3.5" width="17" height="4" fill="{c.lighten(c["blue"], 0.35)}"/>')
    c.parts.append(f'<rect x="3.5" y="7.5" width="4.5" height="13" fill="{c.lighten(c["green"], 0.35)}"/>')
    S(c, "M3 8 H21 M8 3 V21", k, W(c) * 0.7)
    S(c, "M11 18 C11 13 13 11 17 11 M15 9 L17 11 L15 13", c["red"], W(c) * 0.9)


# ---- media -------------------------------------------------------------------
def _media(shape, col="green"):
    def g(c, k):
        P(c, shape, grad(c, col, 0.3), k)
    return g


reg("act-go-play")(_media("M6 3.5 L20 12 L6 20.5 Z"))
reg("act-go-pause")(_media("M5.5 4 H10 V20 H5.5 Z M14 4 H18.5 V20 H14 Z"))
reg("act-go-stop")(_media("M5 5 H19 V19 H5 Z", "red"))
reg("act-go-record")(_media("M12 3.5 A8.5 8.5 0 1 1 11.99 3.5 Z", "red"))
reg("act-go-eject")(_media("M12 3.5 L20.5 13 H3.5 Z M3.5 16 H20.5 V20 H3.5 Z", "blue"))
reg("act-go-seek-fwd")(_media("M2.5 5 L12 12 L2.5 19 Z M12 5 L21.5 12 L12 19 Z"))
reg("act-go-seek-back")(_media("M21.5 5 L12 12 L21.5 19 Z M12 5 L2.5 12 L12 19 Z"))
reg("act-go-skip-fwd")(_media("M4 4.5 L15.5 12 L4 19.5 Z M16 4.5 H20 V19.5 H16 Z"))
reg("act-go-skip-back")(_media("M20 4.5 L8.5 12 L20 19.5 Z M4 4.5 H8 V19.5 H4 Z"))
reg("act-go-play2")(_media("M4 3 L13 8.5 L4 14 Z M11 10 L20 15.5 L11 21 Z"))
reg("act-go-stop2")(_media("M3 3 H13 V13 H3 Z M10 10 H21 V21 H10 Z", "red"))


@reg("act-go-sleeve")
def _(c, k):
    P(c, "M14 4.5 A7.5 7.5 0 1 1 13.99 4.5 Z", c.grad(c["metal"]), k)
    D(c, 18, 12, 1.4, k)
    P(c, "M2.5 3.5 H14.5 V20.5 H2.5 Z", grad(c, "violet", 0.35), k)
    O(c, 8.5, 12, 3, "#ffffff", w=W(c) * 0.7)


@reg("act-go-note")
def _(c, k):
    S(c, "M12 17.5 V4 L19 6.5 V9.5 L12 7", k)
    P(c, "M12 17.5 A3.4 2.7 0 1 1 5.2 17.5 A3.4 2.7 0 1 1 12 17.5 Z", grad(c, "violet", 0.3), k)


@reg("act-go-note16")
def _(c, k):
    S(c, "M12 18 V3.5 C14 6 18 6 18 10 M12 8 C14 10.5 18 10.5 18 14.5", k)
    P(c, "M12 18 A3.4 2.7 0 1 1 5.2 18 A3.4 2.7 0 1 1 12 18 Z", grad(c, "violet", 0.3), k)


@reg("act-go-playlist")
def _(c, k):
    S(c, "M3 5.5 H16 M3 10 H16 M3 14.5 H11 M3 19 H11", k)


@reg("act-go-playlist-normal")
def _(c, k):
    S(c, "M3 5.5 H14 M3 10 H14 M3 14.5 H14", k)
    S(c, "M3 19.5 H19 M16.5 17 L19 19.5 L16.5 22", c["green"])


@reg("act-go-repeat")
def _(c, k):
    S(c, "M4 13 V10 A3 3 0 0 1 7 7 H18 M15.5 4 L18.5 7 L15.5 10 M20 11 V14 A3 3 0 0 1 17 17 H6 M8.5 14 L5.5 17 L8.5 20",
      k, W(c) * 2.4)
    S(c, "M4 13 V10 A3 3 0 0 1 7 7 H18 M15.5 4 L18.5 7 L15.5 10 M20 11 V14 A3 3 0 0 1 17 17 H6 M8.5 14 L5.5 17 L8.5 20",
      c.lighten(c["green"], 0.2), W(c) * 1.1)


@reg("act-go-shuffle")
def _(c, k):
    d = "M3 7 H7 C12 7 12 17 17 17 H20 M17.5 14.5 L20.5 17 L17.5 19.5 M3 17 H7 C12 17 12 7 17 7 H20 M17.5 4.5 L20.5 7 L17.5 9.5"
    S(c, d, k, W(c) * 2.4)
    S(c, d, c.lighten(c["green"], 0.2), W(c) * 1.1)


@reg("act-go-one")
def _(c, k): S(c, "M9 7 L13 4 V20 M9 20 H17", k)


@reg("act-go-progress")
def _(c, k):
    O(c, 12, 12, 7, k, w=W(c) * 0.5)
    S(c, "M12 5 A7 7 0 0 1 19 12 A7 7 0 0 1 12 19", k)


@reg("act-go-clip")
def _(c, k): S(c, "M15 7 V16 A3 3 0 0 1 9 16 V6 A2 2 0 0 1 13 6 V15", k)


# ---- people, chat ---------------------------------------------------------------
@reg("act-go-bubble")
def _(c, k): P(c, "M2.5 4 H21.5 V17 H11 L5.5 21.5 V17 H2.5 Z", c.grad(c["page"]), k)


@reg("act-go-callout")
def _(c, k):
    P(c, "M3 4 H21 V15 H12 L7 20 V15 H3 Z", grad(c, "yellow", 0.5), k)
    S(c, "M7 8 H17 M7 11.5 H14", k, W(c) * 0.7)


def _im(word, col):
    def g(c, k):
        P(c, "M2 3.5 H22 V17 H11 L5.5 21.5 V17 H2 Z", grad(c, col, 0.45), k)
        TX(c, 12, 13.6, word, 7.5 if len(word) <= 3 else 6.5, k)
    return g


@reg("act-go-hash")
def _(c, k): S(c, "M9 4 L7 20 M16 4 L14 20 M4.5 9 H20 M4 15 H19.5", k, W(c) * 1.2)


@reg("act-go-megaphone")
def _(c, k):
    P(c, "M3 9 H7 L17 4 V20 L7 15 H3 Z", grad(c, "orange", 0.4), k)
    S(c, "M7 15 L9 20.5 H11.5 L10 15.5", k)
    S(c, "M19.5 9 Q21.5 12 19.5 15", k)


@reg("act-go-mouse")
def _(c, k):
    P(c, "M6 9 A6 6 0 0 1 18 9 V15 A6 6 0 0 1 6 15 Z", c.grad(c["case"]), k)
    S(c, "M6 10 H18 M12 3 V10", k, W(c) * 0.8)


def _mouse(which):
    def g(c, k):
        GLYPHS["act-go-mouse"](c, k)
        if which == "left":
            P(c, "M6 10 V9 A6 6 0 0 1 12 3 V10 Z", c["blue"], k, W(c) * 0.8)
        elif which == "right":
            P(c, "M18 10 V9 A6 6 0 0 0 12 3 V10 Z", c["blue"], k, W(c) * 0.8)
        if which == "middle":
            P(c, "M10.5 5 H13.5 V9.5 H10.5 Z", c["blue"], k, W(c) * 0.6)
    return g


for _m in ("left", "middle", "right"):
    reg(f"act-go-mouse-{_m}")(_mouse(_m))


@reg("act-go-phone")
def _(c, k):
    P(c, "M6 2.5 H18 V21.5 H6 Z", c.grad(c["case"]), k)
    P(c, "M7.5 5 H16.5 V18 H7.5 Z", c.grad(c["screen"]), k, W(c) * 0.5)


@reg("act-go-tasks")
def _(c, k):
    GLYPHS["act-go-phone"](c, k)
    P(c, "M9 7 H15 V11 H9 Z", "#ffffff", k, W(c) * 0.5)
    P(c, "M9 12.5 H15 V16.5 H9 Z", "#ffffff", k, W(c) * 0.5)


# ---- kdenlive timeline ----------------------------------------------------------
def _clip(c, k, x0, x1, col, y0=8, y1=16):
    P(c, f"M{x0} {y0} H{x1} V{y1} H{x0} Z", grad(c, col, 0.35), k, W(c) * 0.8)


def _tl(kind):
    def g(c, k):
        w = W(c) * 0.9
        if kind == "ripple":
            _clip(c, k, 2, 10, "blue"); _clip(c, k, 12, 22, "green")
            S(c, "M11 4 V20", c["red"], w)
            S(c, "M12 20 H20 M18 18 L20 20 L18 22", k, w)
        elif kind == "rolling":
            _clip(c, k, 2, 12, "blue"); _clip(c, k, 12, 22, "green")
            S(c, "M12 3 V20", c["red"], w)
            S(c, "M7 20.5 H17 M9 18.5 L7 20.5 L9 22.5 M15 18.5 L17 20.5 L15 22.5", k, w)
        elif kind == "slide":
            _clip(c, k, 1.5, 7.5, "blue"); _clip(c, k, 8.5, 15.5, "orange"); _clip(c, k, 16.5, 22.5, "green")
            S(c, "M7 20.5 H17 M9 18.5 L7 20.5 L9 22.5 M15 18.5 L17 20.5 L15 22.5", k, w)
        elif kind == "slip":
            _clip(c, k, 3, 21, "orange", 5, 19)
            S(c, "M7 12 H17 M9.5 9.5 L7 12 L9.5 14.5 M14.5 9.5 L17 12 L14.5 14.5", k, w)
        elif kind == "markers":
            S(c, "M2 18 H22 M4 18 V21 M8 18 V20 M12 18 V21 M16 18 V20 M20 18 V21", k, w * 0.8)
            P(c, "M6 4 H12 V10 L9 13 L6 10 Z", c["red"], k, w * 0.8)
            P(c, "M14 7 H19 V12 L16.5 14.5 L14 12 Z", c["blue"], k, w * 0.8)
        elif kind == "split":
            _clip(c, k, 3, 21, "blue", 3, 10)
            P(c, "M3 14 H21 V21 H3 Z", grad(c, "green", 0.4), k, W(c) * 0.8)
            S(c, "M5 17.5 L7 15.5 L9 19.5 L11 15 L13 19 L15 16 L17 18.5 L19 17", k, W(c) * 0.6)
            DS(c, "M1 12 H23", c["red"], w * 0.8, "1.5 1.5")
    return g


for _t in ("ripple", "rolling", "slide", "slip", "markers", "split"):
    reg(f"act-go-tl-{_t}")(_tl(_t))


@reg("act-go-colorclip")
def _(c, k):
    P(c, "M3 5 H21 V19 H3 Z", c.grad(c["yellow"], c["red"]), k)


# ---- kstars: a night sky -----------------------------------------------------
def sky(c, k):
    P(c, "M2 2 H22 V22 H2 Z", c.grad(c.darken(c["screen"][1], 0.15), c.darken(c["screen"][1], 0.55)), k)


def star(c, x, y, r, col):
    q = r * 0.3
    c.parts.append(f'<path d="M{x:g} {y - r:g} L{x + q:g} {y - q:g} L{x + r:g} {y:g} L{x + q:g} {y + q:g} L{x:g} {y + r:g} '
                   f'L{x - q:g} {y + q:g} L{x - r:g} {y:g} L{x - q:g} {y - q:g} Z" fill="{col}"/>')


def _kstars(kind):
    def g(c, k):
        sky(c, k)
        wh, ye = "#ffffff", c.lighten(c["yellow"], 0.2)
        w = W(c) * 0.7
        if kind == "stars":
            star(c, 9, 9, 5, wh); star(c, 16.5, 15, 3.5, ye); star(c, 7, 17, 2.2, wh)
        elif kind == "clines":
            S(c, "M5 16 L9 8 L15 10 L19 5 M15 10 L17 18", wh, w)
            for x, y in ((5, 16), (9, 8), (15, 10), (19, 5), (17, 18)):
                D(c, x, y, 1.5, ye)
        elif kind == "cbound":
            DS(c, "M4.5 6 L13 4.5 L19.5 9 L17 19.5 L6 17 Z", ye, w, "1.8 1.4")
            D(c, 9, 10, 1.4, wh); D(c, 14, 13, 1.4, wh)
        elif kind == "cnames":
            S(c, "M5 8 L10 5 L16 7", wh, w)
            for x, y in ((5, 8), (10, 5), (16, 7)):
                D(c, x, y, 1.4, ye)
            TX(c, 12, 19, "Abc", 8, wh)
        elif kind == "art":
            S(c, "M6 19 C4 13 7 9 11 8 C15 7 15 4 19 4 M11 8 C13 12 17 13 19 18", c.lighten(c["orange"], 0.2), W(c) * 0.9)
            for x, y in ((6, 19), (11, 8), (19, 4), (19, 18)):
                D(c, x, y, 1.5, wh)
        elif kind == "deepsky":
            S(c, "M12 12 C14 10 17 12 16 15 C14.5 18.5 9 18 7.5 14 C6 9.5 10 5.5 15 6 C19 6.5 21 10 20 13", wh, w)
            D(c, 12, 12, 2, ye)
        elif kind == "fits":
            P(c, "M5 6 H19 V18 H5 Z", "none", wh, w)
            star(c, 12, 12, 4, ye)
            S(c, "M5 9 H3 M19 15 H21", wh, w)
        elif kind == "grid":
            S(c, "M12 3 V21 M12 3 C6 7 6 17 12 21 M12 3 C18 7 18 17 12 21 M3.5 8 Q12 11 20.5 8 M3 13 Q12 16 21 13 M4 18 Q12 21 20 18",
              c.lighten(c["cyan"], 0.3), w)
        elif kind == "hgrid":
            P(c, "M2.5 17 H21.5 V21.5 H2.5 Z", c["green"], "none")
            S(c, "M3 17 Q12 2 21 17 M7.5 17 Q12 7 16.5 17 M12 3 V17 M3 12 Q12 9 21 12", c.lighten(c["green"], 0.35), w)
            S(c, "M2.5 17 H21.5", wh, w)
        elif kind == "horizon":
            P(c, "M2.5 15 L7 12 L11 14.5 L15 11 L21.5 15 V21.5 H2.5 Z", grad(c, "green", 0.2), wh, w)
            P(c, "M9 9 A3 3 0 0 1 15 9 Z", ye, "none")
            star(c, 6, 6, 2, wh); star(c, 18, 5, 1.6, wh)
        elif kind == "mw":
            c.parts.append(f'<path d="M2 15 L15 2 H22 L22 4 L4 22 H2 Z" fill="#ffffff" opacity="0.3"/>')
            for x, y, r in ((6, 15, 1.3), (9, 11, 1), (12, 10, 1.4), (14, 7, 1), (17, 6, 1.2), (10, 14, 0.9), (19, 9, 0.9)):
                D(c, x, y, r, wh)
        elif kind == "satellites":
            G(c, "satellite", 3, 3, 18, wh)
        elif kind == "solar":
            S(c, "M3 12 A9 4.5 0 1 1 21 12 A9 4.5 0 1 1 3 12 Z", c.lighten(c["cyan"], 0.3), w)
            D(c, 12, 12, 3.5, ye)
            D(c, 19.5, 9.3, 1.8, c.lighten(c["blue"], 0.3))
        elif kind == "supernovae":
            P(c, "M12 3 L13.8 9 L20 7 L15.5 11.8 L20.5 16 L14 15 L12 21 L10 15 L3.5 16 L8.5 11.8 L4 7 L10.2 9 Z",
              ye, c["orange"], w)
        elif kind == "xplanet":
            P(c, "M12 6 A6 6 0 1 1 11.99 6 Z", grad(c, "orange", 0.3), "none")
            S(c, "M3 15 C1 18 10 17 16 13 C22 9 23 6 20 6.5", ye, W(c) * 0.9)
        elif kind == "ekos":
            S(c, "M5 13 L17 5.5 L19 8.5 L7 16 Z M11 12.5 L8 20 M11 12.5 L14 20", wh, w)
            G(c, "gear", 13, 13, 9, ye)
        elif kind == "indi":
            S(c, "M5 13 L17 5.5 L19 8.5 L7 16 Z M11 12.5 L8 20 M11 12.5 L14 20", wh, w)
            G(c, "plug", 14, 13, 8, ye)
    return g


for _k in ("stars", "clines", "cbound", "cnames", "art", "deepsky", "fits", "grid", "hgrid", "horizon", "mw",
           "satellites", "solar", "supernovae", "xplanet", "ekos", "indi"):
    reg(f"act-go-ks-{_k}")(_kstars(_k))


# ---- kruler ----------------------------------------------------------------
def _ruler(edge):
    def g(c, k):
        if edge == "east":
            P(c, "M15 2 H21 V22 H15 Z", grad(c, "yellow", 0.3), k)
            S(c, "M15 5 H18 M15 8 H17 M15 11 H18 M15 14 H17 M15 17 H18 M15 20 H17", k, W(c) * 0.6)
            S(c, "M3 12 H11 M8.5 9.5 L11 12 L8.5 14.5", c["blue"])
        elif edge == "south":
            rot(c, 90, lambda cv: GLYPHS["act-go-ruler-east"](cv, k))
        elif edge == "west":
            mirror(c, lambda cv: GLYPHS["act-go-ruler-east"](cv, k))
    return g


for _e in ("east", "south", "west"):
    reg(f"act-go-ruler-{_e}")(_ruler(_e))


# ---- labplot ---------------------------------------------------------------
def axes(c, k, arrows=True):
    S(c, "M4 3 V20 H21", k)
    if arrows:
        S(c, "M2.5 5 L4 3 L5.5 5 M19 18.5 L21 20 L19 21.5", k, W(c) * 0.7)


def _lp(kind):
    def g(c, k):
        bl, rd, w = c["blue"], c["red"], W(c)
        if kind == "curve":
            axes(c, k); S(c, "M5 16 C8 4 11 4 13 10 C15 16 18 16 20 7", bl)
        elif kind == "segments":
            axes(c, k); S(c, "M5 16 L9 8 M10.5 10 L14 14 M15.5 12 L20 6", bl)
            for x, y in ((5, 16), (9, 8), (10.5, 10), (14, 14), (15.5, 12), (20, 6)):
                D(c, x, y, 1.2, k)
        elif kind == "equation":
            axes(c, k); S(c, "M5 18 Q12 -6 20 18", bl)
            TX(c, 12.5, 16.5, "f", 9, rd, italic=True)
        elif kind == "fit":
            axes(c, k)
            for x, y in ((6, 15), (8, 16), (10, 11), (13, 12), (15, 8), (18, 8), (19, 5)):
                D(c, x, y, 1.3, k)
            S(c, "M5 17 L20 5", rd)
        elif kind == "ffilter":
            axes(c, k); S(c, "M5 12 L6 8 L7 15 L8 9 L9 14 L10 10 L11 13", c["grey"], w * 0.6)
            S(c, "M11 12 C13 6 15 6 17 12 C18 15 19 15 20 12", bl)
            P(c, "M7 3 H15 L12 6.5 V9.5 L10 8.5 V6.5 Z", rd, k, w * 0.5)
        elif kind == "ftransform":
            axes(c, k); S(c, "M5 10 C6.5 5 8 5 9 10 C10 15 11.5 15 12 10", c["grey"], w * 0.7)
            S(c, "M14 20 V8 M17 20 V13 M20 20 V16", bl, w * 1.2)
        elif kind == "interp":
            axes(c, k); S(c, "M5 15 C8 6 10 6 12 11 C14 16 17 15 20 6", bl)
            for x, y in ((5, 15), (12, 11), (20, 6), (8.4, 8.5), (16, 14.2)):
                D(c, x, y, 1.5, rd)
        elif kind == "smooth":
            axes(c, k); S(c, "M5 15 L7 10 L8.5 14 L10 8 L12 12 L13.5 7 L15 11 L17 6 L18.5 9 L20 5", c["grey"], w * 0.6)
            S(c, "M5 14 C9 11 14 9 20 6", rd)
        elif kind == "axis-points":
            axes(c, k)
            for x in (8, 12, 16):
                D(c, x, 20, 1.6, bl)
            for y in (8, 12, 16):
                D(c, 4, y, 1.6, rd)
        elif kind == "four":
            P(c, "M4 4 H20 V20 H4 Z", "#ffffff", k)
            S(c, "M8 4 V6 M12 4 V6 M16 4 V6 M8 20 V18 M12 20 V18 M16 20 V18 M4 8 H6 M4 12 H6 M4 16 H6 "
                 "M20 8 H18 M20 12 H18 M20 16 H18", k, w * 0.7)
            S(c, "M7 15 C10 8 13 8 17 12", bl, w * 0.9)
        elif kind == "two":
            axes(c, k, False)
            S(c, "M8 20 V18 M12 20 V18 M16 20 V18 M4 8 H6 M4 12 H6 M4 16 H6", k, w * 0.7)
            S(c, "M7 16 C10 7 13 8 18 11", bl, w * 0.9)
        elif kind == "centered":
            S(c, "M12 3 V21 M3 12 H21", k)
            S(c, "M8 11 V13 M16 11 V13 M11 8 H13 M11 16 H13", k, w * 0.7)
            S(c, "M4 18 C9 16 15 8 20 6", bl, w * 0.9)
        elif kind == "origin":
            S(c, "M12 3 V21 M3 12 H21", k)
            O(c, 12, 12, 2.6, rd)
            S(c, "M4 18 C9 16 15 8 20 6", bl, w * 0.9)
        elif kind == "axis-h":
            S(c, "M2 14 H21 M19 12 L21.5 14 L19 16 M5 14 V17 M9 14 V16 M13 14 V17 M17 14 V16", k)
        elif kind == "axis-v":
            S(c, "M10 22 V3 M8 5 L10 2.5 L12 5 M10 19 H7 M10 15 H8 M10 11 H7 M10 7 H8", k)
        elif kind == "matrix":
            S(c, "M7 3 H4 V21 H7 M17 3 H20 V21 H17", k)
            for x in (8.5, 12, 15.5):
                for y in (7.5, 12, 16.5):
                    D(c, x, y, 1.3, bl)
        elif kind == "workbook":
            P(c, "M6 3 H21 V17 H6 Z", c.grad(c["page"]), k, w * 0.8)
            P(c, "M3 7 H18 V21 H3 Z", c.grad(c["page"]), k)
            S(c, "M3 11.5 H18 M3 16 H18 M8 7 V21 M13 7 V21", k, w * 0.6)
            c.parts.append(f'<rect x="3.6" y="7.6" width="13.8" height="3.4" fill="{c.lighten(c["green"], 0.3)}"/>')
        elif kind == "worksheet":
            _page(c, k)
            S(c, "M7.5 8 V18 H17", k, w * 0.8)
            S(c, "M8.5 16 L11 12 L13.5 14 L16.5 9", bl, w * 0.9)
        elif kind == "tex":
            TX(c, 6.5, 14, "T", 11, k)
            TX(c, 12.3, 17.5, "E", 10, k)
            TX(c, 18, 14, "X", 11, k)
    return g


for _l in ("curve", "segments", "equation", "fit", "ffilter", "ftransform", "interp", "smooth", "axis-points",
           "four", "two", "centered", "origin", "axis-h", "axis-v", "matrix", "workbook", "worksheet", "tex"):
    reg(f"act-go-lp-{_l}")(_lp(_l))


def _layout(kind):
    def g(c, k):
        f = grad(c, "green", 0.45)
        if kind == "h":
            for x in (2.5, 9, 15.5):
                P(c, f"M{x} 7 h6 v10 h-6 Z", f, k, W(c) * 0.8)
        elif kind == "v":
            for y in (2.5, 9, 15.5):
                P(c, f"M5 {y} h14 v6 h-14 Z", f, k, W(c) * 0.8)
        elif kind == "grid":
            for x in (3, 12.5):
                for y in (3, 12.5):
                    P(c, f"M{x} {y} h8.5 v8.5 h-8.5 Z", f, k, W(c) * 0.8)
        elif kind == "break":
            for x, y in ((3, 3), (13, 4), (4, 13)):
                P(c, f"M{x} {y} h7 v7 h-7 Z", grad(c, "grey", 0.5), k, W(c) * 0.8)
    return g


for _y in ("h", "v", "grid", "break"):
    reg(f"act-go-layout-{_y}")(_layout(_y))


# ---- office charts --------------------------------------------------------------
def chart_axes(c, k):
    S(c, "M3 3 V21 H21", k)


def _chart(kind):
    def g(c, k):
        bl, gr, rd, ye = c["blue"], c["green"], c["red"], c["yellow"]
        w = W(c) * 0.7
        lb, lg = c.lighten(bl, 0.25), c.lighten(gr, 0.25)
        if kind in ("pie", "ring", "polar", "polar-stacked"):
            pass
        else:
            chart_axes(c, k)
        if kind == "bar":
            P(c, "M5.5 12 h4 v9 h-4 Z", bl, k, w); P(c, "M11 7 h4 v14 h-4 Z", gr, k, w); P(c, "M16.5 14 h4 v7 h-4 Z", rd, k, w)
        elif kind == "bar-stacked":
            for x, a1, a2 in ((5.5, 6, 4), (11, 9, 6), (16.5, 4, 5)):
                P(c, f"M{x} {21 - a1} h4 v{a1} h-4 Z", bl, k, w)
                P(c, f"M{x} {21 - a1 - a2} h4 v{a2} h-4 Z", ye, k, w)
        elif kind == "bar-percentage":
            for x, a1 in ((5.5, 7), (11, 11), (16.5, 5)):
                P(c, f"M{x} {21 - a1} h4 v{a1} h-4 Z", bl, k, w)
                P(c, f"M{x} 5 h4 v{16 - a1} h-4 Z", ye, k, w)
        elif kind == "line":
            S(c, "M5 17 L9 11 L13 14 L19 6", bl, W(c) * 1.1)
        elif kind == "line-stacked":
            S(c, "M5 18 L9 15 L13 16 L19 12", bl, W(c) * 1.1)
            S(c, "M5 12 L9 8 L13 10 L19 4", rd, W(c) * 1.1)
        elif kind == "line-percentage":
            S(c, "M5 17 L9 14 L13 15 L19 11", bl, W(c) * 1.1)
            S(c, "M5 5 H20", rd, W(c) * 1.1)
            S(c, "M5 11 L9 8 L13 10 L19 7", gr, W(c) * 0.8)
        elif kind == "line-forecast":
            S(c, "M5 17 L9 12 L12 14", bl, W(c) * 1.1)
            DS(c, "M12 14 L16 9 L20 6", rd, W(c) * 1.1, "2 1.6")
        elif kind == "area":
            P(c, "M3.5 20.5 V15 L8 9 L13 13 L20.5 6 V20.5 Z", lb, k, w)
        elif kind == "area-stacked":
            P(c, "M3.5 20.5 V11 L8 6 L13 9 L20.5 4 V20.5 Z", ye, k, w)
            P(c, "M3.5 20.5 V16 L8 13 L13 15 L20.5 11 V20.5 Z", lb, k, w)
        elif kind == "area-percentage":
            P(c, "M3.5 20.5 V4 H20.5 V20.5 Z", ye, k, w)
            P(c, "M3.5 20.5 V13 L8 9 L13 12 L20.5 8 V20.5 Z", lb, k, w)
        elif kind == "area-peak":
            P(c, "M3.5 20.5 V16 L8 13 L12.5 6 L17 14 L20.5 12 V20.5 Z", lg, k, w)
            P(c, "M12.5 3.5 A2.5 2.5 0 1 1 12.49 3.5 Z", rd, k, w)
        elif kind == "pie":
            P(c, "M12 12 V3 A9 9 0 0 1 20.5 15 Z", rd, k, w)
            P(c, "M12 12 L20.5 15 A9 9 0 0 1 5 17.6 Z", bl, k, w)
            P(c, "M12 12 L5 17.6 A9 9 0 0 1 12 3 Z", ye, k, w)
        elif kind == "ring":
            P(c, "M12 3 A9 9 0 0 1 20.5 15 L16.7 13.6 A5 5 0 0 0 12 7 Z", rd, k, w)
            P(c, "M20.5 15 A9 9 0 0 1 5 17.6 L8.1 15.1 A5 5 0 0 0 16.7 13.6 Z", bl, k, w)
            P(c, "M5 17.6 A9 9 0 0 1 12 3 V7 A5 5 0 0 0 8.1 15.1 Z", ye, k, w)
        elif kind in ("polar", "polar-stacked"):
            S(c, "M12 2.5 L21 9 L17.5 20 H6.5 L3 9 Z", c["grey"], w)
            S(c, "M12 12 L12 2.5 M12 12 L21 9 M12 12 L17.5 20 M12 12 L6.5 20 M12 12 L3 9", c["grey"], w * 0.6)
            if kind == "polar-stacked":
                P(c, "M12 4 L19 9.5 L16 18 L8 17 L5 9.5 Z", c.lighten(ye, 0.1), k, w)
            P(c, "M12 7 L17 10.5 L14 15 L9 16 L7 10 Z", lb, k, w)
        elif kind == "scatter":
            for x, y, col in ((6, 16, bl), (8, 11, rd), (11, 14, bl), (13, 8, gr), (16, 12, rd), (18, 6, bl), (15, 17, gr)):
                P(c, f"M{x} {y - 1.7} A1.7 1.7 0 1 1 {x - 0.01} {y - 1.7} Z", col, k, w * 0.8)
    return g


for _c in ("bar", "bar-stacked", "bar-percentage", "line", "line-stacked", "line-percentage", "line-forecast",
           "area", "area-stacked", "area-percentage", "area-peak", "pie", "ring", "polar", "polar-stacked", "scatter"):
    reg(f"act-go-chart-{_c}")(_chart(_c))


# ---- vector editing (nodes, objects) --------------------------------------------
def node_sq(c, x, y, col, k, r=2):
    P(c, f"M{x - r} {y - r} h{2 * r} v{2 * r} h{-2 * r} Z", col, k, W(c) * 0.6)


def _node(kind):
    def g(c, k):
        cy = c["cyan"]
        if kind == "seg-curve":
            S(c, "M4 18 C6 6 18 18 20 6", k)
            node_sq(c, 4, 18, "#ffffff", k); node_sq(c, 20, 6, "#ffffff", k)
            DS(c, "M8 12 C10 10 14 14 16 12", cy, W(c) * 0.7, "1.5 1.2")
        elif kind == "seg-line":
            S(c, "M4 18 L20 6", k)
            node_sq(c, 4, 18, "#ffffff", k); node_sq(c, 20, 6, "#ffffff", k)
            S(c, "M8 15 L16 9", cy, W(c) * 1.4)
        elif kind == "transform":
            DS(c, "M3 3 H21 V21 H3 Z", c["grey"], W(c) * 0.6, "1.5 1.2")
            S(c, "M6 16 C8 6 14 6 18 12", k)
            for x, y in ((6, 16), (11, 8.5), (18, 12)):
                node_sq(c, x, y, cy, k, 1.8)
            for x, y in ((3, 3), (21, 3), (3, 21), (21, 21)):
                F(c, f"M{x - 1.5} {y - 1.5} h3 v3 h-3 Z", k)
        elif kind == "cusp":
            S(c, "M3 19 L12 9 L21 19", k)
            S(c, "M12 9 L7 4 M12 9 L17 4", cy, W(c) * 0.7)
            D(c, 7, 4, 1.3, cy); D(c, 17, 4, 1.3, cy)
            P(c, "M12 6.5 L14.5 9 L12 11.5 L9.5 9 Z", "#ffffff", k, W(c) * 0.6)
        elif kind == "smooth":
            S(c, "M3 19 C6 10 9 9 12 9 C16 9 19 13 21 19", k)
            S(c, "M5 9 H18", cy, W(c) * 0.7)
            D(c, 5, 9, 1.3, cy); D(c, 18, 9, 1.3, cy)
            node_sq(c, 12, 9, "#ffffff", k)
        elif kind == "symmetric":
            S(c, "M3 19 C6 10 9 9 12 9 C15 9 18 10 21 19", k)
            S(c, "M6 9 H18", cy, W(c) * 0.7)
            D(c, 6, 9, 1.3, cy); D(c, 18, 9, 1.3, cy)
            P(c, "M12 7 A2 2 0 1 1 11.99 7 Z", "#ffffff", k, W(c) * 0.6)
            S(c, "M9 6 V12 M15 6 V12", cy, W(c) * 0.5)
        elif kind == "auto":
            S(c, "M3 19 C6 10 9 9 12 9 C15 9 18 10 21 19", k)
            P(c, "M12 6.5 A2.5 2.5 0 1 1 11.99 6.5 Z", c.lighten(c["yellow"], 0.2), k, W(c) * 0.6)
            TX(c, 12, 22.5, "A", 7, c["blue"])
    return g


for _n in ("seg-curve", "seg-line", "transform", "cusp", "smooth", "symmetric", "auto"):
    reg(f"act-go-node-{_n}")(_node(_n))


def _order(front):
    def g(c, k):
        vi = grad(c, "violet", 0.35)
        gy = c.lighten(c["grey"], 0.6)
        if front:
            P(c, "M3 3 H14 V14 H3 Z", gy, k)
            P(c, "M9 9 H20 V20 H9 Z", vi, k)
        else:
            P(c, "M9 9 H20 V20 H9 Z", vi, k)
            P(c, "M3 3 H14 V14 H3 Z", gy, k)
    return g


reg("act-go-order-front")(_order(True))
reg("act-go-order-back")(_order(False))


@reg("act-go-obj-cols")
def _(c, k):
    for x in (3, 10, 17):
        P(c, f"M{x} 3 h4.5 v18 h-4.5 Z", grad(c, "violet", 0.5), k, W(c) * 0.8)


@reg("act-go-obj-rows")
def _(c, k):
    for y in (3, 10, 17):
        P(c, f"M3 {y} h18 v4.5 h-18 Z", grad(c, "violet", 0.5), k, W(c) * 0.8)


@reg("act-go-obj-height")
def _(c, k):
    P(c, "M3 6 H13 V18 H3 Z", grad(c, "violet", 0.5), k)
    S(c, "M18 3 V21 M15.5 5.5 L18 3 L20.5 5.5 M15.5 18.5 L18 21 L20.5 18.5", c["blue"])


@reg("act-go-obj-width")
def _(c, k):
    P(c, "M6 3 H18 V13 H6 Z", grad(c, "violet", 0.5), k)
    S(c, "M3 18 H21 M5.5 15.5 L3 18 L5.5 20.5 M18.5 15.5 L21 18 L18.5 20.5", c["blue"])


@reg("act-go-obj-rot")
def _(c, k):
    P(c, "M7 8 H17 V18 H7 Z", grad(c, "violet", 0.5), k)
    S(c, "M4 9 A9 9 0 0 1 17 3.5 M14 2 L17.5 3.5 L16 7", c["blue"])


@reg("act-go-obj-flip")
def _(c, k):
    P(c, "M10 4 V20 L3 20 Z", grad(c, "violet", 0.4), k)
    P(c, "M14 4 V20 L21 20 Z", "none", k)
    DS(c, "M12 2 V22", c["blue"], W(c) * 0.7, "1.6 1.2")


@reg("act-go-stroke")
def _(c, k):
    S(c, "M3 5 H21", k, W(c) * 1.6)
    DS(c, "M3 11 H21", k, W(c) * 1.2, "3.5 2")
    DS(c, "M3 17 H21", k, W(c) * 1.0, "1 2")


@reg("act-go-topath")
def _(c, k):
    DS(c, "M3 12 A6 6 0 1 1 15 12 A6 6 0 1 1 3 12 Z", c["grey"], W(c) * 0.7, "1.5 1.2")
    S(c, "M12 9 C16 4 21 8 20 13 C19 18 13 20 11 15", k)
    for x, y in ((12, 9), (20, 13), (11, 15)):
        node_sq(c, x, y, c["cyan"], k, 1.7)


# ---- misc ---------------------------------------------------------------------
@reg("act-go-generalise")
def _(c, k):
    P(c, "M4 15 H10 V21 H4 Z M14 15 H20 V21 H14 Z", c.grad(c["page"]), k, W(c) * 0.8)
    S(c, "M7 15 V12 H17 V15 M12 12 V9", k)
    P(c, "M12 2.5 L16 9 H8 Z", "#ffffff", k)


@reg("act-go-tiles")
def _(c, k):
    for x, y in ((9, 3), (3, 9), (13, 11)):
        P(c, f"M{x} {y} h8 v10 h-8 Z", c.grad(c["page"]), k, W(c) * 0.8)
        S(c, f"M{x + 2.5} {y + 3} h3 M{x + 2.5} {y + 6} h3", c["red"], W(c) * 0.7)


@reg("act-go-board")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", "#ffffff", k)
    for i in range(3):
        for j in range(3):
            if (i + j) % 2 == 0:
                c.parts.append(f'<rect x="{3 + i * 6}" y="{3 + j * 6}" width="6" height="6" fill="{c["ink"]}"/>')
    P(c, "M3 3 H21 V21 H3 Z", "none", k)


@reg("act-go-axonometric")
def _(c, k):
    S(c, "M12 3 L21 7.5 V16.5 L12 21 L3 16.5 V7.5 Z", k)
    S(c, "M12 3 V21 M3 7.5 L21 16.5 M21 7.5 L3 16.5 M7.5 5.25 V18.75 M16.5 5.25 V18.75", c["blue"], W(c) * 0.6)


@reg("act-go-grip")
def _(c, k):
    S(c, "M5 9.5 H19 M5 14.5 H19", k)
    S(c, "M9 6 L12 3 L15 6 M9 18 L12 21 L15 18", c["blue"])


@reg("act-go-hexagon")
def _(c, k): P(c, "M7 3.5 H17 L22 12 L17 20.5 H7 L2 12 Z", grad(c, "cyan", 0.45), k)


@reg("act-go-hotpixels")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", c.grad(c["screen"]), k)
    for x, y in ((7, 8), (15, 6), (11, 15), (17, 16)):
        c.parts.append(f'<rect x="{x - 1.4}" y="{y - 1.4}" width="2.8" height="2.8" fill="{c["red"] if x != 15 else "#ffffff"}"/>')


@reg("act-go-item")
def _(c, k):
    P(c, "M2.5 7 H21.5 V17 H2.5 Z", c.lighten(c["blue"], 0.55), k)
    D(c, 6.5, 12, 1.8, k)
    S(c, "M10 12 H18.5", k)


@reg("act-go-join")
def _(c, k):
    O(c, 9, 12, 6.5, k); O(c, 15, 12, 6.5, k)
    F(c, "M12 6.2 A6.5 6.5 0 0 1 12 17.8 A6.5 6.5 0 0 1 12 6.2 Z", c["blue"])


@reg("act-go-merge")
def _(c, k):
    S(c, "M4 4 C4 10 12 10 12 14 M20 4 C20 10 12 10 12 14 V20", k, W(c) * 2.4)
    S(c, "M4 4 C4 10 12 10 12 14 M20 4 C20 10 12 10 12 14 V20", c.lighten(c["green"], 0.2), W(c) * 1.1)
    P(c, "M8.5 17.5 L12 22 L15.5 17.5 Z", grad(c, "green"), k, W(c) * 0.7)


@reg("act-go-junction")
def _(c, k):
    S(c, "M3 12 H12 L19 5 M12 12 L19 19", k)
    P(c, "M12 9 A3 3 0 1 1 11.99 9 Z", c["orange"], k)


def _merge_cells(kind):
    def g(c, k):
        P(c, "M3 4 H21 V20 H3 Z", "#ffffff", k)
        gy = c.lighten(c["grey"], 0.3)
        if kind == "all":
            c.parts.append(f'<rect x="3.6" y="4.6" width="16.8" height="7.4" fill="{c.lighten(c["blue"], 0.4)}"/>')
            S(c, "M3 12 H21 M9 12 V20 M15 12 V20", k, W(c) * 0.7)
        elif kind == "h":
            S(c, "M3 12 H21", gy, W(c) * 0.6)
            S(c, "M12 4 V20", gy, W(c) * 0.6)
            S(c, "M5 12 H10 M8 10 L10 12 L8 14 M19 12 H14 M16 10 L14 12 L16 14", c["blue"])
        elif kind == "v":
            S(c, "M3 12 H21 M12 4 V20", gy, W(c) * 0.6)
            S(c, "M12 5.5 V10 M10 8 L12 10 L14 8 M12 18.5 V14 M10 16 L12 14 L14 16", c["blue"])
    return g


for _mc in ("all", "h", "v"):
    reg(f"act-go-mergecell-{_mc}")(_merge_cells(_mc))


@reg("act-go-warning")
def _(c, k):
    P(c, "M12 2.5 L22 20.5 H2 Z", grad(c, "yellow", 0.3), k)
    S(c, "M12 9 V14.5", k, W(c) * 1.3)
    D(c, 12, 17.5, 1.4, k)


def _staff(c):
    S(c, "M2 8 H22 M2 12 H22 M2 16 H22", c["grey"], W(c) * 0.5)


def head(c, x, y, k, col=None):
    P(c, f"M{x + 2.2} {y} A2.2 1.7 0 1 1 {x - 2.2} {y} A2.2 1.7 0 1 1 {x + 2.2} {y} Z", col or k, k, W(c) * 0.5)


def _minuet(kind):
    def g(c, k):
        _staff(c)
        if kind == "chords":
            for y in (8, 12, 16):
                head(c, 11, y, k)
            S(c, "M13.2 16 V2.5", k)
        elif kind == "intervals":
            head(c, 7, 16, k); head(c, 17, 8, k)
            S(c, "M9.2 16 V5 M19.2 8 V-1", k)
            S(c, "M7 20.5 H17", c["orange"], W(c) * 0.8)
        elif kind == "rhythms":
            head(c, 6, 16, k); head(c, 13, 16, k); head(c, 19, 12, k)
            S(c, "M8.2 16 V5 M15.2 16 V5 M21.2 12 V2", k)
            S(c, "M8.2 5 H15.2", k, W(c) * 1.6)
        elif kind == "scales":
            for i, y in enumerate((18, 15, 12, 9, 6)):
                head(c, 4 + i * 4, y, k, c["blue"] if i in (0, 4) else None)
    return g


for _mi in ("chords", "intervals", "rhythms", "scales"):
    reg(f"act-go-minuet-{_mi}")(_minuet(_mi))


@reg("act-go-motion")
def _(c, k):
    DS(c, "M5 18 C3 9 12 4 15 11 C17 16 20 13 20 7", c["blue"], W(c) * 0.8, "1.6 1.4")
    S(c, "M18 9 L20 6.5 L22 9", c["blue"], W(c) * 0.8)
    P(c, "M5 14.5 A3.5 3.5 0 1 1 4.99 14.5 Z", grad(c, "orange", 0.3), k)


@reg("act-go-multiple")
def _(c, k):
    for d in (0, 4, 8):
        P(c, f"M{11 - d} {3 + d} h10 v10 h-10 Z", grad(c, "blue", 0.6 - d * 0.04), k, W(c) * 0.8)


def _mode(n):
    def g(c, k):
        P(c, "M3 3 H21 V21 H3 Z", grad(c, "blue", 0.6), k)
        TX(c, 12, 17.5, str(n), 14, k)
    return g


for _i in range(1, 6):
    reg(f"act-go-mode{_i}")(_mode(_i))


@reg("act-go-plugs")
def _(c, k):
    P(c, "M3 9 H9 V15 H3 Z", grad(c, "grey", 0.4), k)
    S(c, "M9 10.5 H12 M9 13.5 H12", k)
    P(c, "M14 8 H21 V16 H14 Z", grad(c, "grey", 0.4), k)


@reg("act-go-newline")
def _(c, k):
    S(c, "M3 5 H20 M3 9 H14", k, W(c) * 0.8)
    S(c, "M20 9 V15 H6 M9 12 L6 15 L9 18", c["blue"])


@reg("act-go-news")
def _(c, k):
    P(c, "M4 4 H20 V20 H6 A2 2 0 0 1 4 18 Z", c.grad(c["page"]), k)
    c.parts.append(f'<rect x="7" y="7" width="10" height="3" fill="{c["ink"]}"/>')
    S(c, "M7 13 H11 M7 16 H11", k, W(c) * 0.7)
    P(c, "M13 12.5 H17 V17 H13 Z", c.lighten(c["blue"], 0.3), k, W(c) * 0.5)


@reg("act-go-root")
def _(c, k):
    S(c, "M2.5 13 L5 12 L8 20 L12 4 H21.5", k)
    TX(c, 6, 9.5, "n", 7, c["blue"], italic=True)
    S(c, "M14 9 L19 16 M19 9 L14 16", c["blue"], W(c) * 0.9)


@reg("act-go-vdots")
def _(c, k):
    for y in (5, 12, 19):
        P(c, f"M12 {y - 2.2} A2.2 2.2 0 1 1 11.99 {y - 2.2} Z", k, k, W(c) * 0.3)


@reg("act-go-vdots-left")
def _(c, k):
    for y in (5, 12, 19):
        P(c, f"M16 {y - 2.2} A2.2 2.2 0 1 1 15.99 {y - 2.2} Z", k, k, W(c) * 0.3)
    S(c, "M9 7 L4 12 L9 17", c["blue"])


@reg("act-go-vdots-right")
def _(c, k): mirror(c, lambda cv: GLYPHS["act-go-vdots-left"](cv, k))


@reg("act-go-lens")
def _(c, k):
    P(c, "M12 3 A9 9 0 1 1 11.99 3 Z", c.grad(c["metal"]), k)
    P(c, "M12 7 A5 5 0 1 1 11.99 7 Z", c.grad(c["screen"]), k)
    P(c, "M9.5 9.5 A1.5 1.5 0 1 1 9.49 9.5 Z", "#ffffff", "none")


@reg("act-go-distort")
def _(c, k):
    S(c, "M4 4 Q12 1 20 4 Q23 12 20 20 Q12 23 4 20 Q1 12 4 4 Z", k)
    S(c, "M12 2.5 V21.5 M2.5 12 H21.5 M8 3 Q6 12 8 21 M16 3 Q18 12 16 21 M3 8 Q12 6 21 8 M3 16 Q12 18 21 16",
      c["blue"], W(c) * 0.5)


@reg("act-go-license")
def _(c, k):
    P(c, "M3 4 H21 V17 H3 Z", c.grad(c["page"]), k)
    S(c, "M6 8 H14 M6 11 H12", k, W(c) * 0.7)
    P(c, "M14.5 17 L13.5 22 L16 20.5 L18.5 22 L17.5 17", c["red"], k, W(c) * 0.6)
    P(c, "M16 10.5 A3.5 3.5 0 1 1 15.99 10.5 Z", grad(c, "yellow", 0.2), k, W(c) * 0.7)


@reg("act-go-lighttable")
def _(c, k):
    P(c, "M2 5 H22 V19 H2 Z", grad(c, "yellow", 0.65), k)
    for x in (4.5, 9.5, 14.5):
        P(c, f"M{x} 8 h4.5 v3.5 h-4.5 Z", c.grad(c["screen"]), k, W(c) * 0.5)
        P(c, f"M{x} 13 h4.5 v3.5 h-4.5 Z", grad(c, "green", 0.3), k, W(c) * 0.5)


@reg("act-go-linear")
def _(c, k):
    g = c.grad("#ffffff", c["blue"], horizontal=True)
    P(c, "M3 5 H21 V19 H3 Z", g, k)
    S(c, "M5 12 H19", k, W(c) * 0.7)
    D(c, 5, 12, 1.8, k)
    P(c, "M19 10 A2 2 0 1 1 18.99 10 Z", "#ffffff", k, W(c) * 0.6)


@reg("act-go-connector")
def _(c, k):
    P(c, "M2.5 3 H10 V9 H2.5 Z", grad(c, "blue", 0.5), k)
    P(c, "M14 15 H21.5 V21 H14 Z", grad(c, "green", 0.5), k)
    S(c, "M6.25 9 V18 H14", k)
    D(c, 6.25, 18, 1.4, k)


def _mask(kind):
    def g(c, k):
        if kind == "alpha":
            P(c, "M3 3 H21 V21 H3 Z", "#ffffff", "none")
            for i in range(4):
                for j in range(4):
                    if (i + j) % 2:
                        c.parts.append(f'<rect x="{3 + i * 4.5}" y="{3 + j * 4.5}" width="4.5" height="4.5" fill="{c.lighten(c["grey"], 0.4)}"/>')
            P(c, "M12 6 A6 6 0 1 1 11.99 6 Z", c.grad(c.lighten(c["blue"], 0.2), c["blue"]), k, W(c) * 0.7)
        elif kind == "invert":
            P(c, "M3 3 H12 V21 H3 Z", "#ffffff", "none")
            P(c, "M12 3 H21 V21 H12 Z", c["ink"], "none")
            P(c, "M12 7 A5 5 0 0 0 12 17 Z", c["ink"], "none")
            P(c, "M12 7 A5 5 0 0 1 12 17 Z", "#ffffff", "none")
        elif kind == "luma":
            P(c, "M3 3 H21 V21 H3 Z", c.grad("#000000", "#ffffff", horizontal=True), "none")
            P(c, "M12 7 A5 5 0 1 1 11.99 7 Z", "none", c["yellow"], W(c) * 0.8)
        P(c, "M3 3 H21 V21 H3 Z", "none", k)
    return g


for _mk in ("alpha", "invert", "luma"):
    reg(f"act-go-mask-{_mk}")(_mask(_mk))


def _map(kind):
    def g(c, k):
        gl = c.lighten(c["blue"], 0.55)
        w = W(c) * 0.55
        if kind == "flat":
            P(c, "M2 5 H22 V19 H2 Z", gl, k)
            S(c, "M2 8.5 H22 M2 12 H22 M2 15.5 H22 M7 5 V19 M12 5 V19 M17 5 V19", c["blue"], w)
        elif kind == "mercator":
            P(c, "M3 2 H21 V22 H3 Z", gl, k)
            S(c, "M3 12 H21 M3 9.5 H21 M3 14.5 H21 M3 6 H21 M3 18 H21 M7.5 2 V22 M12 2 V22 M16.5 2 V22", c["blue"], w)
        elif kind == "globe":
            P(c, "M12 3 A9 9 0 1 1 11.99 3 Z", gl, k)
            S(c, "M12 3 C7 7 7 17 12 21 C17 17 17 7 12 3 M3.5 9 H20.5 M3.5 15 H20.5 M3 12 H21",
              c["blue"], w)
        elif kind == "gnomonic":
            P(c, "M3 3 H21 V21 H3 Z", gl, k)
            S(c, "M12 12 L3 3 M12 12 L21 3 M12 12 L3 21 M12 12 L21 21 M12 3 V21 M3 12 H21", c["blue"], w)
            S(c, "M12 12 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0", c["blue"], w)
        P(c, "M12 10 A2 2 0 1 1 11.99 10 Z", c["green"], "none")
    return g


for _mp in ("flat", "mercator", "globe", "gnomonic"):
    reg(f"act-go-map-{_mp}")(_map(_mp))


@reg("act-go-telescope")
def _(c, k):
    P(c, "M3 12 L17 4 L19.5 8.5 L5.5 16.5 Z", c.grad(c["metal"]), k)
    S(c, "M11 12.5 L7 21 M11 12.5 L15 21", k)


@reg("act-go-chunks")
def _(c, k):
    for i in range(4):
        for j in range(4):
            col = c["green"] if (i * 3 + j * 5) % 7 < 4 else "#ffffff"
            P(c, f"M{3 + i * 4.6} {3 + j * 4.6} h3.8 v3.8 h-3.8 Z", col, k, W(c) * 0.5)


@reg("act-go-combine")
def _(c, k):
    P(c, "M2 2.5 H8 V10 H2 Z M2 13.5 H8 V21 H2 Z", c.grad(c["page"]), k, W(c) * 0.8)
    S(c, "M8 6 C11 6 11 12 13 12 M8 17.5 C11 17.5 11 12 13 12", c["blue"], W(c) * 0.9)
    P(c, "M14 6 H22 V18 H14 Z", c.grad(c["page"]), k)


@reg("act-go-folders2")
def _(c, k):
    for x in (1.5, 12.5):
        P(c, f"M{x} 7 h4 l1.5 1.5 h4.5 v10 h-10 Z", c.grad(c["folder"]), k, W(c) * 0.8)


@reg("act-go-panes")
def _(c, k):
    P(c, "M2 4 H11 V20 H2 Z M13 4 H22 V20 H13 Z", "#ffffff", k)
    c.parts.append(f'<rect x="2.5" y="4.5" width="8" height="3" fill="{c.lighten(c["blue"], 0.3)}"/>')
    c.parts.append(f'<rect x="13.5" y="4.5" width="8" height="3" fill="{c.lighten(c["blue"], 0.3)}"/>')


@reg("act-go-cloud")
def _(c, k):
    P(c, "M6.5 18 A4 4 0 0 1 6 10 A5.5 5.5 0 0 1 16.5 8 A4.5 4.5 0 0 1 18 18 Z", grad(c, "blue", 0.6), k)


@reg("act-go-tex2html")
def _(c, k):
    _page(c, k)
    TX(c, 12, 12.5, "L", 8, k)
    S(c, "M8 16 L10 14 L8 18 M16 14 L18 16 L16 18", c["blue"], W(c) * 0.8)
    TX(c, 13, 18.5, "/", 6, c["blue"])


@reg("act-go-bucket")
def _(c, k):
    P(c, "M5 10 L12 3 L19 10 L12 17 Z", c.grad(c["metal"]), k)
    P(c, "M19 10 C21 13 21.5 15 20 16.5 C18.5 17 17.5 15.5 19 10 Z", c["orange"], k, W(c) * 0.6)
    P(c, "M2 19.5 H22 V22 H2 Z", c["orange"], k, W(c) * 0.6)


@reg("act-go-cover")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", grad(c, "violet", 0.35), k)
    P(c, "M12 7 A5 5 0 1 1 11.99 7 Z", c.grad(c["metal"]), k, W(c) * 0.7)
    D(c, 12, 12, 1.3, k)


@reg("act-go-wand")
def _(c, k):
    S(c, "M3 21 L15 9", k, W(c) * 2.2)
    S(c, "M3 21 L15 9", c.lighten(c["violet"], 0.2), W(c) * 1.0)
    star(c, 17.5, 6.5, 5, c["yellow"])


@reg("act-go-sel-minus")
def _(c, k):
    DS(c, "M3 3 H21 V21 H3 Z", k, None, "2.5 2")


@reg("act-go-oilpaint")
def _(c, k):
    P(c, "M3 13 C3 6 8 3 13 3 C19 3 21 7 21 10 C21 13 17 12 16 14 C15 16.5 17 19 14 20.5 C9 22 3 19 3 13 Z",
      c.lighten(c["brown"], 0.4), k)
    for x, y, col in ((8, 9, "red"), (13, 7, "yellow"), (7.5, 15, "blue"), (12, 16.5, "green")):
        D(c, x, y, 1.8, c[col])


@reg("act-go-overexpose")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", "#ffffff", k)
    P(c, "M3 15 L9 9 L14 14 L17 11 L21 15 V21 H3 Z", c.lighten(c["grey"], 0.5), "none")
    P(c, "M15 4.5 A3 3 0 1 1 14.99 4.5 Z", c["yellow"], "none")
    S(c, "M15 1.5 V2.5 M19.5 7.5 H21 M18 4 L19 3", c["yellow"], W(c) * 0.7)
    P(c, "M3 3 H21 V21 H3 Z", "none", k)


@reg("act-go-noise")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", c.lighten(c["grey"], 0.55), k)
    for x, y in ((6, 6), (10, 8), (15, 5), (18, 9), (7, 12), (13, 13), (17, 15), (5, 18), (10, 17), (15, 19)):
        D(c, x, y, 1, k)


@reg("act-go-phrase")
def _(c, k):
    P(c, "M2 5 H22 V16 H10 L5 20 V16 H2 Z", grad(c, "cyan", 0.55), k)
    S(c, "M5.5 9 H18 M5.5 12.5 H14", k, W(c) * 0.7)


@reg("act-go-graduation")
def _(c, k):
    P(c, "M12 4 L22 9 L12 14 L2 9 Z", grad(c, "blue", 0.2), k)
    S(c, "M6 11.5 V16 C9 19 15 19 18 16 V11.5 M20 10 V16", k)


@reg("act-go-trophy")
def _(c, k):
    P(c, "M7 3 H17 V9 A5 5 0 0 1 7 9 Z", grad(c, "yellow", 0.2), k)
    S(c, "M7 5 H4 C4 10 7 10 7 10 M17 5 H20 C20 10 17 10 17 10 M12 14 V18", k)
    P(c, "M8 18 H16 V21 H8 Z", c["brown"], k)


@reg("act-go-medal")
def _(c, k):
    P(c, "M7 2 L10 9 H14 L17 2 H13.5 L12 6 L10.5 2 Z", grad(c, "red"), k, W(c) * 0.7)
    P(c, "M12 9 A6 6 0 1 1 11.99 9 Z", grad(c, "yellow", 0.2), k)
    star(c, 12, 15, 3, c["orange"])


@reg("act-go-lamp")
def _(c, k):
    P(c, "M12 2.5 A6.5 6.5 0 0 1 16 14 V16.5 H8 V14 A6.5 6.5 0 0 1 12 2.5 Z", grad(c, "yellow", 0.4), k)
    S(c, "M9 19 H15 M10 21.5 H14", k)


@reg("act-go-puzzle")
def _(c, k):
    P(c, "M4 7 H9 A2.5 2.5 0 1 1 14 7 H19 V12 A2.5 2.5 0 1 1 19 17 V21 H4 Z", grad(c, "green", 0.4), k)


@reg("act-go-pad")
def _(c, k):
    P(c, "M6 7 H18 A4.5 4.5 0 0 1 18 17 H6 A4.5 4.5 0 0 1 6 7 Z", c.grad(c["case"]), k)
    S(c, "M5 12 H9 M7 10 V14", k)
    D(c, 16, 10.5, 1.3, c["red"]); D(c, 18.5, 13, 1.3, c["blue"])


@reg("act-go-keyboard")
def _(c, k):
    P(c, "M2 6 H22 V18 H2 Z", c.grad(c["case"]), k)
    S(c, "M5 9.5 H6 M8.5 9.5 H9.5 M12 9.5 H13 M15.5 9.5 H16.5 M19 9.5 H19.5 M7 15 H17", k, W(c) * 0.9)
    S(c, "M5 12.25 H6 M8.5 12.25 H9.5 M12 12.25 H13 M15.5 12.25 H19", k, W(c) * 0.9)


@reg("act-go-headphones")
def _(c, k):
    S(c, "M4 15 V12 A8 8 0 0 1 20 12 V15", k, W(c) * 1.2)
    P(c, "M3 14 H7.5 V21 H3 Z M16.5 14 H21 V21 H16.5 Z", grad(c, "blue", 0.3), k)


@reg("act-go-bank")
def _(c, k):
    P(c, "M2.5 8.5 L12 3 L21.5 8.5 Z", grad(c, "grey", 0.4), k)
    S(c, "M5.5 10.5 V17 M10 10.5 V17 M14 10.5 V17 M18.5 10.5 V17", k, W(c) * 1.2)
    P(c, "M2.5 18 H21.5 V21 H2.5 Z", grad(c, "grey", 0.4), k)


@reg("act-go-flag")
def _(c, k):
    S(c, "M5 21.5 V3", k, W(c) * 1.2)
    P(c, "M5 3.5 H19 L16 8 L19 12.5 H5 Z", grad(c, "green", 0.3), k)


@reg("act-go-heart")
def _(c, k):
    P(c, "M12 20.5 C4 15 2.5 11 2.5 8 A4.75 4.75 0 0 1 12 6.5 A4.75 4.75 0 0 1 21.5 8 C21.5 11 20 15 12 20.5 Z",
      grad(c, "red", 0.35), k)


@reg("act-go-globe")
def _(c, k):
    P(c, "M12 3 A9 9 0 1 1 11.99 3 Z", grad(c, "cyan", 0.45), k)
    S(c, "M12 3 C8 7 8 17 12 21 C16 17 16 7 12 3 M3.5 9 H20.5 M3.5 15 H20.5", k, W(c) * 0.7)


@reg("act-go-measure")
def _(c, k):
    P(c, "M2 8 H22 V16 H2 Z", grad(c, "yellow", 0.35), k)
    S(c, "M5 8 V12 M8 8 V11 M11 8 V12 M14 8 V11 M17 8 V12 M20 8 V11", k, W(c) * 0.6)


@reg("act-go-money")
def _(c, k):
    P(c, "M2 6 H22 V18 H2 Z", grad(c, "green", 0.5), k)
    O(c, 12, 12, 3.2, k)
    S(c, "M5 9 V15 M19 9 V15", k, W(c) * 0.6)


@reg("act-go-percent")
def _(c, k):
    S(c, "M18 5 L6 19", k, W(c) * 1.2)
    P(c, "M7 4 A3 3 0 1 1 6.99 4 Z", c["blue"], k, W(c) * 0.7)
    P(c, "M17 14 A3 3 0 1 1 16.99 14 Z", c["blue"], k, W(c) * 0.7)


@reg("act-go-sigma")
def _(c, k): P(c, "M18 6.5 V3.5 H5.5 L12 12 L5.5 20.5 H18 V17.5", "none", c["green"], W(c) * 1.4)


@reg("act-go-font")
def _(c, k):
    S(c, "M3 20 L9 4 L15 20 M5.5 14 H12.5", k, W(c) * 1.2)
    S(c, "M15.5 13 A3 3 0 1 1 15.49 13 M18.5 11 V17.5", c["blue"])


@reg("act-go-lock")
def _(c, k):
    S(c, "M8 10 V7 A4 4 0 0 1 16 7 V10", k, W(c) * 1.2)
    P(c, "M5 10 H19 V21 H5 Z", grad(c, "orange", 0.3), k)
    D(c, 12, 15, 1.6, k)


@reg("act-go-unlock")
def _(c, k):
    S(c, "M8 10 V7 A4 4 0 0 1 16 6", k, W(c) * 1.2)
    P(c, "M5 10 H19 V21 H5 Z", grad(c, "green", 0.3), k)
    D(c, 12, 15, 1.6, k)


@reg("act-go-filter")
def _(c, k): P(c, "M3 4 H21 L14 12.5 V20 L10 18 V12.5 Z", grad(c, "blue", 0.5), k)


@reg("act-go-feed")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", grad(c, "orange", 0.2), k)
    S(c, "M7 10 A7 7 0 0 1 14 17 M7 6 A11 11 0 0 1 18 17", "#ffffff", W(c) * 1.1)
    D(c, 8, 16, 1.7, "#ffffff")


@reg("act-go-magnet")
def _(c, k):
    P(c, "M4 3 H10 V12 A2 2 0 0 0 14 12 V3 H20 V12 A8 8 0 0 1 4 12 Z", grad(c, "red", 0.3), k)
    P(c, "M4 3 H10 V7 H4 Z M14 3 H20 V7 H14 Z", c.lighten(c["grey"], 0.5), k)


@reg("act-go-list")
def _(c, k):
    P(c, "M3 3 H21 V21 H3 Z", c.grad(c["page"]), k)
    S(c, "M6 8 H18 M6 12 H18 M6 16 H14", k, W(c) * 0.8)


@reg("act-go-calendar")
def _(c, k):
    P(c, "M3 5 H21 V21 H3 Z", "#ffffff", k)
    P(c, "M3 5 H21 V9.5 H3 Z", c["red"], k)
    S(c, "M8 3 V7 M16 3 V7", k)
    for x in (7, 12, 17):
        D(c, x, 13.5, 1.1, k); D(c, x, 17.5, 1.1, k)


@reg("act-go-alarm")
def _(c, k):
    P(c, "M12 5 A8 8 0 1 1 11.99 5 Z", "#ffffff", k)
    S(c, "M12 8.5 V13 L15 15 M3.5 6 L6.5 3 M20.5 6 L17.5 3", k)


@reg("act-go-table")
def _(c, k):
    P(c, "M3 4 H21 V20 H3 Z", "#ffffff", k)
    c.parts.append(f'<rect x="3.6" y="4.6" width="16.8" height="4" fill="{c.lighten(c["green"], 0.3)}"/>')
    S(c, "M3 9 H21 M3 14.5 H21 M9 4 V20 M15 4 V20", k, W(c) * 0.7)


@reg("act-go-picture")
def _(c, k):
    P(c, "M3 4 H21 V20 H3 Z", c.grad(c["screen"]), k)
    P(c, "M3 18 L9 11 L13 15 L16 12 L21 17 V20 H3 Z", grad(c, "green", 0.2), "none")
    D(c, 16, 8, 1.8, c["yellow"])
    P(c, "M3 4 H21 V20 H3 Z", "none", k)


@reg("act-go-film")
def _(c, k):
    P(c, "M3 4 H21 V20 H3 Z", c.grad(c.lighten(c["ink"], 0.25), c["ink"]), k)
    P(c, "M7 6.5 H17 V17.5 H7 Z", c.grad(c["screen"]), k, W(c) * 0.5)
    for y in (6.5, 10.5, 14.5):
        c.parts.append(f'<rect x="4" y="{y}" width="1.8" height="2" fill="#ffffff"/>')
        c.parts.append(f'<rect x="18.2" y="{y}" width="1.8" height="2" fill="#ffffff"/>')


@reg("act-go-link")
def _(c, k):
    S(c, "M10 14 L14 10", k, W(c) * 1.1)
    S(c, "M11 7.5 L13.5 5 A3.5 3.5 0 0 1 19 10.5 L16.5 13 M13 16.5 L10.5 19 A3.5 3.5 0 0 1 5 13.5 L7.5 11", k, W(c) * 2.4)
    S(c, "M11 7.5 L13.5 5 A3.5 3.5 0 0 1 19 10.5 L16.5 13 M13 16.5 L10.5 19 A3.5 3.5 0 0 1 5 13.5 L7.5 11",
      c.lighten(c["blue"], 0.25), W(c) * 1.0)


@reg("act-go-sun")
def _(c, k):
    P(c, "M12 7 A5 5 0 1 1 11.99 7 Z", grad(c, "yellow", 0.3), k)
    S(c, "M12 2 V4 M12 20 V22 M2 12 H4 M20 12 H22 M5 5 L6.5 6.5 M17.5 17.5 L19 19 M19 5 L17.5 6.5 M5 19 L6.5 17.5", k)


@reg("act-go-plane")
def _(c, k): P(c, "M2.5 11 L21.5 3 L15 21 L11 13.5 Z", c.grad(c["page"]), k); S(c, "M11 13.5 L21.5 3", k, W(c) * 0.7)


@reg("act-go-chip-gear")
def _(c, k):
    G(c, "gear", 2, 2, 20, k)


# ---- coins (help-donate-*) ----------------------------------------------------------
CURRENCY = {"brl": "R$", "chf": "Fr", "eur": "€", "gbp": "£", "inr": "₹", "jpy": "¥", "pln": "zł",
            "rub": "₽", "sek": "kr", "try": "₺", "uah": "₴", "usd": "$"}


def donate(sym):
    def f(c):
        c.circle(22, 22, 16, c.grad(c.lighten(c["yellow"], 0.3), c.darken(c["yellow"], 0.15)))
        c.circle(22, 22, 12.5, "none", stroke=c.darken(c["yellow"], 0.35), width=1)
        TX(c, 22, 29 if len(sym) == 1 else 27.5, sym, 20 if len(sym) == 1 else 14, c["ink"])
        badge_glyph(c, "heart", "red")
        return True
    return f


def zoom(n):
    def f(c):
        c.circle(21, 21, 9, c.lighten(c["blue"], 0.6), stroke=None)
        action(c, "magnifier")
        TX(c, 21, 25, f"{n}×", 11, c["ink"])
        return True
    return f


def text_icon(s, size=22, col="ink", b=None, bc="green"):
    def f(c):
        TX(c, 22, 31, s, size, c[col])
        if b:
            badge_glyph(c, b, bc)
        return True
    return f


def im(word, col):
    reg(f"act-go-im-{word}")(_im(word, col))
    return a(f"act-go-im-{word}")


# ---- the table ----------------------------------------------------------------
T = {
    # games
    "games-achievements": a("act-go-trophy", "check"),
    "games-config-board": a("act-go-board", "gear", "blue"),
    "games-config-tiles": a("act-go-tiles", "gear", "blue"),
    "games-difficult": a("act-go-pad", "exclamation", "red"),
    "games-highscores": a("act-go-medal", "star", "orange"),
    "games-hint": a("act-go-lamp"),
    "games-solve": a("act-go-puzzle", "check"),
    "generalise": a("act-go-generalise"),
    "globe": a("act-go-globe"),
    # gnumeric
    "gnumeric-autofilter-delete": a("act-go-filter", "cross", "red"),
    "gnumeric-autosum": a("act-go-sigma"),
    "gnumeric-bucket": a("act-go-bucket"),
    "gnumeric-component-insert-shaped": a("shapes", "plus", "green", acc="blue", halo=True),
    "gnumeric-data-slicer": a("act-go-slicer"),
    "gnumeric-font": a("act-go-font"),
    "gnumeric-format-accounting": a("act-go-money"),
    "gnumeric-format-percentage": a("act-go-percent"),
    "gnumeric-format-precision-decrease": a("act-go-prec-down"),
    "gnumeric-format-precision-increase": a("act-go-prec-up"),
    "gnumeric-format-thousand-separator": a("act-go-thousands"),
    "gnumeric-format-halign-distributed": a("act-go-valign-hdist"),
    "gnumeric-format-valign-bottom": a("act-go-valign-bottom"),
    "gnumeric-format-valign-center": a("act-go-valign-center"),
    "gnumeric-format-valign-distributed": a("act-go-valign-distributed"),
    "gnumeric-format-valign-justify": a("act-go-valign-justify"),
    "gnumeric-format-valign-top": a("act-go-valign-top"),
    "gnumeric-formulaguru": a("act-go-fx"),
    "gnumeric-link-external": a("act-go-link", "export", "orange"),
    "gnumeric-link-internal": a("act-go-link", "table", "green"),
    "gnumeric-link-url": a("act-go-link", "globe", "cyan"),
    "gnumeric-object-arrow": a("act-go-obj-arrow"),
    "gnumeric-object-button": a("act-go-button"),
    "gnumeric-object-checkbox": a("act-go-checkbox"),
    "gnumeric-object-combo": a("act-go-combo"),
    "gnumeric-object-ellipse": a("act-go-obj-ellipse"),
    "gnumeric-object-list": a("act-go-listbox"),
    "gnumeric-object-rectangle": a("act-go-obj-rect"),
    "gnumeric-object-scrollbar": a("act-go-scrollbar"),
    "gnumeric-object-spinbutton": a("act-go-spin"),
    "gnumeric-pagesetup-hf-page": a("act-go-hf"),
    "gnumeric-pagesetup-hf-pages": a("act-go-hf-n"),
    "gnumeric-pivottable": a("act-go-pivot"),
    "gnumeric-protection-no": a("act-go-unlock"),
    "gnumeric-protection-yes": a("act-go-lock"),
    # go
    "go-up": a("act-go-up-up"),
    "go-down": a("act-go-up-down"),
    "go-next": a("act-go-up-right"),
    "go-previous": a("act-go-up-left"),
    "go-top": a("act-go-top-up"),
    "go-bottom": a("act-go-top-down"),
    "go-last": a("act-go-top-right"),
    "go-first": a("act-go-top-left"),
    "go-up-skip": a("act-go-skip-up"),
    "go-down-skip": a("act-go-skip-down"),
    "go-next-skip": a("act-go-skip-right"),
    "go-previous-skip": a("act-go-skip-left"),
    "go-next-context": a("act-go-up-right", "lines", "orange"),
    "go-previous-context": a("act-go-up-left", "lines", "orange"),
    "go-next-use": a("act-go-up-right", "target", "violet"),
    "go-previous-use": a("act-go-up-left", "target", "violet"),
    "go-home": a("act-go-house"),
    "go-jump": a("act-go-jump"),
    "go-jump-declaration": a("act-go-jump", "tag", "orange"),
    "go-jump-definition": a("act-go-jump", "code", "violet"),
    "go-parent-folder": a("folder", "arrow-up", "blue", acc="blue", halo=True),
    "grid-axonometric": a("act-go-axonometric"),
    "gtk-index": a("list-number", None, acc="blue", halo=True),
    "gtk-select-font": a("act-go-font", "cursor", "blue"),
    # h
    "handle-move": a("move", None, acc="blue", halo=True),
    "handle-sort": a("act-go-grip"),
    "headphones": a("act-go-headphones"),
    "help-about": a("info", None, acc="blue", halo=True),
    "help-contents": a("act-go-book", "question", "blue"),
    "help-keybord-shortcuts": a("act-go-keyboard", "question", "blue"),
    "help-whatsthis": a("pointer", "question", "blue"),
    "hexagon-shape": a("act-go-hexagon"),
    "home": a("act-go-home"),
    "hotpixels": a("act-go-hotpixels"),
    # im
    "im-aim": im("AIM", "yellow"),
    "im-icq": im("ICQ", "green"),
    "im-identi.ca": im("id", "cyan"),
    "im-mastodon": im("M", "violet"),
    "im-matrix": im("[m]", "grey"),
    "im-msn": im("MSN", "blue"),
    "im-yahoo": im("Y!", "red"),
    "im-user": a("act-go-user"),
    "im-user-away": a("act-go-user", "clock", "orange"),
    "im-user-busy": a("act-go-user", "minus", "red"),
    "im-user-offline": a("act-go-user", "cross", "grey"),
    "im-user-online": a("act-go-user", "check", "green"),
    "im-invisible-user": a("act-go-user-dashed"),
    "im-kick-user": a("act-go-user", "exit", "orange"),
    "im-ban-kick-user": a("act-go-user", "forbidden", "red"),
    # input
    "input-keyboard-virtual-hide": a("act-go-keyboard", "chevron-down", "blue"),
    "input-keyboard-virtual-show": a("act-go-keyboard", "chevron-up", "blue"),
    "input-mouse-click-left": a("act-go-mouse-left"),
    "input-mouse-click-middle": a("act-go-mouse-middle"),
    "input-mouse-click-right": a("act-go-mouse-right"),
    # insert
    "insert-button": a("act-go-button", "plus"),
    "insert-endnote": a("act-go-endnote", "plus"),
    "insert-footnote": a("act-go-footnote", "plus"),
    "insert-horizontal-rule": a("act-go-hrule", "plus"),
    "insert-image": a("act-go-picture", "plus"),
    "insert-link": a("act-go-link", "plus"),
    "insert-math-expression": a("pi", "plus", acc="blue", halo=True),
    "insert-more-mark": a("act-go-moremark", "plus"),
    "insert-page-break": a("act-go-pagebreak", "plus"),
    "insert-table": a("act-go-table", "plus"),
    "insert-table-of-contents": a("list-number", "plus", acc="blue", halo=True),
    "insert-text": a("text", "plus", acc="blue", halo=True),
    "insert-text-frame": a("act-go-textframe", "plus"),
    "insertcellcopy": a("act-go-table", "copy", "blue"),
    "institution": a("act-go-bank"),
    # irc
    "irc-channel-active": a("act-go-hash", "check", "green"),
    "irc-channel-inactive": a("act-go-hash", "zzz", "grey"),
    "irc-operator": a("act-go-user", "at", "blue"),
    "irc-remove-operator": a("act-go-user", "at", "red"),
    "irc-voice": a("act-go-megaphone", "plus"),
    "irc-unvoice": a("act-go-megaphone", "minus", "red"),
    "item": a("act-go-item"),
    "join": a("act-go-join"),
    "journal-new": a("act-go-notebook", "plus"),
    "junction": a("act-go-junction"),
    # kdenlive
    "kdenlive-add-clip": a("act-go-film", "plus"),
    "kdenlive-add-color-clip": a("act-go-colorclip", "plus"),
    "kdenlive-custom-effect": a("act-go-wand", "gear", "violet"),
    "kdenlive-hide-video": a("act-go-film", "eye-off", "grey"),
    "kdenlive-insert-rect": a("act-go-sel-minus", "plus", "violet"),
    "kdenlive-insert-unicode": text_icon("Ω", 26, "ink", "plus", "violet"),
    "kdenlive-ripple": a("act-go-tl-ripple"),
    "kdenlive-rolling": a("act-go-tl-rolling"),
    "kdenlive-slide": a("act-go-tl-slide"),
    "kdenlive-slip": a("act-go-tl-slip"),
    "kdenlive-show-markers": a("act-go-tl-markers"),
    "kdenlive-split-audio": a("act-go-tl-split"),
    "kdenlive-select-images": a("act-go-picture", "check", "violet"),
    "kdenlive-select-texts": a("text", "check", "violet", acc="violet", halo=True),
    "kdenlive-track_has_effect": a("act-go-film", "star", "violet"),
    "key-enter": a("enter-key", None, acc="blue", halo=True),
    # keyframes
    "keyframe": a("act-go-diamond"),
    "keyframe-add": a("act-go-diamond", "plus"),
    "keyframe-disable": a("act-go-diamond", "forbidden", "grey"),
    "keyframe-duplicate": a("act-go-diamond", "copy", "blue"),
    "keyframe-next": a("act-go-key-next"),
    "keyframe-previous": a("act-go-key-prev"),
    "keyframe-record": a("act-go-diamond", "record", "red"),
    "keyframe-remove": a("act-go-diamond", "minus", "red"),
    "keyframe-warn": a("act-go-diamond", "exclamation", "orange"),
    # kmouth & co
    "kmouth-phrase-new": a("act-go-phrase", "plus"),
    "kmouth-phrasebook": a("act-go-book", "chat", "cyan"),
    "kmouth-phresebook-new": a("act-go-book", "plus"),
    "know": a("act-go-graduation"),
    "kontact-import-wizard": a("import", "wand", "violet", acc="blue", halo=True),
    # krusader
    "kr_combine": a("act-go-combine"),
    "kr_comparedirs": a("act-go-folders2", "equals", "blue"),
    "kr_diskusage": a("harddisk", "chart-pie", "orange", acc="grey", halo=True),
    "kr_mountman": a("harddisk", "gear", "blue", acc="grey", halo=True),
    "kr_syncbrowse_on": a("act-go-panes", "sync", "green"),
    "kr_syncbrowse_off": a("act-go-panes", "cross", "grey"),
    "kr_unselect": a("act-go-sel-minus", "minus", "red"),
    "kruler-east": a("act-go-ruler-east"),
    "kruler-south": a("act-go-ruler-south"),
    "kruler-west": a("act-go-ruler-west"),
    # kstars
    "kstars_cbound": a("act-go-ks-cbound"),
    "kstars_clines": a("act-go-ks-clines"),
    "kstars_cnames": a("act-go-ks-cnames"),
    "kstars_constellationart": a("act-go-ks-art"),
    "kstars_deepsky": a("act-go-ks-deepsky"),
    "kstars_ekos": a("act-go-ks-ekos"),
    "kstars_fitsviewer": a("act-go-ks-fits"),
    "kstars_grid": a("act-go-ks-grid"),
    "kstars_hgrid": a("act-go-ks-hgrid"),
    "kstars_horizon": a("act-go-ks-horizon"),
    "kstars_indi": a("act-go-ks-indi"),
    "kstars_mw": a("act-go-ks-mw"),
    "kstars_satellites": a("act-go-ks-satellites"),
    "kstars_solarsystem": a("act-go-ks-solar"),
    "kstars_stars": a("act-go-ks-stars"),
    "kstars_supernovae": a("act-go-ks-supernovae"),
    "kstars_xplanet": a("act-go-ks-xplanet"),
    # ktorrent
    "kt-add-feeds": a("act-go-feed", "plus"),
    "kt-remove-feeds": a("act-go-feed", "minus", "red"),
    "kt-add-filters": a("act-go-filter", "plus"),
    "kt-remove-filters": a("act-go-filter", "minus", "red"),
    "kt-chunks": a("act-go-chunks"),
    "kt-magnet": a("act-go-magnet"),
    "kt-queue-manager": a("act-go-list", "clock", "blue"),
    "kt-set-max-upload-speed": a("act-go-cloud", "arrow-up", "green"),
    "kt-start-all": a("act-go-play2"),
    "kt-stop-all": a("act-go-stop2"),
    "l2h": a("act-go-tex2html"),
    # labplot
    "labplot-TeX-logo": a("act-go-lp-tex"),
    "labplot-axis-horizontal": a("act-go-lp-axis-h"),
    "labplot-axis-vertical": a("act-go-lp-axis-v"),
    "labplot-editbreaklayout": a("act-go-layout-break", "cross", "red"),
    "labplot-editgrid": a("act-go-layout-grid"),
    "labplot-edithlayout": a("act-go-layout-h"),
    "labplot-editvlayout": a("act-go-layout-v"),
    "labplot-matrix": a("act-go-lp-matrix"),
    "labplot-matrix-new": a("act-go-lp-matrix", "plus"),
    "labplot-plot-axis-points": a("act-go-lp-axis-points"),
    "labplot-shift-down-y": a("act-go-lp-two", "arrow-down", "blue"),
    "labplot-shift-up-y": a("act-go-lp-two", "arrow-up", "blue"),
    "labplot-shift-left-x": a("act-go-lp-two", "arrow-left", "blue"),
    "labplot-shift-right-x": a("act-go-lp-two", "arrow-right", "blue"),
    "labplot-workbook": a("act-go-lp-workbook"),
    "labplot-workbook-new": a("act-go-lp-workbook", "plus"),
    "labplot-worksheet": a("act-go-lp-worksheet"),
    "labplot-worksheet-new": a("act-go-lp-worksheet", "plus"),
    "labplot-xy-curve": a("act-go-lp-curve"),
    "labplot-xy-curve-segments": a("act-go-lp-segments"),
    "labplot-xy-equation-curve": a("act-go-lp-equation"),
    "labplot-xy-fit-curve": a("act-go-lp-fit"),
    "labplot-xy-fourier-filter-curve": a("act-go-lp-ffilter"),
    "labplot-xy-fourier-transform-curve": a("act-go-lp-ftransform"),
    "labplot-xy-interpolation-curve": a("act-go-lp-interp"),
    "labplot-xy-smoothing-curve": a("act-go-lp-smooth"),
    "labplot-xy-plot-four-axes": a("act-go-lp-four"),
    "labplot-xy-plot-two-axes": a("act-go-lp-two"),
    "labplot-xy-plot-two-axes-centered": a("act-go-lp-centered"),
    "labplot-xy-plot-two-axes-centered-origin": a("act-go-lp-origin"),
    # layers
    "layer-bottom": a("act-go-layers", "arrow-bottom", "blue"),
    "layer-top": a("act-go-layers", "arrow-top", "blue"),
    "layer-lower": a("act-go-layers", "arrow-down", "cyan"),
    "layer-raise": a("act-go-layers", "arrow-up", "cyan"),
    "layer-next": a("act-go-layers", "chevron-down", "grey"),
    "layer-previous": a("act-go-layers", "chevron-up", "grey"),
    "layer-new": a("act-go-layers", "plus"),
    "layer-delete": a("act-go-layers", "minus", "red"),
    "layer-duplicate": a("act-go-layers", "copy", "blue"),
    "layer-visible-on": a("act-go-layers", "eye", "green"),
    "layer-visible-off": a("act-go-layers", "eye-off", "grey"),
    "lensautofix": a("act-go-lens", "wand", "violet"),
    "lensdistortion": a("act-go-distort"),
    "license": a("act-go-license"),
    "lighttable": a("act-go-lighttable"),
    "linear": a("act-go-linear"),
    "lines-connector": a("act-go-connector"),
    "link": a("act-go-link"),
    "list-add": a("plus", None, acc="green", halo=True),
    "list-add-font": a("act-go-font", "plus"),
    "list-add-user": a("act-go-users", "plus"),
    "list-remove-user": a("act-go-users", "minus", "red"),
    "love-amarok": a("act-go-heart"),
    # mail
    "mail-attachment": a("act-go-env", "act-go-clip", "grey"),
    "mail-encrypted-part": a("act-go-env", "lock", "orange"),
    "mail-forward": a("act-go-env", "forward", "blue"),
    "mail-forward-custom": a("act-go-env", "forward", "violet"),
    "mail-forwarded-replied": a("act-go-env", "act-go-rf", "blue"),
    "mail-invitation": a("act-go-env", "calendar", "red"),
    "mail-mark-important": a("act-go-env", "exclamation", "red"),
    "mail-mark-junk": a("act-go-env", "trash", "brown"),
    "mail-mark-notjunk": a("act-go-env", "thumb-up", "green"),
    "mail-mark-read": a("act-go-env-open"),
    "mail-mark-task": a("act-go-env", "clipboard-check", "cyan"),
    "mail-mark-unread": a("act-go-env"),
    "mail-mark-unread-new": a("act-go-env-dot", "star", "orange"),
    "mail-meeting-request-reply": a("act-go-calendar", "reply", "blue"),
    "mail-message-new": a("act-go-env", "plus"),
    "mail-message-new-list": a("act-go-env", "users", "green"),
    "mail-queue": a("act-go-env", "clock", "orange"),
    "mail-receive": a("act-go-env", "arrow-down", "green"),
    "mail-send": a("act-go-plane"),
    "mail-reply-sender": a("act-go-reply"),
    "mail-reply-all": a("act-go-reply-all"),
    "mail-reply-author": a("act-go-reply", "user", "blue"),
    "mail-reply-custom": a("act-go-reply", "gear", "violet"),
    "mail-reply-custom-all": a("act-go-reply-all", "gear", "violet"),
    "mail-reply-list": a("act-go-reply", "list", "green"),
    "mail-signature-unknown": a("act-go-env", "question", "grey"),
    "mail-signed-full": a("act-go-env", "check", "green"),
    "mail-signed-part": a("act-go-env", "check", "orange"),
    "mail-signed-verified": a("act-go-env", "shield", "blue"),
    "mail-tagged": a("act-go-env", "tag", "violet"),
    # maps, masks
    "map-flat": a("act-go-map-flat"),
    "map-globe": a("act-go-map-globe"),
    "map-gnomonic": a("act-go-map-gnomonic"),
    "map-mercator": a("act-go-map-mercator"),
    "markasblank": a("act-go-page", "check", "grey"),
    "mask-alpha": a("act-go-mask-alpha"),
    "mask-invert": a("act-go-mask-invert"),
    "mask-luma": a("act-go-mask-luma"),
    "measure": a("act-go-measure"),
    # media
    "media-album-cover-manager-amarok": a("act-go-cover", "gear", "blue"),
    "media-album-track": a("act-go-sleeve", "note", "violet"),
    "media-default-album": a("act-go-sleeve"),
    "media-default-track": a("act-go-note"),
    "media-eject": a("act-go-eject"),
    "media-mount": a("disc", "link", "blue", acc="grey", halo=True),
    "media-playback-pause": a("act-go-pause"),
    "media-playback-start": a("act-go-play"),
    "media-playback-stop": a("act-go-stop"),
    "media-record": a("act-go-record"),
    "media-seek-backward": a("act-go-seek-back"),
    "media-seek-forward": a("act-go-seek-fwd"),
    "media-skip-backward": a("act-go-skip-back"),
    "media-skip-forward": a("act-go-skip-fwd"),
    "media-playlist-append": a("act-go-playlist", "plus"),
    "media-playlist-append-next": a("act-go-playlist", "next", "green"),
    "media-playlist-normal": a("act-go-playlist-normal"),
    "media-playlist-play": a("act-go-playlist", "play", "blue"),
    "media-playlist-repeat": a("act-go-repeat"),
    "media-playlist-shuffle": a("act-go-shuffle"),
    "media-random-albums-amarok": a("act-go-shuffle", "disc", "violet"),
    "media-random-tracks-amarok": a("act-go-shuffle", "note", "violet"),
    "media-repeat-album-amarok": a("act-go-repeat", "disc", "violet"),
    "media-repeat-none": a("act-go-repeat", "cross", "grey"),
    "media-repeat-playlist-amarok": a("act-go-repeat", "list", "blue"),
    "media-repeat-single": a("act-go-repeat", "act-go-one", "orange"),
    "media-track-queue-amarok": a("act-go-note", "clock", "blue"),
    "media-track-show-active": a("act-go-note", "eye", "green"),
    # meeting, menus
    "meeting-attending-tentative": a("act-go-calendar", "question", "orange"),
    "meeting-participant-no-response": a("act-go-user", "hourglass", "grey"),
    "meeting-participant-request-response": a("act-go-user", "question", "blue"),
    "menu_new_sep": a("act-go-moremark", "plus", "blue"),
    "merge": a("act-go-merge"),
    "mergecell": a("act-go-mergecell-all"),
    "mergecell-horizontal": a("act-go-mergecell-h"),
    "mergecell-vertical": a("act-go-mergecell-v"),
    "messagebox_warning": a("act-go-warning"),
    "milestone": a("act-go-flag"),
    "minuet-chords": a("act-go-minuet-chords"),
    "minuet-intervals": a("act-go-minuet-intervals"),
    "minuet-rhythms": a("act-go-minuet-rhythms"),
    "minuet-scales": a("act-go-minuet-scales"),
    "mobile-close-app": a("act-go-phone", "cross", "red"),
    "mobile-task-switcher": a("act-go-tasks"),
    "mode1": a("act-go-mode1"),
    "mode2": a("act-go-mode2"),
    "mode3": a("act-go-mode3"),
    "mode4": a("act-go-mode4"),
    "mode5": a("act-go-mode5"),
    "motion_path_animations": a("act-go-motion"),
    "multiple": a("act-go-multiple"),
    "music-note-16th": a("act-go-note16"),
    # n
    "network-connect": a("act-go-plugs", "check", "green"),
    "network-disconnect": a("act-go-plugs", "cross", "red"),
    "new-audio-alarm": a("act-go-alarm", "music", "violet"),
    "new-command-alarm": a("act-go-alarm", "terminal", "grey"),
    "newline": a("act-go-newline"),
    "news-subscribe": a("act-go-news", "plus"),
    "news-unsubscribe": a("act-go-news", "minus", "red"),
    "nextfuzzy": a("act-go-up-right", "question", "orange"),
    "nextfuzzyuntrans": a("act-go-skip-right", "question", "red"),
    "nextuntranslated": a("act-go-skip-right", "language", "red"),
    "node": a("act-go-node-transform", None),
    "node-segment-curve": a("act-go-node-seg-curve"),
    "node-segment-line": a("act-go-node-seg-line"),
    "node-transform": a("act-go-node-transform", "move", "cyan"),
    "node-type-auto-smooth": a("act-go-node-auto"),
    "node-type-cusp": a("act-go-node-cusp"),
    "node-type-smooth": a("act-go-node-smooth"),
    "node-type-symmetric": a("act-go-node-symmetric"),
    "noisereduction": a("act-go-noise", "minus", "blue"),
    "notification-active": a("act-go-bell-dot"),
    "notification-disabled": a("act-go-bell-off"),
    "notification-empty": a("act-go-bell", "check", "green"),
    "notification-inactive": a("act-go-bell-grey"),
    "notification-progress-active": a("act-go-bell", "act-go-progress", "blue"),
    "notification-progress-inactive": a("act-go-bell-grey", "act-go-progress", "grey"),
    "notifications": a("act-go-bells"),
    "notifications-disabled": a("act-go-bells", "cross", "red"),
    "nroot": a("act-go-root"),
    # objects
    "object-columns": a("act-go-obj-cols"),
    "object-rows": a("act-go-obj-rows"),
    "object-flip-horizontal": a("act-go-obj-flip"),
    "object-flip-vertical": lambda c: (c.group("rotate(90 24 24)", lambda cv: action(cv, "act-go-obj-flip")), True)[1],
    "object-group": a("group", None, acc="violet", halo=True),
    "object-ungroup": a("ungroup", None, acc="violet", halo=True),
    "object-height": a("act-go-obj-height"),
    "object-width": a("act-go-obj-width"),
    "object-order-back": a("act-go-order-back", "arrow-bottom", "violet"),
    "object-order-front": a("act-go-order-front", "arrow-top", "violet"),
    "object-order-lower": a("act-go-order-back", "arrow-down", "blue"),
    "object-order-raise": a("act-go-order-front", "arrow-up", "blue"),
    "object-rotate-left": lambda c: (c.group("translate(48 0) scale(-1 1)", lambda cv: action(cv, "act-go-obj-rot")), True)[1],
    "object-rotate-right": a("act-go-obj-rot"),
    "object-stroke-style": a("act-go-stroke"),
    "object-to-path": a("act-go-topath"),
    # office charts
    "office-chart-area": a("act-go-chart-area"),
    "office-chart-area-focus-peak-node": a("act-go-chart-area-peak"),
    "office-chart-area-percentage": a("act-go-chart-area-percentage"),
    "office-chart-area-stacked": a("act-go-chart-area-stacked"),
    "office-chart-bar": a("act-go-chart-bar"),
    "office-chart-bar-percentage": a("act-go-chart-bar-percentage"),
    "office-chart-bar-stacked": a("act-go-chart-bar-stacked"),
    "office-chart-line": a("act-go-chart-line"),
    "office-chart-line-forecast": a("act-go-chart-line-forecast"),
    "office-chart-line-percentage": a("act-go-chart-line-percentage"),
    "office-chart-line-stacked": a("act-go-chart-line-stacked"),
    "office-chart-pie": a("act-go-chart-pie"),
    "office-chart-polar": a("act-go-chart-polar"),
    "office-chart-polar-stacked": a("act-go-chart-polar-stacked"),
    "office-chart-ring": a("act-go-chart-ring"),
    "office-chart-scatter": a("act-go-chart-scatter"),
    "oilpaint": a("act-go-oilpaint"),
    "open-link": a("act-go-link", "arrow-tool", "blue"),
    "overexposure": a("act-go-overexpose", "exclamation", "orange"),
    "overflow-menu": a("act-go-vdots"),
    "overflow-menu-left": a("act-go-vdots-left"),
    "overflow-menu-right": a("act-go-vdots-right"),
}

for _b in ("double-bottom", "thick-bottom", "thick-outside", "top-n-bottom", "top-n-double-bottom", "top-n-thick-bottom"):
    T[f"gnumeric-format-border-{_b}"] = a(f"act-go-border-{_b}")
for _cur, _sym in CURRENCY.items():
    T[f"help-donate-{_cur}"] = donate(_sym)
for _z in range(1, 6):
    T[f"labplot-{_z}x-zoom"] = zoom(_z)


def draw(name, c):
    if not name or name[0] not in FIRST:
        return None
    fn = T.get(name)
    if fn is None:
        return None
    try:
        return fn(c)
    except Exception:  # noqa: BLE001  never raise
        return None
