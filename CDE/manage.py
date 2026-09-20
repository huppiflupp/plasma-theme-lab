#!/usr/bin/env python3
"""User-profile installation with an explicit ownership and rollback manifest."""
import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
DATA = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
STATE = DATA / "cde-copper-install"
MANIFEST = STATE / "manifest.json"
CONFIG_FILES = ("kdeglobals", "kwinrc", "plasmarc", "ksplashrc", "kcminputrc",
                "konsolerc", "plasma-org.kde.plasma.desktop-appletsrc", "kdedefaults")
TARGETS = ("color-schemes/CDECopper.colors", "aurorae/themes/CDECopper",
           "plasma/desktoptheme/cde-copper", "plasma/look-and-feel/org.cde.copper.desktop",
           "plasma/plasmoids/org.cde.copper.frontpanel", "icons/CDECopper",
           "wallpapers/org.cde.copper", "konsole/CDECopper.colorscheme", "konsole/CDE Copper.profile")


def run(*args, check=True):
    return subprocess.run(args, check=check, text=True)


def dbus(*args):
    exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or "/usr/lib/qt6/bin/qdbus"
    run(exe, *args)


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def write_config(file, section, values):
    path = CONFIG / file
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(path)
    if not config.has_section(section):
        config.add_section(section)
    for key, value in values.items():
        config.set(section, key, str(value))
    with path.open("w") as out:
        config.write(out, space_around_delimiters=False)


def install():
    for target in TARGETS:
        if not (ROOT / "build" / target).exists():
            raise RuntimeError("Build first; missing " + target)
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        if manifest["data"] != str(DATA) or manifest["config"] != str(CONFIG):
            raise RuntimeError("Installation paths differ from the ownership manifest")
    else:
        collisions = [str(DATA / t) for t in TARGETS if (DATA / t).exists() or (DATA / t).is_symlink()]
        if collisions:
            raise RuntimeError("Refusing to overwrite unowned paths: " + ", ".join(collisions))
        if STATE.exists():
            if (STATE / "uninstalled-manifest.json").exists():
                STATE.rename(STATE.with_name(STATE.name + ".previous-" + str(time.time_ns())))
            else:
                raise RuntimeError("Backup directory exists without an installation manifest: " + str(STATE))
        STATE.mkdir(parents=True)
        present = []
        for file in CONFIG_FILES:
            if (CONFIG / file).exists():
                copy(CONFIG / file, STATE / "config" / file)
                present.append(file)
        manifest = {"version": 1, "data": str(DATA), "config": str(CONFIG),
                    "targets": list(TARGETS), "config_present": present, "applied": False}
        MANIFEST.write_text(json.dumps(manifest, indent=2))
    for target in TARGETS:
        if target not in manifest["targets"]:
            raise RuntimeError("Target not owned by this installation: " + target)
        remove(DATA / target)
        copy(ROOT / "build" / target, DATA / target)
    run("kbuildsycoca6", check=False)
    print("Installed CDE Copper. Original configuration: " + str(STATE / "config"))


def apply(panel=False):
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before applying it")
    manifest = json.loads(MANIFEST.read_text())
    manifest["applied"] = True
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    run("plasma-apply-lookandfeel", "--apply", "org.cde.copper.desktop")
    run("plasma-apply-colorscheme", "CDECopper")
    run("plasma-apply-desktoptheme", "cde-copper")
    write_config("kdeglobals", "KDE", {"widgetStyle": "Windows", "LookAndFeelPackage": "org.cde.copper.desktop"})
    write_config("kdeglobals", "Icons", {"Theme": "CDECopper"})
    write_config("kdeglobals", "General", {"font": "Noto Sans,10,-1,5,50,0,0,0,0,0", "fixed": "Noto Sans Mono,10,-1,5,50,0,0,0,0,0"})
    write_config("kwinrc", "org.kde.kdecoration2", {"library": "org.kde.kwin.aurorae", "theme": "__aurorae__svg__CDECopper", "ButtonsOnLeft": "M", "ButtonsOnRight": "IAX", "BorderSize": "Normal"})
    write_config("kwinrc", "WM", {"activeFont": "Noto Sans,10,-1,5,63,0,0,0,0,0"})
    write_config("konsolerc", "Desktop Entry", {"DefaultProfile": "CDE Copper.profile"})
    dbus("org.kde.KWin", "/KWin", "reconfigure")
    if panel:
        # KWin exposes workspace creation through D-Bus; no session restart required.
        exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
        count = int(subprocess.check_output([exe, "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.count"], text=True).strip())
        for i in range(count, 4):
            dbus("org.kde.KWin", "/VirtualDesktopManager", "createDesktop", str(i), ("One", "Two", "Three", "Four")[i])
        dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", (ROOT / "layout.js").read_text())
    print("Applied. Log out and back in to reload all application styles and the decoration.")


def uninstall():
    if not MANIFEST.exists():
        raise RuntimeError("No CDE Copper ownership manifest found")
    manifest = json.loads(MANIFEST.read_text())
    if manifest["data"] != str(DATA) or manifest["config"] != str(CONFIG):
        raise RuntimeError("Installation paths differ from the manifest")
    if any(target not in TARGETS for target in manifest["targets"]):
        raise RuntimeError("Unexpected target in ownership manifest")
    if manifest["applied"]:
        run("systemctl", "--user", "stop", "plasma-plasmashell.service")
        for file in CONFIG_FILES:
            remove(CONFIG / file)
            if file in manifest["config_present"]:
                copy(STATE / "config" / file, CONFIG / file)
    for target in manifest["targets"]:
        remove(DATA / target)
    for cache in (HOME / ".cache").glob("plasma_theme_cde-copper*"):
        remove(cache)
    if manifest["applied"]:
        dbus("org.kde.KWin", "/KWin", "reconfigure")
        run("systemctl", "--user", "start", "plasma-plasmashell.service")
    MANIFEST.rename(STATE / "uninstalled-manifest.json")
    print("Removed only manifest-owned files and restored pre-install configuration. Backup retained at " + str(STATE))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "apply", "uninstall"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--panel", action="store_true", help="replace the panel layout, backed up on installation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print("\n".join(str(DATA / t) for t in TARGETS))
        return
    if os.geteuid() == 0:
        raise RuntimeError("Run as the desktop user, not root")
    if args.action == "install":
        install()
        if args.apply:
            apply(args.panel)
    elif args.action == "apply":
        apply(args.panel)
    else:
        uninstall()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
