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
        readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark

        // Neon: the concept's bar (reference/neon-2026.png, bottom edge,
        // measured): navy, lighter at the top, a line of light along the top
        // edge that starts violet at the left and turns cyan-blue. Drawn by
        // the bar itself over the panel's background (CanFillArea: edge to
        // edge). Classic keeps the Plasma style's grey panel.
        // It runs the panel's whole length, under the system tray and the
        // clock beside the bar too: ending with the bar, it left them
        // without the line (the user's remark 21.10.2026).
        property real panelLeft: 0
        property real panelRight: 0
        function measure() {
            const w = Window.window;
            if (!w) return;
            const left = Math.max(0, Math.round(mapToItem(null, 0, 0).x));
            panelLeft = left;
            panelRight = Math.max(0, Math.round(w.width - left - width));
        }
        Timer { id: remeasure; interval: 50; onTriggered: bar.measure() }
        onWidthChanged: remeasure.restart()
        onXChanged: remeasure.restart()
        Connections { target: bar.Window.window; function onWidthChanged() { remeasure.restart(); } }
        Component.onCompleted: remeasure.restart()
        Rectangle {
            visible: bar.neon
            x: -bar.panelLeft
            width: bar.width + bar.panelLeft + bar.panelRight
            height: parent.height
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#0b1d4a" }
                GradientStop { position: 0.45; color: "#071437" }
                GradientStop { position: 1.0; color: "#040b26" }
            }
            Rectangle {
                width: parent.width; height: 2
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#b44dff" }
                    GradientStop { position: 0.12; color: "#5a6dff" }
                    GradientStop { position: 0.35; color: "#2dbbfb" }
                    GradientStop { position: 1.0; color: "#1a5ee0" }
                }
            }
            // The glow under the line.
            Rectangle {
                y: 2; width: parent.width; height: 6
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Qt.rgba(0.18, 0.55, 1, 0.30) }
                    GradientStop { position: 1.0; color: Qt.rgba(0.18, 0.55, 1, 0.0) }
                }
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 6

            TaskTab {
                id: start
                Component.onCompleted: root.startButton = start
                accent: true
                Layout.preferredHeight: bar.side
                Layout.preferredWidth: startRow.implicitWidth + 24
                active: menu.visible
                tip: root.tr("Programs, settings, the desktop and the drives")
                onClicked: menu.visible ? menu.close() : menu.open(start)
                // Text only, "Start" or "Warp" (setting startLabel): with an
                // icon beside it the word shrank to 10 px in a 32 px panel.
                Text {
                    id: startRow
                    anchors.centerIn: parent
                    text: Plasmoid.configuration.startLabel === "warp" ? "Warp" : root.tr("Start")
                    color: Kirigami.Theme.linkColor
                    font.family: Kirigami.Theme.defaultFont.family
                    font.pixelSize: Math.round(bar.side * 0.6)
                    font.bold: true
                    font.italic: Plasmoid.configuration.startLabel === "warp"
                }
            }

            // Workspaces 1-4 as the concept's buttons, the current one lit,
            // in Neon set into a darker well with a faint light along its
            // bottom, as in the concept.
            Rectangle {
                visible: Plasmoid.configuration.showWorkspaces
                Layout.preferredWidth: wsRow.implicitWidth + (bar.neon ? 6 : 0)
                Layout.preferredHeight: bar.side + (bar.neon ? 6 : 0)
                color: bar.neon ? "#050c26" : "transparent"
                border.width: bar.neon ? 1 : 0
                border.color: Qt.rgba(0.35, 0.5, 1, 0.25)
                radius: 2
                Rectangle {
                    visible: bar.neon
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 2 }
                    height: 1
                    color: Qt.rgba(0.28, 0.75, 1, 0.45)
                }
            Row {
                id: wsRow
                anchors.centerIn: parent
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
