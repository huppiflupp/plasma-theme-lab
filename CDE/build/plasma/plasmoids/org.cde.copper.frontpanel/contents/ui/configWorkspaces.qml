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
    property var cfg_workspaceWindowsDefault
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
    property string cfg_workspaceWindows: "none"
    property string cfg_windowDisplay: "strip"
    property alias cfg_groupWindows: groupWindows.checked
    property alias cfg_windowsOnThisScreen: thisScreen.checked
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
        // All ways of showing the open windows in one list; two settings
        // behind it: the strip or tile (windowDisplay), and the switcher's own
        // views (workspaceWindows), which need the switcher.
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Open windows") }
        ComboBox {
            id: windowView
            Kirigami.FormData.label: i18nd("cde-copper", "Shown as:")
            Layout.preferredWidth: Kirigami.Units.gridUnit * 20
            readonly property var values: [["strip", "none"], ["tileLeft", "none"], ["tileRight", "none"],
                                           ["strip", "icons"], ["strip", "pager"]]
            model: [i18nd("cde-copper", "Strip under the tiles"),
                    i18nd("cde-copper", "Window tile left, beside the launchers"),
                    i18nd("cde-copper", "Window tile right, beside the launchers"),
                    i18nd("cde-copper", "Icons under each workspace button"),
                    i18nd("cde-copper", "Each workspace in miniature, with its windows")]
            currentIndex: {
                if (cfg_workspaceWindows === "icons") return 3;
                if (cfg_workspaceWindows === "pager") return 4;
                return Math.max(0, ["strip", "tileLeft", "tileRight"].indexOf(cfg_windowDisplay));
            }
            onActivated: index => {
                // A workspace view keeps the strip or tile chosen before, for
                // when the switcher is hidden.
                if (values[index][1] === "none") cfg_windowDisplay = values[index][0];
                cfg_workspaceWindows = values[index][1];
            }
        }
        Label {
            visible: windowView.currentIndex >= 3 && !showWorkspaces.checked
            Layout.maximumWidth: Kirigami.Units.gridUnit * 22
            wrapMode: Text.WordWrap
            font: Kirigami.Theme.smallFont
            text: i18nd("cde-copper", "Needs the workspace switcher; while it is hidden the console shows the strip (or the tile chosen before).")
        }
        CheckBox {
            id: groupWindows
            // Only the strip groups; the other views show every window.
            enabled: windowView.currentIndex === 0
            text: i18nd("cde-copper", "Group windows of one application (\"3× Konsole\")")
        }
        CheckBox {
            id: thisScreen
            text: i18nd("cde-copper", "Only windows on this console's screen (with a console on every screen)")
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
