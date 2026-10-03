#!/usr/bin/env python3
"""CDE Copper's system parts: boot splash (Plymouth) and boot menu (GRUB).

Run as root, from the extracted package after build.py:

    sudo python3 system.py install [--parts plymouth,grub]
    sudo python3 system.py uninstall
    sudo python3 system.py status

Everything it changes is recorded in /var/lib/cde-copper/system.json with
a copy of each file it edits, and uninstall puts it back: the previous
Plymouth theme (initramfs rebuilt), /etc/default/grub (grub.cfg rebuilt),
the theme folders removed. The user-level theme (manage.py) is separate.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build/system"
STATE = Path("/var/lib/cde-copper")
MANIFEST = STATE / "system.json"
PLYMOUTH_DIR = Path("/usr/share/plymouth/themes/cde-copper")
NAME = "cde-copper"


def run(*args, check=True):
    print("+", " ".join(str(a) for a in args))
    return subprocess.run([str(a) for a in args], check=check, text=True, capture_output=True)


def which(*names):
    return next((shutil.which(n) for n in names if shutil.which(n)), None)


def grub_paths():
    """Fedora keeps GRUB 2 under /boot/grub2 with grub2-* tools, Debian under
    /boot/grub with grub-* tools."""
    for folder, prefix in ((Path("/boot/grub2"), "grub2"), (Path("/boot/grub"), "grub")):
        if folder.is_dir() and which(f"{prefix}-mkconfig"):
            return folder, prefix
    return None, None


def load():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"parts": {}}


def save(manifest):
    STATE.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2))


# ---- Plymouth ---------------------------------------------------------------

def plymouth_install(manifest):
    tool = which("plymouth-set-default-theme")
    if not tool:
        print("plymouth-set-default-theme not found; boot splash skipped")
        return
    # The theme is a script for Plymouth's script module, packaged apart on
    # some systems.
    modules = [Path(d) / "plymouth/script.so" for d in ("/usr/lib64", "/usr/lib", "/usr/lib/x86_64-linux-gnu", "/usr/lib/aarch64-linux-gnu")]
    if not any(m.exists() for m in modules):
        raise RuntimeError("Plymouth's script module is missing: install plymouth-plugin-script (Fedora) "
                           "or plymouth-themes (Debian, Ubuntu), then run this again")
    previous = run(tool).stdout.strip()
    if PLYMOUTH_DIR.exists():
        shutil.rmtree(PLYMOUTH_DIR)
    shutil.copytree(BUILD / "plymouth/cde-copper", PLYMOUTH_DIR)
    print("Rebuilding the initramfs; this takes a minute.")
    run(tool, "-R", NAME)
    manifest["parts"]["plymouth"] = {"previous": previous if previous != NAME else
                                     manifest["parts"].get("plymouth", {}).get("previous", "bgrt")}
    save(manifest)


def plymouth_uninstall(manifest):
    part = manifest["parts"].pop("plymouth", None)
    tool = which("plymouth-set-default-theme")
    if part and tool:
        run(tool, "-R", part["previous"], check=False)
    if PLYMOUTH_DIR.exists():
        shutil.rmtree(PLYMOUTH_DIR)
    save(manifest)


# ---- GRUB -------------------------------------------------------------------

def pf2_name(path):
    """The font name GRUB knows a .pf2 font by (its NAME section)."""
    data = path.read_bytes()
    at = data.find(b"NAME")
    length = int.from_bytes(data[at + 4:at + 8], "big")
    return data[at + 8:at + 8 + length].rstrip(b"\0").decode()


def secure_boot():
    """Under UEFI Secure Boot GRUB refuses to load font files (since 2.06), so
    the theme keeps to GRUB's built-in Unifont there."""
    for var in Path("/sys/firmware/efi/efivars").glob("SecureBoot-*"):
        try:
            return var.read_bytes()[-1] == 1
        except OSError:
            return False
    return False


def set_defaults(path, values):
    text = path.read_text()
    for key, value in values.items():
        line = f'{key}="{value}"'
        if re.search(rf"^#?\s*{key}=.*$", text, re.M):
            text = re.sub(rf"^#?\s*{key}=.*$", line, text, count=1, flags=re.M)
        else:
            text = text.rstrip("\n") + "\n" + line + "\n"
    path.write_text(text)


def grub_install(manifest, background="altai-dark"):
    folder, prefix = grub_paths()
    if not folder:
        print("GRUB 2 not found; boot menu skipped")
        return
    theme = folder / "themes" / NAME
    if theme.exists():
        shutil.rmtree(theme)
    shutil.copytree(BUILD / "grub/cde-copper", theme)
    # A picture of the theme's own wallpapers instead of the tiled backdrop,
    # when the package carries them.
    picture = ROOT / "wallpapers/images" / f"{background}.jpg"
    if background != "lattice" and picture.exists():
        shutil.copy2(picture, theme / "background.jpg")
        text = (theme / "theme.txt").read_text().replace('"background.png"', '"background.jpg"')
        (theme / "theme.txt").write_text(text)
    elif background != "lattice":
        print(f"{picture} not found; the menu keeps the tiled backdrop")
    # Fonts from IBM Plex; the theme names them as GRUB reads them. Under
    # Secure Boot GRUB loads no font files: its built-in Unifont instead.
    names = {}
    if secure_boot():
        print("Secure Boot is on: GRUB loads no font files, the menu uses GRUB's Unifont")
        names = {"sans": "Unifont Regular 16", "mono": "Unifont Regular 16"}
    else:
        fonts = {"sans": (ROOT / "fonts/IBMPlex/IBMPlexSansCondensed-Regular.otf", 20),
                 "mono": (ROOT / "fonts/IBMPlex/IBMPlexMono-Regular.otf", 16)}
        for key, (source, size) in fonts.items():
            target = theme / f"{key}-{size}.pf2"
            run(f"{prefix}-mkfont", "-s", size, "-o", target, source)
            names[key] = pf2_name(target)
    text = (theme / "theme.txt").read_text()
    text = text.replace("IBM Plex Sans Condensed Regular 20", names["sans"]).replace("IBM Plex Mono Regular 16", names["mono"])
    (theme / "theme.txt").write_text(text)
    defaults = Path("/etc/default/grub")
    part = manifest["parts"].get("grub") or {}
    if "backup" not in part:
        STATE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(defaults, STATE / "default-grub")
        part = {"backup": str(STATE / "default-grub")}
    part.update({"folder": str(folder), "prefix": prefix})
    manifest["parts"]["grub"] = part
    save(manifest)
    set_defaults(defaults, {"GRUB_THEME": str(theme / "theme.txt"), "GRUB_TERMINAL_OUTPUT": "gfxterm"})
    run(f"{prefix}-mkconfig", "-o", folder / "grub.cfg")


def grub_uninstall(manifest):
    part = manifest["parts"].pop("grub", None)
    if part:
        shutil.copy2(part["backup"], "/etc/default/grub")
        folder = Path(part["folder"])
        if (folder / "themes" / NAME).exists():
            shutil.rmtree(folder / "themes" / NAME)
        run(f"{part['prefix']}-mkconfig", "-o", folder / "grub.cfg", check=False)
    save(manifest)


PARTS = {"plymouth": (plymouth_install, plymouth_uninstall), "grub": (grub_install, grub_uninstall)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--parts", default="plymouth,grub", help="comma-separated: " + ", ".join(PARTS))
    parser.add_argument("--grub-background", default="altai-dark",
                        help="lattice (the CDE backdrop) or a picture of wallpapers/images, e.g. altai-dark, fluss-dark")
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps(load(), indent=2))
        return 0
    if os.geteuid() != 0:
        print("Run as root (sudo python3 system.py ...)", file=sys.stderr)
        return 1
    if args.action == "install" and not BUILD.exists():
        print("Build first: python3 build.py", file=sys.stderr)
        return 1
    manifest = load()
    for name in [p.strip() for p in args.parts.split(",") if p.strip()]:
        if name not in PARTS:
            print(f"Unknown part {name!r}", file=sys.stderr)
            return 1
        install, uninstall = PARTS[name]
        try:
            if args.action == "install":
                install(manifest, args.grub_background) if name == "grub" else install(manifest)
            else:
                uninstall(manifest)
        except subprocess.CalledProcessError as error:
            print(f"{name}: {' '.join(error.cmd)} failed:\n{error.stdout}{error.stderr}", file=sys.stderr)
            return 1
        except RuntimeError as error:
            print(f"{name}: {error}", file=sys.stderr)
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
