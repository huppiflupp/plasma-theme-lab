pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasma5support as P5Support

// Warp Legacy's panels, each switched on and off at once (not on Apply):
// a switch adds the panel where layout.js puts it, or removes every panel
// that holds the widget. The state is read back from Plasma itself, so it
// stays right whatever was changed elsewhere (Edit Mode, another panel's
// settings). Shared by the settings of all four plasmoids.
KCM.SimpleKCM {
    id: page
    // Plasma hands every page every setting's default; this page shows no
    // setting, so it declares none of the settings themselves (see the
    // other pages).
    property var cfg_launchersDefault
    property var cfg_textButtonsDefault
    property var cfg_trayDefault
    property var cfg_mainDefault
    property var cfg_currentTabDefault
    property var cfg_showWorkspacesDefault
    property var cfg_showGaugesDefault
    property var cfg_showClockDefault
    property var cfg_layoutDefault
    property var cfg_mottoDefault
    property var cfg_collapsedDefault
    property var cfg_drawerWidthDefault
    property var cfg_compactTopDefault
    property var cfg_compactBottomDefault
    property var cfg_sayingMinutesDefault
    property var cfg_clockOpensAppDefault
    property var cfg_calendarCommandDefault
    property var cfg_enabledCalendarPluginsDefault
    property var cfg_weatherServerDefault
    property var cfg_weatherPlaceDefault
    property var cfg_newsUrlDefault
    property var cfg_fetchMinutesDefault
    property var cfg_thisWorkspaceDefault
    property var cfg_startLabelDefault

    readonly property var panels: [
        {plugin: "org.warplegacy.warpbar", name: i18nd("warp-legacy", "Warp Bar"), where: i18nd("warp-legacy", "along the top: desktop menu, window list, tray, clock"),
         script: "var p = new Panel; p.location = 'top'; p.height = 28; p.hiding = 'none'; p.floating = false; "
               + "p.addWidget('org.warplegacy.warpbar'); p.addWidget('org.kde.plasma.panelspacer'); "
               + "p.addWidget('org.kde.plasma.systemtray'); p.addWidget('org.kde.plasma.digitalclock');"},
        {plugin: "org.warplegacy.launchpad", name: i18nd("warp-legacy", "LaunchPad"), where: i18nd("warp-legacy", "floating at the bottom centre: lock, find, shut down, launchers with drawers"),
         script: "var p = new Panel; p.location = 'bottom'; p.alignment = 'center'; p.lengthMode = 'fit'; p.height = 76; "
               + "p.hiding = 'windowsgobelow'; p.floating = true; p.addWidget('org.warplegacy.launchpad');"},
        {plugin: "org.warplegacy.controlstrip", name: i18nd("warp-legacy", "Control Strip"), where: i18nd("warp-legacy", "on the right edge: workspaces, launch list, gauges, clock"),
         script: "var p = new Panel; p.location = 'right'; p.height = 130; p.hiding = 'none'; p.floating = false; "
               + "p.addWidget('org.warplegacy.controlstrip');"},
        {plugin: "org.warplegacy.taskbar", name: i18nd("warp-legacy", "Warp Taskbar"), where: i18nd("warp-legacy", "along the bottom, instead of the Warp Bar: Start, workspaces, windows, tray, clock"),
         script: "var p = new Panel; p.location = 'bottom'; p.height = 44; p.hiding = 'none'; p.floating = false; "
               + "p.addWidget('org.warplegacy.taskbar'); p.addWidget('org.kde.plasma.systemtray'); p.addWidget('org.kde.plasma.digitalclock');"},
        // A drawer at the bottom left, as Mac OS 9's Control Strip: its tab
        // slides it out of the screen and back. A panel of its own, above
        // the windows without taking room from them ("windowsgobelow"), its
        // length "custom" from 10 px so the panel shrinks to the tab (see
        // tablauncher main.qml). With a full-length panel at the bottom
        // (Warp Taskbar) it goes to the top left instead, as panels on one
        // edge overlap. Not on the desktop: there it lay under the windows,
        // and its widget kept its full size when closed, a blind patch over
        // the desktop; not at the left edge: Plasma drew a panel down the
        // whole edge behind it and moved the desktop icons aside.
        {plugin: "org.warplegacy.tablauncher", name: i18nd("warp-legacy", "Tab Launcher"), where: i18nd("warp-legacy", "a drawer at the bottom left that slides in and out: windows, favourites, menu categories on tabs"),
         script: "var taken = panels().some(function(o) { return o.location == 'bottom' && o.lengthMode == 'fill'; }); "
               + "var p = new Panel; p.location = taken ? 'top' : 'bottom'; p.alignment = 'left'; p.height = 94; "
               + "p.hiding = 'windowsgobelow'; p.floating = false; p.lengthMode = 'custom'; p.minimumLength = 10; "
               + "p.maximumLength = screenGeometry(p.screen).width; p.addWidget('org.warplegacy.tablauncher');"}
    ]
    property var present: []
    property bool known: false

    function quote(s) { return "'" + String(s).replace(/\x27/g, "'\\''") + "'"; }
    // Plasma's desktop scripting over D-Bus; its print() comes back as the
    // reply's string (dbus-send, as the VM has no qdbus6).
    function evaluate(script) {
        return "dbus-send --session --print-reply --type=method_call --dest=org.kde.plasmashell /PlasmaShell "
            + "org.kde.PlasmaShell.evaluateScript string:" + quote(script);
    }
    readonly property string query: evaluate("var t = []; panels().concat(desktops()).forEach(function(p) { p.widgets().forEach(function(w) { t.push(w.type); }); }); print(t.join(','));")
    P5Support.DataSource {
        id: shell
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source);
            if (source === page.query) {
                const m = /string "([^"]*)"/.exec(data.stdout || "");
                page.present = m ? m[1].split(",") : [];
                page.known = m !== null;
            } else {
                Qt.callLater(page.refresh);
            }
        }
    }
    function refresh() { shell.connectSource(query); }
    function toggle(panel, on) {
        const script = on ? panel.script
            : "panels().forEach(function(p) { if (p.widgets().some(function(w) { return w.type == '" + panel.plugin + "'; })) p.remove(); });"
              + " desktops().forEach(function(d) { d.widgets().forEach(function(w) { if (w.type == '" + panel.plugin + "') w.remove(); }); });";
        shell.connectSource(evaluate(script));
    }
    Component.onCompleted: refresh()

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Label {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            text: i18nd("warp-legacy", "Each panel can be shown or left out on its own. The change takes effect at once.")
        }
        Repeater {
            model: page.panels
            RowLayout {
                id: line
                required property var modelData
                readonly property bool on: page.present.indexOf(modelData.plugin) >= 0
                spacing: Kirigami.Units.largeSpacing
                Switch {
                    checked: line.on
                    enabled: page.known
                    onToggled: page.toggle(line.modelData, checked)
                }
                ColumnLayout {
                    spacing: 0
                    Label { text: line.modelData.name; font.bold: true }
                    Label { text: line.modelData.where; opacity: 0.75; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
            }
        }
        Label {
            visible: !page.known
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Kirigami.Theme.neutralTextColor
            text: i18nd("warp-legacy", "Plasma could not be asked which panels exist.")
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            opacity: 0.75
            text: i18nd("warp-legacy", "Removing the panel whose settings are open closes this window. The whole layout again: System Settings › Global Theme, with “Use desktop layout from theme”.")
        }
    }
}
