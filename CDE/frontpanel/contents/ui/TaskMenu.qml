pragma ComponentBehavior: Bound
import QtQuick
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager

// The window menu of a task button (right click): minimize, maximize, keep
// above, workspace, new instance, close, through the TasksModel's requests
// as Plasma's task manager makes them. On a group's button the requests go
// to all its windows (TaskGroupingProxyModel), so only those that make
// sense for a group are offered.
//
// One Plasma dialog with a fixed set of rows: rows that do not apply are
// greyed, not hidden, as the dialog keeps the size it was first shown with
// under Wayland (see AppMenu.qml). Workspaces are listed in the menu, not
// in a submenu, for the same reason. Keyboard: Up/Down, Enter or Space,
// Escape closes.
Item {
    id: menu
    // The console's TasksModel and VirtualDesktopInfo.
    property var tasksModel
    property var desktopInfo
    // Optional function(index) -> text for a workspace's row; the
    // workspace's own name otherwise.
    property var workspaceLabel: null
    // Colours and type: a popup in the window colours by default.
    property color surface: consoleColors.window
    property color foreground: consoleColors.windowText
    property color accent: consoleColors.highlight
    property color accentText: consoleColors.highlightText
    property string fontFamily: consoleColors.font
    property int fontWeight: consoleColors.weight
    property real unit: consoleColors.unit
    readonly property bool opened: dialog.visible
    signal closed()

    // The task, followed through rows moving while the menu is open.
    property var taskIndex: null
    property int revision: 0
    property int current: -1

    // row: the task's row in tasksModel; childRow: a window in a group.
    function open(row, anchor, childRow) {
        taskIndex = childRow === undefined || childRow < 0 ? tasksModel.makePersistentModelIndex(row)
                  : tasksModel.makePersistentModelIndex(row, childRow);
        revision++;
        current = -1;
        dialog.visualParent = anchor;
        dialog.visible = true;
    }
    function close() {
        dialog.visible = false;
    }

    readonly property var atm: TaskManager.AbstractTasksModel
    // A plain QModelIndex for the requests, made afresh from the
    // persistent one; null once the task is gone.
    function modelIndex() {
        if (!taskIndex || !taskIndex.valid) return null;
        return taskIndex.parent.valid ? tasksModel.makeModelIndex(taskIndex.parent.row, taskIndex.row)
                                      : tasksModel.makeModelIndex(taskIndex.row);
    }
    function get(role) {
        const i = modelIndex();
        return i ? tasksModel.data(i, role) : undefined;
    }
    function u(pixels) { return Math.round(pixels * unit); }

    // The rows: {kind: "action" | "check" | "caption" | "separator", text,
    // icon, checked, enabled, key, arg}.
    readonly property var entries: (revision, taskIndex !== null ? build() : [])
    function build() {
        const group = Boolean(get(atm.IsGroupParent));
        const minimized = Boolean(get(atm.IsMinimized));
        const window = Boolean(get(atm.IsWindow)) || group;
        const movable = window && Boolean(get(atm.IsVirtualDesktopsChangeable));
        const onAll = Boolean(get(atm.IsOnAllVirtualDesktops));
        const on = get(atm.VirtualDesktops) || [];
        const rows = [
            {kind: "action", key: "minimize", icon: minimized ? "window-restore" : "window-minimize",
             text: minimized ? (group ? i18nd("cde-copper", "Restore All") : i18nd("cde-copper", "Restore"))
                             : (group ? i18nd("cde-copper", "Minimize All") : i18nd("cde-copper", "Minimize")),
             enabled: group || Boolean(get(atm.IsMinimizable))},
            {kind: "check", key: "maximize", text: i18nd("cde-copper", "Maximize"),
             checked: !group && Boolean(get(atm.IsMaximized)), enabled: !group && Boolean(get(atm.IsMaximizable))},
            {kind: "check", key: "keepAbove", text: i18nd("cde-copper", "Keep Above Others"),
             checked: !group && Boolean(get(atm.IsKeepAbove)), enabled: !group && window},
            {kind: "separator"},
            {kind: "caption", text: i18nd("cde-copper", "Move to Workspace")}
        ];
        const ids = desktopInfo ? desktopInfo.desktopIds : [];
        const names = desktopInfo ? desktopInfo.desktopNames : [];
        for (let i = 0; i < ids.length; i++)
            rows.push({kind: "check", key: "desktop", arg: ids[i],
                       text: typeof workspaceLabel === "function" ? workspaceLabel(i) : (names[i] || String(i + 1)),
                       checked: !onAll && on.indexOf(ids[i]) >= 0, enabled: movable});
        rows.push({kind: "check", key: "allDesktops", text: i18nd("cde-copper", "All Workspaces"),
                   checked: onAll, enabled: movable});
        rows.push({kind: "action", key: "newDesktop", icon: "list-add", text: i18nd("cde-copper", "New Workspace"),
                   enabled: movable});
        rows.push({kind: "separator"});
        rows.push({kind: "action", key: "newInstance", icon: "window-new", text: i18nd("cde-copper", "Start New Instance"),
                   enabled: Boolean(get(atm.CanLaunchNewInstance))});
        rows.push({kind: "separator"});
        rows.push({kind: "action", key: "close", icon: "window-close",
                   text: group ? i18nd("cde-copper", "Close All") : i18nd("cde-copper", "Close"),
                   enabled: group || Boolean(get(atm.IsClosable))});
        return rows;
    }
    function selectable(i) {
        const e = entries[i];
        return Boolean(e) && (e.kind === "action" || e.kind === "check") && e.enabled;
    }
    function step(delta) {
        const n = entries.length;
        let i = current;
        for (let k = 0; k < n; k++) {
            i = i < 0 ? (delta > 0 ? 0 : n - 1) : (i + delta + n) % n;
            if (selectable(i)) { current = i; return; }
        }
    }
    function trigger(i) {
        const index = modelIndex();
        if (!selectable(i) || !index) return;
        const e = entries[i];
        const m = tasksModel;
        switch (e.key) {
        case "minimize": m.requestToggleMinimized(index); break;
        case "maximize": m.requestToggleMaximized(index); break;
        case "keepAbove": m.requestToggleKeepAbove(index); break;
        case "desktop": m.requestVirtualDesktops(index, [e.arg]); break;
        // An empty list puts the window on all workspaces; from there back
        // to the current one.
        case "allDesktops": m.requestVirtualDesktops(index, e.checked ? [desktopInfo.currentDesktop] : []); break;
        case "newDesktop": m.requestNewVirtualDesktop(index); break;
        case "newInstance": m.requestNewInstance(index); break;
        case "close": m.requestClose(index); break;
        }
        close();
    }

    Connections {
        target: menu.tasksModel
        enabled: dialog.visible
        function onDataChanged() { menu.revision++; }
        // The window went away while its menu was open.
        function onRowsRemoved() { Qt.callLater(() => { if (!menu.modelIndex()) menu.close(); }); }
    }

    PlasmaCore.Dialog {
        id: dialog
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        onVisibleChanged: {
            if (visible) { body.forceActiveFocus(); return; }
            menu.taskIndex = null;
            menu.current = -1;
            menu.closed();
        }
        mainItem: Bevel {
            id: body
            width: menu.u(240)
            height: column.implicitHeight + 10
            surface: menu.surface
            focus: true
            Accessible.role: Accessible.PopupMenu
            Keys.onEscapePressed: menu.close()
            Keys.onUpPressed: menu.step(-1)
            Keys.onDownPressed: menu.step(1)
            Keys.onReturnPressed: menu.trigger(menu.current)
            Keys.onEnterPressed: menu.trigger(menu.current)
            Keys.onSpacePressed: menu.trigger(menu.current)
            Column {
                id: column
                x: 5; y: 5; width: parent.width - 10
                // The window's title, as AppMenu's heading.
                Bevel {
                    width: parent.width; height: menu.u(27)
                    surface: menu.accent
                    Text {
                        anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                        text: (menu.revision, menu.get(Qt.DisplayRole) || i18nd("cde-copper", "Window"))
                        color: menu.accentText; font.family: menu.fontFamily; font.pixelSize: menu.u(12); font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                }
                Item { width: 1; height: 3 }
                Repeater {
                    model: menu.entries
                    delegate: Loader {
                        id: entry
                        required property var modelData
                        required property int index
                        width: column.width
                        sourceComponent: modelData.kind === "separator" ? separator
                                       : modelData.kind === "caption" ? caption : row
                        Component {
                            id: separator
                            // Motif separator: an etched double line.
                            Item {
                                height: 8
                                Rectangle { y: 3; width: parent.width; height: 1; color: body.shade.bottom }
                                Rectangle { y: 4; width: parent.width; height: 1; color: body.shade.top }
                            }
                        }
                        Component {
                            id: caption
                            Text {
                                height: menu.u(22)
                                leftPadding: 6
                                text: entry.modelData.text
                                color: menu.foreground; opacity: 0.75
                                font.family: menu.fontFamily; font.pixelSize: menu.u(11); font.weight: Font.DemiBold
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                        Component {
                            id: row
                            Rectangle {
                                id: line
                                readonly property bool lit: menu.current === entry.index
                                readonly property color ink: lit ? menu.accentText : menu.foreground
                                height: menu.u(26)
                                color: lit ? menu.accent : "transparent"
                                opacity: entry.modelData.enabled ? 1 : 0.45
                                Accessible.role: Accessible.MenuItem
                                Accessible.name: entry.modelData.text
                                Accessible.checkable: entry.modelData.kind === "check"
                                Accessible.checked: Boolean(entry.modelData.checked)
                                // Motif's toggle in a menu: a small square,
                                // sunken and filled when set.
                                Bevel {
                                    visible: entry.modelData.kind === "check"
                                    x: 8; anchors.verticalCenter: parent.verticalCenter
                                    width: menu.u(11); height: width
                                    sunken: Boolean(entry.modelData.checked)
                                    surface: entry.modelData.checked ? (line.lit ? menu.accentText : menu.accent) : menu.surface
                                }
                                Kirigami.Icon {
                                    visible: entry.modelData.kind === "action"
                                    x: 6; anchors.verticalCenter: parent.verticalCenter
                                    width: menu.u(18); height: width
                                    source: entry.modelData.icon || ""
                                    active: false
                                }
                                Text {
                                    anchors { left: parent.left; leftMargin: menu.u(18) + 14; right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                                    text: entry.modelData.text
                                    color: line.ink
                                    font.family: menu.fontFamily; font.pixelSize: menu.u(12); font.weight: menu.fontWeight
                                    elide: Text.ElideRight
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onEntered: menu.current = menu.selectable(entry.index) ? entry.index : -1
                                    onClicked: menu.trigger(entry.index)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
