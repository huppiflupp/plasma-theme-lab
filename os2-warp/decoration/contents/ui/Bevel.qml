import QtQuick

// OS/2's fixed 3D edges (DESIGN.md §2), not computed from the surface:
//  "button": white/black outside, surface/grey inside; pressed swaps them.
//  "frame":  one white and one grey line, for frames and panels.
//  "field":  sunken, grey/white outside, black inside.
Rectangle {
    id: root
    property string kind: "button"
    property bool sunken: false
    property color light: "#ffffff"
    property color dark: "#808080"
    property color ink: "#000000"
    color: "#cccccc"

    readonly property var lines: {
        if (kind === "frame") return sunken ? [[dark, light]] : [[light, dark]];
        if (kind === "field") return [[dark, light], [ink, color]];
        return sunken ? [[ink, light], [dark, color]] : [[light, ink], [color, dark]];
    }

    Repeater {
        model: root.lines
        Item {
            required property var modelData
            required property int index
            anchors.fill: parent
            anchors.margins: index
            Rectangle { width: parent.width - 1; height: 1; color: modelData[0] }
            Rectangle { width: 1; height: parent.height - 1; color: modelData[0] }
            Rectangle { y: parent.height - 1; width: parent.width; height: 1; color: modelData[1] }
            Rectangle { x: parent.width - 1; width: 1; height: parent.height; color: modelData[1] }
        }
    }
}
