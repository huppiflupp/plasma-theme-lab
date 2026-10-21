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
    // Without a background the panel's input mask is not redrawn when the
    // panel changes length (Panel.qml takes it from an empty FrameSvgItem):
    // after sliding out, only the narrow strip of the slid-in drawer took
    // clicks (VM, 21.10.2026). Setting the hints once more, through a
    // background, draws the mask anew at the panel's present size.
    function refreshMask() {
        if (!alone) return;
        Plasmoid.containment.backgroundHints = PlasmaCore.Types.DefaultBackground;
        Plasmoid.containment.backgroundHints = PlasmaCore.Types.NoBackground;
    }
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
        Timer { id: slideDone; interval: 260; onTriggered: { root.sliding = false; remask.restart(); } }
        // once the panel has its new length
        Timer { id: remask; interval: 150; onTriggered: root.refreshMask() }

    Item {
        id: strip
        x: -drawer.edgeLeft
        width: drawer.width + drawer.edgeLeft + drawer.edgeRight
        height: parent.height
        clip: true

        // No outer frame (the user's wish): the page's frame and the tabs
        // carry the shape.
        Bevel {
            id: pad
            kind: "none"
            width: drawer.padWidth
            height: parent.height
            x: drawer.open ? 0 : -width
            Behavior on x { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

            ColumnLayout {
                id: column
                anchors.fill: parent; anchors.margins: 2
                spacing: 0

                // No title bar of its own (the user's wish): the tabs say
                // what it is, and the drawer is lower without it.
                // The notebook tabs: the current one higher, bold, joined to the
                // page below (no line under it). More tabs than room: arrows at
                // the right turn them as on an OS/2 notebook, and so does the
                // wheel; the last one was simply cut off before.
                Item {
                    id: tabStrip
                    Layout.fillWidth: true; Layout.preferredHeight: 26; Layout.topMargin: 2
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

        // The tab, as on Mac OS 9's Control Strip: flat where it joins the
        // drawer, rounded at its free end, a solid arrow. Neon edges in the
        // strip's light run, classic in OS/2's white and grey.
        Canvas {
            id: tabHandle
            x: pad.x + pad.width
            width: drawer.handle
            height: parent.height
            readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
            readonly property bool hot: tabMouse.containsMouse
            readonly property bool open: drawer.open
            onHotChanged: requestPaint()
            onOpenChanged: requestPaint()
            onNeonChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                // top and bottom on the lines of the tab row and the page
                const w = width - 1.5, top = 10.5, bottom = height - 6.5, r = Math.min(9, w - 2);
                const shape = () => {
                    ctx.beginPath();
                    ctx.moveTo(0, top);
                    ctx.lineTo(w - r, top);
                    ctx.arcTo(w, top, w, top + r, r);
                    ctx.lineTo(w, bottom - r);
                    ctx.arcTo(w, bottom, w - r, bottom, r);
                    ctx.lineTo(0, bottom);
                };
                shape();
                ctx.closePath();
                const fill = ctx.createLinearGradient(0, top, 0, bottom);
                if (neon) {
                    fill.addColorStop(0, hot ? "#1c3478" : "#14275e");
                    fill.addColorStop(1, hot ? "#101c4a" : "#0a1438");
                } else {
                    fill.addColorStop(0, hot ? "#e4e4e4" : "#d8d8d8");
                    fill.addColorStop(1, "#b8b8b8");
                }
                ctx.fillStyle = fill;
                ctx.fill();
                // the edge, open towards the drawer
                shape();
                ctx.lineWidth = 1;
                if (neon) {
                    const edge = ctx.createLinearGradient(0, top, 0, bottom);
                    edge.addColorStop(0, "#48cffe");
                    edge.addColorStop(0.55, Kirigami.Theme.hoverColor.toString());
                    edge.addColorStop(1, "#ff4fd8");
                    ctx.strokeStyle = edge;
                } else {
                    ctx.strokeStyle = "#404040";
                }
                ctx.stroke();
                // the arrow: pointing where the drawer will go
                const cx = w / 2, cy = (top + bottom) / 2, s = 5;
                ctx.beginPath();
                if (open) { ctx.moveTo(cx + s * 0.6, cy - s); ctx.lineTo(cx - s * 0.8, cy); ctx.lineTo(cx + s * 0.6, cy + s); }
                else { ctx.moveTo(cx - s * 0.6, cy - s); ctx.lineTo(cx + s * 0.8, cy); ctx.lineTo(cx - s * 0.6, cy + s); }
                ctx.closePath();
                ctx.fillStyle = neon ? (hot ? "#bff0ff" : "#48cffe") : (hot ? "#2400a8" : "#202020");
                ctx.fill();
            }
            MouseArea { id: tabMouse; anchors.fill: parent; hoverEnabled: true; onClicked: drawer.toggle() }
            PlasmaCore.ToolTipArea { anchors.fill: parent; mainText: drawer.open ? root.tr("Slide in") : root.tr("Slide out") }
        }
    }
    }
}
