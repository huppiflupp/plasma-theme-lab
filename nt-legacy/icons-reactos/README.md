# Symbole aus ReactOS

Zwischenstand. Erzeugt von `tools/gen-icons-reactos.py` aus den
`.ico`-Ressourcen von [ReactOS](https://github.com/reactos/reactos)
(GPL-2.0, clean-room entwickelt — also weitergebbar).

## Warum

Das bisher verwendete Chicago95-Set hat bis heute keine LICENSE-Datei,
und seine Bitmaps stammen laut eigenem README aus *Classic95*, dessen
Lizenz sich nicht ermitteln lässt. Für eine Veröffentlichung (KDE Store)
reicht das nicht.

## Stand

| | |
|---|---|
| zugeordnet | 58 Symbole, 174 Dateien (16/32/48 px) |
| Quelle | `dll/win32/shell32/res/icons`, 181 brauchbare `.ico` |
| Dolphin-Namen abgedeckt | 15 von 56 per Alias, **41 bleiben bei Breeze** |
| Chicago95 zum Vergleich | 3980 echte Symbole |

**Das ist noch kein Ersatz für Chicago95.** Die Werkzeugleisten-Symbole
(Kopieren, Einfügen, Zurück, Ansichtsmodi) fehlen fast vollständig — in
ReactOS liegen sie als Bitmap-Streifen in anderen Modulen, nicht als
`.ico`.

## Nächste Schritte

1. Die restlichen ~123 shell32-Symbole zuordnen (Bogen erzeugen mit
   `--bogen`, dann `ZUORDNUNG` erweitern)
2. Werkzeugleisten-Symbole aus `dll/win32/browseui`, `base/shell/explorer`
   und den Systemsteuerungsmodulen erschließen
3. Erst dann kann das Set `icons/` ablösen

## Optik

Die ReactOS-Symbole sind moderner als die von Chicago95 — blaue Ordner mit
Verläufen statt gelber 16-Farben-Pixelart. Die 4-Bit-Ebenen der Dateien
wären klassischer, sind aber durchgehend mit Dithering-Artefakten
unbrauchbar.
