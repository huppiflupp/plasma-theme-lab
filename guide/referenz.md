# Referenzkarte

Alles Nachschlagbare auf einer Seite. Geprüft auf Plasma 6.7.3.

---

## Pfade

| Was | Nutzerlokal (`~/.local/share/`) | Systemweit (`/usr/share/`) |
|---|---|---|
| Plasma Style | `plasma/desktoptheme/<name>/` | dito |
| Look-and-Feel | `plasma/look-and-feel/<id>/` | dito |
| Layout-Template | `plasma/layout-templates/<id>/` | dito |
| Farbschema | `color-schemes/<Name>.colors` | dito |
| Aurorae | `aurorae/themes/<name>/` | dito |
| Icons / Cursor | `icons/<name>/` | dito |
| Hintergrundbilder | `wallpapers/<name>/` | dito |
| Schriften | `fonts/` | `/usr/share/fonts/` |
| Sperrbildschirm | — | `plasma/shells/org.kde.plasma.desktop/contents/lockscreen/` |
| SDDM-Themes | — | `/usr/share/sddm/themes/<name>/` |

Cache: `~/.cache/plasma_theme_<name>_v<version>.kcache`, `~/.cache/ksvg-elements`

## Kommandos

```bash
# Anwenden
plasma-apply-desktoptheme <name>          # --list-themes
plasma-apply-colorscheme <Name>
plasma-apply-lookandfeel --apply <id>     # --list, --resetLayout (VORSICHT)
plasma-apply-cursortheme <name>
plasma-apply-wallpaperimage <datei>
/usr/libexec/plasma-apply-aurorae <name>

# Paketverwaltung
kpackagetool6 -t Plasma/Theme -i|-u|-r|-l|-s <ziel>
kpackagetool6 --list-types

# Konfiguration lesen/schreiben
kreadconfig6  --file <datei> --group <gruppe> --key <schlüssel>
kwriteconfig6 --file <datei> --group <gruppe> --key <schlüssel> <wert>

# Neu laden
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service

# Einzeltest
plasmawindowed org.kde.plasma.digitalclock
ksplashqml --test <id>
kwin_wayland --virtual --width 1920 --height 1080 --exit-with-session <skript>
```

**Gibt es nicht:** `kpackagetool6 --validate`, `--generate-index`.

## Konfigurationsschlüssel

| Ebene | Datei | Gruppe | Schlüssel | Breeze-Wert |
|---|---|---|---|---|
| Plasma Style | `plasmarc` | `Theme` | `name` | `default` |
| Farbschema | `kdeglobals` | `General` | `ColorScheme` | `BreezeLight` |
| Anwendungsstil | `kdeglobals` | `KDE` | `widgetStyle` | `Breeze` |
| Icons | `kdeglobals` | `Icons` | `Theme` | `breeze` |
| Globales Design | `kdeglobals` | `KDE` | `LookAndFeelPackage` | `org.kde.breeze.desktop` |
| Startbildschirm | `ksplashrc` | `KSplash` | `Theme` | `org.kde.breeze.desktop` |
| Dekoration | `kwinrc` | `org.kde.kdecoration2` | `library` | `org.kde.breeze` |
| Dekoration | `kwinrc` | `org.kde.kdecoration2` | `theme` | `Breeze` |
| Mauszeiger | `kcminputrc` | `Mouse` | `cursorTheme` | `breeze_cursors` |

**Merke:** `kdecoration2`, auch unter KDecoration3. Und der Plasma Style von
Breeze heißt `default`, nicht `breeze`.

## SVG-Element-IDs

**9-Patch:** `topleft` `top` `topright` `left` `center` `right`
`bottomleft` `bottom` `bottomright`

Auch gültig: nur `left`/`center`/`right` (horizontal), nur
`top`/`center`/`bottom` (vertikal), nur `center`.

**Zustandspräfixe** (Beispiel `button.svg`): `normal-` `hover-` `pressed-`
`focus-` `shadow-` `toolbutton-hover-` `mask-normal-`

Ein Präfix gilt als vorhanden, wenn `<präfix>-center` existiert — sonst nichts.

**hint-IDs:**

| ID | Wirkung |
|---|---|
| `hint-tile-center` | center kacheln statt strecken |
| `hint-stretch-borders` | Kanten strecken statt kacheln |
| `hint-compose-over-border` | center unter die Ränder zeichnen |
| `hint-{top,right,bottom,left}-margin` | Innenabstand |
| `hint-{top,right,bottom,left}-inset` | Rahmen nach innen (Schatten, Float) |
| `hint-apply-color-scheme` | monochrom einfärben (nur ohne `colors`) |
| `hint-focus-over-base` | Fokus über Basis |
| `hint-size`, `hint-bar-size`, `hint-scrollbar-size` | Größenvorgaben |

**Farbklassen** (vollständig, aus Breeze extrahiert):

```
ColorScheme-Text              ColorScheme-Background
ColorScheme-Highlight         ColorScheme-Frame
ColorScheme-ViewText          ColorScheme-ViewBackground
ColorScheme-ViewHover         ColorScheme-ViewFocus
ColorScheme-ButtonText        ColorScheme-ButtonBackground
ColorScheme-ButtonHover       ColorScheme-ButtonFocus
ColorScheme-NegativeText      ColorScheme-NeutralText
ColorScheme-PositiveText
```

Immer zusammen mit `fill="currentColor"` bzw. `stroke="currentColor"`.

## Breeze im Quellcode

| Artefakt | Repo |
|---|---|
| **Plasma Style** | `plasma/libplasma` → `src/desktoptheme/{breeze,breeze-light,breeze-dark}/` |
| Qt-Style + Dekoration | `plasma/breeze` → `kstyle/`, `kdecoration/` |
| Farbschemata | `plasma/breeze` → `colors/` |
| Look-and-Feel-Pakete | `plasma/plasma-workspace` → `lookandfeel/` |
| SDDM-Theme | `plasma/plasma-desktop` → `sddm-theme/` |
| Icons | `frameworks/breeze-icons` |
| SVG-Werkzeuge | `frameworks/ksvg` → `src/tools/` |

**Häufigster Irrtum:** Das Repo `plasma/breeze` enthält **keinen** Plasma
Style. Der liegt in `libplasma`.

## Paketstruktur

**Plasma Style** (`metadata.json`):
```json
{ "KPlugin": { "Id": "…", "Name": "…", "Version": "1.0.0",
               "License": "GPL-3.0-or-later", "EnabledByDefault": true },
  "X-Plasma-API": "5.0" }
```

**Look-and-Feel** (`metadata.json`) — `KPackageStructure` ist Pflicht:
```json
{ "KPackageStructure": "Plasma/LookAndFeel",
  "KPlugin": { … },
  "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
  "X-Plasma-APIVersion": "2" }
```

**Aurorae** (`metadata.desktop` — hier korrekt, kein Legacy):
```ini
[Desktop Entry]
Name=…
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__<Ordnername>
```

## Verifikation

```bash
tools/lint-plasma-svg.py <theme> --vergleich /usr/share/plasma/desktoptheme/default
xmllint --noout $(find . -name '*.svg')
check-jsonschema --schemafile kpluginmetadata.schema.json $(find . -name metadata.json)
desktop-file-validate aurorae/*/metadata.desktop
reuse lint
```

Schema: `https://invent.kde.org/sysadmin/ci-utilities/-/raw/master/resources/jsonschemas/kpluginmetadata.schema.json`

## Notausgang

```bash
plasma-apply-lookandfeel --apply org.kde.breeze.desktop
plasma-apply-desktoptheme default

# aus dem TTY:
export XDG_RUNTIME_DIR=/run/user/$(id -u)
kwriteconfig6 --file plasmarc --group Theme --key name default
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
rm -f ~/.cache/plasma_theme_*.kcache

# Panels zurücksetzen (löscht alle Widget-Einstellungen):
mv ~/.config/plasma-org.kde.plasma.desktop-appletsrc{,.bak}

# Grafische Anmeldung abschalten:
sudo systemctl set-default multi-user.target
```

## Fallstricke

| Symptom | Ursache |
|---|---|
| Änderung wirkt nicht | Cache — `rm ~/.cache/plasma_theme_*.kcache` |
| Theme erscheint nicht in der Liste | `metadata.json` fehlerhaft, oder Ordnername ≠ erwartet |
| Globales Design fehlt in der Auswahl | `KPackageStructure` fehlt |
| Dekoration wird nicht gesetzt | Gruppe `kdecoration3` statt `kdecoration2` benutzt |
| Farben werden nicht ersetzt | `fill="currentColor"` fehlt |
| Hover-Effekt fehlt | `hover-center` fehlt — Plasma meldet das nicht |
| Panel-Geometrie falsch | `hint-*-inset` fehlt |
| SDDM-Theme wirkt nicht | System nutzt `plasmalogin` — keine QML-Themes |
| Sperrbildschirm-QML wirkt nicht | gehört ins Shell-Paket, nicht ins Look-and-Feel |
| Nutzer verliert seine Panels | Layout-Skript im Look-and-Feel-Paket |
| Nutzer sieht altes Theme nach Update | `KPlugin.Version` nicht hochgezählt |
