# Mapping to KDE Plasma 6

| Design area | Plasma component | Implementation | Priority |
|---|---|---|---|
| Colours | KDE Color Scheme | `.colors` with active/inactive/disabled groups | P0 |
| Window frames | KDecoration3 | C++/Qt or a compatible decoration; hard bevels and square buttons | P0 |
| Front panel | Plasma Containment/Layout | own Plasma layout plus theme; for true two-row layout possibly an own QML containment | P0 |
| Panel surfaces | Plasma Desktop Theme | SVG elements for panel, widgets, tooltips, dialog backgrounds | P0 |
| Subpanels | own plasmoid/QML popup | bound to a segment, keyboard focus, edge correction | P0/P1 |
| Icons | Freedesktop Icon Theme | full core coverage as SVG; defined fallback rule | P1 |
| Application widgets | Qt Quick Controls Style / Kvantum only as a prototype | long term an own Qt style; hard widget bevels | P1 |
| Global Theme | Look-and-Feel package | bundles colour scheme, Plasma style, layout, icons, wallpaper optional | P1 |
| KWin effects | KWin Script/Settings | short focus/panel animations, firm shadows | P2 |
| Cursor | XCursor Theme | angular, highly visible, 24/32/48 px | P2 |
| Login/Lock | SDDM/Look-and-Feel | only after a stable desktop implementation | P3 |

## Front panel architecture

A true two-row CDE panel can only be approximated with two ordinary Plasma panels. Two coupled panels are acceptable for the first prototype. The goal is a shared QML containment or a dedicated panel plasmoid, so that frame, segmentation, subpanel anchors and autohide work as a single object.

Recommended module structure:

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

## Installation in the user profile

The project must not require root privileges. Typical targets:

```text
~/.local/share/color-schemes/
~/.local/share/plasma/desktoptheme/
~/.local/share/plasma/look-and-feel/
~/.local/share/plasma/plasmoids/
~/.local/share/icons/
~/.local/share/kwin/decorations/
```

The install script must back up existing files of the same name or abort the installation, and never overwrite third-party themes. An `uninstall.sh` may only remove files listed in its own installation manifest.

## Prototyping decision

For quick visual testing, phase 1 may use Kvantum or SVG/QML mock-ups. In the final version Kvantum may only stay if Plasma 6/Qt 6 compatibility, Wayland behaviour and consistent states are demonstrably right. The window decoration and the front panel should not depend on an unmaintained Plasma 5 theme.
