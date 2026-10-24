"""Vorschau aus den erzeugten Dateien — ohne VM, ohne laufendes Plasma.

Setzt Plasma-Style- und Aurorae-SVGs per Element-ID zusammen (frames.py),
legt Text mit PIL darauf und baut je Variante ein Bild: Desktop mit Panel,
Fenster und Popup, darunter GRUB und Plymouth. Ersetzt den VM-Test nicht,
zeigt aber in Sekunden, ob Farben und Formen zusammenpassen.
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont

from . import frames
from .palette import rgb

UI_FONT = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"


def _font(size, path=None):
    for p in (path, UI_FONT, "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"):
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _svg(path):
    with open(path) as f:
        return f.read()


def _rc(path):
    vals = {}
    for line in open(path):
        m = re.match(r"(\w+)=(.*)", line.strip())
        if m:
            vals[m.group(1)] = m.group(2)
    return vals


def window(pkg, var, w, h, title, display_font, active=True):
    base = f"{pkg}/aurorae/themes/{var.camel}"
    rc = _rc(f"{base}/{var.camel}rc")
    deco = frames.renderer(_svg(f"{base}/decoration.svg"))
    prefix = "decoration" if active else "decoration-inactive"
    im = frames.compose(frames.parts(deco, prefix), w, h)
    th, bs = int(rc["TitleHeight"]), int(rc["ButtonWidth"])
    border = int(rc["BorderLeft"])
    d = ImageDraw.Draw(im)
    col = tuple(int(x) for x in rc["ActiveTextColor" if active else "InactiveTextColor"].split(","))
    f = _font(13, display_font)
    tw = d.textlength(title, font=f)
    align = rc.get("TitleAlignment", "Left")
    tx = {"Left": border + 8 + bs + 6, "Center": (w - tw) / 2, "Right": w - tw - 3 * (bs + 4) - 12}[align]
    d.text((tx, th / 2), title, font=f, fill=col, anchor="lm")
    x = w - border - 4
    for b in ("close", "maximize", "minimize"):
        r = frames.renderer(_svg(f"{base}/{b}.svg"))
        state = "active" if active else "inactive"
        if b == "close" and active:
            state = "hover"
        btn = frames.element(r, f"{state}-center", bs, bs)
        x -= bs
        im.alpha_composite(btn, (int(x), int((th - bs) / 2)))
        x -= 3
    menu = frames.element(frames.renderer(_svg(f"{base}/menu.svg")), "active-center", bs, bs)
    im.alpha_composite(menu, (border + 4, int((th - bs) / 2)))
    return im, th, border


def _icon(pkg, var, name, size):
    """Symbol aus dem erzeugten Icon-Theme, sonst None."""
    import glob
    hits = glob.glob(f"{pkg}/icons/{var.camel}Icons/{size}x{size}/*/{name}.png")
    return Image.open(hits[0]).convert("RGBA") if hits else None


def desktop(pkg, var, spec, display_font, W=1600, H=900):
    P = var.P
    dt = f"{pkg}/plasma/desktoptheme/{var.id}"
    wall = Image.open(f"{pkg}/wallpapers/{var.id}/contents/images/1920x1080.jpg").convert("RGBA").resize((W, H))
    im = wall.copy()
    ui = _font(14)
    # Panel unten
    panel_h = 44
    panel = frames.frame(_svg(f"{dt}/widgets/panel-background.svg"), "south", W, panel_h)
    im.alpha_composite(panel, (0, H - panel_h))
    tasks = frames.renderer(_svg(f"{dt}/widgets/tasks.svg"))
    tp = {k: frames.compose(frames.parts(tasks, k), 200, 36) for k in ("normal", "focus", "hover")}
    d = ImageDraw.Draw(im)
    for i, (state, label) in enumerate([("focus", "Dateien"), ("normal", "Terminal"), ("hover", "Browser")]):
        x = 60 + i * 206
        im.alpha_composite(tp[state], (x, H - panel_h + 4))
        d.text((x + 100, H - panel_h / 2), label, font=ui, fill=rgb(P["text"]), anchor="mm")
    d.text((W - 60, H - panel_h / 2), "13:37", font=ui, fill=rgb(P["text"]), anchor="mm")
    start = _icon(pkg, var, "start-here", 32)
    if start:
        im.alpha_composite(start, (14, H - panel_h + 6))
        for i, app in enumerate(["system-file-manager", "utilities-terminal", "internet-web-browser"]):
            ic = _icon(pkg, var, app, 24)
            if ic:
                im.alpha_composite(ic, (60 + i * 206 + 10, H - panel_h + 10))
        for i, (name, label) in enumerate([("computer", "Computer"), ("user-home", "Persönlich"),
                                           ("network-workgroup", "Netzwerk"), ("user-trash-full", "Papierkorb")]):
            ic = _icon(pkg, var, name, 64)
            if ic:
                im.alpha_composite(ic, (24, 120 + i * 100))
                d.text((56, 120 + i * 100 + 74), label, font=_font(12), fill=(255, 255, 255), anchor="mm",
                       stroke_width=2, stroke_fill=(0, 0, 0))
    # Fenster
    ww, wh = 760, 470
    win, th, border = window(pkg, var, ww, wh, "Dateien — Einsatzbefehle", display_font)
    wd = ImageDraw.Draw(win)
    view = frames.renderer(_svg(f"{dt}/widgets/viewitem.svg"))
    cx, cy, cw = border + 8, th + 10, ww - 2 * border - 16
    wd.rectangle([cx, cy, cx + cw, wh - border - 10], fill=rgb(P["window"]))
    for i, name in enumerate(["Basis", "Kraftwerk", "Kaserne", "Radar", "Raffinerie", "Werft", "Labor"]):
        y = cy + 6 + i * 30
        if i == 2:
            win.alpha_composite(frames.compose(frames.parts(view, "selected"), cw - 12, 28), (cx + 6, y))
            col = P["selection_text"]
        elif i == 4:
            win.alpha_composite(frames.compose(frames.parts(view, "hover"), cw - 12, 28), (cx + 6, y))
            col = P["text"]
        else:
            col = P["text"]
        wd.text((cx + 18, y + 14), f"{name}", font=ui, fill=rgb(col), anchor="lm")
        wd.text((cx + cw - 20, y + 14), f"{(i + 3) * 117} KB", font=ui, fill=rgb(P["text2"] if i != 2 else col),
                anchor="rm")
    wd.text((cx + 18, cy + 240), "Link: einsatzplan.txt", font=ui, fill=rgb(P["link"]), anchor="lm")
    if _icon(pkg, var, "folder", 64):
        wd.rectangle([cx, cy, cx + cw, wh - border - 10], fill=rgb(P["window"]))
        grid = ["folder", "folder-documents", "folder-download", "folder-pictures", "folder-music",
                "folder-videos", "application-pdf", "image-x-generic", "package-x-generic", "text-x-script"]
        labels = ["Einsätze", "Dokumente", "Downloads", "Bilder", "Musik", "Videos", "befehl.pdf",
                  "karte.png", "nachschub.zip", "start.sh"]
        for i, (n, lab) in enumerate(zip(grid, labels)):
            ic = _icon(pkg, var, n, 64)
            gx, gy = cx + 20 + (i % 5) * 140, cy + 14 + (i // 5) * 120
            if i == 1:
                sel = frames.compose(frames.parts(view, "selected"), 120, 104)
                win.alpha_composite(sel, (gx - 8, gy - 6))
            if ic:
                win.alpha_composite(ic, (gx + 20, gy))
            wd.text((gx + 52, gy + 84), lab, font=ui, anchor="mm",
                    fill=rgb(P["selection_text"] if i == 1 else P["text"]))
    im.alpha_composite(win, (120, 90))
    # Popup mit Knöpfen
    pw, ph = 380, 230
    pop = frames.frame(_svg(f"{dt}/dialogs/background.svg"), "", pw, ph)
    pd = ImageDraw.Draw(pop)
    pd.text((20, 26), "Startmenü", font=_font(18, display_font), fill=rgb(P["text"]), anchor="lm")
    btn = frames.renderer(_svg(f"{dt}/widgets/button.svg"))
    for i, (state, label) in enumerate([("normal", "Normal"), ("hover", "Hover"), ("pressed", "Gedrückt")]):
        b = frames.compose(frames.parts(btn, state), 104, 34)
        pop.alpha_composite(b, (18 + i * 116, 60))
        pd.text((70 + i * 116, 77), label, font=ui, fill=rgb(P["text"]), anchor="mm")
    le = frames.renderer(_svg(f"{dt}/widgets/lineedit.svg"))
    pop.alpha_composite(frames.compose(frames.parts(le, "base"), 340, 32), (18, 112))
    pd.text((30, 128), "Suchen …", font=ui, fill=rgb(P["text2"]), anchor="lm")
    bar = frames.renderer(_svg(f"{dt}/widgets/bar_meter_horizontal.svg"))
    pop.alpha_composite(frames.compose(frames.parts(bar, "bar-inactive"), 340, 12), (18, 166))
    pop.alpha_composite(frames.compose(frames.parts(bar, "bar-active"), 210, 12), (18, 166))
    pd.text((20, 200), "Energie 62 %", font=ui, fill=rgb(P["text2"]), anchor="lm")
    im.alpha_composite(pop, (W - pw - 60, H - panel_h - ph - 12))
    return im


def grub(pkg, var, spec, W=960, H=540):
    """GRUB-Ansicht: Hintergrund + 9-Patch-Menü mit drei Einträgen."""
    base = f"{pkg}/system/grub/{var.camel}"
    bg = Image.open(f"{base}/background.png").convert("RGBA")
    theme = open(f"{base}/theme.txt").read()
    left_panel = 'left = 50\n' in theme
    names = {"topleft": "nw", "top": "n", "topright": "ne", "left": "w", "center": "c",
             "right": "e", "bottomleft": "sw", "bottom": "s", "bottomright": "se"}
    menu = {p: Image.open(f"{base}/menu_{s}.png").convert("RGBA") for p, s in names.items()}
    sel = {p: Image.open(f"{base}/select_{s}.png").convert("RGBA") for p, s in names.items()}
    if left_panel:
        x, y, w, h = 50, int(1080 * 0.45), 580, int(1080 * 0.45)
    else:
        x, y, w, h = 960 - 380, int(1080 * 0.38), 760, int(1080 * 0.44)
    bg.alpha_composite(frames.compose(menu, w, h), (x, y))
    d = ImageDraw.Draw(bg)
    ttf = f"{pkg}/fonts/{spec['font']}.ttf"
    f = _font(22, ttf)
    pad = menu["topleft"].width
    for i, entry in enumerate(["Nobara Linux (7.2.9)", "Nobara Linux (Rettungsmodus)", "UEFI-Einstellungen"]):
        ey = y + pad + 6 + i * 42
        if i == 0:
            bg.alpha_composite(frames.compose(sel, w - 2 * pad, 38), (x + pad, ey))
        d.text((x + pad + 14, ey + 19), entry, font=f, anchor="lm",
               fill=rgb(var.P["selection_text"] if i == 0 else var.P["text"]))
    return bg.resize((W, H), Image.LANCZOS)


def plymouth(pkg, var, W=960, H=540):
    base = f"{pkg}/system/plymouth/{var.id}"
    bg = Image.open(f"{base}/background.png").convert("RGBA")
    script = open(f"{base}/{var.id}.script").read()
    em = Image.open(f"{base}/emblem.png").convert("RGBA")
    label = Image.open(f"{base}/label.png").convert("RGBA")
    track = Image.open(f"{base}/track.png").convert("RGBA")
    fill = Image.open(f"{base}/fill.png").convert("RGBA")
    cy = int(1080 * 0.42)
    if "emblem.sprite.SetOpacity(1)" in script:
        bg.alpha_composite(em, ((1920 - em.width) // 2, cy - em.height))
    bg.alpha_composite(label, ((1920 - label.width) // 2, cy + 8))
    ty = cy + 8 + label.height + 20
    tx = (1920 - track.width) // 2
    bg.alpha_composite(track, (tx, ty))
    bg.alpha_composite(fill.resize((int((track.width - 8) * 0.6), fill.height)), (tx + 4, ty + 4))
    return bg.resize((W, H), Image.LANCZOS)


def sheet(pkg, variants, spec, dst):
    """Ein Bild je Variante: Desktop oben, GRUB und Plymouth darunter."""
    ttf = f"{pkg}/fonts/{spec['font']}.ttf"
    rows = []
    for var in variants:
        top = desktop(pkg, var, spec, ttf)
        g = grub(pkg, var, spec, 800, 450)
        p = plymouth(pkg, var, 800, 450)
        im = Image.new("RGBA", (1600, 900 + 450), (20, 20, 20, 255))
        im.alpha_composite(top, (0, 0))
        im.alpha_composite(g, (0, 900))
        im.alpha_composite(p, (800, 900))
        rows.append(im)
    out = Image.new("RGB", (1600, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        out.paste(r.convert("RGB"), (0, y))
        y += r.height
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst, quality=88)
    return dst
