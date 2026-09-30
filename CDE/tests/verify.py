#!/usr/bin/env python3
"""Run in the lab VM after build.py; no changes to the active desktop."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
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
            self.assertEqual(doc.get("viewBox"), "0 0 64 64")
            self.assertFalse(any(e.tag.endswith("image") for e in doc.iter()), str(file))
        for file in (ROOT / "build").rglob("*.svg"):
            ET.parse(file)


class Separation(unittest.TestCase):
    """CDE Copper must build from its own directory alone.

    The theme shares a repository with NT Legacy, but neither may influence
    the other. A copy of CDE/ placed somewhere with no sibling tools/ has to
    rebuild build/ byte for byte from CDE/tools/."""

    def test_build_is_self_contained_and_reproducible(self):
        with tempfile.TemporaryDirectory(prefix="cde-copy-") as temp:
            copy = Path(temp) / "island/CDE"
            copy.mkdir(parents=True)
            for item in ("tools", "frontpanel", "build.py", "icons.py", "layout.js"):
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

    def test_no_reference_to_sibling_themes(self):
        for name in ("build.py", "icons.py", "manage.py", "package.py", "install.sh",
                     "apply.sh", "uninstall.sh"):
            text = (ROOT / name).read_text()
            self.assertNotIn("ROOT.parent", text, name)
            self.assertNotIn("../tools", text, name)
            self.assertNotIn("nt-legacy", text, name)


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
            result = self.command("install")
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.command("uninstall")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((self.data / "icons/CDECopper").exists())
            self.assertEqual(unrelated.read_text(), "keep")
            self.assertEqual((self.config / "kdeglobals").read_bytes(), before)

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
