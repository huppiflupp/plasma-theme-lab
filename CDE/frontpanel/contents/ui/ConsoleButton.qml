pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

Button {
    id: control
    property string iconName: ""
    property bool selected: false
    property bool horizontal: false
    property int iconSize: 38
    property color surface: "#2e7180"
    property color foreground: "#ecf1e9"
    implicitWidth: 68
    implicitHeight: 66
    padding: 5
    hoverEnabled: true
    Accessible.name: text
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()
    ToolTip.visible: hovered && Accessible.name.length > 0
    ToolTip.text: Accessible.name
    ToolTip.delay: 750
    background: Bevel {
        sunken: control.down || control.selected
        surface: control.selected ? "#e8874f" : control.hovered ? "#43828e" : control.surface
        Rectangle {
            anchors.fill: parent; anchors.margins: 3
            color: "transparent"
            border.color: "#f0b184"; border.width: control.activeFocus ? 2 : 0
        }
    }
    contentItem: Item {
        implicitWidth: 58; implicitHeight: 55
        Kirigami.Icon {
            id: symbol
            visible: control.iconName !== ""
            source: control.iconName
            width: control.iconSize; height: width
            x: control.horizontal ? 2 : (parent.width - width) / 2
            y: control.horizontal ? (parent.height - height) / 2 : 0
            active: false
        }
        Text {
            text: control.text
            color: control.selected ? "#10262b" : control.foreground
            font.family: "Noto Sans"; font.pixelSize: 11
            font.weight: control.selected ? Font.DemiBold : Font.Normal
            elide: Text.ElideRight
            horizontalAlignment: control.horizontal ? Text.AlignLeft : Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            x: control.horizontal && symbol.visible ? symbol.width + 8 : 0
            y: !control.horizontal && symbol.visible ? symbol.height + 1 : 0
            width: parent.width - x
            height: parent.height - y
        }
    }
}
