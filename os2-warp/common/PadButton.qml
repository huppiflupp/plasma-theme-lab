import QtQuick
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore

// A LaunchPad button: raised, pressed in while held. With an icon it is a
// square launcher (DESIGN.md §5), with text one of the text buttons; the
// mnemonic letter of the text is underlined as in OS/2 ("&Lock"). With
// both, icon and text sit side by side, left-aligned (the Control Strip's
// launch list).
Bevel {
    id: button
    property string text: ""
    property string iconName: ""
    property int iconSize: 32
    property string tip: ""
    property bool active: false
    readonly property bool down: area.pressed || active
    signal clicked()
    signal pressAndHold()

    sunken: down
    activeFocusOnTab: true
    Keys.onSpacePressed: clicked()
    Keys.onReturnPressed: clicked()
    Accessible.role: Accessible.Button
    Accessible.name: tip || text.replace("&", "")
    Accessible.onPressAction: clicked()

    Item {
        anchors.fill: parent
        anchors.leftMargin: button.down ? 1 : 0
        anchors.topMargin: button.down ? 1 : 0
        readonly property bool both: button.iconName !== "" && button.text !== ""
        Kirigami.Icon {
            id: icon
            visible: button.iconName !== ""
            anchors.centerIn: parent.both ? undefined : parent
            anchors.verticalCenter: parent.verticalCenter
            x: parent.both ? 4 : 0
            width: button.iconSize; height: width
            source: button.iconName
        }
        Text {
            visible: button.text !== ""
            anchors.centerIn: parent.both ? undefined : parent
            anchors.verticalCenter: parent.verticalCenter
            x: parent.both ? icon.x + icon.width + 4 : 0
            width: parent.both ? parent.width - x - 2 : implicitWidth
            elide: Text.ElideRight
            text: {
                const i = button.text.indexOf("&");
                const plain = button.text.replace("&", "");
                if (i < 0) return plain;
                const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
                return esc(plain.substring(0, i)) + "<u>" + esc(plain.charAt(i)) + "</u>" + esc(plain.substring(i + 1));
            }
            textFormat: Text.StyledText
            color: Kirigami.Theme.textColor
            font: Kirigami.Theme.defaultFont
        }
    }
    // The keyboard focus: OS/2's dotted line inside the button.
    Rectangle {
        visible: button.activeFocus
        anchors.fill: parent; anchors.margins: 4
        color: "transparent"; border.width: 1; border.color: Kirigami.Theme.textColor
        opacity: 0.6
    }
    PlasmaCore.ToolTipArea {
        anchors.fill: parent
        mainText: button.tip
        active: button.tip !== ""
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            onClicked: button.clicked()
            onPressAndHold: button.pressAndHold()
        }
    }
}
