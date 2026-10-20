pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The LaunchPad after OS/2 Warp 3 and 4 (DESIGN.md §5): two columns of
// text buttons (Lock, Find, Shut down, Window list), then square launchers,
// each with a drawer bar above it that opens a column of further launchers.
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.DefaultBackground

    readonly property var launchers: Launch.parse(Plasmoid.configuration.launchers)
    readonly property int unit: 48           // a launcher button
    readonly property int bar: 10            // the drawer bar above it
    readonly property int gap: 4
    // Popups open away from the screen edge the pad sits on; a floating
    // panel reported no edge (VM, 20.10.2026), and the popups then covered
    // the pad, so anything but an edge counts as the bottom.
    readonly property int popupEdge: [PlasmaCore.Types.TopEdge, PlasmaCore.Types.LeftEdge, PlasmaCore.Types.RightEdge]
        .indexOf(Plasmoid.location) >= 0 ? Plasmoid.location : PlasmaCore.Types.BottomEdge
    function tr(text, ...args) { return i18nd("warp-legacy", text, ...args); }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("LaunchPad:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }

    TaskManager.ActivityInfo { id: activities }
    TaskManager.VirtualDesktopInfo { id: desktops }
    // Every window of this activity: the window list, and the launchers
    // that bring their program's window forward instead of starting it again.
    TaskManager.TasksModel {
        id: windows
        activity: activities.currentActivity
        filterByActivity: true
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }

    // Copied from CDE Copper's console (raiseRunning, 1.0.0): an
    // application launcher whose program is open brings its window forward,
    // with more than one window each click the next.
    function raiseRunning(command) {
        if (String(command).indexOf("app:") !== 0) return false;
        const id = command.substring(4).replace(/\.desktop$/, "").toLowerCase();
        const rows = [];
        for (let i = 0; i < windows.count; i++) {
            const idx = windows.makeModelIndex(i);
            const appId = String(windows.data(idx, TaskManager.AbstractTasksModel.AppId) || "").replace(/\.desktop$/, "").toLowerCase();
            const launcher = Launch.desktopId(String(windows.data(idx, TaskManager.AbstractTasksModel.LauncherUrlWithoutIcon) || "")).toLowerCase();
            if (appId === id || launcher === id) rows.push(idx);
        }
        if (!rows.length) return false;
        const active = rows.findIndex(idx => windows.data(idx, TaskManager.AbstractTasksModel.IsActive));
        windows.requestActivate(rows[(active + 1) % rows.length]);
        return true;
    }
    function launch(entry) {
        drawer.visible = false;
        if (!entry.command || raiseRunning(entry.command)) return;
        run(Launch.resolve(entry.command, root.tr));
    }
    function openDrawer(index, anchor) {
        if (drawer.visible && drawer.index === index) { drawer.visible = false; return; }
        drawer.index = index;
        drawer.visualParent = anchor;
        drawer.visible = true;
    }

    fullRepresentation: Item {
        id: pad
        readonly property bool showText: Plasmoid.configuration.textButtons
        Layout.minimumWidth: content.implicitWidth + 2 * root.gap
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.minimumHeight: content.implicitHeight + 2 * root.gap
        Layout.preferredHeight: Layout.minimumHeight

        RowLayout {
            id: content
            anchors.centerIn: parent
            spacing: 2 * root.gap

            // Lock, Find, Shut down, Window list (Warp 3: Sperren, Suchen,
            // Systemabschluß, Fensterliste).
            GridLayout {
                id: textButtons
                visible: pad.showText
                columns: 2
                rowSpacing: root.gap; columnSpacing: root.gap
                // All four as wide as the widest, as on OS/2's LaunchPad.
                uniformCellWidths: true
                Layout.alignment: Qt.AlignBottom
                Repeater {
                    model: [
                        {text: root.tr("&Lock"), action: "lock"},
                        {text: root.tr("&Find…"), action: "find"},
                        {text: root.tr("&Shut down…"), action: "shutdown"},
                        {text: root.tr("&Window list"), action: "windows"}
                    ]
                    PadButton {
                        required property var modelData
                        text: modelData.text
                        Layout.fillWidth: true
                        Layout.preferredWidth: Math.max(110, metrics.advanceWidth + 24)
                        Layout.preferredHeight: (root.unit + root.bar + root.gap) / 2 - root.gap / 2
                        active: modelData.action === "windows" && windowList.visible
                        TextMetrics { id: metrics; text: modelData.text; font: Kirigami.Theme.defaultFont }
                        onClicked: {
                            switch (modelData.action) {
                            case "lock": root.run(Launch.DBUS + " org.freedesktop.ScreenSaver /ScreenSaver Lock"); break;
                            case "find": root.run(Launch.DBUS + " org.kde.krunner /App display"); break;
                            case "shutdown": root.run(Launch.DBUS + " org.kde.LogoutPrompt /LogoutPrompt promptShutDown"); break;
                            case "windows": windowList.visualParent = textButtons; windowList.visible = !windowList.visible; break;
                            }
                        }
                    }
                }
            }

            // The launchers, each under its drawer bar.
            Repeater {
                model: root.launchers
                ColumnLayout {
                    id: slot
                    required property var modelData
                    required property int index
                    spacing: root.gap / 2
                    Layout.alignment: Qt.AlignBottom
                    PadButton {
                        id: drawerBar
                        Layout.preferredWidth: root.unit; Layout.preferredHeight: root.bar
                        enabled: slot.modelData.drawer.length > 0
                        active: drawer.visible && drawer.index === slot.index
                        tip: enabled ? root.tr("More in %1", slot.modelData.label) : ""
                        onClicked: root.openDrawer(slot.index, slot)
                        // ▵ when the drawer has something in it, as in OS/2.
                        Text {
                            visible: drawerBar.enabled
                            anchors.centerIn: parent
                            text: drawer.visible && drawer.index === slot.index ? "▿" : "▵"
                            font.pixelSize: root.bar + 2
                            color: Kirigami.Theme.textColor
                        }
                    }
                    PadButton {
                        Layout.preferredWidth: root.unit; Layout.preferredHeight: root.unit
                        iconName: slot.modelData.icon
                        tip: root.tr(slot.modelData.label)
                        onClicked: root.launch(slot.modelData)
                    }
                }
            }
        }
    }

    // A drawer: a column of launchers above its bar.
    PlasmaCore.Dialog {
        id: drawer
        property int index: -1
        readonly property var entries: index >= 0 && index < root.launchers.length ? root.launchers[index].drawer : []
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: root.popupEdge
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        mainItem: Bevel {
            kind: "frame"
            width: root.unit + 2 * root.gap
            height: drawerColumn.implicitHeight + 2 * root.gap
            focus: true
            Keys.onEscapePressed: drawer.visible = false
            Column {
                id: drawerColumn
                x: root.gap; y: root.gap
                spacing: root.gap
                Repeater {
                    model: drawer.entries
                    PadButton {
                        required property var modelData
                        width: root.unit; height: root.unit
                        iconName: modelData.icon
                        tip: root.tr(modelData.label)
                        onClicked: root.launch(modelData)
                    }
                }
            }
        }
    }

    WindowList { id: windowList; tasks: windows; location: root.popupEdge }
}
