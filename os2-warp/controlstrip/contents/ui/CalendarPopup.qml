pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.calendar as PlasmaCalendar

// The clock's popup: the month with the events of the enabled calendar
// plugins and the agenda of the chosen day. After CDE Copper's
// CalendarPopup.qml and CalendarPanel.qml (CDE/frontpanel, copied
// 21.10.2026), drawn in Warp Legacy's colours instead of CDE's bevels.
PlasmaCore.Dialog {
    id: popup
    required property var root
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground

    function toggle(anchor) {
        if (visible) { visible = false; return; }
        visualParent = anchor;
        month.resetToToday();
        visible = true;
        panel.forceActiveFocus();
    }

    mainItem: Rectangle {
        id: panel
        readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
        readonly property color accent: neon ? "#3ad0ff" : Kirigami.Theme.highlightColor
        property var agenda: []
        function refresh() { agenda = month.daysModel ? month.daysModel.eventsForDate(month.currentDate) : []; }
        width: 340; height: 470
        color: Kirigami.Theme.backgroundColor
        border.width: 1
        border.color: accent
        focus: true
        Keys.onEscapePressed: popup.visible = false

        // A manager of its own: the popup lives only once asked for.
        // enabledPlugins loads them (populateEnabledPluginsList() would only
        // tick them in a settings list; CDE Copper's popup has that slip).
        PlasmaCalendar.EventPluginsManager {
            id: plugins
            enabledPlugins: Plasmoid.configuration.enabledCalendarPlugins
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 6
            Label {
                Layout.fillWidth: true
                text: month.currentDate.toLocaleDateString(Qt.locale(), Locale.LongFormat)
                color: panel.accent
                font.pixelSize: 15; font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
            }
            PlasmaCalendar.MonthView {
                id: month
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                borderOpacity: 0.25
                // Day-granular: root.now ticks every second.
                today: new Date(popup.root.day + "T00:00:00")
                eventPluginsManager: plugins
                onCurrentDateChanged: panel.refresh()
            }
            Label {
                text: panel.agenda.length ? i18nd("warp-legacy", "Events") : i18nd("warp-legacy", "No events")
                font.weight: Font.DemiBold
                color: Kirigami.Theme.textColor
            }
            ListView {
                id: list
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; spacing: 2
                model: panel.agenda
                delegate: Item {
                    id: row
                    required property var modelData
                    width: list.width; height: 24
                    Rectangle { y: 4; width: 4; height: parent.height - 8; color: row.modelData.eventColor || panel.accent }
                    Label {
                        x: 10; width: parent.width - 10; height: parent.height
                        verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                        color: Kirigami.Theme.textColor
                        text: (row.modelData.isAllDay ? i18nd("warp-legacy", "All day")
                               : Qt.formatTime(row.modelData.startDateTime, Qt.locale().timeFormat(Locale.ShortFormat))) + "   " + row.modelData.title
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    Layout.fillWidth: true
                    text: i18nd("warp-legacy", "Today"); icon.name: "go-jump-today"
                    onClicked: month.resetToToday()
                }
                Button {
                    Layout.fillWidth: true
                    text: i18nd("warp-legacy", "Open Calendar"); icon.name: "view-calendar"
                    onClicked: { popup.visible = false; popup.root.launch(Plasmoid.configuration.calendarCommand || "@calendar"); }
                }
            }
        }
        Connections {
            target: month.daysModel
            function onAgendaUpdated(date) { panel.refresh(); }
        }
    }
}
