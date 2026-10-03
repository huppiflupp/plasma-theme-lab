pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQuickControls
import org.kde.taskmanager as TaskManager
import "backdrops.js" as Backdrops

// Choosing a backdrop: a preview of every pattern in the applied palette.
ColumnLayout {
    id: root
    spacing: Kirigami.Units.largeSpacing
    property alias formLayout: form
    property string cfg_Backdrop: "Pebbles"
    property string cfg_Palette: "Copper"
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
    readonly property string folder: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/cde-copper/backdrops/" + cfg_Palette + "/"

    Kirigami.FormLayout {
        id: form
        twinFormLayouts: parentLayout
        SpinBox {
            id: pixels
            Kirigami.FormData.label: "Pixel size:"
            from: 1; to: 4
            implicitWidth: Kirigami.Units.gridUnit * 6
            textFromValue: value => value + " ×"
        }
        CheckBox {
            id: perWorkspace
            Kirigami.FormData.label: "Workspaces:"
            text: "A backdrop for each workspace, as in CDE"
        }
        Flow {
            visible: perWorkspace.checked
            Kirigami.FormData.label: "Choosing for:"
            spacing: 4
            Repeater {
                model: desktops.numberOfDesktops
                delegate: Button {
                    required property int index
                    checkable: true
                    checked: root.editing === index
                    onClicked: root.editing = index
                    text: (index + 1) + "  " + (desktops.desktopNames[index] || "") + " — " + root.chosen(index)
                }
            }
        }
        KQuickControls.ColorButton {
            id: colour
            Kirigami.FormData.label: "Colour behind the pattern:"
            dialogTitle: "Backdrop colour"
        }
        Label {
            text: "Patterns from CDE (The Open Group, CC BY-SA 3.0), coloured with the palette " + root.cfg_Palette + "."
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
        model: Backdrops.NAMES
        ScrollBar.vertical: ScrollBar {}
        delegate: ItemDelegate {
            id: cell
            required property string modelData
            width: grid.cellWidth - 6
            height: grid.cellHeight - 6
            highlighted: (perWorkspace.checked ? root.chosen(root.editing) : root.cfg_Backdrop) === modelData
            onClicked: root.choose(modelData)
            contentItem: ColumnLayout {
                spacing: 2
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    color: root.cfg_Color
                    border.width: cell.highlighted ? 3 : 1
                    border.color: cell.highlighted ? Kirigami.Theme.highlightColor : Kirigami.Theme.disabledTextColor
                    clip: true
                    Image {
                        anchors.fill: parent; anchors.margins: parent.border.width
                        source: root.folder + cell.modelData + ".png"
                        fillMode: Image.Tile
                        smooth: false
                        cache: false
                        onStatusChanged: if (status === Image.Error) source = Qt.resolvedUrl("../images/Copper/" + cell.modelData + ".png")
                    }
                }
                Label { text: cell.modelData; Layout.alignment: Qt.AlignHCenter; font: Kirigami.Theme.smallFont }
            }
        }
    }
}
