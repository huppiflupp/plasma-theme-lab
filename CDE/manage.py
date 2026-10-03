#!/usr/bin/env python3
"""User-profile installation with an explicit ownership and rollback manifest."""
import argparse
import configparser
import json
import re
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
                "konsolerc", "plasma-org.kde.plasma.desktop-appletsrc", "kdedefaults",
                "Kvantum/kvantum.kvconfig")
# Owned paths below XDG_CONFIG_HOME: the Kvantum widget style lives there.
CONFIG_TARGETS = ("Kvantum/CDECopper",)
KVANTUM_PLUGINS = ("/usr/lib64/qt6/plugins/styles/libkvantum.so",
                   "/usr/lib/x86_64-linux-gnu/qt6/plugins/styles/libkvantum.so",
                   "/usr/lib/qt6/plugins/styles/libkvantum.so")
DECORATION = "kwin4_decoration_qml_cdecopper"
TARGETS = ("color-schemes/CDECopper.colors", "kwin/decorations/" + DECORATION, "kwin/scripts/cde-copper-arrange",
           "plasma/desktoptheme/cde-copper", "plasma/look-and-feel/org.cde.copper.desktop",
           "plasma/plasmoids/org.cde.copper.frontpanel", "icons/CDECopper",
           "wallpapers/org.cde.copper", "wallpapers/CDEBackdrops", "konsole/CDECopper.colorscheme", "konsole/CDE Copper.profile",
           "fonts/CDECopper")
# Owned by 0.1.0 installations and removed when they are upgraded.
LEGACY_TARGETS = ("aurorae/themes/CDECopper",)
# A CDE palette, once applied, owns exactly these generated paths.
PALETTE_PATTERNS = (r"color-schemes/CDE[A-Za-z]+\.colors", r"plasma/desktoptheme/cde-[a-z]+")
PALETTE_CONFIG_PATTERNS = (r"Kvantum/CDE[A-Za-z]+",)
UI_FONT = "IBM Plex Sans Condensed,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
TITLE_FONT = "IBM Plex Sans Condensed,10,-1,5,600,0,0,0,0,0,0,0,0,0,0,1"
MONO_FONT = "IBM Plex Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"


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
    path.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(path)
    if not config.has_section(section):
        config.add_section(section)
    for key, value in values.items():
        config.set(section, key, str(value))
    with path.open("w") as out:
        config.write(out, space_around_delimiters=False)


def kvantum_available():
    return any(Path(p).exists() for p in KVANTUM_PLUGINS) or bool(shutil.which("kvantummanager"))


def install():
    for target in TARGETS + CONFIG_TARGETS:
        if not (ROOT / "build" / target).exists():
            raise RuntimeError("Build first; missing " + target)
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        if manifest["data"] != str(DATA) or manifest["config"] != str(CONFIG):
            raise RuntimeError("Installation paths differ from the ownership manifest")
    else:
        collisions = [str(DATA / t) for t in TARGETS if (DATA / t).exists() or (DATA / t).is_symlink()]
        collisions += [str(CONFIG / t) for t in CONFIG_TARGETS if (CONFIG / t).exists() or (CONFIG / t).is_symlink()]
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
        manifest = {"version": 2, "data": str(DATA), "config": str(CONFIG),
                    "targets": list(TARGETS), "config_targets": list(CONFIG_TARGETS),
                    "config_present": present, "applied": False}
        MANIFEST.write_text(json.dumps(manifest, indent=2))
    for target in [t for t in manifest["targets"] if t in LEGACY_TARGETS]:
        remove(DATA / target)
        manifest["targets"].remove(target)
    for target in TARGETS:
        if target not in manifest["targets"]:
            # New in this version: take it over only if nobody else owns it.
            if (DATA / target).exists() or (DATA / target).is_symlink():
                raise RuntimeError("Refusing to overwrite unowned path: " + str(DATA / target))
            manifest["targets"].append(target)
        remove(DATA / target)
        copy(ROOT / "build" / target, DATA / target)
    for target in CONFIG_TARGETS:
        if target not in manifest.setdefault("config_targets", []):
            manifest["config_targets"].append(target)
        remove(CONFIG / target)
        copy(ROOT / "build" / target, CONFIG / target)
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    run("kbuildsycoca6", check=False)
    if shutil.which("fc-cache"):
        run("fc-cache", "-f", str(DATA / "fonts/CDECopper"), check=False)
    print("Installed CDE Copper. Original configuration: " + str(STATE / "config"))


def palette_owned(target, patterns):
    return any(re.fullmatch(p, target) for p in patterns)


def install_palette(manifest, name):
    """Generate and install one CDE palette; drop the previously applied one."""
    for target in manifest.get("palette_targets", []):
        remove(DATA / target)
    for target in manifest.get("palette_config_targets", []):
        remove(CONFIG / target)
    manifest["palette_targets"], manifest["palette_config_targets"] = [], []
    if name == "Copper":
        manifest["palette"] = "Copper"
        return {"colors": "CDECopper", "plasma": "cde-copper", "kvantum": "CDECopper", "desktop": "#086875"}
    sys.path.insert(0, str(ROOT))
    import build
    stage = STATE / "palette-build"
    remove(stage)
    result = build.build_palette(name, stage)
    for target, base in [(t, DATA) for t in result["targets"]] + [(t, CONFIG) for t in result["config_targets"]]:
        if (base / target).exists() or (base / target).is_symlink():
            raise RuntimeError("Refusing to overwrite unowned path: " + str(base / target))
    for target in result["targets"]:
        copy(stage / target, DATA / target)
    for target in result["config_targets"]:
        copy(stage / target, CONFIG / target)
    remove(stage)
    manifest["palette"] = name
    manifest["palette_targets"] = result["targets"]
    manifest["palette_config_targets"] = result["config_targets"]
    return result


def screen_size():
    """The largest screen, in logical pixels, from Plasma; 3840x2160 if unknown."""
    exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
    script = "var w = 0, h = 0; for (var i = 0; i < screenCount; ++i) { var g = screenGeometry(i); w = Math.max(w, g.width); h = Math.max(h, g.height); } print(w + 'x' + h);"
    try:
        out = subprocess.check_output([exe, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script], text=True)
        width, height = (int(v) for v in out.strip().split("x"))
        if width > 0 and height > 0:
            return width, height
    except (subprocess.CalledProcessError, ValueError, TypeError, OSError):
        pass
    return 3840, 2160


def set_backdrop(manifest, name, scale):
    """Tile one CDE backdrop, coloured with the applied palette; "none" goes
    back to the plain desktop colour of the palette."""
    sys.path.insert(0, str(ROOT))
    import backdrops
    import palettes
    chosen = manifest.get("palette", "Copper")
    colour_set = palettes.copper_desktop() if chosen == "Copper" else palettes.load(chosen)[2]
    folder = DATA / "wallpapers/CDEBackdrops"
    remove(folder)
    backdrops.write_all(colour_set, folder, scale)
    manifest["backdrop"], manifest["backdrop_scale"] = name, scale
    if name == "none":
        script = ("for (var d of desktops()) { d.wallpaperPlugin = 'org.kde.color';"
                  " d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];"
                  f" d.writeConfig('Color', '{colour_set['bg']}'); }}")
    else:
        if name not in backdrops.names():
            raise RuntimeError(f"Unknown backdrop {name!r}; available: {', '.join(backdrops.names())}")
        width, height = screen_size()
        picture = folder / f"desktop-{name}-{chosen}-{width}x{height}@{scale}.png"
        picture.write_bytes(backdrops.desktop(name, backdrops.colours_for(colour_set), width, height, scale))
        # FillMode 6: centred, unscaled; the picture already fills the screen.
        script = ("for (var d of desktops()) { d.wallpaperPlugin = 'org.kde.image';"
                  " d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];"
                  f" d.writeConfig('Image', '{picture.as_uri()}'); d.writeConfig('FillMode', 6);"
                  f" d.writeConfig('Color', '{colour_set['bg']}'); }}")
    dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script)


def apply(panel=False, palette=None, backdrop=None, backdrop_scale=None):
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before applying it")
    manifest = json.loads(MANIFEST.read_text())
    manifest["applied"] = True
    chosen = palette or manifest.get("palette", "Copper")
    theme = install_palette(manifest, chosen)
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    run("plasma-apply-lookandfeel", "--apply", "org.cde.copper.desktop")
    run("plasma-apply-colorscheme", theme["colors"])
    run("plasma-apply-desktoptheme", theme["plasma"])
    # The Motif controls are a Kvantum theme; without the Kvantum style
    # plugin the built-in Qt Windows style is the nearest bevelled fallback.
    if kvantum_available():
        write_config("Kvantum/kvantum.kvconfig", "General", {"theme": theme["kvantum"]})
        style = "kvantum"
    else:
        style = "Windows"
        print("Kvantum style plugin not found; using the Qt Windows style. Install 'kvantum' for the Motif controls.")
    write_config("kdeglobals", "KDE", {"widgetStyle": style, "LookAndFeelPackage": "org.cde.copper.desktop"})
    write_config("kdeglobals", "Icons", {"Theme": "CDECopper"})
    write_config("kdeglobals", "General", {"font": UI_FONT, "fixed": MONO_FONT, "menuFont": UI_FONT, "toolBarFont": UI_FONT})
    write_config("kdeglobals", "WM", {"activeFont": TITLE_FONT})
    write_config("kwinrc", "org.kde.kdecoration2", {"library": "org.kde.kwin.aurorae", "theme": DECORATION, "ButtonsOnLeft": "M", "ButtonsOnRight": "IAX", "BorderSize": "Normal"})
    write_config("kwinrc", "WM", {"activeFont": TITLE_FONT})
    write_config("kwinrc", "Plugins", {"cde-copper-arrangeEnabled": "true"})
    write_config("konsolerc", "Desktop Entry", {"DefaultProfile": "CDE Copper.profile"})
    dbus("org.kde.KWin", "/KWin", "reconfigure")
    dbus("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.start")
    # CDE recolours the backdrop with the palette. The desktop is touched
    # only when a palette or backdrop is asked for, or one was set before.
    if backdrop or palette or manifest.get("backdrop"):
        set_backdrop(manifest, backdrop or manifest.get("backdrop") or "none",
                     backdrop_scale or manifest.get("backdrop_scale", 1))
        MANIFEST.write_text(json.dumps(manifest, indent=2))
    if panel:
        # KWin exposes workspace creation through D-Bus; no session restart required.
        exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
        count = int(subprocess.check_output([exe, "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.count"], text=True).strip())
        for i in range(count, 4):
            dbus("org.kde.KWin", "/VirtualDesktopManager", "createDesktop", str(i), ("One", "Two", "Three", "Four")[i])
        dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", (ROOT / "layout.js").read_text())
    print(f"Applied with palette {chosen}. Log out and back in to reload all application styles and the decoration.")


def list_palettes():
    sys.path.insert(0, str(ROOT))
    import palettes
    import backdrops
    print("Palettes:  Copper (default), " + ", ".join(palettes.names()))
    print("Backdrops: none, " + ", ".join(backdrops.names()))


def uninstall():
    if not MANIFEST.exists():
        raise RuntimeError("No CDE Copper ownership manifest found")
    manifest = json.loads(MANIFEST.read_text())
    if manifest["data"] != str(DATA) or manifest["config"] != str(CONFIG):
        raise RuntimeError("Installation paths differ from the manifest")
    if any(target not in TARGETS + LEGACY_TARGETS for target in manifest["targets"]):
        raise RuntimeError("Unexpected target in ownership manifest")
    if any(not palette_owned(t, PALETTE_PATTERNS) for t in manifest.get("palette_targets", [])) or \
       any(not palette_owned(t, PALETTE_CONFIG_PATTERNS) for t in manifest.get("palette_config_targets", [])):
        raise RuntimeError("Unexpected palette target in ownership manifest")
    if any(target not in CONFIG_TARGETS for target in manifest.get("config_targets", [])):
        raise RuntimeError("Unexpected config target in ownership manifest")
    if manifest["applied"]:
        run("systemctl", "--user", "stop", "plasma-plasmashell.service")
        for file in CONFIG_FILES:
            remove(CONFIG / file)
            if file in manifest["config_present"]:
                copy(STATE / "config" / file, CONFIG / file)
    for target in manifest["targets"]:
        remove(DATA / target)
    for target in manifest.get("config_targets", []):
        remove(CONFIG / target)
    for target in manifest.get("palette_targets", []):
        remove(DATA / target)
    for target in manifest.get("palette_config_targets", []):
        remove(CONFIG / target)
    for cache in (HOME / ".cache").glob("plasma_theme_cde-*"):
        remove(cache)
    if manifest["applied"]:
        dbus("org.kde.KWin", "/KWin", "reconfigure")
        run("systemctl", "--user", "start", "plasma-plasmashell.service")
    MANIFEST.rename(STATE / "uninstalled-manifest.json")
    print("Removed only manifest-owned files and restored pre-install configuration. Backup retained at " + str(STATE))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "apply", "uninstall", "palettes"))
    parser.add_argument("--palette", help="CDE palette to apply (see the 'palettes' action); Copper is the default")
    parser.add_argument("--backdrop", help="CDE backdrop to tile on the desktop (see 'palettes'), or 'none'")
    parser.add_argument("--backdrop-scale", type=int, choices=(1, 2, 3), help="pixel size of the backdrop tiles, e.g. 2 for 200 %% displays")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--panel", action="store_true", help="replace the panel layout, backed up on installation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.action == "palettes":
        list_palettes()
        return
    if args.palette and args.palette != "Copper":
        sys.path.insert(0, str(ROOT))
        import palettes
        if args.palette not in palettes.names():
            raise RuntimeError(f"Unknown palette {args.palette!r}; run: python3 manage.py palettes")
    if args.dry_run:
        print("\n".join([str(DATA / t) for t in TARGETS] + [str(CONFIG / t) for t in CONFIG_TARGETS]))
        return
    if os.geteuid() == 0:
        raise RuntimeError("Run as the desktop user, not root")
    if args.action == "install":
        install()
        if args.apply:
            apply(args.panel, args.palette, args.backdrop, args.backdrop_scale)
    elif args.action == "apply":
        apply(args.panel, args.palette, args.backdrop, args.backdrop_scale)
    else:
        uninstall()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
