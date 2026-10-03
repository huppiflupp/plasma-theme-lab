import QtQuick
import org.kde.kirigami as Kirigami

// One line of a console menu: icon, label, and a cascade arrow for a
// submenu. Highlighted rows take the selection colours, like Motif menus.
Rectangle {
    id: row
    property var glyph
    property string label
    property bool cascade: false
    property bool highlighted: false
    signal activated()
    signal hovered()
    implicitHeight: 30
    color: highlighted ? consoleColors.highlight : "transparent"
    Accessible.role: cascade ? Accessible.ButtonMenu : Accessible.MenuItem
    Accessible.name: label
    Kirigami.Icon {
        id: icon
        x: 6; anchors.verticalCenter: parent.verticalCenter
        width: 22; height: 22
        source: row.glyph
        active: false
    }
    Text {
        anchors { left: icon.right; leftMargin: 8; right: arrow.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
        text: row.label
        color: row.highlighted ? consoleColors.highlightText : consoleColors.windowText
        font.family: consoleColors.font; font.pixelSize: 12
        elide: Text.ElideRight
    }
    Text {
        id: arrow
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        text: row.cascade ? "▸" : ""
        color: row.highlighted ? consoleColors.highlightText : consoleColors.windowText
        font.pixelSize: 12
    }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: row.hovered()
        onClicked: row.activated()
    }
}
