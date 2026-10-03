"""The parts of CDE Copper outside the user's session: the boot splash
(Plymouth) and the boot menu (GRUB), in CDE Copper's colours.

Built into build/system/ by build.py; system.py installs them as root.
Plymouth's script module draws everything from small pieces: one-pixel
colour images it scales into rectangles, a backdrop tile, the logo; the
text is set by Plymouth itself. GRUB gets a whole-screen backdrop and a
nine-piece Motif frame for its menu, the top piece a copper title bar.
No image library: PNGs are written directly.
"""
import struct
import zlib
from pathlib import Path


def png_rgba(width, height, pixels):
    """pixels: rows of (r, g, b, a)."""
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def solid(colour, w=1, h=1):
    return png_rgba(w, h, [[rgb(colour) + (255,)] * w for _ in range(h)])


def logo(size=64):
    """The console's logo from the 16-pixel version, enlarged by whole pixels."""
    from icons import PIXEL, Pixels
    p = Pixels(16)
    PIXEL["cde-menu"](p)
    factor = size // 16
    rows = []
    for j in range(size):
        row = []
        for i in range(size):
            c = p.grid[j // factor][i // factor]
            row.append(rgb(c) + (255,) if c else (0, 0, 0, 0))
        rows.append(row)
    return png_rgba(size, size, rows)


def frame(pieces, P, title=0):
    """A nine-piece Motif frame (GRUB pixmap style): ink outline, light top
    and left, dark bottom and right; with title > 0 the top pieces carry a
    copper title bar of that height."""
    ink, light, dark, face, copper = (rgb(P[k]) + (255,) for k in ("rahmen", "hell", "dunkel", "flaeche", "kopf_aktiv"))
    edge = 4
    top = edge + title

    def colour(x, y, w, h):
        # Position within the whole frame of size w x h.
        if x == 0 or y == 0 or x == w - 1 or y == h - 1:
            return ink
        if title and edge - 1 <= y < top - 1 and 0 < x < w - 1:
            return copper
        if y <= 2 or x <= 2:
            return light if not (y >= h - 3 or x >= w - 3) or (y <= 2 and x <= 2) else dark
        if y >= h - 3 or x >= w - 3:
            return dark
        return face
    # A model frame big enough for all pieces, cut into nine.
    W, H = 3 * edge + 8, top + 8 + edge
    model = [[colour(x, y, W, H) for x in range(W)] for y in range(H)]
    cuts = {"nw": (0, 0, edge, top), "n": (edge, 0, 8, top), "ne": (W - edge, 0, edge, top),
            "w": (0, top, edge, 8), "c": (edge, top, 8, 8), "e": (W - edge, top, edge, 8),
            "sw": (0, H - edge, edge, edge), "s": (edge, H - edge, 8, edge), "se": (W - edge, H - edge, edge, edge)}
    for name, (x, y, w, h) in cuts.items():
        pieces[name] = png_rgba(w, h, [row[x:x + w] for row in model[y:y + h]])


def plymouth_script(P):
    def c(value):
        r, g, b = rgb(value)
        return f"{r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}"
    ink = c(P["rahmen"])
    return f"""# CDE Copper boot splash: a Motif dialog on the tiled backdrop, a meter
# of six blocks for the boot progress, and the passphrase prompt.

W = Window.GetWidth();
H = Window.GetHeight();
Window.SetBackgroundTopColor({c(P["desktop"])});
Window.SetBackgroundBottomColor({c(P["desktop"])});

tile = Image("backdrop.png");
tiles_y = 0;
count = 0;
while (tiles_y < H) {{
    tiles_x = 0;
    while (tiles_x < W) {{
        tiles[count] = Sprite(tile);
        tiles[count].SetPosition(tiles_x, tiles_y, -100);
        count++;
        tiles_x += tile.GetWidth();
    }}
    tiles_y += tile.GetHeight();
}}

ink = Image("ink.png"); face = Image("face.png"); light = Image("light.png");
dark = Image("dark.png"); copper = Image("copper.png"); trough = Image("trough.png"); field = Image("field.png");

fun box(image, x, y, w, h, z) {{
    s = Sprite(image.Scale(w, h));
    s.SetPosition(x, y, z);
    return s;
}}

dw = 460; dh = 210;
dx = Math.Int((W - dw) / 2);
dy = Math.Int((H - dh) / 2);
parts[0] = box(ink, dx, dy, dw, dh, 1);
parts[1] = box(face, dx + 1, dy + 1, dw - 2, dh - 2, 2);
parts[2] = box(light, dx + 1, dy + 1, dw - 2, 2, 3);
parts[3] = box(light, dx + 1, dy + 1, 2, dh - 2, 3);
parts[4] = box(dark, dx + 1, dy + dh - 3, dw - 2, 2, 3);
parts[5] = box(dark, dx + dw - 3, dy + 1, 2, dh - 2, 3);
parts[6] = box(copper, dx + 5, dy + 5, dw - 10, 26, 4);

title_text = Image.Text("CDE Copper", {ink}, 1, "Sans Bold 12");
parts[7] = Sprite(title_text);
parts[7].SetPosition(dx + Math.Int((dw - title_text.GetWidth()) / 2), dy + 18 - Math.Int(title_text.GetHeight() / 2), 5);

logo = Sprite(Image("logo.png"));
logo.SetPosition(dx + 20, dy + 48, 4);

heading = Sprite(Image.Text("Common Desktop Environment", {ink}, 1, "Sans 15"));
heading.SetPosition(dx + 100, dy + 54, 4);
status = Sprite(Image.Text("Starting the system ...", {ink}, 1, "Sans 11"));
status.SetPosition(dx + 100, dy + 84, 4);

# The meter: a sunken well with six blocks.
mx = dx + 18; my = dy + dh - 56; mw = dw - 36; mh = 38;
parts[8] = box(trough, mx, my, mw, mh, 4);
parts[9] = box(dark, mx, my, mw, 2, 5);
parts[10] = box(dark, mx, my, 2, mh, 5);
parts[11] = box(light, mx, my + mh - 2, mw, 2, 5);
parts[12] = box(light, mx + mw - 2, my, 2, mh, 5);
bw = Math.Int((mw - 10 - 5 * 5) / 6);
bh = mh - 10;
lit = copper.Scale(bw, bh);
unlit = face.Scale(bw, bh);
i = 0;
while (i < 6) {{
    blocks[i] = Sprite(unlit);
    blocks[i].SetPosition(mx + 5 + i * (bw + 5), my + 5, 6);
    i++;
}}

fun progress_callback(duration, progress) {{
    n = Math.Int(progress * 6 + 0.999);
    i = 0;
    while (i < 6) {{
        if (i < n) blocks[i].SetImage(lit); else blocks[i].SetImage(unlit);
        i++;
    }}
}}
Plymouth.SetBootProgressFunction(progress_callback);

fun message_callback(text) {{
    status.SetImage(Image.Text(text, {ink}, 1, "Sans 11"));
}}
Plymouth.SetMessageFunction(message_callback);

# The passphrase of an encrypted disk: a sunken field in the dialog.
fun password_callback(prompt, bullets) {{
    status.SetImage(Image.Text(prompt, {ink}, 1, "Sans 11"));
    if (!pw_field) {{
        pw_field = box(field, dx + 100, dy + 108, dw - 120, 26, 6);
        pw_edge = box(dark, dx + 100, dy + 108, dw - 120, 2, 7);
    }}
    pw_field.SetOpacity(1); pw_edge.SetOpacity(1);
    stars = "";
    i = 0;
    while (i < bullets) {{ stars += "*"; i++; }}
    pw_text = Sprite(Image.Text(stars + " ", {ink}, 1, "Sans 14"));
    pw_text.SetPosition(dx + 108, dy + 112, 8);
}}
Plymouth.SetDisplayPasswordFunction(password_callback);

fun normal_callback() {{
    if (pw_field) {{ pw_field.SetOpacity(0); pw_edge.SetOpacity(0); }}
    pw_text = NULL;
    status.SetImage(Image.Text("Starting the system ...", {ink}, 1, "Sans 11"));
}}
Plymouth.SetDisplayNormalFunction(normal_callback);
"""


MENU_WIDTH, TITLE_HEIGHT = 640, 34


def grub_theme(P):
    """GRUB draws image components over everything else, a label on an image
    included, and draws no progress bar without the timeout's id; so the
    title bar is an image with its text already in it, above the menu, both
    a fixed 640 pixels wide."""
    ink, copper = P["rahmen"], P["kopf_aktiv"]
    half = MENU_WIDTH // 2
    return f"""# CDE Copper boot menu: the backdrop, a Motif window with a copper title
# bar, the selection in copper.
desktop-image: "background.png"
desktop-image-scale-method: "crop"
desktop-color: "{P["desktop"]}"
title-text: ""
terminal-font: "IBM Plex Mono Regular 16"

+ image {{
    left = 50%-{half}
    top = 22%
    file = "title.png"
}}

+ boot_menu {{
    left = 50%-{half}
    top = 22%+{TITLE_HEIGHT}
    width = {MENU_WIDTH}
    height = 32%
    item_font = "IBM Plex Sans Condensed Regular 20"
    item_color = "{ink}"
    selected_item_color = "{ink}"
    item_height = 34
    item_padding = 12
    item_spacing = 4
    icon_width = 0
    icon_height = 0
    item_icon_space = 0
    menu_pixmap_style = "menu_*.png"
    selected_item_pixmap_style = "select_*.png"
    scrollbar = false
}}

+ progress_bar {{
    id = "__timeout__"
    left = 50%-{half}
    top = 54%+{TITLE_HEIGHT + 14}
    width = {MENU_WIDTH}
    height = 28
    font = "IBM Plex Sans Condensed Regular 20"
    text = "@TIMEOUT_NOTIFICATION_LONG@"
    text_color = "{ink}"
    fg_color = "{copper}"
    bg_color = "{P["rille"]}"
    border_color = "{ink}"
}}
"""


def title_bar(P, width=MENU_WIDTH, height=TITLE_HEIGHT):
    """The copper title bar: ink outline, light top and left, dark bottom
    and right, as the window frame draws it."""
    ink, light, dark, copper = (rgb(P[k]) + (255,) for k in ("rahmen", "hell", "dunkel", "kopf_aktiv"))
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                row.append(ink)
            elif (y <= 2 or x <= 2) and not (y >= height - 3 or x >= width - 3):
                row.append(light)
            elif y >= height - 3 or x >= width - 3:
                row.append(dark)
            else:
                row.append(copper)
        rows.append(row)
    try:
        # The title set into the image (build machine only; without Pillow
        # the bar stays plain).
        from PIL import Image, ImageDraw, ImageFont
        import io
        image = Image.frombytes("RGBA", (width, height), b"".join(bytes(p) for row in rows for p in row))
        font = ImageFont.truetype(str(Path(__file__).resolve().parent / "fonts/IBMPlex/IBMPlexSansCondensed-SemiBold.otf"), 18)
        draw = ImageDraw.Draw(image)
        box = draw.textbbox((0, 0), "CDE Copper", font=font)
        draw.text(((width - box[2] - box[0]) // 2, (height - box[3] - box[1]) // 2), "CDE Copper", font=font, fill=P["kopf_aktiv_text"])
        out = io.BytesIO()
        image.save(out, "PNG")
        return out.getvalue()
    except (ImportError, OSError):
        return png_rgba(width, height, rows)


def build_system(out: Path, P):
    import backdrops
    import palettes
    base = out / "system"
    colours = backdrops.colours_for(palettes.copper_desktop())
    # Plymouth.
    ply = base / "plymouth/cde-copper"
    ply.mkdir(parents=True, exist_ok=True)
    (ply / "cde-copper.plymouth").write_text(
        "[Plymouth Theme]\nName=CDE Copper\nDescription=A Motif dialog on the CDE backdrop with a meter for the boot progress\n"
        "ModuleName=script\n\n[script]\nImageDir=/usr/share/plymouth/themes/cde-copper\n"
        "ScriptFile=/usr/share/plymouth/themes/cde-copper/cde-copper.script\n")
    (ply / "cde-copper.script").write_text(plymouth_script(P))
    for name, key in (("ink", "rahmen"), ("face", "flaeche"), ("light", "hell"), ("dark", "dunkel"),
                      ("copper", "kopf_aktiv"), ("trough", "rille"), ("field", "fenster")):
        (ply / f"{name}.png").write_bytes(solid(P[key]))
    (ply / "backdrop.png").write_bytes(backdrops.render("Lattice", colours))
    (ply / "logo.png").write_bytes(logo(64))
    # GRUB (fonts are made at installation with grub2-mkfont).
    grub = base / "grub/cde-copper"
    grub.mkdir(parents=True, exist_ok=True)
    (grub / "theme.txt").write_text(grub_theme(P))
    (grub / "background.png").write_bytes(backdrops.desktop("Lattice", colours, 1920, 1080))
    (grub / "title.png").write_bytes(title_bar(P))
    pieces = {}
    frame(pieces, P)
    for name, data in pieces.items():
        (grub / f"menu_{name}.png").write_bytes(data)
    select = {name: png_rgba(*size, [[rgb(P["kopf_aktiv"]) + (255,)] * size[0] for _ in range(size[1])])
              for name, size in (("nw", (2, 2)), ("n", (8, 2)), ("ne", (2, 2)), ("w", (2, 8)), ("c", (8, 8)),
                                 ("e", (2, 8)), ("sw", (2, 2)), ("s", (8, 2)), ("se", (2, 2)))}
    for name, data in select.items():
        (grub / f"select_{name}.png").write_bytes(data)
