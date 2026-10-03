pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "motif.js" as Motif

Button {
    id: control
    property string iconName: ""
    property bool selected: false
    property bool horizontal: false
    property int iconSize: Math.round(38 * consoleColors.unit)
    // Colours default to the console's; popups pass the window colours.
    property color surface: consoleColors.panel
    property color foreground: consoleColors.panelText
    property color accent: consoleColors.highlight
    property color accentText: consoleColors.highlightText
    implicitWidth: Math.round(68 * consoleColors.unit)
    implicitHeight: Math.round(66 * consoleColors.unit)
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
        surface: control.selected ? control.accent
               : control.hovered ? Motif.mix(control.surface, Motif.shades(control.surface).top, 0.2)
               : control.surface
        Rectangle {
            anchors.fill: parent; anchors.margins: 3
            color: "transparent"
            border.color: control.selected ? control.accentText : control.accent
            border.width: control.visualFocus ? 2 : 0
        }
    }
    contentItem: Item {
        implicitWidth: Math.round(58 * consoleColors.unit); implicitHeight: Math.round(55 * consoleColors.unit)
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
            color: control.selected ? control.accentText : control.foreground
            font.family: consoleColors.font; font.pixelSize: Math.round(11 * consoleColors.unit)
            font.weight: control.selected ? Font.DemiBold : consoleColors.weight
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
