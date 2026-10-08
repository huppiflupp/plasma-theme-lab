pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Controls: the progress bars of the Motif controls (Kvantum).
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Progress bars")
    iconName: "preferences-desktop-theme-applications"
    property string chosen: "outlined"
    readonly property var styles: [
        {value: "outlined", text: i18nd("cde-copper", "Outlined: dark edge, one-pixel bevel")},
        {value: "floating", text: i18nd("cde-copper", "Floating: a pixel inside the groove, two-pixel bevel")},
        {value: "slim", text: i18nd("cde-copper", "Slim: 8 pixels high")}]
    onLoad: { chosen = manager.installed.progress || "outlined"; mark(); }
    onApply: if (chosen !== (manager.installed.progress || "outlined"))
        manager.apply("--progress " + chosen, i18nd("cde-copper", "Progress bars: %1", styles.find(s => s.value === chosen).text), true)

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
        Label { text: i18nd("cde-copper", "In use:") }
        ProgressBar { from: 0; to: 100; value: 62; Layout.preferredWidth: 200 }
    }
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 460
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "In the programs' controls (Kvantum); the bar above shows the style in use. After applying, the style manager names the open programs that need a restart.")
    }
}
