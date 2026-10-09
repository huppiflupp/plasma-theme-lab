#!/usr/bin/env python3
"""The KDE Store edition of CDE Copper.

System Settings › Global Theme › "Get New…" installs one Look and Feel
package and nothing else. The other parts come from separate KDE Store
entries that the global theme names as dependencies
("X-KPackage-Dependencies": kns://<knsrc>/api.kde-look.org/<id>); KPackage
fetches them when the theme is installed.

    python3 store.py                    # archives without dependencies
    python3 store.py --ids store-ids.json

The first run makes one archive per store entry in dist/store/<version>/.
Once the parts are uploaded, their content ids go into store-ids.json (one
per part, see the UPLOAD.md written next to the archives) and a second run
writes the global themes with their dependencies.

What the store edition leaves out, because the store has no category for
it or it needs manage.py: the Kvantum Motif controls (an optional archive
for Kvantum Manager is made), CDE's lock screen (Plasma's is used), the 37
palettes with recoloured Plasma surfaces (the colour schemes are included;
the console's "Style Manager…" entry opens System Settings' colours there),
the Style Manager window itself, and the QML window frame (an SVG
Aurorae frame drawn by tools/gen-motif-aurorae.py stands in for it).
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
sys.path.insert(0, str(ROOT))
from build import VERSION  # noqa: E402

PROVIDER = "api.kde-look.org"

# key: (archive name, knsrc, store category as the knsrc asks for it, title, what it is)
PARTS = {
    "console": ("cde-copper-console", "plasmoids.knsrc", "Plasma 6 Extensions",
                "CDE Front Console", "the front console widget"),
    "backdrop": ("cde-copper-backdrop", "wallpaperplugin.knsrc", "Plasma Wallpaper Plugin6",
                 "CDE Backdrop", "CDE's backdrop patterns as a wallpaper plugin"),
    "plasma": ("cde-copper-plasma-style", "plasma-themes.knsrc", "Plasma Theme",
               "CDE Copper Plasma Style", "the Plasma style (panels, popups, widgets)"),
    "frame": ("cde-copper-window-frame", "window-decorations.knsrc", "Plasma 6 Window Decorations",
              "CDE Copper Window Frame", "the Motif window frame (SVG Aurorae, day and night)"),
    "colors": ("cde-copper-colors", "colorschemes.knsrc", "KDE Color Scheme KDE4",
               "CDE Palettes", "CDE's 37 palettes and Copper as colour schemes"),
    "icons": ("cde-copper-icons", "icons.knsrc", "KDE Icon Theme",
              "CDE Copper Icons", "the icon theme"),
    "cursors": ("cde-copper-cursors", "xcursor.knsrc", "X11 Mouse Theme",
                "CDE Copper Cursors", "the X11 cursor font of CDE and Motif"),
    "arrange": ("cde-copper-arrange", "kwinscripts.knsrc", "Kwin Scripts Plasma 6",
                "CDE Copper Window Arrangement", "terminals around the console, terminal sets, saved layouts"),
    "switcher": ("cde-copper-switcher", "kwinswitcher.knsrc", "Kwin Switching Layouts Plasma 6",
                 "CDE Copper Window Switcher", "the Alt+Tab switcher"),
}
THEMES = {
    "org.cde.copper.desktop": ("cde-copper-global-theme", "CDECopper", "CDE Copper"),
    "org.cde.copper.night": ("cde-copper-night-global-theme", "CDECopperNight", "CDE Copper Night"),
}
NIGHT_SCHEME = "CDENorthernSky"


def tar(target, sources, base):
    """A .tar.gz of the given paths, stored relative to base."""
    with tarfile.open(target, "w:gz") as archive:
        for source in sources:
            archive.add(source, arcname=str(Path(source).relative_to(base)),
                        filter=lambda info: None if "__pycache__" in info.name else info)


def frames(stage):
    """The SVG window frames, day (Copper) and night (Northern Sky)."""
    out = stage / "aurorae"
    for name, title, scheme in (("CDECopper", "CDE Copper", "CDECopper"),
                                ("CDECopperNight", "CDE Copper Night", NIGHT_SCHEME)):
        subprocess.run([sys.executable, str(ROOT / "tools/gen-motif-aurorae.py"),
                        "--scheme", str(BUILD / "color-schemes" / (scheme + ".colors")),
                        "--name", name, "--title", title, "--version", VERSION, "-o", str(out)], check=True)
    return out


def console(stage):
    """The console with its translations inside. Plasma registers the
    package's contents/locale for the catalogue plasma_applet_<id> when it
    loads the widget, so the console asks that catalogue instead of
    cde-copper, which KDE would only find in the user's locale folder and
    the console copies there for the next start (too late for the first)."""
    package = "org.cde.copper.frontpanel"
    domain = "plasma_applet_" + package
    target = stage / "plasmoids" / package
    shutil.copytree(BUILD / "plasma/plasmoids" / package, target,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for qml in target.rglob("*.qml"):
        text = qml.read_text(encoding="utf-8")
        qml.write_text(re.sub(r'\b(i18ndp?)\("cde-copper"', r'\1("%s"' % domain, text), encoding="utf-8")
    shutil.copytree(BUILD / "locale", target / "contents/locale")
    for mo in (target / "contents/locale").glob("*/LC_MESSAGES/cde-copper.mo"):
        shutil.copy(mo, mo.with_name(domain + ".mo"))
    return target


def theme(stage, package, frame, title, ids):
    """A global theme in its store form: Breeze widgets (no Kvantum),
    the SVG frame, Plasma's lock screen, and the parts as dependencies."""
    target = stage / "look-and-feel" / package
    shutil.copytree(BUILD / "plasma/look-and-feel" / package, target)
    # Without CDE's own shell, only the standard desktop's layout applies.
    for layout in (target / "contents/layouts").glob("org.cde.copper.shell-layout.js"):
        layout.unlink()
    defaults = (target / "contents/defaults").read_text(encoding="utf-8")
    defaults = defaults.replace("widgetStyle=kvantum", "widgetStyle=Breeze")
    defaults = defaults.replace("theme=kwin4_decoration_qml_cdecopper", "theme=__aurorae__svg__" + frame)
    # The night theme took the splash and Plasma style of the day theme,
    # which a store user need not have.
    defaults = defaults.replace("Theme=org.cde.copper.desktop", "Theme=" + package)
    if "[plasmarc][Theme]" not in defaults:
        defaults += "[plasmarc][Theme]\nname=cde-copper\n"
    # Plasma takes the window switcher from this group (and writes TabBox).
    defaults += "[kwinrc][WindowSwitcher]\nLayoutName=org.cde.copper.switcher\n"
    (target / "contents/defaults").write_text(defaults, encoding="utf-8")

    meta_path = target / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    description = meta["KPlugin"].get("Description", "").rstrip(". ")
    meta["KPlugin"]["Description"] = description + ". KDE Store edition; the full theme is at the project page."
    deps = ["kns://%s/%s/%s" % (PARTS[key][1], PROVIDER, ids[key]) for key in PARTS if ids.get(key)]
    if deps:
        meta["X-KPackage-Dependencies"] = deps
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target, len(deps)


def upload_guide(out, ids, have_deps):
    lines = [f"# CDE Copper {VERSION} — KDE Store upload", "",
             "Upload each part as its own entry on https://store.kde.org (one account, "
             "\"Add Product\"), in the category given: the name KDE asks the store for "
             "(the store's menu may word it slightly differently). Then write the content ids (the "
             "number in the entry's address) into `store-ids.json` next to `store.py` and "
             "run `python3 store.py --ids store-ids.json`: that writes the global themes "
             "with their dependencies. Upload the global themes last. Keep the cursor "
             "archive's name: the store unpacks cursors into a folder named after it.", "",
             "| Part | File | Category | Title | Id |", "|---|---|---|---|---|"]
    for key, (name, knsrc, category, title, what) in PARTS.items():
        file = "CDECopperCursors.tar.gz" if key == "cursors" else f"{name}-{VERSION}.tar.gz"
        lines.append(f"| {key} | `{file}` | {category} | {title} | {ids.get(key, '')} |")
    for package, (name, frame, title) in THEMES.items():
        lines.append(f"| global theme | `{name}-{VERSION}.tar.gz` | Global Themes (Plasma 6) | {title} | "
                     f"{'with dependencies' if have_deps else 'NO DEPENDENCIES YET'} |")
    lines += ["", "Optional, not a dependency (the store has no Kvantum category KDE can install from):", "",
              f"| Kvantum Motif controls | `cde-copper-kvantum-{VERSION}.tar.gz` | Kvantum | "
              "CDE Copper Kvantum | install with Kvantum Manager, then choose the Kvantum style |", "",
              "## What each part is", ""]
    for key, (name, knsrc, category, title, what) in PARTS.items():
        lines.append(f"- **{title}** — {what}.")
    lines += ["", "## Description for the global theme entry", "",
              "CDE Copper brings the Common Desktop Environment to Plasma 6: a front console "
              "with launchers, subpanels, a workspace switch and the window list, the Motif "
              "window frame, CDE's palettes as colour schemes and its backdrops, icons and "
              "cursors after CDE and Motif, and saved window layouts.", "",
              "When applying, tick \"Desktop and window layout\" to get the front console. "
              "This store edition uses Breeze widgets and Plasma's lock screen; the full "
              "theme with Motif controls (Kvantum), CDE's lock screen and the style manager "
              "with all 37 palettes is installed from the project page "
              "(https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE).", ""]
    (out / "UPLOAD.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ids", type=Path, help="store-ids.json: content id per part")
    args = ap.parse_args()
    if not (BUILD / "plasma").is_dir():
        sys.exit("build/ is missing: run python3 build.py first")
    ids = json.loads(args.ids.read_text()) if args.ids else {}
    unknown = set(ids) - set(PARTS)
    if unknown:
        sys.exit("unknown parts in %s: %s" % (args.ids, ", ".join(sorted(unknown))))

    out = ROOT / "dist" / "store" / VERSION
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        made = {
            "console": [console(stage)],
            "backdrop": [BUILD / "plasma/wallpapers/org.cde.copper.backdrop"],
            "plasma": [BUILD / "plasma/desktoptheme/cde-copper"],
            "frame": sorted(frames(stage).iterdir()),
            "colors": sorted((BUILD / "color-schemes").glob("*.colors")),
            "icons": [BUILD / "icons/CDECopper"],
            "cursors": [BUILD / "icons/CDECopperCursors"],
            "arrange": [BUILD / "kwin/scripts/cde-copper-arrange"],
            "switcher": [BUILD / "kwin/tabbox/org.cde.copper.switcher"],
        }
        for key, sources in made.items():
            name = PARTS[key][0]
            if key == "cursors":
                # Cursor themes are unpacked into a folder named after the
                # archive ("subdir-archive"): the archive takes the theme's
                # name and holds its files without a folder of their own.
                cursors = sources[0]
                tar(out / "CDECopperCursors.tar.gz", sorted(cursors.iterdir()), cursors)
                continue
            tar(out / f"{name}-{VERSION}.tar.gz", sources, sources[0].parent)
        tar(out / f"cde-copper-kvantum-{VERSION}.tar.gz", [BUILD / "Kvantum/CDECopper"], BUILD / "Kvantum")
        have_deps = True
        for package, (name, frame, title) in THEMES.items():
            target, count = theme(stage, package, frame, title, ids)
            have_deps = have_deps and count == len(PARTS)
            tar(out / f"{name}-{VERSION}.tar.gz", [target], target.parent)
    upload_guide(out, ids, have_deps)
    for path in sorted(out.iterdir()):
        print(f"{path.stat().st_size // 1024:>6} KiB  {path.relative_to(ROOT)}")
    if not have_deps:
        print("The global themes have no (or not all) dependencies yet; see UPLOAD.md.")


if __name__ == "__main__":
    main()
