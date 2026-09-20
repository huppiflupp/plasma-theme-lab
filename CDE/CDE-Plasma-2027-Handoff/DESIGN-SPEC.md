# Design-Spezifikation

## 1. Leitidee

„CDE auf einer hochwertigen UNIX-Workstation von 2026/27“: robuste, technische, ruhige Oberfläche mit klarer mechanischer Tiefe. Modernität entsteht durch Präzision, HiDPI, Lesbarkeit und durchdachte Animationen – nicht durch Rundungen, Transparenz oder Glas.

## 2. Verbindliche Palette

| Token | Hex | Verwendung | Beispiel |
|---|---:|---|---|
| Desktop Deep Teal | `#086875` | Desktopgrund, große ruhige Flächen | Wallpaper-Grundton |
| Panel Teal | `#2E7180` | Panel- und Menürahmen | Frontpanel |
| Surface Blue Gray | `#86A4AA` | Fensterflächen, Felder | Dateimanager |
| Surface Light | `#AFC2C2` | helle Widgetfläche | Dialoge |
| Copper Active | `#E8874F` | aktive Titelleiste, aktiver Workspace | Fokuszustand |
| Copper Light | `#F0B184` | Highlightkante und Icondetails | obere/Linke Bevelkante |
| Teal Shadow | `#174C55` | tiefe Schattenkante | untere/rechte Bevelkante |
| Ink | `#10262B` | Standardtext und Konturen | Menütext |
| Terminal | `#061C22` | Terminal-/dunkle Spezialfläche | Konsole |
| Cyan Signal | `#3DB5C3` | seltene Statusinformation | Netzwerk/Aktivität |
| Disabled | `#6F8588` | deaktivierter Text | inaktive Aktion |

Kupfer ist ein Fokus- und Aktionssignal, keine flächendeckende Sekundärfarbe. Pro Ansicht soll höchstens ungefähr 10–15 % der Fläche kupferfarben sein.

## 3. Formensprache

- Ecken: grundsätzlich 0–2 px Radius; Fenster und große Panels 0 px.
- Rahmen: außen dunkel, dann hell, innen mittel; 2–3 klar getrennte Stufen.
- Erhabene Elemente: Lichtkante oben/links, Schattenkante unten/rechts.
- Gedrückte Elemente: Bevel-Richtung umkehren; Inhalt 1 px nach rechts/unten versetzen.
- Fokus: Kupferrand plus kontrastreiche innere Linie; nicht nur Farbwechsel.
- Schatten: kurz und fest (z. B. 0 5 px 12 px bei geringer Deckkraft), kein diffuser Material-Design-Schatten.
- Transparenz/Blur: im Kern-Theme nicht verwenden. Optional maximal 3–5 % visuelle Durchlässigkeit im schwebenden Panel.
- Trennlinien: sichtbar, meist 1 px, nie nur durch Abstand ersetzen.

## 4. Typografie

- UI: eine schmale, gut lesbare Sans; bevorzugt `IBM Plex Sans Condensed`, Fallback `Noto Sans`.
- Terminal/technische Labels: `IBM Plex Mono`, Fallback `Noto Sans Mono`.
- Standardgröße: 10–11 pt bei 96 dpi; keine künstlich winzige Retro-Schrift.
- Titelleisten: Semibold, nicht fett-schwarz; Zeichenabstand normal.
- Keine Bitmap-Schrift als Standard. Bitmap-Anmutung darf nur in kleinen dekorativen Labels vorkommen.

## 5. Fensterdekoration

| Element | Vorgabe |
|---|---|
| aktive Titelleiste | Kupfer `#E8874F`, 28–32 px, feine Textur optional |
| inaktive Titelleiste | entsättigtes Blaugrün/Grau, klar von aktiv unterscheidbar |
| Außenrahmen | 4 px visuell, drei harte Bevelstufen |
| Fensterknöpfe | quadratisch 22–24 px, gezeichnete Glyphen, eigener Bevel |
| Reihenfolge | Menü/Window links; Minimieren, Maximieren, Schließen rechts |
| Resize-Zone | unsichtbar mindestens 6–8 px, trotz schmalem sichtbaren Rahmen |

Aktiver Fokus muss auch ohne Farbwahrnehmung durch Kontrast und Rahmenstruktur erkennbar sein.

## 6. Bedienelemente

- Buttons: rechteckig, 28–34 px hoch, 2 px Bevel; Default-Button mit zusätzlichem Kupferrand.
- Eingabefelder: eingesenkter Rahmen, helle Innenfläche; Fokus als Kupfer-Innenkante.
- Menüs: kompakt, 30–34 px Zeilenhöhe, klare Untermenü-Dreiecke, keine Pillen.
- Auswahl: Kupferfläche mit dunkler Schrift oder dunkles Teal mit heller Schrift – abhängig vom Kontrast.
- Tabs: physisch verbunden wirkende Reiter, aktive Lasche öffnet sich zur Inhaltsfläche.
- Scrollbars: 16–20 px, sichtbare Pfeilknöpfe optional; kein ultradünner Overlay-Scrollbar.
- Tooltips: helle Blaugrünfläche, dunkler Doppelrahmen, kurze Einblendung.

## 7. Icon-System

- Eigene Icons sind Pflicht; keine sichtbare Mischung mit Breeze/Papirus/Tela.
- Stil: technische Workstation-Piktogramme, 2–4 Hauptfarben, dunkle Kontur, harte Highlights.
- Geometrie: überwiegend eckig, minimale diagonale Kanten; kein kreisförmiger App-Icon-Look.
- Raster: Master als SVG; optisch auf 16, 22, 24, 32, 48 und 64 px abgestimmt.
- Ordner: teal-grauer Korpus mit kupferfarbener Lasche/Akzent.
- Statusicons: monochrom/zweifarbig, klare Pixel-Silhouette, keine dünnen Breeze-Linien.
- Aktiver Launcher erhält eingedrückten Rahmen und Kupfermarkierung, nicht bloß einen Punkt.

## 8. Frontpanel

Das Frontpanel ist das Alleinstellungsmerkmal und darf nicht wie eine normale Taskbar aussehen.

### Aufbau

- schwebend mit 12–24 px Abstand zum Bildschirmrand; Zielposition zunächst oben, spätere Variante unten möglich
- Breite etwa 88–94 % des Bildschirms, zentriert
- zwei klar getrennte Reihen, zusammen ca. 96–116 px hoch
- obere Reihe: CDE/Toolbox, Workspaces, große Launcher/aktive Tasks, Uhr, zentrale Statusmodule
- untere Reihe: Anwendungen/Orte/System/Hilfe, Kontextaktionen und Systemmodule
- Segmente wirken wie einzelne mechanische Kacheln innerhalb eines gemeinsamen Rahmens
- kleine Dreieck-Auslöser öffnen Subpanels ober- oder unterhalb des zugehörigen Segments

### Verhalten

- drei Modi: immer sichtbar, automatisch ausblenden, per Hotspot ein-/ausfahren
- Ein-/Ausblenden: 140–180 ms, geradlinig oder dezentes ease-out; kein federndes Verhalten
- im verborgenen Zustand bleibt eine 3–5 px breite Griffkante oder ein kleiner kupferner Indikator sichtbar
- Subpanel bleibt offen, solange Pointer/Fokus in Hauptsegment oder Subpanel liegt; Escape schließt
- Tastaturbedienung und Screenreader-Namen für jeden Launcher und jedes Statusmodul
- Popup-Geometrie muss Mehrmonitor- und Bildschirmrandfälle berücksichtigen

## 9. Desktop und Wallpaper

Das Theme muss auch auf einfarbigem Petrol funktionieren. Ein Wallpaper ist optional und darf die Bedienoberfläche nicht dominieren. Kein eingebautes Logo, kein Textzwang und keine UI-Elemente im Wallpaper. Bei einem Bildmotiv sollen ruhige Flächen hinter Fenstern/Panel liegen und Kupfer nur sparsam als Landschafts- oder Lichtakzent auftreten.

## 10. Animation

- nur funktionale Animationen: Panel, Subpanel, Workspacewechsel, Fokuswechsel
- 120–200 ms; keine langen Fades, Bounce-, Jelly- oder Zoom-Effekte
- reduzierte Bewegung respektieren; alle Funktionen ohne Animation nutzbar

## 11. Explizite Ausschlüsse

- kein Breeze/Oxygen/„KDE-Plastik“-Eindruck
- keine großen Rundungen, Pillen, Glasflächen oder Material-Design-Karten
- keine beliebigen Standardicons
- keine lavendel/rosa Zielpalette; sie bleibt nur Entwicklungsreferenz
- keine 1:1-Museumskopie mit winzigen Schriften oder schlechter HiDPI-Nutzbarkeit
- kein modernes Panel, das lediglich teal eingefärbt wurde
