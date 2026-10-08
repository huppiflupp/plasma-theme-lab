pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "palettes.js" as Palettes

// Colour: CDE's 37 palettes and Copper as stripes of their colours.
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Palette")
    iconName: "preferences-desktop-color"
    property string chosen: ""
    onLoad: chosen = manager.current || "Copper"
    onApply: if (chosen && chosen !== manager.current)
        manager.apply("--palette " + manager.quote(chosen), i18nd("cde-copper", "Palette %1", chosen), true)

    Label {
        Layout.preferredWidth: 6 * 124 + 5 * 4; Layout.maximumWidth: 6 * 124 + 5 * 4
        wrapMode: Text.Wrap
        text: i18nd("cde-copper", "The stripes: console, windows, text fields, active and inactive title, desktop. ● marks the palette in use; a double click applies one at once.")
    }
    GridLayout {
        id: grid
        columns: 6
        rowSpacing: 4; columnSpacing: 4
        Repeater {
            model: Palettes.PALETTES
            delegate: Bevel {
                id: swatch
                required property var modelData
                readonly property bool chosen: dialog.chosen === modelData.name
                Layout.preferredWidth: 124; Layout.preferredHeight: 52
                sunken: chosen
                surface: chosen ? dialog.manager.colours.highlight : dialog.manager.colours.window
                Accessible.role: Accessible.RadioButton
                Accessible.name: modelData.name
                Accessible.checked: chosen
                Row {
                    x: 5; y: 5; width: parent.width - 10; height: 24
                    Repeater {
                        model: swatch.modelData.colours
                        delegate: Rectangle {
                            required property string modelData
                            width: parent.width / 6; height: parent.height
                            color: modelData
                        }
                    }
                }
                Text {
                    x: 5; y: 32; width: parent.width - 10
                    text: swatch.modelData.name + (dialog.manager.current === swatch.modelData.name ? "  ●" : "")
                    elide: Text.ElideRight
                    color: swatch.chosen ? dialog.manager.colours.highlightText : dialog.manager.colours.windowText
                    font.family: dialog.manager.colours.font; font.pixelSize: 12
                    font.weight: swatch.chosen ? Font.DemiBold : Font.Normal
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: dialog.chosen = swatch.modelData.name
                    onDoubleClicked: { dialog.chosen = swatch.modelData.name; if (!dialog.manager.busy) { dialog.apply(); dialog.close(); } }
                }
            }
        }
    }
}
