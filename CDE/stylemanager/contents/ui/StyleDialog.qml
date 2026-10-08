pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// A dialog of the style manager, as dtstyle opens one per part: its
// settings over a row of OK, Apply and Cancel. Each dialog reads the
// state in use when it opens (load) and hands its change to the
// manager (apply), which runs the theme's tool.
Window {
    id: dialog
    required property var manager
    property string heading
    property string iconName
    default property alias content: body.data
    // Called on opening: set the controls to what is in use.
    signal load()
    // Called by OK and Apply: hand the change to manager.apply().
    signal apply()
    title: i18nd("cde-copper", "Style Manager – %1", heading)
    flags: Qt.Dialog
    color: manager.colours.window
    minimumWidth: layout.implicitWidth + 24
    minimumHeight: layout.implicitHeight + 24
    width: minimumWidth; height: minimumHeight

    function open() {
        load();
        visible = true;
        raise();
        requestActivate();
    }
    Shortcut { sequence: "Escape"; onActivated: dialog.close() }

    ColumnLayout {
        id: layout
        anchors.fill: parent; anchors.margins: 12
        spacing: 10
        ColumnLayout {
            id: body
            Layout.fillWidth: true; Layout.fillHeight: true
            spacing: 8
        }
        // Motif's etched separator.
        Item {
            Layout.fillWidth: true; Layout.preferredHeight: 2
            Rectangle { width: parent.width; height: 1; color: dialog.manager.colours.shade.bottom }
            Rectangle { y: 1; width: parent.width; height: 1; color: dialog.manager.colours.shade.top }
        }
        RowLayout {
            Layout.fillWidth: true
            uniformCellSizes: true
            spacing: 12
            Button {
                Layout.fillWidth: true
                text: i18nd("cde-copper", "OK")
                enabled: !dialog.manager.busy
                onClicked: { dialog.apply(); dialog.close(); }
            }
            Button {
                Layout.fillWidth: true
                text: i18nd("cde-copper", "Apply")
                enabled: !dialog.manager.busy
                onClicked: dialog.apply()
            }
            Button {
                Layout.fillWidth: true
                text: i18nd("cde-copper", "Cancel")
                onClicked: dialog.close()
            }
        }
    }
}
