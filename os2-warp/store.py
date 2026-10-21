#!/usr/bin/env python3
"""The KDE Store edition of Warp Legacy.

Copied from CDE/store.py (CDE Copper, as of e976e470) and adapted; nothing
is imported from CDE/ (the repository's CLAUDE.md: the themes share no
files). The SVG window frame is drawn by tools/gen-warp-aurorae.py, a copy
of CDE's tools/gen-motif-aurorae.py redrawn for OS/2.

System Settings › Global Theme › "Get New…" installs one Look and Feel
package and nothing else. The other parts come from separate KDE Store
entries that the global theme names as dependencies
("X-KPackage-Dependencies": kns://<knsrc>/api.kde-look.org/<id>); KPackage
fetches them when the theme is installed.

    python3 store.py                    # archives without dependencies
    python3 store.py --ids store-ids.json

It reads an existing build/ and never builds itself (build/ is shared:
run `python3 build.py` first, a full build without WARP_SKIP_ICONS).
The first run makes one archive per store entry in dist/store/<version>/.
Once the parts are uploaded, their content ids go into store-ids.json (one
per part, see the UPLOAD.md written next to the archives) and a second run
writes the global themes with their dependencies.

What the store edition leaves out (STORE.md): everything install.sh does
besides copying packages — warp-legacy-sync at login, the button order
(close left of hide and maximize), choosing the Kvantum theme, the
Konsole profile, LibreOffice's and Firefox's colours, the lock screen
picture, four workspaces, the System Monitor's colours, the IBM Plex
fonts — and the QML window frame (an SVG Aurorae frame stands in for it).
Kvantum and Konsole get optional archives that are no dependency.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
import importlib.util

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
sys.path.insert(0, str(ROOT))
from build import VERSION, VARIANTS, ids as variant_ids  # noqa: E402

PROVIDER = "api.kde-look.org"
DOMAIN = "warp-legacy"
PLASMOIDS = {
    "warpbar": ("org.warplegacy.warpbar", "Warp Bar", "the Warp Bar after the WarpCenter: desktop menu, "
                "window list, lock, find, shut down, a tray of launchers"),
    "launchpad": ("org.warplegacy.launchpad", "LaunchPad", "Warp 4's LaunchPad: lock, find, shut down, "
                  "window list, launchers with drawers"),
    "controlstrip": ("org.warplegacy.controlstrip", "Control Strip", "the Control Strip after Object Desktop: "
                     "workspaces in miniature, launch list, swap and disk gauges, a seven-segment clock"),
    "tablauncher": ("org.warplegacy.tablauncher", "Tab Launcher", "notebook tabs with windows, favourites and "
                    "the application menu, in a drawer that slides into the screen edge"),
    "taskbar": ("org.warplegacy.taskbar", "Warp Taskbar", "the taskbar after the Neon concept: Start opens "
                "the Warp menu, workspaces, a button per window"),
}

# key: (archive name, knsrc, store category as the knsrc asks for it, title, what it is)
PARTS = {key: (f"warp-legacy-{key}", "plasmoids.knsrc", "Plasma 6 Extensions", f"Warp Legacy {title}", what)
         for key, (_, title, what) in PLASMOIDS.items()}
PARTS.update({
    "plasma": ("warp-legacy-plasma-style", "plasma-themes.knsrc", "Plasma Theme",
               "Warp Legacy Plasma Style", "the classic Plasma style (panels, popups, widgets in Warp 4's grey)"),
    "plasma-neon": ("warp-legacy-neon-plasma-style", "plasma-themes.knsrc", "Plasma Theme",
                    "Warp Legacy Neon Plasma Style", "the Neon Plasma style (navy, cyan and violet edges)"),
    "frame": ("warp-legacy-window-frame", "window-decorations.knsrc", "Plasma 6 Window Decorations",
              "Warp Legacy Window Frame", "the OS/2 window frame as SVG Aurorae, classic and Neon"),
    "colors": ("warp-legacy-colors", "colorschemes.knsrc", "KDE Color Scheme KDE4",
               "Warp Legacy Colours", "the colour schemes Warp Legacy and Warp Legacy Neon"),
    "icons": ("warp-legacy-icons", "icons.knsrc", "KDE Icon Theme",
              "Warp Legacy Icons", "Warp 4's yellow folders and grey devices as an icon theme"),
    "icons-neon": ("warp-legacy-neon-icons", "icons.knsrc", "KDE Icon Theme",
                   "Warp Legacy Neon Icons", "the glowing Neon icons: Warp Legacy Neon, Neon 2026 and "
                   "Neon 2026 Violett (the one the global theme picks; it inherits from the other two)"),
    "cursors": ("warp-legacy-neon-cursors", "xcursor.knsrc", "X11 Mouse Theme",
                "Warp Legacy Neon Cursors", "Breeze's cursors with the rim in Neon's light"),
    "wallpapers": ("warp-legacy-wallpapers", "wallpaper.knsrc", "KDE Wallpaper (other)",
                   "Warp Legacy Pictures", "the 38 pictures and two plain desktops as wallpaper packages, 3840x2160"),
})
CURSORS = "WarpLegacyNeonCursors"     # the archive's name is the folder's (subdir-archive)
NEON_ICONS = ["WarpLegacyNeon", "WarpLegacyNeon2026", "WarpLegacyNeon2026Violett"]

# package: (archive name, SVG frame, title, the parts it depends on)
THEMES = {
    "org.warplegacy.desktop": ("warp-legacy-global-theme", "WarpLegacy", "Warp Legacy",
                               list(PLASMOIDS) + ["plasma", "frame", "colors", "icons", "wallpapers"]),
    "org.warplegacy.neon.desktop": ("warp-legacy-neon-global-theme", "WarpLegacyNeon", "Warp Legacy Neon",
                                    list(PLASMOIDS) + ["plasma-neon", "frame", "colors", "icons-neon",
                                                       "cursors", "wallpapers"]),
}
# The Warp menu's "Switch to …" runs session/warp-legacy-switch, which only
# install.sh brings; the store copy falls back to the global theme alone.
SWITCH = 'command: "sh \\"${XDG_DATA_HOME:-$HOME/.local/share}/warp-legacy/warp-legacy-switch\\" toggle",'
SWITCH_STORE = ('command: "sh -c \'s=\\"${XDG_DATA_HOME:-$HOME/.local/share}/warp-legacy/warp-legacy-switch\\"; '
                'if [ -f \\"$s\\" ]; then sh \\"$s\\" toggle; else plasma-apply-lookandfeel --apply " '
                '+ (neon ? "org.warplegacy.desktop" : "org.warplegacy.neon.desktop") + "; fi\'",')
# Keys of the global themes' defaults that name what only install.sh
# brings: the IBM Plex fonts (fonts/), which the store cannot install.
FONT_KEYS = ("font=", "menuFont=", "toolBarFont=", "fixed=", "activeFont=")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def keep(info):
    if "__pycache__" in info.name:
        return None
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


def tar(target, sources, base):
    """A .tar.gz of the given paths, stored relative to base."""
    with tarfile.open(target, "w:gz") as archive:
        for source in sources:
            archive.add(source, arcname=str(Path(source).relative_to(base)), filter=keep)


def frames(stage):
    """The SVG window frames, classic and Neon."""
    out = stage / "aurorae"
    gen = load(ROOT / "tools/gen-warp-aurorae.py", "gen_warp_aurorae")
    for v in VARIANTS:
        name = variant_ids(v)["scheme"]          # WarpLegacy, WarpLegacyNeon
        gen.write_theme(out, name, v["name"], VERSION, v["P"], v["style"])
    return out


def plasmoid(stage, key):
    """A panel with its translations inside. Plasma registers the
    package's contents/locale for the catalogue plasma_applet_<id> when it
    loads the widget, so the copy asks that catalogue instead of
    warp-legacy, which install.sh puts into ~/.local/share/locale."""
    package = PLASMOIDS[key][0]
    domain = "plasma_applet_" + package
    target = stage / "plasmoids" / package
    shutil.copytree(BUILD / "plasma/plasmoids" / package, target,
                    ignore=shutil.ignore_patterns("__pycache__"))
    switched = 0
    for source in list(target.rglob("*.qml")) + list(target.rglob("*.js")):
        text = source.read_text(encoding="utf-8")
        new = re.sub(r'\b(i18nd[a-z]*)\("%s"' % DOMAIN, r'\1("%s"' % domain, text)
        if SWITCH in new:
            new = new.replace(SWITCH, SWITCH_STORE)
            switched += 1
        if new != text:
            source.write_text(new, encoding="utf-8")
    if (target / "contents/ui/DesktopMenu.qml").exists() and not switched:
        sys.exit(f"{package}: the Warp menu's switch entry has changed; adapt SWITCH in store.py")
    for mo in (BUILD / "locale").glob(f"*/LC_MESSAGES/{DOMAIN}.mo"):
        lang = mo.parent.parent.name
        dest = target / "contents/locale" / lang / "LC_MESSAGES" / (domain + ".mo")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mo, dest)
    return target


def konsole(stage):
    """The Konsole colour schemes and profiles, the profiles without the
    IBM Plex Mono font (Konsole's default instead)."""
    target = stage / "konsole"
    target.mkdir(parents=True)
    for source in sorted((BUILD / "konsole").iterdir()):
        text = source.read_text(encoding="utf-8")
        if source.suffix == ".profile":
            text = "".join(line for line in text.splitlines(True) if not line.startswith("Font="))
        (target / source.name).write_text(text, encoding="utf-8")
    return target


def theme(stage, package, frame, title, needs, ids):
    """A global theme in its store form: Breeze widgets (no Kvantum), the
    SVG frame, the system's fonts, and the parts as dependencies."""
    target = stage / "look-and-feel" / package
    shutil.copytree(BUILD / "plasma/look-and-feel" / package, target)
    path = target / "contents/defaults"
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if line.startswith(FONT_KEYS):
            continue
        line = line.replace("widgetStyle=kvantum", "widgetStyle=Breeze")
        line = re.sub(r"^theme=kwin4_decoration_qml_\w+$", "theme=__aurorae__svg__" + frame, line)
        out.append(line)
    # drop groups left empty by the fonts ([kdeglobals][WM])
    defaults = []
    for i, line in enumerate(out):
        if line.startswith("[") and (i + 1 == len(out) or out[i + 1].startswith("[")):
            continue
        defaults.append(line)
    text = "\n".join(defaults) + "\n"
    for needed in ("widgetStyle=Breeze", "theme=__aurorae__svg__" + frame):
        if needed not in text:
            sys.exit(f"{package}: the defaults have changed ({needed} not written); adapt theme() in store.py")
    path.write_text(text, encoding="utf-8")

    meta_path = target / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    description = meta["KPlugin"].get("Description", "").rstrip(". ")
    meta["KPlugin"]["Description"] = description + ". KDE Store edition; the full theme is at the project page."
    deps = ["kns://%s/%s/%s" % (PARTS[key][1], PROVIDER, ids[key]) for key in needs if ids.get(key)]
    if deps:
        meta["X-KPackage-Dependencies"] = deps
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target, len(deps) == len(needs)


def file_name(key):
    return f"{CURSORS}.tar.gz" if key == "cursors" else f"{PARTS[key][0]}-{VERSION}.tar.gz"


def upload_guide(out, ids, complete):
    lines = [f"# Warp Legacy {VERSION} — KDE Store upload", "",
             "Upload each part as its own entry on https://store.kde.org (one account, "
             "\"Add Product\"), in the category given: the name KDE asks the store for "
             "(the store's menu may word it slightly differently). Then write the content ids (the "
             "number in the entry's address) into `store-ids.json` next to `store.py` and "
             "run `python3 store.py --ids store-ids.json`: that writes the global themes "
             "with their dependencies. Upload the global themes last. Keep the cursor "
             "archive's name: the store unpacks cursors into a folder named after it.", "",
             "Licence of every entry: GPL-2.0-or-later (LICENSE). The pictures are generated "
             "decoration, no photographs; nothing of IBM's or Stardock's is included.", "",
             "| Part | File | Category | Title | Id |", "|---|---|---|---|---|"]
    for key, (name, knsrc, category, title, what) in PARTS.items():
        lines.append(f"| {key} | `{file_name(key)}` | {category} | {title} | {ids.get(key, '')} |")
    for package, (name, frame, title, needs) in THEMES.items():
        lines.append(f"| global theme | `{name}-{VERSION}.tar.gz` | Global Themes (Plasma 6) | {title} | "
                     f"{'with dependencies' if complete[package] else 'NO DEPENDENCIES YET'} |")
    lines += ["", "Optional, not a dependency (KDE has no store category it installs these from):", "",
              "| Part | File | Category | Title | How |", "|---|---|---|---|---|",
              f"| Kvantum | `warp-legacy-kvantum-{VERSION}.tar.gz` | Kvantum | Warp Legacy Kvantum | "
              "unpack, install the folders Warp and WarpNeon with Kvantum Manager, choose one, then "
              "System Settings › Application Style › kvantum |",
              f"| Konsole | `warp-legacy-konsole-{VERSION}.tar.gz` | Konsole (or as an extra file of the "
              "global theme entries) | Warp Legacy Konsole | unpack into ~/.local/share/konsole, choose the "
              "profile in Konsole › Settings › Manage Profiles |", "",
              "## Dependencies of the global themes", ""]
    for package, (name, frame, title, needs) in THEMES.items():
        lines.append(f"- **{title}**: " + ", ".join(PARTS[k][3] for k in needs) + ".")
    lines += ["", "## Description per part entry", ""]
    for key, (name, knsrc, category, title, what) in PARTS.items():
        lines.append(f"- **{title}** — {what}. Part of Warp Legacy, OS/2 Warp 4 for Plasma 6; "
                     "installed along with the global themes.")
    lines += ["", "## Description for the global theme entries", "",
              "Put the links of the uploaded parts in (the store shows a bare address as a link); "
              "until the ids are known the lines carry a placeholder.", "",
              "Warp Legacy brings OS/2 Warp 4 to Plasma 6, in two global themes: Warp Legacy, the "
              "classic Warp 4 grey with blue title bars, and Warp Legacy Neon, OS/2 at night with "
              "cyan and violet glowing edges. The Warp Taskbar, the Warp Bar after the WarpCenter, "
              "the LaunchPad, the Control Strip and the Tab Launcher; the OS/2 window frame, "
              "Plasma styles, colour schemes, icons (Warp 4's folders, or glowing Neon ones), "
              "Neon mouse cursors and 38 pictures. Not affiliated with IBM, Arca Noae or Stardock; "
              "everything is drawn anew.", "",
              "Install the global theme and apply it with \"Desktop and window layout\" ticked: "
              "that puts the Warp Taskbar, the Control Strip and the Tab Launcher in place of the "
              "default panel. The parts below are installed along with it (or one by one from "
              "their own entries).", ""]
    for key, (name, knsrc, category, title, what) in PARTS.items():
        link = f"https://store.kde.org/p/{ids[key]}/" if ids.get(key) else "(store link to come)"
        lines.append(f"{title}: {link}")
    lines += ["", "Requirements: Plasma 6 (tested on Fedora 44 / Plasma 6.7 and Kubuntu 26.04 / "
              "Plasma 6.6). After applying: System Settings › Window Decorations › Titlebar Buttons, "
              "put Close left of Minimize and Maximize, as OS/2 had them (the store cannot set the "
              "order). The interface font is IBM Plex Sans Condensed, which the store cannot "
              "install; without it the theme keeps your fonts.", "",
              "This store edition uses Breeze widgets, an SVG version of the window frame (Warp 4's "
              "button look only) and Plasma's lock screen. The full theme adds the QML frame with six "
              "button looks and Neon's glow, OS/2 controls in programs (Kvantum, also offered here "
              "as a separate archive), the button order, Konsole, LibreOffice and Firefox colours, "
              "the neon lock screen, IBM Plex, and keeps it all in step when you switch between "
              "classic and Neon. It is installed from the release archive with install.sh "
              "(link in this entry's Source field).", ""]
    (out / "UPLOAD.md").write_text("\n".join(lines), encoding="utf-8")


def check_build():
    """build/ is shared and may be half-built or a quick one: say what is
    missing instead of packing it."""
    need = [BUILD / "plasma/look-and-feel" / p for p in THEMES]
    need += [BUILD / "plasma/plasmoids" / p for p, _, _ in PLASMOIDS.values()]
    need += [BUILD / "icons" / n for n in ["WarpLegacy", CURSORS] + NEON_ICONS]
    need += [BUILD / "plasma/desktoptheme" / variant_ids(v)["theme"] for v in VARIANTS]
    need += [BUILD / "config/Kvantum" / variant_ids(v)["kvantum"] for v in VARIANTS]
    need += [BUILD / "locale", BUILD / "konsole", BUILD / "wallpapers", BUILD / "color-schemes"]
    missing = [str(p.relative_to(ROOT)) for p in need if not p.exists()]
    if missing:
        sys.exit("build/ is incomplete (run a full python3 build.py, without WARP_SKIP_ICONS): "
                 + ", ".join(missing))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ids", type=Path, help="store-ids.json: content id per part")
    args = ap.parse_args()
    check_build()
    ids = json.loads(args.ids.read_text()) if args.ids else {}
    ids = {k: v for k, v in ids.items() if not k.startswith("_") and v}
    unknown = set(ids) - set(PARTS)
    if unknown:
        sys.exit("unknown parts in %s: %s" % (args.ids, ", ".join(sorted(unknown))))

    out = ROOT / "dist" / "store" / VERSION
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        made = {key: [plasmoid(stage, key)] for key in PLASMOIDS}
        made.update({
            "plasma": [BUILD / "plasma/desktoptheme/warp-legacy"],
            "plasma-neon": [BUILD / "plasma/desktoptheme/warp-legacy-neon"],
            "frame": sorted(frames(stage).iterdir()),
            "colors": sorted((BUILD / "color-schemes").glob("*.colors")),
            "icons": [BUILD / "icons/WarpLegacy"],
            "icons-neon": [BUILD / "icons" / n for n in NEON_ICONS],
            "cursors": [BUILD / "icons" / CURSORS],
            "wallpapers": sorted((BUILD / "wallpapers").iterdir()),
        })
        for key, sources in made.items():
            if key == "cursors":
                # Cursor themes are unpacked into a folder named after the
                # archive ("subdir-archive"): the archive takes the theme's
                # name and holds its files without a folder of their own.
                cursors = sources[0]
                tar(out / file_name(key), sorted(cursors.iterdir()), cursors)
                continue
            tar(out / file_name(key), sources, sources[0].parent)
        tar(out / f"warp-legacy-kvantum-{VERSION}.tar.gz",
            [BUILD / "config/Kvantum" / variant_ids(v)["kvantum"] for v in VARIANTS], BUILD / "config/Kvantum")
        tar(out / f"warp-legacy-konsole-{VERSION}.tar.gz", sorted(konsole(stage).iterdir()), stage / "konsole")
        complete = {}
        for package, (name, frame, title, needs) in THEMES.items():
            target, complete[package] = theme(stage, package, frame, title, needs, ids)
            tar(out / f"{name}-{VERSION}.tar.gz", [target], target.parent)
    upload_guide(out, ids, complete)
    for path in sorted(out.iterdir()):
        print(f"{path.stat().st_size / 1048576:>7.2f} MiB  {path.relative_to(ROOT)}")
    if not all(complete.values()):
        print("The global themes have no (or not all) dependencies yet; see UPLOAD.md.")


if __name__ == "__main__":
    main()
