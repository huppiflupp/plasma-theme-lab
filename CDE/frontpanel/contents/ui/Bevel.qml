import QtQuick
import "motif.js" as Motif

// A console tile: dark outline, then Motif's top and bottom shadows,
// computed from the surface colour so every palette shades correctly.
Rectangle {
    id: root
    property bool sunken: false
    property color surface: "#2e7180"
    readonly property var shade: Motif.shades(surface)
    readonly property color lightEdge: sunken ? shade.bottom : shade.top
    readonly property color darkEdge: sunken ? shade.top : shade.bottom
    color: surface
    border.color: Motif.mix(shade.bottom, Qt.rgba(0, 0, 0, 1), 0.55)
    border.width: 1
    Rectangle { x: 1; y: 1; width: parent.width - 2; height: 1; color: root.lightEdge }
    Rectangle { x: 1; y: 1; width: 1; height: parent.height - 2; color: root.lightEdge }
    Rectangle { x: 2; y: parent.height - 2; width: parent.width - 3; height: 1; color: root.darkEdge }
    Rectangle { x: parent.width - 2; y: 2; width: 1; height: parent.height - 3; color: root.darkEdge }
}
