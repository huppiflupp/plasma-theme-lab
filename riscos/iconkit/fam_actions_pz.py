"""fam_actions_pz.py: actions whose name does not start with a-o in lower
case (p ... z and the names starting with a capital).

Toolbar icons after base.action(): families share a glyph and differ by
badge, arrow or accent. Glyphs of our own are registered as "act-pz-...".
"""
import math

from base import action
from glyphs import GLYPHS, D, F, O, S, W, glyph, reg


# ---- helpers ------------------------------------------------------------------
def Sd(c, d, col, w=None, dash="2.2 1.8"):
    """A dashed stroke (selection frames, guides, bounding boxes)."""
    c.parts.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{(w or W(c)) * 0.8:g}" '
                   f'stroke-dasharray="{dash}" stroke-linecap="butt" stroke-linejoin="round"/>')


def EO(c, d, col, outline):
    c.parts.append(f'<path d="{d}" fill="{col}" fill-rule="evenodd" stroke="{outline}" '
                   f'stroke-width="{W(c) * 0.7:g}" stroke-linejoin="round"/>')


def R(x, y, w, h):
    return f"M{x} {y} h{w} v{h} h-{w} Z"


def tgt(c, x, y):
    """The snap target: a red point."""
    D(c, x, y, 2.6, c["red"])
    D(c, x, y, 1.0, "#ffffff")


def light(c, name="blue", t=0.45):
    return c.lighten(c[name], t)


# ---- marks used as badges ----------------------------------------------------
@reg("act-pz-harrows")
def _(c, k): S(c, "M3 12 H21 M7 8 L3 12 L7 16 M17 8 L21 12 L17 16", k)
@reg("act-pz-varrows")
def _(c, k): S(c, "M12 3 V21 M8 7 L12 3 L16 7 M8 17 L12 21 L16 17", k)
@reg("act-pz-one")
def _(c, k): S(c, "M8 8 L13 4 V20 M8 20 H18", k)
@reg("act-pz-fx")
def _(c, k): S(c, "M4 20 V9 A4 4 0 0 1 8 5 H10 M2 11 H9 M12 11 L20 20 M20 11 L12 20", k)
@reg("act-pz-child")
def _(c, k): S(c, "M6 3 V12 A4 4 0 0 0 10 16 H20 M15 11 L20 16 L15 21", k)
@reg("act-pz-corner")
def _(c, k): S(c, "M5 20 V5 H20", k); F(c, R(5, 5, 6, 6), k)
@reg("act-pz-zone")
def _(c, k): S(c, "M9 4 H5 V20 H9 M15 4 H19 V20 H15", k)
@reg("act-pz-unlink")
def _(c, k): S(c, "M10 7 L12 5 A4 4 0 0 1 18 11 L16 13 M8 11 L6 13 A4 4 0 0 0 12 19 L14 17 M4 4 L7 7 M17 17 L20 20", k)


# ---- path booleans (two circles A and B) ---------------------------------------
_P1, _P2 = "14.66 8.01", "9.34 15.99"
UNION = f"M{_P1} A6 6 0 1 0 {_P2} A6 6 0 1 0 {_P1} Z"
LENS = f"M{_P1} A6 6 0 0 1 {_P2} A6 6 0 0 1 {_P1} Z"
AMB = f"M{_P1} A6 6 0 1 0 {_P2} A6 6 0 0 1 {_P1} Z"
BMA = f"M{_P2} A6 6 0 1 0 {_P1} A6 6 0 0 1 {_P2} Z"
CA = "M3 10 A6 6 0 1 0 15 10 A6 6 0 1 0 3 10 Z"
CB = "M9 14 A6 6 0 1 0 21 14 A6 6 0 1 0 9 14 Z"


@reg("act-pz-union")
def _(c, k): F(c, UNION, light(c, "blue", 0.2), k)
@reg("act-pz-difference")
def _(c, k): Sd(c, CB, k); F(c, AMB, light(c, "blue", 0.2), k)
@reg("act-pz-intersection")
def _(c, k): Sd(c, CA, k); Sd(c, CB, k); F(c, LENS, light(c, "blue", 0.2), k)
@reg("act-pz-exclusion")
def _(c, k): EO(c, UNION + " " + LENS, light(c, "blue", 0.2), k)
@reg("act-pz-division")
def _(c, k):
    c.group("translate(-1.2 -1.2)", lambda cv: F(cv, AMB, light(cv, "blue", 0.2), k))
    F(c, LENS, light(c, "orange", 0.2), k)
    c.group("translate(1.2 1.2)", lambda cv: F(cv, BMA, light(cv, "green", 0.2), k))
@reg("act-pz-cut")
def _(c, k):
    Sd(c, CB, k)
    S(c, f"M{_P1} A6 6 0 1 0 {_P2}", k)
    S(c, f"M{_P1} A6 6 0 0 1 {_P2}", c["red"])
@reg("act-pz-combine")
def _(c, k):
    F(c, R(3, 3, 8, 8), light(c, "blue", 0.2), k)
    F(c, "M12 17 A5 5 0 1 0 22 17 A5 5 0 1 0 12 17 Z", light(c, "blue", 0.2), k)
    S(c, "M11 11 L14 14", k)
@reg("act-pz-break")
def _(c, k):
    F(c, "M10 4 A8 8 0 0 0 10 20 Z", light(c, "blue", 0.2), k)
    F(c, "M14 4 A8 8 0 0 1 14 20 Z", light(c, "green", 0.2), k)
@reg("act-pz-inset")
def _(c, k): Sd(c, "M3 3 H21 V21 H3 Z", k); F(c, R(7, 7, 10, 10), light(c, "blue", 0.2), k)
@reg("act-pz-outset")
def _(c, k): F(c, R(3, 3, 18, 18), light(c, "blue", 0.2), k); Sd(c, "M8 8 H16 V16 H8 Z", k)
@reg("act-pz-polyline")
def _(c, k):
    S(c, "M3 19 L8 7 L13 15 L20 4", k)
    for x, y in ((3, 19), (8, 7), (13, 15), (20, 4)):
        F(c, R(x - 1.6, y - 1.6, 3.2, 3.2), "#ffffff", k)
@reg("act-pz-paraxial")
def _(c, k):
    S(c, "M3 20 V12 H11 V5 H20", k)
    for x, y in ((3, 20), (3, 12), (11, 12), (11, 5), (20, 5)):
        F(c, R(x - 1.6, y - 1.6, 3.2, 3.2), "#ffffff", k)


# ---- pages, paint ----------------------------------------------------------------
def _sides(n):
    def fn(c, k):
        S(c, "M5 3 H19 V21 H5 Z", k, W(c) * 0.6)
        segs = {0: [], 2: ["M5 3 V21", "M19 3 V21"], 3: ["M5 3 V21", "M19 3 V21", "M5 3 H19"],
                4: ["M5 3 V21 H19 V3 Z"]}[n]
        for d in segs:
            S(c, d, c["red"], W(c) * 1.4)
        if n == 0:
            Sd(c, "M8 6 H16 V18 H8 Z", k)
    return fn


for _n in (0, 2, 3, 4):
    reg(f"act-pz-page{_n}")(_sides(_n))


def paint(kind):
    def fn(c):
        x, y, s = 8, 8, 32
        if kind == "solid":
            c.rect(x, y, s, s, c[ "blue"], 2)
        elif kind == "linear":
            c.rect(x, y, s, s, c.grad(c["blue"], "#ffffff", horizontal=True), 2)
        elif kind == "radial":
            c.rect(x, y, s, s, "#ffffff", 2)
            for r, t in ((15, 0.75), (11, 0.5), (7, 0.25), (3.5, 0)):
                c.circle(24, 24, r, c.lighten(c["blue"], t), None)
        elif kind == "conic":
            c.rect(x, y, s, s, "#ffffff", 2)
            for i in range(8):
                a0, a1 = i * math.pi / 4, (i + 1) * math.pi / 4
                p0 = (24 + 15 * math.cos(a0), 24 + 15 * math.sin(a0))
                p1 = (24 + 15 * math.cos(a1), 24 + 15 * math.sin(a1))
                c.path(f"M24 24 L{p0[0]:.2f} {p0[1]:.2f} A15 15 0 0 1 {p1[0]:.2f} {p1[1]:.2f} Z",
                       c.lighten(c["blue"], i / 9), None)
        elif kind == "none":
            c.rect(x, y, s, s, "#ffffff", 2)
            c.line("M11 37 L37 11", c["red"], 3)
        elif kind == "pattern":
            c.rect(x, y, s, s, "#ffffff", 2, None)
            n = 4 if c.small else 8
            q = s / n
            for i in range(n):
                for j in range(n):
                    if (i + j) % 2:
                        c.rect(x + i * q, y + j * q, q, q, c["violet"], 0, None)
        elif kind == "swatch":
            c.rect(14, 4, 26, 26, c["orange"], 2)
            c.rect(8, 10, 26, 26, c["green"], 2)
            c.rect(x - 4, y + 8, 26, 26, c["blue"], 2)
            return True
        elif kind == "unknown":
            c.rect(x, y, s, s, c.lighten(c["grey"], 0.6), 2)
            glyph(c, "question", 12, 12, 24, c["ink"], width=None if not c.small else 3.4)
        c.rect(x, y, s, s, "none", 2)
        return True
    return fn


# ---- UML, connectors, states ------------------------------------------------------
@reg("act-pz-realization")
def _(c, k): Sd(c, "M2 12 H13", k); S(c, "M13 5 L21 12 L13 19 Z", k)
@reg("act-pz-uniassoc")
def _(c, k): S(c, "M2 12 H20 M14 6 L20 12 L14 18", k); F(c, R(2, 9, 4, 6), k)
@reg("act-pz-connector")
def _(c, k): S(c, R(2, 3, 8, 6) + " " + R(14, 15, 8, 6) + " M6 9 V18 H14", k)
@reg("act-pz-fork")
def _(c, k):
    F(c, R(10.5, 3, 3, 18), k)
    S(c, "M2 12 H9 M6 9 L9 12 L6 15 M14 6 H21 M18 3 L21 6 L18 9 M14 18 H21 M18 15 L21 18 L18 21", k)
@reg("act-pz-state")
def _(c, k): S(c, "M8 5 H16 A5 5 0 0 1 21 10 V14 A5 5 0 0 1 16 19 H8 A5 5 0 0 1 3 14 V10 A5 5 0 0 1 8 5 Z M3 10 H21", k)
@reg("act-pz-deploy")
def _(c, k):
    F(c, "M3 9 L7 4 H21 L17 9 Z", light(c, "grey", 0.5), k)
    S(c, "M3 9 H17 V21 H3 Z M17 9 L21 4 V16 L17 21", k)
@reg("act-pz-condition")
def _(c, k): S(c, "M12 3 L21 12 L12 21 L3 12 Z", k); S(c, "M8 12 H16", k)


# ---- physics (Step) ----------------------------------------------------------------
@reg("act-pz-charge")
def _(c, k): F(c, "M5 12 A7 7 0 1 0 19 12 A7 7 0 1 0 5 12 Z", c["red"], k); S(c, "M12 8.5 V15.5 M8.5 12 H15.5", "#ffffff")
@reg("act-pz-cmotor")
def _(c, k):
    F(c, "M8 12 A4 4 0 1 0 16 12 A4 4 0 1 0 8 12 Z", light(c, "grey", 0.3), k)
    S(c, "M12 3 A9 9 0 1 1 3.6 8.6 M12 3 L9 1 M12 3 L9.5 5.5", k)
@reg("act-pz-coulomb")
def _(c, k):
    F(c, "M2 12 A4 4 0 1 0 10 12 A4 4 0 1 0 2 12 Z", c["red"], k)
    F(c, "M14 12 A4 4 0 1 0 22 12 A4 4 0 1 0 14 12 Z", c["blue"], k)
    S(c, "M6 10 V14 M4 12 H8 M16 12 H20", "#ffffff", W(c) * 0.8)
    S(c, "M4 20 H20 M7 17 L4 20 L7 23 M17 17 L20 20 L17 23", k, W(c) * 0.8)
@reg("act-pz-gravity")
def _(c, k):
    F(c, "M2 12 A5 5 0 1 0 12 12 A5 5 0 1 0 2 12 Z", light(c, "brown", 0.2), k)
    F(c, "M17 12 A2.5 2.5 0 1 0 22 12 A2.5 2.5 0 1 0 17 12 Z", light(c, "brown", 0.2), k)
    S(c, "M8 4 H16 M13 1.5 L16 4 L13 6.5 M16 20 H8 M11 17.5 L8 20 L11 22.5", k, W(c) * 0.8)
@reg("act-pz-lmotor")
def _(c, k): F(c, R(2, 7, 9, 10), light(c, "grey", 0.3), k); S(c, "M11 12 H21 M17 8 L21 12 L17 16", k)
@reg("act-pz-softbody")
def _(c, k):
    pts = [(6, 6), (12, 5), (18, 7), (5, 12), (12, 12), (19, 13), (7, 18), (13, 19), (18, 18)]
    S(c, "M6 6 L12 5 L18 7 L19 13 L18 18 L13 19 L7 18 L5 12 Z M12 5 L12 12 L13 19 M5 12 L12 12 L19 13", k, W(c) * 0.8)
    for x, y in pts:
        D(c, x, y, 1.8, k)
@reg("act-pz-spring")
def _(c, k): S(c, "M2 12 H5 L7 6 L10 18 L13 6 L16 18 L18 12 H22", k)
@reg("act-pz-weight")
def _(c, k):
    F(c, "M7 3 H17 L20 13 H4 Z", light(c, "grey", 0.2), k)
    S(c, "M12 14 V21 M9 18 L12 21 L15 18", c["red"])


# ---- strokes -----------------------------------------------------------------------
def _cap(kind):
    def fn(c, k):
        band = light(c, "blue", 0.5)
        if kind == "round":
            F(c, "M3 7 H14 A5 5 0 0 1 14 17 H3 Z", band, k)
        elif kind == "square":
            F(c, R(3, 7, 16, 10), band, k)
        else:
            F(c, R(3, 7, 11, 10), band, k)
        S(c, "M3 12 H14", k, W(c) * 0.7)
        F(c, R(12.5, 10.5, 3, 3), "#ffffff", k)
    return fn


def _join(kind):
    def fn(c, k):
        band = light(c, "blue", 0.5)
        outer = {"miter": "M3 3 H20 V21", "bevel": "M3 3 H15 L20 8 V21",
                 "round": "M3 3 H15 A5 5 0 0 1 20 8 V21"}[kind]
        F(c, outer + " H12 V12 H3 Z", band, k)
        S(c, "M3 7.5 H16 V21", k, W(c) * 0.7)
    return fn


for _k in ("butt", "round", "square"):
    reg(f"act-pz-cap-{_k}")(_cap(_k))
for _k in ("miter", "bevel", "round"):
    reg(f"act-pz-join-{_k}")(_join(_k))


# ---- windows, tabs, panes -----------------------------------------------------------
@reg("act-pz-tab")
def _(c, k):
    F(c, R(2, 4, 9, 5), light(c, "blue", 0.3))
    S(c, "M2 4 H22 V21 H2 Z M2 9 H22 M11 4 V9 M17 4 V9", k)
@reg("act-pz-sidebar-r")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M15 4 V20", k)
@reg("act-pz-pip")
def _(c, k): S(c, "M2 4 H22 V20 H2 Z", k); F(c, R(12, 6.5, 8, 6), k)
@reg("act-pz-split-lr")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M12 4 V20", k); F(c, R(12, 4, 9, 16), light(c, "blue", 0.5))
@reg("act-pz-split-tb")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M3 12 H21", k); F(c, R(3, 12, 18, 8), light(c, "blue", 0.5))
@reg("act-pz-sidetree")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M10 4 V20 M5 7 H8 M6 7 V16 M6 11.5 H8 M6 16 H8", k)
@reg("act-pz-form")
def _(c, k):
    S(c, "M3 3 H21 V21 H3 Z M6 8 H9 M6 14 H9", k)
    S(c, R(11, 6, 7, 4) + " " + R(11, 12, 7, 4), k, W(c) * 0.8)
@reg("act-pz-textframe")
def _(c, k): S(c, "M3 3 H21 V21 H3 Z", k, W(c) * 0.8); S(c, "M6 8 H18 M6 12 H18 M6 16 H13", k)
@reg("act-pz-textfield")
def _(c, k): S(c, R(2, 7, 20, 10), k); S(c, "M7 9.5 V14.5 M5.5 9.5 H8.5 M5.5 14.5 H8.5", k, W(c) * 0.8)
@reg("act-pz-textfield-framed")
def _(c, k):
    Sd(c, R(1.5, 3.5, 21, 17), k)
    S(c, R(4, 8, 16, 8), k); S(c, "M8 10 V14", k, W(c) * 0.8)
@reg("act-pz-textwrap")
def _(c, k): F(c, R(3, 4, 8, 9), light(c, "blue", 0.3), k); S(c, "M14 5 H21 M14 9 H21 M14 13 H21 M3 17 H21 M3 21 H15", k)
@reg("act-pz-textpath")
def _(c, k):
    S(c, "M2 20 Q12 6 22 20", c["blue"], W(c) * 0.8)
    S(c, "M5 13 L8 5 L11 13 M6.1 10 H9.9 M13 6 H19 M16 6 V14", k)


# ---- letters (kerning, spacing) ------------------------------------------------------
_A = "M2 16 L6.5 4 L11 16 M3.7 12 H9.3"
_V = "M10 4 L14.5 16 L19 4"


@reg("act-pz-av")
def _(c, k): S(c, _A + " M12 4 L16.5 16 L21 4", k)
@reg("act-pz-hkern")
def _(c, k): S(c, _A + " " + _V, k); S(c, "M5 20.5 H18 M8 18 L5 20.5 L8 23 M15 18 L18 20.5 L15 23", c["blue"], W(c) * 0.8)
@reg("act-pz-vkern")
def _(c, k): S(c, "M2 20 L6 8 L10 20 M3.3 16 H8.7 M10 3 L13.5 14 L17 3", k); S(c, "M21 3 V20 M19 6 L21 3 L23 6 M19 17 L21 20 L23 17", c["blue"], W(c) * 0.8)
@reg("act-pz-letterspace")
def _(c, k): S(c, "M1 16 L4.5 6 L8 16 M2.3 12.5 H6.7 M16 6 L19.5 16 L23 6", k); S(c, "M9.5 11 H14.5 M11 9 L9.5 11 L11 13 M13 9 L14.5 11 L13 13", c["blue"], W(c) * 0.7)
@reg("act-pz-wordspace")
def _(c, k): S(c, "M2 5 H9 M2 9 H9 M2 13 H7 M15 5 H22 M15 9 H22 M15 13 H20", k); S(c, "M4 19 H20 M7 16.5 L4 19 L7 21.5 M17 16.5 L20 19 L17 21.5", c["blue"], W(c) * 0.8)
@reg("act-pz-linespace")
def _(c, k): S(c, "M10 5 H21 M10 12 H21 M10 19 H21", k); S(c, "M4 4 V20 M2 7 L4 4 L6 7 M2 17 L4 20 L6 17", c["blue"], W(c) * 0.8)
@reg("act-pz-textrot")
def _(c, k): S(c, "M3 5 H12 M7.5 5 V18", k); S(c, "M15 4 A9 9 0 0 1 20 17 M17 14.5 L20 17 L22.5 13.5", c["blue"])


# ---- timeline, media ------------------------------------------------------------------
@reg("act-pz-timeline")
def _(c, k):
    F(c, R(2, 5, 9, 5), light(c, "blue", 0.3), k)
    F(c, R(12, 5, 10, 5), light(c, "violet", 0.3), k)
    F(c, R(5, 13, 12, 5), light(c, "green", 0.3), k)
    S(c, "M14.5 2 V21", c["red"])
@reg("act-pz-zone-in")
def _(c, k): S(c, "M2 18 H22", k, W(c) * 0.6); S(c, "M13 4 H8 V21 H13", c["green"], W(c) * 1.3); S(c, "M14 12 H21 M18 9 L21 12 L18 15", k)
@reg("act-pz-zone-out")
def _(c, k): S(c, "M2 18 H22", k, W(c) * 0.6); S(c, "M11 4 H16 V21 H11", c["red"], W(c) * 1.3); S(c, "M10 12 H3 M6 9 L3 12 L6 15", k)
@reg("act-pz-reverse")
def _(c, k): F(c, "M18 4 V20 L5 12 Z", k)
@reg("act-pz-roll")
def _(c, k):
    F(c, R(2, 9, 9, 10), light(c, "blue", 0.3), k)
    F(c, R(13, 9, 9, 10), light(c, "violet", 0.3), k)
    S(c, "M12 7 V21", c["red"]); S(c, "M7 4 H17 M10 1.5 L7 4 L10 6.5 M14 1.5 L17 4 L14 6.5", k, W(c) * 0.8)
@reg("act-pz-split")
def _(c, k):
    F(c, R(2, 8, 8, 9), light(c, "blue", 0.3), k)
    F(c, R(14, 8, 8, 9), light(c, "blue", 0.3), k)
    Sd(c, "M12 3 V22", c["red"])
@reg("act-pz-waveform")
def _(c, k): S(c, "M2 12 H3 L4.5 8 L6 16 L7.5 4 L9 20 L10.5 7 L12 17 L13.5 9 L15 15 L16.5 6 L18 18 L19.5 10 L21 14 L22 12", k)
@reg("act-pz-eq")
def _(c, k):
    S(c, "M5 3 V21 M12 3 V21 M19 3 V21", k, W(c) * 0.7)
    for x, y in ((5, 15), (12, 7), (19, 12)):
        F(c, R(x - 2.8, y - 1.8, 5.6, 3.6), "#ffffff", k)
@reg("act-pz-lyrics")
def _(c, k): S(c, "M7 17 V5 L11 4", k); D(c, 5, 17, 2.4, k); S(c, "M14 7 H22 M14 12 H22 M14 17 H19", k)
@reg("act-pz-film")
def _(c, k):
    S(c, "M3 5 H21 V19 H3 Z M7 5 V19 M17 5 V19", k)
    F(c, "M10 9 V15 L15 12 Z", k)


# ---- documents, views -----------------------------------------------------------------
@reg("act-pz-cert")
def _(c, k):
    S(c, "M2 3 H22 V16 H14 M5 16 H2 V3", k)
    S(c, "M12 7 H19 M12 11 H19 M5 7 H9", k, W(c) * 0.7)
    F(c, "M4.5 15 A3.5 3.5 0 1 0 11.5 15 A3.5 3.5 0 1 0 4.5 15 Z", c["red"], k)
    S(c, "M6 18 L5 22 M10 18 L11 22", c["red"])
@reg("act-pz-pages-cont")
def _(c, k): S(c, R(7, 1.5, 10, 9) + " " + R(7, 13.5, 10, 9), k)
@reg("act-pz-pages-facing")
def _(c, k): S(c, R(2, 5, 9.5, 14) + " " + R(12.5, 5, 9.5, 14), k)
@reg("act-pz-pages-first")
def _(c, k): S(c, R(7.5, 2, 9, 9) + " " + R(2.5, 13, 9, 9) + " " + R(12.5, 13, 9, 9), k)
@reg("act-pz-pages-overview")
def _(c, k): S(c, " ".join(R(2 + i * 7.3, 3 + j * 9.5, 5.5, 8) for i in range(3) for j in range(2)), k, W(c) * 0.8)
@reg("act-pz-sort-asc")
def _(c, k): S(c, "M5 4 V19 M2 16 L5 19 L8 16", c["blue"]); S(c, "M11 6 H14 M11 12 H17 M11 18 H21", k)
@reg("act-pz-sort-desc")
def _(c, k): S(c, "M5 4 V19 M2 16 L5 19 L8 16", c["blue"]); S(c, "M11 6 H21 M11 12 H17 M11 18 H14", k)
@reg("act-pz-sort-az")
def _(c, k): S(c, "M5 4 V19 M2 16 L5 19 L8 16", c["blue"]); S(c, "M12 10 L14.5 3 L17 10 M13 8 H16 M12 14 H17 L12 21 H17", k)
@reg("act-pz-sort-za")
def _(c, k): S(c, "M5 4 V19 M2 16 L5 19 L8 16", c["blue"]); S(c, "M12 3 H17 L12 10 H17 M12 21 L14.5 14 L17 21 M13 19 H16", k)
@reg("act-pz-splitview")
def _(c, k):
    F(c, R(3, 5, 9, 14), light(c, "cyan", 0.4))
    S(c, "M3 5 H21 V19 H3 Z M3 16 L9 10 L14 15 L16 13 L21 18", k)
    S(c, "M12 2 V22", c["red"])
@reg("act-pz-list-details")
def _(c, k):
    for y in (6, 12, 18):
        F(c, R(2, y - 2, 4, 4), k)
        S(c, f"M8 {y} H14 M17 {y} H22", k)
@reg("act-pz-list-icons")
def _(c, k):
    F(c, R(4, 2, 6, 6), k); F(c, R(14, 2, 6, 6), k); F(c, R(4, 13, 6, 6), k); F(c, R(14, 13, 6, 6), k)
    S(c, "M3 10.5 H11 M13 10.5 H21 M3 21.5 H11 M13 21.5 H21", k, W(c) * 0.7)
@reg("act-pz-grouped")
def _(c, k):
    F(c, R(2, 2.5, 5, 5), k); F(c, R(2, 13.5, 5, 5), k)
    S(c, "M9 5 H21 M9 16 H21", k)
    S(c, "M12 9.5 H21 M12 20.5 H21", k, W(c) * 0.7)
@reg("act-pz-gantt")
def _(c, k):
    S(c, "M2 2 V22", k, W(c) * 0.6)
    F(c, R(4, 3, 9, 4), light(c, "blue", 0.2), k)
    F(c, R(8, 10, 10, 4), light(c, "orange", 0.2), k)
    F(c, R(13, 17, 8, 4), light(c, "green", 0.2), k)
@reg("act-pz-cal-month")
def _(c, k): S(c, "M3 5 H21 V21 H3 Z M3 9 H21 M8 3 V7 M16 3 V7", k); S(c, "M3 13 H21 M3 17 H21 M9 9 V21 M15 9 V21", k, W(c) * 0.6)
@reg("act-pz-cal-week")
def _(c, k): S(c, "M3 5 H21 V21 H3 Z M3 9 H21 M8 3 V7 M16 3 V7", k); F(c, R(3, 12.5, 18, 4), c["red"])
@reg("act-pz-hist-log")
def _(c, k): S(c, "M3 20 H21 M5 20 V5 M8 20 V9 M11 20 V12 M14 20 V14 M17 20 V16 M20 20 V17", k)
@reg("act-pz-bubbles")
def _(c, k):
    S(c, "M3 3 V21 H21", k)
    F(c, "M5 15 A2.5 2.5 0 1 0 10 15 A2.5 2.5 0 1 0 5 15 Z", light(c, "blue", 0.2), k)
    F(c, "M10 8 A4 4 0 1 0 18 8 A4 4 0 1 0 10 8 Z", light(c, "orange", 0.2), k)
    F(c, "M15 16 A2 2 0 1 0 19 16 A2 2 0 1 0 15 16 Z", light(c, "green", 0.2), k)
@reg("act-pz-guides")
def _(c, k):
    Sd(c, "M2 8 H22 M9 2 V22", c["blue"])
    F(c, "M2 5 L5 8 L2 11 Z M6 2 L9 5 L12 2 Z", k)
@reg("act-pz-pixels")
def _(c, k):
    for i in range(3):
        for j in range(3):
            F(c, R(3 + i * 6, 3 + j * 6, 6, 6), k if (i + j) % 2 == 0 else light(c, "grey", 0.4))
@reg("act-pz-trace")
def _(c, k):
    for x, y in ((3, 15), (9, 15), (9, 9), (15, 9), (15, 3)):
        F(c, R(x, y, 6, 6), light(c, "grey", 0.5))
    S(c, "M3 21 C8 21 10 12 13 11 C17 10 18 6 21 3", c["blue"], W(c) * 1.1)
@reg("act-pz-texture")
def _(c, k): S(c, "M3 3 H21 V21 H3 Z", k); S(c, "M3 9 L9 3 M3 15 L15 3 M3 21 L21 3 M9 21 L21 9 M15 21 L21 15", k, W(c) * 0.6)
@reg("act-pz-sqrt")
def _(c, k): S(c, "M2 13 L5 11.5 L8.5 20 L13 3 H22", k); S(c, "M15 8 L20 15 M20 8 L15 15", k, W(c) * 0.8)
@reg("act-pz-octagon")
def _(c, k):
    pts = [(12 + 9.5 * math.cos(math.radians(22.5 + 45 * i)), 12 + 9.5 * math.sin(math.radians(22.5 + 45 * i)))
           for i in range(8)]
    F(c, "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z", c["red"], k)
    S(c, "M8.5 8.5 L15.5 15.5 M15.5 8.5 L8.5 15.5", "#ffffff", W(c) * 1.2)
@reg("act-pz-spray")
def _(c, k):
    F(c, "M10 9 H18 V21 H10 Z", light(c, "grey", 0.3), k)
    F(c, R(12, 5.5, 4, 3.5), k)
    S(c, "M12 7 H10", k)
    for x, y in ((6.5, 4), (4, 6.5), (6.5, 8.5), (3.5, 10), (6, 12)):
        D(c, x, y, 1.1, k)
@reg("act-pz-ellipse-sel")
def _(c, k): Sd(c, "M3 12 A9 6.5 0 1 0 21 12 A9 6.5 0 1 0 3 12 Z", k, W(c) * 1.25)
@reg("act-pz-tools")
def _(c, k):
    GLYPHS["wrench"](c, k)
    c.group("translate(24 0) scale(-1 1)", lambda cv: GLYPHS["screwdriver"](cv, k))
@reg("act-pz-typewriter")
def _(c, k):
    S(c, "M7 10 V3 H17 V10", k, W(c) * 0.9)
    S(c, "M9.5 6 H14.5", k, W(c) * 0.6)
    F(c, "M4 10 H20 L22 20 H2 Z", light(c, "grey", 0.4), k)
    for x in (6, 9.5, 13, 16.5):
        D(c, x + 0.5, 14, 1.1, k)
    S(c, "M7 17.5 H17", k, W(c) * 0.8)


# ---- money --------------------------------------------------------------------------
@reg("act-pz-coins")
def _(c, k):
    gold = c["yellow"]
    F(c, "M5 7 V17 A7 2.8 0 0 0 19 17 V7 Z", gold, k)
    F(c, "M5 7 A7 2.8 0 1 0 19 7 A7 2.8 0 1 0 5 7 Z", c.lighten(gold, 0.4), k)
    S(c, "M5 10.5 A7 2.8 0 0 0 19 10.5 M5 14 A7 2.8 0 0 0 19 14", k, W(c) * 0.6)
@reg("act-pz-cheque")
def _(c, k): S(c, "M2 6 H22 V18 H2 Z", k); S(c, "M5 10 H12 M11 15 Q13 12 14.5 15 T18 14", k, W(c) * 0.7)
@reg("act-pz-card")
def _(c, k): S(c, "M2 5 H22 V19 H2 Z", k); F(c, R(2, 8, 20, 3), k); S(c, R(5, 13.5, 5, 3), k, W(c) * 0.6)
@reg("act-pz-piggy")
def _(c, k):
    F(c, "M4 13 A8 6 0 1 0 20 13 A8 6 0 1 0 4 13 Z", c.lighten(c["red"], 0.55), k)
    S(c, "M20 11 H22 V15 H20 M8 8 L9 4 L12 7.2 M7 18 V21 M16 18 V21 M10 9.5 H14", k)
    D(c, 16, 11, 1, k)
@reg("act-pz-wallet")
def _(c, k): S(c, "M3 7 H19 A2 2 0 0 1 21 9 V18 A2 2 0 0 1 19 20 H3 Z M21 11 H16 A2 2 0 0 0 16 15 H21 M3 7 L15 3 L17 7", k)
@reg("act-pz-wallet-open")
def _(c, k):
    F(c, "M6 9 L8 2 H19 L18 9 Z", c.lighten(c["green"], 0.4), k)
    S(c, "M3 9 H19 A2 2 0 0 1 21 11 V18 A2 2 0 0 1 19 20 H3 Z M21 12.5 H16 A1.8 1.8 0 0 0 16 16.5 H21", k)


# ---- version control ----------------------------------------------------------------
@reg("act-pz-commit")
def _(c, k): S(c, "M2 12 H7.5 M16.5 12 H22", k); O(c, 12, 12, 4.5, k)
@reg("act-pz-diff")
def _(c, k): S(c, "M4 3 H20 V21 H4 Z", k, W(c) * 0.8); S(c, "M8 8.5 H16 M12 4.5 V12.5", c["green"]); S(c, "M8 17 H16", c["red"])
@reg("act-pz-merge")
def _(c, k): S(c, "M7 6 V18 M17 6 C17 13 7 11 7 16", k); O(c, 7, 4, 2, k); O(c, 17, 4, 2, k); O(c, 7, 20, 2, k)


# ---- snapping (the target in red) -----------------------------------------------------


SNAP = {}


def _s(name):
    def deco(fn):
        reg("act-pz-snap-" + name)(fn)
        SNAP["snap-" + name] = "act-pz-snap-" + name
        return fn
    return deco


BOX = "M4 4 H20 V20 H4 Z"


@_s("angle")
def _(c, k): S(c, "M4 20 H21 M4 20 L17 6", k); S(c, "M12 20 A8 8 0 0 0 9.9 14.6", c["blue"], W(c) * 0.8); tgt(c, 17, 6)
@_s("bounding-box-center")
def _(c, k): Sd(c, BOX, k); tgt(c, 12, 12)
@_s("bounding-box-corners")
def _(c, k): Sd(c, BOX, k); [tgt(c, x, y) for x in (4, 20) for y in (4, 20)]
@_s("bounding-box-edges")
def _(c, k): Sd(c, BOX, k); S(c, "M4 4 H20", c["red"], W(c) * 1.2); tgt(c, 14, 4)
@_s("bounding-box-midpoints")
def _(c, k): Sd(c, BOX, k); [tgt(c, x, y) for x, y in ((12, 4), (20, 12), (12, 20), (4, 12))]
@_s("extension")
def _(c, k): S(c, "M3 21 L11 13", k); Sd(c, "M11 13 L20 4", k); tgt(c, 17, 7)
@_s("grid-guide-intersections")
def _(c, k): S(c, "M2 8 H22 M2 16 H22 M8 2 V22 M16 2 V22", k, W(c) * 0.6); tgt(c, 16, 8)
@_s("guideline")
def _(c, k): S(c, "M2 14 H22", c["blue"]); F(c, "M2 10 L5 14 L2 18 Z", k); tgt(c, 12, 14)
@_s("intersection")
def _(c, k): S(c, "M3 5 L21 19 M3 19 L21 5", k); tgt(c, 12, 12)
@_s("node")
def _(c, k):
    S(c, "M3 19 C7 4 16 4 21 15", k)
    F(c, R(1.4, 17.4, 3.2, 3.2), "#ffffff", k)
    F(c, R(18.7, 12.7, 4.6, 4.6), c["red"], k)
@_s("nodes-center")
def _(c, k): O(c, 12, 12, 8.5, k); tgt(c, 12, 12)
@_s("nodes-cusp")
def _(c, k): S(c, "M3 19 L12 6 L21 19", k); F(c, "M12 2.5 L15.5 6 L12 9.5 L8.5 6 Z", c["red"], k)
@_s("nodes-intersection")
def _(c, k): S(c, "M3 6 C10 6 14 18 21 18 M3 18 C10 18 14 6 21 6", k); tgt(c, 12, 12)
@_s("nodes-midpoint")
def _(c, k):
    S(c, "M4 18 L20 6", k)
    F(c, R(2.4, 16.4, 3.2, 3.2), "#ffffff", k); F(c, R(18.4, 4.4, 3.2, 3.2), "#ffffff", k)
    tgt(c, 12, 12)
@_s("nodes-path")
def _(c, k): S(c, "M3 17 C8 4 16 22 21 8", k); tgt(c, 12, 13)
@_s("nodes-rotation-center")
def _(c, k):
    S(c, "M19.5 8 A8.5 8.5 0 1 0 20 15 M20 4 V8.5 H15.5", k)
    S(c, "M12 8 V16 M8 12 H16", c["red"], W(c) * 1.1)
@_s("nodes-smooth")
def _(c, k):
    S(c, "M3 20 C5 6 19 6 21 20", k)
    S(c, "M5 9.5 H19", c["blue"], W(c) * 0.6); D(c, 5, 9.5, 1.5, c["blue"]); D(c, 19, 9.5, 1.5, c["blue"])
    tgt(c, 12, 9.5)
@_s("orthogonal")
def _(c, k): S(c, "M5 3 V19 H21", k); S(c, "M5 13 H11 V19", c["blue"], W(c) * 0.7); tgt(c, 5, 19)
@_s("page")
def _(c, k): S(c, "M4 3 H15 L20 8 V21 H4 Z M15 3 V8 H20", k); tgt(c, 4, 3); tgt(c, 4, 21)
@_s("text-baseline")
def _(c, k): S(c, "M2 18 H22", c["blue"]); S(c, "M4 18 L9 5 L14 18 M5.9 13 H12.1", k); tgt(c, 18, 18)


# ---- the table --------------------------------------------------------------------------
def A(g, accent=None, badge=None, bc=None):
    return (g, accent, badge, bc)


SPEC = {
    # UML conditions, constraints
    "PrePostCondition": A("act-pz-condition", "violet", "repeat", "violet"),
    "precondition": A("act-pz-condition", "violet", "arrow-first", "violet"),
    "primarykey_constraint": A("key", "orange", "table", "orange"),
    "unique_constraint": A("table", None, "act-pz-one", "violet"),
    "realization": A("act-pz-realization", "violet"),
    "uniassociation": A("act-pz-uniassoc", "violet"),
    "standard-connector": A("act-pz-connector"),
    "state-fork": A("act-pz-fork"),
    "stateshape": A("act-pz-state"),
    "umbrello_diagram_deployment": A("act-pz-deploy"),
    # pages
    "page-simple": A("act-pz-page0"),
    "page-2sides": A("act-pz-page2"),
    "page-3sides": A("act-pz-page3"),
    "page-4sides": A("act-pz-page4"),
    "paper-color": A("page", None, "drop", "orange"),
    "panel-fit-height": A("panel", None, "act-pz-varrows", "blue"),
    "panel-fit-width": A("panel", None, "act-pz-harrows", "blue"),
    "swap-panels": A("columns", None, "repeat", "blue"),
    # copy credentials
    "password-copy": A("key", None, "copy", "blue"),
    "username-copy": A("user", None, "copy", "blue"),
    # paths
    "path-union": A("act-pz-union"),
    "path-difference": A("act-pz-difference"),
    "path-intersection": A("act-pz-intersection"),
    "path-exclusion": A("act-pz-exclusion"),
    "path-division": A("act-pz-division"),
    "path-cut": A("act-pz-cut"),
    "path-combine": A("act-pz-combine"),
    "path-break-apart": A("act-pz-break"),
    "path-inset": A("act-pz-inset"),
    "path-outset": A("act-pz-outset"),
    "path-offset-dynamic": A("act-pz-outset", None, "hand", "blue"),
    "path-offset-linked": A("act-pz-outset", None, "link", "blue"),
    "path-effect-parameter-next": A("path", None, "arrow-right", "blue"),
    "path-mask-edit": A("contrast", None, "pencil", "violet"),
    "path-mode-polyline": A("act-pz-polyline"),
    "path-mode-polyline-paraxial": A("act-pz-paraxial"),
    "path-reverse": A("path", None, "arrow-left", "orange"),
    "path-simplify": A("path", None, "minus", "orange"),
    "pathshape": A("vector", "blue"),
    "stroke-to-path": A("path", None, "act-pz-harrows", "violet"),
    "smooth": A("curves", "cyan"),
    "rectangle-make-corners-sharp": A("rectangle", None, "act-pz-corner", "blue"),
    "perspective": A("perspective"),
    "shapes": A("shapes"),
    "symbols": A("sigma", "violet"),
    "percent": A("percent"),
    "sqrt": A("act-pz-sqrt"),
    "stroke-cap-butt": A("act-pz-cap-butt"),
    "stroke-cap-round": A("act-pz-cap-round"),
    "stroke-cap-square": A("act-pz-cap-square"),
    "stroke-join-bevel": A("act-pz-join-bevel"),
    "stroke-join-miter": A("act-pz-join-miter"),
    "stroke-join-round": A("act-pz-join-round"),
    # pixels, photos
    "pixelate": A("act-pz-pixels"),
    "pixelart-trace": A("act-pz-trace"),
    "redeyes": A("eye", "red"),
    "restoration": A("picture", None, "wrench", "green"),
    "sharpenimage": A("picture", None, "sharpen", "blue"),
    "underexposure": A("picture", None, "sun", "orange"),
    "whitebalance": A("picture", None, "thermometer", "cyan"),
    "texture": A("act-pz-texture", "brown"),
    "raindrop": A("drop", "cyan"),
    # player
    "player-time": A("clock", "blue", "play", "blue"),
    "player-volume": A("speaker", "blue"),
    "player-volume-muted": A("speaker-off", "blue"),
    "speaker": A("speaker"),
    "repeat": A("repeat", "blue"),
    "reverse": A("act-pz-reverse", "blue"),
    "waveform": A("act-pz-waveform", "blue"),
    "rss": A("feed", "orange"),
    "torrents": A("share", "green", "arrow-down", "green"),
    "similarartists-amarok": A("people", None, "music", "violet"),
    # plugins, checks
    "plugins": A("puzzle", "green"),
    "preflight-verifier": A("clipboard-check", None, "printer", "blue"),
    "question": A("question", "blue"),
    "process-stop": A("act-pz-octagon"),
    "send_signal": A("send", None, "lightning", "orange"),
    # translation (Lokalize)
    "prevfuzzy": A("arrow-left", None, "question", "orange"),
    "prevfuzzyuntrans": A("arrow-left", None, "question", "red"),
    "prevuntranslated": A("arrow-left", None, "cross", "red"),
    "warnprev": A("arrow-left", None, "exclamation", "orange"),
    "warnnext": A("arrow-right", None, "exclamation", "orange"),
    "translate": A("language"),
    "upindicator": A("chevron-up", "blue"),
    # preview zones (video editor)
    "preview-add-zone": A("act-pz-film", None, "plus", "green"),
    "preview-remove-zone": A("act-pz-film", None, "minus", "red"),
    "preview-remove-all": A("act-pz-film", None, "cross", "red"),
    "preview-render-on": A("act-pz-film", None, "play", "green"),
    "preview-render-off": A("act-pz-film", None, "stop", "grey"),
    # projects
    "project-defaults": A("briefcase", "brown", "gear", "grey"),
    "project-open": A("briefcase", "brown", "open", "blue"),
    "project-development-close": A("briefcase", "brown", "cross", "red"),
    "project-development-new-template": A("briefcase", "brown", "plus", "green"),
    # quick open
    "quickopen": A("open", None, "lightning", "orange"),
    "quickopen-class": A("open", None, "box", "orange"),
    "quickopen-file": A("open", None, "page", "orange"),
    "quickopen-function": A("open", None, "act-pz-fx", "orange"),
    # links
    "remove-link": A("link", None, "minus", "red"),
    # tables
    "resizecol": A("table", None, "act-pz-harrows", "blue"),
    "resizerow": A("table", None, "act-pz-varrows", "blue"),
    "table": A("table"),
    # resources
    "resource-calendar-insert": A("calendar", "brown", "plus", "green"),
    "resource-calendar-child": A("calendar", "brown", "act-pz-child", "blue"),
    "resource-calendar-child-insert": A("calendar", "brown", "act-pz-child", "green"),
    "resource-group-new": A("people", "brown", "plus", "green"),
    # edits
    "roll": A("act-pz-roll"),
    "split": A("act-pz-split"),
    # build
    "run-build": A("hammer", None, "play", "green"),
    "run-build-clean": A("hammer", None, "brush", "orange"),
    "run-build-configure": A("hammer", None, "gear", "grey"),
    "run-build-file": A("hammer", None, "page", "blue"),
    "run-build-install": A("hammer", None, "arrow-down", "green"),
    "run-build-install-root": A("hammer", None, "shield", "red"),
    "run-build-prune": A("hammer", None, "scissors", "red"),
    # selection, layers
    "select-rectangular": A("selection", "blue"),
    "selection-move-to-layer-above": A("layers", None, "arrow-up", "blue"),
    "selection-move-to-layer-below": A("layers", None, "arrow-down", "blue"),
    # show
    "show-all-effects": A("wand", None, "eye", "blue"),
    "show-background": A("picture", None, "eye", "blue"),
    "show-gpu-effects": A("chip", None, "eye", "blue"),
    "show-guides": A("act-pz-guides", None, "eye", "blue"),
    "show-menu": A("menu", None, "eye", "blue"),
    "show-node-handles": A("node", None, "eye", "blue"),
    "show-path-outline": A("path", None, "eye", "blue"),
    # sidebars
    "sidebar-collapse-left": A("sidebar", None, "chevron-left", "blue"),
    "sidebar-expand-left": A("sidebar", None, "chevron-right", "blue"),
    "sidebar-collapse-right": A("act-pz-sidebar-r", None, "chevron-right", "blue"),
    "sidebar-expand-right": A("act-pz-sidebar-r", None, "chevron-left", "blue"),
    # finance (Skrooge)
    "skg-chart-bubble": A("act-pz-bubbles"),
    "skrooge_less": A("money", None, "arrow-down", "red"),
    "skrooge_much_less": A("money", None, "arrow-down-double", "red"),
    "skrooge_more": A("money", None, "arrow-up", "green"),
    "skrooge_much_more": A("money", None, "arrow-up-double", "green"),
    "skrooge_type": A("money", None, "tag", "blue"),
    "taxes-finances": A("money", None, "percent", "red"),
    # smileys
    "smiley": A("smile"),
    "smiley-add": A("smile", None, "plus", "green"),
    "stickers": A("sticky-note", "violet", "star", "violet"),
    # snap: target pictures (SNAP), plus the switch
    "snap": A("magnet", "red"),
    "sort-presence": A("sort", None, "user", "green"),
    "special_paste": A("paste", None, "star", "orange"),
    # physics
    "step_object_ChargedParticle": A("act-pz-charge"),
    "step_object_CircularMotor": A("act-pz-cmotor"),
    "step_object_CoulombForce": A("act-pz-coulomb"),
    "step_object_GravitationForce": A("act-pz-gravity"),
    "step_object_LinearMotor": A("act-pz-lmotor"),
    "step_object_SoftBody": A("act-pz-softbody"),
    "step_object_Spring": A("act-pz-spring"),
    "step_object_WeightForce": A("act-pz-weight"),
    "story-editor": A("book", None, "pen", "blue"),
    # system
    "system-log-out": A("logout"),
    "system-reboot-update": A("restart", None, "arrow-up", "green"),
    "system-shutdown": A("power", "red"),
    "system-shutdown-update": A("power", "red", "arrow-up", "green"),
    "system-suspend": A("sleep"),
    "system-suspend-hibernate": A("hibernate"),
    "system-switch-user": A("switch-user"),
    "system-upgrade": A("arrow-up-double", "green"),
    "system-user-list": A("users", None, "menu", "blue"),
    "system-user-prompt": A("user", None, "question", "blue"),
    # tabs
    "tab-new": A("act-pz-tab", None, "plus", "green"),
    "tab-new-background": A("act-pz-tab", "grey", "plus", "grey"),
    "tab-duplicate": A("act-pz-tab", None, "copy", "blue"),
    "tab-detach": A("act-pz-tab", None, "arrow-tool", "blue"),
    # tags, tasks
    "tag": A("tag"),
    "tag-edit": A("tag", None, "pencil", "blue"),
    "tag-new": A("tag", None, "plus", "green"),
    "task-new": A("clipboard-check", None, "plus", "green"),
    "texlion": A("paw", "orange"),
    # text
    "text-field": A("act-pz-textfield"),
    "text-field-framed": A("act-pz-textfield-framed"),
    "text-flow-into-frame": A("act-pz-textframe", None, "arrow-right", "blue"),
    "text-unflow": A("act-pz-textframe", None, "arrow-left", "orange"),
    "text-frame-link": A("act-pz-textframe", None, "link", "blue"),
    "text-frame-unlink": A("act-pz-textframe", None, "act-pz-unlink", "red"),
    "text-put-on-path": A("act-pz-textpath"),
    "text-remove-from-path": A("act-pz-textpath", None, "minus", "red"),
    "text-speak": A("chat", None, "speaker", "blue"),
    "text-wrap": A("act-pz-textwrap"),
    "text-unkern": A("act-pz-av", None, "minus", "orange"),
    "text_remove_kerns": A("act-pz-av", None, "cross", "red"),
    "text_horz_kern": A("act-pz-hkern"),
    "text_vert_kern": A("act-pz-vkern"),
    "text_letter_spacing": A("act-pz-letterspace"),
    "text_word_spacing": A("act-pz-wordspace"),
    "text_line_spacing": A("act-pz-linespace"),
    "text_rotation": A("act-pz-textrot"),
    "typewriter": A("act-pz-typewriter"),
    # timeline
    "timeline-extract": A("act-pz-timeline", None, "minus", "red"),
    "timeline-lift": A("act-pz-timeline", None, "arrow-up", "orange"),
    "timeline-insert": A("act-pz-timeline", None, "plus", "green"),
    "timeline-overwrite": A("act-pz-timeline", None, "arrow-down", "orange"),
    "timeline-mode-normal": A("act-pz-timeline", None, "pointer", "blue"),
    "timeline-mode-insert": A("act-pz-timeline", None, "arrow-right-double", "blue"),
    "timeline-mode-overwrite": A("act-pz-timeline", None, "square", "blue"),
    "timeline-use-zone-on": A("act-pz-timeline", None, "act-pz-zone", "green"),
    "timeline-use-zone-off": A("act-pz-timeline", None, "act-pz-zone", "grey"),
    "zone-in": A("act-pz-zone-in"),
    "zone-out": A("act-pz-zone-out"),
    # tools
    "tool-animator": A("film", None, "pencil", "orange"),
    "tool-spray": A("act-pz-spray"),
    "tool-tweak": A("gesture", "violet"),
    "tool_color_eraser": A("eraser", None, "drop", "violet"),
    "tool_curve": A("bezier", "violet"),
    "tool_elliptical_selection": A("act-pz-ellipse-sel"),
    "tool_polygon": A("polygon", "violet"),
    "tools": A("act-pz-tools"),
    "tools-check-spelling": A("spell"),
    "tools-wizard": A("wand"),
    "tools-report-bug": A("bug", None, "exclamation", "red"),
    "tools-media-optical-burn": A("disc", "orange", "flame", "red"),
    "tools-media-optical-burn-image": A("archive", None, "flame", "red"),
    "tools-media-optical-copy": A("disc", None, "copy", "blue"),
    "tools-media-optical-erase": A("disc", None, "eraser", "red"),
    "tools-media-optical-format": A("disc", None, "gear", "grey"),
    "tools-rip-audio-cd": A("disc", None, "music", "blue"),
    "tools-rip-video-cd": A("disc", None, "film", "blue"),
    "tools-rip-video-dvd": A("disc", "violet", "film", "violet"),
    # transform
    "transform-affect-gradient": A("gradient-tool", None, "scale", "blue"),
    "transform-affect-pattern": A("act-pz-texture", None, "scale", "blue"),
    "transform-affect-rounded-corners": A("act-pz-corner", None, "scale", "blue"),
    "transform-affect-stroke": A("act-pz-cap-round", None, "scale", "blue"),
    "transform-browse": A("hand"),
    "transform-crop": A("crop"),
    "transform-crop-and-resize": A("crop", None, "resize", "blue"),
    "transform-move": A("move"),
    "transform-move-horizontal": A("act-pz-harrows", "blue"),
    "transform-move-vertical": A("act-pz-varrows", "blue"),
    "transform-rotate": A("rotate-right"),
    "transform-scale": A("scale"),
    "transform-scale-textbox-points": A("text", None, "scale", "blue"),
    "transform-shear-left": A("shear", None, "arrow-left", "blue"),
    "transform-shear-right": A("shear", None, "arrow-right", "blue"),
    "transform-shear-up": A("act-pz-shear-v", None, "arrow-up", "blue"),
    "transform-shear-down": A("act-pz-shear-v", None, "arrow-down", "blue"),
    "transport-mode-flight": A("plane"),
    "trash-empty": A("trash", None, "minus", "red"),
    "trim-margins": A("page", None, "crop", "orange"),
    "trim-to-selection": A("selection", None, "crop", "orange"),
    "unmarkasblank": A("page", None, "cross", "grey"),
    "upload-later": A("upload", None, "clock", "blue"),
    "upload-media": A("upload", None, "picture", "blue"),
    # users
    "user-group-new": A("users", None, "plus", "green"),
    "user-group-delete": A("users", None, "minus", "red"),
    "user-group-properties": A("users", None, "gear", "grey"),
    "user-others": A("users", "grey"),
    "value-decrease": A("arrow-down", "red", "minus", "red"),
    # version control
    "vcs-branch": A("branch", "green"),
    "vcs-branch-delete": A("branch", None, "minus", "red"),
    "vcs-pull": A("branch", None, "arrow-down", "green"),
    "vcs-push": A("branch", None, "arrow-up", "blue"),
    "vcs-commit": A("act-pz-commit", "orange"),
    "vcs-commit-cvs-cervisia": A("act-pz-commit", None, "arrow-up", "blue"),
    "vcs-update-cvs-cervisia": A("act-pz-commit", None, "arrow-down", "green"),
    "vcs-status-cvs-cervisia": A("act-pz-commit", None, "info", "blue"),
    "vcs-remove-cvs-cervisia": A("act-pz-commit", None, "cross", "red"),
    "vcs-diff": A("act-pz-diff"),
    "vcs-diff-cvs-cervisia": A("act-pz-diff", None, "eye", "blue"),
    "vcs-merge": A("act-pz-merge", "violet"),
    "vcs-merge-request": A("act-pz-merge", None, "question", "violet"),
    "vcs-stash": A("box", None, "arrow-down", "violet"),
    "vcs-stash-pop": A("box", None, "arrow-up", "violet"),
    # views
    "view-barcode": A("barcode"),
    "view-barcode-add": A("barcode", None, "plus", "green"),
    "view-barcode-qr": A("qrcode"),
    "view-calendar": A("calendar"),
    "view-calendar-agenda": A("calendar", None, "clock", "blue"),
    "view-calendar-birthday": A("calendar", None, "gift", "red"),
    "view-calendar-journal": A("calendar", None, "book", "brown"),
    "view-calendar-list": A("calendar", None, "list-bullet", "blue"),
    "view-calendar-month": A("act-pz-cal-month"),
    "view-calendar-week": A("act-pz-cal-week"),
    "view-calendar-special-occasion": A("calendar", None, "star", "orange"),
    "view-calendar-tasks": A("calendar", None, "check", "green"),
    "view-calendar-time-spent": A("calendar", None, "hourglass", "brown"),
    "view-calendar-timeline": A("calendar", None, "act-pz-gantt", "blue"),
    "view-calendar-upcoming-days": A("calendar", None, "arrow-right", "green"),
    "view-calendar-upcoming-events": A("calendar", None, "arrow-right-double", "green"),
    "view-calendar-wedding-anniversary": A("calendar", None, "heart", "red"),
    "view-calendar-whatsnext": A("calendar", None, "next", "violet"),
    "view-catalog": A("book", "brown"),
    "view-certificate": A("act-pz-cert"),
    "view-certificate-add": A("act-pz-cert", None, "plus", "green"),
    "view-certificate-export": A("act-pz-cert", None, "arrow-up", "blue"),
    "view-certificate-export-secret": A("act-pz-cert", None, "lock", "red"),
    "view-certificate-export-server": A("act-pz-cert", None, "server", "blue"),
    "view-certificate-import": A("act-pz-cert", None, "arrow-down", "green"),
    "view-certificate-server-configure": A("act-pz-cert", None, "gear", "grey"),
    "view-certificate-sign": A("act-pz-cert", None, "pen", "blue"),
    "view-choose": A("grid", None, "chevron-down", "blue"),
    "view-close": A("panel", None, "cross", "red"),
    "view-left-close": A("sidebar", None, "cross", "red"),
    "view-left-new": A("sidebar", None, "plus", "green"),
    "view-right-close": A("act-pz-sidebar-r", None, "cross", "red"),
    "view-right-new": A("act-pz-sidebar-r", None, "plus", "green"),
    "view-currency-list": A("money", None, "list-bullet", "green"),
    "view-file-columns": A("columns"),
    "view-filter": A("filter"),
    "view-financial-budget": A("chart-pie", "green"),
    "view-financial-category": A("tag", "green"),
    "view-financial-category-add": A("tag", "green", "plus", "green"),
    "view-financial-category-delete": A("tag", "green", "minus", "red"),
    "view-financial-category-edit": A("tag", "green", "pencil", "blue"),
    "view-financial-category-expense": A("tag", "green", "arrow-down", "red"),
    "view-financial-category-income": A("tag", "green", "arrow-up", "green"),
    "view-financial-list": A("list", None, "money", "green"),
    "view-financial-transfer-reconcile": A("repeat", "green", "magnifier", "blue"),
    "view-financial-transfer-reconciled": A("repeat", "green", "check", "green"),
    "view-financial-transfer-unreconciled": A("repeat", "green", "cross", "red"),
    "view-form": A("act-pz-form"),
    "view-form-action": A("act-pz-form", None, "lightning", "orange"),
    "view-fullscreen": A("fullscreen"),
    "view-restore": A("restore-screen"),
    "view-grid": A("grid"),
    "view-group": A("act-pz-grouped"),
    "view-hidden": A("eye-off", "grey"),
    "view-visible": A("eye", "blue"),
    "view-private": A("eye-off", None, "lock", "red"),
    "view-history": A("history"),
    "view-institution": A("bank", "green"),
    "view-institution-add": A("bank", "green", "plus", "green"),
    "view-institution-delete": A("bank", "green", "minus", "red"),
    "view-institution-edit": A("bank", "green", "pencil", "blue"),
    "view-list-details": A("act-pz-list-details"),
    "view-list-icons": A("act-pz-list-icons"),
    "view-list-text": A("lines"),
    "view-list-tree": A("tree"),
    "view-media-config": A("music", None, "gear", "grey"),
    "view-media-equalizer": A("act-pz-eq"),
    "view-media-lyrics": A("act-pz-lyrics"),
    "view-media-playlist": A("list-bullet", None, "music", "blue"),
    "view-media-title": A("music", None, "text", "blue"),
    "view-multiple-objects": A("group", "blue"),
    "view-object-histogram-linear": A("histogram"),
    "view-object-histogram-logarithmic": A("act-pz-hist-log"),
    "view-pages-continuous": A("act-pz-pages-cont"),
    "view-pages-facing": A("act-pz-pages-facing"),
    "view-pages-facing-first-centered": A("act-pz-pages-first"),
    "view-pages-overview": A("act-pz-pages-overview"),
    "view-pim-notes": A("sticky-note"),
    "view-pim-tasks-pending": A("clipboard-check", None, "clock", "orange"),
    "view-presentation": A("presentation"),
    "view-preview": A("picture", None, "magnifier", "blue"),
    "view-readermode": A("book", "blue"),
    "view-readermode-active": A("book", "blue", "check", "green"),
    "view-refresh": A("refresh", "green"),
    "view-sidetree": A("act-pz-sidetree"),
    "view-sort": A("sort"),
    "view-sort-ascending": A("act-pz-sort-asc"),
    "view-sort-descending": A("act-pz-sort-desc"),
    "view-sort-ascending-name": A("act-pz-sort-az"),
    "view-sort-descending-name": A("act-pz-sort-za"),
    "view-split-effect": A("act-pz-splitview"),
    "view-unsplit-effect": A("act-pz-splitview", None, "cross", "grey"),
    "view-split-left-right": A("act-pz-split-lr"),
    "view-split-top-bottom": A("act-pz-split-tb"),
    "view-statistics": A("chart-bar"),
    "view-task": A("clipboard-check"),
    "view-task-child": A("clipboard-check", None, "act-pz-child", "blue"),
    "view-time-schedule-baselined": A("act-pz-gantt", None, "flag", "blue"),
    "view-time-schedule-baselined-remove": A("act-pz-gantt", None, "cross", "red"),
    "view-time-schedule-calculus": A("act-pz-gantt", None, "sigma", "violet"),
    "view-time-schedule-child-insert": A("act-pz-gantt", None, "act-pz-child", "green"),
    "view-time-schedule-edit": A("act-pz-gantt", None, "pencil", "blue"),
    "view-time-schedule-insert": A("act-pz-gantt", None, "plus", "green"),
    "view-web-browser-dom-tree": A("globe", None, "code", "blue"),
    "virtual-desktops": A("workspaces"),
    "wallet-closed": A("act-pz-wallet"),
    "wallet-open": A("act-pz-wallet-open"),
    "widget-alternatives": A("square", None, "repeat", "blue"),
    # windows
    "window": A("window"),
    "window-close": A("window-close"),
    "window-focus": A("window", None, "target", "blue"),
    "window-list": A("windows", None, "menu", "blue"),
    "window-new": A("window", None, "plus", "green"),
    "window-next": A("window", None, "arrow-right", "blue"),
    "window-previous": A("window", None, "arrow-left", "blue"),
    "window-pin": A("window", None, "pin", "blue"),
    "window-unpin": A("window", None, "pin", "grey"),
    "window-restore": A("windows"),
    "window-minimize-pip": A("act-pz-pip", None, "arrow-down", "blue"),
    "window-restore-pip": A("act-pz-pip", None, "arrow-up", "blue"),
    # xml
    "xml-attribute-delete": A("code", "orange", "minus", "red"),
    "xml-element-new": A("code", "orange", "plus", "green"),
    "xml-node-delete": A("code", "orange", "cross", "red"),
    "xml-text-new": A("code", "orange", "text", "blue"),
    # zoom
    "zoom": A("magnifier"),
    "zoom-in": A("zoom-in"),
    "zoom-out": A("zoom-out"),
    "zoom-in-x": A("zoom-in", None, "act-pz-harrows", "blue"),
    "y-zoom-in": A("zoom-in", None, "act-pz-varrows", "blue"),
    "zoom-out-x": A("zoom-out", None, "act-pz-harrows", "blue"),
    "zoom-out-y": A("zoom-out", None, "act-pz-varrows", "blue"),
    "zoom-fit-best": A("magnifier", None, "fullscreen", "blue"),
    "zoom-fit-width": A("magnifier", None, "act-pz-harrows", "blue"),
    "zoom-fit-height": A("magnifier", None, "act-pz-varrows", "blue"),
    "zoom-next": A("magnifier", None, "arrow-right", "blue"),
    "zoom-previous": A("magnifier", None, "arrow-left", "blue"),
    "zoom-original": A("magnifier", None, "act-pz-one", "blue"),
    "zoom-pixels": A("magnifier", None, "grid", "blue"),
}

SPEC.update({k: A(v) for k, v in SNAP.items()})


@reg("act-pz-shear-v")
def _(c, k): S(c, "M5 8 L19 3 V16 L5 21 Z", k)


# ---- financial accounts (KMyMoney) ------------------------------------------------------
ACCOUNTS = {"": "act-pz-coins", "-asset": "house", "-cash": "money", "-checking": "act-pz-cheque",
            "-credit-card": "act-pz-card", "-investment": "chart-line", "-investment-security": "chart-bar",
            "-liability": "anchor", "-loan": "percent", "-savings": "act-pz-piggy"}
for _suffix, _g in ACCOUNTS.items():
    _n = "view-financial-account" + _suffix
    if _suffix:
        SPEC[_n] = A(_g, "green")
    SPEC[_n + "-closed"] = A(_g, "grey", "lock", "grey")
SPEC.update({
    "view-financial-account": A("act-pz-coins"),
    "view-financial-account-add": A("act-pz-coins", None, "plus", "green"),
    "view-financial-account-close": A("act-pz-coins", None, "cross", "orange"),
    "view-financial-account-delete": A("act-pz-coins", None, "minus", "red"),
    "view-financial-account-edit": A("act-pz-coins", None, "pencil", "blue"),
    "view-financial-account-reopen": A("act-pz-coins", None, "unlock", "green"),
})


# ---- drawings of their own ------------------------------------------------------------------
def _smiley_shape(c):
    c.circle(24, 24, 17, c.grad(c.lighten(c["yellow"], 0.3), c["yellow"]))
    glyph(c, "smile", 6, 6, 36, c["ink"], width=None if not c.small else 3.0)
    return True


def _zoom_ratio(text, big_first):
    def fn(c):
        glyph(c, "magnifier", 4, 4, 42, c["ink"], width=None if not c.small else 2.6)
        if not c.small:
            c.text(21.5, 25, text, 9, c["ink"])
        else:
            a, b = (9, 5) if big_first else (5, 9)
            c.rect(12, 21.5 - a / 2, a, a, c["blue"], 0, None)
            c.rect(23.5, 21.5 - b / 2, b, b, c["blue"], 0, None)
        return True
    return fn


CUSTOM = {f"paint-{k}": paint(k) for k in
          ("gradient-conic", "gradient-linear", "gradient-radial", "none", "pattern", "solid", "swatch", "unknown")}
CUSTOM = {k: paint(k.split("-")[-1]) for k in CUSTOM}
CUSTOM["smiley-shape"] = _smiley_shape
CUSTOM["zoom-1-to-2"] = _zoom_ratio("1:2", False)
CUSTOM["zoom-2-to-1"] = _zoom_ratio("2:1", True)


def mine(name):
    return bool(name) and name[0] not in "abcdefghijklmno"


def draw(name, c):
    if not mine(name):
        return None
    try:
        fn = CUSTOM.get(name)
        if fn:
            return fn(c)
        s = SPEC.get(name)
        if s is None:
            return None
        g, acc, badge, bc = s
        return action(c, g, acc, badge, bc)
    except Exception:  # noqa: BLE001
        return None
