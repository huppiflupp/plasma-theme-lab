pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.calendar as PlasmaCalendar

ConfigPage {
    id: page
    property alias cfg_clockOpensApp: opensApp.checked
    property alias cfg_calendarCommand: command.text
    property var cfg_enabledCalendarPlugins: []
    property string cfg_clockStyle: "digital"
    property string cfg_clockDial: "cde"
    property alias cfg_clockSeconds: seconds.checked
    property alias cfg_clockSegmentEdge: segmentEdge.checked
    property alias cfg_clockSegmentShadow: segmentShadow.checked
    readonly property var styles: [{text: i18nd("cde-copper", "Digital"), value: "digital"}, {text: i18nd("cde-copper", "Seven-segment"), value: "segments"},
                                   {text: i18nd("cde-copper", "Analog"), value: "analog"},
                                   {text: i18nd("cde-copper", "LED matrix (red)"), value: "ledmatrix"}, {text: i18nd("cde-copper", "Flip clock"), value: "flipclock"},
                                   {text: i18nd("cde-copper", "VFD (blue-green)"), value: "vfd"}, {text: i18nd("cde-copper", "VFD behind blue glass"), value: "vfd-blue"},
                                   {text: i18nd("cde-copper", "VFD aqua, wide halo"), value: "vfd-aqua"}, {text: i18nd("cde-copper", "Flip-disc (yellow)"), value: "flipdisc"},
                                   {text: i18nd("cde-copper", "Panaplex (gas discharge)"), value: "panaplex"}, {text: i18nd("cde-copper", "Panaplex in the palette's colour"), value: "panaplex-palette"}, {text: i18nd("cde-copper", "Odometer drums"), value: "odometer"},
                                   {text: i18nd("cde-copper", "Pixel type (palette)"), value: "pixel"}, {text: i18nd("cde-copper", "Plasma screen"), value: "plasma"}]
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
        Item { Kirigami.FormData.isSection: true }
        Advanced { id: advanced }
        TextField {
            id: command
            visible: advanced.open
            Kirigami.FormData.label: i18nd("cde-copper", "Calendar application:")
            placeholderText: "@calendar"
            Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        }
        Label {
            visible: advanced.open
            text: i18nd("cde-copper", "@calendar starts Merkuro or KOrganizer, whichever is installed.\nAny command or app:<desktop id> works too.")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
    }
}
