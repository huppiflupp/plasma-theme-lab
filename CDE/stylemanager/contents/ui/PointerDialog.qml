pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kquickcontrols as KQuickControls

// Pointer: the rim of the cursors after the X11 cursor font.
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Pointer")
    iconName: "preferences-desktop-cursors"
    property string chosen: "copper"
    readonly property var styles: [
        {value: "copper", text: i18nd("cde-copper", "Copper rim")},
        {value: "palette", text: i18nd("cde-copper", "Rim in the palette's accent colour")},
        {value: "white", text: i18nd("cde-copper", "White rim, as in X11")},
        {value: "custom", text: i18nd("cde-copper", "Rim in a colour of my own")}]
    readonly property string wanted: chosen === "custom" ? rim.color.toString().substring(0, 7) : chosen
    onLoad: {
        const cursor = manager.installed.cursor || "copper";
        if (cursor.charAt(0) === "#") { rim.color = cursor; chosen = "custom"; }
        else chosen = cursor;
        mark();
    }
    onApply: if (wanted !== (manager.installed.cursor || "copper"))
        manager.apply("--cursor " + manager.quote(wanted), i18nd("cde-copper", "Pointer: %1", styles.find(s => s.value === chosen).text), false)

    ButtonGroup { id: group }
    // Set on loading (a binding to chosen did not show the first state).
    function mark() {
        for (let i = 0; i < choices.count; i++) choices.itemAt(i).checked = styles[i].value === chosen;
    }
    Repeater {
        id: choices
        model: dialog.styles
        delegate: RadioButton {
            required property var modelData
            text: modelData.text
            ButtonGroup.group: group
            onToggled: if (checked) dialog.chosen = modelData.value
        }
    }
    RowLayout {
        enabled: dialog.chosen === "custom"
        Label { text: i18nd("cde-copper", "Rim colour:") }
        KQuickControls.ColorButton {
            id: rim
            color: "#e8874f"
            dialogTitle: i18nd("cde-copper", "Cursor rim")
            onAccepted: chosenColour => rim.color = chosenColour
        }
    }
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 460
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "The cursors after the X11 cursor font: black shapes on a coloured rim, with a soft shadow.")
    }
}
