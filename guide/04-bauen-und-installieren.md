# 4. Bauen und Installieren

Die meisten Theme-Projekte installieren mit `cp -r` aus einem
`install.sh`. Das funktioniert, bis man es zurücknehmen oder eine zweite
Variante pflegen will. Dieses Kapitel zeigt, was stattdessen geht.

---

## 4.1 Warum nicht `cp -r`

Ein typischer Installer sieht so aus:

```bash
rm -rf "$HOME/.local/share/plasma/desktoptheme/meintheme"
cp -r desktoptheme/meintheme "$HOME/.local/share/plasma/desktoptheme/"
```

Vier Probleme:

**Keine Prüfung.** Ein Tippfehler in `metadata.json` fällt erst auf, wenn
der Nutzer das Theme nicht in der Liste findet.

**Keine saubere Deinstallation.** Das `uninstall.sh` muss die Liste der
Pfade doppelt pflegen. Vergisst man einen, bleibt Müll liegen. Schlimmer:
Löscht man Dateien, ohne die Konfiguration zurückzusetzen, bleibt der
Nutzer mit einem halb kaputten System zurück — `plasmarc` zeigt auf ein
Theme, das es nicht mehr gibt.

**Kein `.svgz`.** Ausgeliefert wird, was im Repo liegt.

**Versionen werden von Hand gepflegt.** Bei drei Varianten steht die
Versionsnummer an drei Stellen. Beim Release ändert man zwei davon.

## 4.2 Der Mittelweg ohne CMake

Wer kein CMake will, kommt mit einem `Makefile` und `kpackagetool6` weit:

```makefile
VERSION  := 2.1.0
BUILD    := build
PREFIX   ?= $(HOME)/.local

VARIANTS := niceos9 niceos9-dark niceos9-charcoal

.PHONY: all clean install uninstall check

all: $(BUILD)/.stamp

# metadata.json aus einer Vorlage erzeugen - die Version steht nur hier
$(BUILD)/.stamp: $(shell find desktoptheme -type f)
	@rm -rf $(BUILD); mkdir -p $(BUILD)
	@for v in $(VARIANTS); do \
	    cp -r desktoptheme/$$v $(BUILD)/$$v; \
	    sed "s/@VERSION@/$(VERSION)/" desktoptheme/$$v/metadata.json.in \
	        > $(BUILD)/$$v/metadata.json; \
	    rm -f $(BUILD)/$$v/metadata.json.in; \
	    find $(BUILD)/$$v -name '*.svg' -exec sh -c \
	        'gzip -9 -n -c "$$1" > "$${1}z" && rm "$$1"' _ {} \; ; \
	done
	@touch $@

install: all
	@for v in $(VARIANTS); do \
	    kpackagetool6 -t Plasma/Theme -u $(BUILD)/$$v 2>/dev/null || \
	    kpackagetool6 -t Plasma/Theme -i $(BUILD)/$$v; \
	done

uninstall:
	@for v in $(VARIANTS); do kpackagetool6 -t Plasma/Theme -r $$v || true; done

clean:
	rm -rf $(BUILD)
```

Das erledigt die drei wichtigsten Punkte: eine Versionsnummer,
`.svgz`-Kompression, geprüfte Installation.

## 4.3 kpackagetool6

Der offizielle Weg, KDE-Pakete zu installieren. [geprüft, Plasma 6.7.3]

```bash
kpackagetool6 -t Plasma/Theme       -i ./meintheme       # installieren
kpackagetool6 -t Plasma/Theme       -u ./meintheme       # aktualisieren
kpackagetool6 -t Plasma/Theme       -r meintheme         # entfernen
kpackagetool6 -t Plasma/Theme       -l                   # auflisten
kpackagetool6 -t Plasma/Theme       -s meintheme         # Metadaten zeigen
kpackagetool6 -t Plasma/LookAndFeel -i ./com.example.meintheme
kpackagetool6 -t Plasma/LayoutTemplate -i ./org.example.meintheme.panel
sudo kpackagetool6 -g -t Plasma/Theme -i ./meintheme     # systemweit
```

`-i` und `-u` akzeptieren ein Verzeichnis **oder** ein Archiv
(`.tar.gz`, `.zip`).

Die Typen, die für Themes zählen:

| Typ | Zielverzeichnis |
|---|---|
| `Plasma/Theme` | `plasma/desktoptheme/` |
| `Plasma/LookAndFeel` | `plasma/look-and-feel/` |
| `Plasma/LayoutTemplate` | `plasma/layout-templates/` |
| `KWin/Aurorae` | `aurorae/themes/` |
| `Plasma/Applet` | `plasma/plasmoids/` |

**Was es nicht gibt:** `kpackagetool6 --validate`. Ältere Anleitungen
erwähnen es; im Hilfetext von 6.7.3 kommt es nicht vor. [geprüft]
Zur Metadatenprüfung siehe [Kapitel 5](05-testen.md).

Farbschemata und Aurorae-Themes werden weiterhin einfach kopiert:
```bash
install -Dm644 color-schemes/*.colors -t "$HOME/.local/share/color-schemes/"
cp -r aurorae/MeinTheme "$HOME/.local/share/aurorae/themes/"
```

## 4.4 Varianten ohne Duplikate

Das häufigste Wartungsproblem: drei Farbvarianten, drei SVG-Bäume, jeder
Fix dreimal.

### Wie Breeze es löst

Breeze liefert **einen** SVG-Satz aus, unter dem Namen `default`. Die
Varianten `breeze-light` und `breeze-dark` enthalten: [geprüft]

```console
$ ls /usr/share/plasma/desktoptheme/breeze-light/
colors  metadata.json  plasmarc
```

**Keine einzige SVG-Datei.** Das funktioniert, weil

1. fehlende Dateien auf `default` zurückfallen, und
2. die Breeze-SVGs ihre Farben über `current-color-scheme`-Stylesheets aus
   der `colors`-Datei der jeweiligen Variante beziehen.

### Der Haken für eigene Themes

Der Fallback geht **immer** auf `default`, also auf Breeze — nicht auf dein
Basis-Theme. `meintheme-dark` ohne SVGs zeigt also Breeze-Grafik mit
deinen Farben, nicht deine Grafik.

Daraus folgen zwei gangbare Wege:

**Weg A — eine Variante als Plasma Style, Varianten über das Farbschema.**
Du lieferst genau *einen* Plasma Style aus. Die Varianten entstehen durch
verschiedene Farbschemata und verschiedene Look-and-Feel-Pakete, die
jeweils denselben Plasma Style setzen:

```ini
# look-and-feel/…niceos9-dark/contents/defaults
[plasmarc][Theme]
name=niceos9                 ← derselbe Style für alle Varianten
[kdeglobals][General]
ColorScheme=NiceOS9Dark      ← hier entsteht der Unterschied
```

**Das ist der wartungsärmste Weg** und exakt der Grund, warum Breeze so
gebaut ist: ein SVG-Satz, mehrere globale Designs.

Voraussetzung: Deine SVGs nutzen konsequent `class="ColorScheme-*"` und
`fill="currentColor"`. Ohne das lassen sie sich nicht umfärben.

**Weg B — SVGs beim Bauen in jede Variante kopieren.** Wenn Varianten sich
in der *Form* unterscheiden sollen, nicht nur in der Farbe. Im Repo liegt
ein Satz, das Build-Skript kopiert ihn in alle Varianten. Kostet
Plattenplatz, aber keine doppelte Pflege.

Was du **nicht** tun solltest: drei SVG-Bäume ins Repository legen.

### Farbschemata generieren

Bei mehreren Varianten lohnt sich Generierung aus einer Palette.
[Catppuccin für KDE](https://github.com/catppuccin/kde) macht das
vorbildlich: aus einer Palettendatei entstehen über 60 `.colors`-Dateien.

Für drei Varianten reicht ein kurzes Python-Skript:

```python
# tools/gen-colors.py
PALETTEN = {
    "NiceOS9Bright":   {"bg": "221,221,221", "fg": "0,0,0",       "hl": "0,0,128"},
    "NiceOS9Dark":     {"bg": "44,42,40",    "fg": "230,226,220", "hl": "180,200,255"},
    "NiceOS8Charcoal": {"bg": "60,60,60",    "fg": "220,220,220", "hl": "128,128,160"},
}
VORLAGE = open("templates/colorscheme.in").read()
for name, farben in PALETTEN.items():
    text = VORLAGE
    for schluessel, wert in {**farben, "name": name}.items():
        text = text.replace(f"@{schluessel}@", wert)
    open(f"color-schemes/{name}.colors", "w").write(text)
```

Wichtig: Generierte Dateien gehören mit ins Repository (der Nutzer soll
nicht Python brauchen), aber die Vorlage ist die Quelle der Wahrheit. Ein
CI-Job, der prüft, ob die generierten Dateien aktuell sind, verhindert
Abweichungen.

## 4.5 Rollback ist Teil der Installation

Ein `uninstall.sh`, das nur Dateien löscht, reicht nicht. Wenn dein
Installer `plasmarc` und `kdeglobals` ändert, muss er die alten Werte
sichern:

```bash
# Im Installer, VOR jeder Änderung:
RESTORE="$HOME/.local/share/meintheme/restore.sh"
mkdir -p "$(dirname "$RESTORE")"
{
    echo '#!/usr/bin/env bash'
    echo '# Automatisch erzeugt - stellt den Stand vor der Installation wieder her.'
    echo "kwriteconfig6 --file plasmarc --group Theme --key name \
'$(kreadconfig6 --file plasmarc --group Theme --key name)'"
    echo "kwriteconfig6 --file kdeglobals --group General --key ColorScheme \
'$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)'"
    echo "kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle \
'$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)'"
    echo "kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library \
'$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library)'"
} > "$RESTORE"
chmod +x "$RESTORE"
echo "Rückweg gesichert: $RESTORE"
```

Diese eine Datei ist der Unterschied zwischen „ich probiere das mal aus"
und „ich traue mich nicht".

## 4.6 Veröffentlichen

Das Format für den KDE Store ist ein schlichtes **`.tar.gz`**. Ein
`.plasma`-Format gibt es nicht.

Zwei Stolpersteine: [geprüft an `/usr/share/knsrcfiles/`]

**Plasma Styles brauchen ein Tag.** `plasma-themes.knsrc` filtert mit
`TagFilter=ghns_excluded!=1,plasma##version==5`. Ein Plasma Style ohne das
Tag `plasma##version==5` erscheint **nicht** unter „Neue Plasma-Stile
holen" — auch 2026 nicht.

**Globale Designs werden als ausführbar markiert.** `lookandfeel.knsrc`
setzt `ContentWarning=Executables`, weil Look-and-Feel-Pakete
Layout-Skripte enthalten können. Der Nutzer bekommt eine Warnung. Ein
weiteres Argument, [kein `layouts/` auszuliefern](03-look-and-feel.md#panel-preset-statt-layout-zwang).

### Lizenzen

Für ein Projekt außerhalb von KDE ist nichts davon Pflicht, aber billig zu
haben und macht das Projekt paketierbar (Fedora und Debian fragen genau
danach):

- SPDX-Kopf in jeder Textdatei:
  ```
  SPDX-FileCopyrightText: 2026 Name <mail@example.org>
  SPDX-License-Identifier: GPL-3.0-or-later
  ```
- `LICENSES/<SPDX-Id>.txt` je verwendeter Lizenz (`reuse download <ID>`)
- Binärdateien über `.license`-Sidecar oder `REUSE.toml`
- Für Grafik ist `CC-BY-SA-4.0` die übliche Wahl

Bei einem Retro-Nachbau ist die **Herkunft der Assets** die heiklere Frage
als das Dateiformat. Schriften und Grafiken aus einem kommerziellen
Betriebssystem sind nicht automatisch frei, auch Nachbauten nicht. Die
Lizenz jeder übernommenen Schrift gehört explizit dokumentiert.

---

**Weiter:** [Kapitel 5 — Testen](05-testen.md)
