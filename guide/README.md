# Konforme Plasma-6-Themes bauen

Ein Leitfaden, der an der offiziellen KDE-Dokumentation ansetzt und dort
weitermacht, wo sie aufhört: bei der Frage, wie man ein Theme so baut, dass
man es **gefahrlos ausprobieren** kann und dass es **wartbar** bleibt.

Stand: August 2026 · Referenzsystem: Plasma 6.7.3, KF6, Qt 6, Fedora/Nobara 44

---

## Wer das hier lesen sollte

Wer ein Plasma-Theme schreibt und schon einmal erlebt hat, dass ein Theme
mehr kaputt gemacht hat als es schön gemacht hat. Der Leitfaden setzt
voraus, dass du SVG und INI-Dateien lesen kannst. C++ braucht es nicht.

## Die Kapitel

| # | Kapitel | Worum es geht |
|---|---|---|
| 1 | [Die sieben Ebenen und ihr Risiko](01-ebenen-und-risiko.md) | Was ein Theme überhaupt ist — und welche Teile davon einen Rechner unbrauchbar machen können |
| 2 | [Plasma Style](02-plasma-style.md) | SVGs, 9-Patch, `hint-*`-IDs, Farbschema-Stylesheets |
| 3 | [Look-and-Feel-Paket](03-look-and-feel.md) | Das Bündelpaket, `contents/defaults`, und die Panel-Falle |
| 4 | [Bauen und Installieren](04-bauen-und-installieren.md) | CMake, `kpackagetool6`, Varianten ohne Duplikate |
| 5 | [Testen](05-testen.md) | Vier Stufen: Linter, Einzelwidget, Session, VM |
| 6 | [Wenn es schiefgeht](06-recovery.md) | Rettungskommandos, nach Eskalationsstufe sortiert |

Dazu die [Referenzkarte](referenz.md) — alles Nachschlagbare auf einer Seite.

---

## Die fünf Regeln

Wenn du nur eine Seite liest, dann diese.

**1. Ein Theme, das man nicht gefahrlos ausprobieren kann, ist kein fertiges Theme.**
Der Maßstab ist nicht „sieht gut aus", sondern „der Nutzer kann es anwenden,
doof finden und in zehn Sekunden zurück". Alles andere ist ein Prototyp.

**2. Trenne strikt, was in `$HOME` lebt, von dem, was ins System greift.**
Alles unter `~/.local/share/` ist aus einem TTY in unter einer Minute
reparierbar. Login-Manager, Plymouth und GRUB laufen *vor* dem Login — geht
dort etwas schief, brauchst du im Zweifel ein Live-Medium. Diese beiden
Klassen gehören nie in denselben Installationsdurchlauf.

**3. Wenn du ein Panel-Layout ausliefern willst, sichere vorher das des Nutzers.**
Ein `contents/layouts/org.kde.plasma.desktop-layout.js` ersetzt beim
Anwenden alle Panels und Widgets — und das ist nicht rückgängig zu machen.
KDE fragt vorher nach und hakt die Option nicht vorab an, aber wer das
Theme vollständig sehen will, hakt sie an. Eine gesicherte Kopie von
`plasma-org.kde.plasma.desktop-appletsrc` macht daraus einen Rückweg.
Siehe [Kapitel 3.4](03-look-and-feel.md#34-die-panel-falle).

**4. Baue Varianten aus einer Quelle, nicht per Copy-Paste.**
Drei Farbvarianten heißen nicht drei SVG-Bäume. Breeze löst das mit *einem*
SVG-Satz und drei Farbschemata. Wer kopiert, pflegt jeden Fix dreimal — und
vergisst ihn beim dritten Mal.

**5. Zähle `KPlugin.Version` bei jedem Release hoch.**
Diese Zahl ist der Schlüssel des Render-Caches
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). Ohne Bump sehen deine
Nutzer nach dem Update das alte Theme und melden Fehler, die es nicht gibt.

---

## Warum es diesen Leitfaden gibt

Die offizielle Doku unter [develop.kde.org/docs/plasma/theme](https://develop.kde.org/docs/plasma/theme/)
ist gut, aber sie beschreibt Plasma-Themes als Grafikaufgabe. Die Fragen,
an denen Projekte tatsächlich scheitern, sind andere:

- Welcher Teil meines Themes kann den Rechner meines Nutzers unbrauchbar machen?
- Warum wirkt meine SVG-Änderung nicht? (Antwort: [Cache](02-plasma-style.md#26-der-cache))
- Wie teste ich das, ohne mein eigenes System zu opfern? ([Kapitel 5](05-testen.md))
- Wie pflege ich drei Varianten, ohne dreimal zu arbeiten? ([Kapitel 4](04-bauen-und-installieren.md))

An mehreren Stellen ist die offizielle Doku außerdem veraltet — der
Leitfaden benennt diese Stellen und sagt, was stattdessen gilt.

## Verifikationsgrade

Aussagen sind gekennzeichnet:

- **[geprüft]** — auf Plasma 6.7.3 lokal nachvollzogen
- **[Quelle]** — im aktuellen KDE-Quellcode nachgelesen, mit Pfadangabe
- **[unsicher]** — plausibel, aber nicht verifiziert; behandle es als Vermutung

Wo die offizielle Doku etwas anderes sagt als der Quellcode, steht das
ausdrücklich dabei.
