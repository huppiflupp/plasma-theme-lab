pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.workspace.calendar as PlasmaCalendar

KCM.SimpleKCM {
    id: page
    property alias cfg_clockOpensApp: opensApp.checked
    property alias cfg_calendarCommand: command.text
    property var cfg_enabledCalendarPlugins: []
    property string cfg_clockStyle: "digital"
    property string cfg_clockDial: "cde"
    property alias cfg_clockSeconds: seconds.checked
    readonly property var styles: [{text: "Digital", value: "digital"}, {text: "Seven-segment", value: "segments"},
                                   {text: "Analog", value: "analog"}]
    readonly property var dials: [{text: "CDE (round, as dtclock)", value: "cde"}, {text: "Motif (square well)", value: "motif"},
                                  {text: "Roman numerals", value: "roman"}, {text: "Plain (no dial)", value: "plain"}]

    PlasmaCalendar.EventPluginsManager {
        id: manager
        Component.onCompleted: populateEnabledPluginsList(page.cfg_enabledCalendarPlugins)
    }

    Kirigami.FormLayout {
        ComboBox {
            Kirigami.FormData.label: "Clock display:"
            model: page.styles
            textRole: "text"
            currentIndex: Math.max(0, page.styles.findIndex(s => s.value === page.cfg_clockStyle))
            onActivated: index => page.cfg_clockStyle = page.styles[index].value
        }
        ComboBox {
            Kirigami.FormData.label: "Dial:"
            visible: page.cfg_clockStyle === "analog"
            model: page.dials
            textRole: "text"
            currentIndex: Math.max(0, page.dials.findIndex(d => d.value === page.cfg_clockDial))
            onActivated: index => page.cfg_clockDial = page.dials[index].value
        }
        CheckBox { id: seconds; text: "Show seconds" }
        Label {
            text: "Colours follow the palette: dial in the text-field colour, hands in the text colour,\nsecond hand and lit segments in the selection colour."
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true }
        RadioButton {
            Kirigami.FormData.label: "Clicking the clock:"
            text: "Shows the month and the day's events"
            checked: !opensApp.checked
        }
        RadioButton { id: opensApp; text: "Opens the calendar application" }
        TextField {
            id: command
            Kirigami.FormData.label: "Calendar application:"
            placeholderText: "@calendar"
            Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        }
        Label {
            text: "@calendar starts Merkuro or KOrganizer, whichever is installed.\nAny command or app:<desktop id> works too."
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Events from" }
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
            text: "Appointments come from KOrganizer/Akonadi (\"PIM Events\")."
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
    }
}
