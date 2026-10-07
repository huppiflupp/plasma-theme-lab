#!/usr/bin/env python3
"""CDE Copper's system parts: boot splash (Plymouth), boot menu (GRUB) and
login screen (Plasma Login Manager).

Run as root, from the extracted package after build.py:

    sudo python3 system.py install [--parts plymouth,grub,login] [--palette NAME]
    sudo python3 system.py uninstall
    sudo python3 system.py status

Everything it changes is recorded in /var/lib/cde-copper/system.json with
a copy of each file it edits, and uninstall puts it back: the previous
Plymouth theme (initramfs rebuilt), /etc/default/grub (grub.cfg rebuilt),
/etc/plasmalogin.conf and the greeter user's settings, the theme folders
removed. The user-level theme (manage.py) is separate.

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


# ---- Login screen (Plasma Login Manager) -----------------------------------
#
# The greeter's QML is compiled into plasma-login-greeter, so there is no
# theme folder to fill. What it does read: a wallpaper plugin and its
# settings from /etc/plasmalogin.conf, and the Plasma theme, colours and
# fonts of its own user (plasmalogin, home /var/lib/plasmalogin). This part
# sets those: the tiled backdrop (or a picture), CDE's Plasma surfaces, the
# palette's colours and IBM Plex. "Apply Plasma settings" on System Settings'
# login screen page replaces the greeter user's files; run install again.

LOGIN_DIR = Path("/usr/share/cde-copper/login")
LOGIN_MAIN = Path("/etc/plasmalogin.conf")
LOGIN_FONTS = Path("/usr/share/fonts/cde-copper")
LOGIN_FILES = ("kdeglobals", "plasmarc")
UI_FONT = "IBM Plex Sans Condensed,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
MONO_FONT = "IBM Plex Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"


def login_palette(palette, stage):
    """The palette's colour scheme file and Plasma theme folder."""
    if palette == "Copper":
        return ROOT / "build/color-schemes/CDECopper.colors", ROOT / "build/plasma/desktoptheme/cde-copper"
    sys.path.insert(0, str(ROOT))
    import build
    result = build.build_palette(palette, stage)
    return ROOT / f"build/color-schemes/{result['colors']}.colors", stage / result["targets"][0]


def strip_greeter_groups(text):
    """/etc/plasmalogin.conf without its [Greeter...] groups (Nobara puts its
    own wallpaper there)."""
    keep, inside = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("["):
            inside = line.startswith("[Greeter]")
        if not inside:
            keep.append(line)
    return "".join(keep)


def screen_size():
    """The largest preferred mode of the connected screens, 1920x1080 if none."""
    sizes = []
    for status in Path("/sys/class/drm").glob("card*-*/status"):
        try:
            modes = (status.parent / "modes").read_text().split()
            if status.read_text().strip() == "connected" and modes:
                w, h = (int(v) for v in re.match(r"(\d+)x(\d+)", modes[0]).groups())
                sizes.append((w, h))
        except (OSError, AttributeError, ValueError):
            pass
    return max(sizes, key=lambda s: s[0] * s[1]) if sizes else (1920, 1080)


def greeter_colours(scheme):
    """The palette's colour scheme for the greeter. The greeter draws the
    clock, the labels and the icons on the backdrop in the Button set (6.7.5):
    that set takes the Complementary colours, light text on the dark panel
    colour."""
    groups, name = {}, None
    for line in scheme.splitlines():
        if line.startswith("["):
            name = line.strip()
            groups.setdefault(name, [])
        elif name and line.strip():
            groups[name].append(line)
    if "[Colors:Complementary]" in groups:
        groups["[Colors:Button]"] = list(groups["[Colors:Complementary]"])
    groups.setdefault("[General]", [])
    groups["[General]"] = [l for l in groups["[General]"] if l.split("=")[0] not in ("font", "fixed", "menuFont", "toolBarFont")]
    groups["[General]"] += [f"font={UI_FONT}", f"fixed={MONO_FONT}", f"menuFont={UI_FONT}", f"toolBarFont={UI_FONT}"]
    return "".join(f"{group}\n" + "".join(l + "\n" for l in lines) + "\n" for group, lines in groups.items())


def login_install(manifest, palette, background="lattice"):
    try:
        account = pwd.getpwnam("plasmalogin")
    except KeyError:
        print("Plasma Login Manager not found (no plasmalogin user); login screen skipped")
        return
    home = Path(account.pw_dir)
    config = home / ".config"
    part = manifest["parts"].get("login")
    if not part:
        for path in (LOGIN_DIR, LOGIN_FONTS):
            if path.exists() or path.is_symlink():
                raise RuntimeError("Refusing to overwrite unowned path: " + str(path))
        backup = STATE / "login"
        backup.mkdir(parents=True, exist_ok=True)
        saved = []
        for name in LOGIN_FILES:
            if (config / name).exists():
                shutil.copy2(config / name, backup / name)
                saved.append(name)
        if LOGIN_MAIN.exists():
            shutil.copy2(LOGIN_MAIN, backup / "plasmalogin.conf")
        part = {"backup": str(backup), "saved": saved, "main": LOGIN_MAIN.exists(), "plasma": []}
        manifest["parts"]["login"] = part
        save(manifest)
    stage = Path(tempfile.mkdtemp(prefix="cde-copper-login-"))
    try:
        scheme, desktoptheme = login_palette(palette, stage)
        # The Plasma theme system-wide, where the greeter's user finds it.
        for old in part["plasma"]:
            if Path(old).exists():
                shutil.rmtree(old)
        target = Path("/usr/share/plasma/desktoptheme") / desktoptheme.name
        if target.exists() or target.is_symlink():
            raise RuntimeError("Refusing to overwrite unowned path: " + str(target))
        part["plasma"] = [str(target)]
        save(manifest)
        shutil.copytree(desktoptheme, target)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    # Fonts.
    if LOGIN_FONTS.exists():
        shutil.rmtree(LOGIN_FONTS)
    LOGIN_FONTS.mkdir(parents=True)
    for font in ("IBMPlexSansCondensed-Regular", "IBMPlexSansCondensed-SemiBold", "IBMPlexSansCondensed-Bold",
                 "IBMPlexMono-Regular", "IBMPlexMono-Bold"):
        source = ROOT / "fonts/IBMPlex" / f"{font}.otf"
        if source.exists():
            shutil.copy2(source, LOGIN_FONTS)
    run("fc-cache", "-f", LOGIN_FONTS, check=False)
    # The backdrop tile of the boot splash, or one of the theme's pictures.
    if LOGIN_DIR.exists():
        shutil.rmtree(LOGIN_DIR)
    LOGIN_DIR.mkdir(parents=True)
    picture = ROOT / "wallpapers/images" / f"{background}.jpg"
    if background != "lattice" and picture.exists():
        image, fill = LOGIN_DIR / "background.jpg", 2       # Image.PreserveAspectCrop
        shutil.copy2(picture, image)
    else:
        if background != "lattice":
            print(f"{picture} not found; the login screen keeps the tiled backdrop")
        # The greeter scales any image to the screen, tiles too: the backdrop
        # filled to the largest screen instead, shown unscaled (Image.Pad).
        sys.path.insert(0, str(ROOT))
        import backdrops
        import palettes
        width, height = screen_size()
        if palette == "Copper":
            from build import P
        else:
            P = palettes.theme(palette)
        colours = backdrops.colours_for(palettes.colour_set(P["desktop"]))
        image, fill = LOGIN_DIR / "backdrop.png", 6
        image.write_bytes(backdrops.desktop("Lattice", colours, width, height))
    # Into plasmalogin.conf itself: the greeter takes the plugin and FillMode
    # from plasmalogin.conf.d too, but the Image only from here (6.7.5). The
    # key is WallpaperPluginId; Fedora's defaults.conf spells it WallpaperPlugin.
    main = strip_greeter_groups(LOGIN_MAIN.read_text()) if LOGIN_MAIN.exists() else ""
    LOGIN_MAIN.write_text(main.rstrip("\n") + "\n\n# CDE Copper login screen (system.py uninstall restores the previous file)\n"
                          "[Greeter]\nWallpaperPluginId=org.kde.image\n\n"
                          "[Greeter][Wallpaper][org.kde.image][General]\n"
                          f"Image=file://{image}\nFillMode={fill}\n")
    # The greeter user's colours, fonts and Plasma theme.
    config.mkdir(parents=True, exist_ok=True)
    os.chown(config, account.pw_uid, account.pw_gid)
    files = {"kdeglobals": "# CDE Copper login screen (system.py)\n" + greeter_colours(scheme.read_text()),
             "plasmarc": f"# CDE Copper login screen (system.py)\n[Theme]\nname={target.name}\n"}
    for name, text in files.items():
        (config / name).write_text(text)
        os.chown(config / name, account.pw_uid, account.pw_gid)
    # copy2 carries the SELinux label of the extracted package (user_home_t)
    # along; the system's own labels instead.
    if which("restorecon"):
        run("restorecon", "-R", target, LOGIN_DIR, LOGIN_FONTS, config, LOGIN_MAIN, check=False)
    manifest["parts"]["login"] = part
    save(manifest)
    print("Login screen set; it shows at the next login (or: systemctl restart plasmalogin, which ends sessions)")


def login_uninstall(manifest):
    part = manifest["parts"].get("login")
    if not part:
        return
    backup = Path(part["backup"])
    try:
        account = pwd.getpwnam("plasmalogin")
        config = Path(account.pw_dir) / ".config"
        for name in LOGIN_FILES:
            if name in part["saved"]:
                shutil.copy2(backup / name, config / name)
                os.chown(config / name, account.pw_uid, account.pw_gid)
            elif (config / name).exists():
                (config / name).unlink()
    except KeyError:
        pass
    if part.get("main") and (backup / "plasmalogin.conf").exists():
        shutil.copy2(backup / "plasmalogin.conf", LOGIN_MAIN)
    elif LOGIN_MAIN.exists():
        LOGIN_MAIN.write_text(strip_greeter_groups(LOGIN_MAIN.read_text()))
    for path in [Path(p) for p in part["plasma"]] + [LOGIN_DIR, LOGIN_FONTS]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    if LOGIN_DIR.parent.exists() and not any(LOGIN_DIR.parent.iterdir()):
        LOGIN_DIR.parent.rmdir()
    run("fc-cache", "-f", check=False)
    shutil.rmtree(backup, ignore_errors=True)
    del manifest["parts"]["login"]
    save(manifest)


PARTS = {"plymouth": (plymouth_install, plymouth_uninstall), "grub": (grub_install, grub_uninstall),
         "login": (login_install, login_uninstall)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--parts", default="plymouth,grub,login", help="comma-separated: " + ", ".join(PARTS))
    parser.add_argument("--grub-background", default="altai-dark",
                        help="lattice (the CDE backdrop) or a picture of wallpapers/images, e.g. altai-dark, fluss-dark")
    parser.add_argument("--login-background", default="lattice",
                        help="lattice (the CDE backdrop, tiled) or a picture of wallpapers/images")
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
                if name == "grub":
                    install(manifest, args.grub_background)
                elif name == "login":
                    install(manifest, palette, args.login_background)
                else:
                    install(manifest)
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
