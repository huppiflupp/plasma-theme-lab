#!/usr/bin/env python3
"""Build RISC Legacy's icon themes from the kit (DESIGN.md §8).

For each colour world (ro4 -> RiscLegacy, ro5 -> RiscLegacy2026) every
meaning Breeze has (names.py) that a family module draws is written as
scalable/<category>/<name>.svg (large) and 16/<category> and
22/<category> (small); Breeze's synonyms become symlinks. What no module
draws yet falls through to Breeze (Inherits).

Checks, printed at the end and returned:
  coverage    drawn / meanings per category
  duplicates  two meanings whose large drawings are identical (ids aside):
              the user's rule, no picture twice

    build_icons.py OUTDIR [--sheet DIR] [--world ro4|ro5]
"""
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import names as namesmod  # noqa: E402
from kit import Canvas  # noqa: E402

LARGE_SIZES = (24, 32, 48, 64, 96, 128, 256)
# The freedesktop context per category, spelled as the spec (and Breeze):
# an unknown one ("Mimetypes", "Apps") made KIconLoader skip the folder
# and fall back to Breeze (VM, 25.10.2026).
CONTEXTS = {"places": "Places", "devices": "Devices", "mimetypes": "MimeTypes", "categories": "Categories",
            "emblems": "Emblems", "apps": "Applications", "preferences": "Applications", "status": "Status",
            "emotes": "Emotes", "actions": "Actions"}
THEMES = {"ro4": ("RiscLegacy", "RISC OS 4's icons, drawn anew for RISC Legacy"),
          "ro5": ("RiscLegacy2026", "RISC OS 5's icons, drawn anew for RISC Legacy 2026")}


def modules():
    import importlib
    mods = []
    # places.py, then every family module fam_*.py (one per category or
    # part of one, see README.md).
    # A module another agent is still writing may not import yet: it is
    # reported and left out, the rest builds.
    for m in ["places"] + sorted(p.stem for p in HERE.glob("fam_*.py")):
        try:
            mods.append(importlib.import_module(m))
        except Exception as e:  # noqa: BLE001
            print(f"  (module {m} left out: {type(e).__name__}: {e})", file=sys.stderr)
    return mods


def category_of(module):
    """The category a module draws, from its file name: places, fam_devices
    -> devices, fam_actions_af -> actions. A module asked only for names of
    its own category cannot take another's (devices took status's wireless
    strengths, 25.10.2026)."""
    stem = module.__name__
    return stem.split("_")[1] if stem.startswith("fam_") else stem


def render(name, world, small, mods, category=None):
    """The first module of the name's category that draws it; failing that
    (a name Breeze files elsewhere than its module expected), any module."""
    for own in ((True, False) if category else (False,)):
        for m in mods:
            if own and category_of(m) != category:
                continue
            c = Canvas(world, small)
            try:
                ok = m.draw(name, c)
            except Exception as e:  # noqa: BLE001
                print(f"  ERROR {m.__name__}.draw({name!r}): {type(e).__name__}: {e}", file=sys.stderr)
                continue
            if ok:
                return c.svg()
    return None


def fingerprint(svg):
    return hashlib.sha1(re.sub(r"\bi\d+g\d+\b", "G", svg).encode()).hexdigest()


def build(out, worlds=("ro4", "ro5"), report=True, only=None):
    table = namesmod.names()
    if only:
        table = {k: v for k, v in table.items() if k == only}
    mods = modules()
    result = {}
    for world in worlds:
        theme, comment = THEMES[world]
        base = Path(out) / theme
        dirs = []
        coverage = {}
        prints = defaultdict(list)
        small_prints = defaultdict(list)
        for cat, meanings in table.items():
            drawn = 0
            for name, synonyms in meanings.items():
                large = render(name, world, False, mods, cat)
                if large is None:
                    continue
                small = render(name, world, True, mods, cat)
                drawn += 1
                prints[fingerprint(large)].append(name)
                small_prints[fingerprint(small)].append(name)
                for sub, svg in (("scalable", large), ("16", small)):
                    d = base / sub / cat
                    d.mkdir(parents=True, exist_ok=True)
                    (d / f"{name}.svg").write_text(svg)
                    for s in synonyms:
                        link = d / f"{s}.svg"
                        if not link.exists():
                            link.symlink_to(f"{name}.svg")
            # Fixed sizes as links to the scalable drawings: KIconLoader
            # looks for an exact size through the whole theme chain before
            # it takes a scalable folder, so Breeze's 32 px won over ours
            # (Dolphin, VM 25.10.2026). 22 is the same small drawing as 16.
            # One link per folder, not per file: 69,000 file links made
            # kpackagetool (the store's "Get New…") take over a quarter of
            # an hour to unpack the release archive (VM, 26.10.2026).
            if drawn:
                for size, to in [("22", "16")] + [(str(s), "scalable") for s in LARGE_SIZES]:
                    d = base / size / cat
                    d.parent.mkdir(parents=True, exist_ok=True)
                    if not d.is_symlink():
                        d.symlink_to(f"../{to}/{cat}")
            coverage[cat] = (drawn, len(meanings))
            if drawn:
                dirs += [(f"16/{cat}", 16, "Fixed"), (f"22/{cat}", 22, "Fixed")]
                dirs += [(f"{s}/{cat}", s, "Fixed") for s in LARGE_SIZES]
                dirs += [(f"scalable/{cat}", 48, "Scalable")]
        lines = ["[Icon Theme]", f"Name={theme}", f"Comment={comment}",
                 "Inherits=breeze,hicolor", "Directories=" + ",".join(d for d, _, _ in dirs), ""]
        for d, size, kind in dirs:
            lines += [f"[{d}]", f"Size={size}", f"Type={kind}", f"Context={CONTEXTS[d.split('/')[1]]}"]
            if kind == "Scalable":
                lines += ["MinSize=24", "MaxSize=512"]
            lines.append("")
        base.mkdir(parents=True, exist_ok=True)
        (base / "index.theme").write_text("\n".join(lines))
        dups = [v for v in prints.values() if len(v) > 1]
        # The 16/22 px drawings too: without text, formats told apart only by
        # their band's word came out alike (mimetypes, 25.10.2026).
        small_dups = [v for v in small_prints.values() if len(v) > 1]
        result[world] = (coverage, dups + small_dups)
        if report:
            total = sum(a for a, _ in coverage.values()), sum(b for _, b in coverage.values())
            print(f"{theme}: {total[0]}/{total[1]} drawn; " +
                  ", ".join(f"{k} {a}/{b}" for k, (a, b) in coverage.items() if a))
            for d in dups:
                print("  DUPLICATE:", " = ".join(d))
            for d in small_dups:
                print("  DUPLICATE (small):", " = ".join(d))
    return result


def sheet(out_png, world, category, mods=None, prefix="", start=0, count=100):
    """Drawings of a category at 22 (small), 48 and 96 px, rendered by QtSvg:
    those whose name starts with prefix, at most count from start."""
    from PySide6.QtCore import QByteArray, QRectF
    from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    app = QGuiApplication.instance() or QGuiApplication(["x", "-platform", "offscreen"])  # noqa: F841
    mods = mods or modules()
    items = [n for n in namesmod.names()[category] if n.startswith(prefix) and render(n, world, False, mods)]
    items = items[start:start + count]
    cell, cols = 150, 10
    img = QImage(cols * cell, max(1, (len(items) + cols - 1) // cols) * 130, QImage.Format_ARGB32)
    img.fill(QColor("#e4e4de" if world == "ro5" else "#dddddd"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    for i, n in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * 130
        QSvgRenderer(QByteArray(render(n, world, True, mods).encode())).render(p, QRectF(x + 4, y + 82, 22, 22))
        QSvgRenderer(QByteArray(render(n, world, False, mods).encode())).render(p, QRectF(x + 30, y + 56, 48, 48))
        QSvgRenderer(QByteArray(render(n, world, False, mods).encode())).render(p, QRectF(x + 52, y + 2, 96, 96))
        p.setPen(QColor("#222222"))
        p.setFont(QFont("Sans", 7))
        p.drawText(x + 4, y + 120, n[:28])
    p.end()
    img.save(out_png)
    print(out_png, len(items))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--sheet":
        # --sheet OUT.png WORLD CATEGORY [PREFIX [START [COUNT]]]
        sheet(args[1], args[2], args[3], prefix=args[4] if len(args) > 4 else "",
              start=int(args[5]) if len(args) > 5 else 0, count=int(args[6]) if len(args) > 6 else 100)
    else:
        # OUTDIR [--only CATEGORY]
        build(args[0], only=args[args.index("--only") + 1] if "--only" in args else None)
