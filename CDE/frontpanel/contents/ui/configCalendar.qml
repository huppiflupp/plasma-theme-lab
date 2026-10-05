pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.workspace.calendar as PlasmaCalendar

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
    property var cfg_groupWindowsDefault
    property var cfg_consoleLabelDefault
    property var cfg_consoleScaleDefault
    property var cfg_hideTrayVolumeDefault
    property var cfg_hideTrayIconsDefault
    property var cfg_trayHiddenByConsoleDefault
    property var cfg_panelFrameDefault
    property var cfg_hardContrastDefault
    property var cfg_floatingDefault
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
    property alias cfg_clockOpensApp: opensApp.checked
    property alias cfg_calendarCommand: command.text
    property var cfg_enabledCalendarPlugins: []
    property string cfg_clockStyle: "digital"
    property string cfg_clockDial: "cde"
    property alias cfg_clockSeconds: seconds.checked
    property alias cfg_clockSegmentEdge: segmentEdge.checked
    property alias cfg_clockSegmentShadow: segmentShadow.checked
    readonly property var styles: [{text: i18nd("cde-copper", "Digital"), value: "digital"}, {text: i18nd("cde-copper", "Seven-segment"), value: "segments"},
                                   {text: i18nd("cde-copper", "Analog"), value: "analog"}]
    readonly property var dials: [{text: i18nd("cde-copper", "CDE (round, as dtclock)"), value: "cde"}, {text: i18nd("cde-copper", "Motif (square well)"), value: "motif"},
                                  {text: i18nd("cde-copper", "Roman numerals"), value: "roman"}, {text: i18nd("cde-copper", "Plain (no dial)"), value: "plain"}]

    PlasmaCalendar.EventPluginsManager {
        id: manager
        Component.onCompleted: populateEnabledPluginsList(page.cfg_enabledCalendarPlugins)
    }

    Kirigami.FormLayout {
        ComboBox {
            Kirigami.FormData.label: i18nd("cde-copper", "Clock display:")
            model: page.styles
            textRole: "text"
            currentIndex: Math.max(0, page.styles.findIndex(s => s.value === page.cfg_clockStyle))
            onActivated: index => page.cfg_clockStyle = page.styles[index].value
        }
        ComboBox {
            Kirigami.FormData.label: i18nd("cde-copper", "Dial:")
            visible: page.cfg_clockStyle === "analog"
            model: page.dials
            textRole: "text"
            currentIndex: Math.max(0, page.dials.findIndex(d => d.value === page.cfg_clockDial))
            onActivated: index => page.cfg_clockDial = page.dials[index].value
        }
        CheckBox { id: seconds; text: i18nd("cde-copper", "Show seconds") }
        CheckBox {
            id: segmentShadow
            text: i18nd("cde-copper", "Unlit segments faintly visible")
            enabled: page.cfg_clockStyle === "segments"
        }
        CheckBox {
            id: segmentEdge
            text: i18nd("cde-copper", "Black edge around lit segments")
            enabled: page.cfg_clockStyle === "segments"
        }
        Label {
            text: i18nd("cde-copper", "Colours follow the palette: dial in the text-field colour, hands in the text colour,\nsecond hand and lit segments in the selection colour.")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true }
        RadioButton {
            Kirigami.FormData.label: i18nd("cde-copper", "Clicking the clock:")
            text: i18nd("cde-copper", "Shows the month and the day's events")
            checked: !opensApp.checked
        }
        RadioButton { id: opensApp; text: i18nd("cde-copper", "Opens the calendar application") }
        TextField {
            id: command
            Kirigami.FormData.label: i18nd("cde-copper", "Calendar application:")
            placeholderText: "@calendar"
            Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        }
        Label {
            text: i18nd("cde-copper", "@calendar starts Merkuro or KOrganizer, whichever is installed.\nAny command or app:<desktop id> works too.")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Events from") }
        ColumnLayout {
            Repeater {
                model: manager.model
                delegate: CheckBox {
                    // Roles through model.*: "display" would clash with
                    // AbstractButton.display.
                    required property var model
                    readonly property string pluginId: model.pluginId
                    text: model.display
                    checked: page.cfg_enabledCalendarPlugins.indexOf(pluginId) >= 0
                    onToggled: {
                        const list = page.cfg_enabledCalendarPlugins.filter(id => id !== pluginId);
                        if (checked) list.push(pluginId);
                        page.cfg_enabledCalendarPlugins = list;
                    }
                }
            }
        }
        Label {
            text: i18nd("cde-copper", "Appointments come from KOrganizer/Akonadi (\"PIM Events\").")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
    }
}
