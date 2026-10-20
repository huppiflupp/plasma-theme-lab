pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The taskbar of the user's Neon concept (reference/neon-2026.png, bottom
// edge), an alternative to the Warp Bar along the top: Start opens the
// Warp menu, then the workspaces 1-4, then a button per window, the active
// one lit. The panel's system tray and clock follow as Plasma's widgets.
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.constraintHints: Plasmoid.CanFillArea
    function tr(text, ...args) { return i18nd("warp-legacy", text, ...args); }
    readonly property int popupEdge: [PlasmaCore.Types.TopEdge, PlasmaCore.Types.LeftEdge, PlasmaCore.Types.RightEdge]
        .indexOf(Plasmoid.location) >= 0 ? Plasmoid.location : PlasmaCore.Types.BottomEdge

    // The Meta key opens the Warp menu (org.kde.plasma.launchermenu).
    activationTogglesExpanded: false
    property Item startButton: null
    Connections {
        target: Plasmoid
        function onActivated() { menu.visible ? menu.close() : menu.open(root.startButton); }
    }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("Warp Taskbar:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }

    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: tasks
        activity: activities.currentActivity
        virtualDesktop: desktops.currentDesktop
        screenGeometry: Plasmoid.containment.screenGeometry
        filterByActivity: true
        filterByVirtualDesktop: Plasmoid.configuration.thisWorkspace
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortManual
    }

    fullRepresentation: Item {
        id: bar
        readonly property int side: Math.max(24, height - 8)
        Layout.minimumWidth: 400
        Layout.fillWidth: true
        Layout.preferredHeight: 44

        RowLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 6

            TaskTab {
                id: start
                Component.onCompleted: root.startButton = start
                Layout.preferredHeight: bar.side
                Layout.preferredWidth: startRow.implicitWidth + 24
                active: menu.visible
                tip: root.tr("Programs, settings, the desktop and the drives")
                onClicked: menu.visible ? menu.close() : menu.open(start)
                RowLayout {
                    id: startRow
                    anchors.centerIn: parent
                    spacing: 6
                    Kirigami.Icon { source: "start-here-kde"; Layout.preferredWidth: bar.side - 10; Layout.preferredHeight: bar.side - 10 }
                    Text { text: root.tr("Start"); color: Kirigami.Theme.linkColor; font.pixelSize: bar.side - 14; font.bold: true }
                }
            }

            // Workspaces 1-4 as the concept's buttons, the current one lit.
            Row {
                visible: Plasmoid.configuration.showWorkspaces
                spacing: 1
                Repeater {
                    model: desktops.desktopIds
                    TaskTab {
                        id: ws
                        required property var modelData
                        required property int index
                        readonly property bool current: String(modelData) === String(desktops.currentDesktop)
                        width: bar.side; height: bar.side
                        filled: current
                        active: current && !neon
                        text: String(index + 1)
                        tip: desktops.desktopNames[index] || ""
                        onClicked: root.run(Launch.DBUS + " org.kde.KWin /KWin setCurrentDesktop " + (index + 1))
                    }
                }
            }

            // A button per window.
            ListView {
                id: windows
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: ListView.Horizontal
                spacing: 6
                clip: true
                interactive: false
                model: tasks
                readonly property real each: count ? Math.min(260, (width - (count - 1) * spacing) / count) : 0
                delegate: TaskTab {
                    id: task
                    required property var model
                    required property int index
                    width: windows.each; height: windows.height
                    active: model.IsActive === true
                    tip: model.display || ""
                    onClicked: {
                        const idx = tasks.makeModelIndex(index);
                        if (model.IsActive) tasks.requestToggleMinimized(idx);
                        else tasks.requestActivate(idx);
                    }
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                        spacing: 8
                        Kirigami.Icon { source: task.model.decoration; Layout.preferredWidth: bar.side - 10; Layout.preferredHeight: bar.side - 10 }
                        Text {
                            Layout.fillWidth: true
                            text: task.model.display || ""
                            elide: Text.ElideRight
                            color: Kirigami.Theme.textColor
                            opacity: task.model.IsMinimized ? 0.6 : 1
                            font.family: Kirigami.Theme.defaultFont.family
                            font.pointSize: Kirigami.Theme.defaultFont.pointSize
                            font.bold: task.active
                        }
                    }
                }
            }
        }
    }

    DesktopMenu {
        id: menu
        location: root.popupEdge
        screenRect: Plasmoid.containment.screenGeometry
        run: root.run
    }
}
