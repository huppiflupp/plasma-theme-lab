# 3. Look-and-Feel-Paket

Das Look-and-Feel-Paket ist das, was in den Systemeinstellungen als
**„Globales Design"** erscheint. Es enthält selbst kaum Grafik — es ist
eine Klammer, die die anderen Ebenen zusammenschaltet.

Genau deshalb ist es die riskanteste Ebene, die noch in `$HOME` lebt: Es
schreibt in die Konfiguration des Nutzers.

---

## 3.1 Paketstruktur

Autoritativ aus dem Quellcode
[`plasma-workspace/shell/packageplugins/lookandfeel/lookandfeel.cpp`]:

```
<id>/
├── metadata.json
└── contents/
    ├── defaults                    ← das Kernstück
    ├── colors
    ├── layouts/
    │   ├── org.kde.plasma.desktop-layout.js   ← ersetzt Panels (3.4)
    │   └── defaults
    ├── previews/
    │   ├── preview.png             (400×250)
    │   ├── fullscreenpreview.jpg
    │   ├── lockscreen.png
    │   ├── splash.png
    │   └── windowswitcher.png
    ├── splash/Splash.qml
    ├── logout/Logout.qml
    └── windowswitcher/WindowSwitcher.qml
```

Der Code ruft für keinen dieser Teile `setRequired()` auf — **alles ist
optional**. Fehlende Teile kommen per `setFallbackPackage()` aus
`org.kde.breeze.desktop`.

**Es gibt keinen `lockscreen/`-Ordner mehr** und keinen `loginmanager/`.
Siehe [Kapitel 1.4](01-ebenen-und-risiko.md#wichtig-der-sperrbildschirm-gehört-nicht-mehr-ins-look-and-feel-paket) —
wer dort QML pflegt, pflegt toten Code.

## 3.2 metadata.json

```json
{
    "KPackageStructure": "Plasma/LookAndFeel",
    "KPlugin": {
        "Id": "com.github.huppiflupp.niceos9-dark",
        "Name": "NiceOS9 Dark",
        "Description": "Mac OS 9 Platinum look for Plasma 6",
        "Authors": [{ "Name": "Vorname Nachname", "Email": "mail@example.org" }],
        "License": "GPL-3.0-or-later",
        "Version": "2.1.0",
        "Website": "https://github.com/…"
    },
    "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
    "X-Plasma-APIVersion": "2"
}
```

Zwei Felder sind hier nicht optional:

**`KPackageStructure` auf oberster Ebene.** Ohne diesen Schlüssel erscheint
das Paket nicht unter „Globale Designs". Er gehört *nicht* in `KPlugin`.

**`X-Plasma-APIVersion: "2"`** ist nicht kosmetisch. `kscreenlocker` prüft
den Wert und verweigert bei `< 2` die Verwendung.
[Quelle: `kscreenlocker/greeter/greeterapp.cpp`]

**Zur `Id`:** Umgekehrte Domainnotation ist Konvention
(`org.kde.breeze.desktop`, `com.github.<nutzer>.<theme>`). Leerzeichen in
der Id vermeiden — sie werden zum Verzeichnisnamen.

**Lizenz-Strings:** `KAboutLicense::byKeyword()` normalisiert und erkennt
`"GPL-3.0-or-later"`. `"LGPL-2.1-only"` wird **nicht** erkannt und als
„Custom" angezeigt. Kein Fehler, nur eine hässliche Anzeige.

## 3.3 contents/defaults — das Kernstück

Format: `[datei][Gruppe]` gefolgt von `Schlüssel=Wert`. Die Referenz von
Breeze: [geprüft]

```ini
[kdeglobals][KDE]
widgetStyle=Breeze

[kdeglobals][General]
ColorScheme=BreezeLight

[kdeglobals][Icons]
Theme=breeze

[plasmarc][Theme]
name=default

[Wallpaper]
Image=Next

[kcminputrc][Mouse]
cursorTheme=breeze_cursors

[kwinrc][org.kde.kdecoration2]
library=org.kde.breeze
theme=Breeze

[ksplashrc][KSplash]
Theme=org.kde.breeze.desktop
```

**Merke:** Die Dekorationsgruppe heißt `org.kde.kdecoration2`, auch unter
KDecoration3. Siehe [Kapitel 1.6](01-ebenen-und-risiko.md#16-fensterdekoration-kdecoration3-aber-konfigschlüssel-kdecoration2).

Für ein Aurorae-Theme:
```ini
[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__MeinTheme
```

### Was hier nicht hineingehört

Jeder Schlüssel in `defaults` überschreibt eine Einstellung des Nutzers.
Beschränke dich auf das, was zum Erscheinungsbild gehört. Schriftarten,
Doppelklick-Verhalten, Energieeinstellungen und Tastenkürzel gehören nicht
in ein Theme — auch wenn man sie technisch dort setzen könnte.

## 3.4 Die Panel-Falle

**Der Punkt, an dem ein Theme Nutzerdaten kosten kann.**

Ein `contents/layouts/org.kde.plasma.desktop-layout.js` ist ein Skript, das
die Desktop-Konfiguration neu aufbaut:

```javascript
var panel = new Panel;
panel.location = "top";
panel.addWidget("org.kde.plasma.kickoff");
…
```

Wird es ausgeführt, sind **alle Panels, Widgets und deren Einstellungen des
Nutzers weg**. Nicht rückgängig zu machen. Wer sein Panel über Jahre
eingerichtet hat, verliert diese Arbeit beim Ausprobieren eines Themes.

### Die Entwarnung

KDE schützt an drei Stellen. Wer ein Layout ausliefern will, sollte das
kennen — es ändert die Abwägung.

**Die Checkbox ist vorab nicht angehakt.**
[Quelle: `kcms/lookandfeel/kcm.cpp`, `resetSelectedContents()`]

```cpp
// But do not select layout contents by default if there appaerance settings
if (m_themeContents & KLookAndFeelManager::AppearanceSettings) {
    resetContents &= ~KLookAndFeelManager::LayoutSettings;
}
```

Sobald ein Theme auch Erscheinungsbild-Einstellungen mitbringt — was jedes
ernsthafte Theme tut —, ist „Arbeitsflächen- und Fenster-Layout"
ausgeschaltet, wenn der Dialog aufgeht.

**Es gibt eine Warnung.** `SimpleOptions.qml` blendet unter der Checkbox
eine rote `InlineMessage` ein, sobald man sie anhakt: *„Durch das Anwenden
eines Arbeitsflächen-Layouts werden die aktuellen Arbeitsflächen,
Kontrollleisten, Docks und Miniprogramme gelöscht."*

**Die Kommandozeile fasst das Layout nicht an.**
[Quelle: `kcms/lookandfeel/tool/lnftool.cpp`, geprüft]

```cpp
// By default do not modify the layout, unless explicitly specified
KLookAndFeelManager::Contents selection =
    KLookAndFeelManager::AppearanceSettings | KLookAndFeelManager::BlendChanges;
if (parser.isSet(_resetLayout)) { selection |= KLookAndFeelManager::LayoutSettings; }
```

```console
$ plasma-apply-lookandfeel --help
  -a, --apply <Paketname>    Ein globales Design-Paket anwenden.
      --resetLayout          Das Plasma-Arbeitsflächen-Layout zurücksetzen
```

`plasma-apply-lookandfeel --apply <name>` fasst das Layout also nicht an.
Nur `--resetLayout` tut es.

**Aber:** Diese drei Netze fangen den Nutzer, der versehentlich klickt.
Sie fangen nicht den, der die Checkbox bewusst anhakt — und das tut, wer
das Theme so sehen will, wie es gemeint ist. Für den ist der Verlust
seiner Panelkonfiguration endgültig.

### Was daraus folgt

Ein Layout auszuliefern ist legitim. Bei einem Theme, dessen Aufbau zum
Look gehört — Menüleiste oben, kein schwebendes Panel —, wäre es sogar
unvollständig ohne. Was fehlt, ist der Rückweg.

**Sichere die Panelkonfiguration im Installer, bevor du irgendetwas
änderst:**

```bash
BACKUP="$HOME/.local/share/<theme>/panel-backup-$(date +%F-%H%M).rc"
mkdir -p "$(dirname "$BACKUP")"
cp -a "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "$BACKUP" 2>/dev/null
echo "Panel-Konfiguration gesichert: $BACKUP"
```

Vier Zeilen, und aus „unwiderruflich" wird „Datei zurückkopieren, neu
anmelden". Das ist der Unterschied zwischen einem Theme, das man
ausprobieren kann, und einem, bei dem man vorher überlegt.

### Panel-Preset statt Layout-Zwang

Es gibt ein Paketformat genau für diesen Zweck: **`Plasma/LayoutTemplate`**.

```
layout-templates/org.example.meintheme.panel/
├── metadata.json          ← "KPackageStructure": "Plasma/LayoutTemplate"
└── contents/
    └── layout.js
```

```bash
kpackagetool6 -t Plasma/LayoutTemplate -i ./layout-templates/org.example.meintheme.panel
```

Ein Layout-Template erscheint beim Rechtsklick unter **„Panel hinzufügen"**
und legt ein *zusätzliches* Panel an. Es überschreibt nichts. Der Nutzer
entscheidet.

**Empfehlung:** Beides anbieten. Das `layouts/` im Look-and-Feel für
alle, die das Theme vollständig wollen — abgesichert durch das Backup
oben. Zusätzlich ein Layout-Template für alle, die ihr eingerichtetes
Panel behalten und den Aufbau nur daneben ausprobieren wollen. In der
README ein Satz dazu: „Das passende Panel gibt es auch einzeln — per
Rechtsklick auf den Desktop → Panel hinzufügen → NiceOS9."

Nebeneffekt: Layout-Skripte enthalten oft absolute Pfade (Hintergrundbild),
die der Installer per `sed` einsetzen muss. Ohne Layout-Skript entfällt
dieser Hack.

## 3.5 Vorschaubilder

`contents/previews/preview.png` ist das, was der Nutzer im
Auswahldialog sieht. Fehlt es, steht dort ein graues Rechteck — der
häufigste Grund, warum ein gutes Theme im Store übersehen wird.

| Datei | Wo sichtbar |
|---|---|
| `preview.png` | Kachel in der Design-Auswahl (400×250) |
| `fullscreenpreview.jpg` | Großansicht |
| `lockscreen.png` | Vorschau Sperrbildschirm |
| `splash.png` | Vorschau Startbildschirm |
| `windowswitcher.png` | Vorschau Fensterwechsler |

## 3.6 Startbildschirm (KSplash)

`contents/splash/Splash.qml` — eine QML-Datei, die beim Anmelden gezeigt
wird. Sie bekommt eine Eigenschaft `stage`, die von 1 bis 6 hochzählt.

Zwei Dinge, die man wissen muss: Der Startbildschirm läuft in einem sehr
frühen Sessionzustand — nutze nur `QtQuick`, keine Plasma-Komponenten. Und
er lässt sich einzeln testen:

```bash
ksplashqml --test <paket-id>
```

---

**Weiter:** [Kapitel 4 — Bauen und Installieren](04-bauen-und-installieren.md)
