import QtQuick

// The start-up screen (KSplash): a Motif dialog on the tiled backdrop, as
// CDE showed its session start. KSplash raises `stage` from 1 to 6 while
// Plasma starts; each stage lights one more block of the meter, with the
// part that has just started. The colours and the backdrop tile are those
// of the palette in use (Colours.qml and images/backdrop.png, rewritten by
// CDE Copper's tool with every palette).
Rectangle {
    id: root
    Colours { id: colours }
    color: colours.desktop
    property int stage

    readonly property color face: colours.face
    readonly property color light: colours.light
    readonly property color dark: colours.dark
    readonly property color ink: colours.ink
    readonly property color copper: colours.accent
    readonly property string font: "IBM Plex Sans Condensed"
    // KSplash passes only the count; on Wayland the stages come in this
    // order (plasma-workspace, ksplash/ksplashqml/splashapp.cpp).
    readonly property var parts: [
        {icon: "display", text: i18nd("cde-copper", "Display")}, {icon: "window", text: i18nd("cde-copper", "Window manager")},
        {icon: "plasma", text: "Plasma"}, {icon: "settings", text: i18nd("cde-copper", "Settings")},
        {icon: "session", text: i18nd("cde-copper", "Session")}, {icon: "desktop", text: i18nd("cde-copper", "Desktop")}]

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
        width: 460; height: 250
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
                color: colours.title
                Text {
                    anchors.centerIn: parent
                    text: "CDE Copper"
                    font.family: root.font; font.pixelSize: 14; font.weight: Font.DemiBold
                    color: colours.titleText
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
                    Text { text: i18nd("cde-copper", "Common Desktop Environment"); font.family: root.font; font.pixelSize: 18; color: root.ink }
                    Text {
                        text: root.stage >= 1 && root.stage <= 6 ? i18nd("cde-copper", "Starting: %1 …", root.parts[root.stage - 1].text) : i18nd("cde-copper", "Starting the desktop …")
                        font.family: root.font; font.pixelSize: 13; color: root.ink; opacity: 0.8
                    }
                }
            }
            Bevel {
                // The meter: six blocks in a sunken well.
                sunken: true
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 18 }
                height: 44
                color: colours.trough
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
                            Image {
                                anchors.centerIn: parent
                                width: 22; height: 22
                                sourceSize: Qt.size(22, 22)
                                source: "images/" + root.parts[parent.index].icon + ".svg"
                                opacity: root.stage > parent.index ? 1 : 0.35
                                Behavior on opacity { NumberAnimation { duration: 180 } }
                            }
                        }
                    }
                }
            }
        }
        NumberAnimation on opacity { from: 0; to: 1; duration: 300 }
    }
}
