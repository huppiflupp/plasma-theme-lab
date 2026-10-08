pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

// The saved window layouts (contents/code/layouts.py) as cards: a preview
// of the screens, the name and the applications; a click restores one.
PlasmaCore.Dialog {
    id: layoutsPopup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { layoutsKeeper.opened(); layoutsBody.forceActiveFocus(); }
    mainItem: Bevel {
        id: layoutsBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: layoutsKeeper; root: layoutsPopup.root; dialog: layoutsPopup; segment: layoutsPopup.visualParent ? layoutsPopup.visualParent.parent : null; inside: layoutsHover.hovered }
        HoverHandler { id: layoutsHover }
        Keys.onPressed: layoutsKeeper.keyboard = true
        Keys.onEscapePressed: layoutsPopup.visible = false
        focus: true
        width: 380
        // Up to about three cards; more scroll.
        height: 41 + 40 + (layoutsPopup.root.layoutList.length ? Math.min(layoutView.contentHeight, 560) : 70)
        surface: layoutsPopup.colors.window
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 2
            Bevel {
                Layout.fillWidth: true; Layout.preferredHeight: 27; surface: layoutsPopup.colors.highlight
                Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Saved layouts"); color: layoutsPopup.colors.highlightText; font.family: layoutsPopup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            ConsoleButton {
                Layout.fillWidth: true; Layout.preferredHeight: 38
                text: i18nd("cde-copper", "Save Current Layout…"); iconName: "document-save"
                horizontal: true; iconSize: 28; surface: layoutsPopup.colors.window; foreground: layoutsPopup.colors.windowText
                onClicked: layoutsPopup.root.saveLayout()
            }
            Text {
                visible: layoutsPopup.root.layoutList.length === 0
                Layout.fillWidth: true; Layout.fillHeight: true
                text: i18nd("cde-copper", "No saved layouts yet. Arrange your windows, then save them here.")
                wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                color: layoutsPopup.colors.windowText; font.family: layoutsPopup.colors.font; font.pixelSize: 12
            }
            ListView {
                id: layoutView
                visible: layoutsPopup.root.layoutList.length > 0
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; spacing: 2
                model: layoutsPopup.root.layoutList
                ScrollBar.vertical: ScrollBar { policy: layoutView.contentHeight > layoutView.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }
                delegate: ConsoleButton {
                    id: card
                    required property var modelData
                    property bool confirming: false
                    // The screens side by side as wide as the card, the
                    // text below. Sizes are computed here, not taken from
                    // layouts inside the button (that loops in Qt).
                    readonly property real ratio: preview.status === Image.Ready && preview.implicitWidth > 0
                        ? preview.implicitHeight / preview.implicitWidth : 0.25
                    width: layoutView.width - (layoutView.contentHeight > layoutView.height ? 12 : 0)
                    height: Math.round((width - 14) * ratio) + 4 + 62
                    surface: layoutsPopup.colors.window; foreground: layoutsPopup.colors.windowText
                    Accessible.name: modelData.name
                    onClicked: layoutsPopup.root.restoreLayout(modelData.id)
                    contentItem: Item {
                        Bevel {
                            id: previewBox
                            sunken: true; surface: layoutsPopup.colors.window
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            height: Math.round((card.width - 14) * card.ratio) + 4
                            Image {
                                id: preview
                                anchors.fill: parent; anchors.margins: 2
                                source: card.modelData.image ? "file://" + card.modelData.image : ""
                                sourceSize.width: 720
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                            }
                        }
                        Column {
                            anchors { left: parent.left; right: deleteButton.left; rightMargin: 6; top: previewBox.bottom; topMargin: 4 }
                            spacing: 1
                            Text {
                                width: parent.width; text: card.modelData.name; elide: Text.ElideRight
                                color: layoutsPopup.colors.windowText; font.family: layoutsPopup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold
                            }
                            Text {
                                width: parent.width; text: card.modelData.apps; elide: Text.ElideRight
                                color: layoutsPopup.colors.windowText; font.family: layoutsPopup.colors.font; font.pixelSize: 11
                            }
                            Text {
                                width: parent.width; elide: Text.ElideRight
                                text: i18ndp("cde-copper", "%1 window", "%1 windows", card.modelData.windows) + " · "
                                      + Qt.formatDateTime(new Date(card.modelData.created * 1000), Qt.locale(), Locale.ShortFormat)
                                color: layoutsPopup.colors.windowText; opacity: 0.75; font.family: layoutsPopup.colors.font; font.pixelSize: 11
                            }
                        }
                        // A second click deletes.
                        ConsoleButton {
                            id: deleteButton
                            anchors { right: parent.right; top: previewBox.bottom; topMargin: 8 }
                            width: card.confirming ? 76 : 30; height: 30
                            text: card.confirming ? i18nd("cde-copper", "Delete?") : ""
                            iconName: card.confirming ? "" : "edit-delete"
                            horizontal: true; iconSize: 16; surface: layoutsPopup.colors.window; foreground: layoutsPopup.colors.windowText
                            Accessible.name: i18nd("cde-copper", "Delete layout")
                            onClicked: { if (card.confirming) layoutsPopup.root.deleteLayout(card.modelData.id); else card.confirming = true; }
                        }
                    }
                }
            }
        }
    }
}
