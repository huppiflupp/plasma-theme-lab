pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

// The window tile's list: every window with its icon, title and
// workspace; the active one pressed in, minimized ones faint.
PlasmaCore.Dialog {
    id: windowsPopup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { windowsKeeper.opened(); windowsBody.forceActiveFocus(); }
    mainItem: Bevel {
        id: windowsBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: windowsKeeper; root: windowsPopup.root; dialog: windowsPopup; segment: windowsPopup.root.popupSegment; inside: windowsHover.hovered }
        HoverHandler { id: windowsHover }
        Keys.onPressed: windowsKeeper.keyboard = true
        Keys.onEscapePressed: windowsPopup.visible = false
        focus: true
        width: 380
        // Up to twelve rows; more scroll.
        height: 41 + (windowsPopup.root.taskModel.count ? Math.min(windowsPopup.root.taskModel.count, 12) * 36 : 50)
        surface: windowsPopup.colors.window
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 2
            Bevel {
                Layout.fillWidth: true; Layout.preferredHeight: 27; surface: windowsPopup.colors.highlight
                Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Open Windows"); color: windowsPopup.colors.highlightText; font.family: windowsPopup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Text {
                visible: windowsPopup.root.taskModel.count === 0
                Layout.fillWidth: true; Layout.fillHeight: true
                text: i18nd("cde-copper", "No open windows")
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                color: windowsPopup.colors.windowText; font.family: windowsPopup.colors.font; font.pixelSize: 12
            }
            ListView {
                id: windowList
                visible: windowsPopup.root.taskModel.count > 0
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; spacing: 2
                model: windowsPopup.root.taskModel
                ScrollBar.vertical: ScrollBar { policy: windowList.contentHeight > windowList.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }
                delegate: ConsoleButton {
                    id: windowEntry
                    required property int index
                    required property var model
                    width: windowList.width - (windowList.contentHeight > windowList.height ? 12 : 0)
                    height: 34
                    horizontal: true; surface: windowsPopup.colors.window; foreground: windowsPopup.colors.windowText
                    text: model.display || i18nd("cde-copper", "Window")
                    iconName: ""
                    leftPadding: 36; rightPadding: 34
                    selected: Boolean(model.IsActive) || String(model.WinIdList) === windowsPopup.root.activeWindowId
                    opacity: model.IsMinimized ? 0.6 : 1
                    Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: 22; height: 22; source: windowEntry.model.decoration; active: false }
                    Text {
                        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        text: windowsPopup.root.windowWorkspace(windowEntry.model.IsOnAllVirtualDesktops, windowEntry.model.VirtualDesktops)
                        color: windowEntry.selected ? windowsPopup.colors.highlightText : windowsPopup.colors.windowText
                        font.family: windowsPopup.colors.font; font.pixelSize: 11
                    }
                    onClicked: {
                        windowsPopup.visible = false;
                        const idx = windowsPopup.root.taskModel.makeModelIndex(index);
                        if (model.IsActive) windowsPopup.root.taskModel.requestToggleMinimized(idx); else windowsPopup.root.taskModel.requestActivate(idx);
                    }
                    // The window menu, opened at the window tile: this list
                    // closes as the menu takes the focus. A MouseArea, not a
                    // TapHandler: it takes the press, so the panel's own
                    // context menu does not open as well; the left button is
                    // not accepted and stays the button's.
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.RightButton
                        onPressed: {
                            const anchor = windowsPopup.visualParent;
                            windowsPopup.visible = false;
                            windowsPopup.root.taskMenu.open(windowEntry.index, anchor);
                        }
                    }
                }
            }
        }
    }
}
