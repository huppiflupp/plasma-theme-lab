pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts

// The volume in the strip's row, when it is not one of the small buttons.
ConsoleButton {
    id: status
    // The console (main.qml): given, never looked up.
    required property var root
    Layout.fillWidth: status.root.vertical; Layout.fillHeight: !status.root.vertical
    // As wide as a launcher, so it lines up with the tiles above it.
    Layout.preferredWidth: status.root.vertical ? -1 : status.root.u(68)
    Layout.preferredHeight: status.root.vertical ? status.root.u(26) : -1
    text: status.root.volumeState
    iconSize: status.root.u(18)
    horizontal: true
    iconName: status.root.muted ? "audio-volume-muted" : "audio-volume-high"
    Accessible.name: i18nd("cde-copper", "Volume %1, %2", status.root.volumeState, status.root.networkState)
    onClicked: { status.root.volumeDialog.visualParent = status; status.root.volumeDialog.visible = !status.root.volumeDialog.visible; }
    HoverHandler { onHoveredChanged: status.root.hoverSegment(status, hovered) }
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: event => status.root.setVolume(status.root.volume + (event.angleDelta.y > 0 ? 5 : -5))
    }
}
