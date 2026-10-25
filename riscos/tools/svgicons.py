#!/usr/bin/env python3
"""RISC Legacy 2026's icons as SVG (DESIGN.md §8), drawn after RISC OS 5's
desktop sprites (vendor/riscos-open/Sprites-Iyonix): bright, saturated
colours, a fine dark outline, soft top-lit gradients; folders blue with a
lighter front flap; documents square pages with the corner folded down
at the top right and the file type shown on the page; applications as
RISC OS draws them, an object on its own without a tile.

Drawn on a 48 x 48 grid (scalable, QtSvg's subset: paths and linear
gradients, no filters, so Plasma renders them as previewed). Names Plasma
asks for map onto the drawings below; what is not drawn falls back to the
pixel theme RiscLegacy5 and then Breeze.

    svgicons.py OUTDIR      writes OUTDIR/RiscLegacy2026
    svgicons.py --sheet OUT.png
"""
import sys
from pathlib import Path

INK = "#1b2230"          # the outline: near black, a little blue as RO5's
W = 1.4                  # outline width on the 48 grid

_defs = []


def grad(id_, top, bottom, x1=0, y1=0, x2=0, y2=1):
    _defs.append(f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                 f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
    return f"url(#{id_})"


def svg(body, defs):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">'
            f'<defs>{"".join(defs)}</defs>{body}</svg>\n')


def path(d, fill, stroke=INK, width=W, extra=""):
    s = f' stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def rect(x, y, w, h, fill, r=0, stroke=INK, width=W):
    s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{s}/>'


def circle(cx, cy, r, fill, stroke=INK, width=W):
    s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{s}/>'


# ---- the building blocks -----------------------------------------------
def folder(open_=False, emblem=""):
    back = grad("fb", "#5fb4f0", "#2a7fd0")
    front = grad("ff", "#8fd0ff", "#3d97e6")
    b = path("M4 12 h14 l4 4 h22 v24 a2 2 0 0 1 -2 2 h-36 a2 2 0 0 1 -2 -2 z", back)
    if open_:
        b += path("M7 20 h37 l-3 20 a2 2 0 0 1 -2 2 h-33 a2 2 0 0 1 -2 -2 z", front)
    else:
        b += path("M4 20 h40 v20 a2 2 0 0 1 -2 2 h-36 a2 2 0 0 1 -2 -2 z", front)
        b += path("M6 22 h36", "none", stroke="#ffffff", width=1, extra=' stroke-opacity="0.7"')
    return b + emblem


def page(label_fill=None, content=""):
    """A RISC OS file: a square page, the top right corner folded down."""
    sheet = grad("pg", "#ffffff", "#dfe9f5")
    b = path("M9 5 h22 l9 9 v28 a2 2 0 0 1 -2 2 h-27 a2 2 0 0 1 -2 -2 v-35 a2 2 0 0 1 2 -2 z", sheet)
    b += path("M31 5 v7 a2 2 0 0 0 2 2 h7", "#c4d4e8")
    if label_fill:
        b += path("M7 30 h33 v12 a2 2 0 0 1 -2 2 h-29 a2 2 0 0 1 -2 -2 z", label_fill)
    return b + content


def lines(x, y, n, w=20, gap=4, color="#5a6b85"):
    return "".join(path(f"M{x} {y + i * gap} h{w - (6 if i == n - 1 else 0)}", "none", stroke=color, width=1.6)
                   for i in range(n))


def emblem_badge(content, fill="#ffffff"):
    return circle(34, 32, 8, fill, width=1.2) + content


# ---- the drawings --------------------------------------------------------
def d_folder():
    return folder()


def d_folder_open():
    return folder(open_=True)


def d_home():
    house = path("M28 33 l6 -6 l6 6 v7 h-12 z", "#ffd75a", width=1.2) + path("M32.5 40 v-4 h3 v4", "#b5651d", width=1)
    return folder(emblem=house)


def d_desktop():
    return folder(emblem=rect(26, 28, 16, 11, "#3a4a60", 1.5, width=1.2) + rect(28, 30, 12, 7, "#7fd3ff", 0, stroke=None))


def d_documents():
    return folder(emblem=path("M28 25 h9 l4 4 v12 h-13 z", "#ffffff", width=1.2) + lines(30, 31, 3, 9, 3))


def d_download():
    return folder(emblem=path("M34 25 v10 m-5 -4 l5 5 l5 -5", "none", stroke="#ffffff", width=3) +
                  path("M34 25 v10 m-5 -4 l5 5 l5 -5", "none", stroke="#14508f", width=1.6))


def d_music():
    return folder(emblem=path("M31 39 a3 2.5 0 1 1 0 -0.1 v-12 l9 -2 v11 a3 2.5 0 1 1 0 -0.1", "#1b2230", width=0.8))


def d_pictures():
    return folder(emblem=rect(26, 27, 16, 12, "#ffffff", 1, width=1.2) +
                  path("M27 38 l5 -6 l4 4 l2 -2 l3 4 z", "#3fae5c", stroke=None) + circle(38, 30.5, 1.6, "#ffcc33", stroke=None))


def d_videos():
    return folder(emblem=rect(26, 27, 16, 12, "#2b2f3a", 1, width=1.2) + path("M32 30 v6 l5 -3 z", "#ffffff", stroke=None))


def d_harddisc():
    case = grad("hd", "#f3efe2", "#cfc8b2")
    b = path("M6 18 l6 -6 h30 v20 l-6 6 h-30 z", "#b9b19a")
    b += rect(6, 18, 30, 20, case, 1.5)
    b += path("M6 18 l6 -6 h30 l-6 6 z", grad("hdt", "#fffdf5", "#e6e0cc"))
    b += rect(10, 28, 18, 3, "#4a4f5a", 1, width=0.8) + circle(31, 29.5, 1.5, "#3ddc5a", width=0.8)
    return b


def d_sd():
    body = grad("sd", "#2f6fc7", "#164a96")
    b = path("M12 6 h18 l8 8 v28 a2 2 0 0 1 -2 2 h-24 a2 2 0 0 1 -2 -2 v-34 a2 2 0 0 1 2 -2 z", body)
    b += rect(14, 22, 20, 16, "#f6f1dc", 1.5, width=1)
    b += "".join(rect(15 + i * 4, 8, 2.4, 7, "#e8c55a", 0.5, width=0.6) for i in range(5))
    b += '<text x="24" y="34" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="9" font-weight="bold" ' \
         'text-anchor="middle" fill="#164a96">SD</text>'
    return b


def d_cd():
    disc = grad("cd", "#f4f8ff", "#b8c8e0", 0, 0, 1, 1)
    return circle(24, 24, 18, disc) + circle(24, 24, 18, "none", stroke="#8fd0ff", width=3) + \
        circle(24, 24, 5, "#ffffff") + circle(24, 24, 2, "#9aa8bd", width=0.8)


def d_monitor():
    b = rect(6, 8, 36, 26, grad("mon", "#f3efe2", "#d3ccb6"), 2.5)
    b += rect(10, 12, 28, 18, grad("scr", "#5fb4f0", "#174f9a"), 1, width=1)
    b += path("M18 34 h12 l2 6 h-16 z", "#c9c2ab") + rect(12, 40, 24, 3, "#b9b19a", 1)
    return b


def d_server():
    b = ""
    for i, y in enumerate((8, 20, 32)):
        b += rect(9, y, 30, 10, grad(f"sv{i}", "#f3efe2", "#cfc8b2"), 1.5)
        b += rect(13, y + 4, 12, 2.4, "#4a4f5a", 0.8, width=0.6) + circle(34, y + 5, 1.4, "#3ddc5a", width=0.6)
    return b


def d_network():
    return circle(14, 34, 6, "#5fb4f0") + circle(34, 34, 6, "#5fb4f0") + circle(24, 12, 7, "#ffd75a") + \
        path("M19 17 l-3 11 M29 17 l3 11 M20 34 h8", "none", width=2)


def d_app():
    # RISC OS 5's application: three green cogs in a triangle (!Boot's).
    def cog(cx, cy, r, fill):
        teeth = "".join(f'<rect x="{cx - 1.8}" y="{cy - r - 3}" width="3.6" height="5" rx="0.8" fill="{fill}" '
                        f'stroke="{INK}" stroke-width="1" transform="rotate({a} {cx} {cy})"/>' for a in range(0, 360, 45))
        return teeth + circle(cx, cy, r, fill, width=1.2) + circle(cx, cy, r * 0.38, "#ffffff", width=1)
    g = grad("cog", "#7be36b", "#2f9e3a")
    return cog(24, 14, 7, g) + cog(13, 33, 7, g) + cog(35, 33, 7, g)


def d_apps():
    # RISC OS's Apps: a folder of tools, brush and pen across it.
    return folder(emblem=path("M26 40 l14 -16 l3 3 l-14 16 z", "#ffd75a", width=1.2) +
                  path("M30 26 l12 12", "none", stroke="#c62828", width=3) + path("M30 26 l12 12", "none", stroke=INK, width=0.6))


def d_text():
    return page(content=lines(12, 16, 6, 22, 4))


def d_script():
    return page(content=rect(11, 15, 26, 18, "#1f2a38", 2, width=1) +
                path("M14 20 l4 3 l-4 3 M20 27 h8", "none", stroke="#7fe08a", width=1.8))


def d_html():
    return page(content=circle(24, 25, 9, grad("gl", "#7fd3ff", "#2a7fd0")) +
                path("M15 25 h18 M24 16 c-5 5 -5 13 0 18 c5 -5 5 -13 0 -18", "none", stroke="#ffffff", width=1.2))


def labelled(text, color, content=""):
    return page(color, content + f'<text x="23.5" y="40.5" font-family="TeX Gyre Heros,Helvetica,sans-serif" '
                f'font-size="9" font-weight="bold" text-anchor="middle" fill="#ffffff">{text}</text>')


def picture_on_page():
    return rect(12, 13, 24, 15, "#cfeaff", 1, width=1) + path("M13 27 l7 -8 l5 5 l3 -3 l7 8 z", "#3fae5c", stroke=None) + \
        circle(31, 17, 2, "#ffcc33", stroke=None)


def d_image():
    return page(content=picture_on_page())


def d_jpeg():
    return labelled("JPEG", "#2a7fd0", picture_on_page())


def d_png():
    return labelled("PNG", "#1f9e6a", picture_on_page())


def d_pdf():
    return labelled("PDF", "#d32f2f", lines(12, 15, 3, 22, 4))


def d_audio():
    return labelled("WAV", "#ef7d00", path("M12 20 q3 -8 6 0 t6 0 t6 0 t6 0", "none", stroke="#2a7fd0", width=2))


def d_video():
    film = rect(12, 12, 24, 15, "#2b2f3a", 1, width=1) + path("M21 15.5 v8 l7 -4 z", "#ffffff", stroke=None)
    return labelled("VIDEO", "#7b3fbf", film)


def d_archive():
    box = grad("bx", "#e9c27a", "#b98a3a")
    return path("M8 16 l16 -8 l16 8 v20 l-16 8 l-16 -8 z", box) + path("M8 16 l16 8 l16 -8 M24 24 v20", "none") + \
        path("M16 12 l16 8 v6", "none", stroke="#f6e7c4", width=2.4)


def d_unknown():
    return page(content='<text x="24" y="33" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="20" '
                        'font-weight="bold" text-anchor="middle" fill="#2a7fd0">?</text>')


def d_editor():
    # !Edit: a page and a blue pen across it.
    return page(content=lines(12, 16, 5, 18, 4)) + path("M20 38 l18 -22 l4 3 l-18 22 l-5 1 z", grad("pen", "#5fb4f0", "#174f9a"), width=1.2) + \
        path("M38 16 l4 3", "none", stroke="#ffffff", width=1)


def d_configure():
    # !Configure in RISC OS 5: green and grey cogs.
    def cog(cx, cy, r, fill, n=8):
        teeth = "".join(f'<rect x="{cx - 2}" y="{cy - r - 3.5}" width="4" height="6" rx="0.8" fill="{fill}" '
                        f'stroke="{INK}" stroke-width="1" transform="rotate({a} {cx} {cy})"/>' for a in range(0, 360, 360 // n))
        return teeth + circle(cx, cy, r, fill, width=1.2) + circle(cx, cy, r * 0.35, "#ffffff", width=1)
    return cog(18, 20, 10, grad("cg1", "#c7ccd4", "#7d8590")) + cog(33, 33, 8, grad("cg2", "#7be36b", "#2f9e3a"))


def d_help():
    b = rect(7, 7, 34, 34, grad("hp", "#5f8ff0", "#1d3fa0"), 5)
    return b + '<text x="24" y="35" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="26" font-style="italic" ' \
        'font-weight="bold" text-anchor="middle" fill="#ffffff">i</text>'


def d_taskman():
    # RISC OS 5's task manager: a big green cog.
    teeth = "".join(f'<rect x="21" y="3" width="6" height="9" rx="1" fill="url(#tm)" stroke="{INK}" stroke-width="1.2" '
                    f'transform="rotate({a} 24 24)"/>' for a in range(0, 360, 45))
    g = grad("tm", "#7be36b", "#2a8f34")
    return teeth + circle(24, 24, 14, g) + circle(24, 24, 5.5, "#ffffff")


def d_printer():
    b = rect(13, 6, 22, 14, "#ffffff", 1) + lines(16, 10, 2, 16, 4)
    b += rect(6, 18, 36, 16, grad("pr", "#f3efe2", "#c9c2ab"), 3)
    b += rect(12, 30, 24, 12, "#ffffff", 1) + circle(36, 23, 1.6, "#3ddc5a", width=0.8)
    return b


def d_terminal():
    return rect(5, 9, 38, 30, grad("tb", "#e8e4d8", "#bdb6a0"), 3) + rect(9, 13, 30, 22, "#141a22", 1.5, width=1) + \
        path("M13 19 l5 4 l-5 4 M21 29 h10", "none", stroke="#7fe08a", width=2)


def d_globe():
    g = circle(24, 24, 18, grad("gb", "#7fd3ff", "#1f6fc7"))
    land = path("M13 15 q6 -3 9 2 q-2 5 -7 5 q-3 3 -6 0 z M27 27 q6 -2 9 3 q-3 6 -8 6 q-3 -4 -1 -9 z", "#4fbf5a", width=1)
    return g + land + path("M10 30 q14 5 28 0", "none", stroke="#ffffff", width=0.8, extra=' stroke-opacity="0.6"')


def d_search():
    return circle(20, 20, 12, grad("lens", "#e7f6ff", "#9fd2f5"), width=2) + path("M29 29 l11 11", "none", width=6) + \
        path("M29 29 l11 11", "none", stroke="#c9a14a", width=3.5)


def d_lock():
    return path("M16 22 v-6 a8 8 0 0 1 16 0 v6", "none", width=4) + path("M16 22 v-6 a8 8 0 0 1 16 0 v6", "none", stroke="#c7ccd4", width=2) + \
        rect(11, 21, 26, 20, grad("lk", "#ffd75a", "#d19a1f"), 3) + circle(24, 30, 3, INK, stroke=None) + rect(23, 30, 2, 6, INK, 0, stroke=None)


def d_power():
    return circle(24, 24, 18, grad("pw", "#ff7b6b", "#c62828")) + \
        path("M17 17 a10 10 0 1 0 14 0 M24 12 v12", "none", stroke="#ffffff", width=3.2)


def d_trash():
    can = grad("tr", "#c7ccd4", "#7d8590", 0, 0, 1, 0)
    return path("M12 14 h24 l-2 28 a2 2 0 0 1 -2 2 h-16 a2 2 0 0 1 -2 -2 z", can) + rect(9, 10, 30, 5, "#aab1bc", 1.5) + \
        rect(19, 6, 10, 4, "#aab1bc", 1, width=1) + path("M19 20 v18 M24 20 v18 M29 20 v18", "none", stroke="#5c636e", width=1.4)


def sign(shape, fill, mark):
    return shape(fill) + mark


def d_warning():
    return path("M24 5 l20 36 h-40 z", grad("wn", "#ffe066", "#f2b705")) + \
        '<text x="24" y="38" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="22" font-weight="bold" text-anchor="middle" fill="#1b2230">!</text>'


def d_error():
    return circle(24, 24, 19, grad("er", "#ff6b5e", "#c62828")) + path("M16 16 l16 16 M32 16 l-16 16", "none", stroke="#ffffff", width=4.5)


def d_info():
    return circle(24, 24, 19, grad("in", "#5f8ff0", "#1d3fa0")) + \
        '<text x="24" y="34" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="26" font-style="italic" font-weight="bold" text-anchor="middle" fill="#ffffff">i</text>'


def d_question():
    return circle(24, 24, 19, grad("qu", "#ffffff", "#d7e3f2")) + \
        '<text x="24" y="33" font-family="TeX Gyre Heros,Helvetica,sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="#2a5fa8">?</text>'


def d_paint():
    # !Paint: a palette and a brush.
    pal = path("M8 28 c0 -12 12 -20 24 -16 c8 3 10 10 6 14 c-3 3 -7 0 -9 3 c-2 3 2 6 -2 9 c-8 6 -19 -1 -19 -10 z",
               grad("pl", "#f6e2b8", "#d9b878"))
    blobs = circle(17, 22, 2.6, "#d32f2f", width=0.8) + circle(24, 18, 2.6, "#2a7fd0", width=0.8) + \
        circle(31, 19, 2.6, "#3fae5c", width=0.8) + circle(15, 30, 2.6, "#ffcc33", width=0.8)
    return pal + blobs + path("M26 40 l14 -24 l3 2 l-13 24 z", "#7a4a1d", width=1)


DRAWINGS = {
    "folder": d_folder, "folder-open": d_folder_open, "user-home": d_home, "user-desktop": d_desktop,
    "folder-documents": d_documents, "folder-download": d_download, "folder-music": d_music,
    "folder-pictures": d_pictures, "folder-videos": d_videos,
    "drive-harddisk": d_harddisc, "drive-removable-media": d_sd, "media-optical": d_cd,
    "computer": d_monitor, "network-server": d_server, "network-workgroup": d_network,
    "application-x-executable": d_app, "applications-all": d_apps,
    "text-plain": d_text, "application-x-shellscript": d_script, "text-html": d_html,
    "image-x-generic": d_image, "image-jpeg": d_jpeg, "image-png": d_png, "application-pdf": d_pdf,
    "audio-x-generic": d_audio, "video-x-generic": d_video, "package-x-generic": d_archive,
    "unknown": d_unknown, "accessories-text-editor": d_editor, "preferences-system": d_configure,
    "help-browser": d_help, "utilities-system-monitor": d_taskman, "printer": d_printer,
    "utilities-terminal": d_terminal, "internet-web-browser": d_globe, "system-search": d_search,
    "system-lock-screen": d_lock, "system-shutdown": d_power, "user-trash": d_trash,
    "dialog-warning": d_warning, "dialog-error": d_error, "dialog-information": d_info,
    "dialog-question": d_question, "applications-graphics": d_paint,
}
# Further names on the same drawings.
ALIASES = {
    "inode-directory": "folder", "folder-templates": "folder", "folder-publicshare": "folder",
    "folder-remote": "network-workgroup", "drive-harddisk-root": "drive-harddisk",
    "drive-harddisk-system": "drive-harddisk", "drive-removable-media-usb": "drive-removable-media",
    "media-flash": "drive-removable-media", "media-flash-sd-mmc": "drive-removable-media",
    "drive-optical": "media-optical", "media-optical-cd": "media-optical", "video-display": "computer",
    "preferences-desktop-display": "computer", "applications-other": "applications-all",
    "start-here-kde": "applications-all", "text-x-generic": "text-plain", "text-x-readme": "text-plain",
    "text-x-script": "application-x-shellscript", "text-x-python": "application-x-shellscript",
    "application-xhtml+xml": "text-html", "audio-x-wav": "audio-x-generic", "audio-mpeg": "audio-x-generic",
    "application-zip": "package-x-generic", "application-x-archive": "package-x-generic",
    "application-x-tar": "package-x-generic", "application-x-compressed-tar": "package-x-generic",
    "application-octet-stream": "unknown", "kate": "accessories-text-editor", "kwrite": "accessories-text-editor",
    "org.kde.kate": "accessories-text-editor", "org.kde.kwrite": "accessories-text-editor",
    "systemsettings": "preferences-system", "configure": "preferences-system", "help-contents": "help-browser",
    "khelpcenter": "help-browser", "org.kde.plasma-systemmonitor": "utilities-system-monitor",
    "document-print": "printer", "org.kde.konsole": "utilities-terminal", "konsole": "utilities-terminal",
    "system-file-manager": "folder", "org.kde.dolphin": "folder", "firefox": "internet-web-browser",
    "process-stop": "dialog-error", "user-trash-full": "user-trash", "kolourpaint": "applications-graphics",
    "org.kde.kolourpaint": "applications-graphics", "system-lock-screen-symbolic": "system-lock-screen",
}


def build(out):
    base = Path(out) / "RiscLegacy2026"
    folder_ = base / "scalable/apps"
    folder_.mkdir(parents=True, exist_ok=True)
    for name, draw in DRAWINGS.items():
        _defs.clear()
        body = draw()
        (folder_ / f"{name}.svg").write_text(svg(body, list(_defs)))
    for alias, target in ALIASES.items():
        link = folder_ / f"{alias}.svg"
        if not link.exists():
            link.symlink_to(f"{target}.svg")
    (base / "index.theme").write_text("\n".join([
        "[Icon Theme]", "Name=RiscLegacy2026",
        "Comment=RISC OS 5's desktop icons drawn anew as SVG for RISC Legacy 2026",
        "Inherits=RiscLegacy5,breeze,hicolor", "Directories=scalable/apps", "",
        "[scalable/apps]", "Size=48", "MinSize=8", "MaxSize=512", "Type=Scalable", "Context=Applications", ""]))
    print(base)
    return base


def sheet(out):
    """Every drawing at 24, 48 and 128 px, rendered by QtSvg."""
    import tempfile
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    app = QGuiApplication.instance() or QGuiApplication(["x", "-platform", "offscreen"])
    names = list(DRAWINGS)
    cell = 190
    cols = 8
    img = QImage(cols * cell, ((len(names) + cols - 1) // cols) * 150, QImage.Format_ARGB32)
    img.fill(QColor("#e9e9e4"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    for i, name in enumerate(names):
        _defs.clear()
        r = QSvgRenderer(QByteArray(svg(DRAWINGS[name](), list(_defs)).encode()))
        x, y = (i % cols) * cell, (i // cols) * 150
        r.render(p, QRectF(x + 4, y + 104, 24, 24))
        r.render(p, QRectF(x + 32, y + 80, 48, 48))
        r.render(p, QRectF(x + 84, y + 4, 100, 100))
        p.setPen(QColor("#333333"))
        p.setFont(QFont("Sans", 7))
        p.drawText(x + 4, y + 142, name[:30])
    p.end()
    img.save(out)
    print(out)


if __name__ == "__main__":
    if sys.argv[1] == "--sheet":
        sheet(sys.argv[2])
    else:
        build(sys.argv[1])
