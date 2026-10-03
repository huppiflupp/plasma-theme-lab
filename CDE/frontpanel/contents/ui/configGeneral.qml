import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    // Plasma hands every settings page every setting's default; declared so
    // it takes them quietly. (Not the settings themselves: Plasma saves every
    // cfg_ property a page has, and an unshown one would write back a stale
    // value over what the console changed meanwhile.)
    property var cfg_visibilityModeDefault
    property var cfg_topEdgeDefault
    property var cfg_edgeDefault
    property var cfg_windowsOnThisScreenDefault
    property var cfg_workspaceColoursDefault
    property var cfg_groupWindowsDefault
    property var cfg_consoleLabelDefault
    property var cfg_consoleScaleDefault
    property var cfg_hideTrayVolumeDefault
    property var cfg_hideTrayIconsDefault
    property var cfg_trayHiddenByConsoleDefault
    property var cfg_panelFrameDefault
    property var cfg_styleRequestDefault
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
    property alias cfg_visibilityMode: visibility.currentIndex
    property bool cfg_topEdge
    property int cfg_edge: -1
    property alias cfg_windowsOnThisScreen: thisScreen.checked
    property alias cfg_groupWindows: groupWindows.checked
    property alias cfg_workspaceColours: workspaceColours.checked
    property alias cfg_consoleLabel: label.text
    property real cfg_consoleScale: 1.0
    property alias cfg_hideTrayVolume: hideVolume.checked
    property alias cfg_hideTrayIcons: hideIcons.checked
    property alias cfg_panelFrame: panelFrame.checked
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
            id: thisScreen
            Kirigami.FormData.label: i18nd("cde-copper", "Window list:")
            text: i18nd("cde-copper", "Only windows on this console's screen")
        }
        CheckBox {
            id: workspaceColours
            Kirigami.FormData.label: i18nd("cde-copper", "Workspaces:")
            text: i18nd("cde-copper", "Each button in a colour of its own, as in CDE")
        }
        CheckBox {
            id: groupWindows
            text: i18nd("cde-copper", "Group windows of one application (\"3× Konsole\")")
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
