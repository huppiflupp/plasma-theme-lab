#!/usr/bin/env python3
"""Findet Symbolnamen, die das System anfordert und unser Satz nicht hat.

Das Gegenstueck zu pruefe-symbolfalle.py. Jenes sucht Namen, die wir
FALSCH bedienen; dieses sucht Namen, die wir GAR NICHT bedienen - und
sortiert sie danach, wie oft das System sie ueberhaupt verlangt.

Woher der Bedarf kommt, in dieser Reihenfolge:

  1. Icon= aus allen installierten .desktop-Dateien. Das sind die
     Programmsymbole - jedes fehlende ist im Startmenue sichtbar.
  2. Zeichenketten aus den Programmen und KF6-Bibliotheken selbst.
     Derselbe Weg, auf dem die Zuordnungen in gen-icon-aliase.py
     entstanden sind: ein Icon-Name steht im Quelltext als Literal und
     ueberlebt das Uebersetzen.

Beides zusammen ergibt viel Rauschen - jede beliebige Zeichenkette sieht
aus wie ein Symbolname. Deshalb der Filter: Es zaehlt nur, was auch in
Breeze liegt. Breeze ist der Satz, gegen den Plasma entwickelt wird; was
dort keinen Namen hat, fordert auch niemand an.

Mit --vergleich laesst sich ein zweiter Satz danebenlegen. Dann steht in
der letzten Spalte, ob es dort eine Vorlage gibt:

    ./luecken-symbole.py nt-legacy/icons-nt/NTLegacyIcons \\
        --vergleich nt-legacy/icons/NTLegacySE98

Der Vergleichssatz ist ausdruecklich NUR Vorlage. Fremdmaterial wandert
nicht in den eigenen Satz - warum, steht in nt-legacy/ATTRIBUTION.md.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

BREEZE = Path("/usr/share/icons/breeze")

# Wo nach Zeichenketten gesucht wird. Kein rekursives /usr/bin: das
# dauert Minuten und bringt Namen aus Programmen, die niemand hat.
BINAERE = [
    "/usr/bin/dolphin", "/usr/bin/plasmashell", "/usr/bin/systemsettings",
    "/usr/bin/kate", "/usr/bin/konsole", "/usr/bin/ark", "/usr/bin/gwenview",
    "/usr/bin/okular", "/usr/bin/kwin_wayland", "/usr/bin/kwin_x11",
    "/usr/bin/kinfocenter", "/usr/bin/kcalc", "/usr/bin/spectacle",
    "/usr/bin/discover", "/usr/bin/kwrite", "/usr/bin/krunner",
]
BIB_MUSTER = ["libKF6*.so*", "libplasma*.so*", "libkworkspace*.so*",
              "libPlasma*.so*"]
BIB_ORTE = ["/usr/lib64", "/usr/lib", "/usr/lib/x86_64-linux-gnu"]

DESKTOP_ORTE = ["/usr/share/applications", "/usr/local/share/applications"]

# Ein Symbolname: klein, Ziffern und Bindestriche erlaubt, kein Pfad.
# Die Laengengrenze haelt Einzelbuchstaben und Romane heraus.
NAME = re.compile(rb"[a-z][a-z0-9]{1,40}(?:[-.+][a-z0-9]+){0,6}")


def zeichenketten(pfad: Path, mindestens=4):
    """Druckbare ASCII-Folgen aus einer Datei - wie strings(1).

    Selbst gemacht statt binutils aufzurufen: das Werkzeug soll auch auf
    einem System laufen, auf dem binutils nicht installiert ist.
    """
    try:
        roh = pfad.read_bytes()
    except OSError:
        return
    for treffer in re.finditer(rb"[\x20-\x7e]{%d,}" % mindestens, roh):
        yield treffer.group(0)


def breeze_bestand():
    """Symbolname -> Kontext, aus dem Breeze-Baum gelesen.

    Der Kontext ist das Verzeichnis unterhalb der Groesse
    (breeze/actions/22/foo.svg -> actions). Er sagt spaeter, wohin ein
    fehlendes Symbol in gen-icons.py gehoert.
    """
    bestand = {}
    if not BREEZE.is_dir():
        return bestand
    for f in BREEZE.rglob("*"):
        if f.suffix not in (".svg", ".svgz", ".png"):
            continue
        teile = f.relative_to(BREEZE).parts
        if len(teile) < 2:
            continue
        # Breeze legt <kontext>/<groesse>/name.svg ab, teils auch
        # <kontext>/<groesse>/<unterordner>/name.svg.
        bestand.setdefault(f.name.rsplit(".", 1)[0], teile[0])
    return bestand


def eigener_bestand(theme: Path):
    """Alle Namen eines Themes, Verweise eingeschlossen.

    Ein Symlink zaehlt als vorhanden: Fuer den Icon-Loader ist er ein
    Treffer, und genau darum geht es hier.
    """
    namen = set()
    for f in theme.rglob("*"):
        if f.is_dir():
            continue
        if f.name.rsplit(".", 1)[-1] not in ("svg", "svgz", "png", "xpm"):
            continue
        namen.add(f.name.rsplit(".", 1)[0])
    return namen


def bedarf_aus_desktop():
    """Icon= aus den installierten .desktop-Dateien."""
    zaehler = Counter()
    for ort in DESKTOP_ORTE:
        p = Path(ort)
        if not p.is_dir():
            continue
        for f in p.glob("*.desktop"):
            try:
                for zeile in f.read_text(errors="replace").splitlines():
                    if zeile.startswith("Icon="):
                        wert = zeile[5:].strip()
                        # Absolute Pfade sind kein Themen-Symbol.
                        if wert and "/" not in wert:
                            zaehler[wert] += 1
                        break
            except OSError:
                continue
    return zaehler


def bedarf_aus_binaeren(dateien):
    """Zusammengesetzte Symbolnamen aus Programmen und Bibliotheken.

    Nur zusammengesetzte, und das ist der entscheidende Filter. Der
    erste Versuch nahm jede Zeichenkette, die in Breeze einen Namen
    hat - oben standen dann class, node, item, label, flag, user. Das
    sind Woerter aus dem Quelltext, die Breeze zufaellig auch als Symbol
    fuehrt; angefordert wird davon keines.

    Ein echter Symbolname im Programmtext hat fast immer einen
    Bindestrich (document-open, view-list-icons, dialog-password). Die
    einwortigen Ausnahmen sind Programmnamen - okular, kmail, ark - und
    die stehen ohnehin in den .desktop-Dateien, wo sie belastbar sind.
    """
    zaehler = Counter()
    for pfad in dateien:
        gesehen = set()
        for s in zeichenketten(pfad):
            for m in NAME.finditer(s):
                name = m.group(0).decode()
                if "-" in name:
                    gesehen.add(name)
        # Je Datei nur einmal zaehlen - sonst gewinnt, was oft im
        # Uebersetzungspuffer steht, nicht was oft gebraucht wird.
        zaehler.update(gesehen)
    return zaehler


def sammle_dateien():
    dateien = [Path(b) for b in BINAERE if Path(b).is_file()]
    for ort in BIB_ORTE:
        p = Path(ort)
        if not p.is_dir():
            continue
        for muster in BIB_MUSTER:
            for f in p.glob(muster):
                if f.is_file() and not f.is_symlink():
                    dateien.append(f)
    return dateien


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path, help="der eigene Symbolsatz")
    ap.add_argument("--vergleich", type=Path,
                    help="zweiter Satz, nur als Vorlagen-Hinweis")
    ap.add_argument("--zahl", type=int, default=60,
                    help="wie viele Zeilen (Vorgabe 60, 0 = alle)")
    ap.add_argument("--nur-vorlagen", action="store_true",
                    help="nur Namen, fuer die --vergleich etwas hat")
    args = ap.parse_args()

    if not (args.theme / "index.theme").is_file():
        ap.error(f"{args.theme} ist kein Icon-Theme (index.theme fehlt)")
    if not BREEZE.is_dir():
        print(f"FEHLER: {BREEZE} fehlt - ohne Breeze kein Massstab.",
              file=sys.stderr)
        return 1

    breeze = breeze_bestand()
    eigen = eigener_bestand(args.theme)
    vergleich = eigener_bestand(args.vergleich) if args.vergleich else set()

    dateien = sammle_dateien()
    zaehler = bedarf_aus_binaeren(dateien)
    # Ein Eintrag im Startmenue wiegt schwerer als eine Zeichenkette
    # irgendwo im Programm: dort ist das fehlende Symbol sofort sichtbar.
    for name, n in bedarf_aus_desktop().items():
        zaehler[name] += 5 * n

    # Der Filter, ohne den nur Rauschen herauskaeme.
    luecken = [(n, z) for n, z in zaehler.items()
               if n in breeze and n not in eigen]
    if args.nur_vorlagen:
        luecken = [(n, z) for n, z in luecken if n in vergleich]
    luecken.sort(key=lambda t: (-t[1], t[0]))

    print(f"Gepruefte Dateien: {len(dateien)} "
          f"({sum(1 for d in dateien if d.parent.name == 'bin')} Programme, "
          f"{sum(1 for d in dateien if d.parent.name != 'bin')} Bibliotheken)")
    print(f"Breeze kennt {len(breeze)} Namen, "
          f"{args.theme.name} hat {len(eigen)}.")
    if args.vergleich:
        print(f"{args.vergleich.name} hat {len(vergleich)}.")
    print(f"\nAngefordert, in Breeze vorhanden, bei uns nicht: "
          f"{len(luecken)}\n")

    kopf = f"{'Symbolname':<40} {'Kontext':<12} {'Gewicht':>7}"
    if args.vergleich:
        kopf += "  Vorlage"
    print(kopf)
    print("-" * len(kopf))

    for name, gewicht in (luecken if args.zahl == 0 else luecken[:args.zahl]):
        zeile = f"{name:<40} {breeze[name]:<12} {gewicht:>7}"
        if args.vergleich:
            zeile += "  " + ("ja" if name in vergleich else "-")
        print(zeile)

    if args.zahl and len(luecken) > args.zahl:
        print(f"\n… und {len(luecken) - args.zahl} weitere "
              f"(--zahl 0 zeigt alle).")

    if args.vergleich:
        mit = sum(1 for n, _ in luecken if n in vergleich)
        print(f"\nFuer {mit} der {len(luecken)} Luecken hat "
              f"{args.vergleich.name} eine Vorlage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
