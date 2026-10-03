pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQuickControls
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
            highlighted: root.cfg_Backdrop === modelData
            onClicked: root.cfg_Backdrop = modelData
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
