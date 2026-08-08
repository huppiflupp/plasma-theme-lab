# 1. Die sieben Ebenen und ihr Risiko

„Ein Theme" gibt es in Plasma nicht. Es gibt sieben voneinander unabhängige
Ebenen und ein Bündelpaket, das sie zusammenschaltet. Sie greifen **nicht**
ineinander — jede kann für sich kaputt oder unvollständig sein, ohne dass
die anderen es merken.

Das ist der häufigste Anfängerfehler: Man ändert den Plasma Style und
wundert sich, warum Dolphin unverändert aussieht. Der Plasma Style färbt
die Shell. Dolphin ist eine Qt-App und hört auf eine ganz andere Ebene.

---

## 1.1 Die Übersicht

| # | Ebene | Ort (nutzerlokal) | Metadaten | Wirkt auf |
|---|---|---|---|---|
| 1 | **Plasma Style** | `~/.local/share/plasma/desktoptheme/<name>/` | `metadata.json` | Panel, Plasmoids, Tooltips, OSD, Benachrichtigungen — **nur die Shell** |
| 2 | **Farbschema** | `~/.local/share/color-schemes/<Name>.colors` | INI in der Datei selbst | Qt-Apps **und** Shell |
| 3 | **Anwendungsstil** (QStyle) | Plugin `.so` | Plugin-JSON | **nur Qt-Widget-Apps** |
| 4 | **Fensterdekoration** | `~/.local/share/aurorae/themes/<name>/` | `metadata.desktop` | Titelleisten, Rahmen |
| 5 | **Symbole** | `~/.local/share/icons/<name>/` | `index.theme` | Icons überall |
| 6 | **Mauszeiger** | `~/.local/share/icons/<name>/cursors/` | `index.theme` | Zeiger |
| 7 | **Startbildschirm** (KSplash) | im Look-and-Feel-Paket | — | Ladebildschirm |
| ★ | **Look-and-Feel** („Globales Design") | `~/.local/share/plasma/look-and-feel/<id>/` | `metadata.json` + `KPackageStructure` | bündelt 1–7 über `contents/defaults` |

Der frühere Name „Desktop Theme" für Ebene 1 ist überholt; die Oberfläche
sagt heute **Plasma-Stil**. Der Verzeichnisname `desktoptheme` blieb.

---

## 1.2 Die entscheidende Frage: Wer färbt was?

Diese Verwirrung kostet die meiste Zeit. Sortiert nach dem, was du siehst:

| Was du färben willst | Zuständige Ebene |
|---|---|
| Panel / Taskleiste | Plasma Style (`widgets/panel-background.svg`) |
| Anwendungsstarter, Widgets im Panel | Plasma Style |
| Benachrichtigungen, Tooltips, OSD | Plasma Style |
| Titelleiste eines Fensters | Fensterdekoration (Aurorae) |
| Menüleiste und Werkzeugleiste **in** Dolphin | Anwendungsstil + Farbschema |
| Buttons und Eingabefelder **in** Dolphin | Anwendungsstil (QStyle) |
| Systemeinstellungen, Discover (QML/Kirigami) | Farbschema — **nicht** der Anwendungsstil |
| Sperrbildschirm | Shell-Paket (**nicht** mehr Look-and-Feel, s. 1.4) |
| Anmeldebildschirm | Login-Manager (s. 1.5) |

Der Anwendungsstil ist kompilierter C++-Code (`KStyle`/`QCommonStyle`), kein
Datenformat. Man kann ihn nicht „malen". Wer echte eigene Buttons in
Qt-Apps will, hat drei Optionen: Breeze/Fusion akzeptieren,
[Kvantum](#kvantum) nehmen, oder einen QStyle forken.

### Kvantum

[Kvantum](https://github.com/tsujan/Kvantum) ist ein QStyle, der sein
Aussehen aus SVG + INI zieht — der einzige realistische Weg zu eigenen
Qt-Widgets ohne C++. Aktiv gepflegt (Stand 2026-08).

**Aber:** Kvantum färbt *nur* Qt-Widget-Apps. Plasma-Shell, Panel,
Plasmoids, KRunner und die Systemeinstellungen bleiben unberührt — die
kommen aus dem Plasma Style bzw. dem Farbschema.

Kvantum ist eine externe Abhängigkeit, die der Nutzer installiert haben
muss. Setzt dein `contents/defaults` `widgetStyle=kvantum` und Kvantum
fehlt, landet der Nutzer bei einem ungestylten Fallback. **Als optionale
Zusatzkomponente sinnvoll, als Pflichtbestandteil nicht.** WhiteSur und
Colloid machen es genau so: Kvantum liegt bei, wird aber separat installiert.

---

## 1.3 Risikoklassen — die wichtigste Tabelle im ganzen Leitfaden

| Ebene | Risiko | Warum |
|---|---|---|
| Plasma Style | **niedrig** | Fallback auf `default` ist fest im Code verdrahtet |
| Farbschema | **niedrig** | schlimmstenfalls unleserlich, per CLI umkehrbar |
| Anwendungsstil | niedrig | fehlendes Plugin → Fusion |
| Fensterdekoration | niedrig | KWin fällt auf Breeze zurück |
| Symbole / Mauszeiger | niedrig | Fallback über `Inherits` bzw. `hicolor` |
| Look-and-Feel | **mittel** | schreibt in `kdeglobals`/`kwinrc`; ein Layout-Skript löscht Panels |
| **Login-Manager** | **hoch** | systemweit, greift *vor* dem Login → schwarzer Bildschirm ohne GUI-Rettung |
| **Plymouth / GRUB** | **hoch** | initramfs bzw. Bootloader — schlimmstenfalls startet der Rechner nicht mehr |

**Die Trennlinie verläuft zwischen Zeile 6 und 7.** Alles darüber lebt in
`$HOME` und ist aus einem TTY in einer Minute repariert. Alles darunter
läuft, bevor du dich anmelden kannst.

Praktische Konsequenz für dein Projekt:

```
theme/
├── install.sh            # nur $HOME, kein sudo, jederzeit ausprobierbar
└── risky/                # eigener Ordner, eigene Warnung, Default = nein
    ├── install-sddm.sh
    ├── install-plymouth.sh
    └── install-grub.sh
```

Ein `install.sh`, das nach `sudo` fragt und im selben Durchlauf GRUB
anfasst, ist unabhängig von seiner Codequalität ein Konstruktionsfehler.

---

## 1.4 Plasma ist robuster als sein Ruf — vier Sicherheitsnetze

Es hilft zu wissen, was Plasma von sich aus abfängt. Das schont die Nerven
und verhindert, dass man Schutzmechanismen nachbaut, die es schon gibt.

**Fehlende SVG-Datei → Breeze.** [Quelle: `ksvg/src/ksvg/private/imageset_p.cpp`]
Die Fallback-Kette ist hart auf `default` verdrahtet:
```cpp
fallbackImageSets = {ImageSetPrivate::defaultImageSet};   // "default"
```
Ein konfigurierbarer Fallback existiert **nicht** mehr. Die Doku auf
develop.kde.org nennt weiterhin `[Settings] FallbackTheme=oxygen` in der
`plasmarc` — dieser Schlüssel wird im aktuellen Code nirgends gelesen.

**Fehlende Element-ID → stiller Verzicht.** [Quelle: `ksvg` `FrameSvg::hasElementPrefix()`]
Geprüft wird ausschließlich, ob `<prefix>-center` existiert. Fehlt es, wird
der Präfix leer gesetzt. Kein Absturz — aber auch **keine Warnung**. Genau
deshalb braucht man einen [eigenen Linter](05-testen.md#stufe-1-statische-prüfungen).

**Plasmashell-Absturzschleife ist gedeckelt.** [geprüft]
`/usr/lib/systemd/user/plasma-plasmashell.service`:
```ini
StartLimitIntervalSec=60s
StartLimitBurst=3
ExecStart=/usr/bin/plasmashell --no-respawn
```
Nach drei Fehlstarts in 60 Sekunden gibt systemd auf. Es gibt keine
endlose Schleife. KWin und die Session laufen weiter — nur Panel und
Desktop fehlen. Fenstertastenkürzel funktionieren noch.

**Der Sperrbildschirm kann niemanden aussperren.** [Quelle: `kscreenlocker/greeter/greeterapp.cpp`]
```cpp
// on error, load the fallback lockscreen to not lock the user out of the system
static const QUrl fallbackUrl(QStringLiteral("qrc:/fallbacktheme/LockScreen.qml"));
```
Der Fallback ist in die Binärdatei einkompiliert.

### Wichtig: Der Sperrbildschirm gehört nicht mehr ins Look-and-Feel-Paket

Das ist die folgenreichste Plasma-6-Änderung für Theme-Autoren.
[Quelle: `greeterapp.cpp`, geprüft an `/usr/share/plasma/shells/`]

Der Sperrbildschirm wird aus dem **Shell**-Paket geladen:
```
/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/
```
Das Look-and-Feel-Paketformat kennt **keinen** `lockscreen`-Ordner mehr —
nur noch `previews/lockscreen.png`, also das Vorschaubild.

**Ein `look-and-feel/<x>/contents/lockscreen/LockScreen.qml` ist unter
Plasma 6 toter Code.** Er wird nie geladen. Die Portierungsseite auf
develop.kde.org erwähnt ihn noch; das ist veraltet.

---

## 1.5 Der Login-Manager hat sich 2025/26 geändert

Auf Fedora 44, Nobara 44 und KDE Linux ist **SDDM nicht mehr installiert**.
An seiner Stelle läuft der **Plasma Login Manager** (`plasmalogin`), ein
SDDM-Fork, den KDE seit etwa Plasma 6.6 selbst pflegt. [geprüft]

```console
$ readlink -f /etc/systemd/system/display-manager.service
/usr/lib/systemd/system/plasmalogin.service
$ rpm -q sddm
Das Paket sddm ist nicht installiert
```

Seine Konfiguration liegt in `/etc/plasmalogin.conf` und hat **keine
`[Theme]`-Sektion**. Unter `/usr/share/plasmalogin/` gibt es kein
`themes/`-Verzeichnis.

**Konsequenz: Der Plasma Login Manager unterstützt keine QML-Themes.**
Konfigurierbar ist im Wesentlichen das Hintergrundbild.

Wenn dein Projekt ein SDDM-Theme mitbringt, braucht es deshalb eine
Erkennung — sonst kopierst du Dateien in ein Verzeichnis, das niemand liest:

```bash
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    echo "Dieses System nutzt den Plasma Login Manager."
    echo "Er unterstützt keine QML-Themes - der Anmeldebildschirm bleibt unverändert."
    echo "Konfigurierbar ist nur das Hintergrundbild."
elif [ -f /usr/lib/systemd/system/sddm.service ]; then
    # klassischer SDDM-Pfad
    sudo cp -r sddm/mein-theme /usr/share/sddm/themes/
fi
```

Ob KDE für den Plasma Login Manager perspektivisch Themes vorsieht, ist
offen. **[unsicher]**

---

## 1.6 Fensterdekoration: KDecoration3, aber Konfigschlüssel `kdecoration2`

Eine Stolperfalle, die viel Zeit kostet. Plasma 6 nutzt **KDecoration3** —
das Plugin-Verzeichnis heißt `/usr/lib64/qt6/plugins/org.kde.kdecoration3/`.
[geprüft]

**Der Konfigurationsschlüssel heißt aber weiterhin `org.kde.kdecoration2`.**
[Quelle: `kwin/src/decorations/decorationbridge.cpp`]

```cpp
static const QString s_pluginName    = QStringLiteral("org.kde.kdecoration3");
static const QString s_configKeyName = QStringLiteral("org.kde.kdecoration2");
static const QString s_defaultPlugin = QStringLiteral("org.kde.breeze");
```

Lokal bestätigt:
```console
$ kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library
org.kde.breeze
$ kreadconfig6 --file kwinrc --group org.kde.kdecoration3 --key library
              # leer
```

**Wer in `contents/defaults` `[kwinrc][org.kde.kdecoration3]` schreibt,
erreicht nichts.** Die Gruppe muss `org.kde.kdecoration2` heißen — auch
2026, auch unter KDecoration3.

Es gibt zwei Aurorae-Engines: die klassische (`org.kde.kwin.aurorae`) und
die KDecoration3-native (`org.kde.kwin.aurorae.v2`). Für neue Themes ist
`.v2` richtig.

Aurorae-Themes nutzen weiterhin `metadata.desktop`. Das ist hier **kein**
Legacy, sondern das vorgesehene Format:

```ini
[Desktop Entry]
Name=Mein Theme
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__MeinTheme
X-KDE-PluginInfo-Version=1.0
```

Der Präfix `__aurorae__svg__` ist Pflicht und muss dem Ordnernamen folgen.

---

**Weiter:** [Kapitel 2 — Plasma Style](02-plasma-style.md)
