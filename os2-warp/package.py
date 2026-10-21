#!/usr/bin/env python3
"""Package Warp Legacy for release (after CDE Copper's package.py, a copy;
the two themes share no files).

    python3 package.py        # full build, then dist/warp-legacy-<version>.tar.xz

The archive holds the built theme (build/, every icon set, the cursors,
wallpaper packages, plasmoids, the LibreOffice extension) with install.sh
and uninstall.sh: unpacked, `./install.sh --apply [neon|neon-blue]` needs neither
Python nor a build. The sources too heavy for it (the icon masters,
icons-neon2026/, 170 MB; the wallpaper sources) stay in the repository,
which is where a rebuild starts.

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
NAME = f"warp-legacy-{VERSION}"
archive = DIST / f"{NAME}.tar.xz"
ITEMS = ["build", "install.sh", "uninstall.sh", "README.md", "DESIGN.md", "LICENSE",
         "RELEASE-CHECKLIST.md", "TESTING.md", "libreoffice/README.md", "browser/README.md"]


def keep(info):
    if "__pycache__" in info.name:
        return None
    # the same owner for every file, as a download should have
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


with tarfile.open(archive, "w:xz", preset=6) as tar:
    for item in ITEMS:
        if (ROOT / item).exists():
            tar.add(ROOT / item, arcname=f"{NAME}/{item}", filter=keep)
    tar.add(ROOT / "previews/neon.png", arcname=f"{NAME}/preview.png", filter=keep)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DIST / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{archive}: {archive.stat().st_size:,} bytes")
