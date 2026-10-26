#!/usr/bin/env python3
"""Package RISC Legacy for release (after Warp Legacy's package.py, a copy;
the themes share no files).

    python3 package.py        # full build, then dist/risc-legacy-<version>.tar.xz

One archive, one KDE Store entry (STORE.md): the built theme with all
eight variants, the wallpapers and the fonts, with install.sh and
uninstall.sh. Unpacked, `./install.sh --apply classic --layout` needs
neither Python nor a build. The icons go in as one inner tar, icons.tar,
which install.sh unpacks into build/ the first time: "Get New…" copies a
package file by file, syncing each, and the 16,000 icon files alone took
it eight minutes in the VM (26.10.2026); without them it is ~1,000 files. The sources (iconkit/, the wallpaper sources,
vendor/) stay in the repository, which is where a rebuild starts; the
licences of what the build takes from them go into the archive.

The store's "Get New…" hands a Global Theme entry's file to kpackagetool,
which wants one package with its metadata.json in the archive's single
folder. The folder therefore also carries the classic global theme
(metadata.json, contents/): "Get New…" installs that theme, named and with
its preview; install.sh in that folder brings the rest (Warp Legacy's
package.py, NT Legacy 0.2.3).
"""
import hashlib
import io
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import VARIANTS, VERSION, ids  # noqa: E402

subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)

BUILD = ROOT / "build"
# the parts every release has: a build interrupted by another one packed
# Warp Legacy without an icon set and still reported success (21.10.2026)
NEEDED = ["icons/RiscLegacy", "icons/RiscLegacy2026", "risc-legacy/variants",
          "risc-legacy/shell/follow", "fonts/risc-legacy/TeXGyreHeros"]
NEEDED += [f"plasma/look-and-feel/{ids(v)['lnf']}" for v in VARIANTS]
missing = [n for n in NEEDED if not (BUILD / n).exists()]
if missing:
    sys.exit("build/ is incomplete, not packed: " + ", ".join(missing))

DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
ITEMS = ["install.sh", "uninstall.sh", "README.md", "DESIGN.md", "LICENSE",
         "vendor/riscos-open/LICENSE", "vendor/riscos-open/NOTICE"]
LNF = "org.risclegacy.desktop"


def keep(info):
    if "__pycache__" in info.name:
        return None
    # the same owner for every file, as a download should have
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


top = f"risc-legacy-{VERSION}"
archive = DIST / f"{top}.tar.xz"
# GNU, not Python's default PAX: kpackagetool6 (KArchive) could not open a
# PAX archive (Warp Legacy Neon, Fedora VM, 25.10.2026)
with tarfile.open(archive, "w:xz", preset=6, format=tarfile.GNU_FORMAT) as tar:
    theme = BUILD / "plasma/look-and-feel" / LNF
    tar.add(theme / "metadata.json", arcname=f"{top}/metadata.json", filter=keep)
    tar.add(theme / "contents", arcname=f"{top}/contents", filter=keep)
    tar.add(BUILD, arcname=f"{top}/build",
            filter=lambda info: None if info.name.startswith(f"{top}/build/icons") else keep(info))
    inner = io.BytesIO()
    with tarfile.open(fileobj=inner, mode="w", format=tarfile.GNU_FORMAT) as icons:
        icons.add(BUILD / "icons", arcname="icons", filter=keep)
    info = tarfile.TarInfo(f"{top}/icons.tar")
    info.size, info.mode, info.mtime = inner.tell(), 0o644, (BUILD / "icons").stat().st_mtime
    inner.seek(0)
    tar.addfile(keep(info), inner)
    for item in ITEMS:
        tar.add(ROOT / item, arcname=f"{top}/{item}", filter=keep)
    tar.add(ROOT / "previews/classic.png", arcname=f"{top}/preview.png", filter=keep)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DIST / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{archive}: {archive.stat().st_size:,} bytes")
