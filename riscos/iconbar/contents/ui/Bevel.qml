import QtQuick
import org.kde.kirigami as Kirigami

// RISC OS's 3D edges for the Apps menu (DesktopMenu.qml, which names this
// type as Warp Legacy's Bevel; written anew, same properties):
//  "button": a black line, then light above and left, dark below and right;
//            pressed swaps them.
//  "frame":  one light and one dark line.
//  "field":  sunken, then the black line inside.
// Light and dark from the colour scheme: white and colour 4 in the
// classic variants, the dark variant's lighter and darker greys.
Rectangle {
    id: root
    property string kind: "button"
    property bool sunken: false
    readonly property bool darkScheme: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    property color light: darkScheme ? Qt.lighter(Kirigami.Theme.backgroundColor, 1.6) : "#ffffff"
    property color dark: darkScheme ? Qt.darker(Kirigami.Theme.backgroundColor, 1.8) : "#777777"
    property color ink: darkScheme ? "#0b0c0e" : "#000000"
    readonly property color titleColor: Kirigami.Theme.backgroundColor
    readonly property color titleText: Kirigami.Theme.textColor
    color: Kirigami.Theme.backgroundColor

    readonly property var lines: {
        if (kind === "none") return [];
        if (kind === "frame") return sunken ? [[dark, light]] : [[light, dark]];
        if (kind === "field") return [[dark, light], [ink, color]];
        return sunken ? [[ink, ink], [dark, light]] : [[ink, ink], [light, dark]];
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
