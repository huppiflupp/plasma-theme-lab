pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "launch.js" as Launch

// The volume's subpanel: slider, mute and the audio settings.
PlasmaCore.Dialog {
    id: volumePopup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { volumeKeeper.opened(); volumeBody.forceActiveFocus(); }
    mainItem: Bevel {
        id: volumeBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: volumeKeeper; root: volumePopup.root; dialog: volumePopup; segment: volumePopup.visualParent; inside: volumeHover.hovered }
        HoverHandler { id: volumeHover }
        Keys.onPressed: volumeKeeper.keyboard = true
        width: 276; height: 168
        surface: volumePopup.colors.window
        focus: true
        Keys.onEscapePressed: volumePopup.visible = false
        Keys.onUpPressed: volumePopup.root.setVolume(volumePopup.root.volume + 5)
        Keys.onDownPressed: volumePopup.root.setVolume(volumePopup.root.volume - 5)
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            Bevel {
                Layout.fillWidth: true; Layout.preferredHeight: 27; surface: volumePopup.colors.highlight
                Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Audio  %1", volumePopup.root.volumeState); color: volumePopup.colors.highlightText; font.family: volumePopup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Slider {
                Layout.fillWidth: true
                from: 0; to: 100; stepSize: 1
                value: Math.min(100, volumePopup.root.volume)
                enabled: !volumePopup.root.muted
                onMoved: volumePopup.root.setVolume(value)
                Accessible.name: i18nd("cde-copper", "Volume")
            }
            RowLayout {
                Layout.fillWidth: true
                ConsoleButton {
                    Layout.fillWidth: true; implicitHeight: 38; horizontal: true; iconSize: 22
                    text: volumePopup.root.muted ? i18nd("cde-copper", "Unmute") : i18nd("cde-copper", "Mute"); iconName: volumePopup.root.muted ? "audio-volume-high" : "audio-volume-muted"
                    surface: volumePopup.colors.window; foreground: volumePopup.colors.windowText
                    selected: volumePopup.root.muted
                    onClicked: { volumePopup.root.muted = !volumePopup.root.muted; volumePopup.root.execute("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"); }
                }
                ConsoleButton {
                    Layout.fillWidth: true; implicitHeight: 38; horizontal: true; iconSize: 22
                    text: i18nd("cde-copper", "Settings…"); iconName: "preferences-system"
                    surface: volumePopup.colors.window; foreground: volumePopup.colors.windowText
                    onClicked: { volumePopup.visible = false; volumePopup.root.run(Launch.resolve("@settings kcm_pulseaudio", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg))); }
                }
            }
        }
    }
}
