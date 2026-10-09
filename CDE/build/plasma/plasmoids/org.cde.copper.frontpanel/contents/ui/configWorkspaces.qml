pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ConfigPage {
    id: page
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
            // The list wider than the field: a greyed entry carries its reason.
            popup.width: Math.max(width, Kirigami.Units.gridUnit * 32)
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
            // The switcher's own views need the switcher: offered only with it.
            delegate: ItemDelegate {
                required property int index
                required property string modelData
                width: ListView.view ? ListView.view.width : windowView.width
                enabled: index < 3 || showWorkspaces.checked
                text: enabled ? modelData : i18nd("cde-copper", "%1 – needs the workspace switcher", modelData)
                highlighted: windowView.highlightedIndex === index
            }
            onActivated: index => {
                // A workspace view keeps the strip or tile chosen before, for
                // when the switcher is hidden.
                if (values[index][1] === "none") cfg_windowDisplay = values[index][0];
                cfg_workspaceWindows = values[index][1];
            }
        }
        CheckBox {
            id: groupWindows
            // Only the strip groups; the other views show every window.
            enabled: windowView.currentIndex === 0
            text: i18nd("cde-copper", "Group windows of one application (\"3× Konsole\")")
        }
        CheckBox {
            id: thisScreen
            text: i18nd("cde-copper", "Only windows on this console's screen")
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
