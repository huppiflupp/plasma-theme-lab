pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasma5support as P5Support
import "palettes.js" as Palettes
import "launch.js" as Launch

// The style manager, after CDE's dtstyle: the palettes as colour swatches and
// the backdrops as patterns. A choice becomes the styleRequest setting, so
// the dialog's Apply and OK take it like any other; the console then runs
// the theme's tool, which switches colour scheme, Plasma surfaces, Kvantum
// controls and the desktop together. The CDE palettes are also listed in System Settings ›
// Colours; choosing one there has the same effect.
KCM.SimpleKCM {
    id: page
    readonly property string dataDir: decodeURIComponent(StandardPaths.writableLocation(StandardPaths.GenericDataLocation).toString().replace(/^file:\/\//, ""))
    readonly property string tool: dataDir + "/cde-copper/tool/manage.py"
    property string current: ""          // the palette in use
    property string chosen: ""
    property string backdrop: ""         // "" keeps the desktop as it is
    property string cfg_styleRequest: ""

    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            if (source.indexOf("kreadconfig6") === 0) {
                const scheme = data.stdout.trim();
                page.current = scheme.indexOf("CDE") === 0 ? scheme.substring(3) : "";
                if (!page.chosen) page.chosen = page.current || "Copper";
            }
        }
    }
    Component.onCompleted: shell.connectSource("kreadconfig6 --group General --key ColorScheme")

    // Every change makes a new request (the time keeps two equal ones apart).
    function request() {
        cfg_styleRequest = JSON.stringify({palette: chosen, backdrop: backdrop, scale: pixels.value, at: Date.now()});
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Heading { level: 3; text: "Palette" }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
            text: "CDE's 37 palettes and CDE Copper. The stripes: console, windows, text fields, active and inactive title, desktop. "
                + "Choose one (and a backdrop below), then Apply or OK. ● marks the palette in use."
        }
        GridLayout {
            id: palettes
            Layout.fillWidth: true
            columns: Math.max(2, Math.floor(page.width / (Kirigami.Units.gridUnit * 8)))
            uniformCellWidths: true
            rowSpacing: 4; columnSpacing: 4
            Repeater {
                model: Palettes.PALETTES
                delegate: ItemDelegate {
                    id: swatch
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 7
                    Layout.preferredHeight: Kirigami.Units.gridUnit * 3.2
                    highlighted: page.chosen === modelData.name
                    onClicked: { page.chosen = modelData.name; page.request(); }
                    ToolTip.text: modelData.name + (page.current === modelData.name ? " (in use)" : "")
                    ToolTip.visible: hovered
                    contentItem: ColumnLayout {
                        spacing: 2
                        Row {
                            Layout.fillWidth: true; Layout.preferredHeight: Kirigami.Units.gridUnit * 1.5
                            Repeater {
                                model: swatch.modelData.colours
                                delegate: Rectangle {
                                    required property string modelData
                                    width: (swatch.width - 2 * swatch.padding) / 6; height: parent.height
                                    color: modelData
                                }
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: swatch.modelData.name + (page.current === swatch.modelData.name ? "  ●" : "")
                            elide: Text.ElideRight
                            font.weight: swatch.highlighted ? Font.DemiBold : Font.Normal
                        }
                    }
                }
            }
        }

        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: "Backdrop" }
        RowLayout {
            ComboBox {
                id: backdrops
                Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                model: ["Keep the desktop as it is", "Plain palette colour"].concat(Palettes.BACKDROPS)
                onActivated: index => { page.backdrop = index === 0 ? "" : index === 1 ? "none" : Palettes.BACKDROPS[index - 2]; page.request(); }
            }
            Label { text: "Pixel size:"; visible: page.backdrop && page.backdrop !== "none" }
            SpinBox {
                id: pixels
                visible: page.backdrop && page.backdrop !== "none"
                from: 1; to: 3; value: 1
                textFromValue: value => value + " ×"
                onValueModified: page.request()
            }
        }
        Rectangle {
            // A preview of the pattern, in the palette in use (its tiles are
            // made when a palette is applied).
            visible: page.backdrop && page.backdrop !== "none"
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 6
            border.width: 1
            border.color: Kirigami.Theme.disabledTextColor
            clip: true
            Image {
                anchors.fill: parent; anchors.margins: 1
                fillMode: Image.Tile
                smooth: false
                cache: false
                source: page.backdrop ? "file://" + page.dataDir + "/cde-copper/backdrops/" + (page.current || "Copper") + "/" + page.backdrop + ".png" : ""
            }
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
            text: "Backdrops are CDE's patterns (The Open Group, CC BY-SA 3.0), coloured with the palette. They can also be chosen in the desktop's wallpaper settings as \"CDE Backdrop\"."
        }


    }
}
