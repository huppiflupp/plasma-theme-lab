pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

// The window tile: an arrow strip like a launcher's over a tile with the
// active window's icon and the number of windows. Tile and arrow open
// the list; the wheel brings the next or previous window forward.
GridLayout {
    id: windowSlot
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    rows: windowSlot.root.vertical ? 1 : 2
    columns: windowSlot.root.vertical ? 2 : 1
    rowSpacing: 1; columnSpacing: 1
    Layout.fillWidth: true; Layout.fillHeight: true
    Layout.preferredWidth: windowSlot.root.vertical ? -1 : windowSlot.root.u(68)
    Layout.preferredHeight: windowSlot.root.vertical ? windowSlot.root.u(62) : -1
    function toggle(anchor) {
        windowSlot.root.popupSegment = windowSlot;
        if (windowSlot.root.windowsDialog.visible) { windowSlot.root.windowsDialog.visible = false; return; }
        windowSlot.root.sectionDialog.visible = false;
        windowSlot.root.windowsDialog.visualParent = anchor;
        windowSlot.root.windowsDialog.visible = true;
    }
    ConsoleButton {
        id: windowArrow
        Layout.row: 0
        Layout.column: windowSlot.root.vertical && !windowSlot.root.atRight ? 1 : 0
        Layout.fillWidth: !windowSlot.root.vertical; Layout.fillHeight: windowSlot.root.vertical
        Layout.preferredHeight: windowSlot.root.vertical ? -1 : windowSlot.root.u(13)
        Layout.preferredWidth: windowSlot.root.vertical ? windowSlot.root.u(13) : -1
        text: ""
        Accessible.name: i18nd("cde-copper", "Open Windows")
        selected: windowSlot.root.windowsDialog.visible
        contentItem: Text {
            text: windowSlot.root.arrowGlyph
            color: windowSlot.colors.panelText; font.pixelSize: windowSlot.root.u(12)
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
        onClicked: windowSlot.toggle(windowButton)
    }
    ConsoleButton {
        id: windowButton
        Layout.row: windowSlot.root.vertical ? 0 : 1
        Layout.column: windowSlot.root.vertical && !windowSlot.root.atRight ? 0 : (windowSlot.root.vertical ? 1 : 0)
        Layout.fillWidth: true; Layout.fillHeight: true
        labelled: Plasmoid.configuration.launcherLabels
        text: i18ndp("cde-copper", "%1 window", "%1 windows", windowSlot.root.taskModel.count)
        Accessible.name: windowSlot.root.activeWindowTitle ? text + "\n" + windowSlot.root.activeWindowTitle : text
        selected: windowSlot.root.windowsDialog.visible
        // The list itself shows what the tooltip would.
        ToolTip.visible: hovered && !windowSlot.root.windowsDialog.visible
        onClicked: windowSlot.toggle(windowButton)
        WheelHandler {
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: event => windowSlot.root.stepWindow(event.angleDelta.y > 0 ? -1 : 1)
        }
        // The active window's own icon (a QIcon, which iconName cannot carry).
        contentItem: Item {
            implicitWidth: windowSlot.root.u(58); implicitHeight: windowSlot.root.u(55)
            Kirigami.Icon {
                id: windowIcon
                source: windowSlot.root.activeWindowIcon || "preferences-system-windows"
                width: windowButton.iconSize; height: width
                x: (parent.width - width) / 2
                y: windowButton.labelled ? 0 : (parent.height - height) / 2
                active: false
            }
            Text {
                visible: windowButton.labelled
                text: windowButton.text
                color: windowButton.selected ? windowButton.accentText : windowButton.foreground
                font.family: windowSlot.colors.font; font.pixelSize: windowSlot.root.u(11)
                font.weight: windowButton.selected ? Font.DemiBold : windowSlot.colors.weight
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                y: windowIcon.height + 1
                width: parent.width; height: parent.height - y
            }
            // Without labels the number sits in the corner.
            Text {
                visible: !windowButton.labelled && windowSlot.root.taskModel.count > 0
                anchors { right: parent.right; bottom: parent.bottom }
                text: windowSlot.root.taskModel.count
                color: windowButton.selected ? windowButton.accentText : windowButton.foreground
                font.family: windowSlot.colors.font; font.pixelSize: windowSlot.root.u(11); font.weight: Font.DemiBold
            }
        }
    }
    HoverHandler { onHoveredChanged: windowSlot.root.hoverSegment(windowSlot, hovered) }
}
