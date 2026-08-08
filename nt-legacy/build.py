#!/usr/bin/env python3
"""Baut die Theme-Familie "NT Legacy" aus Farbdefinitionen.

Windows-NT-4.0-Farbwelt fuer Plasma 6, ohne schwarze Flaechen: dunkel
wird nur Text, Rahmen und die aktive Titelleiste. Das haelt das Theme
fuer lange Arbeitssitzungen angenehm und gibt ihm trotzdem mehr
Charakter als Breeze.

NT brachte ab Werk benannte Farbschemata mit ("Appearance Schemes").
Drei davon sind hier nachgebaut: Teal, Lilac und Desert. Sie teilen die
Formensprache und unterscheiden sich nur in den Farben - genau das, was
ein parametrischer Aufbau billig macht.

    ./build.py              # alle Varianten
    ./build.py --nur teal   # eine einzelne
    ./build.py --pruefen    # zusaetzlich linten

Wer etwas aendern will, aendert einen Wert in BASIS oder VARIANTEN und
laesst das Skript neu laufen - nicht 25 Dateien von Hand.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
LAB = HIER.parent

AUTOR = "huppiflupp"
EMAIL = "huppiflupp@users.noreply.github.com"
WEBSITE = "https://github.com/huppiflupp/NiceOS9-theme"
LIZENZ = "GPL-2.0-or-later"
SCHRIFT = "Noto Sans"
VERSION = "0.2.0"

# --------------------------------------------------------------------------
# Farben. Einzige Stelle, an der sie stehen.
# --------------------------------------------------------------------------

BASIS = {
    "flaeche":      "#d8d8d0",   # Hauptflaeche, helles neutrales Grau
    "fenster":      "#f0f0e8",   # Fensterinhalt, fast cremeweiss
    "panel":        "#b8c4c4",   # gedaempftes Petrol-Grau
    "kopf_aktiv":   "#176b78",   # Fensterkopf aktiv, dunkles Petrol
    "kopf_inaktiv": "#60777a",   # entsaettigtes Petrol
    "text":         "#202628",   # sehr dunkles Blau-Grau
    "text2":        "#526166",   # Sekundaertext
    "auswahl":      "#287f8c",   # Petrol
    "auswahl_text": "#ffffff",
    "hover":        "#d6a23a",   # NT-artiges Gold
    "warnung":      "#c87922",
    "fehler":       "#a83232",
    "positiv":      "#39734a",
    "desktop":      "#899a9a",
    "hell":         "#f4f4ee",   # 3D-Kante oben/links
    "dunkel":       "#8a8a82",   # 3D-Kante unten/rechts
    "rahmen":       "#202628",   # Aussenrahmen
}

VARIANTEN = {
    "teal": {
        "anzeige": "NT Legacy",
        "beschreibung": "Petrol und warmes Grau - die Grundfassung",
        "farben": {},
    },
    "lilac": {
        "anzeige": "NT Legacy Flieder",
        "beschreibung": "Flieder statt Petrol, nach NTs Schema Lilac",
        "farben": {
            "panel":        "#c4bcc8",
            "kopf_aktiv":   "#5c4a78",
            "kopf_inaktiv": "#7a7088",
            "auswahl":      "#6b5590",
            "hover":        "#c8a83a",
            "desktop":      "#9a91a6",
            "text2":        "#5a5266",
        },
    },
    "desert": {
        "anzeige": "NT Legacy Wueste",
        "beschreibung": "Sand und Terrakotta, nach NTs Schema Desert",
        "farben": {
            "flaeche":      "#d8d0c0",
            "fenster":      "#f0ece0",
            "panel":        "#c8bca4",
            "kopf_aktiv":   "#7a5c2e",
            "kopf_inaktiv": "#8a7c64",
            "auswahl":      "#96703a",
            "hover":        "#c87922",
            "desktop":      "#a89878",
            "text2":        "#6a5c46",
            "hell":         "#f4f0e6",
            "dunkel":       "#8a8272",
        },
    },
}


def palette(variante):
    return {**BASIS, **VARIANTEN[variante]["farben"]}


def ids(variante):
    """Die Kennungen einer Variante.

    Der Farbschema-Name ist der DATEINAME ohne Endung, nicht das
    Name=-Feld - ein Farbschema "NT Legacy" liefe in contents/defaults
    ins Leere.
    """
    kurz = "NTLegacy" if variante == "teal" else f"NTLegacy{variante.capitalize()}"
    return {
        "style":     "nt-legacy" if variante == "teal" else f"nt-legacy-{variante}",
        "schema":    kurz,
        "aurorae":   kurz,
        "lnf":       "com.github.huppiflupp.nt-legacy"
                     + ("" if variante == "teal" else f"-{variante}"),
        "wallpaper": "ntlegacy" if variante == "teal" else f"ntlegacy-{variante}",
        # Suffix _cursors wie bei breeze_cursors. Ohne ihn landen
        # Icon- und Zeigerthema beide unter ~/.local/share/icons/NTLegacy
        # und ihre index.theme-Dateien ueberschreiben sich gegenseitig -
        # danach findet Plasma keine Icons mehr.
        "cursor":    kurz + "_cursors",
    }


def rgb(hexwert):
    h = hexwert.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def schreibe(pfad: Path, inhalt: str, still=False):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(inhalt)
    if not still:
        print(f"  {pfad.relative_to(HIER)}")


# --------------------------------------------------------------------------

def farbschema(p, anzeige):
    """Die .colors-Datei - wirkt auf Qt-Apps UND die Shell.

    Hier entsteht der eigentliche Charakter. Der Plasma Style faerbt nur
    die Shell; alles andere kommt von hier.
    """
    gruppen = {
        "Colors:Window":        (p["flaeche"], p["text"]),
        "Colors:Button":        (p["flaeche"], p["text"]),
        "Colors:View":          (p["fenster"], p["text"]),
        "Colors:Selection":     (p["auswahl"], p["auswahl_text"]),
        "Colors:Tooltip":       (p["fenster"], p["text"]),
        "Colors:Complementary": (p["panel"],   p["text"]),
        "Colors:Header":        (p["flaeche"], p["text"]),
    }
    z = ["[General]", f"ColorScheme={anzeige}", f"Name={anzeige}",
         "shadeSortColumn=true", "", "[KDE]", "contrast=4", ""]

    for gruppe, (bg, fg) in gruppen.items():
        alt = p["auswahl"] if gruppe == "Colors:Selection" else p["fenster"]
        z += [f"[{gruppe}]",
              f"BackgroundNormal={rgb(bg)}",
              f"BackgroundAlternate={rgb(alt)}",
              f"ForegroundNormal={rgb(fg)}",
              f"ForegroundInactive={rgb(p['text2'])}",
              f"ForegroundActive={rgb(p['auswahl'])}",
              f"ForegroundLink={rgb(p['auswahl'])}",
              f"ForegroundVisited={rgb(p['kopf_inaktiv'])}",
              f"ForegroundNegative={rgb(p['fehler'])}",
              f"ForegroundNeutral={rgb(p['warnung'])}",
              f"ForegroundPositive={rgb(p['positiv'])}",
              f"DecorationFocus={rgb(p['auswahl'])}",
              f"DecorationHover={rgb(p['hover'])}", ""]

    # Ohne diese Gruppe sehen inaktive Fenster-Kopfzeilen aus wie aktive -
    # der Unterschied verschwindet genau dort, wo er gebraucht wird.
    z += ["[Colors:Header][Inactive]",
          f"BackgroundNormal={rgb(p['flaeche'])}",
          f"BackgroundAlternate={rgb(p['fenster'])}",
          f"ForegroundNormal={rgb(p['text2'])}",
          f"ForegroundInactive={rgb(p['text2'])}",
          f"ForegroundActive={rgb(p['kopf_inaktiv'])}",
          f"ForegroundLink={rgb(p['kopf_inaktiv'])}",
          f"ForegroundVisited={rgb(p['kopf_inaktiv'])}",
          f"ForegroundNegative={rgb(p['fehler'])}",
          f"ForegroundNeutral={rgb(p['warnung'])}",
          f"ForegroundPositive={rgb(p['positiv'])}",
          f"DecorationFocus={rgb(p['kopf_inaktiv'])}",
          f"DecorationHover={rgb(p['hover'])}", ""]

    z += ["[WM]",
          f"activeBackground={rgb(p['kopf_aktiv'])}",
          f"activeForeground={rgb(p['auswahl_text'])}",
          f"inactiveBackground={rgb(p['kopf_inaktiv'])}",
          f"inactiveForeground={rgb(p['fenster'])}",
          f"activeBlend={rgb(p['auswahl'])}",
          f"inactiveBlend={rgb(p['kopf_inaktiv'])}", "",
          "[ColorEffects:Disabled]", "ChangeSelectionColor=true",
          f"Color={rgb(p['dunkel'])}", "ColorAmount=0", "ColorEffect=0",
          "ContrastAmount=0.65", "ContrastEffect=1",
          "IntensityAmount=0.1", "IntensityEffect=2", "",
          "[ColorEffects:Inactive]", "ChangeSelectionColor=true",
          f"Color={rgb(p['text2'])}", "ColorAmount=0.025", "ColorEffect=2",
          "ContrastAmount=0.1", "ContrastEffect=2", "Enable=false",
          "IntensityAmount=0", "IntensityEffect=0", ""]
    return "\n".join(z)


def style_colors(p, anzeige):
    """Die colors-Datei IM Plasma Style - faerbt nur die Shell."""
    z = [f"# {anzeige} - Farben der Plasma-Shell",
         "# Complementary steuert Panel und Taskleiste.", ""]
    for gruppe, bg, fg in [
        ("Colors:Complementary", p["panel"],   p["text"]),
        ("Colors:Window",        p["flaeche"], p["text"]),
        ("Colors:View",          p["fenster"], p["text"]),
        ("Colors:Button",        p["flaeche"], p["text"]),
        ("Colors:Selection",     p["auswahl"], p["auswahl_text"]),
        ("Colors:Tooltip",       p["fenster"], p["text"]),
    ]:
        z += [f"[{gruppe}]",
              f"BackgroundNormal={rgb(bg)}",
              f"BackgroundAlternate={rgb(p['flaeche'])}",
              f"ForegroundNormal={rgb(fg)}",
              f"ForegroundInactive={rgb(p['text2'])}",
              f"ForegroundActive={rgb(p['auswahl'])}",
              f"ForegroundNegative={rgb(p['fehler'])}",
              f"ForegroundNeutral={rgb(p['warnung'])}",
              f"ForegroundPositive={rgb(p['positiv'])}",
              f"DecorationFocus={rgb(p['auswahl'])}",
              f"DecorationHover={rgb(p['hover'])}", ""]
    return "\n".join(z)


def metadata_style(k, anzeige, beschreibung):
    return json.dumps({
        "KPlugin": {
            "Authors": [{"Name": AUTOR, "Email": EMAIL}],
            "Category": "",
            "Description": beschreibung,
            "EnabledByDefault": True,
            "Id": k["style"],
            "License": LIZENZ,
            "Name": anzeige,
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "X-Plasma-API": "5.0",
    }, indent=4, ensure_ascii=False) + "\n"


def metadata_lnf(k, anzeige, beschreibung):
    return json.dumps({
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {
            "Authors": [{"Name": AUTOR, "Email": EMAIL}],
            "Category": "",
            "Description": beschreibung,
            "Id": k["lnf"],
            "License": LIZENZ,
            "Name": anzeige,
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
        "X-Plasma-APIVersion": "2",
    }, indent=4, ensure_ascii=False) + "\n"


def defaults(k):
    """contents/defaults - schaltet die Ebenen zusammen.

    Der Zeiger wird gesetzt, weil er mitgeliefert wird. Ein Verweis auf
    ein fehlendes Zeigerthema waere schaedlich - der Nutzer bekaeme den
    Standardzeiger und es saehe nach einem Fehler aus.

    Achtung: Das Icon-Theme wirkt ueber diesen Weg NICHT zuverlaessig -
    install.sh setzt es zusaetzlich hart. Plasma Style, Farbschema und
    Anwendungsstil greifen dagegen wie erwartet. Gemessen in der Test-VM.
    """
    return f"""[kdeglobals][KDE]
widgetStyle=Windows

[kdeglobals][General]
ColorScheme={k['schema']}

[kdeglobals][Icons]
Theme=NTLegacy

[kcminputrc][Mouse]
cursorTheme={k['cursor']}

[Wallpaper]
Image={k['wallpaper']}

[plasmarc][Theme]
name={k['style']}

[kdeglobals][WM]
activeFont={SCHRIFT},10,-1,5,75,0,0,0,0,0
inactiveFont={SCHRIFT},10,-1,5,50,0,0,0,0,0

[ksplashrc][KSplash]
Theme={k['lnf']}
Engine=KSplashQML

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__{k['aurorae']}
"""


def layout_js(k):
    """Panelvorgabe: fest unten, schmal, nicht schwebend - wie NT 4.0.

    ACHTUNG: Ersetzt beim Anwenden die Panels des Nutzers. install.sh
    sichert deshalb vorher, und Plasma fragt zusaetzlich nach (die
    Checkbox ist vorab nicht angehakt).
    """
    return f"""// {k['style']} - Panelvorgabe
var alle = panels();
for (var i = 0; i < alle.length; i++) {{
    alle[i].remove();
}}

var panel = new Panel;
panel.location = "bottom";
panel.height = 30;
panel.floating = false;
panel.hiding = "none";
panel.alignment = "left";

panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");

var flaechen = desktops();
for (var j = 0; j < flaechen.length; j++) {{
    flaechen[j].wallpaperPlugin = "org.kde.image";
    flaechen[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    flaechen[j].writeConfig("Image", "{k['wallpaper']}");
    flaechen[j].reloadConfig();
}}
"""


def wallpaper_svg(p, breite=3840, hoehe=2160):
    """Hintergrund im NT-Stil: ruhige Flaeche, kein Fotorealismus."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}"
     viewBox="0 0 {breite} {hoehe}">
  <defs>
    <linearGradient id="grund" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['kopf_inaktiv']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
    <pattern id="raster" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="1" height="1" fill="{p['fenster']}" opacity="0.045"/>
    </pattern>
  </defs>
  <rect width="{breite}" height="{hoehe}" fill="url(#grund)"/>
  <rect width="{breite}" height="{hoehe}" fill="url(#raster)"/>
</svg>
"""


def vorschau_svg(p, k, breite=600, hoehe=337):
    """Das Bild, das in der Design-Auswahl erscheint.

    Ohne preview.png steht dort ein graues Rechteck - der haeufigste
    Grund, warum ein gutes Theme im Store uebersehen wird. Gezeigt wird
    ein Miniatur-Desktop: Hintergrund, ein Fenster mit Titelleiste und
    das Panel. Das reicht, um die Farbwelt zu erkennen.
    """
    th = 22          # Titelleiste
    ph = 20          # Panel
    fx, fy = 95, 60  # Fensterposition
    fw, fh = 380, 210
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}"
     viewBox="0 0 {breite} {hoehe}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['kopf_inaktiv']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
  </defs>
  <rect width="{breite}" height="{hoehe}" fill="url(#g)"/>

  <!-- Fenster -->
  <rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="{p['rahmen']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{fh-2}" fill="{p['flaeche']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{th}" fill="{p['kopf_aktiv']}"/>
  <rect x="{fx+6}" y="{fy+7}" width="90" height="6" fill="{p['auswahl_text']}" opacity="0.9"/>
  <g fill="{p['flaeche']}">
    <rect x="{fx+fw-52}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-37}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-22}" y="{fy+5}" width="13" height="11"/>
  </g>
  <!-- Inhaltsflaeche mit Auswahlbalken und Akzent -->
  <rect x="{fx+8}" y="{fy+th+9}" width="{fw-18}" height="{fh-th-20}" fill="{p['fenster']}"/>
  <rect x="{fx+12}" y="{fy+th+15}" width="{fw-28}" height="12" fill="{p['auswahl']}"/>
  <rect x="{fx+16}" y="{fy+th+18}" width="60" height="6" fill="{p['auswahl_text']}"/>
  <rect x="{fx+16}" y="{fy+th+36}" width="110" height="6" fill="{p['text']}"/>
  <rect x="{fx+16}" y="{fy+th+50}" width="80" height="6" fill="{p['text2']}"/>
  <rect x="{fx+16}" y="{fy+th+64}" width="46" height="12" fill="{p['hover']}"/>

  <!-- Panel: eine helle Linie oben, wie bei NT -->
  <rect x="0" y="{hoehe-ph}" width="{breite}" height="{ph}" fill="{p['panel']}"/>
  <rect x="0" y="{hoehe-ph}" width="{breite}" height="1" fill="{p['hell']}"/>
  <rect x="6" y="{hoehe-ph+4}" width="34" height="9" fill="{p['flaeche']}"/>
  <rect x="46" y="{hoehe-ph+4}" width="52" height="9" fill="{p['flaeche']}"/>
  <rect x="{breite-40}" y="{hoehe-ph+5}" width="30" height="6" fill="{p['text2']}"/>
</svg>
"""


def splash_qml(p, anzeige):
    """Startbildschirm. Ohne diesen bleibt beim Wechsel von einem anderen
    Theme dessen Splash stehen - mitten im NT-Look ein Breeze-Bildschirm.

    Laeuft in einem sehr fruehen Sitzungszustand: nur QtQuick verwenden,
    keine Plasma-Komponenten.
    """
    return f"""import QtQuick

Rectangle {{
    id: root
    color: "{p['desktop']}"
    property int stage

    // NT zeigte beim Start ein schlichtes Feld mit Produktnamen.
    Rectangle {{
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "{p['flaeche']}"
        border.color: "{p['rahmen']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 24
            color: "{p['kopf_aktiv']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: "{anzeige}"
                color: "{p['auswahl_text']}"
                font.bold: true
                font.pixelSize: 13
            }}
        }}

        // Fortschritt: stage laeuft von 1 bis 6
        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; bottom: parent.bottom
                       margins: 14 }}
            height: 14
            color: "{p['fenster']}"
            border.color: "{p['dunkel']}"
            border.width: 1

            Rectangle {{
                anchors {{ left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }}
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "{p['auswahl']}"
                Behavior on width {{ NumberAnimation {{ duration: 180 }} }}
            }}
        }}
    }}
}}
"""


def logout_qml(p):
    """Abmeldedialog. Ohne diesen sieht der Abmeldebildschirm Breeze-artig
    aus - der sichtbarste Bruch im Gesamteindruck."""
    return f"""import QtQuick
import org.kde.plasma.components as PlasmaComponents

Item {{
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal cancelRequested()
    signal lockScreenRequested()

    property string mode
    property var currentAction

    Rectangle {{
        anchors.fill: parent
        color: "{p['rahmen']}"
        opacity: 0.55
        MouseArea {{ anchors.fill: parent; onClicked: root.cancelRequested() }}
    }}

    Rectangle {{
        anchors.centerIn: parent
        width: 340
        height: 150
        color: "{p['flaeche']}"
        border.color: "{p['rahmen']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 22
            color: "{p['kopf_aktiv']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: i18n("Beenden")
                color: "{p['auswahl_text']}"
                font.bold: true
            }}
        }}

        Row {{
            anchors.centerIn: parent
            spacing: 10
            PlasmaComponents.Button {{
                text: i18n("Abmelden"); onClicked: root.logoutRequested()
            }}
            PlasmaComponents.Button {{
                text: i18n("Neu starten"); onClicked: root.rebootRequested()
            }}
            PlasmaComponents.Button {{
                text: i18n("Herunterfahren"); onClicked: root.haltRequested()
            }}
        }}

        PlasmaComponents.Button {{
            anchors {{ bottom: parent.bottom; horizontalCenter: parent.horizontalCenter
                       bottomMargin: 10 }}
            text: i18n("Abbrechen")
            onClicked: root.cancelRequested()
        }}
    }}
}}
"""


def plasmarc():
    return """[Wallpaper]
defaultWallpaperTheme=Next
defaultFileSuffix=.png
defaultWidth=1920
defaultHeight=1080

[AdaptiveTransparency]
enabled=false
"""


# --------------------------------------------------------------------------

def baue(variante, pruefen=False):
    v = VARIANTEN[variante]
    k = ids(variante)
    p = palette(variante)
    anzeige, beschreibung = v["anzeige"], v["beschreibung"]

    print(f"\n=== {anzeige} ({variante}) ===")

    style = HIER / "desktoptheme" / k["style"]
    schreibe(style / "metadata.json", metadata_style(k, anzeige, beschreibung), still=True)
    schreibe(style / "plasmarc", plasmarc(), still=True)
    schreibe(style / "colors", style_colors(p, anzeige), still=True)

    r = subprocess.run(
        [sys.executable, str(LAB / "tools" / "gen-plasma-svg.py"),
         "--alle", "-o", str(style), "--palette", "nt-legacy",
         "--aussenrahmen", "1", "--rahmen", "1", "--stil", "bevel"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False

    # Der Generator kennt nur die Grundpalette. Die Variantenfarben
    # werden hier nachgezogen - Suchen und Ersetzen ueber die erzeugten
    # Dateien ist einfacher, als dem Generator ein Palettenformat
    # beizubringen, und das Ergebnis ist identisch.
    ersetzungen = {BASIS[key]: p[key] for key in p
                   if key in BASIS and BASIS[key] != p[key]}
    if ersetzungen:
        for datei in style.rglob("*.svg"):
            s = datei.read_text()
            for alt, neu in ersetzungen.items():
                s = s.replace(alt, neu)
            datei.write_text(s)
    print(f"  desktoptheme/{k['style']}/  ({len(list(style.rglob('*.svg')))} SVGs)")

    schreibe(HIER / "color-schemes" / f"{k['schema']}.colors",
             farbschema(p, anzeige), still=True)
    print(f"  color-schemes/{k['schema']}.colors")

    r = subprocess.run(
        [sys.executable, str(LAB / "tools" / "gen-aurorae.py"),
         "--name", k["aurorae"], "--anzeige", anzeige,
         "-o", str(HIER / "aurorae"), "--autor", AUTOR,
         "--lizenz", LIZENZ, "--version", VERSION,
         "--button", "18", "--titelhoehe", "24"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False
    deko = HIER / "aurorae" / k["aurorae"]
    if ersetzungen:
        for datei in deko.glob("*.svg"):
            s = datei.read_text()
            for alt, neu in ersetzungen.items():
                s = s.replace(alt, neu)
            datei.write_text(s)
    print(f"  aurorae/{k['aurorae']}/")

    wp = HIER / "wallpapers" / k["wallpaper"]
    schreibe(wp / "metadata.json", json.dumps({
        "KPlugin": {"Authors": [{"Name": AUTOR}], "Id": k["wallpaper"],
                    "License": LIZENZ, "Name": anzeige}},
        indent=4, ensure_ascii=False) + "\n", still=True)
    svg = wp / "contents" / "images" / "3840x2160.svg"
    schreibe(svg, wallpaper_svg(p), still=True)
    r = subprocess.run(["magick", "-background", "none", str(svg),
                        str(svg.with_suffix(".png"))],
                       capture_output=True, text=True)
    print(f"  wallpapers/{k['wallpaper']}/"
          + ("" if r.returncode == 0 else "   (PNG uebersprungen)"))

    # Mauszeiger: eine Standardfassung und eine mit farbigem Zeiger
    for zname, fuell, anz in [
        (f"{k['schema']}_cursors", "#ffffff", anzeige),
        (f"{k['schema']}Rot_cursors", "#c03028", f"{anzeige} (roter Zeiger)"),
    ]:
        r = subprocess.run(
            [sys.executable, str(LAB / "tools" / "gen-cursor.py"),
             "-o", str(HIER / "cursors"), "--name", zname,
             "--anzeige", anz, "--fuellung", fuell],
            capture_output=True, text=True)
        if r.returncode != 0:
            print("  Mauszeiger uebersprungen:", r.stderr.strip().splitlines()[0]
                  if r.stderr.strip() else "unbekannter Fehler")
            break
        print(r.stdout.rstrip())

    lnf = HIER / "look-and-feel" / k["lnf"]
    schreibe(lnf / "metadata.json", metadata_lnf(k, anzeige, beschreibung), still=True)
    schreibe(lnf / "contents" / "defaults", defaults(k), still=True)
    schreibe(lnf / "contents" / "layouts" / "org.kde.plasma.desktop-layout.js",
             layout_js(k), still=True)

    schreibe(lnf / "contents" / "splash" / "Splash.qml",
             splash_qml(p, anzeige), still=True)
    schreibe(lnf / "contents" / "logout" / "Logout.qml", logout_qml(p), still=True)

    # Vorschaubilder fuer die Design-Auswahl
    vs = lnf / "contents" / "previews"
    svg_v = vs / "preview.svg"
    schreibe(svg_v, vorschau_svg(p, k), still=True)
    # 600x337 wie Breeze - die Kachel im Auswahldialog ist 16:9.
    # Bei 400x250 (16:10) wird das Bild beschnitten.
    for datei, groesse in [("preview.png", "600x337"),
                           ("fullscreenpreview.jpg", "1920x1080"),
                           ("lockscreen.png", "600x337"),
                           ("splash.png", "600x337")]:
        subprocess.run(["magick", "-background", "none", str(svg_v),
                        "-resize", groesse + "!", str(vs / datei)],
                       capture_output=True)
    svg_v.unlink(missing_ok=True)
    print(f"  look-and-feel/{k['lnf']}/  (mit Vorschau)")

    if pruefen:
        subprocess.run([sys.executable, str(LAB / "tools" / "lint-plasma-svg.py"),
                        str(style)])
    return True


def main():
    ap = argparse.ArgumentParser(description="Baut die NT-Legacy-Familie.")
    ap.add_argument("--nur", choices=sorted(VARIANTEN), help="nur eine Variante")
    ap.add_argument("--pruefen", action="store_true", help="danach linten")
    args = ap.parse_args()

    print(f"NT Legacy {VERSION}")
    welche = [args.nur] if args.nur else list(VARIANTEN)
    for v in welche:
        if not baue(v, args.pruefen):
            return 1

    icons = HIER / "icons" / "NTLegacy"
    if icons.is_dir():
        r = subprocess.run(
            [sys.executable, str(LAB / "tools" / "gen-symbolic-aliase.py"),
             str(icons)], capture_output=True, text=True)
        zeile = r.stdout.strip().splitlines()
        print(f"\nSymbolische Aliase: {zeile[0] if zeile else '—'}")

    print(f"\nFertig ({len(welche)} Varianten). Installieren: ./install.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
