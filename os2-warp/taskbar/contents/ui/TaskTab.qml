import QtQuick
import org.kde.kirigami as Kirigami

// A taskbar button. Neon after the concept (reference/neon-2026.png,
// bottom edge): a dark tile with a faint blue outline; the active window
// lit, its outline cyan with a glowing line along the bottom; the current
// workspace filled blue (filled: true). Classic: OS/2's raised button,
// pressed in while active (PadButton).
Item {
    id: tab
    property bool active: false
    property bool filled: false
    property string tip: ""
    property string text: ""
    default property alias content: holder.data
    signal clicked()
    readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark

    PadButton {
        anchors.fill: parent
        visible: !tab.neon
        active: tab.active
        text: tab.text
        tip: tab.tip
        onClicked: tab.clicked()
        // The current workspace in Warp's selection blue, so it reads at a
        // glance; a pressed-in button alone was too faint (VM, 21.10.2026).
        Rectangle {
            visible: tab.filled
            anchors.fill: parent; anchors.margins: 3
            color: Kirigami.Theme.highlightColor
            Text { anchors.centerIn: parent; text: tab.text; color: Kirigami.Theme.highlightedTextColor; font: Kirigami.Theme.defaultFont }
        }
    }

    Item {
        anchors.fill: parent
        visible: tab.neon
        // A soft glow behind the lit button.
        Rectangle {
            visible: tab.active || tab.filled
            anchors.fill: parent; anchors.margins: -3
            radius: 4
            color: "transparent"
            border.width: 3
            border.color: Qt.rgba(0.28, 0.81, 1, 0.18)
        }
        Rectangle {
            anchors.fill: parent
            radius: 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: tab.filled ? "#3a8cff" : tab.active ? "#12306e" : "#0c1638" }
                GradientStop { position: 1.0; color: tab.filled ? "#1a52d6" : tab.active ? "#0c1d4a" : "#080f2a" }
            }
            border.width: 1
            border.color: tab.active || tab.filled ? "#48cffe" : Qt.rgba(0.45, 0.58, 1, 0.32)
        }
        // The concept's line of light under the active window.
        Rectangle {
            visible: tab.active
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 6; rightMargin: 6; bottomMargin: 1 }
            height: 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Qt.rgba(0.28, 0.81, 1, 0.2) }
                GradientStop { position: 0.5; color: "#bff0ff" }
                GradientStop { position: 1.0; color: Qt.rgba(0.28, 0.81, 1, 0.2) }
            }
        }
        Text {
            visible: tab.text !== ""
            anchors.centerIn: parent
            text: tab.text
            color: tab.filled ? "#ffffff" : Kirigami.Theme.textColor
            font: Kirigami.Theme.defaultFont
        }
        MouseArea { anchors.fill: parent; onClicked: tab.clicked() }
    }
    Item { id: holder; anchors.fill: parent }
}
