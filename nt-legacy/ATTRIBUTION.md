# Herkunft und Lizenzen

Das Theme selbst steht unter **GPL-2.0-or-later** (siehe `LICENSE`).
Erzeugt wird es vollständig von `build.py`; die SVGs, Farbschemata,
Fensterdekorationen, Mauszeiger und Hintergrundbilder sind
Eigenerzeugnisse aus den Paletten in diesem Skript.

## Übernommene Bestandteile

| Bestandteil | Herkunft | Lizenz |
|---|---|---|
| `icons/NTLegacy/` | [Chicago95](https://github.com/grassmunk/Chicago95), Verzeichnis `Icons/Chicago95` | siehe unten |

### Zum Icon-Set

Chicago95 führt im README `License: GPL-3.0+/MIT`, hat aber **keine
LICENSE-Datei im Repository**; GitHub erkennt entsprechend keine Lizenz.
Die Icons stammen laut Chicago95-README ihrerseits aus *Classic95*
(gnome-look.org 1012363), dessen Lizenz sich nicht ermitteln ließ.

Ein Unterprojekt im selben Repository (`Extras/libreoffice-chicago95-iconset`)
beschreibt sein Material ausdrücklich als *„Screenscrapes of original
assets"* aus MS Office 95. Das betrifft **nicht** den hier verwendeten
Ordner `Icons/Chicago95`, zeigt aber, dass im Projekt mit
Original-Microsoft-Material gearbeitet wurde.

**Daraus folgt:** Die Lizenzlage des Icon-Sets ist nicht abschließend
geklärt. Wer dieses Theme weitergibt oder in den KDE Store stellt, sollte
das vorher klären — etwa durch Nachfrage im Chicago95-Issue-Tracker nach
der Herkunft der Bitmaps.

Lizenzsichere Alternativen, falls nötig:

- **SE98** (github.com/nestoris/Win98SE) — echte GPL-2.0-Datei, größerer
  Umfang, aber Windows-98/2000-Stil statt NT 4.0
- **ReactOS** (github.com/reactos/reactos) — GPL-2.0, clean-room
  entwickelt, lizenzrechtlich unbedenklich; liegt als `.ico` vor und
  müsste umgesetzt werden

## Nicht enthalten

Original-Grafiken, -Schriften oder -Zeiger aus Windows NT oder Windows 95
sind **nicht** Bestandteil dieses Themes. Die Mauszeiger sind als
Pixelmuster in `tools/gen-cursor.py` neu gezeichnet.
