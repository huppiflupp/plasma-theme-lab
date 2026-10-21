pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The Warp Bar after OS/2 Warp 4's WarpCenter (DESIGN.md §4), for a panel
// on the top edge: the desktop button with its cascading menu, the window
// list, lock, find and shut down, then a tray of launchers. The panel's
// system tray and clock follow as Plasma's own widgets (the layout puts
// them there), so the bar needs no tray code of its own.
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.constraintHints: Plasmoid.CanFillArea

    // The tray's launchers (launch.js TRAY for a fresh bar).
    readonly property var tray: Launch.parse(Plasmoid.configuration.tray, Launch.TRAY)
    readonly property int popupEdge: [PlasmaCore.Types.BottomEdge, PlasmaCore.Types.LeftEdge, PlasmaCore.Types.RightEdge]
        .indexOf(Plasmoid.location) >= 0 ? Plasmoid.location : PlasmaCore.Types.TopEdge
    function tr(text, ...args) { return i18nd("warp-legacy", text, ...args); }

    // The Meta key opens the desktop menu (org.kde.plasma.launchermenu).
    activationTogglesExpanded: false
    Connections {
        target: Plasmoid
        function onActivated() { desktopMenu.visible ? desktopMenu.close() : desktopMenu.open(root.desktopButton); }
    }
    property Item desktopButton: null

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("Warp Bar:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }
    // A tray launcher whose program is open brings its window forward, each
    // click the next one (as the LaunchPad's), and is marked as running.
    property int windowRevision: 0
    Connections {
        target: windows
        function onCountChanged() { root.windowRevision++; }
        function onDataChanged() { root.windowRevision++; }
    }
    function windowsOf(entry) {
        const rows = [];
        for (let i = 0; i < windows.count; i++) {
            const idx = windows.makeModelIndex(i);
            const appId = String(windows.data(idx, TaskManager.AbstractTasksModel.AppId) || "");
            const launcher = Launch.desktopId(String(windows.data(idx, TaskManager.AbstractTasksModel.LauncherUrlWithoutIcon) || ""));
            if (Launch.belongsTo(appId, entry.command) || Launch.belongsTo(launcher, entry.command)) rows.push(idx);
        }
        return rows;
    }
    function launch(entry) {
        const rows = windowsOf(entry);
        if (rows.length) {
            const active = rows.findIndex(idx => windows.data(idx, TaskManager.AbstractTasksModel.IsActive));
            windows.requestActivate(rows[(active + 1) % rows.length]);
            return;
        }
        if (entry.command) run(Launch.resolve(entry.command, root.tr));
    }

    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: windows
        activity: activities.currentActivity
        filterByActivity: true
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }

    fullRepresentation: Item {
        id: bar
        readonly property int side: Math.max(20, height - 4)
        Layout.minimumWidth: row.implicitWidth + 4
        Layout.preferredWidth: Layout.minimumWidth
        Layout.minimumHeight: 24
        Layout.preferredHeight: 28

        RowLayout {
            id: row
            anchors.verticalCenter: parent.verticalCenter
            x: 2
            spacing: 2

            // The desktop button: the word "Warp" where the WarpCenter had
            // IBM's OS/2 Warp logo.
            PadButton {
                id: desktop
                Component.onCompleted: root.desktopButton = desktop
                Layout.preferredWidth: mark.implicitWidth + 16
                Layout.preferredHeight: bar.side
                tip: root.tr("Desktop")
                active: desktopMenu.visible
                onClicked: desktopMenu.visible ? desktopMenu.close() : desktopMenu.open(desktop)
                RowLayout {
                    id: mark
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: desktop.down ? 1 : 0
                    anchors.verticalCenterOffset: desktop.down ? 1 : 0
                    spacing: 3
                    // The word alone (the user's wish): beside an icon it was
                    // too small for the 28 px bar.
                    Text {
                        text: "Warp"
                        font.family: Kirigami.Theme.defaultFont.family
                        font.pixelSize: Math.round(bar.side * 0.68)
                        font.bold: true; font.italic: true
                        color: Kirigami.Theme.linkColor
                    }
                }
            }
            Repeater {
                model: [
                    {icon: "preferences-system-windows", tip: root.tr("Window list"), action: "windows"},
                    {icon: "system-lock-screen", tip: root.tr("Lock"), action: "lock"},
                    {icon: "system-search", tip: root.tr("Find"), action: "find"},
                    {icon: "system-shutdown", tip: root.tr("Shut down"), action: "shutdown"}
                ]
                PadButton {
                    id: action
                    required property var modelData
                    Layout.preferredWidth: bar.side; Layout.preferredHeight: bar.side
                    iconName: modelData.icon; iconSize: bar.side - 6
                    tip: modelData.tip
                    active: modelData.action === "windows" && windowList.visible
                    onClicked: {
                        switch (modelData.action) {
                        case "windows": windowList.visualParent = action; windowList.visible = !windowList.visible; break;
                        case "lock": root.run(Launch.DBUS + " org.freedesktop.ScreenSaver /ScreenSaver Lock"); break;
                        case "find": root.run(Launch.DBUS + " org.kde.krunner /App display"); break;
                        case "shutdown": root.run(Launch.DBUS + " org.kde.LogoutPrompt /LogoutPrompt promptShutDown"); break;
                        }
                    }
                }
            }
            // The tray: a sunken well of launchers.
            Bevel {
                kind: "field"
                Layout.leftMargin: 4
                Layout.preferredHeight: bar.side
                Layout.preferredWidth: trayRow.implicitWidth + 6
                RowLayout {
                    id: trayRow
                    anchors.centerIn: parent
                    spacing: 1
                    Repeater {
                        model: root.tray
                        PadButton {
                            id: trayButton
                            required property var modelData
                            readonly property int open: (root.windowRevision, root.windowsOf(modelData).length)
                            Layout.preferredWidth: bar.side - 4; Layout.preferredHeight: bar.side - 4
                            iconName: modelData.icon; iconSize: bar.side - 10
                            tip: open ? root.tr("%1 (open)", root.tr(modelData.label)) : root.tr(modelData.label)
                            onClicked: root.launch(modelData)
                            // Open: a lit bar along the bottom, as a taskbar marks
                            // running programs; cyan-pink in Neon, Warp blue else.
                            Rectangle {
                                visible: trayButton.open > 0
                                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 4; rightMargin: 4; bottomMargin: 3 }
                                height: 3; radius: 1
                                gradient: Gradient {
                                    orientation: Gradient.Horizontal
                                    GradientStop { position: 0.0; color: trayButton.neon ? "#48cffe" : Kirigami.Theme.highlightColor }
                                    GradientStop { position: 1.0; color: trayButton.neon ? "#ff4fd8" : Kirigami.Theme.highlightColor }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    DesktopMenu {
        id: desktopMenu
        location: root.popupEdge
        screenRect: Plasmoid.containment.screenGeometry
        run: root.run
    }
    WindowList { id: windowList; tasks: windows; location: root.popupEdge }
}
