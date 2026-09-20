# Implementierungs- und Testanleitung

## Phase 0 — sichere Arbeitsbasis

1. Zielversion von Plasma, Distribution und Qt dokumentieren.
2. Entwicklung in einem neuen Benutzerprofil oder einer VM beginnen.
3. Vor Änderungen `~/.config`, `~/.local/share/plasma`, Farbschemata und KWin-Konfiguration sichern.
4. Repository mit Komponentenordnern, Lizenzangaben und Screenshot-Vergleich anlegen.

## Phase 1 — visueller Kernprototyp

Lieferumfang:

- Farbschema aus `design-tokens.json`
- aktive/inaktive Fensterdekoration
- statischer zweistöckiger Panel-Prototyp
- 12 Kernicons: CDE-Menü, Home, Datei, Ordner, Terminal, Web, Mail, Editor, Workspace, Netzwerk, Audio, Papierkorb
- Beispielansicht bei 1920×1080 und 2560×1440

Abnahme:

- Zielpalette wirkt wie `05-target-teal-copper-panel.png`.
- Fenster und Panel sind auf den ersten Blick Motif/CDE, nicht Breeze.
- aktive Titelleiste, gedrückter Button und Fokusfeld haben drei verschiedene, eindeutige Zustände.

## Phase 2 — funktionales Frontpanel

1. Segmentkomponente und zwei Reihen bauen.
2. Launcher, Tasks und Workspace-Umschaltung anbinden.
3. Subpanel-Auslöser und Popups implementieren.
4. Sichtbar/Autohide/Hotspot als Konfiguration anbieten.
5. Mehrmonitorlogik und Panelposition oben/unten testen.
6. Pointer, Tastatur und Touch separat prüfen.

## Phase 3 — Theme-Abdeckung

- Plasma-Widgets, Benachrichtigungen, Kalender, System Tray und Tooltips
- Qt-Widgets/Qt Quick Controls
- vollständige Kernicon-Abdeckung und kontrollierter Fallback
- Cursor, Sperrbildschirm und optional SDDM

## Phase 4 — Verpackung

- `install.sh`, `uninstall.sh`, Versionsmanifest und Lizenzdateien
- trockener Testlauf ohne Root-Rechte
- Installation auf frischem Benutzerprofil
- vollständige Entfernung mit Wiederherstellung der vorherigen Auswahl

## Visuelle Prüfmatrix

| Prüfung | Erwartung | Fehlerbeispiel |
|---|---|---|
| 100 % Skalierung | Kanten exakt, Text nicht gequetscht | halbe Pixel, verschwommene SVGs |
| 150 % Skalierung | Bevelstufen weiterhin klar | unterschiedlich dicke Rahmen |
| 200 % Skalierung | Icons besitzen saubere optische Größen | hochskalierte 16-px-Rastergrafik |
| aktives/inaktives Fenster | ohne Zögern unterscheidbar | nur minimal anderer Farbton |
| Tastaturfokus | an jedem Widget sichtbar | Fokus nur bei Texteingaben |
| Panel-Autohide | keine Fokusfalle, kein Flackern | Panel schließt beim Weg zum Subpanel |
| Mehrmonitor | Popup bleibt vollständig sichtbar | Subpanel außerhalb des Bildschirms |
| dunkler Terminalinhalt | Rahmen bleibt klar lesbar | schwarze Fläche verschluckt Dekoration |

## Funktionale Abnahmekriterien

- Plasma startet ohne QML- oder KWin-Fehler.
- Kein Bestandteil benötigt Root-Rechte.
- Wayland-Sitzung ist primär funktionsfähig.
- Autohide und Subpanel lassen sich vollständig per Tastatur bedienen.
- Deinstallation entfernt nur eigene Dateien.
- Fallback-Icons fallen kontrolliert auf ein dokumentiertes Theme zurück; im sichtbaren Kernbereich gibt es keine Stilbrüche.

## Screenshot-Vergleich

Für jeden Meilenstein denselben Testdesktop aufnehmen:

- Dateimanager links, Terminal rechts
- aktiver und inaktiver Fenstertitel gleichzeitig sichtbar
- geöffnetes Anwendungsmenü und ein Subpanel
- vier Workspaces, Systemstatus und Uhr im Panel
- Auflösung und Skalierungsfaktor im Dateinamen

Das LLM soll zu jedem Screenshot kurz auflisten: Abweichung, vermutete Ursache, betroffene Komponente und nächster Fix.
