"""fam_actions_af.py: toolbar actions whose name starts with a-f.

Families share a glyph and differ by badge, arrow or accent (README.md):
document-* a page, edit-* the editing tool, align-*/distribute-* the
geometry drawn on the 48 grid, format-* text formatting, filename-*
tokens as chips, code-* symbol tiles, debug-* the stepping arrows.
"""
from base import action
from glyphs import glyph, reg, S, F, O, D

ME = "abcdef"


# ---- helpers on the 48 grid ------------------------------------------------
def gl(c, name, col=None, x=6, y=6, s=36):
    """A glyph as action() draws it (heavier line when small)."""
    glyph(c, name, x, y, s, c[col] if col in c.w else (col or c["ink"]),
          width=None if not c.small else 108.0 / s)


def badge(c, name, bc="green"):
    col = c[bc] if bc in c.w else bc
    c.circle(36, 36, 9 if not c.small else 10.5, col, width=1.1)
    glyph(c, name, 29.5, 29.5, 13, "#ffffff", width=3.2 if not c.small else 4)


def tx(c, x, y, s, size, col=None, weight="bold", italic=False, anchor="middle"):
    c.text(x, y, s, size, c[col] if col in c.w else (col or c["ink"]), weight, anchor, italic)


def light(c, col, t=0.45):
    return c.grad(c.lighten(c[col], t), c[col])


def A(g, accent=None, b=None, bc=None, fill=None):
    return lambda c: action(c, g, accent, b, bc, fill)


def K(*fns):
    def run(c):
        for f in fns:
            f(c)
    return run


def Bd(name, bc="green"):
    return lambda c: badge(c, name, bc)


def G(name, col=None, x=6, y=6, s=36):
    return lambda c: gl(c, name, col, x, y, s)


# ---- glyphs of this family -------------------------------------------------
@reg("act-af-accept-signal")
def _(c, k): S(c, "M3 5 H21 V19 H3 L8.5 12 Z", k)
@reg("act-af-subtitle")
def _(c, k): S(c, "M3 5 H21 V19 H3 Z", k); S(c, "M7 13.5 H17 M9 16.5 H15", k, W2(c))
@reg("act-af-addressbook")
def _(c, k): S(c, "M6 3 H20 V21 H6 Z M3 7 H8 M3 12 H8 M3 17 H8", k); O(c, 13, 10, 2.6, k); S(c, "M9 18 C9 14 17 14 17 18", k)
@reg("act-af-col-adjust")
def _(c, k): S(c, "M4 3 V21 M20 3 V21", k); S(c, "M7.5 12 H16.5 M10 9.5 L7.5 12 L10 14.5 M14 9.5 L16.5 12 L14 14.5", k)
@reg("act-af-row-adjust")
def _(c, k): S(c, "M3 4 H21 M3 20 H21", k); S(c, "M12 7.5 V16.5 M9.5 10 L12 7.5 L14.5 10 M9.5 14 L12 16.5 L14.5 14", k)


def W2(c):
    return getattr(c, "_gw", 1.8) * 1.4


def _uml_boxes(c, k):
    S(c, "M2 8 H6 V16 H2 Z M18 8 H22 V16 H18 Z", k)
@reg("act-af-aggregation")
def _(c, k): _uml_boxes(c, k); S(c, "M6 12 H9 M18 12 L13.5 9 L9 12 L13.5 15 Z", k)
@reg("act-af-composition")
def _(c, k): _uml_boxes(c, k); S(c, "M6 12 H9", k); F(c, "M18 12 L13.5 9 L9 12 L13.5 15 Z", k, k)
@reg("act-af-association")
def _(c, k): _uml_boxes(c, k); S(c, "M6 12 H18", k)
@reg("act-af-dependency")
def _(c, k): _uml_boxes(c, k); S(c, "M6 12 H8 M10.5 12 H12.5 M15 12 H17.5 M14 9 L17.5 12 L14 15", k)
@reg("act-af-artifact")
def _(c, k): S(c, "M3 5 H21 V19 H3 Z", k); S(c, "M12 8 H15.5 L18 10.5 V16 H12 Z M15.5 8 V10.5 H18", k)
@reg("act-af-atmosphere")
def _(c, k): F(c, "M7 21 A5 5 0 0 1 17 21 Z", k); S(c, "M3.5 21 A8.5 8.5 0 0 1 20.5 21 M1 21 A11 11 0 0 1 23 21", k)
@reg("act-af-transition")
def _(c, k): F(c, "M10 9 H14 V15 H10 Z", k); S(c, "M3 5 H14 V15 H3 Z M10 9 H21 V19 H10 Z", k)
@reg("act-af-handset")
def _(c, k): F(c, "M6 3 L9.5 3.5 L11 8.5 L8.5 10.5 C9.5 12.5 11.5 14.5 13.5 15.5 L15.5 13 L20.5 14.5 L21 18 C21 19.5 19.5 21 18 21 C10 20.5 3.5 14 3 6 C3 4.5 4.5 3 6 3 Z", k)
@reg("act-af-hangup")
def _(c, k): F(c, "M2 15 C6 8 18 8 22 15 L20 18.5 L15.5 17 V13.5 C13 12.5 11 12.5 8.5 13.5 V17 L4 18.5 Z", k)
@reg("act-af-voicemail")
def _(c, k): O(c, 6.5, 12, 4, k); O(c, 17.5, 12, 4, k); S(c, "M6.5 16 H17.5", k)
@reg("act-af-category")
def _(c, k): O(c, 12, 6, 3.4, k); S(c, "M12 9.4 V12.5 M6 12.5 H18 M6 12.5 V15 M18 12.5 V15 M3 15 H9 V20.5 H3 Z M15 15 H21 V20.5 H15 Z", k)
@reg("act-af-charcoal")
def _(c, k): F(c, "M15 3 L21 9 L12 18 L6 12 Z", k); S(c, "M7 17 L4.5 20.5 M3 22 C6 19 9 23 13 21", k)
@reg("act-af-scope")
def _(c, k): S(c, "M3 5 H21 V19 H3 Z", k); S(c, "M5 15 C7 7 9 7 11 12 C13 17 15 17 17 10 L19 8", k)
@reg("act-af-fragment")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M3 9.5 H9 L11 7.5 V4", k); S(c, "M3 14.5 H6 M9 14.5 H12 M15 14.5 H18", k)
@reg("act-af-curve-conn")
def _(c, k): S(c, "M2 3 H8 V9 H2 Z M16 15 H22 V21 H16 Z M8 6 C16 6 8 18 16 18", k)
@reg("act-af-elbow-conn")
def _(c, k): S(c, "M2 3 H8 V9 H2 Z M16 15 H22 V21 H16 Z M8 6 H12 V18 H16", k)
@reg("act-af-coordinate")
def _(c, k): S(c, "M4 3 V20 H21", k); S(c, "M4 9 H6.5 M9 9 H11.5 M16 12 V14 M16 16.5 V18.5", k, W(c) * 0.7); D(c, 16, 9, 2.2, k)
@reg("act-af-cursor-cross")
def _(c, k): S(c, "M12 3 V9 M12 15 V21 M3 12 H9 M15 12 H21", k)
@reg("act-af-gauge")
def _(c, k): S(c, "M3.5 17 A9 9 0 1 1 20.5 17 M12 15 L16.5 8.5 M6 11 L7.5 12 M12 6 V7.5 M18 11 L16.5 12", k); D(c, 12, 15, 1.7, k)
@reg("act-af-dfrac")
def _(c, k): S(c, "M3 12 H21", k, W2(c)); S(c, "M8 3 H16 V9 H8 Z M8 15 H16 V21 H8 Z", k)
@reg("act-af-input")
def _(c, k): S(c, "M2 12 H15 V20 H2 Z M5 15 H6 M8.5 15 H9.5 M12 15 H12.5 M5 17.5 H12 M16.5 10 A2.75 2.75 0 0 1 22 10 V15 A2.75 2.75 0 0 1 16.5 15 Z M19.25 7.5 V11 M19.25 7 C19 4 14 5 13 2", k)
@reg("act-af-tiles")
def _(c, k): [S(c, f"M{x} {y - 4} L{x + 4} {y} L{x} {y + 4} L{x - 4} {y} Z", k) for x, y in ((7, 7), (17, 7), (7, 17), (17, 17))]
@reg("act-af-scroll")
def _(c, k): S(c, "M7 4 H19 A2 2 0 0 1 19 8 H17 V18 A2.5 2.5 0 0 1 14.5 20.5 H5 A2.2 2.2 0 0 1 5 16 H7 Z M10 9 H14 M10 12 H14 M10 15 H12.5", k)
@reg("act-af-xml")
def _(c, k): S(c, "M3 4 H21 V20 H3 Z M3 8 H21", k); S(c, "M9 11 L6 14 L9 17 M15 11 L18 14 L15 17 M13 10.5 L11 17.5", k)
@reg("act-af-stem")
def _(c, k): S(c, "M3 20 H21 M6 20 V12 M10 20 V6 M14 20 V10 M18 20 V15", k); [D(c, x, y, 1.8, k) for x, y in ((6, 12), (10, 6), (14, 10), (18, 15))]
@reg("act-af-graph")
def _(c, k): S(c, "M6.5 7 L17.5 7 M5.5 8.5 L10.5 17 M18.5 8.5 L13.5 17 M19 9 V15", k); [O(c, x, y, 2.3, k) for x, y in ((5, 6), (19, 6), (12, 19), (19, 17))]
@reg("act-af-digraph")
def _(c, k):
    S(c, "M7.5 6 H16 M5.5 8.5 L10 15.5 M18.5 8.5 L14 15.5", k)
    F(c, "M17 6 L14 4.2 V7.8 Z M10.8 17 L8 15.6 L11 13.8 Z M13.2 17 L16 15.6 L13 13.8 Z", k, k)
    [O(c, x, y, 2.3, k) for x, y in ((5, 6), (19, 6), (12, 19))]
@reg("act-af-quake")
def _(c, k): S(c, "M2 12 H5 L7.5 7 L10 17 L12 3 L14 21 L16 8 L18 14.5 L19.5 12 H22", k)
@reg("act-af-bomb")
def _(c, k): D(c, 10, 14, 7, k); S(c, "M14.5 8.5 L16.5 6.5 C17.5 5.5 18.5 6 19 5", k); S(c, "M21 2 V3.5 M21 6.5 V8 M18 5 H19 M23 5 H24", k, W(c) * 0.7)
@reg("act-af-backspace")
def _(c, k): S(c, "M8 5 H21 V19 H8 L2 12 Z M11.5 9 L17 14.5 M17 9 L11.5 14.5", k)
@reg("act-af-field-clear")
def _(c, k): S(c, "M2 7 H22 V17 H2 Z M5 10 V14", k); S(c, "M14 9.5 L19 14.5 M19 9.5 L14 14.5", k)
@reg("act-af-shredder")
def _(c, k): S(c, "M3 10 H21 V14 H3 Z M6 10 V3 H18 V10 M6 14 V20 M9 14 V21.5 M12 14 V19 M15 14 V21.5 M18 14 V20", k)
@reg("act-af-find")
def _(c, k): O(c, 10, 10, 6.5, k, c.lighten(c["cyan"], 0.6)); S(c, "M15 15 L20.5 20.5", k, W(c) * 1.6)
@reg("act-af-guides")
def _(c, k): S(c, "M3 3 H21 V21 H3 Z", k); S(c, "M9 3 V21 M3 15 H21", c["blue"], W(c) * 0.9)
@reg("act-af-face")
def _(c, k): S(c, "M3 8 V3 H8 M16 3 H21 V8 M21 16 V21 H16 M8 21 H3 V16", k); O(c, 12, 12, 5, k); D(c, 10.2, 11, 0.9, k); D(c, 13.8, 11, 0.9, k); S(c, "M10 14 C11 15 13 15 14 14", k, W(c) * 0.7)
@reg("act-af-linewidth")
def _(c, k): S(c, "M4 5 H20", k, 0.9); S(c, "M4 10 H20", k, 1.9); S(c, "M4 17 H20", k, 4)
@reg("act-af-opacity")
def _(c, k): S(c, "M4 4 H20 V20 H4 Z", k); F(c, "M4 20 L20 4 V20 Z", k); F(c, "M4 4 H8 V8 H4 Z M12 4 H16 V8 H12 Z M8 8 H12 V12 H8 Z M4 12 H8 V16 H4 Z", k)
@reg("act-af-entity")
def _(c, k): S(c, "M4 4 H20 V20 H4 Z M4 9 H20 M7 13 H16 M7 16.5 H13", k)
@reg("act-af-ledger")
def _(c, k): F(c, "M3 9 H21 V14 H3 Z", c.lighten(c["blue"], 0.5)); S(c, "M3 4 H21 V20 H3 Z M3 9 H21 M3 14 H21 M9 4 V20", k)
@reg("act-af-warn")
def _(c, k): S(c, "M12 3 L22 20 H2 Z", k); S(c, "M12 9 V14", k, W2(c)); D(c, 12, 17, 1.2, k)
@reg("act-af-swap")
def _(c, k): S(c, "M2 3 H9 V10 H2 Z M15 14 H22 V21 H15 Z M11 6.5 H18.5 V11 M16.5 9 L18.5 11.5 L20.5 9 M13 17.5 H5.5 V13 M3.5 15 L5.5 12.5 L7.5 15", k)
@reg("act-af-swap-cw")
def _(c, k): S(c, "M3 3 H9 V9 H3 Z M15 15 H21 V21 H15 Z M12 4 A8 8 0 0 1 20 12 M18 10 L20 12.5 L22 10 M12 20 A8 8 0 0 1 4 12 M2 14 L4 11.5 L6 14", k)
@reg("act-af-zorder")
def _(c, k): S(c, "M3 7 H13 V17 H3 Z", k); F(c, "M8 3 H18 V13 H8 Z", c.lighten(c["blue"], 0.4), k); S(c, "M20 9 V21 M18 11 L20 9 L22 11 M18 19 L20 21 L22 19", k)
@reg("act-af-star-outline")
def _(c, k):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 9 if i % 2 == 0 else 4
        pts.append(f"{12 + r * math.cos(a):.2f} {12.8 + r * math.sin(a):.2f}")
    S(c, "M" + " L".join(pts) + " Z", k)
@reg("act-af-pentagram")
def _(c, k):
    import math
    p = [(12 + 9.5 * math.cos(-math.pi / 2 + i * 4 * math.pi / 5), 12.8 + 9.5 * math.sin(-math.pi / 2 + i * 4 * math.pi / 5)) for i in range(5)]
    S(c, "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in p) + " Z", k)
@reg("act-af-coin")
def _(c, k): O(c, 12, 12, 8.5, k); O(c, 12, 12, 5, k)
@reg("act-af-forecast")
def _(c, k): S(c, "M4 3 V20 H21 M6 16 L10 12 L13 14", k); S(c, "M15 11.5 L16.5 10 M18 8.5 L20 6.5", k)
@reg("act-af-torch")
def _(c, k): S(c, "M2 9.5 H11 L15 6.5 V17.5 L11 14.5 H2 Z M6 12 H8", k)
@reg("act-af-torch-on")
def _(c, k): S(c, "M2 9.5 H11 L15 6.5 V17.5 L11 14.5 H2 Z M6 12 H8 M17.5 8 L21.5 5.5 M18 12 H23 M17.5 16 L21.5 18.5", k)
@reg("act-af-flower")
def _(c, k):
    import math
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        O(c, 12 + 5.5 * math.cos(a), 12 + 5.5 * math.sin(a), 3.6, k)
    D(c, 12, 12, 2.6, k)
@reg("act-af-food")
def _(c, k): O(c, 13, 12, 6.5, k); O(c, 13, 12, 3.6, k); S(c, "M3 3 V8 A1.5 1.5 0 0 0 6 8 V3 M4.5 8 V21 M22 3 C19.5 5 19.5 11 21.5 12 V21", k)
@reg("act-af-fork")
def _(c, k): O(c, 6, 5, 2.2, k); O(c, 18, 5, 2.2, k); O(c, 12, 19, 2.2, k); S(c, "M6 7.2 V9 C6 12 12 12 12 14 V16.8 M18 7.2 V9 C18 12 12 12 12 14", k)
@reg("act-af-radical")
def _(c, k): S(c, "M2 13 L5 12 L8.5 20 L12.5 4 H22", k); S(c, "M14 9.5 L19.5 16 M19.5 9.5 L14 16", k)
@reg("act-af-quote")
def _(c, k): F(c, "M4 5 H9 V10 L7 14 H5 L6.5 10 H4 Z M11 5 H16 V10 L14 14 H12 L13.5 10 H11 Z", k); S(c, "M4 18 H20 M18 7 H20 M18 11 H20", k)
@reg("act-af-pilcrow")
def _(c, k): S(c, "M11 4 V20 M15 4 V20 M10 4 H17", k); F(c, "M11 4 A4 4 0 0 0 11 12 Z", k, k)
@reg("act-af-chip-bars")
def _(c, k): S(c, "M3 5 H21 V19 H3 Z", k)
@reg("act-af-uppercase")
def _(c, k): S(c, "M2 19 L6.5 6 L11 19 M3.6 14.5 H9.4 M13 19 L17.5 6 L22 19 M14.6 14.5 H20.4", k)
@reg("act-af-cuboid")
def _(c, k): S(c, "M3 8 H15 V20 H3 Z M3 8 L8 3 H20 L15 8 M20 3 V15 L15 20", k)
@reg("act-af-donut")
def _(c, k): O(c, 12, 12, 8.5, k); O(c, 12, 12, 3.8, k)
@reg("act-af-ellipse-arc")
def _(c, k): S(c, "M3 12 A9 6 0 1 1 12 18", k); D(c, 3, 12, 1.4, k); D(c, 12, 18, 1.4, k)
@reg("act-af-ellipse-seg")
def _(c, k): S(c, "M12 12 L3 12 A9 6 0 1 1 12 18 Z", k)
@reg("act-af-freehand")
def _(c, k): S(c, "M3 17 C5 10 8 10 9 14 C10 18 13 18 14 12 C15 7 18 6 21 9", k)
@reg("act-af-cross-shape")
def _(c, k): S(c, "M9 3 H15 V9 H21 V15 H15 V21 H9 V15 H3 V9 H9 Z", k)
@reg("act-af-number")
def _(c, k): O(c, 12, 12, 8.5, k); S(c, "M10 9 L12.5 7 V17 M10 17 H15", k)
@reg("act-af-polyline")
def _(c, k): S(c, "M3 18 L8 7 L13 15 L17 5 L21 12", k); [D(c, x, y, 1.4, k) for x, y in ((3, 18), (8, 7), (13, 15), (17, 5), (21, 12))]
@reg("act-af-rrect")
def _(c, k): S(c, "M8 5 H16 A4 4 0 0 1 20 9 V15 A4 4 0 0 1 16 19 H8 A4 4 0 0 1 4 15 V9 A4 4 0 0 1 8 5 Z", k)
@reg("act-af-inv-corners")
def _(c, k): S(c, "M8 4 H16 A4 4 0 0 0 20 8 V16 A4 4 0 0 0 16 20 H8 A4 4 0 0 0 4 16 V8 A4 4 0 0 0 8 4 Z", k)
@reg("act-af-calligraphic")
def _(c, k): F(c, "M3 19 C6 12 9 8 14 6 L15 8 C10 10 7 14 5 20 Z", k); S(c, "M14 9 L19 4 L21 6 L16 11 Z", k)
@reg("act-af-watercolor")
def _(c, k): S(c, "M20 3 L12 11 M12 11 C9 10 7 12 7 14 C7 16 6 17 5 18 C9 18 12 17 12 14 Z", k); S(c, "M18 13 C16 16 15.5 18 15.5 19 A2.5 2.5 0 0 0 20.5 19 C20.5 18 20 16 18 13 Z", k)
@reg("act-af-highlight")
def _(c, k): F(c, "M3 17 H21 V21 H3 Z", c["yellow"]); S(c, "M15 3 L20 8 L13 15 L9.5 15 L8 13.5 V10 Z M8 13.5 L5.5 16", k)
@reg("act-af-text-tool")
def _(c, k): S(c, "M3 20 L9 4 L15 20 M5.3 14 H12.7 M19 4 V20 M17 4 H21 M17 20 H21", k)
@reg("act-af-spark")
def _(c, k): S(c, "M12 3 V8 M12 16 V21 M3 12 H8 M16 12 H21 M5.5 5.5 L9 9 M15 15 L18.5 18.5 M5.5 18.5 L9 15 M15 9 L18.5 5.5", k)


def tri(c, k, pts):
    S(c, "M" + " L".join(f"{x} {y}" for x, y in pts) + " Z", k)


for _i, _pts in enumerate((((4, 4), (20, 20), (4, 20)), ((20, 4), (20, 20), (4, 20)),
                           ((4, 4), (20, 4), (20, 20)), ((4, 4), (20, 4), (4, 20))), 1):
    reg(f"act-af-tri{_i}")(lambda c, k, p=_pts: tri(c, k, p))
for _i, _d in enumerate(("M4 16 A8 8 0 0 1 20 16 Z", "M8 4 A8 8 0 0 1 8 20 Z",
                         "M4 8 A8 8 0 0 0 20 8 Z", "M16 4 A8 8 0 0 0 16 20 Z"), 1):
    reg(f"act-af-half{_i}")(lambda c, k, d=_d: S(c, d, k))


def W(c):
    return getattr(c, "_gw", 1.8)


# ---- align / distribute geometry (48 grid) ---------------------------------
def _t(r, v):
    return (r[1], r[0], r[3], r[2]) if v else r


def _box(c, r, v, col="blue"):
    x, y, w, h = _t(r, v)
    c.rect(x, y, w, h, light(c, col), 1.5)


def _ln(c, x1, y1, x2, y2, v, col="red", width=2.4):
    if v:
        x1, y1, x2, y2 = y1, x1, y2, x2
    c.line(f"M{x1:g} {y1:g} L{x2:g} {y2:g}", c[col] if col in c.w else col, width)


def _anchor(c, r, v):
    x, y, w, h = _t(r, v)
    c.rect(x, y, w, h, c.lighten(c["grey"], 0.65), 1.5, c["grey"])


ALIGN = {
    "left": dict(line=8, boxes=[(8, 9, 30, 11), (8, 27, 18, 11)]),
    "right": dict(line=40, boxes=[(10, 9, 30, 11), (22, 27, 18, 11)]),
    "center": dict(line=24, boxes=[(9, 9, 30, 11), (15, 27, 18, 11)]),
    "left-out": dict(anchor=(27, 5, 16, 38), line=27, boxes=[(5, 10, 22, 10), (13, 28, 14, 10)]),
    "right-out": dict(anchor=(5, 5, 16, 38), line=21, boxes=[(21, 10, 22, 10), (21, 28, 14, 10)]),
}


def align(mode, v=False, b=None, bc="grey"):
    def run(c):
        if mode == "node":
            pts = [(6, 4), (14, 4), (24, 10), (38, 17), (24, 24), (10, 31), (24, 38), (32, 43), (42, 44)]
            if v:
                pts = [(y, x) for x, y in pts]
            p = pts
            _ln(c, 24, 3, 24, 45, v, "red", 2.2)
            c.path(f"M{p[0][0]} {p[0][1]} Q{p[1][0]} {p[1][1]} {p[2][0]} {p[2][1]} Q{p[3][0]} {p[3][1]} {p[4][0]} {p[4][1]} "
                   f"Q{p[5][0]} {p[5][1]} {p[6][0]} {p[6][1]} Q{p[7][0]} {p[7][1]} {p[8][0]} {p[8][1]}", "none")
            for q in (p[2], p[4], p[6]):
                c.rect(q[0] - 3.5, q[1] - 3.5, 7, 7, c["blue"], 0, width=1.2)
        else:
            m = ALIGN[mode]
            if "anchor" in m:
                _anchor(c, m["anchor"], v)
            for r in m["boxes"]:
                _box(c, r, v)
            _ln(c, m["line"], 3, m["line"], 45, v)
        if b:
            badge(c, b, bc)
    return run


def align_baseline(v):
    def run(c):
        if v:      # letters side by side sitting on one line
            _ln(c, 4, 34, 44, 34, False)
            tx(c, 15, 34, "A", 24); tx(c, 33, 34, "g", 24)
            if c.small:
                c.rect(8, 16, 12, 18, light(c, "blue"), 1.5); c.rect(26, 24, 12, 10, light(c, "blue"), 1.5)
        else:      # text anchors on one vertical line
            _ln(c, 12, 4, 12, 44, False)
            tx(c, 12, 21, "Abc", 16, anchor="start"); tx(c, 12, 40, "Ag", 16, anchor="start")
            if c.small:
                c.rect(12, 8, 26, 12, light(c, "blue"), 1.5); c.rect(12, 27, 16, 12, light(c, "blue"), 1.5)
            for y in (21, 40):
                c.circle(12, y, 2.5 if not c.small else 3.5, c["red"], None)
    return run


DBOX = [(4, 14, 8, 18), (18, 8, 11, 30), (35, 17, 8, 12)]


def distribute(mode, v=False, b=None, bc="grey"):
    def run(c):
        if mode == "page":
            x, y, w, h = _t((2, 4, 44, 40), v)
            c.rect(x, y, w, h, c.grad(c["page"]), 1.5, c["grey"])
        if mode == "margin":
            for xx in (2, 46):
                _ln(c, xx, 4, xx, 44, v, "grey", 1.6)
        if mode == "node":
            pts = [(6, 30), (18, 12), (30, 32), (42, 14)]
            if v:
                pts = [(y, x) for x, y in pts]
            c.path("M" + " L".join(f"{x} {y}" for x, y in pts), "none")
            for (x, y), (ox, oy) in zip(pts, [(6, 30), (18, 12), (30, 32), (42, 14)]):
                c.rect(x - 3, y - 3, 6, 6, c["blue"], 0, width=1)
            for ox in (6, 18, 30, 42):
                _ln(c, ox, 40, ox, 45, v, "red", 2)
        else:
            for r in DBOX:
                _box(c, r, v)
        guides = {"left": (4, 18, 35), "center": (8, 23.5, 39), "right": (12, 29, 43)}.get(mode)
        if guides:
            for gx in guides:
                _ln(c, gx, 3, gx, 45, v, "red", 1.6)
        if mode in ("equal", "margin"):
            gaps = [(12, 18), (29, 35)] + ([(2, 4), (43, 46)] if mode == "margin" else [])
            for a, z in gaps:
                x, y, w, h = _t((a, 20, z - a, 8), v)
                c.rect(x, y, w, h, c["red"], 0, None)
        if mode == "plain":
            _ln(c, 6, 43, 42, 43, v, "ink", 1.8)
            _ln(c, 6, 43, 10, 40, v, "ink", 1.8); _ln(c, 6, 43, 10, 46, v, "ink", 1.8)
            _ln(c, 42, 43, 38, 40, v, "ink", 1.8); _ln(c, 42, 43, 38, 46, v, "ink", 1.8)
        if b:
            badge(c, b, bc)
    return run


def distribute_baseline(v):
    def run(c):
        if v:
            for y in (14, 27, 40):
                _ln(c, 4, y, 44, y, False, "red", 1.6)
            tx(c, 10, 14, "A", 12, anchor="start"); tx(c, 18, 27, "Ag", 12, anchor="start"); tx(c, 8, 40, "Abc", 12, anchor="start")
            if c.small:
                c.rect(10, 6, 14, 8, light(c, "blue"), 1); c.rect(18, 19, 18, 8, light(c, "blue"), 1); c.rect(8, 32, 26, 8, light(c, "blue"), 1)
        else:
            for x in (8, 22, 36):
                _ln(c, x, 4, x, 44, False, "red", 1.6)
            for x, y, s in ((8, 18, "A"), (22, 34, "B"), (36, 24, "C")):
                tx(c, x, y, s, 14, anchor="start")
                if c.small:
                    c.rect(x, y - 10, 8, 10, light(c, "blue"), 1)
        if c.small:
            badge(c, "text", "grey")
    return run


def scatter(extra=None, b=None, bc="grey"):
    def run(c):
        for r in ((5, 6, 14, 10), (24, 4, 16, 12), (8, 24, 12, 14), (26, 24, 14, 8)):
            c.rect(*r, light(c, "blue"), 1.5)
        if extra:
            extra(c)
        if b:
            badge(c, b, bc)
    return run


def overlaps(c):
    c.rect(4, 8, 22, 18, light(c, "blue"), 1.5)
    c.rect(16, 18, 22, 18, light(c, "cyan"), 1.5)


def unclump(c):
    for r in ((3, 3, 12, 10), (33, 3, 12, 10), (3, 35, 12, 10), (33, 35, 12, 10)):
        c.rect(*r, light(c, "blue"), 1.5)
    c.circle(24, 24, 3, c["red"], None)
    for d in ("M20 20 L15 15", "M28 20 L33 15", "M20 28 L15 33", "M28 28 L33 33"):
        c.line(d, "ink", 2)


def escape(dirs):
    heads = {"up": "M24 18 V5 M19 10 L24 5 L29 10", "down": "M24 30 V43 M19 38 L24 43 L29 38",
             "left": "M18 24 H5 M10 19 L5 24 L10 29", "right": "M30 24 H43 M38 19 L43 24 L38 29"}

    def run(c):
        for d in dirs:
            c.line(heads[d], c["blue"], 2.6)
        c.rect(19, 19, 10, 10, c.grad(c["page"]), 1, width=1.6)
        c.path("M21 21 L27 27 M27 21 L21 27", "none", c["red"], 1.8)
    return run


# ---- tables and borders ----------------------------------------------------
TX, TY = (6, 18, 30, 42), (8, 19, 30, 41)


def table(cells=(), col="blue", merge=None, split=None, b=None, bc="green"):
    """A 3 x 3 table; cells: (col, row) to fill; merge: ((c0,r),(c1,r))
    drawn without the divider; split: a cell with a red divider."""
    def run(c):
        c.rect(6, 8, 36, 33, c.grad(c["page"]), 1, None)
        for (i, j) in cells:
            c.rect(TX[i], TY[j], TX[i + 1] - TX[i], TY[j + 1] - TY[j], light(c, col, 0.35), 0, None)
        c.rect(6, 8, 36, 33, "none", 1)
        lines = "".join(f"M{x} 8 V41 " for x in TX[1:3]) + "".join(f"M6 {y} H42 " for y in TY[1:3])
        c.path(lines, "none", "ink", 1.2)
        if merge:
            (i0, j), (i1, _) = merge
            c.rect(TX[i0], TY[j], TX[i1 + 1] - TX[i0], TY[j + 1] - TY[j], light(c, col, 0.35), 0, "ink", 1.2)
        if split:
            i, j = split
            xm = (TX[i] + TX[i + 1]) / 2
            c.line(f"M{xm} {TY[j]} V{TY[j + 1]}", c["red"], 2.2)
        if b:
            badge(c, b, bc)
    return run


EDGES = {"L": "M8 8 V40", "R": "M40 8 V40", "T": "M8 8 H40", "B": "M8 40 H40",
         "H": "M8 24 H40", "V": "M24 8 V40", "D1": "M8 40 L40 8", "D2": "M8 8 L40 40"}


def border(on):
    def run(c):
        c.rect(8, 8, 32, 32, c.grad(c["page"]), 0, None)
        for e, d in EDGES.items():
            if e.startswith("D"):
                continue
            if e not in on:
                c.path(d, "none", c["grey"], 1 if not c.small else 0.8)
        for e in on:
            c.path(EDGES[e], "none", "ink", 3.2)
    return run


def border_style(c):
    c.path("M6 10 H42", "none", "ink", 1.4)
    c.path("M6 19 H10 M14 19 H18 M22 19 H26 M30 19 H34 M38 19 H42", "none", "ink", 2.2)
    c.path("M6 28 H8 M12 28 H14 M18 28 H20 M24 28 H26 M30 28 H32 M36 28 H38", "none", "ink", 2.2)
    c.path("M6 36 H42 M6 40 H42", "none", "ink", 1.6)


# ---- nodes (path editing) --------------------------------------------------
def _sq(c, x, y, col, s=6):
    s = s * (1.7 if c.small else 1)
    c.rect(x - s / 2, y - s / 2, s, s, col, 0, width=1.2)


CURVE = "M5 36 C10 14 18 12 24 22 C30 32 38 34 43 12"


def nodes(kind):
    """Inkscape's node tools. Small: the same picture with bigger nodes,
    fewer and heavier lines (handles thick, curves simpler)."""
    def run(c):
        blue, white, sm = c["blue"], "#ffffff", c.small
        hw = 1.4 if not sm else 1.6           # handle lines (x1.6 when small)
        hr = 2.5 if not sm else 3.6           # handle ends
        if kind in ("add", "insert", "remove"):
            c.path(CURVE if not sm else "M5 36 C10 14 18 14 24 22 C30 30 36 30 40 14", "none")
            if not sm:
                _sq(c, 5, 36, white); _sq(c, 43, 12, white)
            _sq(c, 24, 22, c["green"] if kind != "remove" else c["red"], 7)
        elif kind == "break":
            c.path("M5 36 C10 14 17 12 21 18", "none"); c.path("M27 26 C31 32 38 34 43 12", "none")
            _sq(c, 19 if sm else 21, 17 if sm else 18, blue); _sq(c, 29 if sm else 27, 27 if sm else 26, blue)
            if not sm:
                c.line("M17 30 L22 25 M31 14 L26 19", c["red"], 2)
        elif kind == "join":
            c.path("M5 36 C8 20 14 18 24 24", "none"); c.path("M43 36 C40 20 34 18 24 24", "none")
            _sq(c, 24, 24, blue, 7)
            c.line("M14 10 L20 16 M20 11 V16 H15 M34 10 L28 16 M28 11 V16 H33", c["green"], 2)
        elif kind in ("connect", "disconnect"):
            c.path("M4 6 C4 18 8 24 14 24", "none"); c.path("M44 6 C44 18 40 24 34 24", "none")
            if kind == "connect":
                c.line("M19 24 H29", c["green"], 3.2)
            else:
                c.line("M20 19 L28 29 M28 19 L20 29", c["red"], 2.4)
            _sq(c, 14, 24, blue); _sq(c, 34, 24, blue)
        elif kind == "corner":
            c.path("M4 42 L24 12 L44 42", "none")
            c.line("M24 12 L10 5 M24 12 L38 5", c["grey"], hw)
            z = 6 if not sm else 9
            c.path(f"M24 {12 - z} L{24 + z} 12 L24 {12 + z} L{24 - z} 12 Z", blue, width=1.2)
        elif kind in ("smooth", "symmetric"):
            c.path("M4 42 C8 16 40 16 44 42", "none")
            left = 6 if kind == "symmetric" else 16
            right = 42 if kind == "symmetric" else 44
            c.line(f"M{left} 22 H{right}", c["grey"], hw)
            c.circle(left, 22, hr, white, width=1.2); c.circle(right, 22, hr, white, width=1.2)
            if kind == "symmetric":
                c.line("M14 27 V32 M34 27 V32", c["ink"], 1.8)
            _sq(c, 24, 22, blue)
        elif kind in ("node-curve", "node-line", "seg-curve", "seg-line"):
            d = "M8 38 C8 10 40 10 40 38" if kind.endswith("curve") else "M8 38 L40 10"
            seg = kind.startswith("seg")
            c.path(d, "none", c["orange"] if seg else "ink", 3.4 if seg else None)
            col = white if seg else blue
            if kind.endswith("curve"):
                _sq(c, 8, 38, col, 7); _sq(c, 40, 38, col, 7)
            else:
                _sq(c, 8, 38, col, 7); _sq(c, 40, 10, col, 7)
        return True
    return run


# ---- UML relations: two classes and the line between them -----------------
def uml(kind):
    def run(c):
        sm = c.small
        for x in (3, 35):
            c.rect(x, 13, 10, 22, c.grad(c["page"]), 1.5)
            if not sm:
                c.line(f"M{x} 19 h10", "ink", 1)
        w = 2.2 if not sm else 2.0            # x1.6 when small
        dia = "M35 24 L26 17 L17 24 L26 31 Z"
        if kind == "association":
            c.line("M13 24 H35", "ink", w)
        elif kind in ("aggregation", "composition"):
            c.line("M13 24 H17", "ink", w)
            c.path(dia, "#ffffff" if kind == "aggregation" else c["ink"], "ink", w * 0.8)
        elif kind == "dependency":
            c.line("M13 24 H16 M20 24 H23 M27 24 H33" if not sm else "M13 24 H17 M23 24 H33", "ink", w)
            c.path("M27 17 L34 24 L27 31", "none", "ink", w)
        return True
    return run


def align_out_side(bottom):
    """Boxes beside the anchor, with their edge on the anchor's far edge
    (the top-out/bottom-out of the horizontal row)."""
    def run(c):
        _anchor(c, (27, 14, 17, 20), False)
        if bottom:      # tops of the boxes on the anchor's bottom edge
            for r in ((4, 34, 10, 10), (16, 34, 9, 7)):
                _box(c, r, False)
            _ln(c, 3, 34, 45, 34, False)
        else:           # bottoms on the anchor's top edge
            for r in ((4, 4, 10, 10), (16, 7, 9, 7)):
                _box(c, r, False)
            _ln(c, 3, 14, 45, 14, False)
        return True
    return run


# ---- text and chips --------------------------------------------------------
def letters(s, size=22, y=32, col=None, italic=False, x=24, weight="bold"):
    def run(c):
        c.text(x, y, s, size, c[col] if col in c.w else (col or c["ink"]), weight, "middle", italic)
    return run


def chip(text=None, size=20, inner=None, col="violet"):
    def run(c):
        c.rect(5, 11, 38, 26, c.grad(c.lighten(c[col], 0.7), c.lighten(c[col], 0.4)), 7)
        if text:
            c.text(24, 24 + size * 0.36, text, size, c["ink"])
        if inner:
            inner(c)
    return run


def moodbar(c):
    for i, col in enumerate(("red", "orange", "yellow", "green", "cyan", "blue", "violet")):
        c.rect(9 + i * 4.3, 16, 4.3, 16, c[col], 0, None)


def code_tile(letter, col, size=24):
    def run(c):
        c.rect(7, 7, 34, 34, c.grad(c.lighten(c[col], 0.25), c.darken(c[col], 0.15)), 7)
        c.text(24, 24 + size * 0.36, letter, size, "#ffffff")
    return run


def swatch(fill):
    def run(c):
        f = c[fill] if fill in c.w else fill
        c.circle(36, 36, 9 if not c.small else 10.5, f, width=1.4)
    return run


def color_dots(c):
    for (x, y), col in zip(((17, 18), (31, 18), (24, 30)), ("red", "green", "blue")):
        c.circle(x, y, 10, c[col], width=1.2)


def hue_wheel(c):
    import math
    cols = ("red", "orange", "yellow", "green", "cyan", "blue", "violet")
    n = len(cols)
    for i, col in enumerate(cols):
        a0, a1 = 2 * math.pi * i / n - math.pi / 2, 2 * math.pi * (i + 1) / n - math.pi / 2
        x0, y0 = 24 + 17 * math.cos(a0), 24 + 17 * math.sin(a0)
        x1, y1 = 24 + 17 * math.cos(a1), 24 + 17 * math.sin(a1)
        c.path(f"M24 24 L{x0:.2f} {y0:.2f} A17 17 0 0 1 {x1:.2f} {y1:.2f} Z", c[col], None)
    c.circle(24, 24, 17, "none")
    c.circle(24, 24, 6, "#ffffff")


def channelmixer(c):
    for x, col, knob in ((12, "red", 14), (24, "green", 28), (36, "blue", 20)):
        c.line(f"M{x} 6 V42", "ink", 1.6)
        c.rect(x - 5, knob - 3.5, 10, 7, c[col], 1.5, width=1.2)


def gradient_rect(c):
    id_ = f"{c.tag}g{len(c.defs)}"
    c.defs.append(f'<linearGradient id="{id_}" x1="0" y1="0" x2="1" y2="0">'
                  f'<stop offset="0" stop-color="{c["red"]}"/><stop offset="0.5" stop-color="{c["yellow"]}"/>'
                  f'<stop offset="1" stop-color="{c["blue"]}"/></linearGradient>')
    c.rect(5, 10, 38, 28, f"url(#{id_})", 2)


def negative(c):
    c.rect(5, 9, 38, 30, c.grad(c.lighten(c["ink"], 0.25), c["ink"]), 2)
    c.path("M5 33 L17 21 L27 30 L31 26 L43 36", "none", "#ffffff", 2)
    c.circle(31, 17, 3, "#ffffff", None)


def emboss(c):
    c.rect(8, 8, 32, 32, c.grad(c["case"]), 1, None)
    c.path("M8 40 V8 H40", "none", "#ffffff", 3)
    c.path("M8 40 H40 V8", "none", c["case_dark"], 3)
    c.rect(8, 8, 32, 32, "none", 1)
    c.text(24, 31, "A", 20, c.darken(c["case"][1], 0.3))


def bordertool(c):
    c.rect(6, 6, 36, 36, c["orange"], 2)
    c.rect(13, 13, 22, 22, c.grad(c["page"]), 0)


def chroma(col):
    def run(c):
        c.circle(24, 24, 17, c.grad(c.lighten(c[col], 0.5), c[col]))
        c.path("M24 7 V41 M7 24 H41", "none", "#ffffff", 1.2)
        c.path("M14 30 L22 18 L30 26 L36 14", "none", "ink", 2.2)
    return run


def luma(c):
    c.rect(6, 8, 36, 32, c.grad("#ffffff", "#202020"), 2)
    c.path("M10 34 L18 28 L26 22 L36 12", "none", c["red"], 2.4)


def code_glyph_text(s, size):
    return lambda c: c.text(24, 30, s, size, c["ink"])


def depth(a, b_):
    def run(c):
        c.text(16, 20, a, 15, c["ink"])
        c.text(32, 42, b_, 15, c["ink"])
        c.line("M14 26 L24 34 M24 28 V34 H18", c["blue"], 2.4)
    return run


def precision(more):
    def run(c):
        c.text(23, 26, ".00" if more else ".0", 17, c["ink"])
        if more:
            c.line("M14 34 H34 M30 30 L34 34 L30 38", c["green"], 2.4)
        else:
            c.line("M34 34 H14 M18 30 L14 34 L18 38", c["red"], 2.4)
    return run


def fontsize(more):
    def run(c):
        c.text(18, 38, "A", 30, c["ink"])
        c.text(36, 38, "A", 16, c["ink"])
        arrow = "M38 6 V18 M34 10 L38 6 L42 10" if more else "M38 6 V18 M34 14 L38 18 L42 14"
        c.line(arrow, c["green"] if more else c["red"], 2.4)
    return run


def spacing(n):
    def run(c):
        gap = {1: 6, 2: 10, 3: 14}[n]
        y = 24 - gap * (1 if n < 3 else 1)
        rows = 4 if n == 1 else 3 if n == 2 else 3
        ys = [24 - gap * (rows - 1) / 2 + i * gap for i in range(rows)]
        for yy in ys:
            c.line(f"M17 {yy:g} H42", "ink", 2)
        c.line(f"M9 {ys[0]:g} V{ys[-1]:g} M6 {ys[0] + 3:g} L9 {ys[0]:g} L12 {ys[0] + 3:g} "
               f"M6 {ys[-1] - 3:g} L9 {ys[-1]:g} L12 {ys[-1] - 3:g}", c["blue"], 2)
        del y
    return run


def valign(pos):
    def run(c):
        c.rect(6, 6, 36, 36, c.grad(c["page"]), 2)
        y0 = {"top": 12, "center": 20, "bottom": 28}[pos]
        c.line(f"M12 {y0} H36 M12 {y0 + 8} H30", c["blue"], 3)
    return run


def script(sub):
    def run(c):
        c.text(19, 34, "X", 26, c["ink"])
        c.text(36, 42 if sub else 22, "2", 15, c["blue"])
    return run


def textdir(kind):
    def run(c):
        gl(c, "act-af-pilcrow", "ink", 4, 4, 28)
        if kind == "vertical":
            c.line("M38 8 V36 M34 32 L38 36 L42 32", c["blue"], 2.4)
        elif kind == "ltr":
            c.line("M8 40 H38 M34 36 L38 40 L34 44", c["blue"], 2.4)
        else:
            c.line("M6 40 H42 M10 36 L6 40 L10 44 M38 36 L42 40 L38 44", c["blue"], 2.4)
    return run


def squiggle(c):
    gl(c, "underline", "ink", 8, 2, 32)
    c.path("M8 41 Q11 37 14 41 T20 41 T26 41 T32 41 T38 41", "none", c["red"], 2)


def textcolor(c):
    c.text(24, 32, "A", 30, c["ink"])
    c.rect(8, 36, 32, 7, c["red"], 1)


# ---- debugger --------------------------------------------------------------
def codelines(c, hi=None):
    for i, y in enumerate((10, 18, 26, 34, 42)):
        w = (24, 16, 20, 12, 18)[i]
        c.line(f"M6 {y} H{6 + w}", c["blue"] if hi == i else c["grey"], 2.6 if hi == i else 2)


def dbg(kind):
    def run(c):
        red, ink = c["red"], c["ink"]
        if kind == "over":
            codelines(c)
            c.path("M10 18 C10 4 34 4 34 22", "none", ink, 2.4)
            c.path("M30 18 L34 24 L38 18", "none", ink, 2.4)
            c.circle(34, 34, 3.5, red, None)
        elif kind in ("into", "into-ins"):
            codelines(c)
            c.path("M30 4 V24 M25 19 L30 24 L35 19", "none", ink, 2.6)
            c.circle(30, 33, 3.5, red, None)
        elif kind == "out":
            codelines(c)
            c.path("M30 34 V12 M25 17 L30 12 L35 17", "none", ink, 2.6)
            c.circle(30, 40, 3.5, red, None)
        elif kind == "ins":
            codelines(c, 2)
            c.path("M34 6 V22 M30 18 L34 22 L38 18", "none", ink, 2.6)
        elif kind == "to-cursor":
            codelines(c)
            c.path("M4 26 H24 M19 21 L24 26 L19 31", "none", ink, 2.6)
            c.path("M30 14 V38 M27 14 H33 M27 38 H33", "none", red, 2.4)
        elif kind == "from-cursor":
            codelines(c)
            c.path("M12 14 V38 M9 14 H15 M9 38 H15", "none", red, 2.4)
            c.path("M18 26 H40 M35 21 L40 26 L35 31", "none", ink, 2.6)
        if kind in ("ins", "into-ins"):
            badge(c, "chip", "grey")
    return run


def run_cursor(c):
    c.path("M14 8 V36 M10 8 H18 M10 36 H18", "none", c["red"], 2.6)
    badge(c, "play", "green")


# ---- the table ---------------------------------------------------------------
def acrobat(c):
    action(c, "page", "red")
    if not c.small:
        c.text(23, 36, "PDF", 9, c["red"])


def face(b, bc="blue"):
    return A("act-af-face", None, b, bc)


def select(extra, b=None, bc="blue"):
    def run(c):
        gl(c, "selection", "ink")
        if extra:
            extra(c)
        if b:
            badge(c, b, bc)
    return run


def sel_cursor(c):
    gl(c, "cursor", "ink", 22, 18, 24)


def sel_all(c):
    c.rect(14, 14, 9, 9, light(c, "blue"), 1); c.rect(25, 14, 9, 9, light(c, "blue"), 1)
    c.rect(14, 25, 9, 9, light(c, "blue"), 1); c.rect(25, 25, 9, 9, light(c, "blue"), 1)


def sel_invert(c):
    c.path("M12 12 H36 V36 Z", light(c, "blue"), "ink", 1)


def sel_text(c):
    c.path("M14 18 H34 M14 24 H34 M14 30 H26", "none", c["blue"], 2.4)


def sel_layers(c):
    gl(c, "layers", "blue", 14, 13, 20)


def sel_original(c):
    gl(c, "picture", "green", 13, 13, 22)


def folderact(g="folder", fill=False):
    return lambda c: action(c, g, "blue" if fill else None, None, None, g if fill else None)


SPEC = {
    "accept_signal": A("act-af-accept-signal", "orange"),
    "acrobat": acrobat,
    "activities": A("activities", "violet"),
    "add-subtitle": A("act-af-subtitle", None, "plus"),
    "address-book-new": A("act-af-addressbook", None, "plus"),
    "adjustcol": K(A("table"), A("act-af-col-adjust", "red")),
    "adjustrow": K(A("table"), A("act-af-row-adjust", "red")),
    "adjustcurves": A("curves", "blue"),
    "adjusthsl": hue_wheel,
    "adjustlevels": A("levels", "blue"),
    "adjustrgb": color_dots,
    "aggregation": uml("aggregation"),
    "akonadiconsole": A("terminal", None, "database", "blue"),
    "align-horizontal-baseline": align_baseline(False),
    "align-horizontal-bottom-out": align_out_side(True),
    "align-horizontal-center": align("center"),
    "align-horizontal-left": align("left"),
    "align-horizontal-left-out": align("left-out"),
    "align-horizontal-left-to-anchor": align("left", False, "anchor"),
    "align-horizontal-node": align("node"),
    "align-horizontal-right": align("right"),
    "align-horizontal-right-out": align("right-out"),
    "align-horizontal-right-to-anchor": align("right", False, "anchor"),
    "align-horizontal-top-out": align_out_side(False),
    "align-none": scatter(None, "cross", "red"),
    "align-vertical-baseline": align_baseline(True),
    "align-vertical-bottom": align("right", True),
    "align-vertical-bottom-out": align("right-out", True),
    "align-vertical-center": align("center", True),
    "align-vertical-node": align("node", True),
    "align-vertical-top": align("left", True),
    "align-vertical-top-out": align("left-out", True),
    "amarok_cart_add": A("cart", None, "plus"),
    "amarok_cart_remove": A("cart", None, "minus", "red"),
    "amarok_cart_view": A("cart", None, "eye", "blue"),
    "anchor": A("anchor"),
    "antivignetting": K(lambda c: c.rect(6, 8, 36, 32, c.grad(c.lighten(c["grey"], 0.3), c["grey"]), 3),
                        lambda c: c.ellipse(24, 24, 15, 13, c.grad(c["page"]), width=1.2), Bd("minus", "grey")),
    "application-exit": A("exit", "red"),
    "application-menu": K(A("window"), Bd("menu", "blue")),
    "appointment-new": A("calendar", None, "plus"),
    "archive-extract": A("archive", "brown", "arrow-up", "green"),
    "archive-insert": A("archive", "brown", "arrow-down", "blue"),
    "archive-remove": A("archive", "brown", "minus", "red"),
    "artifact": A("act-af-artifact", "orange"),
    "association": uml("association"),
    "atmosphere": A("act-af-atmosphere", "cyan"),
    "auto-transition": A("act-af-transition", None, "wand", "violet"),
    "auto-type": A("keyboard", None, "lightning", "orange"),
    "autocorrection": A("abc", None, "wand", "orange"),
    "automated-tasks": A("gear", None, "clock", "blue"),
    "backgroundtool": A("picture", "green", None, None, "picture"),
    "backup": A("harddisk", None, "history", "blue"),
    "bboxnext": A("selection", None, "arrow-right", "blue"),
    "bboxprev": A("selection", None, "arrow-left", "blue"),
    "bitmap-trace": A("picture", None, "path", "violet"),
    "black_sum": A("sigma", "grey", None, None, "sigma"),
    "blur": A("blur", "cyan"),
    "blurfx": A("blur", "violet", "wand", "violet"),
    "bookmark-edit": A("bookmark", None, "pen", "blue"),
    "bookmark-new": A("bookmark", None, "plus"),
    "bookmark-remove": A("bookmark", None, "minus", "red"),
    "bookmarks": K(G("bookmark", "ink", 2, 4, 30), G("bookmark", "red", 16, 10, 30)),
    "bookmarks-bookmarked": K(lambda c: c.path("M15 10.5 H33 V37.5 L24 30 L15 37.5 Z", c["red"], None), A("bookmark")),
    "boost": A("repeat", "violet"),
    "boost-boosted": A("repeat", "green", None, None, "repeat"),
    "bordertool": bordertool,
    "brightness-high": A("sun", "orange", "plus", "orange"),
    "brightness-low": A("brightness", "orange", "minus", "grey"),
    "bwtonal": A("contrast", "brown", None, None, "contrast"),
    "call-start": A("act-af-handset", "green"),
    "call-stop": A("act-af-hangup", "red"),
    "call-voicemail": A("act-af-voicemail", "blue"),
    "category": A("act-af-category", "violet"),
    "category2parent": A("act-af-category", "violet", "arrow-up", "violet"),
    "child2category": A("act-af-category", "violet", "arrow-down", "violet"),
    "channelmixer": channelmixer,
    "character-set": K(lambda c: c.rect(5, 8, 38, 32, c.grad(c["page"]), 3), letters("A\u00e4\u03a9", 17, 30)),
    "charcoaltool": A("act-af-charcoal"),
    "check_constraint": A("database", None, "check"),
    "chronometer": A("stopwatch"),
    "chronometer-pause": A("stopwatch", None, "pause", "orange"),
    "choice-rhomb": A("diamond", "orange", None, None, "diamond"),
    "circular-arrow-shape": A("refresh", "blue", None, None, "refresh"),
    "code-block": code_tile("{ }", "blue", 20),
    "code-class": code_tile("C", "violet"),
    "code-context": code_tile("::", "grey"),
    "code-function": code_tile("f", "green", 26),
    "code-typedef": code_tile("T", "orange"),
    "code-variable": code_tile("x", "red", 26),
    "collapse-all": A("act-af-collapse"),
    "expand-all": A("act-af-expand"),
    "color-gradient": gradient_rect,
    "color-management": A("color", None, "gear", "blue"),
    "color-mode-black-white": A("contrast"),
    "color-mode-hue-shift-negative": K(hue_wheel, Bd("minus", "red")),
    "color-mode-hue-shift-positive": K(hue_wheel, Bd("plus", "green")),
    "color-mode-invert-image": K(negative, Bd("contrast", "grey")),
    "color-mode-invert-text": K(lambda c: c.rect(6, 8, 36, 32, c.grad(c.lighten(c["ink"], 0.25), c["ink"]), 3),
                                letters("A", 26, 33, "white")),
    "color-picker": A("color-picker"),
    "color-picker-black": K(A("color-picker"), swatch("#000000")),
    "color-picker-grey": K(A("color-picker"), swatch("grey")),
    "color-picker-white": K(A("color-picker"), swatch("#ffffff")),
    "colorfx": A("color", None, "wand", "violet"),
    "colorneg": negative,
    "colors-chromablue": chroma("blue"),
    "colors-chromagreen": chroma("green"),
    "colors-chromared": chroma("red"),
    "colors-luma": luma,
    "combined_fragment": A("act-af-fragment"),
    "compass": A("compass"),
    "composite-track-off": A("act-af-transition", "grey", "cross", "red"),
    "composite-track-on": A("act-af-transition", "blue", "check", "green"),
    "composite-track-preview": A("act-af-transition", "blue", "eye", "blue"),
    "composition": uml("composition"),
    "configure": A("gear"),
    "contrast": A("contrast", "ink", None, None, "contrast"),
    "coordinate": A("act-af-coordinate"),
    "copy-coordinates": A("act-af-coordinate", None, "copy", "blue"),
    "crosshairs": A("crosshair"),
    "cursor-cross": A("act-af-cursor-cross"),
    "curve-connector": A("act-af-curve-conn"),
    "dashboard-show": A("act-af-gauge", "blue"),
    "database-change-key": A("database", None, "key", "orange"),
    "database-index": A("database", None, "list", "blue"),
    "debug-execute-from-cursor": dbg("from-cursor"),
    "debug-execute-to-cursor": dbg("to-cursor"),
    "debug-run": A("bug", None, "play", "green"),
    "debug-run-cursor": K(lambda c: codelines(c), run_cursor),
    "debug-step-instruction": dbg("ins"),
    "debug-step-into": dbg("into"),
    "debug-step-into-instruction": dbg("into-ins"),
    "debug-step-out": dbg("out"),
    "debug-step-over": dbg("over"),
    "deep-history": K(lambda c: c.circle(24, 24, 17, c.grad(c["page"])), letters("H*", 18, 31)),
    "delete-comment": A("comment", None, "cross", "red"),
    "edit-table-delete-row": table([(0, 1), (1, 1), (2, 1)], "red", b="minus", bc="red"),
    "deletecell": table([(1, 1)], "red", b="cross", bc="red"),
    "dependency": uml("dependency"),
    "depth16to8": depth("16", "8"),
    "depth8to16": depth("8", "16"),
    "description": A("lines", None, "info", "blue"),
    "dfrac": A("act-af-dfrac"),
    "dialog-cancel": A("forbidden", "red"),
    "dialog-input-devices": A("act-af-input"),
    "dialog-layers": A("layers"),
    "dialog-messages": A("chat", None, "info", "blue"),
    "dialog-ok-apply": A("check", "green", None, None, "check"),
    "dialog-rows-and-columns": table([(0, 0), (1, 0), (2, 0), (0, 1), (0, 2)], "blue", b="properties", bc="blue"),
    "dialog-scripts": A("act-af-scroll"),
    "dialog-tile-clones": A("act-af-tiles", "blue"),
    "dialog-xml-editor": A("act-af-xml"),
    "discrete": A("act-af-stem"),
    "distribute-graph": A("act-af-graph"),
    "distribute-graph-directed": A("act-af-digraph"),
    "distribute-horizontal": distribute("plain"),
    "distribute-horizontal-baseline": distribute_baseline(False),
    "distribute-horizontal-center": distribute("center"),
    "distribute-horizontal-equal": distribute("equal"),
    "distribute-horizontal-left": distribute("left"),
    "distribute-horizontal-margin": distribute("margin"),
    "distribute-horizontal-node": distribute("node"),
    "distribute-horizontal-page": distribute("page"),
    "distribute-horizontal-right": distribute("right"),
    "distribute-randomize": scatter(None, "dice", "violet"),
    "distribute-remove-overlaps": K(overlaps, Bd("move", "orange")),
    "distribute-unclump": unclump,
    "distribute-vertical": distribute("plain", True),
    "distribute-vertical-baseline": distribute_baseline(True),
    "distribute-vertical-bottom": distribute("right", True),
    "distribute-vertical-center": distribute("center", True),
    "distribute-vertical-equal": distribute("equal", True),
    "distribute-vertical-margin": distribute("margin", True),
    "distribute-vertical-node": distribute("node", True),
    "distribute-vertical-page": distribute("page", True),
    "distribute-vertical-top": distribute("left", True),
    "dontknow": K(A("chat", "blue"), G("question", "blue", 15, 9, 18)),
    "download-later": A("download", None, "clock", "orange"),
    "drag-surface": A("hand", None, "move", "blue"),
    # draw-*: the shape in blue; tools in ink with their mark
    "draw-arrow": A("arrow-tool", "blue"),
    "draw-bezier-curves": A("bezier", "blue"),
    "draw-brush": A("brush", None, None, None),
    "draw-calligraphic": A("act-af-calligraphic"),
    "draw-circle": A("circle", "blue", None, None, "circle"),
    "draw-connector": A("act-af-elbow-conn", "blue"),
    "draw-cross": A("act-af-cross-shape", "blue"),
    "draw-cuboid": A("act-af-cuboid", "blue"),
    "draw-donut": A("act-af-donut", "blue"),
    "draw-ellipse": A("ellipse", "blue"),
    "draw-ellipse-arc": A("act-af-ellipse-arc", "blue"),
    "draw-ellipse-segment": A("act-af-ellipse-seg", "blue"),
    "draw-eraser": A("eraser", "red", None, None, "eraser"),
    "draw-freehand": K(A("act-af-freehand", "blue"), G("pencil", "ink", 24, 22, 20)),
    "draw-halfcircle1": A("act-af-half1", "blue"),
    "draw-halfcircle2": A("act-af-half2", "blue"),
    "draw-halfcircle3": A("act-af-half3", "blue"),
    "draw-halfcircle4": A("act-af-half4", "blue"),
    "draw-highlight": A("act-af-highlight"),
    "draw-line": A("line-tool", "blue"),
    "draw-number": A("act-af-number", "blue"),
    "draw-path": A("path", "blue"),
    "draw-polygon": A("polygon", "blue"),
    "draw-polygon-star": A("act-af-star-outline", "blue"),
    "draw-polyline": A("act-af-polyline", "blue"),
    "draw-rectangle": A("rectangle", "blue"),
    "draw-rectangle-rounded": A("act-af-rrect", "blue"),
    "draw-spiral": A("spiral", "blue"),
    "draw-square-inverted-corners": A("act-af-inv-corners", "blue"),
    "draw-star": A("star", "blue"),
    "draw-text": A("act-af-text-tool"),
    "draw-triangle": A("triangle", "blue"),
    "draw-triangle1": A("act-af-tri1", "blue"),
    "draw-triangle2": A("act-af-tri2", "blue"),
    "draw-triangle3": A("act-af-tri3", "blue"),
    "draw-triangle4": A("act-af-tri4", "blue"),
    "draw-watercolor": A("act-af-watercolor", "cyan"),
    "earthquake": A("act-af-quake", "brown"),
    # edit-*
    "edit-bomb": A("act-af-bomb"),
    "edit-clear": A("act-af-backspace"),
    "edit-clear-history": A("history", None, "cross", "red"),
    "edit-clear-locationbar-ltr": A("act-af-field-clear"),
    "edit-clone": A("copy", "violet", "link", "blue"),
    "edit-clone-unlink": A("copy", "violet", "cross", "red"),
    "edit-copy": A("copy"),
    "edit-copy-path": A("copy", None, "folder", "grey"),
    "edit-cut": A("scissors"),
    "edit-delete": A("trash", "red"),
    "edit-delete-shred": A("act-af-shredder", "red"),
    "edit-download": A("download", None, "pen", "blue"),
    "edit-find": A("act-af-find"),
    "edit-find-replace": A("act-af-find", None, "sync", "blue"),
    "edit-group": A("group"),
    "edit-guides": A("act-af-guides"),
    "edit-image-face-add": face("plus", "green"),
    "edit-image-face-detect": face("magnifier", "blue"),
    "edit-image-face-recognize": face("user", "violet"),
    "edit-image-face-show": face("eye", "orange"),
    "edit-line-width": A("act-af-linewidth"),
    "edit-move": K(A("move"), lambda c: c.rect(19, 19, 10, 10, light(c, "blue"), 1.5)),
    "edit-node": A("node"),
    "edit-opacity": A("act-af-opacity"),
    "edit-paste": A("paste"),
    "edit-paste-in-place": A("paste", None, "target", "blue"),
    "edit-paste-style": A("paste", None, "brush", "violet"),
    "edit-redo": A("redo"),
    "edit-reset": A("rotate-left", "orange"),
    "edit-select": select(sel_cursor),
    "edit-select-all": select(sel_all),
    "edit-select-all-layers": select(sel_layers),
    "edit-select-invert": select(sel_invert),
    "edit-select-lasso": A("lasso"),
    "edit-select-none": select(None, "cross", "red"),
    "edit-select-original": select(sel_original),
    "edit-select-text": select(sel_text),
    "edit-table-cell-merge": table(merge=((0, 1), (1, 1))),
    "edit-table-cell-split": table([(1, 1)], split=(1, 1)),
    "edit-table-delete-column": table([(1, 0), (1, 1), (1, 2)], "red", b="cross", bc="red"),
    "edit-table-insert-column-left": table([(0, 0), (0, 1), (0, 2)], "green", b="plus"),
    "edit-table-insert-column-right": table([(2, 0), (2, 1), (2, 2)], "green", b="plus"),
    "edit-table-insert-row-above": table([(0, 0), (1, 0), (2, 0)], "green", b="plus"),
    "edit-table-insert-row-below": table([(0, 2), (1, 2), (2, 2)], "green", b="plus"),
    "edit-table-insert-row-under": table([(0, 2), (1, 2), (2, 2)], "green", b="arrow-down", bc="blue"),
    "edit-text-frame-update": A("act-af-entity", None, "refresh", "blue"),
    "edit-undo": A("undo"),
    "embosstool": emboss,
    "entity": A("act-af-entity", "brown"),
    "entrance_animations": A("star", "green", "arrow-right", "green"),
    "entry-new": A("act-af-ledger", None, "plus"),
    "errornext": A("act-af-warn", "red", "arrow-down", "blue"),
    "errorprev": A("act-af-warn", "red", "arrow-up", "blue"),
    "escape-direction-all": escape(("up", "down", "left", "right")),
    "escape-direction-down": escape(("down",)),
    "escape-direction-horizontal": escape(("left", "right")),
    "escape-direction-left": escape(("left",)),
    "escape-direction-right": escape(("right",)),
    "escape-direction-up": escape(("up",)),
    "escape-direction-vertical": escape(("up", "down")),
    "exception": A("lightning", "orange"),
    "exchange-positions": A("act-af-swap"),
    "exchange-positions-clockwise": A("act-af-swap-cw"),
    "exchange-positions-zorder": A("act-af-zorder"),
    "favorite": A("act-af-star-outline", "orange"),
    "favorite-favorited": A("star", "orange"),
    "favorite-genres-amarok": A("act-af-star-outline", "orange", "music", "violet"),
    "feed-subscribe": A("feed", "orange", "plus"),
    # filename tokens (a file-name scheme: each piece a chip)
    "filename-and-amarok": chip("&"),
    "filename-bpm-amarok": chip("BPM", 13),
    "filename-dash-amarok": chip("-", 28),
    "filename-discnumber-amarok": chip(inner=G("disc", "ink", 12, 12, 24)),
    "filename-divider": chip("|", 22, col="grey"),
    "filename-dot-amarok": chip(inner=lambda c: c.circle(24, 29, 3, c["ink"], None)),
    "filename-filetype-amarok": chip("ext", 15),
    "filename-group-length": chip(inner=G("clock", "ink", 12, 12, 24), col="blue"),
    "filename-group-tracks": chip(inner=G("list-number", "ink", 12, 12, 24), col="blue"),
    "filename-initial-amarok": chip("A.", 19),
    "filename-moodbar": chip(inner=moodbar, col="grey"),
    "filename-slash-amarok": chip("/", 22),
    "filename-space-amarok": chip(inner=lambda c: c.path("M14 22 V30 H34 V22", "none", "ink", 2.4)),
    "filename-title-amarok": chip("T", 22),
    "filename-underscore-amarok": chip(inner=lambda c: c.line("M15 31 H33", "ink", 2.6)),
    "fill-color": K(A("fill"), lambda c: c.rect(6, 38, 22, 6, c["red"], 1)),
    "fill-rule-even-odd": K(lambda c: c.path(_pent(), c["blue"], None, opacity=None),
                            lambda c: c.path(_pent_inner(), c.grad(c["page"]), None), A("act-af-pentagram")),
    "fill-rule-nonzero": K(lambda c: c.path(_pent(), c["blue"], None), A("act-af-pentagram")),
    "filmgrain": K(A("film"), lambda c: [c.circle(x, y, 1.3 if not c.small else 1.8, c["ink"], None)
                                          for x, y in ((21, 15), (27, 19), (22, 25), (28, 30), (20, 33))]),
    "final_activity": K(lambda c: c.circle(24, 24, 16, "#ffffff"), lambda c: c.circle(24, 24, 10, c["ink"], None)),
    "financial-account": A("bank", "green", "act-af-coin", "orange"),
    "financial-categories": A("chart-pie", "green", "tag", "violet"),
    "financial-forecast": A("act-af-forecast", "green"),
    "financial-list": A("list", "green", "act-af-coin", "orange"),
    "find-location": A("location", None, "magnifier", "blue"),
    "fingerprint": A("fingerprint"),
    "flag": A("flag"),
    "flag-black": K(lambda c: c.path("M15 13 H33 L28.5 19 L33 25 H15 Z", "#202020", None), A("flag")),
    "flag-blue": K(lambda c: c.path("M15 13 H33 L28.5 19 L33 25 H15 Z", c["blue"], None), A("flag")),
    "flag-green": K(lambda c: c.path("M15 13 H33 L28.5 19 L33 25 H15 Z", c["green"], None), A("flag")),
    "flag-red": K(lambda c: c.path("M15 13 H33 L28.5 19 L33 25 H15 Z", c["red"], None), A("flag")),
    "flag-yellow": K(lambda c: c.path("M15 13 H33 L28.5 19 L33 25 H15 Z", c["yellow"], None), A("flag")),
    "flash": A("lightning", "orange", None, None, "lightning"),
    "flashlight-off": A("act-af-torch"),
    "flashlight-on": K(A("act-af-torch-on", "orange")),
    "flower-shape": A("act-af-flower", "violet"),
    "folder-add": A("folder", None, "plus", "blue"),
    "folder-new": A("folder", "blue", "plus", None, "folder"),
    "folder-edit-sign-decrypted": A("folder", None, "unlock", "orange"),
    "folder-edit-sign-encrypt": A("folder", None, "lock", "green"),
    "folder-open-recent": A("folder-open", "blue", "clock", "blue", "folder-open"),
    "folder-stash": A("folder", None, "archive", "brown"),
    "folder-sync": A("folder", None, "sync", "blue"),
    "font-disable": A("font", None, "cross", "red"),
    "font-enable": A("font", None, "check"),
    "food": A("act-af-food"),
    "foreign_green": A("key", "green"),
    "foreign_red": A("key", "red"),
    "foreignkey_constraint": A("key", None, "link", "blue"),
    "fork": A("act-af-fork"),
    # format-*: nodes
    "format-add-node": K(nodes("add"), Bd("plus")),
    "format-insert-node": K(nodes("insert"), Bd("arrow-down", "blue")),
    "format-remove-node": K(nodes("remove"), Bd("minus", "red")),
    "format-break-node": nodes("break"),
    "format-join-node": nodes("join"),
    "format-connect-node": nodes("connect"),
    "format-disconnect-node": nodes("disconnect"),
    "format-node-corner": nodes("corner"),
    "format-node-smooth": nodes("smooth"),
    "format-node-symmetric": nodes("symmetric"),
    "format-node-curve": nodes("node-curve"),
    "format-node-line": nodes("node-line"),
    "format-segment-curve": nodes("seg-curve"),
    "format-segment-line": nodes("seg-line"),
    "format-convert-to-path": K(A("text"), Bd("path", "violet")),
    # format-*: cells and borders
    "format-align-vertical-bottom": valign("bottom"),
    "format-align-vertical-center": valign("center"),
    "format-align-vertical-top": valign("top"),
    "format-border-set-all": border("LRTBHV"),
    "format-border-set-bottom": border(["B"]),
    "format-border-set-diagonal-bl-tr": border(["D1"]),
    "format-border-set-diagonal-tl-br": border(["D2"]),
    "format-border-set-external": border(["L", "R", "T", "B"]),
    "format-border-set-internal": border(["H", "V"]),
    "format-border-set-internal-horizontal": border(["H"]),
    "format-border-set-internal-vertical": border(["V"]),
    "format-border-set-left": border(["L"]),
    "format-border-set-none": K(border([]), Bd("cross", "grey")),
    "format-border-set-right": border(["R"]),
    "format-border-set-top": border(["T"]),
    "format-border-style": border_style,
    "format-currency": A("money", None, "act-af-coin", "orange"),
    "format-number-percent": K(lambda c: c.rect(5, 8, 38, 32, c.grad(c["page"]), 3), A("percent", "blue")),
    "format-precision-less": precision(False),
    "format-precision-more": precision(True),
    # format-*: text
    "format-font-size-less": fontsize(False),
    "format-font-size-more": fontsize(True),
    "format-indent-less": A("outdent"),
    "format-indent-more": A("indent"),
    "format-justify-center": A("align-center"),
    "format-justify-fill": A("align-justify"),
    "format-justify-left": A("align-left"),
    "format-justify-right": A("align-right"),
    "format-line-spacing-double": spacing(2),
    "format-line-spacing-normal": spacing(1),
    "format-line-spacing-triple": spacing(3),
    "format-list-ordered": A("list-number"),
    "format-text-blockquote": A("act-af-quote"),
    "format-text-bold": A("bold"),
    "format-text-capitalize": letters("Aa", 24, 33),
    "format-text-code": K(lambda c: c.rect(5, 10, 38, 28, c.grad(c["page"]), 3), A("code", "blue")),
    "format-text-color": textcolor,
    "format-text-direction-horizontal": textdir("horizontal"),
    "format-text-direction-ltr": textdir("ltr"),
    "format-text-direction-vertical": textdir("vertical"),
    "format-text-italic": A("italic"),
    "format-text-lowercase": letters("ab", 24, 31),
    "format-text-strikethrough": A("strikethrough"),
    "format-text-subscript": script(True),
    "format-text-superscript": script(False),
    "format-text-symbol": letters("Ω", 30, 36),
    "format-text-underline": A("underline"),
    "format-text-underline-squiggle": squiggle,
    "format-text-uppercase": A("act-af-uppercase"),
    "formula": A("act-af-radical"),
}


@reg("act-af-collapse")
def _(c, k): S(c, "M6 3 L12 9 L18 3 M6 21 L12 15 L18 21 M4 12 H20", k)
@reg("act-af-expand")
def _(c, k): S(c, "M6 9 L12 3 L18 9 M6 15 L12 21 L18 15 M4 12 H20", k)


def _pent_pts(r=14.25):
    import math
    return [(24 + r * math.cos(-math.pi / 2 + i * 4 * math.pi / 5), 25.2 + r * math.sin(-math.pi / 2 + i * 4 * math.pi / 5))
            for i in range(5)]


def _pent():
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in _pent_pts()) + " Z"


def _pent_inner():
    import math
    # the inner pentagon of the pentagram (where even-odd leaves a hole)
    r = 14.25 * math.cos(2 * math.pi / 5) / math.cos(math.pi / 5)
    pts = [(24 + r * math.cos(math.pi / 2 + i * 2 * math.pi / 5), 25.2 + r * math.sin(math.pi / 2 + i * 2 * math.pi / 5))
           for i in range(5)]
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"

@reg("act-af-page-pen")
def _(c, k): S(c, "M6 3 H14 L18 7 V21 H6 Z M14 3 V7 H18", k); S(c, "M9 17.5 L9.5 15 L14 10.5 L16 12.5 L11.5 17 Z", k)
@reg("act-af-compare")
def _(c, k): S(c, "M2 5 H7 L10 8 V20 H2 Z M14 4 H19 L22 7 V19 H14 Z", k); S(c, "M4 12 H8 M4 15 H8 M16 11 H20 M16 14 H18", k, W(c) * 0.7)
@reg("act-af-page-swap")
def _(c, k): S(c, "M2 2 H7 L10 5 V12 H2 Z M14 12 H19 L22 15 V22 H14 Z M12 5.5 H18.5 V9.5 M16.5 7.5 L18.5 10 L20.5 7.5 M12 18.5 H5.5 V14.5 M3.5 16.5 L5.5 14 L7.5 16.5", k)
@reg("act-af-page-unequal")
def _(c, k): S(c, "M1 5 H6 L9 8 V19 H1 Z M15 5 H20 L23 8 V19 H15 Z", k); S(c, "M10 10 H14 M10 14 H14 M13 7.5 L11 16.5", k)
@reg("act-af-saves")
def _(c, k): S(c, "M8 8 H18 L21 11 V21 H8 Z M11 8 V12 H17 V8 M10.5 15 H18.5 V21 M4 17 V4 H15 L17 6", k)


def badge2(name, bc="green"):
    def run(c):
        col = c[bc] if bc in c.w else bc
        c.circle(37, 11, 7.5 if not c.small else 9, col, width=1.1)
        glyph(c, name, 31.5, 5.5, 11, "#ffffff", width=3.2 if not c.small else 4)
    return run


SPEC.update({
    "document-close": A("page", None, "cross", "red"),
    "document-compareleft": A("act-af-compare", None, "arrow-left", "blue"),
    "document-compareright": A("act-af-compare", None, "arrow-right", "blue"),
    "document-decrypt": A("page", None, "unlock", "orange"),
    "document-encrypted": A("page", None, "lock", "green"),
    "document-edit": A("act-af-page-pen"),
    "document-edit-decrypt": A("act-af-page-pen", None, "unlock", "orange"),
    "document-edit-decrypt-verify": K(A("act-af-page-pen", None, "unlock", "orange"), badge2("check", "green")),
    "document-edit-encrypt": A("act-af-page-pen", None, "lock", "green"),
    "document-edit-sign": A("act-af-page-pen", None, "signature", "violet"),
    "document-edit-sign-encrypt": K(A("act-af-page-pen", None, "lock", "green"), badge2("signature", "violet")),
    "document-export": A("page", None, "arrow-right", "blue"),
    "document-import": A("page", None, "arrow-left", "green"),
    "document-new": A("page", None, "plus"),
    "document-new-from-template": A("pages", None, "plus"),
    "document-open": A("open"),
    "document-open-recent": A("open", None, "clock", "blue"),
    "document-open-remote": A("open", None, "globe", "blue"),
    "document-preview-archive": A("archive", "brown", "eye", "blue"),
    "document-print": A("printer"),
    "document-print-direct": A("printer", None, "lightning", "orange"),
    "document-properties": A("page", None, "properties", "blue"),
    "document-replace": A("page", None, "refresh", "orange"),
    "document-revert": A("page", None, "undo", "orange"),
    "document-save": A("save"),
    "document-save-all": A("act-af-saves"),
    "document-save-as": A("save", None, "pen", "blue"),
    "document-save-as-template": A("save", None, "pages", "violet"),
    "document-scan": A("scanner"),
    "document-send": A("page", None, "send", "blue"),
    "document-share": A("page", None, "share", "blue"),
    "document-swap": A("act-af-page-swap"),
    "document-unequal": A("act-af-page-unequal"),
    "align-vertical-bottom-to-anchor": align("right", True, "anchor"),
    "amarok_change_language": A("language", None, "refresh", "violet"),
    "choice-round": A("circle", "orange", None, None, "circle"),
    "format-list-unordered": A("list-bullet"),
})


def draw(name, c):
    if not name or name[0] not in ME:
        return None
    fn = SPEC.get(name)
    if fn is None:
        return None
    fn(c)
    return True
