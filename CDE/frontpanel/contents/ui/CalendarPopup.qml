pragma ComponentBehavior: Bound
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import "launch.js" as Launch

// The clock's subpanel: the month with the events of the calendar plugins.
PlasmaCore.Dialog {
    id: calendar
    // The console (main.qml): given, never looked up.
    required property var root
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    mainItem: CalendarPanel {
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: calendarKeeper; root: calendar.root; dialog: calendar; segment: calendar.visualParent; inside: calendarHover.hovered }
        PlasmaCalendar.EventPluginsManager {
            id: eventPlugins
            Component.onCompleted: populateEnabledPluginsList(Plasmoid.configuration.enabledCalendarPlugins)
        }
        Connections {
            target: Plasmoid.configuration
            function onEnabledCalendarPluginsChanged() { eventPlugins.populateEnabledPluginsList(Plasmoid.configuration.enabledCalendarPlugins); }
        }
        HoverHandler { id: calendarHover }
        Keys.onPressed: calendarKeeper.keyboard = true
        pluginsManager: eventPlugins
        onCloseRequested: calendar.visible = false
        onOpenCalendar: { calendar.visible = false; calendar.root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg))); }
    }
    onVisibleChanged: if (visible) { calendarKeeper.opened(); mainItem.forceActiveFocus(); }
}
