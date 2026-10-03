import QtQuick

// The start-up screen (KSplash): a Motif dialog on the tiled backdrop, as
// CDE showed its session start. KSplash raises `stage` from 1 to 6 while
// Plasma starts; each stage lights one more block of the meter.
Rectangle {
    id: root
    color: "#086875"
    property int stage

    readonly property color face: "#86a4aa"
    readonly property color light: "#c9dedb"
    readonly property color dark: "#41646a"
    readonly property color ink: "#10262b"
    readonly property color copper: "#e8874f"
    readonly property string font: "IBM Plex Sans Condensed"

    // A Motif bevel: light top and left, dark bottom and right.
    component Bevel: Rectangle {
        property bool sunken: false
        property int depth: 2
        color: root.face
        Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: parent.depth; color: parent.sunken ? root.dark : root.light }
        Rectangle { anchors { left: parent.left; top: parent.top; bottom: parent.bottom } width: parent.depth; color: parent.sunken ? root.dark : root.light }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: parent.depth; color: parent.sunken ? root.light : root.dark }
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: parent.depth; color: parent.sunken ? root.light : root.dark }
    }

    Image {
        anchors.fill: parent
        source: "images/backdrop.png"
        fillMode: Image.Tile
        smooth: false
    }

    Rectangle {
        // The window's ink outline around the bevel.
        id: dialog
        width: 460; height: 236
        anchors.centerIn: parent
        color: root.ink
        opacity: 0
        Bevel {
            anchors.fill: parent; anchors.margins: 1
            Bevel {
                // Title bar.
                id: title
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                height: 26
                color: root.copper
                Text {
                    anchors.centerIn: parent
                    text: "CDE Copper"
                    font.family: root.font; font.pixelSize: 14; font.weight: Font.DemiBold
                    color: root.ink
                }
            }
            Row {
                anchors { left: parent.left; right: parent.right; top: title.bottom; margins: 18 }
                spacing: 18
                Image {
                    source: "images/logo.svg"
                    width: 72; height: 72
                    sourceSize: Qt.size(72, 72)
                }
                Column {
                    spacing: 6
                    anchors.verticalCenter: parent.verticalCenter
                    Text { text: "Common Desktop Environment"; font.family: root.font; font.pixelSize: 18; color: root.ink }
                    Text { text: "Starting the desktop …"; font.family: root.font; font.pixelSize: 13; color: root.ink; opacity: 0.8 }
                }
            }
            Bevel {
                // The meter: six blocks in a sunken well.
                sunken: true
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 18 }
                height: 30
                color: "#6f8f96"
                Row {
                    anchors.fill: parent; anchors.margins: 5
                    spacing: 5
                    Repeater {
                        model: 6
                        delegate: Bevel {
                            required property int index
                            width: (parent.width - 5 * 5) / 6
                            height: parent.height
                            depth: 2
                            color: root.stage > index ? root.copper : root.face
                            sunken: root.stage <= index
                            Behavior on color { ColorAnimation { duration: 180 } }
                        }
                    }
                }
            }
        }
        NumberAnimation on opacity { from: 0; to: 1; duration: 300 }
    }
}
