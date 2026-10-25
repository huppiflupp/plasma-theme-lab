#!/usr/bin/env python3
"""Icon themes from RISC OS's own sprites (DESIGN.md §8).

The Wimp's sprite files in the RISC OS sources (vendor/riscos-open,
Apache 2.0) hold the desktop's icons: filing systems, directories,
applications, file types (by RISC OS file type number), the ROM
applications and the error box's symbols. Each is mapped here to the
freedesktop names Plasma asks for; what RISC OS has no picture for is
left to Breeze (Inherits).

Two themes:
  RiscLegacy    RISC OS 4's sprites (Sprites-RO400): classic and 4
  RiscLegacy5   RISC OS 5's (Sprites-Iyonix: blue folders, alpha): 2026

RISC OS icons are 34 x 34 at 90 dpi ("small_" ones 17 x 17). They are
scaled by whole numbers, nearest neighbour, so pixels stay pixels: 17
(small), 34, 68, 136, each in a folder of that size with Type=Threshold,
so Plasma takes the nearest one for 16, 22, 32, 48, 64 or 128.

    iconset.py OUTDIR      writes OUTDIR/RiscLegacy and OUTDIR/RiscLegacy5
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor/riscos-open"

# freedesktop name -> RISC OS sprite (without small_). A sprite missing
# from one set falls back to the other set's.
MAP = {
    # places and devices
    "folder": "directory", "inode-directory": "directory", "folder-open": "directoryo",
    "user-home": "directory", "folder-documents": "directory", "folder-download": "directory",
    "folder-pictures": "directory", "folder-music": "directory", "folder-videos": "directory",
    "folder-templates": "directory", "folder-publicshare": "directory", "user-desktop": "directory",
    "folder-remote": "network", "network-workgroup": "network", "network-server": "fileserver",
    "drive-harddisk": "harddisc", "drive-harddisk-root": "harddisc", "drive-harddisk-system": "harddisc",
    "drive-removable-media": "floppysd", "drive-removable-media-usb": "floppysd",
    "media-flash": "floppysd", "media-flash-sd-mmc": "floppysd",
    "media-floppy": "floppydisc", "drive-optical": "cddisc", "media-optical": "cddisc",
    "media-optical-cd": "cddisc", "media-optical-dvd": "cddisc",
    "computer": "display", "video-display": "display", "preferences-desktop-display": "display",
    # applications
    "application-x-executable": "application", "application-x-sharedlib": "file_ffa",
    "applications-all": "romapps", "applications-other": "romapps", "start-here-kde": "romapps",
    "accessories-text-editor": "!edit", "kate": "!edit", "kwrite": "!edit", "org.kde.kate": "!edit",
    "org.kde.kwrite": "!edit",
    "preferences-system": "!configure", "systemsettings": "!configure", "configure": "!configure",
    "help-browser": "!help", "help-contents": "!help", "help-about": "information", "khelpcenter": "!help",
    "accessories-character-map": "!chars", "kcharselect": "!chars",
    "printer": "!printers", "document-print": "!printers",
    "utilities-system-monitor": "switcher", "org.kde.plasma-systemmonitor": "switcher",
    "preferences-desktop-color": "palette", "preferences-desktop-theme": "palette",
    "applications-graphics": "!paint", "kolourpaint": "!paint", "org.kde.kolourpaint": "!paint",
    "inkscape": "!draw", "org.inkscape.Inkscape": "!draw", "draw-freehand": "!draw",
    "preferences-desktop-font": "!fonts", "font-x-generic": "file_ff6",
    "alarm-symbolic": "!alarm", "chronometer": "!alarm", "korganizer": "!alarm", "preferences-system-time": "!alarm",
    # file types (RISC OS type numbers: fff Text, ffb BASIC, feb Obey,
    # faf HTML, c85 JPEG, b60 PNG, 695 GIF, ff9 Sprite, adf PDF, fb1 WAVE,
    # ae7 ARMovie, ddc Archive, ffd Data, ff6 Font, aff DrawFile)
    "text-plain": "file_fff", "text-x-generic": "file_fff", "text-x-readme": "file_fff",
    "text-x-script": "file_ffb", "application-x-shellscript": "file_feb", "text-x-python": "file_feb",
    "text-html": "file_faf", "application-xhtml+xml": "file_faf",
    "image-jpeg": "file_c85", "image-png": "file_b60", "image-gif": "file_695",
    "image-x-generic": "file_ff9", "image-svg+xml": "file_aff", "image-x-xcf": "file_ff9",
    "application-pdf": "file_adf", "audio-x-generic": "file_fb1", "audio-x-wav": "file_fb1",
    "audio-mpeg": "file_fb1", "video-x-generic": "file_ae7",
    "application-zip": "file_ddc", "application-x-archive": "file_ddc", "package-x-generic": "file_ddc",
    "application-x-tar": "file_ddc", "application-x-compressed-tar": "file_ddc",
    "application-octet-stream": "file_ffd", "unknown": "file_xxx", "text-x-csv": "file_dfe",
    # the error box
    "dialog-error": "error", "dialog-information": "information", "dialog-warning": "warning",
    "dialog-question": "question", "process-stop": "program",
}
SIZES = (1, 2, 4)        # 34, 68, 136 from the large sprites
SETS = {"RiscLegacy": ("Sprites-RO400", "Sprites-Iyonix", "RISC OS 4's desktop icons"),
        "RiscLegacy5": ("Sprites-Iyonix", "Sprites-RO400", "RISC OS 5's desktop icons")}


def sprite(name, first, second, small=False):
    for folder in (first, second):
        n = ("small_" + name[5:] if name.startswith("file_") else "small_" + name.lstrip("!")) if small else name
        for candidate in ([n, "sm" + name] if small else [n]):
            p = VENDOR / folder / f"{candidate}.png"
            if p.exists():
                return Image.open(p).convert("RGBA")
    return None


def fit(im, edge):
    """Centre on a square canvas (some sprites are 41 x 40, 31 x 34 …)."""
    canvas = Image.new("RGBA", (edge, edge), (0, 0, 0, 0))
    if im.width > edge or im.height > edge:
        im = im.copy(); im.thumbnail((edge, edge), Image.NEAREST)
    canvas.paste(im, ((edge - im.width) // 2, (edge - im.height) // 2), im)
    return canvas


def build(out):
    for theme, (first, second, comment) in SETS.items():
        base = Path(out) / theme
        dirs = []
        for scale in SIZES:
            edge = 34 * scale
            d = f"{edge}x{edge}/apps"
            dirs.append((d, edge))
            (base / d).mkdir(parents=True, exist_ok=True)
        small_dir = "17x17/apps"
        (base / small_dir).mkdir(parents=True, exist_ok=True)
        dirs.append((small_dir, 17))
        for fd, ro in MAP.items():
            big = sprite(ro, first, second)
            if big is None:
                continue
            big = fit(big, 34)
            for scale in SIZES:
                e = 34 * scale
                big.resize((e, e), Image.NEAREST).save(base / f"{e}x{e}/apps/{fd}.png")
            small = sprite(ro, first, second, small=True)
            fit(small, 17).save(base / small_dir / f"{fd}.png") if small is not None else \
                big.resize((17, 17), Image.LANCZOS).save(base / small_dir / f"{fd}.png")
        lines = ["[Icon Theme]", f"Name={theme}", f"Comment={comment}, from the RISC OS sources",
                 "Inherits=breeze,hicolor", "Directories=" + ",".join(d for d, _ in dirs), ""]
        for d, edge in dirs:
            lines += [f"[{d}]", f"Size={edge}", "Type=Threshold", "Threshold=8", "Context=Applications", ""]
        (base / "index.theme").write_text("\n".join(lines))
        print(base)


if __name__ == "__main__":
    build(sys.argv[1])
