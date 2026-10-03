#!/usr/bin/env python3
"""Run in the lab VM after build.py; no changes to the active desktop."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import struct
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Assets(unittest.TestCase):
    def test_vector_assets_and_aliases(self):
        files = list((ROOT / "build/icons/CDECopper").rglob("*.svg"))
        self.assertGreater(len(files), 100)
        originals = [f for f in files if not f.is_symlink()]
        self.assertGreater(len(originals), 40)
        for file in files:
            self.assertTrue(file.resolve().is_relative_to(ROOT / "build/icons/CDECopper"))
            doc = ET.parse(file).getroot()
            # scalable/ on a 64-unit grid; 16/ and 22/ hold pixel versions
            # on their own size, whole pixels only.
            size = file.parent.parent.name
            grid = "64" if size == "scalable" else size
            self.assertEqual(doc.get("viewBox"), f"0 0 {grid} {grid}", str(file))
            if size != "scalable":
                for e in doc.iter():
                    for attr in ("x", "y", "width", "height"):
                        if e.get(attr) is not None:
                            self.assertTrue(e.get(attr).isdigit(), f"{file}: {attr}={e.get(attr)}")
            self.assertFalse(any(e.tag.endswith("image") for e in doc.iter()), str(file))
        for file in (ROOT / "build").rglob("*.svg"):
            ET.parse(file)


class Cursors(unittest.TestCase):
    def test_xcursor_files(self):
        import struct
        folder = ROOT / "build/icons/CDECopperCursors/cursors"
        for name in ("left_ptr", "default", "pointer", "text", "wait", "progress", "not-allowed", "ew-resize", "nwse-resize", "grab"):
            data = (folder / name).read_bytes()
            magic, header, version, count = struct.unpack("<4sIII", data[:16])
            self.assertEqual((magic, header, count), (b"Xcur", 16, 4), name)
            for k in range(count):
                kind, size, position = struct.unpack("<3I", data[16 + 12 * k:28 + 12 * k])
                chunk = struct.unpack("<9I", data[position:position + 36])
                self.assertEqual((chunk[0], chunk[1], chunk[4], chunk[5]), (36, 0xfffd0002, size, size), name)
                self.assertLess(chunk[6], size); self.assertLess(chunk[7], size)
                self.assertEqual(len(data) >= position + 36 + 4 * size * size, True, name)


class Separation(unittest.TestCase):
    """CDE Copper must build from its own directory alone.

    The theme shares a repository with NT Legacy, but neither may influence
    the other. A copy of CDE/ placed somewhere with no sibling tools/ has to
    rebuild build/ byte for byte from CDE/tools/."""

    def test_build_is_self_contained_and_reproducible(self):
        with tempfile.TemporaryDirectory(prefix="cde-copy-") as temp:
            copy = Path(temp) / "island/CDE"
            copy.mkdir(parents=True)
            for item in ("tools", "frontpanel", "decoration", "arrange", "backdrop", "fonts", "palettes", "backdrops", "screenshots",
                         "lookandfeel", "shell", "build.py", "icons.py", "cursors.py", "gtktheme.py", "kvantum.py", "palettes.py", "backdrops.py", "layout.js"):
                source = ROOT / item
                if source.is_dir():
                    shutil.copytree(source, copy / item, symlinks=True,
                                    ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    shutil.copy2(source, copy / item)
            result = subprocess.run([sys.executable, str(copy / "build.py")],
                                    cwd=copy, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = {p.relative_to(ROOT / "build") for p in (ROOT / "build").rglob("*") if p.is_file() or p.is_symlink()}
            actual = {p.relative_to(copy / "build") for p in (copy / "build").rglob("*") if p.is_file() or p.is_symlink()}
            self.assertEqual(expected, actual)
            for rel in sorted(expected):
                a, b = ROOT / "build" / rel, copy / "build" / rel
                if a.is_symlink() or b.is_symlink():
                    self.assertEqual(os.readlink(a), os.readlink(b), str(rel))
                else:
                    self.assertEqual(a.read_bytes(), b.read_bytes(), str(rel))

    def test_global_theme_brings_its_layout(self):
        # Plasma only reads this path; a layout elsewhere is silently ignored.
        lnf = ROOT / "build/plasma/look-and-feel/org.cde.copper.desktop/contents"
        layout = lnf / "layouts/org.kde.plasma.desktop-layout.js"
        self.assertTrue(layout.is_file())
        self.assertIn("org.cde.copper.frontpanel", layout.read_text())
        self.assertFalse((lnf / "layout.js").exists())
        self.assertIn("widgetStyle=kvantum", (lnf / "defaults").read_text())

    def test_no_reference_to_sibling_themes(self):
        for name in ("build.py", "icons.py", "manage.py", "package.py", "install.sh",
                     "apply.sh", "uninstall.sh", "palettes.py", "backdrops.py", "kvantum.py"):
            text = (ROOT / name).read_text()
            self.assertNotIn("ROOT.parent", text, name)
            self.assertNotIn("../tools", text, name)
            self.assertNotIn("nt-legacy", text, name)


class Palettes(unittest.TestCase):
    """The 37 CDE palettes: readable, and complete enough to build from."""

    def test_every_text_colour_is_readable(self):
        sys.path.insert(0, str(ROOT))
        import palettes
        self.assertEqual(len(palettes.names()), 37)
        pairs = [("text", "flaeche"), ("text2", "flaeche"), ("link", "flaeche"), ("fenster_text", "fenster"),
                 ("auswahl_text", "auswahl"), ("kopf_aktiv_text", "kopf_aktiv"),
                 ("kopf_inaktiv_text", "kopf_inaktiv"), ("panel_text", "panel")]
        for name in palettes.names():
            colours = palettes.theme(name)
            for fg, bg in pairs:
                self.assertGreaterEqual(palettes.contrast(colours[fg], colours[bg]), 4.5, f"{name}: {fg} on {bg}")

    def test_motif_shading_matches_the_reference(self):
        # Worked by hand through Motif's CalculateColorsRGB for Broica's set 5
        # (#c600 b2d2 a87e): brightness 46639, a medium background, so the
        # top shadow lightens by 57 % and the bottom shadow darkens by
        # 60 + trunc(-14.2) = 46 % (C truncation, not floor).
        sys.path.insert(0, str(ROOT))
        import palettes
        s = palettes.load("Broica")[4]
        self.assertEqual((s["ts"], s["bs"]), ("#e7deda", "#6a605a"))

    def test_palette_builds_and_lints(self):
        sys.path.insert(0, str(ROOT))
        import build
        with tempfile.TemporaryDirectory(prefix="cde-palette-") as temp:
            result = build.build_palette("Alpine", Path(temp))
            for target in result["targets"] + result["config_targets"]:
                self.assertTrue((Path(temp) / target).exists(), target)
            lint = subprocess.run([sys.executable, str(ROOT / "tools/lint-plasma-svg.py"),
                                   str(Path(temp) / "plasma/desktoptheme/cde-alpine")], capture_output=True, text=True)
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)


class Backdrops(unittest.TestCase):
    def test_every_backdrop_renders(self):
        sys.path.insert(0, str(ROOT))
        import backdrops
        import palettes
        colours = backdrops.colours_for(palettes.load("Default")[2])
        self.assertGreaterEqual(len(backdrops.names()), 25)
        for name in backdrops.names():
            tile = backdrops.render(name, colours)
            self.assertTrue(tile.startswith(b"\x89PNG"), name)
            # The image data must hold every declared row (SkyLight.pm is one short).
            import zlib
            width, height = struct.unpack(">II", tile[16:24])
            data = zlib.decompress(tile[tile.index(b"IDAT") + 4:tile.index(b"IEND") - 8])
            self.assertEqual(len(data), height * (1 + 3 * width), name)
            screen = backdrops.desktop(name, colours, 640, 480, 2)
            width, height = struct.unpack(">II", screen[16:24])
            self.assertEqual((width, height), (640, 480), name)


class ConsoleMenus(unittest.TestCase):
    """frontpanel/contents/code/menus.py against made-up profiles."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cde-menus-")
        self.home = Path(self.temp.name)
        apps = self.home / ".local/share/applications"
        apps.mkdir(parents=True)
        for app_id, name, exec_line in (("org.mozilla.firefox", "Firefox", "firefox %u"),
                                        ("org.kde.kwrite", "KWrite", "kwrite %U"),
                                        ("libreoffice-writer", "LibreOffice Writer", "libreoffice --writer %U"),
                                        ("libreoffice-calc", "LibreOffice Calc", "libreoffice --calc %U"),
                                        ("chromium-browser", "Chromium", "chromium-browser %U")):
            (apps / f"{app_id}.desktop").write_text(f"[Desktop Entry]\nName={name}\nExec={exec_line}\nIcon={app_id}\n")
        self.env = {**os.environ, "HOME": str(self.home), "XDG_DATA_HOME": str(self.home / ".local/share"),
                    "XDG_CONFIG_HOME": str(self.home / ".config"), "XDG_DATA_DIRS": str(self.home / "none")}

    def tearDown(self):
        self.temp.cleanup()

    def run_menus(self, kind, command):
        result = subprocess.run([sys.executable, str(ROOT / "frontpanel/contents/code/menus.py"), kind, command],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_firefox_bookmarks_toolbar_first_without_duplicates(self):
        import sqlite3
        root = self.home / ".config/mozilla/firefox"
        profile = root / "abc.default"
        profile.mkdir(parents=True)
        (root / "profiles.ini").write_text("[Profile0]\nName=default\nIsRelative=1\nPath=abc.default\nDefault=1\n")
        db = sqlite3.connect(profile / "places.sqlite")
        db.executescript("""
            CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT);
            CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER, parent INTEGER,
                                        position INTEGER, title TEXT, guid TEXT, dateAdded INTEGER);
            INSERT INTO moz_bookmarks VALUES (2, 2, NULL, 1, 0, 'menu', 'menu________', 0);
            INSERT INTO moz_bookmarks VALUES (3, 2, NULL, 1, 1, 'toolbar', 'toolbar_____', 0);
            INSERT INTO moz_places VALUES (1, 'https://menu.example/'), (2, 'https://bar.example/'), (3, 'place:sort=8');
            INSERT INTO moz_bookmarks VALUES (10, 1, 1, 2, 0, 'Menu', 'a', 5);
            INSERT INTO moz_bookmarks VALUES (11, 1, 2, 3, 0, 'Bar', 'b', 1);
            INSERT INTO moz_bookmarks VALUES (12, 1, 2, 2, 1, 'Bar again', 'c', 2);
            INSERT INTO moz_bookmarks VALUES (13, 1, 3, 3, 1, 'Smart', 'd', 3);
        """)
        db.commit(); db.close()
        result = self.run_menus("bookmarks", "app:org.mozilla.firefox")
        self.assertEqual([i["args"][0] for i in result["items"]], ["https://bar.example/", "https://menu.example/"])

    def test_chromium_bookmarks(self):
        path = self.home / ".config/chromium/Default"
        path.mkdir(parents=True)
        (path / "Bookmarks").write_text(json.dumps({"roots": {"bookmark_bar": {"children": [
            {"type": "folder", "children": [{"type": "url", "name": "Deep", "url": "https://deep.example/"}]},
            {"type": "url", "name": "Top", "url": "https://top.example/"}]}}}))
        result = self.run_menus("bookmarks", "app:chromium-browser")
        self.assertEqual([i["label"] for i in result["items"]], ["Deep", "Top"])

    def test_recent_files_from_all_three_sources(self):
        import sqlite3
        docs = self.home / "Dokumente"
        docs.mkdir()
        for name in ("notiz.txt", "brief.odt", "tabelle.ods", "mit leer.txt", "geloescht.txt"):
            (docs / name).write_text("x")
        (docs / "geloescht.txt").unlink()
        folder = self.home / ".local/share/kactivitymanagerd/resources"
        folder.mkdir(parents=True)
        db = sqlite3.connect(folder / "database")
        db.execute("CREATE TABLE ResourceScoreCache (usedActivity TEXT, initiatingAgent TEXT, targettedResource TEXT,"
                   " scoreType INTEGER, cachedScore FLOAT, firstUpdate INTEGER, lastUpdate INTEGER)")
        db.execute("INSERT INTO ResourceScoreCache VALUES ('a', 'org.kde.kwrite', ?, 0, 1, 1, 100)", (str(docs / "notiz.txt"),))
        db.execute("INSERT INTO ResourceScoreCache VALUES ('a', 'org.kde.kwrite', ?, 0, 1, 1, 50)", (str(docs / "geloescht.txt"),))
        db.execute("INSERT INTO ResourceScoreCache VALUES ('a', 'org.kde.dolphin', ?, 0, 1, 1, 200)", (str(docs / "brief.odt"),))
        db.commit(); db.close()
        (self.home / ".local/share/recently-used.xbel").write_text(f"""<?xml version="1.0"?>
<xbel version="1.0" xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks"
      xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info">
 <bookmark href="file://{docs}/mit%20leer.txt" modified="2026-10-03T10:00:00Z">
  <info><metadata owner="http://freedesktop.org"><mime:mime-type type="text/plain"/>
   <bookmark:applications><bookmark:application name="KWrite" exec="'kwrite %u'" modified="2026-10-03T10:00:00Z" count="1"/></bookmark:applications>
  </metadata></info>
 </bookmark>
</xbel>""")
        office = self.home / ".config/libreoffice/4/user"
        office.mkdir(parents=True)
        (office / "registrymodifications.xcu").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema">
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="0" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file://{docs}/tabelle.ods</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="1" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file://{docs}/brief.odt</value></prop></node></item>
</oor:items>""")
        kwrite = self.run_menus("recent", "app:org.kde.kwrite")
        self.assertEqual([i["label"] for i in kwrite["items"]], ["mit leer.txt", "notiz.txt"])
        self.assertEqual(kwrite["items"][0]["args"], [str(docs / "mit leer.txt")])
        self.assertEqual([i["label"] for i in self.run_menus("recent", "app:libreoffice-writer")["items"]], ["brief.odt"])
        self.assertEqual([i["label"] for i in self.run_menus("recent", "app:libreoffice-calc")["items"]], ["tabelle.ods"])


class Installer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cde-test-")
        self.home = Path(self.temp.name)
        self.data = self.home / ".local/share"
        self.config = self.home / ".config"
        self.config.mkdir()
        (self.config / "kdeglobals").write_text("[Icons]\nTheme=existing-theme\n")
        tools = self.home / "bin"
        tools.mkdir()
        cache = tools / "kbuildsycoca6"
        cache.write_text("#!/bin/sh\nexit 0\n")
        cache.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "XDG_DATA_HOME": str(self.data),
                    "XDG_CONFIG_HOME": str(self.config), "XDG_CACHE_HOME": str(self.home / ".cache"),
                    "PATH": str(tools) + ":" + os.environ["PATH"]}

    def tearDown(self):
        self.temp.cleanup()

    def command(self, action):
        return subprocess.run([sys.executable, str(ROOT / "manage.py"), action],
                              env=self.env, text=True, capture_output=True)

    def test_round_trip_and_reinstall(self):
        unrelated = self.data / "icons/AnotherTheme/sentinel"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("keep")
        before = (self.config / "kdeglobals").read_bytes()
        for _ in range(2):
            result = self.command("install")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((self.data / "icons/CDECopper/scalable/all/folder.svg").is_file())
            self.assertTrue((self.data / "fonts/CDECopper/IBMPlexSansCondensed-Regular.otf").is_file())
            self.assertTrue((self.config / "Kvantum/CDECopper/CDECopper.kvconfig").is_file())
            self.assertTrue((self.data / "kwin/decorations/kwin4_decoration_qml_cdecopper/contents/ui/main.qml").is_file())
            self.assertTrue((self.data / "kwin/scripts/cde-copper-arrange/contents/code/main.js").is_file())
            self.assertTrue((self.data / "plasma/wallpapers/org.cde.copper.backdrop/contents/images/Copper/Pebbles.png").is_file())
            self.assertEqual(len(list((self.data / "color-schemes").glob("CDE*.colors"))), 38)
            # The palette tool runs from the profile, without the archive.
            tool = self.data / "cde-copper/tool/manage.py"
            listing = subprocess.run([sys.executable, str(tool), "palettes"], env=self.env, text=True, capture_output=True)
            self.assertIn("Broica", listing.stdout, listing.stderr)
            result = self.command("install")
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.command("uninstall")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((self.data / "icons/CDECopper").exists())
            self.assertFalse((self.config / "Kvantum/CDECopper").exists())
            self.assertEqual(unrelated.read_text(), "keep")
            self.assertEqual((self.config / "kdeglobals").read_bytes(), before)

    def test_upgrade_from_0_1_drops_the_svg_decoration(self):
        self.assertEqual(self.command("install").returncode, 0)
        manifest = self.data / "cde-copper-install/manifest.json"
        value = json.loads(manifest.read_text())
        # A 0.1.0 installation: SVG decoration owned, no QML decoration, no script.
        value["targets"] = [t for t in value["targets"] if not t.startswith("kwin/")] + ["aurorae/themes/CDECopper"]
        manifest.write_text(json.dumps(value))
        legacy = self.data / "aurorae/themes/CDECopper"
        legacy.mkdir(parents=True)
        (legacy / "decoration.svg").write_text("<svg/>")
        import shutil as sh
        sh.rmtree(self.data / "kwin")
        result = self.command("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(legacy.exists())
        self.assertNotIn("aurorae/themes/CDECopper", json.loads(manifest.read_text())["targets"])
        self.assertEqual(self.command("uninstall").returncode, 0)
        self.assertFalse((self.data / "kwin/decorations/kwin4_decoration_qml_cdecopper").exists())

    def test_palette_targets_are_owned_and_removed(self):
        self.assertEqual(self.command("install").returncode, 0)
        code = ("import json, manage; m = json.loads(manage.MANIFEST.read_text()); "
                "manage.install_palette(m, 'Lilac'); manage.MANIFEST.write_text(json.dumps(m)); "
                "manage.install_palette(m, 'Desert'); manage.MANIFEST.write_text(json.dumps(m))")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Colour schemes of all palettes are installed; the generated parts of
        # the previous palette go.
        self.assertTrue((self.data / "color-schemes/CDELilac.colors").is_file())
        self.assertFalse((self.data / "plasma/desktoptheme/cde-lilac").exists())
        self.assertFalse((self.config / "Kvantum/CDELilac").exists())
        self.assertTrue((self.data / "plasma/desktoptheme/cde-desert/metadata.json").is_file())
        self.assertTrue((self.config / "Kvantum/CDEDesert/CDEDesert.svg").is_file())
        self.assertEqual(self.command("uninstall").returncode, 0)
        self.assertFalse((self.data / "plasma/desktoptheme/cde-desert").exists())
        self.assertFalse((self.data / "color-schemes/CDEDesert.colors").exists())
        self.assertFalse((self.data / "cde-copper").exists())
        self.assertFalse((self.config / "Kvantum/CDEDesert").exists())

    def test_upgrade_from_0_2_keeps_its_generated_scheme(self):
        self.assertEqual(self.command("install").returncode, 0)
        manifest = self.data / "cde-copper-install/manifest.json"
        value = json.loads(manifest.read_text())
        # 0.2 with Broica applied: its scheme was a palette target.
        value["targets"].remove("color-schemes/CDEBroica.colors")
        value["palette"], value["palette_targets"] = "Broica", ["color-schemes/CDEBroica.colors"]
        manifest.write_text(json.dumps(value))
        result = self.command("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(manifest.read_text())
        self.assertIn("color-schemes/CDEBroica.colors", value["targets"])
        self.assertNotIn("color-schemes/CDEBroica.colors", value["palette_targets"])

    def test_scheme_set_by_a_global_theme_is_found(self):
        # A global theme leaves the scheme only in the defaults layer.
        (self.config / "kdedefaults").mkdir()
        (self.config / "kdedefaults/kdeglobals").write_text("[General]\nColorScheme=CDEBroica\n")
        code = "import manage; print(manage.current_scheme())"
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), "CDEBroica", result.stderr)

    def test_collision_is_not_overwritten(self):
        existing = self.data / "icons/CDECopper"
        existing.mkdir(parents=True)
        (existing / "sentinel").write_text("keep")
        result = self.command("install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unowned", result.stderr)
        self.assertEqual((existing / "sentinel").read_text(), "keep")
        self.assertFalse((self.data / "cde-copper-install").exists())

    def test_unexpected_manifest_target_is_rejected(self):
        self.assertEqual(self.command("install").returncode, 0)
        manifest = self.data / "cde-copper-install/manifest.json"
        value = json.loads(manifest.read_text())
        value["targets"].append("../unrelated")
        manifest.write_text(json.dumps(value))
        result = self.command("uninstall")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.data / "icons/CDECopper").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
