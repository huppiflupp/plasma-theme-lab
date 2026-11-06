#!/usr/bin/env python3
"""Update the translation template and the catalogs, from CDE/.

    python3 po/update.py            # rewrite po/cde-copper.pot and po/*.po
    python3 po/update.py --check    # only report messages that would be lost

xgettext finds the literal i18nd() calls of the QML and JavaScript. It cannot
see messages looked up by a variable, such as backdrop names and picture titles
from the Python generators or the labels in main.xml. Those live in
po/names.pot, by hand; a catalog merged without them loses their translations.
"""
import ast
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PO = ROOT / "po"
SOURCES = ("frontpanel/contents/ui/*.qml", "frontpanel/contents/ui/launch.js", "frontpanel/contents/config/config.qml",
           "backdrop/contents/ui/config.qml", "lookandfeel/contents/splash/Splash.qml",
           "lookandfeel/contents/logout/Logout.qml", "shell/contents/lockscreen/LockScreen.qml",
           "stylemanager/contents/ui/*.qml")


def version():
    return re.search(r'^VERSION = "(.+)"', (ROOT / "build.py").read_text(), re.M).group(1)


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True, stderr=subprocess.DEVNULL)


def template(output):
    """The extracted messages together with the hand-kept ones."""
    with tempfile.TemporaryDirectory(prefix="cde-po-") as temp:
        extracted = Path(temp) / "extracted.pot"
        files = sorted(str(path.relative_to(ROOT)) for pattern in SOURCES for path in ROOT.glob(pattern))
        run("xgettext", "-C", "--from-code=UTF-8", "-k", "-ki18nd:2", "-ki18ndc:2c,3", "-ki18ndp:2,3", "-kI18N_NOOP:1",
            "--flag=i18nd:2:kde-format", "--flag=i18ndp:2:kde-format", "--flag=i18ndp:3:kde-format",
            "--package-name=cde-copper", f"--package-version={version()}", "-o", str(extracted), *files)
        run("msgcat", "--use-first", "-o", str(output), str(extracted), str(PO / "names.pot"))


def messages(path):
    """The msgids of a catalog, without the obsolete ones."""
    text = Path(path).read_text(encoding="utf-8")
    ids, entry = set(), None
    for line in text.splitlines() + [""]:
        if line.startswith("msgid "):
            entry = ast.literal_eval(line[6:])
        elif line.startswith('"') and entry is not None:
            entry += ast.literal_eval(line)
        elif entry is not None:
            if entry:
                ids.add(entry)
            entry = None
    return ids


def main():
    with tempfile.TemporaryDirectory(prefix="cde-po-") as temp:
        fresh = Path(temp) / "fresh.pot"
        template(fresh)
        known = messages(fresh)
        lost = {catalog.name: messages(catalog) - known for catalog in PO.glob("*.po")}
        if "--check" in sys.argv:
            for name, ids in lost.items():
                for message in sorted(ids):
                    print(f"{name}: would lose {message!r}")
            return 1 if any(lost.values()) else 0
        (PO / "cde-copper.pot").write_text(fresh.read_text(encoding="utf-8"), encoding="utf-8")
    for catalog in PO.glob("*.po"):
        run("msgmerge", "--quiet", "--update", "--backup=none", str(catalog), str(PO / "cde-copper.pot"))
        run("msgattrib", "--no-obsolete", "-o", str(catalog), str(catalog))
    return 0


if __name__ == "__main__":
    sys.exit(main())
