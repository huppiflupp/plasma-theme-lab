pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Terminal: which colours the terminals take from the palette (terminals.py).
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Terminal")
    iconName: "utilities-terminal"
    property string chosen: "dark"
    readonly property var styles: [
        {value: "dark", text: i18nd("cde-copper", "Dark, tinted with the palette")},
        {value: "field", text: i18nd("cde-copper", "Like the palette's text fields")}]
    onLoad: { chosen = manager.installed.terminal || "dark"; mark(); }
    onApply: if (chosen !== (manager.installed.terminal || "dark"))
        manager.apply("--terminal " + chosen, i18nd("cde-copper", "Terminal: %1", styles.find(s => s.value === chosen).text), false)

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
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 460
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "Both follow the palette. Programs that paint their own surfaces, such as Midnight Commander, are hard to read on light text fields. New terminal windows take the colours; of the open ones only Alacritty, kitty and WezTerm follow at once.")
    }
}
