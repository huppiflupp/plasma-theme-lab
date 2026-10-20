pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "launch.js" as Launch

// The Control Strip after Object Desktop on OS/2 Warp 4 (DESIGN.md §6), for
// a panel on the right edge, top to bottom: the workspaces in miniature
// (wallpaper and window outlines, the number bottom right, a red bar under
// the current one), a launch list, gauges for swap and every mounted file
// system, a seven-segment clock.
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.constraintHints: Plasmoid.CanFillArea

    readonly property var defaultLaunchers: [
        {label: "Files", icon: "system-file-manager", command: "@files"},
        {label: "Terminal", icon: "utilities-terminal", command: "@terminal"},
        {label: "Web", icon: "internet-web-browser", command: "@browser"},
        {label: "Text Editor", icon: "accessories-text-editor", command: "@editor"},
        {label: "System Settings", icon: "preferences-system", command: "@settings"},
        {label: "Desktop", icon: "user-desktop", command: "@files xdg:DESKTOP"}
    ]
    readonly property var launchers: Launch.parse(Plasmoid.configuration.launchers, defaultLaunchers)
    function tr(text, ...args) { return i18nd("warp-legacy", text, ...args); }
    property date now: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("Control Strip:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    function run(shell) { runner.connectSource(Launch.detached(shell)); }

    // ---- readings ----------------------------------------------------------
    // Swap and the mounted file systems, every ten seconds; one row per
    // device (btrfs mounts the same one at / and /home).
    property var swap: ({total: 0, used: 0})
    property var disks: []
    // The wallpaper of the desktop, for the workspace miniatures: a picture
    // path, or a package whose first image is taken. Until one is chosen
    // the desktop shows the global theme's, which only its defaults name.
    property string wallpaper: ""
    readonly property string gaugeQuery: "sh -c " + Launch.quote("LC_ALL=C free -b; echo ---; LC_ALL=C df -P -B1 -x tmpfs -x devtmpfs -x efivarfs -x overlay -x squashfs -x fuse.portal 2>/dev/null")
    readonly property string wallpaperQuery: "sh -c " + Launch.quote(
        "img=$(grep -m1 '^Image=' \"$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc\" | cut -d= -f2-); p=; "
        + "if [ -z \"$img\" ]; then lnf=$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage); "
        + "for d in \"$HOME/.local/share/plasma/look-and-feel\" /usr/share/plasma/look-and-feel; do "
        + "[ -f \"$d/$lnf/contents/defaults\" ] && img=$(kreadconfig6 --file \"$d/$lnf/contents/defaults\" --group Wallpaper --key Image) && break; done; fi; "
        + "case \"$img\" in file://*) p=${img#file://} ;; /*) p=$img ;; ?*) for d in \"$HOME/.local/share/wallpapers\" /usr/share/wallpapers; do "
        + "[ -d \"$d/$img/contents/images\" ] && p=$(ls -1 \"$d/$img/contents/images/\"* | head -1) && break; done ;; esac; "
        + "[ -d \"$p\" ] && p=$(ls -1 \"$p/contents/images/\"* 2>/dev/null | head -1); echo \"$p\"")
    P5Support.DataSource {
        engine: "executable"
        interval: 10000
        connectedSources: [root.gaugeQuery, root.wallpaperQuery]
        onNewData: function(sourceName, data) {
            if (sourceName === root.wallpaperQuery) root.wallpaper = String(data.stdout || "").trim();
            else root.readGauges(String(data.stdout || ""));
        }
    }
    function readGauges(text) {
        const parts = text.split("---");
        const swapLine = (parts[0] || "").split("\n").find(l => l.indexOf("Swap:") === 0);
        if (swapLine) {
            const f = swapLine.trim().split(/\s+/);
            swap = {total: Number(f[1]) || 0, used: Number(f[2]) || 0};
        }
        const seen = {};
        const list = [];
        (parts[1] || "").split("\n").slice(1).forEach(line => {
            const f = line.trim().split(/\s+/);
            if (f.length < 6 || seen[f[0]] || f[0].indexOf("/dev/") !== 0) return;
            seen[f[0]] = true;
            list.push({mount: f.slice(5).join(" "), total: Number(f[1]) || 0, free: Number(f[3]) || 0});
        });
        disks = list;
    }
    function size(bytes) {
        const units = ["B", "K", "M", "G", "T"];
        let i = 0, v = bytes;
        while (v >= 1000 && i < units.length - 1) { v /= 1024; i++; }
        return (v >= 100 || i === 0 ? Math.round(v) : v.toFixed(1)) + units[i];
    }
    // "/" is the root, "/run/media/me/Stick" the stick: the last part.
    function mountLabel(mount) { return mount === "/" ? "/" : mount.split("/").pop(); }

    // ---- workspaces --------------------------------------------------------
    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: windows
        activity: activities.currentActivity
        filterByActivity: true
        filterByVirtualDesktop: false
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }

    fullRepresentation: Item {
        id: strip
        readonly property int inner: width - 8
        Layout.minimumWidth: 110
        Layout.preferredWidth: 130
        Layout.fillHeight: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 3

            // Workspaces, the last at the top as in Object Desktop.
            Repeater {
                model: Plasmoid.configuration.showWorkspaces ? desktops.desktopIds.slice().reverse() : []
                ColumnLayout {
                    id: workspace
                    required property var modelData
                    required property int index
                    readonly property int number: desktops.desktopIds.length - index
                    readonly property bool current: String(modelData) === String(desktops.currentDesktop)
                    readonly property rect area: Plasmoid.containment.screenGeometry
                    readonly property real scale: strip.inner / Math.max(1, area.width)
                    spacing: 1
                    Bevel {
                        kind: "field"
                        Layout.preferredWidth: strip.inner
                        Layout.preferredHeight: Math.round(workspace.area.height * workspace.scale) + 4
                        color: Kirigami.Theme.backgroundColor
                        Image {
                            anchors.fill: parent; anchors.margins: 2
                            source: root.wallpaper ? "file://" + root.wallpaper : ""
                            sourceSize.width: strip.inner * 2
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }
                        Item {
                            anchors.fill: parent; anchors.margins: 2
                            clip: true
                            Repeater {
                                model: windows
                                Rectangle {
                                    id: outline
                                    required property var model
                                    readonly property rect frame: model.Geometry || Qt.rect(0, 0, 0, 0)
                                    readonly property var on: model.VirtualDesktops || []
                                    visible: !model.IsMinimized && frame.width > 0
                                             && (model.IsOnAllVirtualDesktops || on.map(String).indexOf(String(workspace.modelData)) >= 0)
                                    x: Math.round((frame.x - workspace.area.x) * workspace.scale)
                                    y: Math.round((frame.y - workspace.area.y) * workspace.scale)
                                    width: Math.max(4, Math.round(frame.width * workspace.scale))
                                    height: Math.max(4, Math.round(frame.height * workspace.scale))
                                    z: model.StackingOrder || 0
                                    color: Kirigami.Theme.backgroundColor
                                    border.width: 1
                                    border.color: model.IsActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.textColor
                                    Rectangle {
                                        width: parent.width; height: Math.min(3, parent.height)
                                        color: model.IsActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.disabledTextColor
                                    }
                                    Kirigami.Icon {
                                        anchors.centerIn: parent
                                        readonly property int side: Math.min(16, Math.min(parent.width, parent.height) - 4)
                                        visible: side >= 8
                                        width: side; height: side
                                        source: outline.model.decoration
                                    }
                                }
                            }
                        }
                        Text {
                            anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 3
                            text: workspace.number + "."
                            font.pixelSize: 11; font.bold: true
                            color: "white"; style: Text.Outline; styleColor: "black"
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: root.run(Launch.DBUS + " org.kde.KWin /KWin setCurrentDesktop " + workspace.number)
                        }
                    }
                    // Red under the current workspace, black under the others.
                    Bevel {
                        kind: "frame"
                        Layout.preferredWidth: strip.inner; Layout.preferredHeight: 7
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width - 30; height: 3
                            color: workspace.current ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                        }
                    }
                }
            }

            // The launch list.
            Repeater {
                model: root.launchers
                PadButton {
                    required property var modelData
                    Layout.preferredWidth: strip.inner; Layout.preferredHeight: 24
                    iconName: modelData.icon; iconSize: 18
                    text: root.tr(modelData.label)
                    tip: root.tr(modelData.label)
                    onClicked: if (modelData.command) root.run(Launch.resolve(modelData.command, root.tr))
                }
            }

            Item { Layout.fillHeight: true }

            // Gauges: label, then a sunken bar; swap fills red with what is
            // used, the drives grey with what is used, the free part teal.
            Repeater {
                model: Plasmoid.configuration.showGauges
                       ? [{label: root.tr("Swap: %1", root.size(root.swap.used)), part: root.swap.total ? root.swap.used / root.swap.total : 0, swap: true,
                           tip: root.tr("Swap: %1 of %2 in use", root.size(root.swap.used), root.size(root.swap.total))}]
                         .concat(root.disks.map(d => ({label: root.mountLabel(d.mount) + " " + root.size(d.free), part: d.total ? 1 - d.free / d.total : 0, swap: false,
                                                     tip: root.tr("%1: %2 free of %3", d.mount, root.size(d.free), root.size(d.total))})))
                       : []
                Bevel {
                    id: gauge
                    required property var modelData
                    kind: "frame"
                    Layout.preferredWidth: strip.inner; Layout.preferredHeight: 20
                    PlasmaCore.ToolTipArea { anchors.fill: parent; mainText: gauge.modelData.tip }
                    Text {
                        x: 4; width: parent.width * 0.52 - 4
                        anchors.verticalCenter: parent.verticalCenter
                        text: gauge.modelData.label
                        elide: Text.ElideRight
                        font.pixelSize: 10
                        color: Kirigami.Theme.textColor
                    }
                    Bevel {
                        kind: "field"
                        x: parent.width * 0.52; width: parent.width - x - 4
                        height: 12; anchors.verticalCenter: parent.verticalCenter
                        color: gauge.modelData.swap ? "#008080" : "#008080"
                        Rectangle {
                            x: 2; y: 2; height: parent.height - 4
                            width: Math.round((parent.width - 4) * Math.max(0, Math.min(1, gauge.modelData.part)))
                            color: gauge.modelData.swap ? "#e00000" : "#909090"
                        }
                    }
                }
            }

            // The clock: cyan segments on black, as Object Desktop's.
            Bevel {
                visible: Plasmoid.configuration.showClock
                kind: "field"
                Layout.preferredWidth: strip.inner; Layout.preferredHeight: 30
                color: "black"
                Row {
                    anchors.centerIn: parent
                    spacing: 2
                    readonly property color lit: "#30e0e0"
                    // Unlit segments a faint shadow of the lit ones.
                    readonly property color unlit: "#0a5050"
                    SegmentDigits { text: Qt.formatTime(root.now, "hh"); digitHeight: 22; weight: 0.1; aspect: 0.62; accent: parent.lit; ink: parent.unlit }
                    Column { spacing: 6; anchors.verticalCenter: parent.verticalCenter
                        Rectangle { width: 2; height: 2; color: parent.parent.lit }
                        Rectangle { width: 2; height: 2; color: parent.parent.lit } }
                    SegmentDigits { text: Qt.formatTime(root.now, "mm"); digitHeight: 22; weight: 0.1; aspect: 0.62; accent: parent.lit; ink: parent.unlit }
                    Column { spacing: 6; anchors.verticalCenter: parent.verticalCenter
                        Rectangle { width: 2; height: 2; color: parent.parent.lit }
                        Rectangle { width: 2; height: 2; color: parent.parent.lit } }
                    SegmentDigits { text: Qt.formatTime(root.now, "ss"); digitHeight: 22; weight: 0.1; aspect: 0.62; accent: parent.lit; ink: parent.unlit }
                }
                PlasmaCore.ToolTipArea { anchors.fill: parent; mainText: Qt.formatDate(root.now, Qt.locale().dateFormat(Locale.LongFormat)) }
            }
        }
    }
}
