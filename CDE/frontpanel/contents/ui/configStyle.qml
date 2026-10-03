pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.kquickcontrols as KQuickControls
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
    property string progressInUse: ""    // progress bar style in use
    readonly property var progressStyles: [
        {value: "outlined", text: "Outlined: dark edge, one-pixel bevel"},
        {value: "floating", text: "Floating: a pixel inside the groove, two-pixel bevel"},
        {value: "slim", text: "Slim: 8 pixels high"}]
    readonly property var cursorStyles: [
        {value: "copper", text: "Copper rim"},
        {value: "palette", text: "Rim in the palette's accent colour"},
        {value: "white", text: "White rim, as in X11"},
        {value: "custom", text: "Rim in a colour of my own"}]

    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            if (source.indexOf("kreadconfig6") === 0) {
                const scheme = data.stdout.trim();
                page.current = scheme.indexOf("CDE") === 0 ? scheme.substring(3) : "";
                if (!page.chosen) page.chosen = page.current || "Copper";
            } else if (source.indexOf("cat ") === 0) {
                try { page.progressInUse = JSON.parse(data.stdout).progress || "outlined"; } catch (e) { page.progressInUse = "outlined"; }
                progressBox.currentIndex = Math.max(0, page.progressStyles.findIndex(s => s.value === page.progressInUse));
                let cursor = "copper";
                try { cursor = JSON.parse(data.stdout).cursor || "copper"; } catch (e) {}
                if (cursor.charAt(0) === "#") { cursorColour.color = cursor; cursor = "custom"; }
                cursorBox.currentIndex = Math.max(0, page.cursorStyles.findIndex(s => s.value === cursor));
            }
        }
    }
    // The palette in use can change while the page is open (Apply, or System
    // Settings); its tiles replace the old palette's, so look again.
    Timer {
        interval: 2500; repeat: true; running: page.visible
        onTriggered: shell.connectSource("kreadconfig6 --group General --key ColorScheme")
    }
    Component.onCompleted: {
        shell.connectSource("kreadconfig6 --group General --key ColorScheme");
        shell.connectSource("cat " + Launch.quote(dataDir + "/cde-copper-install/manifest.json"));
    }

    // Every change makes a new request (the time keeps two equal ones apart).
    function request() {
        cfg_styleRequest = JSON.stringify({palette: chosen, backdrop: backdrop, scale: pixels.value,
                                           progress: progressStyles[progressBox.currentIndex].value,
                                           cursor: cursorBox.currentIndex === 3 ? cursorColour.color.toString().substring(0, 7) : cursorStyles[cursorBox.currentIndex].value,
                                           at: Date.now()});
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
        Kirigami.Heading { level: 3; text: "Progress bars" }
        RowLayout {
            ComboBox {
                id: progressBox
                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                model: page.progressStyles
                textRole: "text"
                onActivated: page.request()
            }
            ProgressBar { from: 0; to: 100; value: 62; Layout.preferredWidth: Kirigami.Units.gridUnit * 8 }
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
            text: "In the programs' controls (Kvantum); the bar beside shows the style in use. Programs already open take it when restarted."
        }

        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: "Mouse cursors" }
        RowLayout {
            ComboBox {
                id: cursorBox
                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                model: page.cursorStyles
                textRole: "text"
                onActivated: page.request()
            }
            KQuickControls.ColorButton {
                id: cursorColour
                visible: cursorBox.currentIndex === 3
                color: "#e8874f"
                dialogTitle: "Cursor rim"
                onAccepted: chosenColour => { cursorColour.color = chosenColour; page.request(); }
            }
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
            text: "The cursors after the X11 cursor font: black shapes on a coloured rim, with a soft shadow."
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
                id: preview
                // The packaged Copper tile when the palette's is not there.
                property bool fallback: false
                readonly property string profileTile: "file://" + page.dataDir + "/cde-copper/backdrops/" + (page.current || "Copper") + "/" + page.backdrop + ".png"
                readonly property string packageTile: "file://" + page.dataDir + "/plasma/wallpapers/org.cde.copper.backdrop/contents/images/Copper/" + page.backdrop + ".png"
                onProfileTileChanged: fallback = false
                anchors.fill: parent; anchors.margins: 1
                fillMode: Image.Tile
                smooth: false
                cache: false
                source: !page.backdrop || page.backdrop === "none" ? "" : fallback ? packageTile : profileTile
                onStatusChanged: if (status === Image.Error && !fallback) fallback = true
            }
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
            text: "Backdrops are CDE's patterns (The Open Group, CC BY-SA 3.0), coloured with the palette. They can also be chosen in the desktop's wallpaper settings as \"CDE Backdrop\"."
        }


    }
}
