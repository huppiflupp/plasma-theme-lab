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

Two exceptions to "master as is": the Internet globe (internet-web-browser,
applications-internet) is drawn per size from icons-neon2026/globe-body.png
with its own orbit ring (globe()), and the folder bodies are lifted to the
lighter azure of the concept's folders at build time (lighten_folder()).

Violet variant: icons-neon2026/masters-violett/<name>.png holds violet
versions of the icons that are mostly cyan in the concept (hue-shifted rims
and glow toward violet-magenta at the lower right, then a light img2img pass;
or a violet twin of the motif elsewhere in the concept). Icons without a
violet master use the normal one.

    build_icons(out_dir)     -> out_dir/WarpLegacyNeon2026/{index.theme, NxN/...}
    build_icons(out_dir, "WarpLegacyNeon2026Violett", violet=True)
    python3 icons_neon2026.py -> build-icons-preview-2026/ + uebersicht.png
                                 + vergleich.png (concept left, icon right)
                                 + violett-vergleich.png (concept, cyan, violet)
"""
import math
import os
import pathlib
import shutil
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MASTERS = HERE / "icons-neon2026" / "masters"
MASTERS_VIOLET = HERE / "icons-neon2026" / "masters-violett"
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


def master(name, violet=False):
    """Path of the master for an icon (violet one if asked for and present)."""
    if violet and (MASTERS_VIOLET / f"{name}.png").exists():
        return MASTERS_VIOLET / f"{name}.png"
    return MASTERS / f"{name}.png"


# --- Internet globe: drawn per size ------------------------------------------
# The concept's thin orbit vanished below 48 px and the Browser master had no
# violet at all. The sphere comes from icons-neon2026/globe-body.png (the
# "Internet" desktop globe with its orbit inpainted away, see
# _work/globe_body.py); ring, magenta rim light and glow are drawn here, the
# ring at least ~1.6 px wide at every size. Both globe names share it.
GLOBE_BODY = HERE / "icons-neon2026" / "globe-body.png"
GLOBES = ("internet-web-browser", "applications-internet")
_GLOBE_SPHERE = (129, 128, 77)                  # centre x, y, radius in globe-body.png
_GLOBE_ORBIT = (127, 122.5, 96, 25, -27.5)      # centre x, y, semi-axes, tilt (same frame)
_GLOBE_SCALE = 1.15     # body and orbit enlarged about the tile centre: the
                        # concept's orbit is ~1.25x the sphere wide, not 1.4x
# ring colour along the major axis (-1 = left end, +1 = right end):
# cyan at the left, magenta in front of the globe, violet at the right
_GLOBE_FRONT = {False: [(-1, (70, 232, 255)), (-0.25, (90, 205, 255)),
                        (0.3, (255, 84, 222)), (1, (156, 96, 255))],
                True: [(-1, (150, 130, 255)), (-0.2, (215, 96, 255)),
                       (0.3, (255, 84, 210)), (1, (168, 88, 255))]}
_GLOBE_BACK = {False: [(-1, (70, 232, 255)), (0.4, (64, 176, 255)), (1, (156, 96, 255))],
               True: [(-1, (150, 130, 255)), (0.4, (128, 104, 255)), (1, (168, 88, 255))]}
_GLOBE_GLOW = {False: (40, 112, 255), True: (124, 72, 255)}


def _ramp(stops, t):
    """Colour stops [(t, rgb), ...] -> float array (h, w, 3) for t (h, w)."""
    ts = [p for p, _ in stops]
    return np.dstack([np.interp(t, ts, [c[i] for _, c in stops]) for i in range(3)])


def globe(s, violet=False):
    """The Internet globe at s px: sphere, orbit in front/behind, glow."""
    C = 512
    k = C / 256
    w = max(0.042 * s, 1.6) * C / s           # ring width on the canvas
    # small sizes: less room needed for the glow, a more open ring
    small = min(max((48 - s) / 26, 0), 1)       # 0 at >= 48 px, 1 at <= 22 px
    f = _GLOBE_SCALE + 0.1 * small
    ecx, ecy, ea, eb, eang = _GLOBE_ORBIT
    ecx, ecy, ea, eb = (128 + (ecx - 128) * f, 128 + (ecy - 128) * f, ea * f,
                        eb * f * (1 + 0.2 * small))
    yy, xx = np.mgrid[0:C, 0:C] + 0.5
    # orbit in its own frame: u along the major axis, v across
    t = math.radians(eang)
    dx, dy = xx - ecx * k, yy - ecy * k
    u = (dx * math.cos(t) + dy * math.sin(t)) / (ea * k)
    v = (-dx * math.sin(t) + dy * math.cos(t)) / (eb * k)
    r = np.hypot(u, v)
    # distance to the ellipse, approximated by the radial error times the
    # local scale (|grad r|^-1); fine for a ring this flat
    gx = (u * math.cos(t) / (ea * k) - v * math.sin(t) / (eb * k)) / np.maximum(r, 1e-6)
    gy = (u * math.sin(t) / (ea * k) + v * math.cos(t) / (eb * k)) / np.maximum(r, 1e-6)
    dist = np.abs(r - 1) / np.maximum(np.hypot(gx, gy), 1e-9)
    ring = np.clip(w / 2 + 0.5 - dist, 0, 1)
    core = np.clip(w * 0.22 + 0.5 - dist, 0, 1)
    tu = np.clip(u / np.maximum(r, 1e-6), -1, 1)
    front = v > 0                               # lower half passes in front

    def layer(rgb, a):
        return Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8))

    def ring_layer(stops, mask, strength):
        rgb = _ramp(stops, tu)
        rgb = rgb + (255 - rgb) * (core * 0.6)[..., None]   # bright neon core
        return layer(rgb, ring * mask * strength)

    sx, sy, sr = _GLOBE_SPHERE
    sx, sy, sr = (128 + (sx - 128) * f) * k, (128 + (sy - 128) * f) * k, sr * f * k
    sd = np.hypot(xx - sx, yy - sy)
    disk = np.clip(sr + 0.5 - sd, 0, 1)
    glow_col = np.broadcast_to(np.array(_GLOBE_GLOW[violet], float), (C, C, 3))
    out = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    # glow of sphere and ring
    ga = Image.fromarray((np.maximum(disk, ring) * 255).astype(np.uint8))
    ga = np.asarray(ga.filter(ImageFilter.GaussianBlur(10 + w * 0.8)), float) / 255
    out.alpha_composite(layer(glow_col, ga * 0.75))
    out.alpha_composite(ring_layer(_GLOBE_BACK[violet], ~front, 0.85))
    bs = round(C * f)
    body = Image.open(GLOBE_BODY).convert("RGBA").resize((bs, bs), Image.LANCZOS)
    out.alpha_composite(body.crop(((bs - C) // 2, (bs - C) // 2,
                                   (bs - C) // 2 + C, (bs - C) // 2 + C)))
    # magenta rim light on the lower right of the sphere, like the concept
    ang = np.degrees(np.arctan2(yy - sy, xx - sx))   # 0 = right, 90 = down
    arc = np.clip(1 - np.abs(ang - 55) / 60, 0, 1) ** 0.7
    rw = max(0.03 * s, 1.0) * C / s
    rim = np.clip(rw / 2 + 0.5 - np.abs(sd - (sr - rw / 2)), 0, 1) * arc
    out.alpha_composite(layer(_ramp(_GLOBE_FRONT[violet], np.full((C, C), 0.45)),
                              rim * (0.95 if violet else 0.8)))
    # ring glow, then the front half of the ring over the sphere
    rg = Image.fromarray((ring * front * 255).astype(np.uint8))
    rg = np.asarray(rg.filter(ImageFilter.GaussianBlur(w * 0.9 + 3)), float) / 255
    out.alpha_composite(layer(_ramp(_GLOBE_FRONT[violet], tu), rg * 0.7))
    out.alpha_composite(ring_layer(_GLOBE_FRONT[violet], front, 1.0))
    return _premul_resize(out, s)


# --- Folder body: lighter azure ----------------------------------------------
# The masters' folder bodies came out a dark royal blue (mean ~#2257a8); the
# folders of the concept's "C:\Projects" window are a bright azure (~#0a64e9,
# glossy toward #04a0ff). Saturated blue pixels are lifted toward that, while
# pale emblem strokes (low saturation), dark emblem lines and the golden edges
# stay as they are, so the special folders keep their contrast.
LIGHT_FOLDERS = ("folder", "folder-applications", "folder-development",
                 "folder-documents", "folder-download", "folder-pictures",
                 "folder-videos", "folder-temp", "user-home")


def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def lighten_folder(img):
    a = np.asarray(img.convert("RGBA"), float) / 255
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.asarray(img.convert("RGB").convert("HSV"), float)[..., 0] * 360 / 255
    wt = (_smooth(hue, 195, 205) * (1 - _smooth(hue, 238, 250))   # blue only
          * _smooth(sat, 0.72, 0.88)                              # not the pale emblems
          * _smooth(mx, 0.22, 0.38))                              # not dark lines
    v2 = 1 - (1 - mx) ** 2.8                    # 0.55 -> 0.89, 0.8 -> 0.99
    gain = np.where(mx > 1e-6, v2 / np.maximum(mx, 1e-6), 1)
    lifted = rgb * gain[..., None]
    lifted[..., 1] = np.minimum(lifted[..., 1] * 1.08 + 0.02, 1)  # a touch toward azure
    rgb = rgb + (lifted - rgb) * wt[..., None]
    out = np.dstack([rgb, a[..., 3]])
    return Image.fromarray((out * 255 + 0.5).clip(0, 255).astype(np.uint8))


def render(name, s, violet=False):
    if name in GLOBES:
        return globe(s, violet)
    img = Image.open(master(name, violet)).convert("RGBA")
    if name in LIGHT_FOLDERS:
        img = lighten_folder(img)
    return _premul_resize(img, s)


def build_icons(out, name="WarpLegacyNeon2026", violet=False):
    """Write a complete freedesktop icon theme to out/<name>/.

    violet=True: "Warp Legacy Neon 2026 Violett", violet masters where they
    exist, inheriting from the cyan set. Returns the theme directory.
    Existing content of out/<name> is replaced.
    """
    out = pathlib.Path(out)
    root = out / name
    if root.exists():
        shutil.rmtree(root)
    dirs = set()
    missing = []
    for n, (ctx, _src, _box) in ICONS.items():
        if n not in GLOBES and not (MASTERS / f"{n}.png").exists():
            missing.append(n)
            continue
        for s in SIZES:
            d = root / f"{s}x{s}" / ctx
            d.mkdir(parents=True, exist_ok=True)
            dirs.add((s, ctx))
            render(n, s, violet).save(d / f"{n}.png", optimize=True)
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
    if violet:
        head = ["Name=Warp Legacy Neon 2026 Violett",
                "Comment=The Warp 2026 neon concept icons with violet-magenta rim light",
                "Inherits=WarpLegacyNeon2026,WarpLegacyNeon,breeze-dark,hicolor"]
    else:
        head = ["Name=Warp Legacy Neon 2026",
                "Comment=The icons of the Warp 2026 neon concept, glow included",
                "Inherits=WarpLegacyNeon,breeze-dark,hicolor"]
    lines = ["[Icon Theme]"] + head + ["Example=folder",
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
        bx, by = (i % cols) * cell_w + 8, (i // cols) * cell_h + 4
        # 1:1 size as in the concept
        sheet.paste(crop, (bx, by + (zoom - tile) // 2))
        small = Image.new("RGBA", (tile, tile), BG + (255,))
        small.alpha_composite(render(n, tile))
        sheet.paste(small, (bx + 72 + 8, by + (zoom - tile) // 2))
        # enlarged
        sheet.paste(crop.resize((zoom, zoom), Image.LANCZOS), (bx + 2 * 72 + 16, by))
        big = Image.new("RGBA", (zoom, zoom), BG + (255,))
        big.alpha_composite(render(n, zoom))
        sheet.paste(big, (bx + 2 * 72 + zoom + 24, by))
        dr.text((bx, by + zoom + 4), f"{n}  <-  {src}", fill=(0xe8, 0xf0, 0xff), font=font)
    sheet.convert("RGB").save(dest)


def _concept_tile(concept, box):
    """Concept crop framed like the masters (core = 204/256 of the tile)."""
    x0, y0, x1, y1 = box
    tile = round(max(x1 - x0, y1 - y0) * 256 / 204)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    l, t = round(cx - tile / 2), round(cy - tile / 2)
    return concept.crop((l, t, l + tile, t + tile))


# violet twins of a motif elsewhere in the concept (shown next to the own crop)
VIOLET_REFS = {
    "office-calendar": ("Date/Time (Control Panel)", (1320, 854, 1355, 893)),
}


def violet_comparison(dest, zoom=128):
    """Per violet icon: concept crop(s) | cyan master | violet master, on navy."""
    concept = Image.open(CONCEPT).convert("RGB")
    names = [n for n in ICONS if n in GLOBES or (MASTERS_VIOLET / f"{n}.png").exists()]
    cols = 2
    cell_w, cell_h = 4 * zoom + 5 * 8, zoom + 30
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), BG + (255,))
    dr = ImageDraw.Draw(sheet)
    font = _font(11)
    for i, n in enumerate(names):
        _ctx, src, box = ICONS[n]
        bx, by = (i % cols) * cell_w + 8, (i // cols) * cell_h + 4
        crops = [_concept_tile(concept, box)]
        label = src
        if n in VIOLET_REFS:
            crops.append(_concept_tile(concept, VIOLET_REFS[n][1]))
            label += " + " + VIOLET_REFS[n][0]
        else:
            crops.append(None)
        x = bx
        for c in crops:
            if c is not None:
                sheet.paste(c.resize((zoom, zoom), Image.LANCZOS), (x, by))
            x += zoom + 8
        for v in (False, True):
            t = Image.new("RGBA", (zoom, zoom), BG + (255,))
            t.alpha_composite(render(n, zoom, v))
            sheet.paste(t, (x, by))
            x += zoom + 8
        dr.text((bx, by + zoom + 4), f"{n}  <-  {label}  |  cyan  |  violett",
                fill=(0xe8, 0xf0, 0xff), font=font)
    sheet.convert("RGB").save(dest)


if __name__ == "__main__":
    prev = HERE / "build-icons-preview-2026"
    prev.mkdir(exist_ok=True)
    t = time.time()
    root = build_icons(prev)
    contact_sheet(root, prev / "uebersicht.png")
    comparison(root, prev / "vergleich.png")
    vroot = build_icons(prev, "WarpLegacyNeon2026Violett", violet=True)
    contact_sheet(vroot, prev / "uebersicht-violett.png")
    violet_comparison(prev / "violett-vergleich.png")
    print(f"{len(ICONS)} icons, {len(ALIASES)} aliases, {len(SIZES)} sizes -> {root} "
          f"({time.time() - t:.1f} s); violet masters: "
          f"{len(list(MASTERS_VIOLET.glob('*.png')))} -> {vroot}")
