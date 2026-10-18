pragma ComponentBehavior: Bound
import QtQuick
import "windows.js" as Windows

// A window's button in the workspace switcher as drag source, laid in it
// (anchors.fill: parent). As with the launcher tiles (DropTarget.qml), the
// drag starts after a press-and-hold, Qt's 0.8 s: a click still brings the
// window forward, since the button skips its click only after a hold. A
// DragHandler in a button took every press from it (09.10.2026).
Item {
    id: source
    // The window's id (TasksModel's WinIdList, as text).
    property string windowId: ""
    property bool active: true
    anchors.fill: parent

    Connections {
        target: source.active && source.windowId !== "" ? source.parent : null
        ignoreUnknownSignals: true
        function onPressAndHold() { source.start(); }
    }
    function start() {
        const button = source.parent || source;
        const hx = button.pressX !== undefined ? button.pressX : button.width / 2;
        const hy = button.pressY !== undefined ? button.pressY : button.height / 2;
        payload.Drag.mimeData = {[Windows.WINDOW_MIME]: Windows.windowRef(source.windowId, hx / Math.max(1, button.width), hy / Math.max(1, button.height))};
        button.grabToImage(result => {
            payload.Drag.imageSource = result.url;
            payload.Drag.hotSpot.x = hx;
            payload.Drag.hotSpot.y = hy;
            payload.Drag.active = true;
        });
    }
    Item {
        id: payload
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.onDragFinished: Drag.active = false
    }
}
