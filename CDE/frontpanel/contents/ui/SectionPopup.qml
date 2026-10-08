pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "launch.js" as Launch

// A launcher's subpanel (Places, System, Mail, Terminals, Bookmarks…):
// the title over a button per entry, as root.openSection sets them.
PlasmaCore.Dialog {
    id: popup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { popupKeeper.opened(); popupBody.forceActiveFocus(); }
    mainItem: Bevel {
        id: popupBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: popupKeeper; root: popup.root; dialog: popup; segment: popup.root.popupSegment; inside: popupHover.hovered }
        HoverHandler { id: popupHover }
        Keys.onPressed: popupKeeper.keyboard = true
        width: 320; height: 41 + popup.root.entries.length * 38
        surface: popup.colors.window
        focus: true
        Keys.onEscapePressed: popup.visible = false
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 2
            Bevel {
                Layout.fillWidth: true; Layout.preferredHeight: 27; surface: popup.colors.highlight
                Text { anchors.centerIn: parent; text: popup.root.popupTitle; color: popup.colors.highlightText; font.family: popup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Repeater {
                model: popup.root.entries
                delegate: ConsoleButton {
                    required property var modelData
                    Layout.fillWidth: true; Layout.fillHeight: true
                    text: modelData.label; iconName: modelData.icon
                    horizontal: true; iconSize: 28; surface: popup.colors.window; foreground: popup.colors.windowText
                    enabled: modelData.command !== ""
                    Accessible.name: modelData.tip || modelData.label
                    onClicked: {
                        popup.visible = false;
                        // The style manager is a page of the console's settings.
                        if (modelData.command === "@style") Plasmoid.internalAction("configure").trigger();
                        else popup.root.run(Launch.resolve(modelData.command, modelData.args, (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)));
                    }
                }
            }
        }
    }
}
