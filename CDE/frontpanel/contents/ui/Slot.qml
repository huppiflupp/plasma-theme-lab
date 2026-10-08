pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "launch.js" as Launch

// A launcher tile with its subpanel arrow: arrow above the tile across,
// beside it (towards the screen) upright.
GridLayout {
    id: slot
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    required property var modelData
    // Its place: "left" or "right" of the window display, and the index.
    required property int index
    property string side: ""
    rows: slot.root.vertical ? 1 : 2
    columns: slot.root.vertical ? 2 : 1
    rowSpacing: 1; columnSpacing: 1
    Layout.fillWidth: true; Layout.fillHeight: true
    Layout.preferredWidth: slot.root.vertical ? -1 : slot.root.u(68)
    Layout.preferredHeight: slot.root.vertical ? slot.root.u(62) : -1
    ConsoleButton {
        id: arrow
        Layout.row: 0
        Layout.column: slot.root.vertical && !slot.root.atRight ? 1 : 0
        Layout.fillWidth: !slot.root.vertical; Layout.fillHeight: slot.root.vertical
        Layout.preferredHeight: slot.root.vertical ? -1 : slot.root.u(13)
        Layout.preferredWidth: slot.root.vertical ? slot.root.u(13) : -1
        text: ""
        enabled: slot.modelData.menu !== ""
        opacity: enabled ? 1 : 0.35
        Accessible.name: slot.modelData.menu ? i18nd("cde-copper", "Open %1", i18nd("cde-copper", (Launch.MENUS.find(m => m.value === slot.modelData.menu) || {text: slot.modelData.menu}).text)) : ""
        selected: slot.root.sectionDialog.visible && slot.root.sectionDialog.visualParent === arrow
        contentItem: Text {
            text: slot.root.arrowGlyph
            color: slot.colors.panelText; font.pixelSize: slot.root.u(12)
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
        onClicked: { slot.root.popupSegment = slot; slot.root.openMenu(slot.modelData, arrow); }
    }
    ConsoleButton {
        id: launcher
        Layout.row: slot.root.vertical ? 0 : 1
        Layout.column: slot.root.vertical && !slot.root.atRight ? 0 : (slot.root.vertical ? 1 : 0)
        Layout.fillWidth: true; Layout.fillHeight: true
        text: Launch.slotLabel(slot.modelData, text => i18nd("cde-copper", text)); iconName: slot.modelData.icon
        labelled: Plasmoid.configuration.launcherLabels
        onClicked: slot.root.launch(slot.modelData, launcher)
        selected: drop.hot
        // Files, an application or another tile dropped on the tile.
        DropTarget {
            id: drop
            anchors.fill: parent
            launcherSlot: slot.modelData; side: slot.side; index: slot.index
            // Rearranging by press-and-hold: off until confirmed on a real
            // desktop. (A DragHandler took every press from the button, so
            // launchers no longer started, 09.10.2026.)
            draggable: false
            surface: slot.colors.panel; accent: slot.colors.highlight
            onRunRequested: command => slot.root.run(command)
            onReplaceLauncher: (desktopId, newSlot) => slot.root.replaceLauncher(slot.side, slot.index, newSlot)
            onMoveLauncher: (fromSide, fromIndex, toSide, toIndex) => slot.root.moveLauncher(fromSide, fromIndex, toSide, toIndex)
        }
        // The Applications tile, where the Meta key opens the menu.
        Component.onCompleted: if (slot.modelData.command === "@applications") slot.root.appsTile = launcher
    }
    HoverHandler { onHoveredChanged: slot.root.hoverSegment(slot, hovered) }
}
