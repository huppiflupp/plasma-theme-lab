"""Mouse cursors after the X11 cursor font that CDE and Motif used.

The glyphs of the X cursor font are 16 x 16 bitmaps: black shapes with a
white mask, a few white with a black outline (hand, watch face). They are
drawn here on the same 16-pixel grid with the pixel painter of icons.py;
24 px is rasterised on its own, 32, 48 and 64 px are whole-number
enlargements (of 16, 24 and 16), so the cursors keep their pixel edges.
The files are written in the Xcursor format directly, without xcursorgen.
"""
import math
import struct
from pathlib import Path

from icons import Pixels, COPPER

BLACK, WHITE = "#000000", "#ffffff"
SIZES = {24: (24, 1), 32: (16, 2), 48: (24, 2), 64: (16, 4)}   # size: (drawn at, enlarged by)


def turn(points, degrees, centre=(8, 8)):
    a = math.radians(degrees)
    cx, cy = centre
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in points]


def shift(points, dx, dy, scale=1.0):
    return [(dx + x * scale, dy + y * scale) for x, y in points]


ARROW = [(1, 1), (1, 14), (4.2, 11), (6.5, 15.8), (8.8, 14.8), (6.6, 10.2), (11, 10.2)]
DOUBLE = [(0.3, 8), (4.5, 3.8), (4.5, 6.6), (11.5, 6.6), (11.5, 3.8), (15.7, 8), (11.5, 12.2), (11.5, 9.4), (4.5, 9.4), (4.5, 12.2)]


def rim(p, mask):
    """The pixels around a shape: the cursor font's mask is the glyph grown
    by one pixel in every direction, so thin strokes keep their colour."""
    return {(i + dx, j + dy) for i, j in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if 0 <= i + dx < p.n and 0 <= j + dy < p.n} - mask


def dark(p, mask):
    """A black shape on a white rim."""
    p.fill(rim(p, mask), WHITE)
    p.fill(mask, BLACK)


def light(p, mask):
    """A white shape with a black rim (hand, watch face)."""
    p.fill(rim(p, mask), BLACK)
    p.fill(mask, WHITE)


def arrow(p, small=None):
    dark(p, p.poly(ARROW))
    if small:
        small(p)


def watch(p, x=0, y=0, s=1.0):
    q = lambda pts: p.poly(shift(pts, x, y, s))
    dark(p, q([(5, 0), (11, 0), (11, 4), (5, 4)]) | q([(5, 12), (11, 12), (11, 16), (5, 16)]))
    light(p, p.disc(x + 8 * s, y + 8 * s, 6 * s))
    p.fill(p.line(x + 8 * s, y + 8 * s, x + 8 * s, y + 4 * s) | p.line(x + 8 * s, y + 8 * s, x + 11 * s, y + 9.5 * s), BLACK)
    p.fill(p.rect(x + 13.8 * s, y + 7 * s, 1.5 * s, 2 * s), COPPER)


def ibeam(p, angle=0):
    pts = [[(4.5, 0.5), (11.5, 0.5), (11.5, 2.5), (9, 2.5), (9, 13.5), (11.5, 13.5), (11.5, 15.5), (4.5, 15.5), (4.5, 13.5), (7, 13.5), (7, 2.5), (4.5, 2.5)]]
    dark(p, p.poly(turn(pts[0], angle)))


def hand(p, fingers="point"):
    palm = p.poly([(3, 7.5), (13.5, 7.5), (13.5, 12.5), (11, 15.8), (5, 15.8), (2, 12), (2, 9.5)])
    if fingers == "point":
        # Index finger up at the left, the others folded beside it, thumb
        # out to the left: the X11 hand2.
        index = p.rect(3.5, 1, 3, 9)
        folded = p.rect(6.5, 5.5, 2.6, 4) | p.rect(9.1, 6, 2.6, 4) | p.rect(11.7, 7, 2.6, 4)
        thumb = p.poly([(0.5, 9.5), (2, 8.5), (4, 10.5), (4, 13.5)])
        body = p.poly([(3.5, 9), (14.3, 9), (14.3, 12.5), (12, 15.5), (5.5, 15.5), (3.5, 13)])
        light(p, index | folded | thumb | body)
        p.fill(p.vline(6.5, 6, 3.5) | p.vline(9.1, 6.5, 3) | p.vline(11.7, 7.5, 2.5), BLACK)
    elif fingers == "open":
        parts = palm | p.rect(0.5, 6, 3, 5)
        for x, top in ((3.5, 2), (6.3, 0.5), (9.1, 1), (11.9, 2.5)):
            parts |= p.rect(x, top, 2.6, 7)
        light(p, parts)
        p.fill(p.vline(6.3, 1.5, 6) | p.vline(9.1, 1.5, 6) | p.vline(11.9, 3, 4.5), BLACK)
    else:   # closed: the fingers folded over the palm
        light(p, palm | p.rect(3, 5, 10.5, 4))
        p.fill(p.vline(5.8, 5, 3) | p.vline(8.5, 5, 3) | p.vline(11.2, 5, 3), BLACK)


def double(p, angle, bar=False):
    shape = p.poly(turn(DOUBLE, angle))
    if bar:
        shape |= p.poly(turn([(7, 0.5), (9, 0.5), (9, 15.5), (7, 15.5)], angle))
    dark(p, shape)


def cross(p):
    dark(p, p.rect(7, 0, 2, 16) | p.rect(0, 7, 16, 2))
    p.fill(p.rect(7.5, 7.5, 1, 1), WHITE)


def fleur(p):
    tip = [(8, 0.3), (11.5, 4), (9.2, 4), (9.2, 6.8), (6.8, 6.8), (6.8, 4), (4.5, 4)]
    mask = p.rect(6.8, 6.8, 2.4, 2.4)
    for a in (0, 90, 180, 270):
        mask |= p.poly(turn(tip, a))
    dark(p, mask)


def forbidden(p):
    dark(p, (p.disc(8, 8, 7.6) - p.disc(8, 8, 4.6)) | p.poly(turn([(1.5, 7), (14.5, 7), (14.5, 9), (1.5, 9)], 45)))


def badge(kind):
    """A small sign at the arrow's lower right (copy, link, no-drop, help...)."""
    def draw(p):
        if kind == "plus":
            light(p, p.rect(9, 9, 7, 7))
            p.fill(p.rect(12, 10.5, 1, 4) | p.rect(10.5, 12, 4, 1), BLACK)
        elif kind == "link":
            light(p, p.rect(9, 9, 7, 7))
            p.fill(p.line(11, 14, 14, 11) | p.rect(12, 10.5, 2.5, 1) | p.rect(13.5, 10.5, 1, 2.5), BLACK)
        elif kind == "no":
            dark(p, (p.disc(12.5, 12.5, 3.4) - p.disc(12.5, 12.5, 1.6)) | p.line(10.5, 14.5, 14.5, 10.5))
        elif kind == "help":
            light(p, p.rect(9.5, 8.5, 6.5, 7.5))
            p.fill(p.rect(11, 9.8, 3.5, 1) | p.rect(13.5, 9.8, 1, 2.5) | p.rect(12, 11.8, 2, 1) | p.rect(12, 12.5, 1, 1) | p.rect(12, 14.2, 1, 1), BLACK)
        elif kind == "watch":
            watch(p, 8.5, 8.5, 0.47)
        elif kind == "menu":
            light(p, p.rect(9, 8.5, 7, 7.5))
            for y in (10, 12, 14):
                p.fill(p.hline(10.5, y, 4), BLACK)
    return draw


def lens(p, sign):
    dark(p, p.poly([(9, 10.5), (10.5, 9), (15.8, 14.3), (14.3, 15.8)]))
    light(p, p.disc(6.5, 6.5, 5.8))
    p.fill(p.rect(4, 6, 5, 1), BLACK)
    if sign == "+":
        p.fill(p.rect(6, 4, 1, 5), BLACK)


def pencil(p):
    light(p, p.poly([(1, 15), (2, 11.5), (11.5, 2), (14, 4.5), (4.5, 14)]))
    p.fill(p.poly([(10.5, 3), (12.8, 0.8), (15.2, 3.2), (13, 5.5)]), COPPER)
    p.fill(p.line(1, 15, 2.5, 13.5), BLACK)


def x_cursor(p):
    dark(p, p.poly(turn([(1, 6.5), (15, 6.5), (15, 9.5), (1, 9.5)], 45)) | p.poly(turn([(1, 6.5), (15, 6.5), (15, 9.5), (1, 9.5)], -45)))


def plus(p):
    light(p, p.rect(5.5, 0.5, 5, 15) | p.rect(0.5, 5.5, 15, 5))


# name: (painter, hotspot on the 16 grid)
CURSORS = {
    "left_ptr": (arrow, (1, 1)),
    "right_ptr": (lambda p: dark(p, p.poly([(16 - x, y) for x, y in ARROW])), (15, 1)),
    "xterm": (ibeam, (8, 8)),
    "vertical-text": (lambda p: ibeam(p, 90), (8, 8)),
    "watch": (watch, (8, 8)),
    "left_ptr_watch": (lambda p: arrow(p, badge("watch")), (1, 1)),
    "hand2": (hand, (5, 1)),
    "openhand": (lambda p: hand(p, "open"), (8, 8)),
    "closedhand": (lambda p: hand(p, "closed"), (8, 8)),
    "crosshair": (cross, (8, 8)),
    "fleur": (fleur, (8, 8)),
    "sb_h_double_arrow": (lambda p: double(p, 0), (8, 8)),
    "sb_v_double_arrow": (lambda p: double(p, 90), (8, 8)),
    "size_fdiag": (lambda p: double(p, 45), (8, 8)),
    "size_bdiag": (lambda p: double(p, -45), (8, 8)),
    "split_h": (lambda p: double(p, 0, True), (8, 8)),
    "split_v": (lambda p: double(p, 90, True), (8, 8)),
    "crossed_circle": (forbidden, (8, 8)),
    "question_arrow": (lambda p: arrow(p, badge("help")), (1, 1)),
    "copy": (lambda p: arrow(p, badge("plus")), (1, 1)),
    "link": (lambda p: arrow(p, badge("link")), (1, 1)),
    "dnd-none": (lambda p: arrow(p, badge("no")), (1, 1)),
    "context-menu": (lambda p: arrow(p, badge("menu")), (1, 1)),
    "zoom-in": (lambda p: lens(p, "+"), (6, 6)),
    "zoom-out": (lambda p: lens(p, "-"), (6, 6)),
    "pencil": (pencil, (1, 15)),
    "X_cursor": (x_cursor, (8, 8)),
    "plus": (plus, (8, 8)),
}
# The names programs ask for: X11, Qt and CSS; each a link to a drawing.
ALIASES = {
    "left_ptr": ["default", "arrow", "top_left_arrow", "dnd-move", "move-arrow", "left_arrow", "draped_box"],
    "xterm": ["text", "ibeam"],
    "watch": ["wait"],
    "left_ptr_watch": ["progress", "half-busy"],
    "hand2": ["pointer", "pointing_hand", "hand", "hand1", "dnd-link-hand"],
    "openhand": ["grab", "fleur-open"],
    "closedhand": ["grabbing", "dnd-none-closed"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross"],
    "fleur": ["move", "all-scroll", "size_all"],
    "sb_h_double_arrow": ["ew-resize", "size_hor", "h_double_arrow", "e-resize", "w-resize", "left_side", "right_side"],
    "sb_v_double_arrow": ["ns-resize", "size_ver", "v_double_arrow", "n-resize", "s-resize", "top_side", "bottom_side", "double_arrow"],
    "size_fdiag": ["nwse-resize", "nw-resize", "se-resize", "top_left_corner", "bottom_right_corner"],
    "size_bdiag": ["nesw-resize", "ne-resize", "sw-resize", "top_right_corner", "bottom_left_corner"],
    "split_h": ["col-resize", "sb_h_double_arrow_bar"],
    "split_v": ["row-resize"],
    "crossed_circle": ["not-allowed", "forbidden", "circle", "no-drop"],
    "question_arrow": ["help", "whats_this", "left_ptr_help"],
    "copy": ["dnd-copy", "alias-copy"],
    "link": ["alias", "dnd-link"],
    "dnd-none": ["dnd-no-drop"],
    "plus": ["cell"],
    "pencil": ["draft"],
    "X_cursor": ["pirate"],
}


def render(draw, size):
    drawn, factor = SIZES[size]
    p = Pixels(drawn)
    draw(p)
    rows = []
    for j in range(drawn):
        row = []
        for i in range(drawn):
            c = p.grid[j][i]
            row.append(0 if not c else 0xff000000 | int(c[1:], 16))
        rows.append(row)
    # Whole-number enlargement keeps the pixel edges.
    return [[rows[j // factor][i // factor] for i in range(size)] for j in range(size)]


def xcursor(draw, hotspot):
    """One Xcursor file with an image per size (ARGB, unpremultiplied
    values are fine for opaque and fully transparent pixels)."""
    chunks = []
    for size in sorted(SIZES):
        pixels = render(draw, size)
        hx, hy = (min(size - 1, round(v * size / 16)) for v in hotspot)
        header = struct.pack("<9I", 36, 0xfffd0002, size, 1, size, size, hx, hy, 0)
        body = b"".join(struct.pack("<I", v) for row in pixels for v in row)
        chunks.append((size, header + body))
    toc_len = 16 + 12 * len(chunks)
    out, position, toc = b"", toc_len, b""
    for size, data in chunks:
        toc += struct.pack("<3I", 0xfffd0002, size, position)
        position += len(data)
    out = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(chunks)) + toc + b"".join(d for _, d in chunks)
    return out


def build_cursors(out: Path, name="CDECopperCursors"):
    theme = out / "icons" / name
    folder = theme / "cursors"
    if folder.exists():
        import shutil
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    for cursor, (draw, hotspot) in CURSORS.items():
        (folder / cursor).write_bytes(xcursor(draw, hotspot))
    for target, names in ALIASES.items():
        for alias in names:
            if alias not in CURSORS:
                (folder / alias).symlink_to(target)
    (theme / "index.theme").write_text("[Icon Theme]\nName=CDE\nComment=Cursors after the X11 cursor font of CDE and Motif\n")
