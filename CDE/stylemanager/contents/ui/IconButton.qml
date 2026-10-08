pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "motif.js" as Motif

// One of the style manager's large buttons, as in dtstyle: the symbol
// over its name, on a Motif bevel in the window's colour.
Button {
    id: control
    required property var colours
    property string iconName: ""
    // The part whose dialog is open.
    property bool selected: false
    implicitWidth: 92
    implicitHeight: 86
    padding: 4
    hoverEnabled: true
    Accessible.name: text
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()
    background: Bevel {
        sunken: control.down || control.selected
        surface: control.hovered && control.enabled ? Motif.mix(control.colours.window, Motif.shades(control.colours.window).top, 0.2)
                                                    : control.colours.window
        Rectangle {
            anchors.fill: parent; anchors.margins: 3
            color: "transparent"
            border.color: control.colours.highlight
            border.width: control.visualFocus ? 2 : 0
        }
    }
    contentItem: Item {
        opacity: control.enabled ? 1 : 0.45
        Kirigami.Icon {
            id: symbol
            source: control.iconName
            width: 48; height: 48
            x: (parent.width - width) / 2; y: 2
            active: false
        }
        Text {
            text: control.text
            color: control.colours.windowText
            font.family: control.colours.font; font.pixelSize: 12
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            y: symbol.height + 4
            width: parent.width; height: parent.height - y
        }
    }
}
