pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The Tab Launcher after Object Desktop's Tab LaunchPad (DESIGN.md §7): a
// panel dressed as a window, its own (inactive) title bar, a row of notebook
// tabs, and the launchers of the chosen tab as square icon buttons. "Tasks"
// holds the open windows, "Main" the user's favourites, the other tabs are
// the categories of the application menu (Kicker's model, so they follow
// installed and removed programs).
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    readonly property var mainList: Launch.parse(Plasmoid.configuration.main, Launch.MAIN)
    property int tab: Plasmoid.configuration.currentTab
    onTabChanged: Plasmoid.configuration.currentTab = tab
    readonly property int unit: 40
    function tr(text, ...args) { return i18nd("warp-legacy", text, ...args); }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("Tab Launcher:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }

    Kicker.AppsModel { id: categories; flat: false; sorted: true; autoPopulate: true; showSeparators: false; appletInterface: Plasmoid }
    TaskManager.ActivityInfo { id: activities }
    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.TasksModel {
        id: windows
        activity: activities.currentActivity
        virtualDesktop: desktops.currentDesktop
        filterByActivity: true
        filterByVirtualDesktop: true
        groupMode: TaskManager.TasksModel.GroupDisabled
    }
    // Tab names: Tasks, Main, then the categories.
    readonly property var tabs: {
        const names = [tr("Tasks"), tr("Main")];
        for (let i = 0; i < categories.count; i++)
            names.push(String(categories.data(categories.index(i, 0), Qt.DisplayRole) || ""));
        return names;
    }
    readonly property var categoryModel: tab >= 2 && tab - 2 < categories.count ? categories.modelForRow(tab - 2) : null

    fullRepresentation: Bevel {
        id: pad
        kind: "frame"
        Layout.minimumWidth: 420
        Layout.preferredWidth: Math.max(420, tabRow.implicitWidth + 12)
        Layout.minimumHeight: column.implicitHeight + 8
        Layout.preferredHeight: Layout.minimumHeight

        ColumnLayout {
            id: column
            anchors.fill: parent; anchors.margins: 4
            spacing: 0

            // The title bar, as an inactive window's.
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 20
                color: pad.titleColor
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 3; anchors.rightMargin: 6
                    Kirigami.Icon { source: "start-here-kde"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                    Text {
                        Layout.fillWidth: true
                        text: root.tr("Tab Launcher – %1", root.tabs[root.tab] || "")
                        color: pad.titleText
                        font: Kirigami.Theme.defaultFont
                        elide: Text.ElideRight
                    }
                }
            }
            // The notebook tabs: the current one higher, bold, joined to the
            // page below (no line under it).
            Item {
                Layout.fillWidth: true; Layout.preferredHeight: 26; Layout.topMargin: 4
                clip: true
                Row {
                    id: tabRow
                    x: 2; anchors.bottom: parent.bottom
                    spacing: -1
                    Repeater {
                        model: root.tabs
                        Bevel {
                            id: tabItem
                            required property string modelData
                            required property int index
                            readonly property bool current: index === root.tab
                            kind: "frame"
                            width: label.implicitWidth + 18
                            height: current ? 26 : 22
                            anchors.bottom: parent.bottom
                            z: current ? 1 : 0
                            Text {
                                id: label
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: tabItem.current ? -1 : 1
                                text: tabItem.modelData
                                font.family: Kirigami.Theme.defaultFont.family
                                font.pointSize: Kirigami.Theme.defaultFont.pointSize
                                font.bold: tabItem.current
                                color: Kirigami.Theme.textColor
                            }
                            // Joined to the page: the current tab covers the
                            // page's top line.
                            Rectangle {
                                visible: tabItem.current
                                x: 1; y: parent.height - 1; width: parent.width - 2; height: 2
                                color: pad.color
                            }
                            MouseArea { anchors.fill: parent; onClicked: root.tab = tabItem.index }
                        }
                    }
                }
            }
            // The page: the tab's launchers in a row.
            Bevel {
                kind: "frame"
                Layout.fillWidth: true; Layout.preferredHeight: root.unit + 10
                ListView {
                    id: page
                    anchors.fill: parent; anchors.margins: 5
                    orientation: ListView.Horizontal
                    spacing: 2
                    clip: true
                    model: root.tab === 0 ? windows : root.tab === 1 ? root.mainList : root.categoryModel
                    delegate: PadButton {
                        required property var model
                        required property int index
                        // Main's entries are plain objects (model.modelData),
                        // windows and menu entries model rows.
                        readonly property var entry: root.tab === 1 ? model.modelData : null
                        width: root.unit; height: root.unit
                        iconSize: root.unit - 10
                        iconName: entry ? entry.icon : ""
                        tip: entry ? root.tr(entry.label) : String(model.display || "")
                        Kirigami.Icon {
                            visible: root.tab !== 1
                            anchors.centerIn: parent
                            width: root.unit - 10; height: width
                            source: root.tab !== 1 ? model.decoration : ""
                        }
                        onClicked: {
                            if (root.tab === 0) windows.requestActivate(windows.makeModelIndex(index));
                            else if (root.tab === 1) { if (entry.command) root.run(Launch.resolve(entry.command, root.tr)); }
                            else if (root.categoryModel) root.categoryModel.trigger(index, "", null);
                        }
                    }
                    Text {
                        visible: page.count === 0
                        anchors.centerIn: parent
                        text: root.tab === 0 ? root.tr("No open windows") : root.tr("Nothing here")
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }
    }
}
