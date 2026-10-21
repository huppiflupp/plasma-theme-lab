import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kcmutils as KCM

// Settings page; only the settings shown are declared as cfg_ (see the
// other pages), the defaults of all quietly.
KCM.SimpleKCM {
    id: page
    property bool cfg_showWorkspaces
    property bool cfg_thisWorkspace
    property string cfg_startLabel
    property var cfg_startLabelDefault
    property var cfg_showWorkspacesDefault
    property var cfg_thisWorkspaceDefault
    property var cfg_launchersDefault
    property var cfg_textButtonsDefault
    property var cfg_trayDefault
    property var cfg_mainDefault
    property var cfg_currentTabDefault
    property var cfg_showGaugesDefault
    property var cfg_showClockDefault
    property var cfg_layoutDefault
    property var cfg_mottoDefault
    property var cfg_collapsedDefault
    property var cfg_drawerWidthDefault
    ColumnLayout {
        RowLayout {
            Label { text: i18nd("warp-legacy", "Start button:") }
            RadioButton { text: i18nd("warp-legacy", "Start"); checked: page.cfg_startLabel !== "warp"; onToggled: if (checked) page.cfg_startLabel = "start" }
            RadioButton { text: "Warp"; checked: page.cfg_startLabel === "warp"; onToggled: if (checked) page.cfg_startLabel = "warp" }
        }
        CheckBox { text: i18nd("warp-legacy", "Workspace buttons"); checked: page.cfg_showWorkspaces; onToggled: page.cfg_showWorkspaces = checked }
        CheckBox { text: i18nd("warp-legacy", "Only the windows of the current workspace"); checked: page.cfg_thisWorkspace; onToggled: page.cfg_thisWorkspace = checked }
    }
}
