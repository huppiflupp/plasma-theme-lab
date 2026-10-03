import QtQuick

// A Motif shadowed rectangle: light edge top/left, dark edge bottom/right,
// reversed when sunken.
Rectangle {
    id: bevel
    property color light: "white"
    property color dark: "black"
    property bool sunken: false
    property int thickness: 2
    readonly property color first: sunken ? dark : light
    readonly property color second: sunken ? light : dark

    Repeater {
        model: bevel.thickness
        Item {
            required property int index
            anchors.fill: parent
            Rectangle { x: index; y: index; width: bevel.width - 2 * index - 1; height: 1; color: bevel.first }
            Rectangle { x: index; y: index; width: 1; height: bevel.height - 2 * index - 1; color: bevel.first }
            Rectangle { x: index + 1; y: bevel.height - index - 1; width: bevel.width - 2 * index - 1; height: 1; color: bevel.second }
            Rectangle { x: bevel.width - index - 1; y: index + 1; width: 1; height: bevel.height - 2 * index - 1; color: bevel.second }
        }
    }
}
