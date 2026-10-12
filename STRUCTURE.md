# Zielstruktur für NiceOS9

Vorschlag, abgeleitet aus Breeze und [Klassy](https://github.com/paulmcauley/klassy)
(dem am besten strukturierten Drittprojekt für Plasma 6).

Noch nicht umgesetzt — erst wird der Ist-Zustand in der VM gemessen, dann
umgebaut. Sonst baut man um, ohne zu wissen, was vorher kaputt war.

---

## Ist-Zustand

```
NiceOS9-theme/
├── install.sh              479 Zeilen, macht alles auf einmal, ruft sudo
├── install-grub.sh         schreibt nach /boot/grub2/
├── install-plymouth.sh     baut initramfs neu
├── install-sddm.sh         schreibt nach /usr/share/sddm/
├── uninstall.sh            löscht Dateien, setzt Konfiguration nicht zurück
├── desktoptheme/           3 Varianten × 1 SVG   (Breeze: 43)
├── plasma/                 2 Ordner, Zweck unklar — Dublette zu desktoptheme?
├── look-and-feel/          3 Varianten, mit layouts/ und totem lockscreen/
├── aurorae/                3 Dekorationen
├── color-schemes/          4 Farbschemata
├── icons/                  1543 PNG
├── fonts/, wallpapers/, grub/, plymouth/, sddm/, previews/, screenshots/
└── autostart/              panel-nofloat mit fest verdrahtetem /home/seeas
```

### Die acht Befunde

| # | Befund | Wirkung |
|---|---|---|
| 1 | `look-and-feel/*/contents/layouts/*.js` | kann die Panels des Nutzers ersetzen — **nicht umkehrbar**, aber nur nach ausdrücklicher Zustimmung (s. u.) |
| 2 | Ein Installer für `$HOME` **und** GRUB/Plymouth/SDDM | ein Durchlauf kann den Rechner am Booten hindern |
| 3 | 1 statt 43 Widget-SVGs | der Look ist zu 97 % Breeze |
| 4 | `look-and-feel/*/contents/lockscreen/` | toter Code — Plasma 6 lädt den Sperrbildschirm aus dem Shell-Paket |
| 5 | `uninstall.sh` löscht nur Dateien | **in der VM belegt**, s. u. |
| 6 | `sed HOME_PLACEHOLDER`, fest verdrahtetes `/home/seeas` | bricht bei abweichenden Pfaden |
| 7 | `defaults` setzt `cursorTheme=XCursor-Pro-Red` | der Installer liefert den Cursor nicht aus, obwohl er im Repo liegt |
| 8 | Metadaten unvollständig | behoben — `Version`, `License`, `Website`, `Authors` ergänzt |

### Befund 5, belegt statt behauptet

Testlauf `tests/laeufe/niceos9-20260807-195105`, Ablauf: installieren →
anwenden → neu starten → deinstallieren → neu starten.

Nach `uninstall.sh` **und** einem Neustart:

```
Globales Design: [niceos9-bright]     ← zeigt auf ein gelöschtes Verzeichnis
Plasma Style   : []
Farbschema     : []
Icons          : []
Stil           : []
Dekoration     : []

$ ls ~/.local/share/plasma/look-and-feel/niceos9-bright
ls: Zugriff nicht möglich: Datei oder Verzeichnis nicht gefunden
```

Sichtbar: helles Panel ohne passendes Theme, **leerer Systembereich** —
Lautstärke, Netzwerk und Zwischenablage fehlen. Kein Absturz, aber ein
Desktop, den man von Hand wieder herrichten muss.

Screenshots im Testlauf-Verzeichnis.

### Nebenbefund zum Anwenden

Ein Global Theme entfaltet seine Wirkung **erst nach einem Neustart der
Sitzung** vollständig. Direkt nach `plasma-apply-lookandfeel --apply`
greifen nur Teile (Icons ja, Plasma Style und Farbschema nicht), und in
den Konfigurationsdateien steht noch nichts — Plasma hält die Werte bis
zum Sitzungsende im Speicher.

Für Tests heißt das: Ohne Neustart misst man einen Zwischenzustand.
Für die README heißt es: Der Hinweis „ab- und wieder anmelden" gehört
dazu.

Dazu zwei Dinge, die **richtig** sind und so bleiben sollten: die Gruppe
`org.kde.kdecoration2` (auch unter KDecoration3 korrekt) und der Aufbau der
vorhandenen `panel-background.svg` — 9-Patch vollständig, Farbschema
angebunden.

---

## Zielstruktur

```
niceos9/
├── Makefile                    eine Versionsnummer, .svgz beim Bauen
├── install.sh                  nur $HOME, kein sudo — ruft nur make
├── uninstall.sh                aus dem Manifest, mit Konfigurations-Rollback
├── README.md  LICENSE  LICENSES/  REUSE.toml
│
├── desktoptheme/
│   └── niceos9/                EINE Variante mit SVGs
│       ├── metadata.json.in
│       ├── plasmarc
│       ├── colors
│       ├── widgets/*.svg       Ziel: die 14 aus Prioritaet 1+2
│       └── dialogs/background.svg
│
├── color-schemes/              hier entstehen die Varianten
│   ├── NiceOS9Bright.colors
│   ├── NiceOS9Dark.colors
│   └── NiceOS8Charcoal.colors
│
├── aurorae/ChicagoNine{,Dark,Eight}/
│
├── look-and-feel/              drei Bündel, alle auf denselben Plasma Style
│   └── com.github.huppiflupp.niceos9-{bright,dark,charcoal}/
│       ├── metadata.json.in
│       └── contents/
│           ├── defaults
│           └── previews/
│                               ← KEIN layouts/, KEIN lockscreen/
│
├── layout-templates/           das Panel als Angebot statt als Zwang
│   └── org.huppiflupp.niceos9.panel/
│
├── icons/nineicons-redux/
├── fonts/  wallpapers/
│
├── tools/
│   ├── lint-plasma-svg.py      → schon fertig in plasma-theme-lab/tools/
│   └── gen-colors.py           Farbschemata aus einer Palette
│
└── risky/                      getrennt, eigene Warnung, Default = nein
    ├── README.md               "diese Skripte können den Rechner am Booten hindern"
    ├── install-sddm.sh         + Erkennung: plasmalogin hat keine QML-Themes
    ├── install-plymouth.sh
    └── install-grub.sh
```

## Die sieben Änderungen

**1 — `layouts/` bleibt, aber mit Sicherungsnetz.**

Erste Einschätzung revidiert. Das Panel gehört zum Mac-OS-9-Look; ein
Theme ohne die Leiste oben ist unvollständig. Und KDE schützt bereits an
drei Stellen: [Quelle: `kcms/lookandfeel/kcm.cpp`, `SimpleOptions.qml`]

```cpp
// But do not select layout contents by default if there appaerance settings
if (m_themeContents & KLookAndFeelManager::AppearanceSettings) {
    resetContents &= ~KLookAndFeelManager::LayoutSettings;
}
```

- die Checkbox „Arbeitsflächen- und Fenster-Layout" ist **vorab nicht
  angehakt**, sobald das Theme auch Erscheinungsbild-Einstellungen liefert
- darunter steht eine rote Warnung, sichtbar sobald man sie anhakt
- `plasma-apply-lookandfeel --apply` fasst das Layout ohne
  `--resetLayout` nicht an

Was fehlt, ist der **Rückweg**. Der Installer soll vor der Installation
die Panel-Konfiguration sichern:

```bash
BACKUP="$HOME/.local/share/niceos9/panel-backup-$(date +%F-%H%M).rc"
mkdir -p "$(dirname "$BACKUP")"
cp -a "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "$BACKUP" 2>/dev/null
echo "Panel-Konfiguration gesichert: $BACKUP"
```

Damit wird aus „unwiderruflich" ein „eine Datei zurückkopieren und neu
anmelden". Das ist der eigentliche Mangel — nicht das Layout selbst.

Zusätzlich ein `Plasma/LayoutTemplate` für Leute, die ihr eingerichtetes
Panel behalten und den NiceOS9-Aufbau nur daneben ausprobieren wollen.
Ergänzung, kein Ersatz.

Der `HOME_PLACEHOLDER`-`sed`-Hack im Layout-Skript bleibt damit bestehen
und sollte separat gelöst werden — das Wallpaper lässt sich im Skript
über eine relative Auflösung statt eines absoluten Pfades setzen.

**2 — Risikoskripte nach `risky/`.**
`install.sh` fragt nicht mehr nach sudo und fasst nichts außerhalb von
`$HOME` an. Wer GRUB will, ruft `risky/install-grub.sh` bewusst auf.
Zusätzlich in `install-sddm.sh` die Erkennung, ob überhaupt SDDM läuft —
auf Fedora 44 und Nobara ist es `plasmalogin`, der keine QML-Themes kennt.

**3 — Eine Variante mit SVGs.**
`desktoptheme/niceos9` ist die einzige mit Grafik. `dark` und `charcoal`
verschwinden als Plasma Styles; ihre Wirkung übernehmen die Farbschemata.
Voraussetzung: Die SVGs nutzen `class="ColorScheme-*"` + `fill="currentColor"`.
Die vorhandene `panel-background.svg` tut das bereits.

Das reduziert drei zu pflegende Bäume auf einen — die Bedingung dafür,
dass sich 14 neue SVGs überhaupt lohnen.

**4 — `lockscreen/` löschen.** Toter Code seit Plasma 6.

**5 — `uninstall.sh` mit Rollback.**
Der Installer sichert vor der ersten Änderung die alten Werte von
`plasmarc`, `kdeglobals` und `kwinrc` in ein `restore.sh`. Die
Deinstallation ruft es auf. Diese eine Datei ist der Unterschied zwischen
„ich probiere das mal aus" und „ich trau mich nicht".

**6 — Makefile statt `cp -r`.**
Eine Versionsnummer für alle Pakete, `.svgz` beim Bauen, Installation über
`kpackagetool6` (prüft die Metadaten), Deinstallation aus dem Manifest.

**7 — `plasma/` klären.**
Der Ordner `plasma/niceos9-{bright,dark}/` enthält `colors`, `metadata.json`
und `plasmarc` — dieselbe Form wie `desktoptheme/`, aber der Installer
kopiert ihn nirgendwohin. Vermutlich eine Dublette aus einer früheren
Fassung. **Vor dem Löschen klären** — falls er einen Zweck hat, gehört der
dokumentiert.

## Die SVG-Arbeit

Der Linter sagt, was fehlt:

```
Prioritaet 1:  dialogs/background.svg, widgets/background.svg
Prioritaet 2:  tooltip, listitem, viewitem, button, lineedit, checkmarks,
               radiobutton, switch, scrollbar, slider, frame, toolbar
```

14 Dateien. Danach ist es ein eigenständiges Theme und nicht mehr Breeze
mit Retro-Panel. Die restlichen 39 sind Feinschliff.

Das ist Gestaltungsarbeit, keine Strukturarbeit — sie gehört nach dem
Umbau, nicht davor.

## Reihenfolge

1. Ist-Zustand in der VM messen (Testlauf gegen das aktuelle Repo)
2. Struktur umbauen — Punkte 1, 2, 4, 5, 7 (mechanisch, kein Design)
3. Erneut testen: gleicher Look, aber gefahrlos ausprobierbar?
4. Punkt 3 (eine Variante) — braucht eine Entscheidung über die Farbschemata
5. Punkt 6 (Makefile)
6. Dann erst die 14 SVGs
