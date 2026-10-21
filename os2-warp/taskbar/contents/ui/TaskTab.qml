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
    // Always lit, with the concept's violet glow (the Start button).
    property bool accent: false
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
        readonly property bool lit: tab.active || tab.filled || tab.accent
        // A soft glow behind the lit button: violet for Start, cyan else.
        Rectangle {
            visible: parent.lit
            anchors.fill: parent; anchors.margins: -3
            radius: 4
            color: "transparent"
            border.width: 3
            border.color: tab.accent ? Qt.rgba(0.48, 0.30, 1, 0.45) : Qt.rgba(0.28, 0.81, 1, 0.22)
        }
        Rectangle {
            anchors.fill: parent
            radius: 2
            gradient: Gradient {
                // The current workspace: the concept's blue, lit from the
                // left and running into deep royal blue on the right
                // (measured on its "1"; top to bottom before, the user's
                // remark 21.10.2026).
                orientation: tab.filled ? Gradient.Horizontal : Gradient.Vertical
                GradientStop { position: 0.0; color: tab.filled ? "#1a9cff" : tab.active ? "#12306e" : "#0c1a40" }
                GradientStop { position: 0.3; color: tab.filled ? "#0a62f2" : tab.active ? "#0f2760" : "#0a1636" }
                GradientStop { position: 1.0; color: tab.filled ? "#002c96" : tab.active ? "#0c1d4a" : "#08112c" }
            }
            border.width: 1
            border.color: tab.active || tab.filled || tab.accent ? "#48cffe" : Qt.rgba(0.45, 0.58, 1, 0.32)
        }
        // A sheen over the upper half of the lit workspace button: off, the
        // concept's has none (its light comes from the left).
        Rectangle {
            visible: false
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 1 }
            height: parent.height * 0.45
            radius: 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.22) }
                GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.0) }
            }
        }
        // The concept's violet-pink light in the right corners: strong on
        // lit buttons, a hint on the others (lost when the buttons stopped
        // using Bevel's NeonFrame, the user's remark 21.10.2026).
        NeonFrame {
            anchors.fill: parent
            opacity: parent.lit ? 0.9 : 0.35
            light: "#48cffe"; dark: Kirigami.Theme.hoverColor; accent: "#ff4fd8"
        }
        // Start: a violet glow along the left edge, as in the concept.
        Rectangle {
            visible: tab.accent
            anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 1 }
            width: parent.width * 0.35
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Qt.rgba(0.48, 0.30, 1, 0.40) }
                GradientStop { position: 1.0; color: Qt.rgba(0.48, 0.30, 1, 0.0) }
            }
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
