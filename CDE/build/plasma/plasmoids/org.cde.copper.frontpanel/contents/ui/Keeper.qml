import QtQuick

// A subpanel's timer: it closes the dialog once the pointer has left it
// and the segment that opened it (DESIGN-SPEC §8); opened or used from
// the keyboard, it stays until Escape or a second click.
Timer {
    id: keeper
    // The console (main.qml): its hoveredSegment.
    required property var root
    property var dialog
    property Item segment
    property bool inside: false
    property bool keyboard: false
    readonly property bool keep: inside || keyboard || (segment !== null && keeper.root.hoveredSegment === segment)
    interval: 450
    running: dialog && dialog.visible && !keep
    onTriggered: if (dialog) dialog.visible = false
    // The pointer on the segment when it opens: a click, not a key.
    function opened() { keyboard = !(segment !== null && keeper.root.hoveredSegment === segment); }
}
