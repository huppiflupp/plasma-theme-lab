pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.calendar as PlasmaCalendar

// The clock's subpanel: a month view with the events of the enabled
// calendar plugins (KOrganizer/Akonadi, holidays, ...) and the agenda of
// the selected day. i18nd("cde-copper", "Open Calendar") starts the configured calendar app.
Bevel {
    id: panel
    property var pluginsManager
    signal openCalendar()
    signal closeRequested()
    surface: consoleColors.window
    width: 380
    height: 520
    focus: true
    Keys.onEscapePressed: closeRequested()

    property var agenda: []
    function refresh() {
        agenda = month.daysModel ? month.daysModel.eventsForDate(month.currentDate) : [];
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 5
        Bevel {
            Layout.fillWidth: true; Layout.preferredHeight: 29
            surface: consoleColors.highlight
            Text {
                anchors.centerIn: parent
                text: month.currentDate.toLocaleDateString(Qt.locale(), Locale.LongFormat)
                color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 13; font.weight: Font.DemiBold
            }
        }
        Bevel {
            Layout.fillWidth: true; Layout.preferredHeight: 290
            sunken: true; surface: consoleColors.field
            PlasmaCalendar.MonthView {
                id: month
                anchors.fill: parent; anchors.margins: 3
                borderOpacity: 0.25
                today: consoleColors.now
                eventPluginsManager: panel.pluginsManager
                onCurrentDateChanged: panel.refresh()
            }
        }
        Text {
            Layout.fillWidth: true
            text: panel.agenda.length ? i18nd("cde-copper", "Events") : i18nd("cde-copper", "No events")
            color: consoleColors.windowText; font.family: consoleColors.font; font.pixelSize: 12; font.weight: Font.DemiBold
        }
        ListView {
            id: list
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true; spacing: 2
            model: panel.agenda
            delegate: Bevel {
                required property var modelData
                width: list.width; height: 34
                surface: consoleColors.window
                Rectangle { x: 4; y: 4; width: 4; height: parent.height - 8; color: modelData.eventColor || consoleColors.highlight }
                Text {
                    x: 14; width: parent.width - 18; height: parent.height
                    verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                    color: consoleColors.windowText; font.family: consoleColors.font; font.pixelSize: 12
                    text: (modelData.isAllDay ? i18nd("cde-copper", "All day") : modelData.startDateTime.toLocaleTimeString(Qt.locale(), Locale.ShortFormat)) + "   " + modelData.title
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            ConsoleButton {
                Layout.fillWidth: true; implicitHeight: 34; horizontal: true; iconSize: 22
                text: i18nd("cde-copper", "Today"); iconName: "go-jump-today"
                surface: consoleColors.window; foreground: consoleColors.windowText
                onClicked: month.resetToToday()
            }
            ConsoleButton {
                Layout.fillWidth: true; implicitHeight: 34; horizontal: true; iconSize: 22
                text: i18nd("cde-copper", "Open Calendar"); iconName: "view-calendar"
                surface: consoleColors.window; foreground: consoleColors.windowText
                onClicked: panel.openCalendar()
            }
        }
    }
    Connections {
        target: month.daysModel
        function onAgendaUpdated(date) { panel.refresh(); }
    }
    Component.onCompleted: refresh()
}
