# Herkunft und Lizenzen

Das Theme steht unter **GPL-2.0-or-later** (siehe `LICENSE`).

## Alles darin ist Eigenerzeugnis

| Bestandteil | Erzeugt von |
|---|---|
| Plasma-Stil, Farbschemata, Fensterdekoration, Mauszeiger, Verlaufsflächen | `build.py` mit `tools/gen-plasma-svg.py`, `gen-aurorae.py`, `gen-cursor.py` |
| Symbole — Ordner, Laufwerke, Dateitypen, Werkzeugleiste | `tools/gen-icons.py` |
| Landschaften, Kacheln, Großbilder | lokal mit einem Bildmodell gerendert, siehe unten |

**Kein übernommenes Fremdmaterial.** Das Theme kann uneingeschränkt
weitergegeben werden, auch über den KDE Store.

## Die Hintergrundbilder

Bis 0.2.5 stimmte der Satz „alles ist programmatisch erzeugt" wörtlich:
Die Hintergründe waren SVG-Verläufe aus `build.py`. Seit 0.2.6 liegen
zusätzlich 26 gerenderte Bilder bei, und die entstehen anders — deshalb
steht es hier ausdrücklich.

Gerendert wurde lokal mit **FLUX.1-schnell** (Apache-2.0) auf einer
eigenen Maschine; kein Dienst, keine fremden Bilder als Vorlage.
Anschließend vervierfacht mit dem ESRGAN-Modell **4x-UltraSharp** und
nahtlos gemacht (Versatz mit Überblendung bei Texturen, Spiegelung bei
Ornamenten).

Zwei Punkte zur Lizenz, damit sie nicht untergehen:

- FLUX.1-schnell steht unter Apache-2.0, seine Ausgaben sind
  uneingeschränkt verwendbar. Unkritisch.
- 4x-UltraSharp wird als **CC BY-NC-SA 4.0** geführt — nicht-kommerziell.
  Ob diese Bedingung auf die *Ausgabe* eines Modells durchschlägt, ist
  ungeklärt und wird unterschiedlich beurteilt. Wer hier sicher gehen
  will, rendert die Bilder ohne diesen Schritt neu; die Rohbilder liegen
  in `wallpaper/` und `tools/mach-hintergruende.py` baut die Pakete
  daraus in einem Durchlauf.

Die Verlaufsflächen aus `build.py` bleiben erhalten — je Variante als
Paket `ntlegacy-<farbwelt>-flaeche`. Wer aus dem Quelltext baut, hat
damit auch ohne die Bilder einen passenden Hintergrund.

## Warum die Symbole selbst gezeichnet sind

Der erste Ansatz war [Chicago95](https://github.com/grassmunk/Chicago95).
Es führt im README `License: GPL-3.0+/MIT`, hat aber (Stand August 2026,
zweimal geprüft) **keine LICENSE-Datei** — nur eine `CREDITS` mit drei
Namen. Die Symbole stammen laut selbem README aus *Classic95*
(gnome-look.org 1012363), dessen Lizenz sich nicht ermitteln ließ. Ein
Unterprojekt im selben Repository beschreibt sein Material ausdrücklich
als *„Screenscrapes of original assets"* aus MS Office 95.

Der zweite Ansatz waren die Symbolressourcen von
[ReactOS](https://github.com/reactos/reactos) — GPL-2.0 und clean-room
entwickelt, also einwandfrei. Zwei Gründe sprachen am Ende dagegen:

1. **Optik.** Die ReactOS-Symbole sind moderner als NT 4.0: blaue Ordner
   mit Farbverläufen statt gelber Flächen. Die 4-Bit-Ebenen der
   `.ico`-Dateien wären klassischer, sind aber durchgehend mit
   Dithering-Artefakten unbrauchbar.
2. **Deckung.** Werkzeugleisten-Symbole — Kopieren, Einfügen, Zurück,
   Ansichtsmodi — liegen dort als Bitmap-Streifen in Programmressourcen
   oder gar nicht vor. Sie hätten ohnehin gezeichnet werden müssen.

Wenn ohnehin die Hälfte selbst entsteht, ist es konsequenter, alles selbst
zu zeichnen: einheitlicher Stil, eine Lizenz, keine Fremdquelle zu pflegen.

## Das Symbolset

```bash
tools/gen-icons.py nt-legacy/icons-nt/NTLegacyIcons
tools/gen-icon-aliase.py     nt-legacy/icons-nt/NTLegacyIcons
tools/gen-symbolic-aliase.py nt-legacy/icons-nt/NTLegacyIcons
```

162 gezeichnete Symbole in 16/22/32/48 px, dazu Verweise für weitere
Namen. Von den Namen, die Dolphin und PCManFM-Qt anfordern, fällt keiner
mehr auf Breeze zurück.

Seit 0.2.7 in acht Größen: 16, 22, 32, 48, 64, 96, 128 und 256 px — alle,
die Dolphin in seinem Zoomregler anbietet.

Der Weg dahin ist eine Lehre wert. In 0.2.6 lag dort stattdessen dieselbe
Zeichnung als SVG unter `scalable/`, gültig ab 64 px; nach der
Freedesktop-Spezifikation müsste sie ab dieser Größe gewinnen, und mit
`QIcon` gemessen tat sie das auch. Beim Melder blieb es trotzdem
pixelig.

Nachgestellt und gemessen: Dolphin liest bei 200 px die
`places/48/folder.png` und zieht sie hoch — die SVG wird nicht einmal
geöffnet. KDE-Programme laden Symbole über **KIconLoader**, nicht über
Qts eigenen Lader, und der zieht `scalable`-Verzeichnisse hier nicht
heran. Deshalb jetzt echte Bitmaps in jeder Größe: das hängt von keiner
Gewichtung ab.

Die SVGs unter `scalable/` bleiben liegen — reine Qt-Programme ohne
KDE-Integration finden sie, und sie kosten wenig.

Gemessen wurde ohne `strace`: Die Zugriffszeiten der Symboldateien mit
`touch -a -d "3 days ago"` zurückdatieren, dann das Programm starten und
nachsehen, welche Datei ein neues Datum hat. `relatime` aktualisiert von
sich aus nichts, was jünger als 24 Stunden ist — daran war der erste
Messversuch gescheitert.

Die Gegenstandsfarben folgen bewusst **nicht** dem Farbschema: Unter
Windows NT blieb der Ordner gelb und das Laufwerk grau, egal welche
Farbwelt eingestellt war. Nur Linien- und Akzentfarbe richten sich nach
der Variante.

## SE98 — geprüft, aus demselben Grund nicht übernommen

`fetch-icons.sh` kann inzwischen auch [SE98](https://www.opencode.net/nestoris/Win98SE)
holen. Der Satz ist verlockend: rund 6.400 Namen gegen unsere 229, in
Größen von 8 bis 1024 px, mit einer `index.theme`, die alle 109
Verzeichnisse vollständig führt — deutlich besser gepflegt als
Chicago95. Von den Symbolnamen, die Plasma auf diesem System tatsächlich
anfordert und die uns fehlen, deckt er 93 ab.

Er steht trotzdem **nicht** im Repository, und zwar aus demselben Grund
wie Chicago95 — nur ist der Befund hier klarer. Anders als Chicago95
liegt eine `LICENSE` bei, GPL-2.0 im Volltext. Die eigene README des
Projekts beschreibt aber, was darunter liegt:

> „Enhanced Classic icon theme […] **from MicroSoft Memphis project** […]
> inspired by Chicago95 theme (**actually it's a manual copy-paste
> fork**) of Grassmunk"

> „there are some icons from **Faenza** and **Chicago95** themes in it"

„Memphis" war der Entwicklungsname von Windows 98. Bei Chicago95 war die
Herkunft der Bitmaps *ungeklärt*; hier steht sie im Klartext. Eine
Lizenz deckt nur, was derjenige geschaffen hat, der sie setzt — auf
fremde Bitmaps kann niemand die GPL legen. Dazu kommt: Es gibt keine
`CREDITS` und keine datei-genaue Zuordnung, der selbstgezeichnete Anteil
lässt sich vom übernommenen also gar nicht trennen.

Für den eigenen Rechner ist das unerheblich, für die Weitergabe nicht.
Deshalb dasselbe Verfahren wie bei Chicago95: nachladbar, nicht
mitgeliefert.

Was wir stattdessen daraus ziehen, ist die Lückenliste.
`tools/luecken-symbole.py` ermittelt, welche Namen das System anfordert
und unser Satz nicht hat — aus den `.desktop`-Dateien und den
Zeichenketten der KF6-Bibliotheken, gefiltert gegen Breeze. Mit
`--vergleich` steht daneben, ob SE98 eine Vorlage hätte:

```bash
tools/luecken-symbole.py nt-legacy/icons-nt/NTLegacyIcons \
    --vergleich nt-legacy/icons/NTLegacySE98
```

Das ist die zulässige Nutzung eines fremden Satzes: hinsehen, dann
selbst zeichnen.

## Die fremden Sätze weiterhin nutzbar

`fetch-icons.sh` installiert Chicago95 als `NTLegacy` und SE98 als
`NTLegacySE98`. Beide liegen **nicht** im Repository (`nt-legacy/icons/`
steht in `.gitignore`) und sind nicht Teil der Weitergabe — wer sie
geholt hat, kann sie in den Systemeinstellungen auswählen.

## Nicht enthalten

Schriften. Das Theme setzt keine mit; es verwendet, was das System bietet.
