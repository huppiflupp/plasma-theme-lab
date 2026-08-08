#!/usr/bin/env python3
"""Baut ein Icon-Theme aus den ReactOS-Symbolressourcen.

Warum ReactOS: Chicago95 hat bis heute keine LICENSE-Datei, und seine
Bitmaps stammen laut eigenem README aus *Classic95*, dessen Lizenz sich
nicht ermitteln laesst. ReactOS ist GPL-2.0 und clean-room entwickelt -
also weitergebbar, auch ueber den KDE Store.

Die Symbole liegen dort als .ico mit Windows-Ressourcennummern
(3.ico, 1001.ico ...), nicht unter sprechenden Namen. Die Zuordnung zu
freedesktop-Namen steht in ZUORDNUNG weiter unten und ist Handarbeit.

    ./gen-icons-reactos.py --quelle <reactos-repo> --ziel <icon-theme>
    ./gen-icons-reactos.py --quelle <repo> --bogen /tmp/uebersicht

Der zweite Aufruf erzeugt beschriftete Uebersichtsbilder aller Symbole -
die Grundlage, um weitere zuzuordnen.

Zur Konvertierung: ImageMagick und Pillow lesen die Maske dieser Dateien
falsch und streuen Farbpunkte ueber das Bild. Farbe und Maske einzeln zu
holen und selbst zusammenzusetzen liefert dagegen ein sauberes Ergebnis -
siehe _konvertiere().
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

GROESSEN = (16, 32, 48)

# Ressourcennummer -> (freedesktop-Name, Kontext)
#
# Die Nummern folgen der Windows-shell32-Konvention, die ReactOS aus
# Kompatibilitaetsgruenden uebernimmt. Geprueft wurde jede einzelne am
# Uebersichtsbogen - Nummern raten fuehrt zu Ordnern, die wie Drucker
# aussehen.
ZUORDNUNG = {
    # ── Orte ──────────────────────────────────────────────────────────
    4:    ("folder",                    "places"),
    5:    ("folder-open",               "places"),
    235:  ("user-home",                 "places"),
    133:  ("folder-documents",          "places"),
    237:  ("folder-music",              "places"),
    238:  ("folder-videos",             "places"),
    29:   ("folder-publicshare",        "places"),
    38:   ("folder-print",              "places"),
    46:   ("folder-saved-search",       "places"),
    321:  ("folder-system",             "places"),
    326:  ("folder-remote",             "places"),
    32:   ("user-trash",                "places"),
    33:   ("user-trash-full",           "places"),
    16:   ("computer",                  "places"),
    15:   ("network-workgroup",         "places"),
    14:   ("network-server",            "places"),

    # ── Geraete ───────────────────────────────────────────────────────
    7:    ("media-floppy",              "devices"),
    8:    ("drive-harddisk",            "devices"),
    9:    ("drive-removable-media",     "devices"),
    12:   ("drive-optical",             "devices"),
    302:  ("media-optical",             "devices"),
    294:  ("media-optical-audio",       "devices"),
    17:   ("printer",                   "devices"),
    18:   ("printer-network",           "devices"),
    248:  ("camera-photo",              "devices"),
    315:  ("scanner",                   "devices"),
    272:  ("input-mouse",               "devices"),
    308:  ("media-flash",               "devices"),
    314:  ("pda",                       "devices"),
    283:  ("computer-laptop",           "devices"),
    35:   ("video-display",             "devices"),

    # ── Anwendungen und Einstellungen ─────────────────────────────────
    25:   ("applications-system",       "apps"),
    274:  ("preferences-system",        "apps"),
    23:   ("system-search",             "apps"),
    24:   ("help-browser",              "apps"),
    26:   ("preferences-desktop-screensaver", "apps"),
    155:  ("preferences-desktop-font",  "apps"),
    269:  ("system-users",              "apps"),
    47:   ("applications-internet",     "apps"),
    20:   ("applications-other",        "apps"),
    41:   ("applications-multimedia",   "apps"),

    # ── Aktionen ──────────────────────────────────────────────────────
    281:  ("edit-find",                 "actions"),
    45:   ("system-log-out",            "actions"),
    48:   ("system-lock-screen",        "actions"),
    322:  ("bookmarks",                 "actions"),
    21:   ("document-open-recent",      "actions"),
    139:  ("document-print-preview",    "actions"),

    # ── Dateitypen ────────────────────────────────────────────────────
    1:    ("text-x-generic",            "mimetypes"),
    152:  ("text-x-preview",            "mimetypes"),
    153:  ("application-x-generic",     "mimetypes"),
    225:  ("audio-x-generic",           "mimetypes"),
    224:  ("video-x-generic",           "mimetypes"),
    226:  ("image-x-generic",           "mimetypes"),
    156:  ("font-x-generic",            "mimetypes"),

    # ── Status ────────────────────────────────────────────────────────
    200:  ("dialog-error",              "status"),
    1001: ("dialog-information",        "status"),
    1004: ("dialog-question",           "status"),
    11:   ("network-offline",           "status"),
}


def _magick(*args):
    subprocess.run(["magick", *[str(a) for a in args]], check=True,
                   capture_output=True)


def _konvertiere(ico: Path, groesse: int, ziel: Path) -> bool:
    """Holt eine Groesse aus der .ico und schreibt sie als PNG.

    Farbe und Maske werden getrennt geholt und dann zusammengesetzt. Der
    direkte Weg (magick datei.ico ziel.png) erzeugt bei diesen Dateien
    ein Punktmuster in den Farben des Symbols - die Maske wird dabei als
    Bilddaten missdeutet.
    """
    ebene = _ebene_fuer(ico, groesse)
    if ebene is None:
        return False
    # Vor allem anderen: Die Zwischendateien liegen neben dem Ziel, und
    # ohne das Verzeichnis scheitert schon der erste Aufruf.
    ziel.parent.mkdir(parents=True, exist_ok=True)
    farbe = ziel.with_suffix(".farbe.tmp.png")
    maske = ziel.with_suffix(".maske.tmp.png")
    try:
        _magick(f"{ico}[{ebene}]", "-alpha", "off", farbe)
        _magick(f"{ico}[{ebene}]", "-alpha", "extract", maske)
        _magick(farbe, maske, "-alpha", "off",
                "-compose", "CopyOpacity", "-composite", ziel)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        farbe.unlink(missing_ok=True)
        maske.unlink(missing_ok=True)


def _ebenen(ico: Path):
    """Liefert [(index, breite, bittiefe)] aller Ebenen einer .ico."""
    aus = subprocess.run(["magick", "identify", str(ico)],
                         capture_output=True, text=True)
    ebenen = []
    for i, zeile in enumerate(aus.stdout.splitlines()):
        teile = zeile.split()
        if len(teile) < 5:
            continue
        try:
            breite = int(teile[2].split("x")[0])
        except ValueError:
            continue
        tiefe = next((t for t in teile if t.endswith("-bit")), "0-bit")
        ebenen.append((i, breite, int(tiefe.split("-")[0])))
    return ebenen


def _ebene_fuer(ico: Path, groesse: int):
    """Waehlt die Ebene mit passender Groesse und hoechster Farbtiefe."""
    passend = [e for e in _ebenen(ico) if e[1] == groesse]
    if not passend:
        return None
    return max(passend, key=lambda e: e[2])[0]


def bogen(quelle: Path, ziel: Path, pro_bild=48):
    """Erzeugt beschriftete Uebersichtsbilder aller Symbole."""
    icos = sorted(quelle.rglob("*.ico"),
                  key=lambda p: (p.parent.name, _num(p.stem)))
    if not icos:
        print(f"Keine .ico unter {quelle}", file=sys.stderr)
        return 1
    ziel.mkdir(parents=True, exist_ok=True)
    tmp = ziel / "_tmp"
    tmp.mkdir(exist_ok=True)

    kacheln, uebersprungen = [], 0
    for ico in icos:
        k = tmp / f"{ico.parent.name}__{ico.stem}.png"
        if not _konvertiere(ico, 48, k):
            uebersprungen += 1
            continue
        # Beschriftung unter das Symbol, sonst ist der Bogen wertlos
        _magick(k, "-filter", "point", "-resize", "48x48",
                "-background", "#D8D8D0", "-flatten",
                "-gravity", "center", "-extent", "56x56",
                "-background", "#D8D8D0", "-fill", "#202628",
                "-pointsize", "11", "label:" + ico.stem,
                "-gravity", "center", "-append", k)
        kacheln.append(k)

    bilder = []
    for i in range(0, len(kacheln), pro_bild):
        teil = kacheln[i:i + pro_bild]
        aus = ziel / f"bogen-{i // pro_bild + 1:02d}.png"
        _magick("montage", *teil, "-tile", "8x", "-geometry", "+4+4",
                "-background", "#D8D8D0", aus)
        bilder.append(aus)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(kacheln)} Symbole, {len(bilder)} Bogen in {ziel}")
    if uebersprungen:
        print(f"  {uebersprungen} uebersprungen (keine 48px-Ebene)")
    return 0


def _num(s: str):
    try:
        return (0, int(s))
    except ValueError:
        return (1, s)


def _index_theme(ziel: Path, name: str):
    """Schreibt die index.theme. Ohne sie ist das Verzeichnis kein Theme -
    weder Plasma noch der Alias-Generator erkennen es an."""
    kontexte = sorted(d.name for d in ziel.iterdir() if d.is_dir())
    verzeichnisse = [f"{k}/{g}" for k in kontexte for g in GROESSEN
                     if (ziel / k / str(g)).is_dir()]
    zeilen = ["[Icon Theme]",
              f"Name={name}",
              "Comment=Symbole aus den ReactOS-Ressourcen (GPL-2.0)",
              # Breeze als Rueckfallebene ist ehrlicher als hicolor: was
              # fehlt, faellt ohnehin dorthin - so steht es wenigstens da.
              "Inherits=breeze,hicolor",
              f"Directories={','.join(verzeichnisse)}",
              ""]
    for v in verzeichnisse:
        kontext, groesse = v.split("/")
        zeilen += [f"[{v}]", f"Size={groesse}",
                   f"Context={kontext.capitalize()}", "Type=Fixed", ""]
    (ziel / "index.theme").write_text("\n".join(zeilen))
    return len(verzeichnisse)


def bauen(quelle: Path, ziel: Path):
    if not ZUORDNUNG:
        print("ZUORDNUNG ist leer - erst --bogen erzeugen und zuordnen.",
              file=sys.stderr)
        return 1
    gebaut, fehlend = 0, []
    for nummer, (name, kontext) in ZUORDNUNG.items():
        treffer = list(quelle.rglob(f"{nummer}.ico"))
        if not treffer:
            fehlend.append(nummer)
            continue
        for g in GROESSEN:
            if _konvertiere(treffer[0], g, ziel / kontext / str(g) / f"{name}.png"):
                gebaut += 1
    print(f"  {gebaut} Dateien aus {len(ZUORDNUNG)} Zuordnungen")
    if fehlend:
        print(f"  {len(fehlend)} Ressourcen nicht gefunden: {fehlend[:8]}")
    if gebaut:
        n = _index_theme(ziel, ziel.name)
        print(f"  index.theme mit {n} Verzeichnissen")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quelle", type=Path, required=True,
                    help="ReactOS-Arbeitskopie")
    ap.add_argument("--ziel", type=Path, help="Icon-Theme-Verzeichnis")
    ap.add_argument("--bogen", type=Path, help="Uebersichtsbilder hierhin")
    args = ap.parse_args()

    if not args.quelle.is_dir():
        ap.error(f"{args.quelle} gibt es nicht")
    if args.bogen:
        return bogen(args.quelle, args.bogen)
    if args.ziel:
        return bauen(args.quelle, args.ziel)
    ap.error("entweder --bogen oder --ziel angeben")


if __name__ == "__main__":
    raise SystemExit(main())
