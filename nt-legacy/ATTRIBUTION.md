# Herkunft und Lizenzen

Das Theme steht unter **GPL-2.0-or-later** (siehe `LICENSE`). Erzeugt wird
es von `build.py`; die SVGs, Farbschemata, Fensterdekorationen, Mauszeiger
und Hintergrundbilder sind Eigenerzeugnisse aus den Paletten in diesem
Skript.

## Symbole (`icons-reactos/NTLegacyOS`)

Das mitgelieferte Symbolset hat zwei Quellen, beide weitergebbar:

| Teil | Herkunft | Lizenz |
|---|---|---|
| Shell-Symbole (Ordner, Laufwerke, Papierkorb, Dateitypen) | [ReactOS](https://github.com/reactos/reactos), `dll/win32/shell32/res/icons` | **GPL-2.0** (`COPYING` im Repository) |
| Werkzeugleisten-Symbole (Navigation, Ansichtsmodi, Bearbeiten) | Eigenerzeugnis, `tools/gen-icons-aktionen.py` | GPL-2.0-or-later, wie das Theme |

ReactOS ist **clean-room** entwickelt — die Symbole sind Neuschöpfungen,
keine Kopien von Microsoft-Material. Das ist der Grund, warum dieses Set
und nicht Chicago95 mitgeliefert wird.

Erzeugt wird es mit:

```bash
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/reactos/reactos.git
tools/gen-icons-reactos.py --quelle reactos/dll/win32/shell32/res/icons \
                           --ziel nt-legacy/icons-reactos/NTLegacyOS
tools/gen-icons-aktionen.py nt-legacy/icons-reactos/NTLegacyOS
tools/gen-icon-aliase.py    nt-legacy/icons-reactos/NTLegacyOS
```

## Chicago95 — bewusst *nicht* enthalten

`fetch-icons.sh` kann [Chicago95](https://github.com/grassmunk/Chicago95)
nachinstallieren. Es ist **nicht Teil dieses Repositorys** und steht in
`.gitignore`.

Grund: Chicago95 führt im README `License: GPL-3.0+/MIT`, hat aber (Stand
August 2026, erneut geprüft) **keine LICENSE-Datei** — nur eine `CREDITS`
mit drei Namen. Die Symbole stammen laut selbem README aus *Classic95*
(gnome-look.org 1012363), dessen Lizenz sich nicht ermitteln ließ. Ein
Unterprojekt im selben Repository beschreibt sein Material ausdrücklich als
*„Screenscrapes of original assets"* aus MS Office 95.

Wer Chicago95 lokal installiert hat, kann es weiterhin auswählen — es
liegt dann als eigenes Symbolthema `NTLegacy` neben `NTLegacyOS`. Für die
Weitergabe des Themes ist es ungeeignet.

## Optischer Unterschied

Die ReactOS-Symbole sind moderner als die von Chicago95: blaue Ordner mit
Verläufen statt gelber 16-Farben-Pixelart. Die 4-Bit-Ebenen der
`.ico`-Dateien wären klassischer, sind aber durchgehend mit
Dithering-Artefakten unbrauchbar — geprüft, nicht vermutet.

## Nicht enthalten

Schriften. Das Theme setzt keine mit; es verwendet, was das System bietet.
