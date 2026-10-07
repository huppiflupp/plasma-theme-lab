pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQuickControls
import org.kde.taskmanager as TaskManager
import "backdrops.js" as Backdrops

// Choosing a backdrop: a preview of every pattern in the applied palette,
// then CDE Copper's pictures ("picture:<key>"), those painted for the
// palette first.
ColumnLayout {
    id: root
    // Plasma hands every settings page every setting's default; declared so
    // it takes them quietly. (Not the settings themselves: Plasma saves every
    // cfg_ property a page has, and an unshown one would write back a stale
    // value over what the console changed meanwhile.)
    property var cfg_BackdropDefault
    property var cfg_PerWorkspaceDefault
    property var cfg_WorkspacesDefault
    property var cfg_PaletteDefault
    property var cfg_PixelSizeDefault
    property var cfg_ColorDefault
    property var cfg_RevisionDefault
    spacing: Kirigami.Units.largeSpacing
    property alias formLayout: form
    property string cfg_Backdrop: "Pebbles"
    // The palette is set by CDE Copper's tool, not here: read, never saved,
    // so the page cannot write back one that was replaced meanwhile.
    property var wallpaperConfiguration
    readonly property string palette: (wallpaperConfiguration && wallpaperConfiguration.Palette) || "Copper"
    readonly property string revision: wallpaperConfiguration && wallpaperConfiguration.Revision ? "?r=" + wallpaperConfiguration.Revision : ""
    property alias cfg_PixelSize: pixels.value
    property alias cfg_Color: colour.color
    property alias cfg_PerWorkspace: perWorkspace.checked
    property var cfg_Workspaces: []
    // The workspace whose backdrop the grid sets, with PerWorkspace on.
    property int editing: Math.max(0, desktops.desktopIds.indexOf(desktops.currentDesktop))
    TaskManager.VirtualDesktopInfo { id: desktops }
    function chosen(index) { return cfg_Workspaces[index] || cfg_Backdrop; }
    function choose(name) {
        if (!perWorkspace.checked) { cfg_Backdrop = name; return; }
        const list = [];
        for (let i = 0; i < Math.max(desktops.numberOfDesktops, cfg_Workspaces.length); i++) list.push(chosen(i));
        list[editing] = name;
        cfg_Workspaces = list;
    }
    readonly property var choices: Backdrops.NAMES
        .concat(Backdrops.TILES.map(t => t.key))
        .concat(Backdrops.TILES.map(t => "natural:" + t.key))
        .concat(Backdrops.PICTURES.filter(p => p.palette === palette).map(p => "picture:" + p.key))
        .concat(Backdrops.PICTURES.filter(p => p.palette !== palette).map(p => "picture:" + p.key))
    function label(value) {
        const picture = Backdrops.PICTURES.find(p => "picture:" + p.key === value);
        const natural = value.startsWith("natural:");
        const tile = Backdrops.TILES.find(t => t.key === (natural ? value.slice(8) : value));
        return picture ? picture.name : tile ? (natural ? i18nd("cde-copper", "%1 (natural colour)", tile.name) : tile.name) : value;
    }
    function isTile(value) { return Backdrops.TILES.some(t => t.key === (value.startsWith("natural:") ? value.slice(8) : value)); }
    // A tile's preview: natural from the package, or tinted from the profile.
    function tileSource(value) {
        return value.startsWith("natural:") ? Qt.resolvedUrl("../images/tiles/" + value.slice(8) + ".jpg") : folder + value + ".jpg";
    }
    readonly property string pictures: StandardPaths.writableLocation(StandardPaths.GenericDataLocation) + "/wallpapers/"
    // The palette in use, kept under this name by the tool.
    readonly property string folder: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/cde-copper/backdrops/current/"

    Kirigami.FormLayout {
        id: form
        twinFormLayouts: parentLayout
        SpinBox {
            id: pixels
            Kirigami.FormData.label: i18nd("cde-copper", "Pixel size:")
            from: 1; to: 4
            implicitWidth: Kirigami.Units.gridUnit * 6
            textFromValue: value => value + " ×"
        }
        CheckBox {
            id: perWorkspace
            Kirigami.FormData.label: i18nd("cde-copper", "Workspaces:")
            text: i18nd("cde-copper", "A backdrop for each workspace, as in CDE")
        }
        Flow {
            visible: perWorkspace.checked
            Kirigami.FormData.label: i18nd("cde-copper", "Choosing for:")
            spacing: 4
            Repeater {
                model: desktops.numberOfDesktops
                delegate: Button {
                    required property int index
                    checkable: true
                    checked: root.editing === index
                    onClicked: root.editing = index
                    text: (index + 1) + "  " + (desktops.desktopNames[index] || "") + " — " + root.label(root.chosen(index))
                }
            }
        }
        KQuickControls.ColorButton {
            id: colour
            Kirigami.FormData.label: i18nd("cde-copper", "Colour behind the pattern:")
            dialogTitle: i18nd("cde-copper", "Backdrop colour")
        }
        Label {
            text: i18nd("cde-copper", "Patterns from CDE (The Open Group, CC BY-SA 3.0) and material tiles, coloured with the palette %1; the tiles again in their natural colour; then the pictures, those for %1 first.", root.palette)
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
    }
    GridView {
        id: grid
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 14
        clip: true
        cellWidth: Kirigami.Units.gridUnit * 8
        cellHeight: Kirigami.Units.gridUnit * 6
        model: root.choices
        ScrollBar.vertical: ScrollBar {}
        delegate: ItemDelegate {
            id: cell
            required property string modelData
            readonly property bool isPicture: modelData.startsWith("picture:")
            width: grid.cellWidth - 6
            height: grid.cellHeight - 6
            highlighted: (perWorkspace.checked ? root.chosen(root.editing) : root.cfg_Backdrop) === modelData
            onClicked: root.choose(modelData)
            ToolTip.visible: hovered
            ToolTip.text: root.label(modelData)
            ToolTip.delay: 600
            contentItem: ColumnLayout {
                spacing: 2
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    Layout.preferredWidth: 0
                    color: root.cfg_Color
                    border.width: cell.highlighted ? 3 : 1
                    border.color: cell.highlighted ? Kirigami.Theme.highlightColor : Kirigami.Theme.disabledTextColor
                    clip: true
                    Image {
                        anchors.fill: parent; anchors.margins: parent.border.width
                        visible: cell.isPicture
                        source: cell.isPicture ? root.pictures + "org.cde.copper." + cell.modelData.slice(8) + "/contents/images/3840x2160.jpg" : ""
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        sourceSize.width: width
                    }
                    Image {
                        anchors.fill: parent; anchors.margins: parent.border.width
                        visible: !cell.isPicture
                        source: cell.isPicture ? "" : root.isTile(cell.modelData) ? root.tileSource(cell.modelData) + root.revision : root.folder + cell.modelData + ".png" + root.revision
                        fillMode: Image.Tile
                        smooth: !root.isTile(cell.modelData)
                        cache: false
                        // A tile is 1024 px: shown at a quarter, so the preview reads as material.
                        sourceSize.width: root.isTile(cell.modelData) ? 256 : 0
                        onStatusChanged: if (status === Image.Error && !cell.modelData.startsWith("natural:")) source = Qt.resolvedUrl("../images/Copper/" + cell.modelData + (root.isTile(cell.modelData) ? ".jpg" : ".png"))
                    }
                }
                // Shortened rather than widening the cell: every preview as wide.
                Label {
                    text: root.label(cell.modelData)
                    Layout.fillWidth: true; Layout.preferredWidth: 0
                    horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                    font: Kirigami.Theme.smallFont
                }
            }
        }
    }
}
