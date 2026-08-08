#!/usr/bin/env python3
"""Erzeugt die Werkzeugleisten-Symbole, die ReactOS nicht liefert.

ReactOS hat die Shell-Symbole (Ordner, Laufwerke, Papierkorb), aber keine
verwertbaren Werkzeugleisten-Symbole: Kopieren, Einfuegen, Zurueck,
Ansichtsmodi. Die liegen dort als Bitmap-Streifen in Programmressourcen
oder gar nicht vor.

Weil genau diese Symbole in Dolphin und PCManFM-Qt staendig sichtbar sind
und ohne sie der Breeze-Rueckfall greift - flache graue Striche neben
Pixelart - werden sie hier selbst erzeugt. Das hat drei Vorteile: es ist
lizenzrein (Eigenerzeugnis unter der Theme-Lizenz), stilistisch
kontrollierbar, und die Farben kommen aus derselben Palette wie der Rest.

    ./gen-icons-aktionen.py <icon-theme-verzeichnis>
    ./gen-icons-aktionen.py <verz> --palette desert

Gezeichnet wird bewusst grob: 16 px sind 16 px. Feine Linien verschwinden
beim Skalieren, deshalb liegen alle Formen auf ganzen Pixeln und die
Strichstaerke waechst mit der Groesse.
"""

import argparse
import subprocess
from pathlib import Path

GROESSEN = (16, 22, 32, 48)

PALETTEN = {
    "teal":   {"linie": "#202628", "flaeche": "#D8D8D0", "hell": "#F0F0E8",
               "akzent": "#287F8C", "warn": "#C87922", "gut": "#39734A",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
    "desert": {"linie": "#2A2620", "flaeche": "#D8D0C0", "hell": "#F0EADC",
               "akzent": "#8C6A28", "warn": "#C87922", "gut": "#5A6B32",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
    "lilac":  {"linie": "#252230", "flaeche": "#D8D8D0", "hell": "#F0F0E8",
               "akzent": "#6A5A8C", "warn": "#C87922", "gut": "#39734A",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
}


class Zeichner:
    """Zeichnet auf einem 32x32-Raster; die Ausgabe wird skaliert."""

    def __init__(self, p):
        self.p = p

    # -- Bausteine ------------------------------------------------------
    def blatt(self, x=8, y=4, b=16, h=24, farbe=None):
        """Ein Dokument mit umgeknickter Ecke - die Grundform vieler
        Datei-Symbole."""
        f = farbe or self.p["papier"]
        knick = 6
        return (f'<path d="M{x},{y} h{b-knick} l{knick},{knick} v{h-knick} '
                f'h{-b} z" fill="{f}" stroke="{self.p["linie"]}" '
                f'stroke-width="1.5"/>'
                f'<path d="M{x+b-knick},{y} v{knick} h{knick} z" '
                f'fill="{self.p["flaeche"]}" stroke="{self.p["linie"]}" '
                f'stroke-width="1.5"/>')

    def zeilen(self, x=11, y=13, b=10, n=3, farbe=None):
        f = farbe or self.p["linie"]
        return "".join(
            f'<rect x="{x}" y="{y + i*4}" width="{b}" height="1.5" fill="{f}"/>'
            for i in range(n))

    def pfeil(self, richtung, farbe=None, mx=16, my=16, gr=9):
        """Ein massives Dreieck. Bei 16 px ist alles andere Matsch."""
        f = farbe or self.p["akzent"]
        pkt = {
            "links":  f"{mx-gr},{my} {mx+gr//2},{my-gr} {mx+gr//2},{my+gr}",
            "rechts": f"{mx+gr},{my} {mx-gr//2},{my-gr} {mx-gr//2},{my+gr}",
            "hoch":   f"{mx},{my-gr} {mx-gr},{my+gr//2} {mx+gr},{my+gr//2}",
            "runter": f"{mx},{my+gr} {mx-gr},{my-gr//2} {mx+gr},{my-gr//2}",
        }[richtung]
        return (f'<polygon points="{pkt}" fill="{f}" '
                f'stroke="{self.p["linie"]}" stroke-width="1.2" '
                f'stroke-linejoin="round"/>')

    def ordner(self, x=3, y=8, b=26, h=18, farbe=None):
        f = farbe or self.p["gold"]
        return (f'<path d="M{x},{y+4} v{h-4} h{b} v{-h+2} h{-b//2} '
                f'l-3,-3 h{-b//2+3} z" fill="{f}" '
                f'stroke="{self.p["linie"]}" stroke-width="1.5" '
                f'stroke-linejoin="round"/>')

    def lupe(self, cx=14, cy=14, r=7):
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{self.p["hell"]}" '
                f'stroke="{self.p["linie"]}" stroke-width="2"/>'
                f'<line x1="{cx+r-1}" y1="{cy+r-1}" x2="{cx+r+7}" '
                f'y2="{cy+r+7}" stroke="{self.p["linie"]}" stroke-width="3" '
                f'stroke-linecap="round"/>')

    def kreuz(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["linie"]
        return (f'<line x1="{cx-r}" y1="{cy-r}" x2="{cx+r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<line x1="{cx+r}" y1="{cy-r}" x2="{cx-r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>')

    def plus(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["gut"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>'
                f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def minus(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["warn"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def kasten(self, x, y, b, h, farbe=None, rand=None):
        return (f'<rect x="{x}" y="{y}" width="{b}" height="{h}" '
                f'fill="{farbe or self.p["hell"]}" '
                f'stroke="{rand or self.p["linie"]}" stroke-width="1.5"/>')


def symbole(z: Zeichner):
    """Name -> SVG-Inhalt. Die Namen sind die, die Dolphin und
    PCManFM-Qt tatsaechlich anfordern."""
    p = z.p
    s = {}

    # --- Navigation
    s["go-previous"] = z.pfeil("links")
    s["go-next"] = z.pfeil("rechts")
    s["go-up"] = z.pfeil("hoch")
    s["go-down"] = z.pfeil("runter")
    s["go-parent-folder"] = z.pfeil("hoch")
    s["go-home"] = (z.ordner(farbe=p["gold"]) +
                    f'<path d="M16,6 l9,8 h-4 v7 h-10 v-7 h-4 z" '
                    f'fill="{p["hell"]}" stroke="{p["linie"]}" '
                    f'stroke-width="1.5" stroke-linejoin="round"/>')

    # --- Ansichtsmodi: die auffaelligste Luecke in Dolphins Leiste
    s["view-list-icons"] = "".join(
        z.kasten(4 + sp * 12, 4 + ze * 12, 9, 9, p["akzent"])
        for ze in range(2) for sp in range(2))
    s["view-list-details"] = (
        "".join(z.kasten(4, 5 + i * 8, 6, 5, p["akzent"]) for i in range(3)) +
        "".join(f'<rect x="13" y="{6 + i*8}" width="15" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-list-text"] = s["view-list-details"]
    s["view-list-tree"] = (
        f'<line x1="7" y1="5" x2="7" y2="26" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>' +
        "".join(f'<line x1="7" y1="{9 + i*8}" x2="13" y2="{9 + i*8}" '
                f'stroke="{p["linie"]}" stroke-width="1.5"/>'
                f'<rect x="14" y="{6 + i*8}" width="13" height="6" '
                f'fill="{p["akzent"]}" stroke="{p["linie"]}" '
                f'stroke-width="1"/>' for i in range(3)))
    s["view-file-columns"] = "".join(
        z.kasten(4 + i * 9, 5, 7, 22, p["akzent"] if i == 0 else p["hell"])
        for i in range(3))
    s["view-preview"] = z.blatt() + z.lupe(cx=20, cy=20, r=6)
    s["view-sort-ascending"] = (
        z.pfeil("hoch", mx=8, my=16, gr=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{6 + i*4}" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-sort-descending"] = (
        z.pfeil("runter", mx=8, my=16, gr=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{14 - i*4}" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-sort"] = s["view-sort-ascending"]
    s["view-refresh"] = (
        f'<path d="M25,16 a9,9 0 1 1 -3,-6.7" fill="none" '
        f'stroke="{p["gut"]}" stroke-width="3.5"/>'
        f'<polygon points="26,4 26,13 17,10" fill="{p["gut"]}"/>')
    s["view-hidden"] = z.blatt() + z.kreuz(cx=20, cy=22, r=5, farbe=p["warn"])
    s["view-visible"] = z.blatt() + z.lupe(cx=20, cy=20, r=6)

    # --- Bearbeiten
    s["edit-copy"] = (z.blatt(x=4, y=3, b=14, h=20) +
                      z.blatt(x=13, y=9, b=14, h=20))
    s["edit-cut"] = (
        f'<line x1="9" y1="4" x2="21" y2="22" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<line x1="23" y1="4" x2="11" y2="22" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="9" cy="25" r="4" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="23" cy="25" r="4" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')
    s["edit-paste"] = (
        z.kasten(6, 5, 20, 24, p["gold"]) +
        z.kasten(10, 2, 12, 6, p["flaeche"]) +
        z.kasten(10, 12, 12, 14, p["papier"]))
    s["edit-delete"] = z.blatt() + z.kreuz(cx=21, cy=22, r=6, farbe="#A83232")
    s["edit-rename"] = (
        z.blatt() +
        f'<path d="M18,22 l7,-7 3,3 -7,7 -4,1 z" fill="{p["gold"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.2"/>')
    s["edit-find"] = z.lupe()
    s["edit-clear"] = z.kreuz(farbe=p["warn"])
    s["edit-undo"] = (
        f'<path d="M8,18 a9,9 0 1 1 9,9" fill="none" stroke="{p["akzent"]}" '
        f'stroke-width="3.5"/><polygon points="3,17 13,17 8,25" '
        f'fill="{p["akzent"]}"/>')
    s["edit-redo"] = (
        f'<path d="M24,18 a9,9 0 1 0 -9,9" fill="none" stroke="{p["akzent"]}" '
        f'stroke-width="3.5"/><polygon points="29,17 19,17 24,25" '
        f'fill="{p["akzent"]}"/>')
    s["edit-select-all"] = (
        f'<rect x="4" y="4" width="24" height="24" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-dasharray="3,2"/>' +
        z.kasten(9, 9, 14, 14, p["akzent"]))

    # --- Dateien
    s["document-new"] = z.blatt() + z.plus(cx=22, cy=22, r=5)
    s["document-open"] = z.ordner(farbe=p["gold"])
    s["document-save"] = (
        z.kasten(4, 4, 24, 24, p["akzent"]) +
        z.kasten(10, 4, 12, 9, p["flaeche"]) +
        z.kasten(8, 18, 16, 10, p["hell"]))
    s["document-properties"] = z.blatt() + z.lupe(cx=21, cy=21, r=5)
    s["folder-new"] = z.ordner() + z.plus(cx=23, cy=21, r=5)
    s["list-add"] = z.plus()
    s["list-remove"] = z.minus()

    # --- Zoom
    s["zoom-in"] = z.lupe() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="2.5"/><line x1="14" y1="10" x2="14" y2="18" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')
    s["zoom-out"] = z.lupe() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="2.5"/>')
    s["zoom-original"] = z.lupe()
    s["zoom-fit-best"] = z.lupe() + (
        f'<rect x="10" y="10" width="8" height="8" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')

    # --- Fenster und Dialoge
    s["window-close"] = z.kreuz(farbe="#A83232")
    s["dialog-close"] = s["window-close"]
    s["dialog-ok"] = (
        f'<polyline points="6,17 13,24 26,8" fill="none" '
        f'stroke="{p["gut"]}" stroke-width="4" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    s["dialog-cancel"] = z.kreuz(farbe="#A83232")
    s["tab-new"] = z.kasten(4, 8, 24, 20, p["hell"]) + z.plus(cx=16, cy=18, r=5)
    s["tab-close"] = z.kasten(4, 8, 24, 20, p["hell"]) + z.kreuz(cx=16, cy=18, r=5)

    # --- Menue und Einstellungen
    s["application-menu"] = "".join(
        f'<rect x="6" y="{7 + i*7}" width="20" height="3.5" '
        f'fill="{p["linie"]}"/>' for i in range(3))
    s["open-menu"] = s["application-menu"]
    s["show-menu"] = s["application-menu"]
    s["configure"] = (
        f'<circle cx="16" cy="16" r="6" fill="{p["flaeche"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>' +
        "".join(f'<rect x="15" y="2" width="2.5" height="6" '
                f'fill="{p["linie"]}" transform="rotate({a},16,16)"/>'
                for a in range(0, 360, 45)))
    s["settings-configure"] = s["configure"]
    s["configure-toolbars"] = s["configure"]

    # --- Sonstiges aus Dolphins Leiste
    s["view-split-left-right"] = (
        z.kasten(3, 6, 12, 20, p["hell"]) + z.kasten(17, 6, 12, 20, p["akzent"]))
    s["swap-panels"] = (z.pfeil("rechts", mx=16, my=10, gr=7) +
                        z.pfeil("links", mx=16, my=22, gr=7))
    s["view-filter"] = (
        f'<polygon points="4,5 28,5 19,16 19,27 13,23 13,16" '
        f'fill="{p["akzent"]}" stroke="{p["linie"]}" stroke-width="1.5" '
        f'stroke-linejoin="round"/>')
    s["object-locked"] = (
        z.kasten(8, 14, 16, 14, p["gold"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0 v4" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')
    s["object-unlocked"] = (
        z.kasten(8, 14, 16, 14, p["hell"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')

    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--palette", default="teal", choices=sorted(PALETTEN))
    ap.add_argument("--kontext", default="actions")
    args = ap.parse_args()

    z = Zeichner(PALETTEN[args.palette])
    alle = symbole(z)
    geschrieben = 0

    for name, inhalt in alle.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" '
               f'height="32" viewBox="0 0 32 32">\n'
               f'  <!-- Erzeugt von tools/gen-icons-aktionen.py -->\n'
               f'  {inhalt}\n</svg>\n')
        for g in GROESSEN:
            ziel = args.theme / args.kontext / str(g) / f"{name}.png"
            ziel.parent.mkdir(parents=True, exist_ok=True)
            tmp = ziel.with_suffix(".svg")
            tmp.write_text(svg)
            try:
                subprocess.run(
                    ["magick", "-background", "none", "-density",
                     str(int(g * 96 / 32)), str(tmp), "-resize", f"{g}x{g}",
                     str(ziel)], check=True, capture_output=True)
                geschrieben += 1
            except subprocess.CalledProcessError as e:
                print(f"  {name} {g}px: {e.stderr.decode()[:80]}")
            finally:
                tmp.unlink(missing_ok=True)

    print(f"  {len(alle)} Symbole, {geschrieben} Dateien "
          f"({args.palette}) nach {args.theme}/{args.kontext}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
