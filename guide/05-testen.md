# 5. Testen

Vier Stufen, von Sekunden bis Minuten. Die ersten drei laufen gefahrlos auf
dem Arbeitsrechner. Die vierte gehört in eine Wegwerf-VM.

| Stufe | Was | Dauer | Wo |
|---|---|---|---|
| 1 | Statische Prüfungen | Sekunden | überall, CI |
| 2 | Einzelnes Widget rendern | Sekunden | Arbeitsrechner |
| 3 | Session neu laden | ~30 s | Arbeitsrechner |
| 4 | Vollinstallation | Minuten | **nur VM** |

---

## 5.1 Stufe 1 — statische Prüfungen

### Der SVG-Linter

Plasma meldet fehlende Element-IDs **nicht**. Ein `hover-center`, das fehlt,
äußert sich darin, dass der Hover-Effekt einfach nicht da ist. Es gibt kein
offizielles Werkzeug dagegen — weder von KDE noch von Dritten.

Dieses Projekt bringt eines mit:

```bash
tools/lint-plasma-svg.py desktoptheme/meintheme
tools/lint-plasma-svg.py desktoptheme/meintheme \
    --vergleich /usr/share/plasma/desktoptheme/default
```

Es prüft:

- wohlgeformtes XML
- Vollständigkeit der 9-Patch-Sätze je Zustandspräfix (kennt auch die
  legitimen 3-Patch-Formen, die Breeze selbst verwendet)
- `current-color-scheme`-Stylesheet vorhanden, wenn `ColorScheme-*`-Klassen
  benutzt werden
- `fill="currentColor"` gesetzt — ohne das bleiben die festen Farben stehen
- unbekannte Farbklassen (Tippfehler in `ColorScheme-…`)
- `hint-*-inset` bei Panel-Hintergründen
- Pflichtfelder in `metadata.json`

Der Vergleichsmodus zeigt, welche SVGs gegenüber Breeze fehlen — nach
Dringlichkeit sortiert, mit den abgekündigten `icons/` herausgerechnet.

**Kalibrierung:** Der Linter läuft gegen Breeze selbst mit null Fehlern
durch. Das ist die Gegenprobe, die jeder Linter braucht — ein Werkzeug, das
die Referenzimplementierung anmeckert, meckert falsch.

### Metadaten gegen KDEs eigenes Schema

KDE liefert ein JSON-Schema für `KPluginMetaData` aus und nutzt es in der
eigenen CI:

```bash
curl -sO https://invent.kde.org/sysadmin/ci-utilities/-/raw/master/resources/jsonschemas/kpluginmetadata.schema.json
check-jsonschema --schemafile kpluginmetadata.schema.json $(find . -name metadata.json)
```

Es fängt Tippfehler in Personenobjekten und falsche Typen. Fehlende
Pflichtfelder fängt es **nicht** (`additionalProperties: true`, keine
Top-Level-`required`) — dafür ist der Linter oben zuständig.

### Der Rest

```bash
xmllint --noout $(find . -name '*.svg')          # XML-Wohlgeformtheit
desktop-file-validate aurorae/*/metadata.desktop  # Aurorae-Metadaten
reuse lint                                        # Lizenzkonformität
appstreamcli validate <datei>                     # AppStream, falls erzeugt
```

`reuse` ist dasselbe Werkzeug, das KDE in der CI benutzt
(`fsfe/reuse:5` als Container).

## 5.2 Stufe 2 — ein einzelnes Widget rendern

Das am meisten unterschätzte Werkzeug:

```bash
plasmawindowed org.kde.plasma.digitalclock
plasmawindowed org.kde.plasma.kickoff
```

Es rendert ein einzelnes Plasmoid in einem eigenen Fenster, mit dem aktiven
Plasma Style. Kein `plasmashell --replace`, keine Wartezeit, kein Risiko für
die laufende Session.

Für SVG-Arbeit ist das die schnellste Rückkopplung, die es gibt: Datei
speichern, Cache löschen, `plasmawindowed` neu starten.

## 5.3 Stufe 3 — Session neu laden

```bash
plasma-apply-desktoptheme meintheme
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

**Das Löschen des Caches ist nicht optional.** Ohne das siehst du deine
Änderung nicht und suchst den Fehler an der falschen Stelle. Siehe
[Kapitel 2.6](02-plasma-style.md#26-der-cache).

Weitere nützliche Kommandos:

```bash
plasma-apply-desktoptheme --list-themes
plasma-apply-colorscheme MeinSchema
plasma-apply-lookandfeel --list
plasma-apply-lookandfeel --apply com.example.meintheme   # ohne --resetLayout!
/usr/libexec/plasma-apply-aurorae MeinTheme
```

### `plasma-apply-colorscheme` lädt ein *geändertes* Schema nicht neu

Ein Fallstrick, der viel Verwirrung stiftet: Wer die `.colors`-Datei
bearbeitet und danach

```bash
plasma-apply-colorscheme MeinSchema
```

aufruft, sieht **keine Änderung** — das Schema ist ja bereits aktiv, also
tut der Befehl nichts. Die alten Farben stehen weiterhin in `kdeglobals`.

Besonders tückisch beim Zurücksetzen nach einem Test: Die `.colors`-Datei
sieht wieder richtig aus, das System zeigt aber weiter die Testfarben.

Der Umweg über ein anderes Schema erzwingt das Neuladen:

```bash
plasma-apply-colorscheme BreezeLight
plasma-apply-colorscheme MeinSchema
```

Kontrollieren lässt sich der tatsächliche Zustand nur in `kdeglobals`, nicht
in der Schemadatei:

```bash
kreadconfig6 --file kdeglobals --group "Colors:Selection" --key BackgroundNormal
```

**Dasselbe Muster bei der Fensterdekoration:** `BorderSize` wirkt weder über
`plasma-apply-*` noch über `qdbus org.kde.KWin /KWin reconfigure` — KWin
übernimmt die Rahmengröße erst beim Sitzungsstart. Ein Testlauf über alle
acht Größen ohne Neuanmeldung misst achtmal denselben Zustand.

## 5.4 Stufe 4 — Vollinstallation in der VM

**Alles, was `sudo` braucht, gehört hierhin.** Login-Manager, Plymouth und
GRUB laufen, bevor du dich anmelden kannst — ein Fehler dort kostet im
Zweifel ein Live-Medium und einen Abend.

Auch wenn dein Installer nur in `$HOME` schreibt, ist die VM der bessere
Ort: Nur dort kannst du prüfen, wie sich das Theme auf einem **frischen**
Benutzerkonto verhält. Auf deinem eigenen Rechner hast du längst
Einstellungen, die Lücken im Theme kaschieren.

Das Vorgehen, das sich bewährt hat:

1. VM einmal aufsetzen, Werkzeuge installieren
2. **Snapshot `clean`** anlegen
3. Vor jedem Testlauf auf `clean` zurücksetzen
4. Theme einspielen, installieren, Screenshot, Befund festhalten
5. Zurück zu 3

Der Snapshot ist der eigentliche Trick. Ohne ihn testet man beim zweiten
Durchlauf auf den Resten des ersten.

Dieses Projekt bringt die VM mit:

```bash
vm/build-vm.sh              # einmalig, unbeaufsichtigte Installation
vm/provision.sh             # Werkzeuge, Autologin
vm/vmctl.sh snap create clean

vm/vmctl.sh reset           # zurück auf clean, dauert Sekunden
vm/vmctl.sh push ../niceos9 /home/tester/theme
vm/vmctl.sh ssh 'cd theme && ./install.sh'
vm/vmctl.sh shot befund.png
```

**Screenshots über den Hypervisor, nicht über den Gast.** `vmctl.sh shot`
nutzt `virsh screenshot` — das funktioniert auch dann noch, wenn Plasma
abgestürzt ist oder gar keine Session mehr läuft. Genau das ist bei
Theme-Tests der interessante Fall. Ein `spectacle` im Gast kann per
Definition nichts liefern, wenn die Session weg ist.

### Was man in der VM prüft

- Installiert das Theme auf einem frischen Konto ohne Fehler?
- Sieht es auf einem frischen Konto so aus wie gedacht?
- Startet die Session nach dem Anwenden noch?
- Überlebt es einen **Neustart**? (Der häufigste Fall, in dem ein Theme
  auffällt: beim nächsten Anmelden.)
- Bringt `uninstall.sh` das System wirklich in den Ausgangszustand?
- Was hat sich im System geändert? (`rpm -Va`, Vergleich mit der Baseline)

Der Punkt „überlebt einen Neustart" ist der wichtigste und wird am
häufigsten übersprungen.

## 5.5 Headless

KWin bringt ein virtuelles Backend mit — Xvfb braucht es nicht:

```bash
kwin_wayland --virtual --width 1920 --height 1080 \
             --no-lockscreen --no-global-shortcuts \
             --exit-with-session ./tools/smoke.sh
```

`smoke.sh` startet `plasmashell`, wartet, macht einen Screenshot und
vergleicht ihn mit einem Referenzbild:

```bash
compare -metric AE referenz.png aktuell.png diff.png
```

Für ein Retro-Theme mit pixelgenauem Anspruch ist Screenshot-Vergleich
sinnvoll. KDE selbst meidet ihn bewusst und nutzt stattdessen
[selenium-webdriver-at-spi](https://invent.kde.org/sdk/selenium-webdriver-at-spi)
über AT-SPI2 — für ein Theme-Projekt ist das überdimensioniert.

## 5.6 Was KDE selbst macht

Zur Einordnung: Die CI-Konfiguration ist zentral in
`sysadmin/ci-utilities`; die Repos binden nur Vorlagen ein. `plasma/breeze`
nutzt `linux-qt6`, `freebsd-qt6`, `windows-qt6`, `xml-lint`, `yaml-lint`.
`libplasma` zusätzlich `qml-lint`.

Verfügbar und für eigene Projekte kopierbar: `clang-format`, `cppcheck`,
`json-validation`, `reuse-lint`, `qml-lint`, `xml-lint`, `yaml-lint`,
`pre-commit`, `flatpak`.

**Einen Theme-Linter gibt es in dieser Sammlung nicht.** Die SVG-Struktur
prüft niemand — das ist die Lücke, die `tools/lint-plasma-svg.py` schließt.

---

**Weiter:** [Kapitel 6 — Wenn es schiefgeht](06-recovery.md)
