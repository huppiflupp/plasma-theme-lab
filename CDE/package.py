#!/usr/bin/env python3
"""Package the built theme and its reproducible vector sources.

The pictures under wallpapers/ (92 MB of JPEG sources) stay out: build/
holds them as the installed wallpaper packages, and the sources are in
the repository for anyone rebuilding."""
import hashlib
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import VERSION  # noqa: E402

DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
archive = DIST / f"cde-copper-{VERSION}.tar.xz"
items = ["build", "frontpanel", "stylemanager", "decoration", "arrange", "backdrop", "fonts", "palettes", "backdrops", "tools", "lookandfeel", "shell", "tabbox", "po", "i18n.py", "build.py", "icons.py", "cursors.py", "gtktheme.py", "systemparts.py", "system.py",
         "kvantum.py", "palettes.py", "backdrops.py", "configpage.py", "manage.py", "install.sh",
         "apply.sh", "uninstall.sh", "layout.js", "README.md", "LICENSE", "TESTING.md", "tests"]
with tarfile.open(archive, "w:xz") as tar:
    for item in items:
        tar.add(ROOT / item, arcname="cde-copper/" + item,
                filter=lambda info: None if "__pycache__" in info.name else info)
    tar.add(ROOT / "screenshots/desktop-arranged-1920.png", arcname="cde-copper/preview.png")
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DIST / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{archive}: {archive.stat().st_size:,} bytes")
