pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import "motif.js" as Motif
import "palettes.js" as Palettes

// The style manager, after CDE's dtstyle: a row of large buttons, each
// opening the dialog of one part of the desktop's style. Shown as a window
// of its own by plasmawindowed (the console's System › Style Manager…).
// Every change runs the theme's tool (manage.py palette …), which switches
// colour scheme, Plasma surfaces, Kvantum controls, icons, GTK theme and
// desktop together; afterwards the open programs that still show the old
// style are named (code/stale.py).
PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation

    readonly property string dataDir: decodeURIComponent(StandardPaths.writableLocation(StandardPaths.GenericDataLocation).toString().replace(/^file:\/\//, ""))
    readonly property string tool: dataDir + "/cde-copper/tool/manage.py"
    readonly property string manifest: dataDir + "/cde-copper-install/manifest.json"
    readonly property string helper: decodeURIComponent(Qt.resolvedUrl("../code/stale.py").toString().replace(/^file:\/\//, ""))
    // The KDE Store edition has no manage.py; there is nothing to apply.
    property bool hasTool: true
    // The installation's choices (manifest.json: palette, backdrop, cursor…).
    property var installed: ({})
    property string current: ""          // the palette in use
    readonly property color desktopColour: {
        const palette = Palettes.PALETTES.find(p => p.name === (current || "Copper"));
        return palette ? palette.colours[5] : colours.window;
    }
    property bool busy: false
    property string status: ""
    property bool failed: false
    // After a change to the programs' style: the open programs by kind.
    property var restart: []
    property var own: []
    property bool checked: false

    Item { id: windowSet; Kirigami.Theme.colorSet: Kirigami.Theme.Window; Kirigami.Theme.inherit: false }
    Item { id: viewSet; Kirigami.Theme.colorSet: Kirigami.Theme.View; Kirigami.Theme.inherit: false }
    QtObject {
        id: colourSet
        readonly property color window: windowSet.Kirigami.Theme.backgroundColor
        readonly property color windowText: windowSet.Kirigami.Theme.textColor
        readonly property color field: viewSet.Kirigami.Theme.backgroundColor
        readonly property color fieldText: viewSet.Kirigami.Theme.textColor
        readonly property color highlight: windowSet.Kirigami.Theme.highlightColor
        readonly property color highlightText: windowSet.Kirigami.Theme.highlightedTextColor
        readonly property var shade: Motif.shades(window)
        readonly property string font: Kirigami.Theme.defaultFont.family
    }
    readonly property alias colours: colourSet

    function quote(s) {
        return "'" + String(s).replace(/\x27/g, "'\\''") + "'";
    }
    function load() {
        reader.connectSource("test -f " + quote(tool) + " && echo yes || echo no");
        reader.connectSource("kreadconfig6 --group General --key ColorScheme");
        reader.connectSource("cat " + quote(manifest));
    }
    Component.onCompleted: load()

    P5Support.DataSource {
        id: reader
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            if (source.indexOf("test -f") === 0) {
                root.hasTool = data.stdout.trim() === "yes";
            } else if (source.indexOf("kreadconfig6") === 0) {
                const scheme = data.stdout.trim();
                root.current = scheme.indexOf("CDE") === 0 ? scheme.substring(3) : "";
            } else {
                try { root.installed = JSON.parse(data.stdout) || {}; } catch (e) { root.installed = {}; }
            }
        }
    }
    // The palette in use may change meanwhile (System Settings, the night
    // theme): look again now and then.
    Timer {
        interval: 3000; repeat: true; running: !root.busy
        onTriggered: reader.connectSource("kreadconfig6 --group General --key ColorScheme")
    }

    // One change at a time. The tool runs as a unit of its own, so closing
    // the window does not cut a palette switch short; its output goes to a
    // log, of which the last lines are shown when it fails.
    property bool programs: false
    function apply(args, what, programs) {
        if (busy || !hasTool) return;
        busy = true; failed = false; checked = false;
        restart = []; own = [];
        root.programs = programs;
        status = i18nd("cde-copper", "Applying: %1…", what);
        pendingWhat = what;
        const log = "\"${XDG_RUNTIME_DIR:-/tmp}/cde-copper-style.log\"";
        const script = "python3 " + quote(tool) + " palette " + args + " > " + log + " 2>&1";
        // systemd-run expands $ itself: doubled, the shell gets it.
        worker.connectSource("systemd-run --user --wait --collect --quiet -p KillMode=process -- sh -c "
                             + quote(script.replace(/\$/g, "$$$$")) + "; echo \"exit=$?\"; tail -n 4 " + log);
    }
    property string pendingWhat: ""
    P5Support.DataSource {
        id: worker
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            root.busy = false;
            const out = data.stdout || "";
            const ok = /^exit=0$/m.test(out);
            root.failed = !ok;
            root.status = ok ? i18nd("cde-copper", "Applied: %1.", root.pendingWhat)
                             : i18nd("cde-copper", "Could not apply %1: %2", root.pendingWhat,
                                     out.replace(/^exit=\d+\n?/m, "").trim() || data.stderr || "?");
            root.load();
            if (ok && root.programs) root.checkPrograms();
        }
    }

    // The open windows' programs, and which of them need a restart.
    TaskManager.TasksModel {
        id: tasks
        groupMode: TaskManager.TasksModel.GroupDisabled
        filterByVirtualDesktop: false; filterByScreen: false; filterByActivity: false
    }
    Instantiator {
        id: windows
        model: tasks
        delegate: QtObject {
            required property var model
            readonly property var info: ({pid: model.AppPid, name: model.AppName || model.display, icon: model.decoration, id: model.AppId || ""})
        }
    }
    property var candidates: ({})
    function checkPrograms() {
        const found = {};
        for (let i = 0; i < windows.count; i++) {
            const info = windows.objectAt(i).info;
            // Not this window (plasmawindowed): it follows the colours itself.
            if (!info.pid || info.id.indexOf("plasmawindowed") >= 0) continue;
            found[info.pid] = info;
        }
        candidates = found;
        const pids = Object.keys(found);
        if (pids.length === 0) { checked = true; return; }
        checker.connectSource("python3 " + quote(helper) + " " + pids.join(" "));
    }
    P5Support.DataSource {
        id: checker
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            let kinds = {};
            try { kinds = JSON.parse(data.stdout); } catch (e) {}
            const seen = {}, restart = [], own = [];
            for (const pid in kinds) {
                const info = root.candidates[pid];
                if (!info || seen[info.name]) continue;
                seen[info.name] = true;
                if (kinds[pid] === "restart") restart.push(info);
                else if (kinds[pid] === "own") own.push(info);
            }
            root.restart = restart; root.own = own;
            root.checked = true;
        }
    }

    readonly property var parts: [
        {key: "palette", text: i18nd("cde-copper", "Palette"), icon: "preferences-desktop-color", dialog: paletteDialog},
        {key: "backdrop", text: i18nd("cde-copper", "Backdrop"), icon: "preferences-desktop-wallpaper", dialog: backdropDialog},
        {key: "window", text: i18nd("cde-copper", "Window"), icon: "preferences-desktop-theme-windowdecorations", dialog: windowDialog},
        {key: "pointer", text: i18nd("cde-copper", "Pointer"), icon: "preferences-desktop-cursors", dialog: pointerDialog},
        {key: "lock", text: i18ndc("cde-copper", "style manager part", "Lock Screen"), icon: "system-lock-screen", dialog: lockDialog},
        {key: "controls", text: i18nd("cde-copper", "Controls"), icon: "preferences-desktop-theme-applications", dialog: controlsDialog}]

    fullRepresentation: Rectangle {
        id: face
        color: colours.window
        Layout.minimumWidth: layout.implicitWidth + 20
        Layout.minimumHeight: layout.implicitHeight + 20
        // plasmawindowed opens at a fixed or remembered size; the window
        // takes the face's, its height fixed as dtstyle's is.
        function fit() {
            const window = face.Window.window;
            if (!window) return;
            const height = Math.max(face.Layout.minimumHeight, 100);
            window.minimumHeight = height; window.maximumHeight = height;
            window.width = Math.max(face.Layout.minimumWidth, 100);
            window.height = height;
        }
        Timer { id: fitter; interval: 50; onTriggered: face.fit() }
        Component.onCompleted: fitter.start()
        // plasmawindowed restores the size it saved after the face is made.
        onHeightChanged: if (Math.abs(height - Layout.minimumHeight) > 1) fitter.restart()
        Connections {
            target: layout
            function onImplicitHeightChanged() { fitter.restart(); }
        }

        ColumnLayout {
            id: layout
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.margins: 10
            spacing: 10
            RowLayout {
                spacing: 6
                Repeater {
                    model: root.parts
                    delegate: IconButton {
                        required property var modelData
                        colours: root.colours
                        text: modelData.text
                        iconName: modelData.icon
                        selected: modelData.dialog.visible
                        enabled: root.hasTool
                        onClicked: modelData.dialog.open()
                    }
                }
            }
            Bevel {
                // The state: the palette in use, a change under way, and the
                // programs that keep the old style until restarted.
                Layout.fillWidth: true
                Layout.preferredHeight: report.implicitHeight + 16
                sunken: true
                surface: colours.field
                ColumnLayout {
                    id: report
                    x: 8; y: 8; width: parent.width - 16
                    spacing: 4
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        color: colours.fieldText
                        font.family: colours.font; font.pixelSize: 12
                        text: !root.hasTool
                            ? i18nd("cde-copper", "This edition of CDE Copper comes from the KDE Store and cannot recolour the theme: choose a colour scheme in System Settings › Colours. The style manager with CDE's 37 palettes, backdrops and the Motif controls is part of the full installation from the project page.")
                            : root.status || i18nd("cde-copper", "Palette in use: %1", root.current || i18nd("cde-copper", "none of CDE's"))
                        font.weight: root.failed ? Font.DemiBold : Font.Normal
                    }
                    BusyIndicator { visible: root.busy; running: root.busy; Layout.preferredHeight: 28; Layout.preferredWidth: 28 }
                    Text {
                        Layout.fillWidth: true
                        visible: root.checked
                        wrapMode: Text.Wrap
                        color: colours.fieldText
                        font.family: colours.font; font.pixelSize: 12
                        text: root.restart.length
                            ? i18nd("cde-copper", "These open programs keep the old style until they are restarted:")
                            : i18nd("cde-copper", "The open programs have taken the new style. Programs started from now on take it too.")
                    }
                    Flow {
                        Layout.fillWidth: true
                        visible: root.checked && root.restart.length > 0
                        spacing: 10
                        Repeater {
                            model: root.restart
                            delegate: Row {
                                id: program
                                required property var modelData
                                spacing: 4
                                Kirigami.Icon { source: program.modelData.icon; width: 22; height: 22 }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: program.modelData.name
                                    color: colours.fieldText
                                    font.family: colours.font; font.pixelSize: 12; font.weight: Font.DemiBold
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: root.checked && root.own.length > 0
                        wrapMode: Text.Wrap
                        color: colours.fieldText
                        font.family: colours.font; font.pixelSize: 12
                        text: i18nd("cde-copper", "Keep their own look (Flatpak, libadwaita): %1", root.own.map(p => p.name).join(", "))
                    }
                }
            }
        }
    }

    PaletteDialog { id: paletteDialog; manager: root }
    BackdropDialog { id: backdropDialog; manager: root }
    WindowDialog { id: windowDialog; manager: root }
    PointerDialog { id: pointerDialog; manager: root }
    LockDialog { id: lockDialog; manager: root }
    ControlsDialog { id: controlsDialog; manager: root }
}
