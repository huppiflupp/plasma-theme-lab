pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Qt.labs.folderlistmodel
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The RISC OS iconbar (DESIGN.md §5): along the bottom of the screen, the
// filing systems on the left with their names below (here the root file
// system, the home folder, mounted media, and Apps, which opens the
// application menu), the running programs on the right, one icon per
// program, then the clock in its white box and the task manager.
//
// Select (left click) on a program brings its window forward, or
// iconises it when it is in front; Adjust (middle click) opens another
// window of it, as RISC OS's Adjust opens a second view.
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.constraintHints: Plasmoid.CanFillArea
    function tr(text, ...args) { return i18nd("risc-legacy", text, ...args); }
    readonly property int popupEdge: [PlasmaCore.Types.TopEdge, PlasmaCore.Types.LeftEdge, PlasmaCore.Types.RightEdge]
        .indexOf(Plasmoid.location) >= 0 ? Plasmoid.location : PlasmaCore.Types.BottomEdge

    // Meta opens the Apps menu (org.kde.plasma.launchermenu).
    activationTogglesExpanded: false
    property Item appsButton: null
    Connections {
        target: Plasmoid
        function onActivated() { menu.visible ? menu.close() : menu.open(root.appsButton); }
    }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("Iconbar:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }
    function launch(command) { run(Launch.resolve(command, root.tr)); }

    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: tasks
        activity: activities.currentActivity
        virtualDesktop: desktops.currentDesktop
        screenGeometry: Plasmoid.containment.screenGeometry
        filterByActivity: true
        filterByVirtualDesktop: false
        groupMode: TaskManager.TasksModel.GroupApplications
        groupInline: false
        sortMode: TaskManager.TasksModel.SortAlpha
        launchInPlace: true
    }
    // The iconised windows, one by one: RISC OS puts each on the Pinboard
    // as an icon with the window's title; here they sit on the iconbar,
    // left of the programs (the user's question 25.10.2026: where do
    // minimised windows go?).
    TaskManager.TasksModel {
        id: iconised
        activity: activities.currentActivity
        virtualDesktop: desktops.currentDesktop
        screenGeometry: Plasmoid.containment.screenGeometry
        filterByActivity: true
        filterByVirtualDesktop: false
        filterNotMinimized: true
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortLastActivated
    }

    // Mounted media, as RISC OS shows a drive icon per filing system.
    readonly property string user: String(Qt.resolvedUrl("~")).split("/").pop()
    FolderListModel {
        id: media
        folder: "file:///run/media/" + root.user
        showFiles: false
    }

    fullRepresentation: Item {
        id: bar
        Layout.minimumWidth: 300
        Layout.fillWidth: true
        Layout.preferredHeight: 64
        readonly property int icon: Math.max(16, Math.min(Plasmoid.configuration.iconSize, height - label - 6))
        readonly property int label: Math.round(Kirigami.Theme.smallFont.pixelSize > 0 ? Kirigami.Theme.smallFont.pixelSize * 1.4
                                                                                        : Kirigami.Theme.smallFont.pointSize * 1.9)

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 4
            spacing: 4

            // ---- filing systems -------------------------------------
            IconbarItem {
                iconName: "drive-harddisk"; text: root.tr("Discs")
                size: bar.icon; labelHeight: bar.label
                tip: root.tr("The root file system")
                onSelect: root.launch("@files /")
            }
            IconbarItem {
                iconName: "user-home"; text: root.tr("Home")
                size: bar.icon; labelHeight: bar.label
                tip: root.tr("Your home folder")
                onSelect: root.launch("@files ~")
            }
            Repeater {
                model: media
                IconbarItem {
                    required property string fileName
                    required property string filePath
                    iconName: "drive-removable-media"; text: fileName
                    size: bar.icon; labelHeight: bar.label
                    visible: filePath.indexOf("/run/media/") === 0
                    onSelect: root.launch("@files " + filePath)
                }
            }
            IconbarItem {
                id: apps
                Component.onCompleted: root.appsButton = apps
                iconName: "applications-all"; fallback: "applications-other"
                text: root.tr("Apps")
                size: bar.icon; labelHeight: bar.label
                tip: root.tr("Programs, settings, folders; type to find a program")
                active: menu.visible
                onSelect: menu.visible ? menu.close() : menu.open(apps)
            }

            Item { Layout.fillWidth: true }

            // ---- iconised windows -----------------------------------
            Repeater {
                model: iconised
                IconbarItem {
                    required property var model
                    required property int index
                    iconSource: model.decoration
                    text: model.display || ""
                    size: Math.round(bar.icon * 0.7); labelHeight: bar.label
                    labelWidth: bar.icon * 2.4
                    tip: root.tr("Iconised: %1", model.display || "")
                    onSelect: iconised.requestToggleMinimized(iconised.makeModelIndex(index))
                }
            }
            Rectangle {
                visible: iconised.count > 0
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                Layout.topMargin: 8; Layout.bottomMargin: 8
                color: Kirigami.Theme.disabledTextColor
            }

            // ---- programs -------------------------------------------
            Repeater {
                model: tasks
                IconbarItem {
                    id: task
                    required property var model
                    required property int index
                    iconSource: model.decoration
                    text: Plasmoid.configuration.taskLabels ? (model.AppName || model.display || "") : ""
                    size: bar.icon; labelHeight: Plasmoid.configuration.taskLabels ? bar.label : 0
                    tip: model.display || ""
                    active: model.IsActive === true
                    onSelect: {
                        const idx = tasks.makeModelIndex(index);
                        if (model.IsGroupParent) tasks.requestActivate(tasks.makeModelIndex(index, (model.IsActive ? 1 : 0)));
                        else if (model.IsActive) tasks.requestToggleMinimized(idx);
                        else tasks.requestActivate(idx);
                    }
                    onAdjust: tasks.requestNewInstance(tasks.makeModelIndex(index))
                }
            }

            // ---- clock ----------------------------------------------
            Clock {
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.preferredHeight: Math.round(bar.icon * 0.75)
                Layout.preferredWidth: implicitWidth
                riscos: Plasmoid.configuration.clockStyle === "riscos"
                onClicked: root.launch("@calendar")
            }
            IconbarItem {
                iconName: "utilities-system-monitor"; text: ""
                size: bar.icon; labelHeight: 0
                tip: root.tr("Task manager: programs and memory")
                onSelect: root.launch("@sysmon")
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
