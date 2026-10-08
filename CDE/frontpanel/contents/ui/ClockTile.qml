pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "launch.js" as Launch

// The clock; a click opens the calendar (or the calendar application).
ConsoleButton {
    id: clock
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    Layout.fillWidth: clock.root.vertical; Layout.fillHeight: !clock.root.vertical
    Layout.preferredWidth: clock.root.vertical ? -1 : clock.root.u(92)
    Layout.preferredHeight: clock.root.vertical ? clock.root.u(72) : -1
    surface: clock.colors.window
    selected: clock.root.calendarDialog.visible
    Accessible.name: Qt.formatDateTime(clock.root.now, Qt.locale().dateTimeFormat(Locale.LongFormat))
    onClicked: {
        if (Plasmoid.configuration.clockOpensApp) clock.root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)));
        else { clock.root.calendarDialog.visualParent = clock; clock.root.calendarDialog.visible = !clock.root.calendarDialog.visible; }
    }
    HoverHandler { onHoveredChanged: clock.root.hoverSegment(clock, hovered) }
    contentItem: ClockFace {
        style: Plasmoid.configuration.clockStyle
        dial: Plasmoid.configuration.clockDial
        seconds: Plasmoid.configuration.clockSeconds
        segmentShadow: Plasmoid.configuration.clockSegmentShadow
        segmentEdge: Plasmoid.configuration.clockSegmentEdge
        now: clock.root.now
        ink: clock.selected ? clock.colors.highlightText : clock.colors.windowText
        dim: clock.colors.hard ? 1 : 0.8
        bold: clock.colors.hard
        // Lit segments and the second hand: the selection (copper) colour,
        // swapped while the tile itself is highlighted.
        accent: clock.selected ? clock.colors.highlightText : clock.colors.highlight
        lamp: clock.colors.highlight
        dialColor: clock.colors.field
        tile: clock.selected ? clock.colors.highlight : clock.colors.window
        font: clock.colors.font
    }
}
