pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "motif.js" as Motif

// The workspace switcher: a button per workspace, with the windows on it
// as icons (WindowWell) or as a miniature pager (WindowMap) below it.
Bevel {
    id: workspacesBlock
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: Plasmoid.configuration.showWorkspaces
    // With the windows each button has a well of window icons below it.
    readonly property bool withWindows: workspacesBlock.root.windowDisplay === "workspaces" || workspacesBlock.root.windowDisplay === "pager"
    // Two rows across: more workspaces widen the block, upright they
    // stack. With the windows one row across, for room under the buttons.
    readonly property int columns: workspacesBlock.root.vertical ? 2
                                 : withWindows ? Math.max(1, workspacesBlock.root.desktopInfo.desktopIds.length)
                                 : Math.max(2, Math.ceil(workspacesBlock.root.desktopInfo.desktopIds.length / 2))
    readonly property int rows: Math.max(1, Math.ceil(workspacesBlock.root.desktopInfo.desktopIds.length / columns))
    Layout.fillWidth: workspacesBlock.root.vertical; Layout.fillHeight: !workspacesBlock.root.vertical
    // With the windows each column holds four icons across.
    readonly property int cellWidth: withWindows ? Math.max(Plasmoid.configuration.workspaceButtonWidth, 4 * 25 + 4) : Plasmoid.configuration.workspaceButtonWidth
    Layout.preferredWidth: workspacesBlock.root.vertical ? -1 : workspacesBlock.root.u((cellWidth + 12) * columns)
    Layout.preferredHeight: workspacesBlock.root.vertical ? workspacesBlock.root.u(withWindows ? 8 + rows * 70 : 72) : -1
    surface: Motif.shades(workspacesBlock.colors.panel).bottom; sunken: true
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 4; spacing: 3
        Text {
            // With the windows the room goes to their icons.
            visible: !workspacesBlock.withWindows
            Layout.fillWidth: true; text: i18nd("cde-copper", "WORKSPACES"); color: workspacesBlock.colors.hard ? Motif.stark(workspacesBlock.colors.panel) : Motif.shades(workspacesBlock.colors.panel).top
            font.pixelSize: workspacesBlock.root.u(9); font.family: workspacesBlock.colors.font; horizontalAlignment: Text.AlignHCenter
            font.weight: workspacesBlock.colors.weight
        }
        GridLayout {
            columns: parent.parent.columns; rowSpacing: 3; columnSpacing: 3
            Layout.fillWidth: true; Layout.fillHeight: true
            Repeater {
                model: workspacesBlock.root.desktopInfo.desktopIds
                delegate: ColumnLayout {
                    id: workspaceCell
                    required property int index
                    required property var modelData
                    Layout.fillWidth: true; Layout.fillHeight: true
                    spacing: 2
                    ConsoleButton {
                        readonly property int index: workspaceCell.index
                        readonly property var modelData: workspaceCell.modelData
                        Layout.fillWidth: true; Layout.fillHeight: !workspacesBlock.withWindows
                        // With the windows a low button, the icons below it larger.
                        Layout.preferredHeight: workspacesBlock.withWindows ? workspacesBlock.root.u(17) : -1
                        topPadding: workspacesBlock.withWindows ? 0 : 5; bottomPadding: topPadding
                        implicitWidth: workspacesBlock.root.u(workspacesBlock.root.vertical ? 40 : workspacesBlock.cellWidth); implicitHeight: workspacesBlock.root.u(23)
                        text: workspacesBlock.root.workspaceLabel(index)
                        Accessible.name: workspacesBlock.root.workspaceTitle(index)
                        selected: workspacesBlock.root.desktopInfo.currentDesktop === modelData
                        // As in CDE, each workspace in a colour of its own.
                        readonly property var own: Plasmoid.configuration.workspaceColours && workspacesBlock.root.workspaceColours.length
                                                   ? workspacesBlock.root.workspaceColours[index % workspacesBlock.root.workspaceColours.length] : null
                        surface: own ? own.bg : workspacesBlock.colors.panel
                        foreground: own ? (workspacesBlock.colors.hard ? Motif.stark(own.bg) : own.fg) : workspacesBlock.colors.panelText
                        accent: own ? own.sel : workspacesBlock.colors.highlight
                        accentText: own ? (workspacesBlock.colors.hard ? Motif.stark(own.bg) : own.fg) : workspacesBlock.colors.highlightText
                        onClicked: workspacesBlock.root.run(workspacesBlock.root.dbus + " org.kde.KWin /KWin setCurrentDesktop " + (index + 1))
                    }
                    WindowWell {
                        root: workspacesBlock.root; colors: workspacesBlock.colors
                        visible: workspacesBlock.root.windowDisplay === "workspaces"
                        desktop: workspaceCell.modelData
                        Layout.fillWidth: true; Layout.fillHeight: true
                    }
                    WindowMap {
                        root: workspacesBlock.root; colors: workspacesBlock.colors
                        visible: workspacesBlock.root.windowDisplay === "pager"
                        desktop: workspaceCell.modelData
                        desktopNumber: workspaceCell.index + 1
                        Layout.fillWidth: true; Layout.fillHeight: true
                    }
                }
            }
        }
    }

    // A workspace in miniature, as the pagers of the 1990s drew it: each
    // window a raised rectangle where it lies on the screens, its icon in
    // it, the active one in the selection colour. Minimized windows lie as
    // small icons along the map's lower edge, where dtwm put its icons.
    // A click brings a window forward; one beside the windows switches to
    // the workspace.
    component WindowMap: Bevel {
        id: map
        // The console (main.qml) and its colours: given, never looked up.
        required property var root
        required property var colors
        property string desktop: ""
        property int desktopNumber: 1
        sunken: true
        surface: Motif.shades(map.colors.panel).bottom
        readonly property var rows: map.root.windowRows(desktop, map.root.windowRevision)
        readonly property rect area: map.root.desktopArea
        readonly property real scale: Math.min((width - 4) / Math.max(1, area.width), (height - 4) / Math.max(1, area.height))
        MouseArea {
            anchors.fill: parent
            onClicked: map.root.run(map.root.dbus + " org.kde.KWin /KWin setCurrentDesktop " + map.desktopNumber)
        }
        Item {
            id: screens
            width: Math.round(map.area.width * map.scale); height: Math.round(map.area.height * map.scale)
            x: Math.round((map.width - width) / 2); y: Math.round((map.height - height) / 2)
            clip: true
            // The screens' outlines, for orientation with more than one.
            Repeater {
                model: Qt.application.screens.length > 1 ? Qt.application.screens : []
                delegate: Rectangle {
                    required property var modelData
                    x: Math.round((modelData.virtualX - map.area.x) * map.scale)
                    y: Math.round((modelData.virtualY - map.area.y) * map.scale)
                    width: Math.round(modelData.width * map.scale); height: Math.round(modelData.height * map.scale)
                    color: "transparent"
                    border.width: 1; border.color: Motif.shades(map.colors.panel).top
                    opacity: 0.35
                }
            }
            Repeater {
                model: map.rows
                delegate: ConsoleButton {
                    id: windowRect
                    required property int modelData
                    readonly property var idx: map.root.taskModel.makeModelIndex(modelData)
                    readonly property int revision: map.root.windowRevision
                    readonly property rect frame: (revision, map.root.taskModel.data(idx, TaskManager.AbstractTasksModel.Geometry)) || Qt.rect(0, 0, 0, 0)
                    visible: !(revision, map.root.taskModel.data(idx, TaskManager.AbstractTasksModel.IsMinimized)) && frame.width > 0
                    x: Math.round((frame.x - map.area.x) * map.scale)
                    y: Math.round((frame.y - map.area.y) * map.scale)
                    width: Math.max(6, Math.round(frame.width * map.scale))
                    height: Math.max(6, Math.round(frame.height * map.scale))
                    // Top windows over lower ones.
                    z: (revision, map.root.taskModel.data(idx, TaskManager.AbstractTasksModel.StackingOrder)) || 0
                    padding: 0; text: ""
                    Accessible.name: (revision, map.root.taskModel.data(idx, Qt.DisplayRole) || i18nd("cde-copper", "Window"))
                    selected: (revision, Boolean(map.root.taskModel.data(idx, TaskManager.AbstractTasksModel.IsActive)))
                    contentItem: Item {
                        Kirigami.Icon {
                            readonly property int side: Math.min(map.root.u(20), Math.min(windowRect.width, windowRect.height) - 4)
                            visible: side >= 8
                            anchors.centerIn: parent
                            width: side; height: side
                            source: (windowRect.revision, map.root.taskModel.data(windowRect.idx, Qt.DecorationRole))
                            active: false; roundToIconSize: false
                        }
                    }
                    onClicked: {
                        if (selected) map.root.taskModel.requestToggleMinimized(idx); else map.root.taskModel.requestActivate(idx);
                    }
                    // The window menu. A MouseArea, not a TapHandler: it takes the
                    // press, so the panel's own context menu does not open as well;
                    // the left button is not accepted and stays the button's.
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.RightButton
                        onPressed: map.root.taskMenu.open(windowRect.modelData, windowRect)
                    }
                }
            }
        }

        // Minimized windows, as dtwm laid its icons along the bottom of the
        // screen: a row of small icons at the map's lower left, without a
        // frame, on the sunken surface. A click brings the window back, the
        // right button opens its menu; what does not fit is counted, "+3".
        Row {
            id: iconRow
            anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 2
            spacing: 1
            z: 2
            readonly property int side: Math.max(8, Math.min(map.root.u(14), Math.floor((map.height - 4) / 3)))
            readonly property var minimized: {
                const revision = map.root.windowRevision;
                return map.rows.filter(i => Boolean(map.root.taskModel.data(map.root.taskModel.makeModelIndex(i), TaskManager.AbstractTasksModel.IsMinimized)));
            }
            readonly property int capacity: Math.max(1, Math.floor((map.width - 4 + 1) / (side + 1)))
            readonly property bool overflow: minimized.length > capacity
            Repeater {
                model: iconRow.overflow ? iconRow.minimized.slice(0, iconRow.capacity - 1) : iconRow.minimized
                delegate: Item {
                    id: minimizedIcon
                    required property int modelData
                    readonly property var idx: map.root.taskModel.makeModelIndex(modelData)
                    readonly property int revision: map.root.windowRevision
                    width: iconRow.side; height: iconRow.side
                    Accessible.name: (revision, map.root.taskModel.data(idx, Qt.DisplayRole) || i18nd("cde-copper", "Window"))
                    Kirigami.Icon {
                        anchors.fill: parent
                        source: (minimizedIcon.revision, map.root.taskModel.data(minimizedIcon.idx, Qt.DecorationRole))
                        active: false; roundToIconSize: false
                    }
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        hoverEnabled: true
                        QQC2.ToolTip.visible: containsMouse
                        QQC2.ToolTip.text: minimizedIcon.Accessible.name
                        QQC2.ToolTip.delay: 750
                        onClicked: mouse => {
                            if (mouse.button === Qt.RightButton) map.root.taskMenu.open(minimizedIcon.modelData, minimizedIcon);
                            else map.root.taskModel.requestActivate(minimizedIcon.idx);
                        }
                    }
                }
            }
            Text {
                visible: iconRow.overflow
                width: iconRow.side; height: iconRow.side
                text: "+" + (iconRow.minimized.length - iconRow.capacity + 1)
                color: map.colors.panelText
                font.family: map.colors.font; font.pixelSize: map.root.u(9)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // A workspace's windows as small icon buttons in a sunken well: a click
    // brings a window forward (and its workspace), on the active one it
    // minimizes. What does not fit is counted in the last place, "+3".
    component WindowWell: Bevel {
        id: iconWell
        // The console (main.qml) and its colours: given, never looked up.
        required property var root
        required property var colors
        property string desktop: ""
        sunken: true
        surface: Motif.shades(iconWell.colors.panel).bottom
        readonly property var rows: iconWell.root.windowRows(desktop, iconWell.root.windowRevision)
        // Two rows of icons in the well's height, no larger than 24.
        readonly property int side: Math.max(10, Math.min(iconWell.root.u(24), Math.floor((height - 4 - 1) / 2)))
        readonly property int perRow: Math.max(1, Math.floor((width - 4 + 1) / (side + 1)))
        readonly property int capacity: perRow * Math.max(1, Math.floor((height - 4 + 1) / (side + 1)))
        readonly property bool overflow: rows.length > capacity
        Flow {
            anchors.fill: parent; anchors.margins: 2
            spacing: 1
            clip: true
            Repeater {
                model: iconWell.overflow ? iconWell.rows.slice(0, iconWell.capacity - 1) : iconWell.rows
                delegate: ConsoleButton {
                    id: windowIcon
                    required property int modelData
                    readonly property var idx: iconWell.root.taskModel.makeModelIndex(modelData)
                    readonly property int revision: iconWell.root.windowRevision
                    width: iconWell.side; height: iconWell.side
                    padding: 0; text: ""
                    Accessible.name: (revision, iconWell.root.taskModel.data(idx, Qt.DisplayRole) || i18nd("cde-copper", "Window"))
                    selected: (revision, Boolean(iconWell.root.taskModel.data(idx, TaskManager.AbstractTasksModel.IsActive)))
                    opacity: (revision, iconWell.root.taskModel.data(idx, TaskManager.AbstractTasksModel.IsMinimized)) ? 0.5 : 1
                    contentItem: Item {
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: Math.round(iconWell.side * 0.75); height: width
                            source: (windowIcon.revision, iconWell.root.taskModel.data(windowIcon.idx, Qt.DecorationRole))
                            active: false; roundToIconSize: false
                        }
                    }
                    onClicked: {
                        if (selected) iconWell.root.taskModel.requestToggleMinimized(idx); else iconWell.root.taskModel.requestActivate(idx);
                    }
                    // The window menu. A MouseArea, not a TapHandler: it takes the
                    // press, so the panel's own context menu does not open as well;
                    // the left button is not accepted and stays the button's.
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.RightButton
                        onPressed: iconWell.root.taskMenu.open(windowIcon.modelData, windowIcon)
                    }
                }
            }
            Text {
                visible: iconWell.overflow
                width: iconWell.side; height: iconWell.side
                text: "+" + (iconWell.rows.length - iconWell.capacity + 1)
                color: iconWell.colors.panelText
                font.family: iconWell.colors.font; font.pixelSize: iconWell.root.u(9)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
