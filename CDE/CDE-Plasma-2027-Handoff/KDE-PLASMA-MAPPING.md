# Zuordnung zu KDE Plasma 6

| Designbereich | Plasma-Baustein | Umsetzung | Priorität |
|---|---|---|---|
| Farben | KDE Color Scheme | `.colors` mit aktiven/inaktiven/disabled Gruppen | P0 |
| Fensterrahmen | KDecoration3 | C++/Qt oder kompatible Dekoration; harte Bevels und quadratische Buttons | P0 |
| Frontpanel | Plasma Containment/Layout | eigenes Plasma-Layout plus Theme; für echte Zweireihigkeit ggf. eigenes QML-Containment | P0 |
| Paneloberflächen | Plasma Desktop Theme | SVG-Elemente für Panel, Widgets, Tooltips, Dialoghintergründe | P0 |
| Subpanels | eigenes Plasmoid/QML-Popup | an Segment gebunden, Tastaturfokus, Randkorrektur | P0/P1 |
| Icons | Freedesktop Icon Theme | vollständige Kernabdeckung als SVG; definierte Fallback-Regel | P1 |
| Anwendungswidgets | Qt Quick Controls Style / Kvantum nur als Prototyp | langfristig eigener Qt-Style; harte Widget-Bevels | P1 |
| Global Theme | Look-and-Feel-Paket | bündelt Farbschema, Plasma-Stil, Layout, Icons, Wallpaper optional | P1 |
| KWin-Effekte | KWin Script/Settings | kurze Fokus-/Panelanimationen, feste Schatten | P2 |
| Cursor | XCursor Theme | eckig, gut sichtbar, 24/32/48 px | P2 |
| Login/Lock | SDDM/Look-and-Feel | erst nach stabiler Desktop-Implementierung | P3 |

## Frontpanel-Architektur

Ein echtes zweistöckiges CDE-Panel ist mit zwei gewöhnlichen Plasma-Panels nur näherungsweise möglich. Für den ersten Prototyp sind zwei gekoppelte Panels zulässig. Das Ziel ist ein gemeinsames QML-Containment oder ein spezielles Panel-Plasmoid, damit Rahmen, Segmentierung, Subpanel-Anker und Autohide wie ein einziges Objekt funktionieren.

Empfohlene Modulstruktur:

```text
org.cde.plasma.frontpanel/
├── metadata.json
├── contents/ui/main.qml
├── contents/ui/PanelRow.qml
├── contents/ui/SegmentButton.qml
├── contents/ui/SubpanelPopup.qml
├── contents/ui/WorkspaceStrip.qml
├── contents/ui/StatusCluster.qml
└── contents/config/main.xml
```

## Installation im Benutzerprofil

Das Projekt soll keine Root-Rechte voraussetzen. Typische Ziele:

```text
~/.local/share/color-schemes/
~/.local/share/plasma/desktoptheme/
~/.local/share/plasma/look-and-feel/
~/.local/share/plasma/plasmoids/
~/.local/share/icons/
~/.local/share/kwin/decorations/
```

Das Installationsskript muss vorhandene gleichnamige Dateien sichern oder die Installation abbrechen, niemals fremde Themes überschreiben. Ein `uninstall.sh` darf ausschließlich Dateien entfernen, die im eigenen Installationsmanifest stehen.

## Prototyping-Entscheidung

Für schnelles visuelles Testen kann Phase 1 Kvantum oder SVG/QML-Mockups verwenden. Für die Endfassung darf Kvantum nur bleiben, wenn Plasma-6-/Qt-6-Kompatibilität, Wayland-Verhalten und konsistente Zustände nachweislich stimmen. Die Fensterdekoration und das Frontpanel sollten nicht von einem nicht gepflegten Plasma-5-Theme abhängen.
