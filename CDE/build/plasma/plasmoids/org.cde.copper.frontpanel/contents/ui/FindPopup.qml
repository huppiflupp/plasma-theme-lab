pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami

// Find Application (from the applications menu): the applications that
// match the search field, found by Plasma's application search (the one
// KRunner uses: names, generic names, keywords), best first; Return starts
// the first. Kicker's flat AppsModel, used here before, lists only the
// categories in Plasma 6.
PlasmaCore.Dialog {
    id: applications
    // The console's colours: given, never looked up.
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    // Opened by typing in the applications menu: that text goes in first.
    property string initialText: ""
    function open(text) {
        initialText = text || "";
        visible = true;
    }
    onVisibleChanged: if (visible) { appSearch.text = initialText; initialText = ""; appSearch.cursorPosition = appSearch.text.length; appSearch.forceActiveFocus(); }
    mainItem: Bevel {
        // A Dialog takes no children of its own: its helpers live in here.
        Kicker.RunnerModel { id: search; appletInterface: Plasmoid; runners: ["krunner_services"]; mergeResults: true; query: appSearch.text }
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
                onAccepted: if (appList.count > 0) { appList.model.trigger(0, "", null); applications.visible = false; }
            }
            ListView {
                id: appList
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; model: search.count > 0 ? search.modelForRow(0) : null; spacing: 2
                ScrollBar.vertical: ScrollBar {}
                delegate: ConsoleButton {
                    required property int index
                    required property var model
                    width: appList.width - 14
                    height: 37
                    text: model.display || i18nd("cde-copper", "Application")
                    iconName: ""
                    Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: 26; height: 26; source: parent.model.decoration; active: false }
                    leftPadding: 40
                    horizontal: true; surface: applications.colors.window; foreground: applications.colors.windowText
                    onClicked: { appList.model.trigger(index, "", null); applications.visible = false; }
                }
            }
        }
    }
}
