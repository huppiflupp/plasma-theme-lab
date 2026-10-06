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
    // Plasma hands every settings page every setting's default; declared so
    // it takes them quietly. (Not the settings themselves: Plasma saves every
    // cfg_ property a page has, and an unshown one would write back a stale
    // value over what the console changed meanwhile.)
    property var cfg_visibilityModeDefault
    property var cfg_topEdgeDefault
    property var cfg_edgeDefault
    property var cfg_windowsOnThisScreenDefault
    property var cfg_workspaceColoursDefault
    property var cfg_groupWindowsDefault
    property var cfg_consoleLabelDefault
    property var cfg_consoleScaleDefault
    property var cfg_hideTrayVolumeDefault
    property var cfg_hideTrayIconsDefault
    property var cfg_trayHiddenByConsoleDefault
    property var cfg_panelFrameDefault
    property var cfg_hardContrastDefault
    property var cfg_floatingDefault
    property var cfg_everyScreenDefault
    property var cfg_styleRequestDefault
    property var cfg_leftLaunchersDefault
    property var cfg_rightLaunchersDefault
    property var cfg_clockOpensAppDefault
    property var cfg_clockStyleDefault
    property var cfg_clockDialDefault
    property var cfg_clockSecondsDefault
    property var cfg_clockSegmentEdgeDefault
    property var cfg_clockSegmentShadowDefault
    property var cfg_calendarCommandDefault
    property var cfg_enabledCalendarPluginsDefault
    property var cfg_showWorkspacesDefault
    property var cfg_workspaceCountDefault
    property var cfg_workspaceButtonWidthDefault
    property var cfg_workspaceLabelsDefault
    property var cfg_launcherLabelsDefault
    readonly property string dataDir: decodeURIComponent(StandardPaths.writableLocation(StandardPaths.GenericDataLocation).toString().replace(/^file:\/\//, ""))
    readonly property string tool: dataDir + "/cde-copper/tool/manage.py"
    // The KDE Store edition comes without manage.py, which applies palettes.
    property bool hasTool: true
    property string current: ""          // the palette in use
    property string chosen: ""
    property string backdrop: ""         // "" keeps the desktop as it is
    readonly property bool isPicture: backdrop.startsWith("picture:")
    readonly property bool isPattern: backdrop !== "" && backdrop !== "none" && !isPicture
    property string cfg_styleRequest: ""
    property string progressInUse: ""    // progress bar style in use
    readonly property var progressStyles: [
        {value: "outlined", text: i18nd("cde-copper", "Outlined: dark edge, one-pixel bevel")},
        {value: "floating", text: i18nd("cde-copper", "Floating: a pixel inside the groove, two-pixel bevel")},
        {value: "slim", text: i18nd("cde-copper", "Slim: 8 pixels high")}]
    readonly property var cursorStyles: [
        {value: "copper", text: i18nd("cde-copper", "Copper rim")},
        {value: "palette", text: i18nd("cde-copper", "Rim in the palette's accent colour")},
        {value: "white", text: i18nd("cde-copper", "White rim, as in X11")},
        {value: "custom", text: i18nd("cde-copper", "Rim in a colour of my own")}]

    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            if (source.indexOf("test -f") === 0) {
                page.hasTool = data.stdout.trim() === "yes";
            } else if (source.indexOf("kreadconfig6") === 0) {
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
                let lock = "cde";
                try { lock = JSON.parse(data.stdout).lockscreen || "cde"; } catch (e) {}
                lockBox.currentIndex = lock === "plasma" ? 1 : 0;
                let shadow = true;
                try { shadow = JSON.parse(data.stdout).window_shadow !== false; } catch (e) {}
                windowShadow.checked = shadow;
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
        shell.connectSource("test -f " + Launch.quote(tool) + " && echo yes || echo no");
        shell.connectSource("kreadconfig6 --group General --key ColorScheme");
        shell.connectSource("cat " + Launch.quote(dataDir + "/cde-copper-install/manifest.json"));
    }

    // Every change makes a new request (the time keeps two equal ones apart).
    function request() {
        cfg_styleRequest = JSON.stringify({palette: chosen, backdrop: backdrop, scale: pixels.value,
                                           progress: progressStyles[progressBox.currentIndex].value,
                                           cursor: cursorBox.currentIndex === 3 ? cursorColour.color.toString().substring(0, 7) : cursorStyles[cursorBox.currentIndex].value,
                                           lockscreen: lockBox.currentIndex === 1 ? "plasma" : "cde",
                                           windowShadow: windowShadow.checked,
                                           at: Date.now()});
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: !page.hasTool
            type: Kirigami.MessageType.Information
            text: i18nd("cde-copper", "This edition of CDE Copper comes from the KDE Store and cannot recolour the theme: choose a colour scheme in System Settings › Colours. The style manager with CDE's 37 palettes, backdrops and the Motif controls is part of the full installation from the project page.")
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            enabled: page.hasTool
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Palette") }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
                text: i18nd("cde-copper", "CDE's 37 palettes and CDE Copper. The stripes: console, windows, text fields, active and inactive title, desktop. Choose one (and a backdrop below), then Apply or OK. ● marks the palette in use.")
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
                        ToolTip.text: page.current === modelData.name ? i18nd("cde-copper", "%1 (in use)", modelData.name) : modelData.name
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
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Progress bars") }
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
                text: i18nd("cde-copper", "In the programs' controls (Kvantum); the bar beside shows the style in use. Programs already open take it when restarted.")
            }

            Kirigami.Separator { Layout.fillWidth: true }
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Mouse cursors") }
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
                    dialogTitle: i18nd("cde-copper", "Cursor rim")
                    onAccepted: chosenColour => { cursorColour.color = chosenColour; page.request(); }
                }
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
                text: i18nd("cde-copper", "The cursors after the X11 cursor font: black shapes on a coloured rim, with a soft shadow.")
            }

            Kirigami.Separator { Layout.fillWidth: true }
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Windows") }
            CheckBox {
                id: windowShadow
                checked: true
                text: i18nd("cde-copper", "Short hard shadow at the right and bottom of each window")
                onToggled: page.request()
            }

            Kirigami.Separator { Layout.fillWidth: true }
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Lock screen") }
            ComboBox {
                id: lockBox
                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                model: [i18nd("cde-copper", "CDE's: a Motif dialog on the backdrop"), i18nd("cde-copper", "Plasma's own")]
                onActivated: page.request()
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
                text: i18nd("cde-copper", "Plasma takes the lock screen from its shell package; CDE's comes in a shell package of its own that takes everything else from Plasma's. Switching restarts the desktop shell once.")
            }

            Kirigami.Separator { Layout.fillWidth: true }
            Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Backdrop") }
            RowLayout {
                ComboBox {
                    id: backdrops
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                    // Patterns, then the pictures: those painted for the chosen
                    // palette first.
                    readonly property var choices: [{value: "", text: i18nd("cde-copper", "Keep the desktop as it is")},
                                                    {value: "none", text: i18nd("cde-copper", "Plain palette colour")}]
                        .concat(Palettes.BACKDROPS.map(name => ({value: name, text: name})))
                        .concat(Palettes.PICTURES.filter(p => p.palette === page.chosen)
                                .map(p => ({value: "picture:" + p.key, text: i18nd("cde-copper", "Picture: %1 (for this palette)", p.name)})))
                        .concat(Palettes.PICTURES.filter(p => p.palette !== page.chosen)
                                .map(p => ({value: "picture:" + p.key, text: i18nd("cde-copper", "Picture: %1", p.name)})))
                    model: choices
                    textRole: "text"
                    onActivated: index => { page.backdrop = choices[index].value; page.request(); }
                    onChoicesChanged: currentIndex = Math.max(0, choices.findIndex(c => c.value === page.backdrop))
                }
                Label { text: i18nd("cde-copper", "Pixel size:"); visible: page.isPattern }
                SpinBox {
                    id: pixels
                    visible: page.isPattern
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
                    visible: page.isPicture
                    source: page.isPicture ? "file://" + page.dataDir + "/wallpapers/org.cde.copper." + page.backdrop.slice(8) + "/contents/images/3840x2160.jpg" : ""
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    sourceSize.width: width
                }
                Image {
                    id: preview
                    visible: page.isPattern
                    // The packaged Copper tile when the palette's is not there.
                    property bool fallback: false
                    readonly property string profileTile: "file://" + page.dataDir + "/cde-copper/backdrops/" + (page.current || "Copper") + "/" + page.backdrop + ".png"
                    readonly property string packageTile: "file://" + page.dataDir + "/plasma/wallpapers/org.cde.copper.backdrop/contents/images/Copper/" + page.backdrop + ".png"
                    onProfileTileChanged: fallback = false
                    anchors.fill: parent; anchors.margins: 1
                    fillMode: Image.Tile
                    smooth: false
                    cache: false
                    source: !page.isPattern ? "" : fallback ? packageTile : profileTile
                    onStatusChanged: if (status === Image.Error && !fallback) fallback = true
                }
            }
            Label {
                Layout.fillWidth: true; wrapMode: Text.Wrap; opacity: 0.75
                text: i18nd("cde-copper", "Backdrops are CDE's patterns (The Open Group, CC BY-SA 3.0), coloured with the palette, or CDE Copper's pictures, each painted for one palette and shown dark under a dark one. They can also be chosen in the desktop's wallpaper settings as \"CDE Backdrop\", one per workspace too.")
            }
        }
    }
}
