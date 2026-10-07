#!/usr/bin/env python3
"""Package the built theme and its reproducible vector sources."""
import hashlib
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
archive = DIST / "cde-copper-0.8.13.tar.xz"
items = ["build", "frontpanel", "decoration", "arrange", "backdrop", "fonts", "palettes", "backdrops", "wallpapers", "tools", "lookandfeel", "shell", "tabbox", "po", "i18n.py", "build.py", "icons.py", "cursors.py", "gtktheme.py", "systemparts.py", "system.py",
         "kvantum.py", "palettes.py", "backdrops.py", "manage.py", "install.sh",
         "apply.sh", "uninstall.sh", "layout.js", "README.md", "LICENSE", "TESTING.md", "tests"]
with tarfile.open(archive, "w:xz") as tar:
    for item in items:
        tar.add(ROOT / item, arcname="cde-copper/" + item,
                filter=lambda info: None if "__pycache__" in info.name else info)
    tar.add(ROOT / "screenshots/desktop-arranged-1920.png", arcname="cde-copper/preview.png")
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DIST / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{archive}: {archive.stat().st_size:,} bytes")
