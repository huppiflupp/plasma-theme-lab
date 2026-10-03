#!/usr/bin/env python3
"""User-profile installation with an explicit ownership and rollback manifest."""
import argparse
import configparser
import fcntl
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
sys.path.insert(0, str(ROOT))
import palettes  # noqa: E402  (ships beside this file, also in the tool copy)

# Every CDE palette is installed as a colour scheme, so System Settings lists
# them; the rest of a palette is generated when it is applied.
SCHEMES = tuple(f"color-schemes/CDE{name}.colors" for name in palettes.names())
TOOL = "cde-copper"
TARGETS = ("color-schemes/CDECopper.colors", "kwin/decorations/" + DECORATION, "kwin/scripts/cde-copper-arrange",
           "plasma/desktoptheme/cde-copper", "plasma/look-and-feel/org.cde.copper.desktop",
           "plasma/plasmoids/org.cde.copper.frontpanel", "icons/CDECopper",
           "wallpapers/org.cde.copper", "plasma/wallpapers/org.cde.copper.backdrop",
           "konsole/CDECopper.colorscheme", "konsole/CDE Copper.profile",
           "fonts/CDECopper", TOOL) + SCHEMES
# The tool copy: what applying a palette needs, so the console and System
# Settings can switch palettes without the extracted archive.
TOOL_SOURCES = ("manage.py", "build.py", "palettes.py", "backdrops.py", "kvantum.py", "icons.py",
                "layout.js", "tools", "palettes", "backdrops")
# Owned by older installations and removed when they are upgraded.
LEGACY_TARGETS = ("aurorae/themes/CDECopper", "wallpapers/CDEBackdrops", "wallpapers/org.cde.copper.backdrop")
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


def install_tool():
    """Copy the palette tool into the profile; generated backdrops stay."""
    tool = DATA / TOOL / "tool"
    if tool.resolve() == ROOT.resolve():
        return   # running from the copy itself
    remove(tool)
    tool.mkdir(parents=True)
    for item in TOOL_SOURCES:
        source = ROOT / item
        if source.is_dir():
            shutil.copytree(source, tool / item, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, tool / item)
    # Copper's tiles until a palette is applied (previews, CDE Backdrop).
    tiles = DATA / TOOL / "backdrops"
    if not tiles.exists():
        import backdrops
        backdrops.write_all(palettes.copper_desktop(), tiles / "Copper")


def install():
    for target in TARGETS + CONFIG_TARGETS:
        if target != TOOL and not (ROOT / "build" / target).exists():
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
            # A colour scheme generated by 0.2 for an applied palette is ours.
            if target in manifest.get("palette_targets", []):
                manifest["palette_targets"].remove(target)
            elif (DATA / target).exists() or (DATA / target).is_symlink():
                raise RuntimeError("Refusing to overwrite unowned path: " + str(DATA / target))
            manifest["targets"].append(target)
        if target == TOOL:
            install_tool()
            continue
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
        if target not in TARGETS:   # 0.2 listed the colour scheme here
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


def plasma_script(script):
    dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script)


def current_scheme():
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(CONFIG / "kdeglobals")
    return config.get("General", "ColorScheme", fallback="")


def workspace_set(name):
    """The palette's workspace colour set (CDE set 3): the desktop colours."""
    return palettes.copper_desktop() if name == "Copper" else palettes.load(name)[2]


def set_palette(manifest, name):
    """Switch everything to one palette: colour scheme, Plasma surfaces,
    Kvantum controls, and the backdrop tiles and desktop colour."""
    import backdrops
    theme = install_palette(manifest, name)
    if current_scheme() != theme["colors"]:
        run("plasma-apply-colorscheme", theme["colors"])
    run("plasma-apply-desktoptheme", theme["plasma"])
    if kvantum_available():
        write_config("Kvantum/kvantum.kvconfig", "General", {"theme": theme["kvantum"]})
    colour_set = workspace_set(name)
    # Tiles for the "CDE Backdrop" wallpaper type, in this palette's colours.
    folder = DATA / TOOL / "backdrops"
    remove(folder)
    backdrops.write_all(colour_set, folder / name)
    # Desktops showing a backdrop follow the palette; a plain desktop colour
    # follows it only when the theme set it (apply.sh --backdrop none).
    plain = "if (d.wallpaperPlugin === 'org.kde.color') { d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General']; d.writeConfig('Color', '%s'); }" % colour_set["bg"]
    plasma_script("for (var d of desktops()) { if (d.wallpaperPlugin === 'org.cde.copper.backdrop') {"
                  " d.currentConfigGroup = ['Wallpaper', 'org.cde.copper.backdrop', 'General'];"
                  f" d.writeConfig('Palette', '{name}'); d.writeConfig('Color', '{colour_set['bg']}'); }}"
                  + (" else " + plain if manifest.get("backdrop") == "none" else "") + " }")
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    return theme


def set_backdrop(manifest, name, scale):
    """Show one CDE backdrop through the "CDE Backdrop" wallpaper type, or
    with "none" the plain desktop colour of the palette."""
    import backdrops
    chosen = manifest.get("palette", "Copper")
    colour_set = workspace_set(chosen)
    manifest["backdrop"], manifest["backdrop_scale"] = name, scale
    if name == "none":
        plasma_script("for (var d of desktops()) { d.wallpaperPlugin = 'org.kde.color';"
                      " d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];"
                      f" d.writeConfig('Color', '{colour_set['bg']}'); }}")
    else:
        if name not in backdrops.names():
            raise RuntimeError(f"Unknown backdrop {name!r}; available: {', '.join(backdrops.names())}")
        plasma_script("for (var d of desktops()) { d.wallpaperPlugin = 'org.cde.copper.backdrop';"
                      " d.currentConfigGroup = ['Wallpaper', 'org.cde.copper.backdrop', 'General'];"
                      f" d.writeConfig('Backdrop', '{name}'); d.writeConfig('Palette', '{chosen}');"
                      f" d.writeConfig('PixelSize', {int(scale)}); d.writeConfig('Color', '{colour_set['bg']}'); }}")
    MANIFEST.write_text(json.dumps(manifest, indent=2))


def palette_action(name=None, backdrop=None, scale=None, follow=False, notify=False):
    """Switch palette (and backdrop) of an applied installation; with follow,
    take the palette from the colour scheme chosen in System Settings."""
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before choosing a palette")
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "lock", "w") as lock:
        # Two consoles (two screens) may ask at the same moment.
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = json.loads(MANIFEST.read_text())
        if follow:
            scheme = current_scheme()
            match = re.fullmatch(r"CDE([A-Za-z]+)", scheme)
            name = match.group(1) if match else None
            if name not in ("Copper", *palettes.names()):
                return
        # Only an explicit or a changed palette is applied; a backdrop alone
        # keeps the palette as it is.
        if name and (not follow or name != manifest.get("palette", "Copper")):
            set_palette(manifest, name)
            if notify and shutil.which("notify-send"):
                run("notify-send", "-a", "CDE Front Console", "-i", "preferences-desktop-color",
                    f"Palette {name}", "Restart applications to bring their controls into the new colours.", check=False)
        if backdrop:
            set_backdrop(manifest, backdrop, scale or manifest.get("backdrop_scale", 1))


def apply(panel=False, palette=None, backdrop=None, backdrop_scale=None):
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before applying it")
    manifest = json.loads(MANIFEST.read_text())
    manifest["applied"] = True
    chosen = palette or manifest.get("palette", "Copper")
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    run("plasma-apply-lookandfeel", "--apply", "org.cde.copper.desktop")
    set_palette(manifest, chosen)
    # The Motif controls are a Kvantum theme; without the Kvantum style
    # plugin the built-in Qt Windows style is the nearest bevelled fallback.
    if kvantum_available():
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
    if backdrop:
        set_backdrop(manifest, backdrop, backdrop_scale or manifest.get("backdrop_scale", 1))
    if panel:
        # KWin exposes workspace creation through D-Bus; no session restart required.
        exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
        count = int(subprocess.check_output([exe, "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.count"], text=True).strip())
        for i in range(count, 4):
            dbus("org.kde.KWin", "/VirtualDesktopManager", "createDesktop", str(i), ("One", "Two", "Three", "Four")[i])
        dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", (ROOT / "layout.js").read_text())
    print(f"Applied with palette {chosen}. Log out and back in to reload all application styles and the decoration.")


def list_palettes():
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
    parser.add_argument("action", choices=("install", "apply", "uninstall", "palettes", "palette"))
    parser.add_argument("--palette", help="CDE palette to apply (see the 'palettes' action); Copper is the default")
    parser.add_argument("--backdrop", help="CDE backdrop to tile on the desktop (see 'palettes'), or 'none'")
    parser.add_argument("--follow-scheme", action="store_true", help="palette: take the palette from the colour scheme in System Settings")
    parser.add_argument("--notify", action="store_true", help="palette: report the switch as a desktop notification")
    parser.add_argument("--backdrop-scale", type=int, choices=(1, 2, 3), help="pixel size of the backdrop tiles, e.g. 2 for 200 %% displays")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--panel", action="store_true", help="replace the panel layout, backed up on installation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.action == "palettes":
        list_palettes()
        return
    if args.palette and args.palette != "Copper":
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
    elif args.action == "palette":
        palette_action(args.palette, args.backdrop, args.backdrop_scale, args.follow_scheme, args.notify)
    else:
        uninstall()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
