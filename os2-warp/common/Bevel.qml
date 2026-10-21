import QtQuick
import org.kde.kirigami as Kirigami

// OS/2's fixed 3D edges (DESIGN.md §2), as in the window frame:
//  "button": an outline, a light and a dark ring; pressed swaps them.
//  "frame":  one light and one dark line.
//  "field":  sunken, dark/light outside, the outline colour inside.
// The edge colours follow the variant: a dark colour scheme is Neon
// (cyan light, violet dark, DESIGN.md §9a), a light one Warp 4's grey.
Rectangle {
    id: root
    property string kind: "button"
    property bool sunken: false
    readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    property color light: neon ? "#48cffe" : "#ffffff"
    property color dark: neon ? "#7a4dff" : "#808080"
    property color ink: neon ? "#020617" : "#000000"
    // An inactive title bar (the Tab Launcher's): Warp 4's mid grey with
    // light grey text, Neon's navy with muted blue (build.py's palettes).
    readonly property color titleColor: neon ? "#0b1430" : "#808080"
    readonly property color titleText: neon ? "#7f8fbf" : "#cccccc"
    color: Kirigami.Theme.backgroundColor

    readonly property var lines: {
        if (kind === "none") return [];        // the surface alone, no edge
        if (kind === "frame") return sunken ? [[dark, light]] : [[light, dark]];
        if (kind === "field") return [[dark, light], [ink, color]];
        return sunken ? [[ink, ink], [dark, light]] : [[ink, ink], [light, dark]];
    }

    // Neon draws the outer line of a raised frame or button as the window
    // frame does (NeonFrame.qml): cyan, pink in the right corners.
    readonly property bool glowEdge: neon && !sunken && kind !== "field" && kind !== "none"
    NeonFrame {
        visible: root.glowEdge
        anchors.fill: parent
        anchors.margins: root.kind === "frame" ? 0 : 1
        light: root.light; dark: root.dark; accent: "#ff4fd8"
        z: 1
    }
    Repeater {
        model: root.lines
        Item {
            required property var modelData
            required property int index
            // The ring NeonFrame replaces stays out.
            visible: !(root.glowEdge && index === (root.kind === "frame" ? 0 : 1))
            anchors.fill: parent
            anchors.margins: index
            Rectangle { width: parent.width - 1; height: 1; color: modelData[0] }
            Rectangle { width: 1; height: parent.height - 1; color: modelData[0] }
            Rectangle { y: parent.height - 1; width: parent.width; height: 1; color: modelData[1] }
            Rectangle { x: parent.width - 1; width: 1; height: parent.height; color: modelData[1] }
        }
    }
}
