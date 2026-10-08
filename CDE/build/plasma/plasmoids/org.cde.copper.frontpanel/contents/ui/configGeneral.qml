import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: page
    // Plasma hands every settings page every setting's default; declared so
    // it takes them quietly. (Not the settings themselves: Plasma saves every
    // cfg_ property a page has, and an unshown one would write back a stale
    // value over what the console changed meanwhile.)
    property var cfg_visibilityModeDefault
    property var cfg_topEdgeDefault
    property var cfg_edgeDefault
    property var cfg_windowsOnThisScreenDefault
    property var cfg_workspaceColoursDefault
    property var cfg_showWorkspacesDefault
    property var cfg_workspaceCountDefault
    property var cfg_groupWindowsDefault
    property var cfg_windowDisplayDefault
    property var cfg_llmTileDefault
    property var cfg_llmHostsDefault
    property var cfg_smallButtonsDefault
    property var cfg_smallStyleDefault
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
    property var cfg_workspaceButtonWidthDefault
    property var cfg_workspaceLabelsDefault
    property alias cfg_visibilityMode: visibility.currentIndex
    property bool cfg_topEdge
    property int cfg_edge: -1
    property alias cfg_launcherLabels: launcherLabels.checked
    property alias cfg_consoleLabel: label.text
    property real cfg_consoleScale: 1.0
    property alias cfg_hideTrayVolume: hideVolume.checked
    property alias cfg_hideTrayIcons: hideIcons.checked
    property alias cfg_panelFrame: panelFrame.checked
    property alias cfg_hardContrast: hardContrast.checked
    property alias cfg_floating: floating.checked
    property alias cfg_everyScreen: everyScreen.checked
    // The session block's small buttons, kept in this order.
    property alias cfg_llmTile: llmTile.checked
    property alias cfg_llmHosts: llmHosts.text
    property var cfg_smallButtons: []
    property string cfg_smallStyle: "family"
    readonly property var smallStyles: [
        {value: "family", text: i18nd("cde-copper", "All alike, the meters among the keys")},
        {value: "instruments", text: i18nd("cde-copper", "Meters sunken, in the clock's colours")},
        {value: "led", text: i18nd("cde-copper", "Meters as an LED field over the keys")},
        {value: "panel", text: i18nd("cde-copper", "Meters as a panel of bars beside the keys")}]
    readonly property var smallChoices: [
        {kind: "configure", text: i18nd("cde-copper", "Console settings")},
        {kind: "lock", text: i18nd("cde-copper", "Lock screen")},
        {kind: "desktop", text: i18nd("cde-copper", "Show desktop")},
        {kind: "load", text: i18nd("cde-copper", "Load meter (processor and memory)")},
        {kind: "llm", text: i18nd("cde-copper", "LLM cluster (tokens per second)")},
        {kind: "volume", text: i18nd("cde-copper", "Volume (otherwise in the strip's row)")},
        {kind: "network", text: i18nd("cde-copper", "Network (WLAN or cable)")},
        {kind: "logout", text: i18nd("cde-copper", "Leave session")}]
    function setSmall(kind, on) {
        const chosen = smallChoices.map(c => c.kind)
            .filter(k => k === kind ? on : (cfg_smallButtons || []).indexOf(k) >= 0);
        cfg_smallButtons = chosen.length ? chosen : ["configure"];
    }
    Kirigami.FormLayout {
        ComboBox {
            id: visibility
            Kirigami.FormData.label: i18nd("cde-copper", "Visibility:")
            model: [i18nd("cde-copper", "Always visible"), i18nd("cde-copper", "Auto-hide / edge reveal"), i18nd("cde-copper", "Dodge windows")]
        }
        ComboBox {
            Kirigami.FormData.label: i18nd("cde-copper", "Screen edge:")
            model: [i18nd("cde-copper", "Bottom"), i18nd("cde-copper", "Top"), i18nd("cde-copper", "Left"), i18nd("cde-copper", "Right")]
            currentIndex: cfg_edge >= 0 ? cfg_edge : (cfg_topEdge ? 1 : 0)
            onActivated: index => { cfg_edge = index; cfg_topEdge = index === 1; }
        }
        CheckBox {
            id: floating
            text: i18nd("cde-copper", "Floating, a gap from the screen edge (off: on the edge)")
        }
        CheckBox {
            id: everyScreen
            Kirigami.FormData.label: i18nd("cde-copper", "Screens:")
            text: i18nd("cde-copper", "A console on every screen (off: one console for all)")
        }
        CheckBox {
            id: launcherLabels
            Kirigami.FormData.label: i18nd("cde-copper", "Launchers:")
            text: i18nd("cde-copper", "Labels under the icons (off: larger icons, names as tooltips)")
        }
        Repeater {
            model: page.smallChoices
            delegate: CheckBox {
                required property int index
                required property var modelData
                Kirigami.FormData.label: index === 0 ? i18nd("cde-copper", "Small buttons:") : ""
                text: modelData.text
                checked: (page.cfg_smallButtons || []).indexOf(modelData.kind) >= 0
                onToggled: page.setSmall(modelData.kind, checked)
            }
        }
        ComboBox {
            Kirigami.FormData.label: i18nd("cde-copper", "Small buttons style:")
            model: page.smallStyles
            textRole: "text"
            currentIndex: Math.max(0, page.smallStyles.findIndex(s => s.value === page.cfg_smallStyle))
            onActivated: index => page.cfg_smallStyle = page.smallStyles[index].value
        }
        CheckBox {
            id: llmTile
            text: i18nd("cde-copper", "LLM cluster as a large tile")
        }
        TextField {
            id: llmHosts
            Layout.fillWidth: true
            Kirigami.FormData.label: i18nd("cde-copper", "LLM hosts (comma-separated):")
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: i18nd("cde-copper", "Comma-separated name=http://host:port or name=ssh:PORT. SSH uses curl on the host. Never configure socket proxy ports; ai395:8090 is blocked.")
        }
        CheckBox {
            id: hideVolume
            Kirigami.FormData.label: i18nd("cde-copper", "System tray:")
            text: i18nd("cde-copper", "Leave the volume to the console")
        }
        CheckBox {
            id: hideIcons
            text: i18nd("cde-copper", "Status icons only behind the console's button")
        }
        CheckBox {
            id: panelFrame
            Kirigami.FormData.label: i18nd("cde-copper", "Panel:")
            text: i18nd("cde-copper", "Frame behind the console")
        }
        CheckBox {
            id: hardContrast
            Kirigami.FormData.label: i18nd("cde-copper", "Text:")
            text: i18nd("cde-copper", "Hard contrast: black (white on dark surfaces) instead of the palette's colours")
        }
        TextField { id: label; Kirigami.FormData.label: i18nd("cde-copper", "Console label:") }
        SpinBox {
            Kirigami.FormData.label: i18nd("cde-copper", "Size:")
            Layout.minimumWidth: Kirigami.Units.gridUnit * 7
            from: 75; to: 200; stepSize: 25
            value: Math.round(cfg_consoleScale * 100)
            textFromValue: value => value + " %"
            valueFromText: text => parseInt(text)
            onValueModified: cfg_consoleScale = value / 100
        }
    }
}
