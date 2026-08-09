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
├── nt-legacy-0.2.0.tar.xz                      2,3 MB   Gesamtpaket
├── nt-legacy-global-themes-0.2.0.tar.xz        1,5 MB
├── nt-legacy-icons-0.2.0.tar.xz                168 KB
├── nt-legacy-plasma-styles-0.2.0.tar.xz         40 KB
├── nt-legacy-window-decorations-0.2.0.tar.xz    12 KB
├── nt-legacy-cursors-0.2.0.tar.xz               12 KB
├── nt-legacy-color-schemes-0.2.0.tar.xz        4,0 KB
├── screenshots/                                 10 Vollbilder
└── SHA256SUMS
```

## Warum mehrere Archive?

Der Store kennt je Eintrag genau **eine** Kategorie. Ein Theme wie dieses
besteht aber aus sechs Ebenen. Deshalb gibt es beides:

- **Das Gesamtpaket** mit `install.sh` — für Leute, die alles auf einmal
  wollen. Das ist der Weg, den die meisten größeren Themes gehen.
- **Einzelarchive je Ebene** — nur damit funktioniert *Neue holen …*
  direkt in den Systemeinstellungen. KNewStuff entpackt das Archiv an die
  passende Stelle und erwartet dort genau eine Ebene.

Format ist `tar.xz`: kleiner als ZIP, unter Linux überall auspackbar, und
es erhält symbolische Verweise. Das Symbolset besteht fast zur Hälfte aus
Verweisen — ein ZIP würde daraus Kopien machen.

## Was gehört in welche Kategorie?

| Datei | Kategorie im Store | Systemeinstellungen |
|---|---|---|
| `nt-legacy-0.2.0.tar.xz` | **Global Themes** | (manuell, mit `install.sh`) |
| `nt-legacy-global-themes-…` | Global Themes | Erscheinungsbild → Globales Design |
| `nt-legacy-plasma-styles-…` | Plasma Themes | Erscheinungsbild → Plasma-Stil |
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

**Wichtig:** Das Theme enthält **kein Fremdmaterial**. Symbole, SVGs,
Fensterdekoration, Mauszeiger und Hintergründe sind vollständig erzeugt
(`tools/gen-icons.py`, `gen-plasma-svg.py`, `gen-aurorae.py`,
`gen-cursor.py`). Details in `nt-legacy/ATTRIBUTION.md`. Chicago95 ist
ausdrücklich **nicht** enthalten — dessen Lizenzlage ist ungeklärt.

**Screenshots:** liegen in `dist/screenshots/`, zehn Vollbilder in
1920×1080, je Variante eines. Jedes zeigt vier Programme (Konsole,
KolourPaint, Dragon Player, PCManFM-Qt), englische Oberfläche.

Für die Übersicht am besten `nt-legacy.jpg` (Petrol) als erstes Bild —
das ist die Grundfassung.

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

Die Versionsnummer steckt auch im Namen des Render-Caches
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). Wer sie nicht erhöht,
liefert ein Update aus, das beim Nutzer nicht sichtbar wird.
