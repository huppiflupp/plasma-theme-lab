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
    property string cfg_tray
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Heading { level: 3; text: i18nd("warp-legacy", "Launchers in the tray") }
        LauncherEditor {
            Layout.fillWidth: true
            entries: Launch.parse(page.cfg_tray, Launch.TRAY)
            onEdited: list => page.cfg_tray = Launch.serialize(list)
        }
        Button { text: i18nd("warp-legacy", "Restore the default launchers"); icon.name: "edit-undo"; onClicked: page.cfg_tray = "" }
    }
}
