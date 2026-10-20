#!/usr/bin/env python3
"""Warp Legacy Neon 2026 icon set: the icons of the user's concept image.

Unlike icons_neon.py (own drawings), this set reproduces the icons of
reference/neon-2026.png as closely as possible. Each master in
icons-neon2026/masters/<name>.png (256 px RGBA) was made from the concept:
cut out (label removed), 4x-UltraSharp, a light Z-Image img2img pass for
clean edges, then matted off the navy background so the glow survives as a
translucent fringe. The pipeline lives in icons-neon2026/_work/.
Brand-like icons of the concept (Nextcloud, Teams, Office) are left out.

Anything not in the concept is inherited from WarpLegacyNeon.

    build_icons(out_dir)     -> out_dir/WarpLegacyNeon2026/{index.theme, NxN/...}
    python3 icons_neon2026.py -> build-icons-preview-2026/ + uebersicht.png
                                 + vergleich.png (concept left, icon right)
"""
import math
import os
import pathlib
import shutil
import sys
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MASTERS = HERE / "icons-neon2026" / "masters"
CONCEPT = HERE / "reference" / "neon-2026.png"
# Every size Dolphin offers: KIconLoader takes fixed directories only
# (see icons_neon.py), a missing 96 would be scaled from another size.
SIZES = (16, 22, 24, 32, 48, 64, 96, 128, 256)
BG = (0x0a, 0x15, 0x2e)

CONTEXTS = {"places": "Places", "devices": "Devices", "apps": "Applications",
            "categories": "Categories", "mimetypes": "MimeTypes",
            "actions": "Actions", "status": "Status"}

# icon name -> (context, concept element, tight box in the concept)
ICONS = {
    "user-desktop": ("places", "Workplace (desktop)", (30, 79, 74, 126)),
    "computer": ("devices", "My Computer (desktop)", (31, 166, 75, 211)),
    "network-workgroup": ("places", "Network (desktop)", (30, 249, 74, 294)),
    "applications-internet": ("categories", "Internet (desktop)", (24, 335, 78, 383)),
    "folder": ("places", "Files (desktop)", (31, 423, 72, 465)),
    "applications-other": ("categories", "Applications (desktop)", (31, 505, 72, 546)),
    "folder-templates": ("places", "Templates (desktop)", (32, 592, 71, 636)),
    "preferences-system": ("categories", "Settings (desktop)", (29, 679, 71, 722)),
    "applications-games": ("categories", "Games (desktop)", (29, 768, 71, 810)),
    "system-shutdown": ("actions", "Shut Down (desktop)", (32, 864, 69, 902)),
    "drive-harddisk": ("devices", "Drives (WPS)", (172, 153, 225, 192)),
    "preferences-system-details": ("categories", "System (WPS)", (275, 148, 309, 195)),
    "folder-applications": ("places", "Programs (WPS)", (362, 153, 405, 196)),
    "office-calendar": ("apps", "2026 (WPS)", (464, 151, 506, 195)),
    "folder-documents": ("places", "Documents (WPS)", (559, 153, 601, 193)),
    "folder-pictures": ("places", "Pictures (WPS)", (170, 242, 218, 284)),
    "folder-videos": ("places", "Videos (WPS)", (267, 242, 313, 286)),
    "folder-music": ("places", "Music (WPS)", (362, 239, 406, 288)),
    "folder-download": ("places", "Downloads (WPS)", (462, 244, 505, 284)),
    "folder-development": ("places", "Projects (WPS)", (557, 244, 600, 284)),
    "cpu": ("devices", "AI (WPS)", (636, 246, 682, 291)),
    "folder-cloud": ("places", "Cloud (WPS)", (165, 338, 221, 377)),
    "internet-web-browser": ("apps", "Browser (WPS)", (542, 337, 585, 380)),
    "utilities-terminal": ("apps", "Terminal (WPS)", (632, 343, 680, 379)),
    "user-home": ("places", "Docs, house folder (C:\\Projects)", (1252, 508, 1292, 547)),
    "x-office-spreadsheet": ("mimetypes", "FINANCE (C:\\Projects)", (1055, 592, 1096, 634)),
    "folder-locked": ("places", "Private (C:\\Projects)", (1124, 591, 1159, 633)),
    "folder-temp": ("places", "Temp (C:\\Projects)", (1187, 593, 1226, 631)),
    "text-plain": ("mimetypes", "TODO.txt (C:\\Projects)", (1254, 592, 1287, 634)),
    "video-display": ("devices", "Display (Control Panel)", (1042, 783, 1082, 826)),
    "audio-volume-high": ("status", "Sound (Control Panel)", (1133, 783, 1170, 824)),
    "preferences-system-network": ("categories", "Network (Control Panel)", (1223, 781, 1262, 824)),
    "security-high": ("status", "Security (Control Panel)", (1411, 780, 1448, 823)),
    "input-keyboard": ("devices", "Keyboard (Control Panel)", (952, 858, 993, 889)),
    "input-mouse": ("devices", "Mouse (Control Panel)", (1044, 855, 1078, 892)),
    "printer": ("devices", "Printers (Control Panel)", (1132, 853, 1172, 895)),
    "preferences-system-power": ("categories", "Power (Control Panel)", (1223, 854, 1261, 894)),
    "preferences-system-time": ("categories", "Date/Time (Control Panel)", (1320, 854, 1355, 893)),
    "preferences-desktop": ("categories", "Workspace (Control Panel)", (1412, 853, 1452, 894)),
}

# (context, alias) -> target icon name
ALIASES = {
    ("places", "folder-open"): "folder",
    ("places", "folder-blue"): "folder",
    ("mimetypes", "inode-directory"): "folder",
    ("places", "folder-home"): "user-home",
    ("places", "folder-downloads"): "folder-download",
    ("places", "folder-image"): "folder-pictures",
    ("places", "folder-video"): "folder-videos",
    ("places", "folder-sound"): "folder-music",
    ("mimetypes", "audio-x-generic"): "folder-music",
    ("places", "folder-projects"): "folder-development",
    ("places", "folder-network"): "network-workgroup",
    ("actions", "system-lock-screen"): "folder-locked",
    ("status", "object-locked"): "folder-locked",
    ("mimetypes", "text-x-generic"): "text-plain",
    ("mimetypes", "text-x-generic-template"): "folder-templates",
    ("mimetypes", "application-vnd.oasis.opendocument.spreadsheet"): "x-office-spreadsheet",
    ("actions", "office-chart-bar"): "x-office-spreadsheet",
    ("mimetypes", "x-office-calendar"): "office-calendar",
    ("apps", "org.kde.konsole"): "utilities-terminal",
    ("apps", "konsole"): "utilities-terminal",
    ("apps", "systemsettings"): "preferences-system",
    ("actions", "configure"): "preferences-system",
    ("categories", "applications-system"): "preferences-system",
    ("categories", "applications-all"): "applications-other",
    ("devices", "input-gaming"): "applications-games",
    ("devices", "drive-harddisk-solidstate"): "drive-harddisk",
    ("apps", "hwinfo"): "preferences-system-details",
    ("apps", "org.kde.kinfocenter"): "preferences-system-details",
    ("categories", "preferences-desktop-display"): "video-display",
    ("devices", "audio-speakers"): "audio-volume-high",
    ("devices", "audio-card"): "audio-volume-high",
    ("categories", "preferences-desktop-sound"): "audio-volume-high",
    ("apps", "multimedia-volume-control"): "audio-volume-high",
    ("categories", "preferences-security"): "security-high",
    ("categories", "preferences-desktop-keyboard"): "input-keyboard",
    ("categories", "preferences-desktop-mouse"): "input-mouse",
    ("categories", "preferences-devices-printer"): "printer",
    ("devices", "printer-network"): "printer",
    ("categories", "preferences-system-power-management"): "preferences-system-power",
    ("categories", "preferences-desktop-theme-global"): "preferences-desktop",
    ("apps", "web-browser"): "internet-web-browser",
}


def _premul_resize(img, s):
    """Downscale in premultiplied alpha (no dark/navy fringes)."""
    out = img.convert("RGBa").resize((s, s), Image.LANCZOS)
    if s <= 32:  # small sizes: a little crispness back after the big reduction
        out = out.filter(ImageFilter.UnsharpMask(radius=0.6, percent=70 if s <= 22 else 45,
                                                 threshold=0))
    return out.convert("RGBA")


def render(name, s):
    return _premul_resize(Image.open(MASTERS / f"{name}.png").convert("RGBA"), s)


def build_icons(out, name="WarpLegacyNeon2026"):
    """Write a complete freedesktop icon theme to out/<name>/.

    Returns the theme directory. Existing content of out/<name> is replaced.
    """
    out = pathlib.Path(out)
    root = out / name
    if root.exists():
        shutil.rmtree(root)
    dirs = set()
    missing = []
    for n, (ctx, _src, _box) in ICONS.items():
        if not (MASTERS / f"{n}.png").exists():
            missing.append(n)
            continue
        for s in SIZES:
            d = root / f"{s}x{s}" / ctx
            d.mkdir(parents=True, exist_ok=True)
            dirs.add((s, ctx))
            render(n, s).save(d / f"{n}.png", optimize=True)
    for (ctx, alias), target in ALIASES.items():
        if target in missing:
            continue
        tctx = ICONS[target][0]
        if (ctx, alias) == (tctx, target):
            continue
        for s in SIZES:
            d = root / f"{s}x{s}" / ctx
            d.mkdir(parents=True, exist_ok=True)
            dirs.add((s, ctx))
            link = d / f"{alias}.png"
            rel = f"{target}.png" if tctx == ctx else f"../{tctx}/{target}.png"
            if link.exists() or link.is_symlink():
                link.unlink()
            os.symlink(rel, link)
    order = sorted(dirs)
    lines = ["[Icon Theme]", "Name=Warp Legacy Neon 2026",
             "Comment=The icons of the Warp 2026 neon concept, glow included",
             "Inherits=WarpLegacyNeon,breeze-dark,hicolor", "Example=folder",
             "DisplayDepth=32",
             "Directories=" + ",".join(f"{s}x{s}/{c}" for s, c in order), ""]
    for s, c in order:
        lines += [f"[{s}x{s}/{c}]", f"Size={s}", f"Context={CONTEXTS[c]}",
                  "Type=Fixed", ""]
    (root / "index.theme").write_text("\n".join(lines))
    if missing:
        print("warning: masters missing:", ", ".join(missing), file=sys.stderr)
    return root


def _font(px):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", px)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(root, dest, sizes=(16, 22, 32, 48, 128)):
    names = [(c, n) for n, (c, _, _) in ICONS.items()
             if (root / "16x16" / c / f"{n}.png").exists()]
    pad, gap = 14, 10
    cw = sum(sizes) + gap * (len(sizes) - 1) + 2 * pad
    ch = max(sizes) + 2 * pad + 18
    cols = 4
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), BG + (255,))
    font = _font(12)
    dr = ImageDraw.Draw(sheet)
    for i, (ctx, n) in enumerate(names):
        x0, y0 = (i % cols) * cw + pad, (i // cols) * ch + pad
        x = x0
        for s in sizes:
            im = Image.open(root / f"{s}x{s}" / ctx / f"{n}.png")
            sheet.alpha_composite(im, (x, y0 + (max(sizes) - s) // 2))
            x += s + gap
        dr.text((x0, y0 + max(sizes) + 4), n, fill=(0xe8, 0xf0, 0xff), font=font)
    sheet.convert("RGB").save(dest)


def comparison(root, dest, zoom=128):
    """Per icon: concept crop | own icon, at concept size and enlarged."""
    concept = Image.open(CONCEPT).convert("RGB")
    names = [n for n, (c, _, _) in ICONS.items() if (root / "16x16" / c / f"{n}.png").exists()]
    cols = 3
    cell_w, cell_h = 2 * 72 + 2 * zoom + 5 * 8, zoom + 30
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), BG + (255,))
    dr = ImageDraw.Draw(sheet)
    font = _font(11)
    for i, n in enumerate(names):
        ctx, src, (x0, y0, x1, y1) = ICONS[n]
        side = max(x1 - x0, y1 - y0)
        # same framing as the masters: core fills 204/256 of the tile
        tile = round(side * 256 / 204)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        crop = concept.crop((round(cx - tile / 2), round(cy - tile / 2),
                             round(cx - tile / 2) + tile, round(cy - tile / 2) + tile))
        own = Image.open(MASTERS / f"{n}.png").convert("RGBA")
        bx, by = (i % cols) * cell_w + 8, (i // cols) * cell_h + 4
        # 1:1 size as in the concept
        sheet.paste(crop, (bx, by + (zoom - tile) // 2))
        small = Image.new("RGBA", (tile, tile), BG + (255,))
        small.alpha_composite(_premul_resize(own, tile))
        sheet.paste(small, (bx + 72 + 8, by + (zoom - tile) // 2))
        # enlarged
        sheet.paste(crop.resize((zoom, zoom), Image.LANCZOS), (bx + 2 * 72 + 16, by))
        big = Image.new("RGBA", (zoom, zoom), BG + (255,))
        big.alpha_composite(_premul_resize(own, zoom))
        sheet.paste(big, (bx + 2 * 72 + zoom + 24, by))
        dr.text((bx, by + zoom + 4), f"{n}  <-  {src}", fill=(0xe8, 0xf0, 0xff), font=font)
    sheet.convert("RGB").save(dest)


if __name__ == "__main__":
    prev = HERE / "build-icons-preview-2026"
    prev.mkdir(exist_ok=True)
    t = time.time()
    root = build_icons(prev)
    contact_sheet(root, prev / "uebersicht.png")
    comparison(root, prev / "vergleich.png")
    print(f"{len(ICONS)} icons, {len(ALIASES)} aliases, {len(SIZES)} sizes -> {root} "
          f"({time.time() - t:.1f} s)")
