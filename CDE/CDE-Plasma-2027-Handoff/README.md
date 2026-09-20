# CDE Plasma 2027 — Design- und Prototyping-Paket

Dieses Paket beschreibt eine moderne KDE-Plasma-Oberfläche, deren Herkunft aus CDE und Motif sofort erkennbar bleibt. Es ist als Übergabe an ein Coding-LLM oder einen Theme-Entwickler gedacht.

## Zielbild

Die verbindliche visuelle Referenz ist `references/05-target-teal-copper-panel.png`:

- Petrol/Türkis als Desktop- und Panelbasis
- Kupferorange für aktive Titelleisten, Auswahl und wichtige Zustände
- harte, mehrstufige Motif-Bevels statt glatter Breeze-/Plastikflächen
- eigenständige, gezeichnete Workstation-Icons statt Standard-Freedesktop-Icons
- schwebendes, zweistöckiges CDE-Frontpanel mit kleinen Subpanel-Auslösern
- moderne Nutzbarkeit: HiDPI, klare Typografie, brauchbare Abstände, Plasma 6/Wayland

## Inhalt

| Datei/Ordner | Zweck |
|---|---|
| `references/` | Alle fünf Entwurfs-Screenshots in chronologischer Reihenfolge |
| `DESIGN-SPEC.md` | Verbindliche Designregeln, Maße, Zustände und Ausschlüsse |
| `KDE-PLASMA-MAPPING.md` | Zuordnung der Gestaltung zu Plasma-Komponenten |
| `IMPLEMENTATION-GUIDE.md` | Umsetzungsreihenfolge, Test- und Abnahmekriterien |
| `LLM-PROMPT.md` | Direkt einsetzbarer Auftrag für ein Coding-LLM |
| `design-tokens.json` | Maschinenlesbare Farben, Geometrie und Effekte |
| `MANIFEST.md` | Bedeutung und Priorität der Referenzbilder |

## Empfohlene Verwendung

1. Das ZIP vollständig entpacken.
2. Dem LLM den kompletten Ordner zur Verfügung stellen.
3. `LLM-PROMPT.md` als ersten Auftrag verwenden.
4. Zuerst nur Phase 1 (Farbschema, Fensterdekoration, Panel-Prototyp) umsetzen und Screenshots gegen `05-target-teal-copper-panel.png` vergleichen.
5. Erst danach Icons, Subpanels und Installationsskript ausbauen.

## Technischer Zielrahmen

- KDE Plasma 6
- Qt 6
- Wayland als primäres Ziel, X11 ohne bewusste Abhängigkeit
- bevorzugt SVG/QML/KDecoration3; keine Raster-Skalierung für Rahmen oder Icons
- reproduzierbare Installation und vollständige Deinstallation im Benutzerprofil

Die Screenshots sind Konzeptbilder. Einzelne Texte, Appnamen und Platzierungen sind keine pixelgenauen Implementierungsvorgaben; die Regeln in `DESIGN-SPEC.md` haben Vorrang.
