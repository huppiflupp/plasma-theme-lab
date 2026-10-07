pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: page
    // Plasma hands every settings page every setting's default; declared so
    // it takes them quietly (see configGeneral.qml).
    property var cfg_visibilityModeDefault
    property var cfg_topEdgeDefault
    property var cfg_edgeDefault
    property var cfg_windowsOnThisScreenDefault
    property var cfg_showWorkspacesDefault
    property var cfg_workspaceCountDefault
    property var cfg_workspaceButtonWidthDefault
    property var cfg_workspaceLabelsDefault
    property var cfg_workspaceColoursDefault
    property var cfg_groupWindowsDefault
    property var cfg_windowDisplayDefault
    property var cfg_consoleLabelDefault
    property var cfg_consoleScaleDefault
    property var cfg_hideTrayVolumeDefault
    property var cfg_hideTrayIconsDefault
    property var cfg_trayHiddenByConsoleDefault
    property var cfg_panelFrameDefault
    property var cfg_hardContrastDefault
    property var cfg_floatingDefault
    property var cfg_everyScreenDefault
    property var cfg_styleRequestDefault
    property var cfg_launcherLabelsDefault
    property var cfg_leftLaunchersDefault
    property var cfg_rightLaunchersDefault
    property var cfg_clockOpensAppDefault
    property var cfg_clockStyleDefault
    property var cfg_clockDialDefault
    property var cfg_clockSecondsDefault
    property var cfg_clockSegmentEdgeDefault
    property var cfg_clockSegmentShadowDefault
    property var cfg_calendarCommandDefault
    property var cfg_enabledCalendarPluginsDefault
    property alias cfg_showWorkspaces: showWorkspaces.checked
    property alias cfg_workspaceCount: workspaceCount.value
    property alias cfg_workspaceButtonWidth: buttonWidth.value
    property alias cfg_workspaceColours: workspaceColours.checked
    // One label per workspace; an empty one shows the number.
    property var cfg_workspaceLabels: []
    function setLabel(index, text) {
        const list = (cfg_workspaceLabels || []).slice();
        while (list.length < 8) list.push("");
        list[index] = text;
        cfg_workspaceLabels = list;
    }
    Kirigami.FormLayout {
        CheckBox {
            id: showWorkspaces
            Kirigami.FormData.label: i18nd("cde-copper", "Switcher:")
            text: i18nd("cde-copper", "Show the workspace switcher")
        }
        SpinBox {
            id: workspaceCount
            Kirigami.FormData.label: i18nd("cde-copper", "Number of workspaces:")
            from: 1; to: 8
            enabled: showWorkspaces.checked
        }
        SpinBox {
            id: buttonWidth
            Kirigami.FormData.label: i18nd("cde-copper", "Button width:")
            from: 40; to: 200; stepSize: 5
            enabled: showWorkspaces.checked
        }
        CheckBox {
            id: workspaceColours
            text: i18nd("cde-copper", "Each button in a colour of its own, as in CDE")
            enabled: showWorkspaces.checked
        }
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Labels (empty: the number)") }
        Repeater {
            model: workspaceCount.value
            delegate: TextField {
                required property int index
                Kirigami.FormData.label: i18nd("cde-copper", "Workspace %1:", index + 1)
                enabled: showWorkspaces.checked
                placeholderText: String(index + 1)
                text: (page.cfg_workspaceLabels || [])[index] || ""
                onTextEdited: page.setLabel(index, text)
            }
        }
    }
}
