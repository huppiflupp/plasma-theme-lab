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
                "konsolerc", "auroraerc", "plasma-org.kde.plasma.desktop-appletsrc", "kdedefaults",
                "Kvantum/kvantum.kvconfig")
# Owned paths below XDG_CONFIG_HOME: the Kvantum widget style lives there.
CONFIG_TARGETS = ("Kvantum/CDECopper",)
KVANTUM_PLUGINS = ("/usr/lib64/qt6/plugins/styles/libkvantum.so",
                   "/usr/lib/x86_64-linux-gnu/qt6/plugins/styles/libkvantum.so",
                   "/usr/lib/qt6/plugins/styles/libkvantum.so")
DECORATION = "kwin4_decoration_qml_cdecopper"
sys.path.insert(0, str(ROOT))
import palettes  # noqa: E402  (ships beside this file, also in the tool copy)
from build import PICTURES  # noqa: E402  (build.py is part of the tool copy too)

# Every CDE palette is installed as a colour scheme, so System Settings lists
# them; the rest of a palette is generated when it is applied.
SCHEMES = tuple(f"color-schemes/CDE{name}.colors" for name in palettes.names())
TOOL = "cde-copper"
LANGUAGES = ("de",)        # po/<language>.po, compiled by build.py
TARGETS = ("color-schemes/CDECopper.colors", "kwin/decorations/" + DECORATION, "kwin/scripts/cde-copper-arrange",
           "kwin/tabbox/org.cde.copper.switcher",
           "plasma/desktoptheme/cde-copper", "plasma/look-and-feel/org.cde.copper.desktop",
           "plasma/look-and-feel/org.cde.copper.night",
           "plasma/plasmoids/org.cde.copper.frontpanel", "icons/CDECopper",
           "wallpapers/org.cde.copper", "plasma/wallpapers/org.cde.copper.backdrop",
           *(f"wallpapers/org.cde.copper.{key}" for key, _, _ in PICTURES),
           "konsole/CDECopper.colorscheme", "konsole/CDE Copper.profile",
           "kstyle/themes/kvantum.themerc", "kstyle/themes/kvantum-dark.themerc", "icons/CDECopperCursors",
           "plasma/shells/org.cde.copper.shell", "themes/CDECopper",
           # The translations (domain cde-copper); fixed, as the tool copy has no po/.
           *(f"locale/{lang}/LC_MESSAGES/cde-copper.mo" for lang in LANGUAGES),
           "fonts/CDECopper", TOOL) + SCHEMES
# The tool copy: what applying a palette needs, so the console and System
# Settings can switch palettes without the extracted archive.
TOOL_SOURCES = ("manage.py", "build.py", "palettes.py", "backdrops.py", "kvantum.py", "icons.py", "cursors.py", "gtktheme.py",
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
    # These command-line Qt tools need no window. Avoid Qt's fatal display
    # connection path, including stale DISPLAY values inherited at login.
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    try:
        return subprocess.run(args, check=check, text=True, env=env, timeout=30)
    except FileNotFoundError:
        if check:
            raise RuntimeError("Required program not found: " + str(args[0]))
        return None


def session_ready():
    """Do not auto-start a bus or run apply tools before Plasma is ready."""
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) or not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        return False
    exe = shutil.which("dbus-send")
    if not exe:
        return False
    try:
        for service in ("org.kde.KWin", "org.kde.plasmashell"):
            result = subprocess.run([exe, "--session", "--print-reply", "--reply-timeout=2000",
                                     "--dest=org.freedesktop.DBus", "/org/freedesktop/DBus",
                                     "org.freedesktop.DBus.NameHasOwner", "string:" + service],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode or "boolean true" not in result.stdout:
                return False
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def save_manifest(manifest):
    pending = MANIFEST.with_suffix(".tmp")
    pending.write_text(json.dumps(manifest, indent=2))
    pending.replace(MANIFEST)


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
        backdrops.write_tiles(palettes.copper_desktop(), tiles / "Copper", material_tiles())
    # Tiles from before 0.8.12 have no "current" link: the one palette there.
    current = tiles / "current"
    if not current.exists():
        remove(current)
        folders = sorted(f.name for f in tiles.iterdir() if f.is_dir() and not f.is_symlink())
        if folders:
            current.symlink_to(folders[0])


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
                    "config_present": present, "config_files": list(CONFIG_FILES), "applied": False}
        save_manifest(manifest)
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
        save_manifest(manifest)
        if target == TOOL:
            install_tool()
            continue
        remove(DATA / target)
        copy(ROOT / "build" / target, DATA / target)
    for target in CONFIG_TARGETS:
        if target not in manifest.setdefault("config_targets", []):
            if (CONFIG / target).exists() or (CONFIG / target).is_symlink():
                raise RuntimeError("Refusing to overwrite unowned path: " + str(CONFIG / target))
            manifest["config_targets"].append(target)
        save_manifest(manifest)
        remove(CONFIG / target)
        copy(ROOT / "build" / target, CONFIG / target)
    save_manifest(manifest)
    # The copy from build/ has copper cursors and outlined progress bars;
    # keep the chosen ones.
    if cursor_edge(manifest) != CURSOR_COLOURS["copper"]:
        install_cursors(manifest)
    if manifest.get("palette", "Copper") != "Copper":
        update_splash(manifest["palette"])
    if manifest.get("palette", "Copper") == "Copper" and manifest.get("progress", "outlined") != "outlined":
        copper_kvantum(manifest["progress"])
    run("kbuildsycoca6", check=False)
    if shutil.which("fc-cache"):
        run("fc-cache", "-f", str(DATA / "fonts/CDECopper"), check=False)
    # Desktops whose backdrop settings still name an older palette (saved by
    # a settings dialog opened before a palette change) get the one applied.
    if manifest.get("applied") and run("systemctl", "--user", "-q", "is-active", "plasma-plasmashell.service", check=False).returncode == 0:
        sync_desktops(manifest, manifest.get("palette", "Copper"), check=False)
    print("Installed CDE Copper. Original configuration: " + str(STATE / "config"))


def offer_shell_restart(restart):
    """A running plasmashell keeps the front panel's old code and settings
    schema; new settings would not even be saved until it restarts. Asked
    only at a terminal, so scripts and tests never restart the session."""
    if run("systemctl", "--user", "-q", "is-active", "plasma-plasmashell.service", check=False).returncode:
        return
    if not restart and sys.stdin.isatty():
        try:
            restart = input("Restart Plasma now to load the new front panel? [y/N] ").strip().lower() in ("y", "yes", "j", "ja")
        except EOFError:
            pass
    if restart:
        run("systemctl", "--user", "restart", "plasma-plasmashell.service")
        print("Plasma restarted.")
    else:
        print("Restart Plasma to load the new front panel: systemctl --user restart plasma-plasmashell")


def palette_owned(target, patterns):
    return any(re.fullmatch(p, target) for p in patterns)


def copper_kvantum(progress):
    """Copper's Kvantum theme is installed from build/ (outlined progress
    bars); another progress style regenerates it in place (it is ours)."""
    sys.path.insert(0, str(ROOT))
    import build
    from kvantum import build_kvantum
    stage = STATE / "palette-build"
    remove(stage)
    build_kvantum(stage, build.P, progress=progress)
    remove(CONFIG / "Kvantum/CDECopper")
    copy(stage / "Kvantum/CDECopper", CONFIG / "Kvantum/CDECopper")
    remove(stage)


CURSOR_COLOURS = {"copper": "#e8874f", "white": "#ffffff"}


def cursor_edge(manifest):
    """The rim colour of the cursors: copper, white, the palette's accent
    (its active title colour, as the controls use it) or #rrggbb."""
    choice = manifest.get("cursor", "copper")
    if choice == "palette":
        name = manifest.get("palette", "Copper")
        return CURSOR_COLOURS["copper"] if name == "Copper" else palettes.theme(name)["kopf_aktiv"]
    if re.fullmatch(r"#[0-9a-fA-F]{6}", choice):
        return choice.lower()
    return CURSOR_COLOURS.get(choice, CURSOR_COLOURS["copper"])


def cursor_tool():
    """plasma-apply-cursortheme, when it can run: it needs an X display (it
    also tells XWayland) and aborts without one, as from a shell over ssh,
    which Plasma reports as a crash. Without it the cursor written to
    kcminputrc takes effect at the next login."""
    return bool(os.environ.get("DISPLAY")) and shutil.which("plasma-apply-cursortheme") is not None


def install_cursors(manifest):
    """Rebuild the cursor theme (ours) with the chosen rim colour and make
    Plasma load it again: the same name alone would keep the cached images."""
    sys.path.insert(0, str(ROOT))
    from cursors import build_cursors
    stage = STATE / "cursor-build"
    remove(stage)
    build_cursors(stage, edge=cursor_edge(manifest))
    remove(DATA / "icons/CDECopperCursors")
    copy(stage / "icons/CDECopperCursors", DATA / "icons/CDECopperCursors")
    remove(stage)
    if read_config("kcminputrc", "Mouse", "cursorTheme") == "CDECopperCursors" and cursor_tool():
        run("plasma-apply-cursortheme", "breeze_cursors", check=False)
        run("plasma-apply-cursortheme", "CDECopperCursors", check=False)


def install_palette(manifest, name):
    """Generate and install one CDE palette; drop the previously applied one."""
    for target in manifest.get("palette_targets", []):
        if target not in TARGETS:   # 0.2 listed the colour scheme here
            remove(DATA / target)
    for target in manifest.get("palette_config_targets", []):
        remove(CONFIG / target)
    manifest["palette_targets"], manifest["palette_config_targets"] = [], []
    progress = manifest.get("progress", "outlined")
    if name == "Copper":
        manifest["palette"] = "Copper"
        if progress != "outlined" or (CONFIG / "Kvantum/CDECopper").exists():
            copper_kvantum(progress)
        return {"colors": "CDECopper", "plasma": "cde-copper", "kvantum": "CDECopper", "desktop": "#086875"}
    sys.path.insert(0, str(ROOT))
    import build
    stage = STATE / "palette-build"
    remove(stage)
    result = build.build_palette(name, stage, progress=progress)
    for target, base in [(t, DATA) for t in result["targets"]] + [(t, CONFIG) for t in result["config_targets"]]:
        if (base / target).exists() or (base / target).is_symlink():
            raise RuntimeError("Refusing to overwrite unowned path: " + str(base / target))
    # Record every generated path before copying: a failed copy must still
    # be recoverable by uninstall or a repeated palette request.
    manifest["palette"] = name
    manifest["palette_targets"] = result["targets"]
    manifest["palette_config_targets"] = result["config_targets"]
    save_manifest(manifest)
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
    """The colour scheme in effect. A global theme writes its choices to the
    defaults layer (kdedefaults/kdeglobals) and removes them from kdeglobals,
    so a scheme set by switching the global theme is only found there."""
    for path in (CONFIG / "kdeglobals", CONFIG / "kdedefaults/kdeglobals"):
        config = configparser.ConfigParser(interpolation=None, strict=False)
        config.optionxform = str
        config.read(path)
        scheme = config.get("General", "ColorScheme", fallback="")
        if scheme:
            return scheme
    return ""


def workspace_set(name):
    """The palette's workspace colour set (CDE set 3): the desktop colours."""
    return palettes.copper_desktop() if name == "Copper" else palettes.load(name)[2]


def read_config(file, section, key):
    """A value in effect: the user's file, else the defaults layer."""
    for path in (CONFIG / file, CONFIG / "kdedefaults" / file):
        config = configparser.ConfigParser(interpolation=None, strict=False)
        config.optionxform = str
        config.read(path)
        value = config.get(section, key, fallback="")
        if value:
            return value
    return ""


def notify_change(kind):
    """KDE's change broadcast: 0 palette, 2 style (KGlobalSettings)."""
    if shutil.which("dbus-send"):
        run("dbus-send", "--session", "--type=signal", "/KGlobalSettings",
            "org.kde.KGlobalSettings.notifyChange", f"int32:{kind}", "int32:0", check=False)
    elif shutil.which("gdbus"):
        run("gdbus", "emit", "--session", "--object-path", "/KGlobalSettings",
            "--signal", "org.kde.KGlobalSettings.notifyChange", str(kind), "0", check=False)


def update_icons(name):
    """The icon set in the palette's colours (icons.recolour), drawn afresh
    from icons.py: Copper's as built, any other recoloured. Swapped in whole,
    then running programs are told to reload their icons."""
    sys.path.insert(0, str(ROOT))
    import build
    from icons import build_icons, recolour
    target = DATA / "icons/CDECopper"
    if not target.exists():
        return
    stage = STATE / "icon-build"
    remove(stage)
    build_icons(stage)
    if name != "Copper":
        recolour(stage / "icons/CDECopper", palettes.theme(name))
    old = target.with_name("CDECopper.old")
    remove(old)
    target.rename(old)
    (stage / "icons/CDECopper").rename(target)
    remove(old)
    remove(stage)
    remove(HOME / ".cache/icon-cache.kcache")
    if shutil.which("dbus-send"):
        run("dbus-send", "--session", "--type=signal", "/KIconLoader",
            "org.kde.KIconLoader.iconChanged", "int32:0", check=False)


def refresh_running_windows():
    """Bring windows that are already open into the new palette.

    Kvantum has no reload: a running program keeps its style object until the
    style *name* changes (plasma-integration's KHintsSettings only calls
    QApplication::setStyle for a different name). A short detour through
    Fusion makes KDE programs create a fresh Kvantum style with the new
    theme. KWin keeps the colours of existing window frames; switching the
    decoration away and back makes it build them anew. Programs without
    KDE's platform theme still need a restart."""
    if read_config("kdeglobals", "KDE", "widgetStyle") == "kvantum":
        write_config("kdeglobals", "KDE", {"widgetStyle": "fusion"})
        notify_change(2)
        time.sleep(1)
        write_config("kdeglobals", "KDE", {"widgetStyle": "kvantum"})
        notify_change(2)
        time.sleep(1)
        notify_change(0)
    if read_config("kwinrc", "org.kde.kdecoration2", "theme") == DECORATION:
        write_config("kwinrc", "org.kde.kdecoration2", {"library": "org.kde.breeze"})
        try:
            dbus("org.kde.KWin", "/KWin", "reconfigure")
            time.sleep(0.5)
        finally:
            write_config("kwinrc", "org.kde.kdecoration2", {"library": "org.kde.kwin.aurorae"})
        dbus("org.kde.KWin", "/KWin", "reconfigure")


def sync_desktops(manifest, name, check=True):
    """Desktops showing a backdrop follow the palette; a plain desktop colour
    follows it only when the theme set it: --backdrop none, or the colour
    is a palette's desktop colour (the global theme's layout sets Copper's)."""
    colour_set = workspace_set(name)
    ours = sorted({workspace_set(p)["bg"].lower() for p in ("Copper", *palettes.names())})
    always = "true" if manifest.get("backdrop") == "none" else "false"
    plain = ("if (d.wallpaperPlugin === 'org.kde.color') { d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];"
             f" if ({always} || {json.dumps(ours)}.indexOf(String(d.readConfig('Color')).toLowerCase()) >= 0)"
             f" d.writeConfig('Color', '{colour_set['bg']}'); }}")
    # The palette (and its colour behind the pattern) goes to every desktop's
    # backdrop settings, also where another wallpaper type is shown now:
    # switched back, it would otherwise look for an older palette's tiles,
    # which are gone.
    script = ("for (var d of desktops()) { var shown = d.wallpaperPlugin;"
                " d.currentConfigGroup = ['Wallpaper', 'org.cde.copper.backdrop', 'General'];"
                f" d.writeConfig('Palette', '{name}'); d.writeConfig('Color', '{colour_set['bg']}');"
                f" d.writeConfig('Revision', '{int(time.time() * 1000)}');"
                " if (shown !== 'org.cde.copper.backdrop') { " + plain + " } }")
    if check:
        plasma_script(script)
    else:
        exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or "/usr/lib/qt6/bin/qdbus"
        run(exe, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script, check=False)


def pattern_set(manifest, name, colour_set):
    """The colours CDE's two-colour patterns are drawn in: the workspace set,
    white (or black) on the desktop colour as in CDE. With the option
    "palette" a dark palette draws them in its most colourful light colour
    instead of white, Amber's amber on its dark brown."""
    if manifest.get("pattern_colour") != "palette" or palettes.readable(colour_set["bg"]) != "#ffffff":
        return colour_set
    try:
        candidates = [s["bg"] for s in palettes.load(name)]
    except KeyError:
        candidates = [palettes.copper_desktop()["ts"]]
    def colourful(c):
        r, g, b = (int(c[i:i+2], 16) / 255 for i in (1, 3, 5))
        high, low = max(r, g, b), min(r, g, b)
        return (high - low) * high
    legible = [c for c in candidates if palettes.contrast(c, colour_set["bg"]) >= 3]
    if not legible:
        return colour_set
    return {**colour_set, "fg": max(legible, key=colourful)}


def set_palette(manifest, name):
    """Switch everything to one palette: colour scheme, Plasma surfaces,
    Kvantum controls, and the backdrop tiles and desktop colour."""
    import backdrops
    # The console colours its workspace buttons from this; written before
    # the scheme changes, so the console finds it when it repaints.
    (DATA / TOOL).mkdir(parents=True, exist_ok=True)
    (DATA / TOOL / "workspaces.json").write_text(json.dumps(palettes.workspace_colours(name)))
    theme = install_palette(manifest, name)
    if manifest.get("cursor") == "palette":
        install_cursors(manifest)
    if current_scheme() != theme["colors"]:
        run("plasma-apply-colorscheme", theme["colors"])
    run("plasma-apply-desktoptheme", theme["plasma"])
    if kvantum_available():
        write_config("Kvantum/kvantum.kvconfig", "General", {"theme": theme["kvantum"]})
    colour_set = workspace_set(name)
    # Tiles for the "CDE Backdrop" wallpaper type, in this palette's colours.
    folder = DATA / TOOL / "backdrops"
    remove(folder)
    backdrops.write_all(pattern_set(manifest, name, colour_set), folder / name)
    backdrops.write_tiles(colour_set, folder / name, material_tiles())
    # The palette's folder under a fixed name too: a desktop that still names
    # an older palette (its wallpaper settings were saved elsewhere) finds
    # tiles there instead of none.
    (folder / "current").symlink_to(name)
    sync_desktops(manifest, name)
    integrate_xfile()
    update_splash(name)
    update_icons(name)
    update_gtk(name)
    save_manifest(manifest)
    return theme


XFILE_MARK = "! Written by CDE Copper; delete this line to keep your own settings."
XFILE_RESOURCES = HOME / "XFile"       # Xt's per-user app-defaults ($HOME/%N)
XFILE_DESKTOP = DATA / "applications" / "cde-copper-xfile.desktop"


def kde_colour(group, key):
    """A colour of the applied scheme as #rrggbb."""
    value = read_config("kdeglobals", f"Colors:{group}", key)
    parts = [int(part) for part in value.split(",")[:3]] if value else [0, 0, 0]
    return "#%02x%02x%02x" % tuple(parts)


def integrate_xfile():
    """XFile, the Motif file manager closest to CDE's dtfile, in the palette:
    Motif shades its bevels from the background like CDE did, so the scheme's
    window, view and selection colours are all it needs. Its X resources go
    to ~/XFile unless the user keeps an own file there. A menu entry is added
    when the installation brought none (XFile ships without one)."""
    if not shutil.which("xfile"):
        return
    if XFILE_RESOURCES.exists() and XFILE_MARK not in XFILE_RESOURCES.read_text(errors="replace"):
        print(f"{XFILE_RESOURCES} is your own; XFile keeps its colours")
    else:
        terminal = read_config("kdeglobals", "General", "TerminalApplication") or "konsole"
        XFILE_RESOURCES.write_text("\n".join([
            XFILE_MARK,
            f"! Palette {current_scheme()}, renewed with every palette change.",
            f"XFile*background: {kde_colour('Window', 'BackgroundNormal')}",
            f"XFile*foreground: {kde_colour('Window', 'ForegroundNormal')}",
            f"XFile*XmTextField.background: {kde_colour('View', 'BackgroundNormal')}",
            f"XFile*XmTextField.foreground: {kde_colour('View', 'ForegroundNormal')}",
            f"*FileList.background: {kde_colour('View', 'BackgroundNormal')}",
            f"*FileList.foreground: {kde_colour('View', 'ForegroundNormal')}",
            f"*FileList.selectColor: {kde_colour('Selection', 'BackgroundNormal')}",
            "XFile*renderTable: ui",
            "XFile*renderTable.ui.fontType: FONT_IS_XFT",
            "XFile*renderTable.ui.fontName: IBM Plex Sans Condensed",
            "XFile*renderTable.ui.fontSize: 10",
            *(f"*FileList.renderTable.{kind}.fontName: IBM Plex Sans Condensed"
              for kind in ("regular", "directory", "symlink", "special")),
            f"XFile.tools.terminal: {terminal}",
            f"XFile.variable.terminal: {terminal} -e",
            # The desktop's own choices (Default Applications) open files.
            *(f"XFile.variable.{name}: xdg-open" for name in
              ("textEditor", "imageViewer", "imageEditor", "audioPlayer", "videoPlayer", "pdfViewer", "webBrowser")),
            ""]))
    system = [Path(d) / "applications" for d in
              os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")]
    if not any((folder / "xfile.desktop").exists() for folder in system):
        XFILE_DESKTOP.parent.mkdir(parents=True, exist_ok=True)
        if XFILE_DESKTOP.exists() and "X-CDE-Copper=true" not in XFILE_DESKTOP.read_text(errors="replace"):
            return
        XFILE_DESKTOP.write_text("""[Desktop Entry]
Type=Application
Name=XFile
GenericName=File Manager
Comment=Motif file manager, in the CDE palette
Exec=xfile %f
Icon=system-file-manager
Terminal=false
Categories=System;FileTools;FileManager;
MimeType=inode/directory;
# Choosable as the file manager, never the default by itself (Dolphin has 10).
InitialPreference=1
X-CDE-Copper=true
""")


def remove_xfile_integration():
    if XFILE_RESOURCES.exists() and XFILE_MARK in XFILE_RESOURCES.read_text(errors="replace"):
        remove(XFILE_RESOURCES)
    if XFILE_DESKTOP.exists() and "X-CDE-Copper=true" in XFILE_DESKTOP.read_text(errors="replace"):
        remove(XFILE_DESKTOP)


SHELL, DEFAULT_SHELL = "org.cde.copper.shell", "org.kde.plasma.desktop"


def current_shell():
    return read_config("plasmashellrc", "Shell", "ShellPackage") or os.environ.get("PLASMA_DEFAULT_SHELL", DEFAULT_SHELL)


def set_lockscreen(manifest, kind, running=True):
    """CDE's lock screen ("cde") or Plasma's ("plasma").

    Plasma 6 takes the lock screen from the shell package that plasmashell
    runs (plasmashellrc [Shell] ShellPackage), and kscreenlocker reads the
    same key. CDE's lives in the shell package org.cde.copper.shell, which
    takes everything else from org.kde.plasma.desktop. plasmashell names its
    panel and desktop configuration after the shell, so the configuration
    moves with it: plasmashell is stopped (it writes its file), the file is
    copied to the other name, the key set, plasmashell started again."""
    current = current_shell()
    wanted = SHELL if kind == "cde" else manifest.get("shell_previous", DEFAULT_SHELL)
    manifest["lockscreen"] = kind
    if current == wanted or (kind == "plasma" and current != SHELL):
        return
    if kind == "cde":
        manifest["shell_previous"] = current
    save_manifest(manifest)
    if running:
        run("systemctl", "--user", "stop", "plasma-plasmashell.service")
    source = CONFIG / f"plasma-{current}-appletsrc"
    if source.exists():
        shutil.copy2(source, CONFIG / f"plasma-{wanted}-appletsrc")
    if kind == "cde":
        manifest["shell_previous"] = current
    write_config("plasmashellrc", "Shell", {"ShellPackage": wanted})
    if running:
        start_shell()


# The shell follows the global theme. A global theme applied with its
# layout looks for <shell>-layout.js; other themes (Breeze, NT Legacy, ...)
# only ship one for Plasma's shell, so under CDE's shell they got Plasma's
# default panel instead of their own. A systemd path unit watches kdeglobals
# and runs "follow-theme": away from CDE's global themes back to the shell
# before, with the theme's layout loaded there if the layout was replaced;
# back to CDE (with CDE's lock screen chosen) into CDE's shell.
OUR_THEMES = ("org.cde.copper.desktop", "org.cde.copper.night")
WATCH = "cde-copper-theme"


def move_shell(current, wanted):
    """plasmashell under another shell package, its configuration moved."""
    run("systemctl", "--user", "stop", "plasma-plasmashell.service")
    source = CONFIG / f"plasma-{current}-appletsrc"
    if source.exists():
        shutil.copy2(source, CONFIG / f"plasma-{wanted}-appletsrc")
    write_config("plasmashellrc", "Shell", {"ShellPackage": wanted})
    start_shell()


def start_shell():
    """Start plasmashell; quick theme switches could hit systemd's start
    limit (start-limit-hit), which left the desktop without a shell."""
    run("systemctl", "--user", "reset-failed", "plasma-plasmashell.service", check=False)
    if run("systemctl", "--user", "start", "plasma-plasmashell.service", check=False).returncode:
        time.sleep(2)
        run("systemctl", "--user", "reset-failed", "plasma-plasmashell.service", check=False)
        run("systemctl", "--user", "start", "plasma-plasmashell.service")


def wait_for_shell(seconds=30):
    exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
    for _ in range(seconds * 2):
        result = subprocess.run([exe, "org.kde.plasmashell", "/PlasmaShell"], capture_output=True, text=True,
                                env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
        if "loadLookAndFeelDefaultLayout" in result.stdout:
            break
        time.sleep(0.5)
    else:
        return False
    # A layout script needs every screen's desktop: run too early, its
    # panels for further screens found no screen (screen -1) and were gone.
    probe = "var s = {}; for (var d of desktops()) if (d.screen >= 0) s[d.screen] = 1; print(Object.keys(s).length + ' ' + screenCount)"
    for _ in range(seconds * 2):
        result = subprocess.run([exe, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", probe],
                                capture_output=True, text=True, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
        found = result.stdout.split()
        if len(found) == 2 and found[0] == found[1] and found[1] != "0":
            time.sleep(1)
            return True
        time.sleep(0.5)
    return True


def follow_theme():
    if not MANIFEST.exists() or not session_ready():
        return
    manifest = json.loads(MANIFEST.read_text())
    if not manifest.get("applied"):
        return
    # System Settings writes the theme first and then has the layout applied.
    time.sleep(3)
    theme = read_config("kdeglobals", "KDE", "LookAndFeelPackage") or ""
    shell = current_shell()
    if theme not in OUR_THEMES and shell == SHELL:
        panels = CONFIG / f"plasma-{SHELL}-appletsrc"
        console_kept = panels.exists() and "org.cde.copper.frontpanel" in panels.read_text(errors="replace")
        previous = manifest.get("shell_previous", DEFAULT_SHELL)
        move_shell(SHELL, previous if previous != SHELL else DEFAULT_SHELL)
        # The layout was replaced (the console is gone): the theme's own,
        # loaded under the shell it was written for.
        if not console_kept and theme and wait_for_shell():
            dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.loadLookAndFeelDefaultLayout", theme)
    elif theme in OUR_THEMES and shell != SHELL and manifest.get("lockscreen", "cde") == "cde":
        manifest["shell_previous"] = shell
        save_manifest(manifest)
        move_shell(shell, SHELL)
    rescue_lost_panels()


def lost_panels():
    exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
    result = subprocess.run([exe, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript",
                             "print(panels().filter(function (p) { return p.screen < 0; }).length)"],
                            capture_output=True, text=True, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    return result.stdout.strip() not in ("", "0")


def rescue_lost_panels():
    """A layout loaded while plasmashell runs, on two screens, could leave a
    panel on no screen (screen -1) and the desktops black until plasmashell
    started again (seen with NT Legacy's layout script, which sets each
    panel's screen). Checked twice; then plasmashell is restarted once."""
    if not wait_for_shell(15) or not lost_panels():
        return
    time.sleep(3)
    if lost_panels():
        run("systemctl", "--user", "stop", "plasma-plasmashell.service", check=False)
        start_shell()


def watch_units(enable):
    """The path unit that runs follow-theme, and its service."""
    folder = CONFIG / "systemd/user"
    path, service = folder / f"{WATCH}.path", folder / f"{WATCH}.service"
    if not enable:
        run("systemctl", "--user", "disable", "--now", f"{WATCH}.path", check=False)
        remove(path)
        remove(service)
        run("systemctl", "--user", "daemon-reload", check=False)
        return
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text("[Unit]\nDescription=CDE Copper: the shell follows the global theme\n\n"
                    "[Path]\nPathChanged=%h/.config/kdeglobals\nPathChanged=%h/.config/kdedefaults/kdeglobals\n\n"
                    "[Install]\nWantedBy=default.target\n")
    service.write_text("[Unit]\nDescription=CDE Copper: the shell follows the global theme\n\n"
                       "[Service]\nType=oneshot\nExecStart=/usr/bin/python3 %h/.local/share/cde-copper/tool/manage.py follow-theme\n")
    run("systemctl", "--user", "daemon-reload", check=False)
    run("systemctl", "--user", "enable", "--now", f"{WATCH}.path", check=False)


GTK_THEME = "CDECopper"


def gtk_theme(name=None):
    """The GTK theme Plasma sets (kded's gtkconfig), or set it."""
    exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
    if not exe:
        return ""
    args = [exe, "org.kde.GtkConfig", "/GtkConfig", "org.kde.GtkConfig." + ("setGtkTheme" if name else "gtkTheme")] + ([name] if name else [])
    result = subprocess.run(args, capture_output=True, text=True, timeout=10,
                            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    return result.stdout.strip()


def update_gtk(name):
    """Rebuild the GTK theme (ours) in the palette; running GTK programs load
    it again when the theme name changes, so it is switched away and back."""
    sys.path.insert(0, str(ROOT))
    import build
    from gtktheme import build_gtk
    build_gtk(DATA, build.P if name == "Copper" else palettes.theme(name))
    if gtk_theme() == GTK_THEME:
        gtk_theme("Adwaita")
        time.sleep(0.5)
        gtk_theme(GTK_THEME)


def update_splash(name):
    """The start-up screen in the palette: its Colours.qml and backdrop tile
    in the installed global theme (ours)."""
    sys.path.insert(0, str(ROOT))
    import build
    colours = build.P if name == "Copper" else palettes.theme(name)
    tile = DATA / TOOL / "backdrops" / name / "Lattice.png"
    # Both global themes: the start-up screen comes from the day one, the
    # logout dialog from whichever is applied.
    for ident in ("org.cde.copper.desktop", "org.cde.copper.night"):
        splash = DATA / f"plasma/look-and-feel/{ident}/contents/splash"
        if not splash.exists():
            continue
        (splash / "Colours.qml").write_text(build.splash_colours(colours))
        if tile.exists():
            shutil.copy2(tile, splash / "images/backdrop.png")
    # The lock screen (shell package) shares colours and tile.
    lock = DATA / "plasma/shells/org.cde.copper.shell/contents/lockscreen"
    if lock.exists():
        (lock / "Colours.qml").write_text(build.splash_colours(colours))
        if tile.exists():
            shutil.copy2(tile, lock / "images/backdrop.png")


def material_tiles():
    """The natural-colour material tiles, as installed with the backdrop plugin."""
    return DATA / "plasma/wallpapers/org.cde.copper.backdrop/contents/images/tiles"


def set_backdrop(manifest, name, scale):
    """Show one CDE backdrop or picture through the "CDE Backdrop" wallpaper
    type, or with "none" the plain desktop colour of the palette."""
    import backdrops
    chosen = manifest.get("palette", "Copper")
    colour_set = workspace_set(chosen)
    manifest["backdrop"], manifest["backdrop_scale"] = name, scale
    if name == "none":
        plasma_script("for (var d of desktops()) { d.wallpaperPlugin = 'org.kde.color';"
                      " d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];"
                      f" d.writeConfig('Color', '{colour_set['bg']}'); }}")
    else:
        # A picture is "picture:<key>" of the picture wallpapers.
        known = (backdrops.names() + backdrops.tile_names() + [f"natural:{key}" for key in backdrops.tile_names()]
                 + [f"picture:{key}" for key, _, _ in PICTURES])
        if name not in known:
            raise RuntimeError(f"Unknown backdrop {name!r}; available: {', '.join(known)}")
        plasma_script("for (var d of desktops()) { d.wallpaperPlugin = 'org.cde.copper.backdrop';"
                      " d.currentConfigGroup = ['Wallpaper', 'org.cde.copper.backdrop', 'General'];"
                      # One backdrop chosen: it replaces backdrops per workspace.
                      f" d.writeConfig('Backdrop', '{name}'); d.writeConfig('Palette', '{chosen}'); d.writeConfig('PerWorkspace', false);"
                      f" d.writeConfig('PixelSize', {int(scale)}); d.writeConfig('Color', '{colour_set['bg']}'); }}")
    save_manifest(manifest)


def set_window_shadow(manifest, on):
    """The window frame's short hard shadow, an option of the decoration
    (auroraerc, the decoration's own group; System Settings shows it too)."""
    manifest["window_shadow"] = on
    write_config("auroraerc", DECORATION, {"windowShadow": "true" if on else "false"})
    dbus("org.kde.KWin", "/KWin", "reconfigure")


def palette_action(name=None, backdrop=None, scale=None, follow=False, notify=False, progress=None, cursor=None, lockscreen=None,
                   window_shadow=None, pattern_colour=None):
    """Switch palette (and backdrop) of an applied installation; with follow,
    take the palette from the colour scheme chosen in System Settings."""
    if not session_ready():
        if follow:
            return
        raise RuntimeError("Apply palettes from a running Plasma session")
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before choosing a palette")
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE.with_suffix(".lock"), "a") as lock:
        # Two consoles (two screens) may ask at the same moment.
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = json.loads(MANIFEST.read_text())
        if follow:
            scheme = current_scheme()
            match = re.fullmatch(r"CDE([A-Za-z]+)", scheme)
            name = match.group(1) if match else None
            if name not in ("Copper", *palettes.names()):
                return
        if lockscreen:
            set_lockscreen(manifest, lockscreen)
            save_manifest(manifest)
        if window_shadow is not None:
            set_window_shadow(manifest, window_shadow)
            save_manifest(manifest)
        if cursor:
            manifest["cursor"] = cursor
            install_cursors(manifest)
            save_manifest(manifest)
        if pattern_colour and pattern_colour != manifest.get("pattern_colour", "cde"):
            # The patterns are drawn when a palette is applied: draw again.
            manifest["pattern_colour"] = pattern_colour
            name = name or manifest.get("palette", "Copper")
            follow = False
        if progress:
            # A progress style, even the same again, rebuilds the controls of
            # the palette in use (an older installation may lack it).
            manifest["progress"] = progress
            name = name or manifest.get("palette", "Copper")
            follow = False
        # Only an explicit or a changed palette is applied; a backdrop alone
        # keeps the palette as it is.
        if name and (not follow or name != manifest.get("palette", "Copper")):
            set_palette(manifest, name)
            refresh_running_windows()
            if notify and shutil.which("notify-send"):
                run("notify-send", "-a", "CDE Front Console", "-i", "preferences-desktop-color",
                    f"Palette {name}", "Restart applications to bring their controls into the new colours.", check=False)
        if backdrop:
            set_backdrop(manifest, backdrop, scale or manifest.get("backdrop_scale", 1))


def apply(panel=False, palette=None, backdrop=None, backdrop_scale=None):
    if not session_ready():
        raise RuntimeError("Apply the theme from a running Plasma session")
    if not MANIFEST.exists():
        raise RuntimeError("Install the theme before applying it")
    manifest = json.loads(MANIFEST.read_text())
    manifest["applied"] = True
    chosen = palette or manifest.get("palette", "Copper")
    save_manifest(manifest)
    run("plasma-apply-lookandfeel", "--apply", "org.cde.copper.desktop")
    set_palette(manifest, chosen)
    # The Motif controls are a Kvantum theme; without the Kvantum style
    # plugin the built-in Qt Windows style is the nearest bevelled fallback.
    if kvantum_available():
        style = "kvantum"
    else:
        style = "Windows"
        print("Kvantum style plugin not found; using the Qt Windows style. Install 'kvantum' for the Motif controls.")
    # Day and night for Plasma's automatic switching (Quick Settings).
    write_config("kdeglobals", "KDE", {"widgetStyle": style, "LookAndFeelPackage": "org.cde.copper.desktop",
                                      "DefaultLightLookAndFeel": "org.cde.copper.desktop",
                                      "DefaultDarkLookAndFeel": "org.cde.copper.night"})
    write_config("kdeglobals", "Icons", {"Theme": "CDECopper"})
    # Cursors after the X11 cursor font; plasma-apply-cursortheme also tells
    # running programs and XWayland.
    write_config("kcminputrc", "Mouse", {"cursorTheme": "CDECopperCursors"})
    write_config("ksplashrc", "KSplash", {"Engine": "KSplashQML", "Theme": "org.cde.copper.desktop"})
    if cursor_tool():
        run("plasma-apply-cursortheme", "CDECopperCursors", check=False)
    write_config("kdeglobals", "General", {"font": UI_FONT, "fixed": MONO_FONT, "menuFont": UI_FONT, "toolBarFont": UI_FONT})
    write_config("kdeglobals", "WM", {"activeFont": TITLE_FONT})
    write_config("kwinrc", "org.kde.kdecoration2", {"library": "org.kde.kwin.aurorae", "theme": DECORATION, "ButtonsOnLeft": "M", "ButtonsOnRight": "IAX", "BorderSize": "Normal"})
    write_config("kwinrc", "WM", {"activeFont": TITLE_FONT})
    write_config("kwinrc", "Plugins", {"cde-copper-arrangeEnabled": "true"})
    write_config("kwinrc", "TabBox", {"LayoutName": "org.cde.copper.switcher"})
    write_config("konsolerc", "Desktop Entry", {"DefaultProfile": "CDE Copper.profile"})
    dbus("org.kde.KWin", "/KWin", "reconfigure")
    dbus("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.start")
    set_lockscreen(manifest, manifest.get("lockscreen", "cde"))
    watch_units(True)
    # GTK programs: Motif controls too (Plasma's gtkconfig sets GTK 3/4).
    previous = gtk_theme()
    if previous and previous != GTK_THEME:
        manifest["gtk_previous"] = previous
    gtk_theme(GTK_THEME)
    save_manifest(manifest)
    if backdrop:
        set_backdrop(manifest, backdrop, backdrop_scale or manifest.get("backdrop_scale", 1))
    if panel:
        # KWin exposes workspace creation through D-Bus; no session restart
        # required. The console's own setting (cdecopperrc, mirrored from its
        # configuration) decides how many; the console renames and trims
        # them itself once it runs.
        exe = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
        count = int(subprocess.check_output([exe, "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.count"], text=True).strip())
        saved = configparser.ConfigParser(interpolation=None, strict=False)
        saved.optionxform = str
        saved.read(CONFIG / "cdecopperrc")
        shown = saved.get("Console", "showWorkspaces", fallback="true") != "false"
        wanted = max(1, min(8, int(saved.get("Console", "workspaceCount", fallback="4")))) if shown else count
        for i in range(count, wanted):
            dbus("org.kde.KWin", "/VirtualDesktopManager", "createDesktop", str(i), str(i + 1))
        # KWin keeps its workspaces in memory and writes kwinrc only when they
        # change: after an uninstall restored an older kwinrc, four running
        # workspaces would need no change and the next login find one.
        # KWin adds the ids for missing entries itself.
        write_config("kwinrc", "Desktops", {"Number": str(max(wanted, count)), "Rows": "2"})
        dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", (ROOT / "layout.js").read_text())
    print(f"Applied with palette {chosen}. Log out and back in to reload all application styles and the decoration.")


def list_palettes():
    import backdrops
    print("Palettes:  Copper (default), " + ", ".join(palettes.names()))
    print("Backdrops: none, " + ", ".join(backdrops.names() + backdrops.tile_names()))


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
    config_files = manifest.get("config_files", [f for f in CONFIG_FILES if f != "auroraerc"])
    if any(file not in CONFIG_FILES for file in config_files):
        raise RuntimeError("Unexpected config backup in ownership manifest")
    # The watcher first, or restoring kdeglobals would set it off.
    watch_units(False)
    if manifest["applied"]:
        run("systemctl", "--user", "stop", "plasma-plasmashell.service")
        # Keep the current files before switching shells copies panel config
        # over the default shell's file.
        kept = STATE / "config-at-uninstall"
        remove(kept)
        for file in CONFIG_FILES:
            if (CONFIG / file).exists():
                copy(CONFIG / file, kept / file)
        shell_config = f"plasma-{SHELL}-appletsrc"
        if (CONFIG / shell_config).exists():
            copy(CONFIG / shell_config, kept / shell_config)
    if gtk_theme() == GTK_THEME:
        gtk_theme(manifest.get("gtk_previous", "Breeze"))
    # Back to Plasma's shell package (and lock screen) with the panel
    # configuration, before the saved configuration is restored.
    if current_shell() == SHELL:
        set_lockscreen(manifest, "plasma", running=False)
        remove(CONFIG / f"plasma-{SHELL}-appletsrc")
    if manifest["applied"]:
        # The pre-install files come back whole; what was changed since is
        # kept beside them, so nothing set after installing is lost.
        for file in config_files:
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
    remove_xfile_integration()
    if manifest["applied"]:
        dbus("org.kde.KWin", "/KWin", "reconfigure")
        start_shell()
    # The decoration's own group in auroraerc (its options), written by the
    # theme; the rest of that file belongs to other decorations.
    # New installs restored this file whole, including any pre-existing CDE
    # options. Only older installs without a backup need group cleanup.
    if manifest["applied"] and "auroraerc" not in config_files and (CONFIG / "auroraerc").exists():
        aurorae = configparser.ConfigParser(interpolation=None, strict=False)
        aurorae.optionxform = str
        aurorae.read(CONFIG / "auroraerc")
        if aurorae.remove_section(DECORATION):
            with (CONFIG / "auroraerc").open("w") as out:
                aurorae.write(out, space_around_delimiters=False)
    MANIFEST.rename(STATE / "uninstalled-manifest.json")
    # Keep the lock inode: a waiting process may already have it open.
    print("Removed only manifest-owned files and restored pre-install configuration. Backup retained at " + str(STATE)
          + "; the configuration as it was before uninstalling is in " + str(STATE / "config-at-uninstall"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "apply", "uninstall", "palettes", "palette", "follow-theme"))
    parser.add_argument("--palette", help="CDE palette to apply (see the 'palettes' action); Copper is the default")
    parser.add_argument("--backdrop", help="CDE backdrop to tile on the desktop (see 'palettes'), or 'none'")
    parser.add_argument("--follow-scheme", action="store_true", help="palette: take the palette from the colour scheme in System Settings")
    parser.add_argument("--notify", action="store_true", help="palette: report the switch as a desktop notification")
    parser.add_argument("--backdrop-scale", type=int, choices=(1, 2, 3), help="pixel size of the backdrop tiles, e.g. 2 for 200 %% displays")
    parser.add_argument("--progress", choices=("outlined", "floating", "slim"),
                        help="palette: progress bar style (outlined, floating in the groove, slim)")
    parser.add_argument("--cursor", type=lambda v: v if v in ("copper", "palette", "white") or re.fullmatch(r"#[0-9a-fA-F]{6}", v) else parser.error(f"--cursor: {v!r}"),
                        help="palette: rim of the cursors: copper, palette (its accent), white or #rrggbb")
    parser.add_argument("--window-shadow", choices=("on", "off"), help="palette: the window frame's short hard shadow")
    parser.add_argument("--pattern-colour", choices=("cde", "palette"),
                        help="palette: CDE's patterns in white (or black) as in CDE, or on dark palettes in a colour of the palette")
    parser.add_argument("--lockscreen", choices=("cde", "plasma"), help="palette: CDE's lock screen (a shell package of its own) or Plasma's")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--panel", action="store_true", help="replace the panel layout, backed up on installation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restart-shell", action="store_true", help="install: restart Plasma afterwards without asking")
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
    if args.action != "palette":
        STATE.parent.mkdir(parents=True, exist_ok=True)
        # Outside STATE, which a reinstall may rename. Palette uses the same
        # lock below; all mutations of ownership must be serialized.
        lock = open(STATE.with_suffix(".lock"), "a")
        fcntl.flock(lock, fcntl.LOCK_EX)
    if args.action == "install":
        install()
        if args.apply:
            apply(args.panel, args.palette, args.backdrop, args.backdrop_scale)
        offer_shell_restart(args.restart_shell)
    elif args.action == "apply":
        apply(args.panel, args.palette, args.backdrop, args.backdrop_scale)
    elif args.action == "follow-theme":
        follow_theme()
    elif args.action == "palette":
        palette_action(args.palette, args.backdrop, args.backdrop_scale, args.follow_scheme, args.notify, args.progress, args.cursor, args.lockscreen,
                       None if args.window_shadow is None else args.window_shadow == "on", args.pattern_colour)
    else:
        uninstall()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
