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

    PlasmaCalendar.EventPluginsManager {
        id: manager
        Component.onCompleted: populateEnabledPluginsList(page.cfg_enabledCalendarPlugins)
    }

    Kirigami.FormLayout {
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
