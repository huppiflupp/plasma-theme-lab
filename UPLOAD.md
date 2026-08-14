# Veröffentlichen auf store.kde.org (kde-look.org)

Die Archive entstehen mit

```bash
./tools/mach-paket.sh
```

und liegen danach in `dist/`. Sie sind **nicht** im Repository — sie
lassen sich jederzeit reproduzieren, und Binärdateien blähen die
Historie nur auf.

```
dist/
├── nt-legacy-0.2.3.tar.xz                      2,3 MB   Gesamtpaket
├── nt-legacy-global-theme-<farbwelt>-0.2.3.tar.xz       10 Stück
├── nt-legacy-plasma-style-<farbwelt>-0.2.3.tar.xz       10 Stück
├── nt-legacy-icons-0.2.3.tar.xz                184 KB
├── nt-legacy-window-decorations-0.2.3.tar.xz    12 KB
├── nt-legacy-cursors-0.2.3.tar.xz               12 KB
├── nt-legacy-color-schemes-0.2.3.tar.xz        4,0 KB
├── screenshots/                                 16 Bilder (10 + 5 Tag/Nacht + Übersicht)
└── SHA256SUMS
```

## Warum mehrere Archive?

Der Store kennt je Eintrag genau **eine** Kategorie. Ein Theme wie dieses
besteht aber aus sechs Ebenen. Deshalb gibt es beides:

- **Das Gesamtpaket** mit `install.sh` — für Leute, die alles auf einmal
  wollen. Das ist der Weg, den die meisten größeren Themes gehen.
- **Einzelarchive je Ebene** — nur damit funktioniert *Neue holen …*
  direkt in den Systemeinstellungen.

## Warum Global Themes und Plasma-Stile je Variante ein Archiv sind

Bis 0.2.2 lagen alle zehn Fassungen in einem Archiv. Über *Neue holen …*
war das Ergebnis: fünf bis sechs namenlose Einträge, die aussehen wie
Breeze, und kein einziges NT-Design. Aus der Community gemeldet und mit
`kpackagetool6` nachgestellt.

Der Grund steht in den `knsrc`-Dateien von Plasma. Es gibt zwei Sorten:

| `Uncompress=` | Verhalten | Bündel erlaubt? |
|---|---|---|
| `archive`, `true` | entpackt stumpf ins Zielverzeichnis | ja |
| `kpackage` | reicht an `kpackagetool6` weiter | **nein** |

`kpackagetool6` erwartet **genau ein** Paket, dessen `metadata.json` an
der Archivwurzel liegt. Lagen dort zehn Ordner, nahm es das Archiv selbst
für das Paket und benannte es nach der Datei:

```
$ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-global-themes-0.2.2.tar.xz
Erfolgreich installiert: …/plasma/look-and-feel/nt-legacy-global-themes-0/
```

Ein Ordner ohne `metadata.json` — kein Design, ein namenloser Eintrag, und
der nächste Versuch legt `-1` daneben. Bei den Plasma-Stilen schlägt schon
die Installation fehl („Das Paket wird als ungültig betrachtet").

Global Themes und Plasma Themes laufen beide über `kpackage`. Aurorae,
Symbole, Mauszeiger und Farbschemata über `archive` — dort bleiben die
Bündel.

**Beim Hochladen:** die alten Bündelarchive im Store **löschen**, nicht
nur die neuen daneben legen. Wer die alte Datei zieht, bekommt weiter die
kaputten Einträge.

Format ist `tar.xz`: kleiner als ZIP, unter Linux überall auspackbar, und
es erhält symbolische Verweise. Das Symbolset besteht fast zur Hälfte aus
Verweisen — ein ZIP würde daraus Kopien machen.

## Was gehört in welche Kategorie?

| Datei | Kategorie im Store | Systemeinstellungen |
|---|---|---|
| `nt-legacy-0.2.3.tar.xz` | **Global Themes** | (manuell, mit `install.sh`) |
| `nt-legacy-global-theme-<farbwelt>-…` (10×) | Global Themes | Erscheinungsbild → Globales Design |
| `nt-legacy-plasma-style-<farbwelt>-…` (10×) | Plasma Themes | Erscheinungsbild → Plasma-Stil |
| `nt-legacy-window-decorations-…` | Window Decorations | Erscheinungsbild → Fensterdekorationen |
| `nt-legacy-icons-…` | Icon Sets | Erscheinungsbild → Symbole |
| `nt-legacy-cursors-…` | Cursors | Erscheinungsbild → Mauszeiger |
| `nt-legacy-color-schemes-…` | Color Schemes | Erscheinungsbild → Farben |

**Empfehlung für den Anfang:** Einen Eintrag unter *Global Themes* mit dem
Gesamtpaket. Das ist am wenigsten Pflegeaufwand und deckt den Fall ab, für
den das Theme gedacht ist — jemand will die NT-Anmutung komplett. Die
Einzelarchive kannst du später als weitere Dateien im selben Eintrag
anhängen oder als eigene Einträge nachreichen.

## Angaben für den Eintrag

**Lizenz:** GPL-2.0-or-later — im Formular als *GPL 2.0* auswählen.

**Beschreibungstext:** `nt-legacy/INSTALL.md` liegt im Gesamtpaket und ist
auf Englisch geschrieben — Voraussetzungen, beide Installationswege, die
zehn Fassungen, Fehlersuche, Rückweg. Für das Beschreibungsfeld im Store
reichen die Abschnitte *Requirements*, *Option 1* und *The ten versions*;
der Rest steht ohnehin im Archiv daneben.

**Dieser Satz gehört dazu**, direkt unter die Installationszeilen — sonst
versprechen die Bildschirmfotos mehr, als eine Installation ohne
`--panel` liefert:

> The screenshots show the theme with its own panel — run
> `./apply.sh <variant> --panel` to get it; without that flag your
> existing panel is left untouched.

**Wichtig:** Das Theme enthält **kein Fremdmaterial**. Symbole, SVGs,
Fensterdekoration, Mauszeiger und Hintergründe sind vollständig erzeugt
(`tools/gen-icons.py`, `gen-plasma-svg.py`, `gen-aurorae.py`,
`gen-cursor.py`). Details in `nt-legacy/ATTRIBUTION.md`. Chicago95 ist
ausdrücklich **nicht** enthalten — dessen Lizenzlage ist ungeklärt.

**Screenshots:** liegen in `dist/screenshots/` und werden von
`mach-paket.sh` miterzeugt:

| Datei | Maße | Zweck |
|---|---|---|
| `00-uebersicht.jpg` | 1956×744 | alle fünf Farbwelten, je Tag und Nacht |
| `01-tag-nacht-*.jpg` … `05-…` | 1920×1080 | eine Farbwelt, diagonal geteilt |
| `nt-legacy.jpg` | 1920×1080 | Petrol — die Grundfassung |
| `nt-legacy-*.jpg` | 1920×1080 | je eine einzelne Fassung |

Jedes Vollbild zeigt vier Programme (Konsole, KolourPaint, Dragon Player,
PCManFM-Qt) mit englischer Oberfläche.

**Die geteilten Bilder** legen Tag- und Nachtfassung derselben Farbwelt in
ein Bild: Schnitt diagonal von oben rechts nach unten links, oben links
Tag, unten rechts Nacht. Im Store ist das die übliche Darstellung für
Themes mit zwei Fassungen — zwei fast gleiche Vollbilder nebeneinander
liest man dagegen leicht als Wiederholung.

Das funktioniert nur, weil `gen-vorschau.sh` für jede Variante dieselben
Programme in derselben Reihenfolge bei derselben Auflösung öffnet. Die
Fensterkanten laufen dadurch über den Schnitt hinweg durch. Wer die
Aufnahmen anders erzeugt, bekommt zwei versetzte Bilder statt einer
geteilten Fläche.

**Reihenfolge in der Galerie:** `00-uebersicht.jpg` zuerst — es zeigt die
Bandbreite auf einen Blick, und danach entscheidet sich, ob jemand
weiterklickt. Dann die fünf geteilten Bilder, dann die Einzelfassungen für
alle, die eine bestimmte Variante ganz sehen wollen. Die Dateinamen sind
so sortiert, dass ein `ls` schon die richtige Reihenfolge ergibt.

**Abhängigkeiten**, die in die Beschreibung gehören:

- Plasma 6 (getestet auf 6.7, Fedora 44)
- Der Anwendungsstil steht auf *MS Windows 9x* — der ist in Qt eingebaut,
  es muss nichts nachinstalliert werden
- PCManFM-Qt ist **optional**. `anmutung.sh` setzt es als Dateimanager,
  weil Dolphins Speicheranzeige am Widget-Stil vorbei zeichnet. Ohne
  PCManFM-Qt funktioniert alles, nur diese eine Leiste sieht fremd aus

## Vor dem Hochladen prüfen

```bash
./tools/mach-paket.sh --pruefen   # was käme hinein?
sha256sum -c dist/SHA256SUMS      # Archive unbeschädigt?
```

Das Paketskript bricht ab, wenn Chicago95-Symbole im Archiv landen
würden — auch dann, wenn `fetch-icons.sh` sie vorher lokal installiert
hat.

## Nach dem Hochladen

Der Store zieht die Versionsnummer nicht automatisch. Bei einer neuen
Fassung:

1. `KPlugin.Version` in allen `metadata.json` erhöhen (macht `build.py`)
2. `./tools/mach-paket.sh` neu laufen lassen
3. Neue Dateien im bestehenden Eintrag hinzufügen, alte nicht löschen —
   sonst brechen Verweise aus Foren und Sammlungen

**Eine Ausnahme:** `nt-legacy-global-themes-0.2.2.tar.xz` und
`nt-legacy-plasma-styles-0.2.2.tar.xz` (beide Plural) gehören gelöscht.
Sie lassen sich über *Neue holen …* nicht installieren und hinterlassen
kaputte Einträge — siehe oben. Ein toter Verweis ist besser als eine
Datei, die den Rechner des Nutzers vollmüllt.

Die Versionsnummer steckt auch im Namen des Render-Caches
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). Wer sie nicht erhöht,
liefert ein Update aus, das beim Nutzer nicht sichtbar wird.
