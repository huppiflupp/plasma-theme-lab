# 2. Plasma Style

Der Plasma Style färbt die Shell: Panel, Plasmoids, Tooltips, Benachrichtigungen,
OSD. Er besteht fast vollständig aus SVG-Dateien plus einer Handvoll
Metadaten.

---

## 2.1 Verzeichnislayout

```
<name>/
├── metadata.json          # Pflicht — ohne sie wird das Theme nicht gefunden
├── plasmarc               # optional: Standard-Hintergrundbild, Transparenz
├── colors                 # optional: eigene Palette für die Shell
├── widgets/*.svg          # der Hauptteil (Breeze: 43 Dateien)
├── dialogs/background.svg # Hintergrund aller Plasma-Popups
├── opaque/{widgets,dialogs}/       # Variante ohne Transparenz
├── translucent/{widgets,dialogs}/  # Variante mit Transparenz
├── solid/{widgets,dialogs}/        # Variante für Blur-freie Umgebungen
└── icons/*.svg            # VERALTET in Plasma 6 — nicht mehr anlegen
```

Die drei Varianten-Ordner sind optional. Plasma wählt je nach Umgebung
(Compositing an/aus, Blur verfügbar) den passenden Satz und fällt sonst auf
`widgets/` zurück.

`icons/` war früher für Tray-Symbole zuständig. In Plasma 6 kommen die aus
dem Icon-Theme. Breeze liefert die Dateien noch mit, neue Themes brauchen
sie nicht.

## 2.2 metadata.json

```json
{
    "KPlugin": {
        "Id": "niceos9",
        "Name": "NiceOS9",
        "Description": "Mac OS 9 Platinum style for the Plasma shell",
        "Authors": [{ "Name": "Vorname Nachname", "Email": "mail@example.org" }],
        "License": "GPL-3.0-or-later",
        "Version": "2.1.0",
        "Website": "https://github.com/…",
        "Category": "",
        "EnabledByDefault": true
    },
    "X-Plasma-API": "5.0"
}
```

Vier Dinge, die man wissen muss:

**Die Theme-Identität ist der Ordnername, nicht `Id`.** [Quelle: `kcms/desktoptheme/themesmodel.cpp`, geprüft]
Der KCM scannt Verzeichnisse unter `plasma/desktoptheme` und nutzt den
Verzeichnisnamen. Beweis: Das installierte `breeze-light` trägt
`"Id": "default"` in seiner `metadata.json` und heißt trotzdem überall
`breeze-light`. Die Doku empfiehlt, beides gleich zu halten — das ist eine
gute Empfehlung, aber keine Bedingung.

**`Version` ist der Cache-Schlüssel.** Siehe [2.6](#26-der-cache). Bei jedem
Release hochzählen.

**`metadata.desktop` funktioniert noch, ist aber abgekündigt.**
[Quelle: `ksvg/src/ksvg/private/imageset_p.cpp`] Der Code prüft erst
`metadata.json`, dann `metadata.desktop`, und gibt bei letzterem eine
Warnung aus. Neue Themes: nur JSON.

**`X-Plasma-API`** steht bei Breeze auch 2026 auf `"5.0"`. Ob der Wert
überhaupt ausgewertet wird, ließ sich im Code nicht nachweisen
**[unsicher]**. Nimm `"5.0"`, um Breeze zu folgen.

## 2.3 Das 9-Patch-System

Jedes rahmenartige Element besteht aus neun benannten SVG-Elementen:

```
topleft      top       topright
   left    center    right
bottomleft  bottom  bottomright
```

Die Skalierungsregeln:

| Teil | Verhalten | Umschalten mit |
|---|---|---|
| Ecken | werden **nie** skaliert | — |
| Kanten | werden **gekachelt** | `hint-stretch-borders` → strecken |
| `center` | wird **gestreckt** | `hint-tile-center` → kacheln |

Für einen Retro-Look mit 1-Pixel-Rahmen ist das die zentrale Mechanik:
Ecken bleiben pixelgenau, Kanten kacheln sauber.

### Präfixe machen aus einem 9-Patch einen Zustand

IDs setzen sich aus mehreren bindestrich-getrennten Teilen zusammen. Ein
Präfix davor definiert einen Zustand. Aus `widgets/button.svg` von Breeze:

```
normal-topleft, normal-top, normal-center, …
hover-topleft,  hover-top,  hover-center,  …
pressed-…, focus-…, shadow-…
toolbutton-hover-…, toolbutton-pressed-…
mask-normal-…
```

Plasma prüft die Existenz eines Präfixes, indem es nachsieht, ob
`<prefix>-center` da ist — mehr nicht. [Quelle: `ksvg` `FrameSvg::hasElementPrefix()`]

```cpp
// for now it simply checks if a center element exists,
// because it could make sense for certain themes to not have all the elements
```

Fehlt `hover-center`, gibt es keinen Hover-Zustand — **ohne Fehlermeldung**.
Das ist der Grund für [Stufe 1 des Testens](05-testen.md).

### Nützliches Werkzeug

KDE liefert eine Inkscape-Erweiterung mit, die genau dafür gedacht ist:
`ksvg/src/tools/inkscape extensions/plasmarename.{inx,py}` — „Plasma →
PlasmaRename" setzt einen Präfix auf alle selektierten Elemente. Damit baut
man einen `hover-*`-Satz aus einem `normal-*`-Satz in Sekunden statt in
zwanzig Klicks.

## 2.4 Alle hint-IDs

Ein `hint-*`-Element ist ein unsichtbares Rechteck, dessen Geometrie eine
Angabe transportiert. Man zeichnet es in Inkscape, gibt ihm die ID, setzt
die Deckkraft auf 0.

| ID | Wirkung |
|---|---|
| `hint-tile-center` | `center` kacheln statt strecken |
| `hint-stretch-borders` | Kanten strecken statt kacheln |
| `hint-compose-over-border` | `center` **unter** die Ränder zeichnen — verhindert Alpha-Überlagerung an halbtransparenten Rändern |
| `hint-{top,right,bottom,left}-margin` | Innenabstand des Inhalts festlegen |
| `hint-{top,right,bottom,left}-inset` | Rahmen nach innen versetzen — für Schatten und schwebende Panels |
| `hint-apply-color-scheme` | ganzes SVG monochron einfärben (nur ohne `colors`-Datei) |
| `hint-focus-over-base` | Fokusrahmen über die Basis legen (`lineedit.svg`) |
| `hint-size`, `hint-bar-size`, `hint-scrollbar-size`, `hint-handle-size` | Größenvorgaben |
| `hint-preferred-icon-size` | bevorzugte Symbolgröße |
| `hint-rotation-angle` | Uhr-/Busy-Widget |
| `hint-glow-radius`, `hint-use-shadow`, `hint-show-separator` | Effekte |

Hints lassen sich mit Präfixen kombinieren: `shadow-hint-top-margin`,
`floating-hint-bottom-margin`, `normal-hint-compose-over-border`. Alle drei
kommen in Breeze tatsächlich vor. [geprüft]

**`hint-*-inset` ist der Plasma-6-Neuzugang.** Er trennt die gezeichnete
Fläche vom beanspruchten Platz — nötig für schwebende Panels und
Schlagschatten. Ein Theme ohne Insets sieht auf einem schwebenden Panel
falsch aus.

## 2.5 Farbschema-Unterstützung

Es gibt zwei Mechanismen. Der zweite ist der richtige.

**(a) `hint-apply-color-scheme`** — ein Element mit dieser ID einfügen und
**keine** `colors`-Datei mitliefern. Dann wird das ganze SVG monochrom in
Fensterhintergrundfarbe eingefärbt. Grobes Werkzeug, selten sinnvoll.

**(b) Das `current-color-scheme`-Stylesheet** — der Standardweg:

```xml
<defs>
  <style id="current-color-scheme" type="text/css">
    .ColorScheme-Text             { color:#31363b; }
    .ColorScheme-Background       { color:#eff0f1; }
    .ColorScheme-Highlight        { color:#3daee9; }
    .ColorScheme-ViewText         { color:#31363b; }
    .ColorScheme-ViewBackground   { color:#fcfcfc; }
    .ColorScheme-ViewHover        { color:#93cee9; }
    .ColorScheme-ViewFocus        { color:#3daee9; }
    .ColorScheme-ButtonText       { color:#31363b; }
    .ColorScheme-ButtonBackground { color:#eff0f1; }
    .ColorScheme-ButtonHover      { color:#93cee9; }
    .ColorScheme-ButtonFocus      { color:#3daee9; }
  </style>
</defs>

<path class="ColorScheme-Background" fill="currentColor" d="…"/>
```

Vor dem Rendern ersetzt Plasma die `color:`-Werte durch die Systemfarben.

**Zwei Dinge sind Pflicht:** die Klasse **und** `fill="currentColor"` bzw.
`stroke="currentColor"`. Ohne `currentColor` bleibt die feste Farbe stehen.

Gradienten akzeptieren keine Klassen — dafür das Gradient-Element in eine
Gruppe wickeln: `<g class="ColorScheme-Background">…</g>`.

`ColorScheme-Highlight` ist ein Sonderfall: Sie folgt der vom Nutzer
gesetzten **Akzentfarbe**.

**Warum das wichtig ist:** Nur wer diese Klassen konsequent nutzt, kann
Farbvarianten ohne SVG-Duplikate bauen. Siehe
[Kapitel 4](04-bauen-und-installieren.md#44-varianten-ohne-duplikate).

### Hilfsskripte

In `frameworks/ksvg/src/tools/`:

- `apply-stylesheet.sh` — ersetzt feste Farben durch `ColorScheme-*`-Klassen
- `currentColorFillFix.sh` — repariert `fill`-Attribute für `currentColor`
- `split-plasma-svgs` — zerlegt eine Plasma-SVG in Einzelelemente (Debugging)

## 2.6 Der Cache

**Die häufigste Ursache für „meine Änderung wirkt nicht".**

Plasma cacht gerenderte Pixmaps in
`~/.cache/plasma_theme_<name>_v<version>.kcache` plus `~/.cache/ksvg-elements`.
Der Cachename enthält die Version aus `metadata.json`:

```cpp
QString cacheFile = QLatin1String("plasma_theme_") + imageSetName;
if (!themeVersion.isEmpty()) { cacheFile += QLatin1String("_v") + themeVersion; }
```
[Quelle: `ksvg`]

Daraus folgt zweierlei:

**Beim Entwickeln** nach jeder SVG-Änderung:
```bash
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

**Beim Veröffentlichen** die Version hochzählen. Sonst sehen deine Nutzer
nach dem Update das alte Theme und melden Fehler, die längst behoben sind.

## 2.7 Welche SVGs braucht man wirklich?

Formal keine — alles fällt auf Breeze zurück. Praktisch nach Sichtbarkeit:

| Priorität | Datei | Was man sieht |
|---|---|---|
| **1** | `widgets/panel-background.svg` | Panel / Taskleiste |
| **1** | `dialogs/background.svg` | alle Plasma-Popups |
| **1** | `widgets/background.svg` | Plasmoid-Hintergründe |
| 2 | `widgets/tooltip.svg` | Tooltips |
| 2 | `widgets/listitem.svg`, `viewitem.svg` | Listen (Anwendungsstarter!) |
| 2 | `widgets/button.svg`, `lineedit.svg` | Bedienelemente in Plasmoids |
| 2 | `widgets/checkmarks.svg`, `radiobutton.svg`, `switch.svg` | Auswahlelemente |
| 2 | `widgets/scrollbar.svg`, `slider.svg` | Regler |
| **1** | `widgets/tasks.svg` | Fensterknöpfe in der Taskleiste — von `taskmanager.so` angefordert, per `strings` verifiziert |
| 3 | `widgets/plasmoidheading.svg`, `toolbar.svg`, `frame.svg` | Rahmen, Kopfzeilen |
| 3 | `widgets/clock.svg`, `analog_meter.svg`, `pager.svg` | spezielle Widgets |
| — | `icons/*.svg` | **veraltet** — weglassen |

**Der Satz, um den es geht:** Ein Theme mit nur `panel-background.svg` ist
kein eigener Look — es ist Breeze mit einem anderen Panel. Die Prioritäten
1 und 2 sind die Schwelle, ab der ein Theme als eigenständig wahrgenommen
wird. Das sind rund 12 Dateien, nicht 43.

## 2.8 Im Repo .svg, ausgeliefert .svgz

Breeze komprimiert beim Bauen jede `.svg` mit `gzip -9 -n` zu `.svgz`.
[Quelle: `libplasma/src/desktoptheme/CMakeLists.txt`, geprüft an
`/usr/share/plasma/desktoptheme/default/widgets/` — dort liegen 43 `.svgz`]

Das `-n` unterdrückt den Zeitstempel, damit Builds reproduzierbar bleiben.

Diese Arbeitsteilung ist richtig und sollte übernommen werden: Im Repository
liegen Klartext-SVGs, die man diffen und in Inkscape öffnen kann.
Ausgeliefert wird die komprimierte Fassung. Plasma liest beide.

Wie man das ohne CMake macht, steht in
[Kapitel 4](04-bauen-und-installieren.md).

---

**Weiter:** [Kapitel 3 — Look-and-Feel-Paket](03-look-and-feel.md)
