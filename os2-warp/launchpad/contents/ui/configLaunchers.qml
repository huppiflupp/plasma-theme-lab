pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import "launch.js" as Launch

// Settings page. Plasma hands every page every setting's default, declared
// here so it takes them quietly; the settings themselves only where shown:
// Plasma saves every cfg_ property a page has, and an unshown one would
// write back a stale value (found in CDE Copper, ConfigPage.qml).
KCM.SimpleKCM {
    id: page
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
    property var cfg_thisWorkspaceDefault
    property string cfg_launchers
    property bool cfg_textButtons
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        CheckBox { text: i18nd("warp-legacy", "Lock, Find, Shut down and Window list beside the launchers"); checked: page.cfg_textButtons; onToggled: page.cfg_textButtons = checked }
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: i18nd("warp-legacy", "Launchers and their drawers") }
        LauncherEditor {
            Layout.fillWidth: true
            drawers: true
            entries: Launch.parse(page.cfg_launchers)
            onEdited: list => page.cfg_launchers = Launch.serialize(list)
        }
        Button { text: i18nd("warp-legacy", "Restore the default launchers"); icon.name: "edit-undo"; onClicked: page.cfg_launchers = "" }
    }
}
