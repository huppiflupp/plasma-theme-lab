pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami

// Find Application (from the applications menu): every application in one
// list, narrowed by the search field; Return starts the first one shown.
PlasmaCore.Dialog {
    id: applications
    // The console's colours: given, never looked up.
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { appSearch.text = ""; appSearch.forceActiveFocus(); }
    mainItem: Bevel {
        // A Dialog takes no children of its own: its helpers live in here.
        Kicker.AppsModel { id: allApps; flat: true; sorted: true; autoPopulate: true; appletInterface: Plasmoid }
        width: 340; height: 480; surface: applications.colors.window
        Keys.onEscapePressed: applications.visible = false
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 6; spacing: 5
            Bevel {
                surface: applications.colors.highlight; Layout.fillWidth: true; Layout.preferredHeight: 29
                Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Find Application"); color: applications.colors.highlightText; font.family: applications.colors.font; font.pixelSize: 13 }
            }
            TextField {
                id: appSearch
                Layout.fillWidth: true; placeholderText: i18nd("cde-copper", "Search")
                color: applications.colors.fieldText; font.pixelSize: 13
                background: Bevel { sunken: true; surface: applications.colors.field }
                Keys.onEscapePressed: applications.visible = false
                onAccepted: {
                    for (let i = 0; i < appList.count; i++) {
                        const item = appList.itemAtIndex(i);
                        if (item && item.visible) { allApps.trigger(i, "", null); applications.visible = false; break; }
                    }
                }
            }
            ListView {
                id: appList
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; model: allApps; spacing: 2
                ScrollBar.vertical: ScrollBar {}
                delegate: ConsoleButton {
                    required property int index
                    required property var model
                    width: appList.width - 14
                    visible: appSearch.text.length === 0 || text.toLowerCase().indexOf(appSearch.text.toLowerCase()) >= 0
                    height: visible ? 37 : 0
                    text: model.display || i18nd("cde-copper", "Application")
                    iconName: ""
                    Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: 26; height: 26; source: parent.model.decoration; active: false }
                    leftPadding: 40
                    horizontal: true; surface: applications.colors.window; foreground: applications.colors.windowText
                    onClicked: { allApps.trigger(index, "", null); applications.visible = false; }
                }
            }
        }
    }
}
