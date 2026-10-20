pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

// The window list (Warp: Fensterliste): every window, click brings it
// forward; a window on another workspace takes the workspace along.
PlasmaCore.Dialog {
    id: windowList
    // A TaskManager.TasksModel of the windows to list.
    required property var tasks
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    mainItem: Bevel {
        kind: "frame"
        width: 360
        height: Math.min(420, listView.contentHeight + 8 + 4) || 40
        focus: true
        Keys.onEscapePressed: windowList.visible = false
        Bevel {
            kind: "field"
            anchors.fill: parent; anchors.margins: 4
            color: Kirigami.Theme.backgroundColor
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            ListView {
                id: listView
                anchors.fill: parent; anchors.margins: 2
                clip: true
                model: windowList.tasks
                delegate: Rectangle {
                    id: row
                    required property var model
                    required property int index
                    width: ListView.view.width; height: 24
                    color: hover.hovered ? Kirigami.Theme.highlightColor : "transparent"
                    HoverHandler { id: hover }
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 4; anchors.rightMargin: 4
                        Kirigami.Icon { source: row.model.decoration; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                        Text {
                            Layout.fillWidth: true
                            text: row.model.display
                            elide: Text.ElideRight
                            color: hover.hovered ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                            font: Kirigami.Theme.defaultFont
                        }
                    }
                    TapHandler {
                        onTapped: {
                            windowList.tasks.requestActivate(windowList.tasks.makeModelIndex(row.index));
                            windowList.visible = false;
                        }
                    }
                }
            }
            Text {
                visible: listView.count === 0
                anchors.centerIn: parent
                text: i18nd("warp-legacy", "No open windows")
                color: Kirigami.Theme.disabledTextColor
            }
        }
    }
}
