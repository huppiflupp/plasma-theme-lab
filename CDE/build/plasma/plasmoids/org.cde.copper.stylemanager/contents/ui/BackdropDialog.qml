pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "palettes.js" as Palettes
import "backdrops.js" as Backdrops

// Backdrop: as in dtstyle, the list of backdrops beside a preview.
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Backdrop")
    iconName: "preferences-desktop-wallpaper"
    property string chosen: ""
    readonly property bool isPicture: chosen.startsWith("picture:")
    readonly property bool isTile: Backdrops.TILES.some(t => t.key === (chosen.startsWith("natural:") ? chosen.slice(8) : chosen))
    readonly property bool isPattern: Palettes.BACKDROPS.indexOf(chosen) >= 0
    // As the "CDE Backdrop" wallpaper lists them: patterns, material tiles in
    // the palette's colours and in their own, then the pictures, those
    // painted for the palette in use first.
    readonly property var choices: [{value: "none", text: i18nd("cde-copper", "Plain palette colour")}]
        .concat(Palettes.BACKDROPS.map(name => ({value: name, text: name})))
        .concat(Backdrops.TILES.map(t => ({value: t.key, text: t.name})))
        .concat(Backdrops.TILES.map(t => ({value: "natural:" + t.key, text: i18nd("cde-copper", "%1 (natural colour)", t.name)})))
        .concat(Palettes.PICTURES.filter(p => p.palette === manager.current)
                .map(p => ({value: "picture:" + p.key, text: i18nd("cde-copper", "Picture: %1 (for this palette)", p.name)})))
        .concat(Palettes.PICTURES.filter(p => p.palette !== manager.current)
                .map(p => ({value: "picture:" + p.key, text: i18nd("cde-copper", "Picture: %1", p.name)})))
        // A backdrop set some other way (several per workspace, an older
        // name): kept unless another is chosen.
        .concat(known(manager.installed.backdrop) ? [] : [{value: "", text: i18nd("cde-copper", "Keep the desktop as it is")}])
    function known(value) {
        return value === "none" || Palettes.BACKDROPS.indexOf(value) >= 0
            || Backdrops.TILES.some(t => t.key === value || "natural:" + t.key === value)
            || Palettes.PICTURES.some(p => "picture:" + p.key === value);
    }
    onLoad: {
        chosen = known(manager.installed.backdrop) ? manager.installed.backdrop : "";
        pixels.value = manager.installed.backdrop_scale || 1;
        patternColour.checked = manager.installed.pattern_colour === "palette";
        list.currentIndex = Math.max(0, choices.findIndex(c => c.value === chosen));
        list.positionViewAtIndex(list.currentIndex, ListView.Center);
    }
    onApply: {
        let args = chosen ? "--backdrop " + manager.quote(chosen) + " --backdrop-scale " + pixels.value : "";
        const patterns = patternColour.checked ? "palette" : "cde";
        if (patterns !== (manager.installed.pattern_colour || "cde")) args += " --pattern-colour " + patterns;
        if (!args) return;
        const name = (choices.find(c => c.value === chosen) || {text: chosen}).text;
        manager.apply(args, i18nd("cde-copper", "Backdrop %1", name), false);
    }

    RowLayout {
        spacing: 12
        Bevel {
            Layout.preferredWidth: 270; Layout.preferredHeight: 300
            sunken: true
            surface: dialog.manager.colours.field
            ListView {
                id: list
                anchors.fill: parent; anchors.margins: 3
                clip: true
                model: dialog.choices
                keyNavigationEnabled: true
                focus: true
                ScrollBar.vertical: ScrollBar {}
                onCurrentIndexChanged: if (currentIndex >= 0) dialog.chosen = dialog.choices[currentIndex].value
                delegate: Rectangle {
                    id: row
                    required property var modelData
                    required property int index
                    width: ListView.view.width; height: 22
                    color: ListView.isCurrentItem ? dialog.manager.colours.highlight : "transparent"
                    Text {
                        x: 5; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 10
                        text: row.modelData.text
                        elide: Text.ElideRight
                        color: row.ListView.isCurrentItem ? dialog.manager.colours.highlightText : dialog.manager.colours.fieldText
                        font.family: dialog.manager.colours.font; font.pixelSize: 12
                    }
                    MouseArea { anchors.fill: parent; onClicked: list.currentIndex = row.index }
                }
            }
        }
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            spacing: 8
            Bevel {
                // The pattern in the palette in use (its tiles are made when
                // a palette is applied), or the picture.
                Layout.preferredWidth: 320; Layout.preferredHeight: 200
                sunken: true
                surface: dialog.manager.colours.field
                clip: true
                Image {
                    anchors.fill: parent; anchors.margins: 2
                    visible: dialog.isPicture
                    source: dialog.isPicture ? "file://" + dialog.manager.dataDir + "/wallpapers/org.cde.copper." + dialog.chosen.slice(8) + "/contents/images/3840x2160.jpg" : ""
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    sourceSize.width: width
                }
                Image {
                    id: preview
                    visible: dialog.isPattern
                    // The packaged Copper tile when the palette's is not there.
                    property bool fallback: false
                    readonly property string profileTile: "file://" + dialog.manager.dataDir + "/cde-copper/backdrops/" + (dialog.manager.current || "Copper") + "/" + dialog.chosen + ".png"
                    readonly property string packageTile: "file://" + dialog.manager.dataDir + "/plasma/wallpapers/org.cde.copper.backdrop/contents/images/Copper/" + dialog.chosen + ".png"
                    onProfileTileChanged: fallback = false
                    anchors.fill: parent; anchors.margins: 2
                    fillMode: Image.Tile
                    smooth: false
                    cache: false
                    source: !dialog.isPattern ? "" : fallback ? packageTile : profileTile
                    onStatusChanged: if (status === Image.Error && !fallback) fallback = true
                }
                Image {
                    // A material tile (1024 px) at a quarter, so it reads as
                    // material: natural from the plugin, tinted from the profile.
                    anchors.fill: parent; anchors.margins: 2
                    visible: dialog.isTile
                    fillMode: Image.Tile
                    sourceSize.width: 256; sourceSize.height: 256
                    asynchronous: true
                    cache: false
                    source: !dialog.isTile ? ""
                          : dialog.chosen.startsWith("natural:") ? "file://" + dialog.manager.dataDir + "/plasma/wallpapers/org.cde.copper.backdrop/contents/images/tiles/" + dialog.chosen.slice(8) + ".jpg"
                          : "file://" + dialog.manager.dataDir + "/cde-copper/backdrops/current/" + dialog.chosen + ".jpg"
                }
                Rectangle {
                    anchors.fill: parent; anchors.margins: 2
                    visible: dialog.chosen === "none"
                    color: dialog.manager.desktopColour
                }
            }
            RowLayout {
                enabled: dialog.isPattern || dialog.isTile
                Label { text: i18nd("cde-copper", "Pixel size:") }
                SpinBox {
                    id: pixels
                    from: 1; to: 3; value: 1
                    textFromValue: value => value + " ×"
                }
            }
        }
    }
    CheckBox {
        id: patternColour
        text: i18nd("cde-copper", "On dark palettes, patterns in a colour of the palette instead of white")
    }
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 600
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "Backdrops are CDE's patterns (The Open Group, CC BY-SA 3.0), coloured with the palette, or CDE Copper's pictures, each painted for one palette and shown dark under a dark one. They can also be chosen in the desktop's wallpaper settings as \"CDE Backdrop\", one per workspace too.")
    }
}
