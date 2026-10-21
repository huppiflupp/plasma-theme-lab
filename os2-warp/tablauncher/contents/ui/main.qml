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

    // A drawer at the bottom left, as Mac OS 9's Control Strip: the tab at
    // its right end slides it out of the screen to the left and back. It
    // lives alone in a bottom (or top) panel, left aligned, of length
    // "custom" with a minimum of 10 px (PanelsPage.qml): the panel follows
    // the applet's width, so a closed drawer is no wider than its tab and
    // covers nothing else. Not "fit": Plasma keeps a fit panel at least as
    // long as it is thick (PanelView::resizeWindow), 116 px of empty panel
    // beside the tab. Not the left edge: a vertical panel is at least as
    // long as it is thick too, and the drawer is ~800 px thick there.
    property bool sliding: false
    // Alone in its panel, the panel draws no background of its own (Panel.qml
    // drops it for a containment with NoBackground); shared with other
    // widgets, the panel stays as it is.
    readonly property bool alone: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
        && Plasmoid.containment && (Plasmoid.containment.applets || []).length === 1
    onAloneChanged: if (alone) Plasmoid.containment.backgroundHints = PlasmaCore.Types.NoBackground
    Component.onCompleted: if (alone) Plasmoid.containment.backgroundHints = PlasmaCore.Types.NoBackground
    // No panel margins: the drawer's frame is the strip's edge.
    Plasmoid.constraintHints: Plasmoid.CanFillArea

    fullRepresentation: Item {
        id: drawer
        readonly property int handle: 22
        // Natural width: all tabs in a row; "drawerWidth" caps it where
        // another panel shares the edge (the tab row then scrolls).
        readonly property real padWidth: Plasmoid.configuration.drawerWidth > 0
            ? Plasmoid.configuration.drawerWidth : Math.max(420, tabRow.implicitWidth + 12)
        readonly property bool open: !Plasmoid.configuration.collapsed
        // What shows: the pad and its tab, or only the tab.
        readonly property real shown: (open || root.sliding ? padWidth : 0) + handle
        // The panel keeps a margin at both ends of its length (its
        // containment, after the Plasma style). The strip is drawn over
        // them, flush with the screen edge, and the applet is that much
        // narrower: the panel is exactly as wide as what shows.
        property int edgeLeft: 0
        property int edgeRight: 0
        function measure() {
            const w = Window.window;
            if (!root.alone || !w) return;
            const left = Math.max(0, Math.round(mapToItem(null, 0, 0).x));
            const right = Math.max(0, Math.round(w.width - left - width));
            if (left !== edgeLeft) edgeLeft = left;
            if (right !== edgeRight) edgeRight = right;
        }
        Timer { id: remeasure; interval: 50; onTriggered: drawer.measure() }
        onWidthChanged: remeasure.restart()
        Connections { target: drawer.Window.window; function onWidthChanged() { remeasure.restart(); } }
        Component.onCompleted: remeasure.restart()
        Layout.minimumWidth: Math.max(1, shown - edgeLeft - edgeRight)
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.minimumHeight: column.implicitHeight + 8
        Layout.preferredHeight: Layout.minimumHeight
        // Opening: the panel widens at once, then the pad slides in;
        // closing: the pad slides out, then the room goes back (slideDone).
        function toggle() {
            root.sliding = true;
            Plasmoid.configuration.collapsed = open;
            slideDone.restart();
        }
        Timer { id: slideDone; interval: 260; onTriggered: root.sliding = false }

    Item {
        id: strip
        x: -drawer.edgeLeft
        width: drawer.width + drawer.edgeLeft + drawer.edgeRight
        height: parent.height
        clip: true

        Bevel {
            id: pad
            kind: "frame"
            width: drawer.padWidth
            height: parent.height
            x: drawer.open ? 0 : -width
            Behavior on x { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

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
                // page below (no line under it). More tabs than room: arrows at
                // the right turn them as on an OS/2 notebook, and so does the
                // wheel; the last one was simply cut off before.
                Item {
                    id: tabStrip
                    Layout.fillWidth: true; Layout.preferredHeight: 26; Layout.topMargin: 4
                    readonly property bool overflow: tabRow.implicitWidth + 4 > width
                    readonly property real room: width - (overflow ? arrows.width + 4 : 0)
                    property real shift: 0
                    function turn(step) {
                        shift = Math.max(0, Math.min(tabRow.implicitWidth + 4 - room, shift + step));
                    }
                    onWidthChanged: turn(0)
                    WheelHandler { onWheel: event => tabStrip.turn(event.angleDelta.y < 0 || event.angleDelta.x < 0 ? 80 : -80) }
                    Item {
                        width: tabStrip.room; height: parent.height
                        clip: true
                    Row {
                        id: tabRow
                        x: 2 - tabStrip.shift; anchors.bottom: parent.bottom
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
                    Row {
                        id: arrows
                        visible: tabStrip.overflow
                        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.bottomMargin: 1
                        spacing: 1
                        PadButton { width: 20; height: 20; text: "◂"; enabled: tabStrip.shift > 0; onClicked: tabStrip.turn(-120) }
                        PadButton { width: 20; height: 20; text: "▸"; enabled: tabStrip.shift < tabRow.implicitWidth + 4 - tabStrip.room; onClicked: tabStrip.turn(120) }
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

        // The tab: a narrow raised strip with an arrow, always at the drawer's
        // right end.
        Bevel {
            id: tabHandle
            kind: "frame"
            x: pad.x + pad.width
            width: drawer.handle
            height: parent.height
            Text {
                anchors.centerIn: parent
                text: drawer.open ? "◂" : "▸"
                color: Kirigami.Theme.textColor
                font.pixelSize: 14
            }
            // grip lines, as on the Mac OS 9 strip's tab
            Column {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom; anchors.bottomMargin: 8
                spacing: 2
                Repeater { model: 3; Rectangle { width: 8; height: 1; color: Kirigami.Theme.disabledTextColor } }
            }
            MouseArea { anchors.fill: parent; onClicked: drawer.toggle() }
            PlasmaCore.ToolTipArea { anchors.fill: parent; mainText: drawer.open ? root.tr("Slide in") : root.tr("Slide out") }
        }
    }
    }
}
