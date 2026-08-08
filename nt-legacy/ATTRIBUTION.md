# Herkunft und Lizenzen

Das Theme steht unter **GPL-2.0-or-later** (siehe `LICENSE`).

## Alles darin ist Eigenerzeugnis

| Bestandteil | Erzeugt von |
|---|---|
| Plasma-Stil, Farbschemata, Fensterdekoration, Mauszeiger, Hintergründe | `build.py` mit `tools/gen-plasma-svg.py`, `gen-aurorae.py`, `gen-cursor.py` |
| Symbole — Ordner, Laufwerke, Dateitypen, Werkzeugleiste | `tools/gen-icons.py` |

**Kein übernommenes Fremdmaterial.** Das Theme kann uneingeschränkt
weitergegeben werden, auch über den KDE Store.

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

136 gezeichnete Symbole in 16/22/32/48 px, dazu Verweise für weitere
Namen. Von den Namen, die Dolphin und PCManFM-Qt anfordern, fällt keiner
mehr auf Breeze zurück.

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
