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

Dazu liegt seit 0.2.6 dieselbe Zeichnung als SVG unter `scalable/`, gültig
ab 64 px. Grund: Dolphin bietet Symbolgrößen bis 256 px an, und weil unser
Satz den Namen abfängt, wurde bis dahin das 48-px-Bitmap hochgezogen. Die
Bitmaps bis 48 px bleiben unangetastet — bei 16 px ist dort jede Kante von
Hand gesetzt, und eine Vektorfassung, die auch diese Größen bedient, hätte
genau das zerstört.

Die Gegenstandsfarben folgen bewusst **nicht** dem Farbschema: Unter
Windows NT blieb der Ordner gelb und das Laufwerk grau, egal welche
Farbwelt eingestellt war. Nur Linien- und Akzentfarbe richten sich nach
der Variante.

## Chicago95 weiterhin nutzbar

`fetch-icons.sh` installiert Chicago95 lokal als eigenes Symbolthema
`NTLegacy`. Es liegt **nicht** im Repository (steht in `.gitignore`) und
ist nicht Teil der Weitergabe — wer es installiert hat, kann es in den
Systemeinstellungen auswählen.

## Nicht enthalten

Schriften. Das Theme setzt keine mit; es verwendet, was das System bietet.
