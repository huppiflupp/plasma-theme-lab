#!/usr/bin/env python3
"""Package Warp Legacy for release (after CDE Copper's package.py, a copy;
the two themes share no files).

    python3 package.py        # full build, then two archives in dist/:
                              #   warp-legacy-<version>.tar.xz       classic
                              #   warp-legacy-neon-<version>.tar.xz  Neon and Neon Blue

Each archive holds the built theme of its family (build/ without the
other family's global theme, Plasma style, window frame, colours, Kvantum,
Konsole, icons and cursors) and everything shared: the panels, all the
wallpapers, the fonts, LibreOffice and the browsers, with install.sh and
uninstall.sh. Unpacked, `./install.sh --apply [neon-blue] --layout` needs
neither Python nor a build. The sources too heavy for it (the icon
masters, icons-neon2026/, 170 MB; the wallpaper sources) stay in the
repository, which is where a rebuild starts.

One archive per KDE Store entry (STORE.md): the store's "Get New…" hands a
Global Theme entry's file to kpackagetool, which wants one package with its
metadata.json in the archive's single folder. The folder therefore also
carries the family's main global theme (metadata.json, contents/): "Get
New…" installs that theme, named and with its preview, instead of a nameless
folder that turned every theme in the list into "Breeze" (UPLOAD.md, NT
Legacy 0.2.3); install.sh in that folder brings the rest.

The build is a full one, never WARP_SKIP_ICONS: a quick test build left
the first Neon icon set out.
"""
import hashlib
import os
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import VERSION  # noqa: E402

env = dict(os.environ)
env.pop("WARP_SKIP_ICONS", None)
subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, env=env)

# A build interrupted by another one running at the same time packed
# without an icon set and still reported success (21.10.2026): the parts
# every release has must be there.
NEEDED = ["icons/WarpLegacy", "icons/WarpLegacyNeon", "icons/WarpLegacyNeon2026", "icons/WarpLegacyNeon2026Violett",
          "icons/WarpLegacyNeonCursors/cursors", "icons/WarpLegacyNeonBlueCursors/cursors", "plasma/look-and-feel/org.warplegacy.desktop",
          "plasma/look-and-feel/org.warplegacy.neon.desktop", "plasma/look-and-feel/org.warplegacy.neon-blue.desktop",
          "wallpapers/org.warplegacy.neon-roehren", "wallpapers/org.warplegacy.dunkel-lichtbogen-blau",
          "wallpapers/org.warplegacy.neon-roehren-hell", "warp-legacy/libreoffice/warp-legacy.oxt",
          "warp-legacy/warp-legacy-switch"]
missing = [n for n in NEEDED if not (ROOT / "build" / n).exists()]
if missing:
    sys.exit("build/ is incomplete, not packed: " + ", ".join(missing))

DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
ITEMS = ["install.sh", "uninstall.sh", "README.md", "DESIGN.md", "LICENSE",
         "RELEASE-CHECKLIST.md", "TESTING.md", "libreoffice/README.md", "browser/README.md"]
BUILD = ROOT / "build"

# family: (archive name, its global theme for kpackage, preview, what of
# build/ belongs to the other family only)
CLASSIC_ONLY = ["plasma/look-and-feel/org.warplegacy.desktop", "plasma/desktoptheme/warp-legacy",
                "kwin/decorations/kwin4_decoration_qml_warplegacy", "color-schemes/WarpLegacy.colors",
                "konsole/WarpLegacy.colorscheme", "konsole/Warp Legacy.profile", "config/Kvantum/Warp",
                "icons/WarpLegacy"]
NEON_ONLY = [p.relative_to(BUILD).as_posix() for pattern in
             ["plasma/look-and-feel/org.warplegacy.neon*", "plasma/desktoptheme/warp-legacy-neon*",
              "kwin/decorations/kwin4_decoration_qml_warplegacyneon*", "color-schemes/WarpLegacyNeon*",
              "konsole/*Neon*", "config/Kvantum/WarpNeon*", "icons/WarpLegacyNeon*"]
             for p in BUILD.glob(pattern)]
FAMILIES = {
    "classic": ("warp-legacy", "org.warplegacy.desktop", "previews/classic.png", NEON_ONLY),
    "neon": ("warp-legacy-neon", "org.warplegacy.neon.desktop", "previews/neon.png", CLASSIC_ONLY),
}
for path in CLASSIC_ONLY:
    if not (BUILD / path).exists():
        sys.exit(f"build/{path} is missing, not packed")


def keep(info):
    if "__pycache__" in info.name:
        return None
    # the same owner for every file, as a download should have
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


sums = []
for family, (name, lnf, preview, leave_out) in FAMILIES.items():
    top = f"{name}-{VERSION}"
    archive = DIST / f"{top}.tar.xz"
    skip = {f"{top}/build/{path}" for path in leave_out}

    def family_only(info):
        if info.name in skip or any(info.name.startswith(s + "/") for s in skip):
            return None
        return keep(info)

    # GNU, not Python's default PAX: kpackagetool6 (KArchive) could not
    # open the Neon archive in PAX ("cannot open the package file"), the
    # same files in GNU format it installed (Fedora VM, 25.10.2026).
    with tarfile.open(archive, "w:xz", preset=6, format=tarfile.GNU_FORMAT) as tar:
        theme = BUILD / "plasma/look-and-feel" / lnf
        tar.add(theme / "metadata.json", arcname=f"{top}/metadata.json", filter=keep)
        tar.add(theme / "contents", arcname=f"{top}/contents", filter=keep)
        tar.add(BUILD, arcname=f"{top}/build", filter=family_only)
        for item in ITEMS:
            if (ROOT / item).exists():
                tar.add(ROOT / item, arcname=f"{top}/{item}", filter=keep)
        tar.add(ROOT / preview, arcname=f"{top}/preview.png", filter=keep)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sums.append(f"{digest}  {archive.name}\n")
    print(f"{archive}: {archive.stat().st_size:,} bytes")
(DIST / "SHA256SUMS").write_text("".join(sums))
