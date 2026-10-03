#!/usr/bin/env python3
"""CDE Copper's system parts: boot splash (Plymouth) and boot menu (GRUB).

Run as root, from the extracted package after build.py:

    sudo python3 system.py install [--parts plymouth,grub] [--palette NAME]
    sudo python3 system.py uninstall
    sudo python3 system.py status

Everything it changes is recorded in /var/lib/cde-copper/system.json with
a copy of each file it edits, and uninstall puts it back: the previous
Plymouth theme (initramfs rebuilt), /etc/default/grub (grub.cfg rebuilt),
the theme folders removed. The user-level theme (manage.py) is separate.

The boot parts take the colours of a CDE palette: by default the one the
user calling sudo has applied (from their CDE Copper manifest), Copper when
there is none. After switching palettes, run install again to follow.
"""
import argparse
import fcntl
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build/system"
STATE = Path("/var/lib/cde-copper")
MANIFEST = STATE / "system.json"
PLYMOUTH_DIR = Path("/usr/share/plymouth/themes/cde-copper")
NAME = "cde-copper"
GFXPAYLOAD = Path("/etc/grub.d/09_cde_copper_gfxpayload")


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
    pending = MANIFEST.with_suffix(".tmp")
    pending.write_text(json.dumps(manifest, indent=2))
    pending.replace(MANIFEST)


def user_palette():
    """The palette applied by the user behind sudo, Copper if unknown."""
    try:
        home = Path(pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir)
        manifest = home / ".local/share/cde-copper-install/manifest.json"
        return json.loads(manifest.read_text()).get("palette", "Copper")
    except (KeyError, OSError, ValueError):
        return "Copper"


def build_for(palette):
    """build/system as shipped for Copper; other palettes are drawn afresh
    into a temporary folder from the same generators."""
    global BUILD
    if palette == "Copper":
        return
    sys.path.insert(0, str(ROOT))
    import palettes
    from systemparts import build_system
    out = Path(tempfile.mkdtemp(prefix="cde-copper-system-"))
    build_system(out, palettes.theme(palette))
    BUILD = out / "system"
    print(f"Boot screens drawn in the colours of palette {palette}")


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
    if (PLYMOUTH_DIR.exists() or PLYMOUTH_DIR.is_symlink()) and "plymouth" not in manifest["parts"]:
        raise RuntimeError("Refusing to overwrite unowned path: " + str(PLYMOUTH_DIR))
    manifest["parts"]["plymouth"] = {"previous": previous if previous != NAME else
                                     manifest["parts"].get("plymouth", {}).get("previous", "bgrt")}
    save(manifest)
    if PLYMOUTH_DIR.exists():
        shutil.rmtree(PLYMOUTH_DIR)
    shutil.copytree(BUILD / "plymouth/cde-copper", PLYMOUTH_DIR)
    print("Rebuilding the initramfs; this takes a minute.")
    run(tool, "-R", NAME)


def plymouth_uninstall(manifest):
    part = manifest["parts"].get("plymouth")
    if not part:
        return
    tool = which("plymouth-set-default-theme")
    if not tool:
        raise RuntimeError("plymouth-set-default-theme missing; ownership retained")
    # Keep the theme and recovery record until the initramfs is restored.
    run(tool, "-R", part["previous"])
    if PLYMOUTH_DIR.exists():
        shutil.rmtree(PLYMOUTH_DIR)
    del manifest["parts"]["plymouth"]
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
    part = manifest["parts"].get("grub") or {}
    if not part:
        for path in (theme, GFXPAYLOAD):
            if path.exists() or path.is_symlink():
                raise RuntimeError("Refusing to overwrite unowned path: " + str(path))
        STATE.mkdir(parents=True, exist_ok=True)
        shutil.copy2("/etc/default/grub", STATE / "default-grub")
        part = {"backup": str(STATE / "default-grub"), "folder": str(folder), "prefix": prefix}
        manifest["parts"]["grub"] = part
        save(manifest)
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
    # gfxpayload=keep hands GRUB's graphics mode to the kernel, so the
    # screen does not drop to a black text mode before Plymouth starts.
    set_defaults(defaults, {"GRUB_THEME": str(theme / "theme.txt"), "GRUB_TERMINAL_OUTPUT": "gfxterm",
                            "GRUB_GFXPAYLOAD_LINUX": "keep"})
    # Boot loader spec entries (Fedora) ignore GRUB_GFXPAYLOAD_LINUX: a
    # global, exported setting reaches them too.
    # The terminal in the window colour (terminal.cfg), where GRUB has the
    # module for it: not under Secure Boot.
    colour = "" if secure_boot() else (theme / "terminal.cfg").read_text()
    GFXPAYLOAD.write_text("#!/bin/sh\n# CDE Copper: keep GRUB's graphics mode for Plymouth (system.py uninstall removes this)\n"
                          "cat <<'EOF'\nset gfxpayload=keep\nexport gfxpayload\n" + colour + "EOF\n")
    GFXPAYLOAD.chmod(0o755)
    run(f"{prefix}-mkconfig", "-o", folder / "grub.cfg")


def grub_uninstall(manifest):
    part = manifest["parts"].get("grub")
    if part:
        shutil.copy2(part["backup"], "/etc/default/grub")
        folder = Path(part["folder"])
        if GFXPAYLOAD.exists():
            GFXPAYLOAD.unlink()
        run(f"{part['prefix']}-mkconfig", "-o", folder / "grub.cfg")
        if (folder / "themes" / NAME).exists():
            shutil.rmtree(folder / "themes" / NAME)
        del manifest["parts"]["grub"]
    save(manifest)


PARTS = {"plymouth": (plymouth_install, plymouth_uninstall), "grub": (grub_install, grub_uninstall)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--parts", default="plymouth,grub", help="comma-separated: " + ", ".join(PARTS))
    parser.add_argument("--grub-background", default="altai-dark",
                        help="lattice (the CDE backdrop) or a picture of wallpapers/images, e.g. altai-dark, fluss-dark")
    parser.add_argument("--palette", help="CDE palette for the boot screens (default: the one you applied, else Copper)")
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
    if args.action == "install":
        palette = args.palette or user_palette()
        try:
            build_for(palette)
        except KeyError as error:
            print(error, file=sys.stderr)
            return 1
        manifest["palette"] = palette
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
        except (RuntimeError, OSError) as error:
            print(f"{name}: {error}", file=sys.stderr)
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    # Serialize installs and uninstalls; status stays read-only.
    if "status" in sys.argv or os.geteuid() != 0:
        sys.exit(main())
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sys.exit(main())
