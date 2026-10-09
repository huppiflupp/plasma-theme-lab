#!/usr/bin/env python3
"""Package the built theme and its reproducible vector sources, and the
pictures as an archive of their own.

    cde-copper-<version>.tar.xz            the theme, installed with install.sh
    cde-copper-wallpapers-<version>.tar.gz the 40 picture packages and the teal desktop, unpacked
                                           into ~/.local/share/wallpapers

The pictures under wallpapers/ (92 MB of JPEG sources) stay out of the
theme archive: build/ holds them as the installed wallpaper packages, and
the sources are in the repository for anyone rebuilding. The picture
archive holds the packages at its top level, as the store unpacks
wallpaper archives: each picture light and dark at 3840x2160."""
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
pictures = DIST / f"cde-copper-wallpapers-{VERSION}.tar.gz"
with tarfile.open(pictures, "w:gz", compresslevel=6) as tar:
    for package in sorted((ROOT / "build/wallpapers").iterdir()):
        tar.add(package, arcname=package.name)
    tar.add(ROOT / "LICENSE", arcname="LICENSE")
    tar.add(ROOT / "wallpapers/README.md", arcname="README.md")
lines = []
for made in (archive, pictures):
    digest = hashlib.sha256(made.read_bytes()).hexdigest()
    lines.append(f"{digest}  {made.name}\n")
    print(f"{made}: {made.stat().st_size:,} bytes")
(DIST / "SHA256SUMS").write_text("".join(lines))
