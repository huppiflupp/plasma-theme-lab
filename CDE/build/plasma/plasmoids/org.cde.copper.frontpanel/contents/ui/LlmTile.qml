pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.plasma.plasmoid

// The LLM cluster as a launcher-sized tile: its tokens per second, the
// arrow and the tile open the cluster's popup.
GridLayout {
    id: tile
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    rows: tile.root.vertical ? 1 : 2
    columns: tile.root.vertical ? 2 : 1
    rowSpacing: 1; columnSpacing: 1
    Layout.fillWidth: true; Layout.fillHeight: true
    Layout.preferredWidth: tile.root.vertical ? -1 : tile.root.u(68)
    Layout.preferredHeight: tile.root.vertical ? tile.root.u(62) : -1
    readonly property bool popupSelected: tile.root.llmDialog.visible && (tile.root.llmDialog.visualParent === arrow || tile.root.llmDialog.visualParent === launcher)
    Binding { target: tile.root; property: "llmTileVisible"; value: tile.visible && tile.Window.window !== null && tile.Window.window.visible; restoreMode: Binding.RestoreBindingOrValue }
    ConsoleButton {
        id: arrow
        Layout.row: 0
        Layout.column: tile.root.vertical && !tile.root.atRight ? 1 : 0
        Layout.fillWidth: !tile.root.vertical; Layout.fillHeight: tile.root.vertical
        Layout.preferredHeight: tile.root.vertical ? -1 : tile.root.u(13)
        Layout.preferredWidth: tile.root.vertical ? tile.root.u(13) : -1
        text: ""
        Accessible.name: i18nd("cde-copper", "LLM cluster: %1 t/s", Math.round(tile.root.llmTotal))
        selected: tile.popupSelected
        contentItem: Text {
            text: tile.root.arrowGlyph
            color: tile.colors.panelText; font.pixelSize: tile.root.u(12)
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
        onClicked: tile.root.toggleLlm(arrow, tile)
    }
    ConsoleButton {
        id: launcher
        Layout.row: tile.root.vertical ? 0 : 1
        Layout.column: tile.root.vertical && !tile.root.atRight ? 0 : (tile.root.vertical ? 1 : 0)
        Layout.fillWidth: true; Layout.fillHeight: true
        text: ""
        labelled: Plasmoid.configuration.launcherLabels
        Accessible.name: i18nd("cde-copper", "LLM cluster: %1 t/s", Math.round(tile.root.llmTotal))
        selected: tile.popupSelected
        onClicked: tile.root.toggleLlm(launcher, tile)
        contentItem: Item {
            implicitWidth: tile.root.u(58); implicitHeight: tile.root.u(55)
            Text {
                width: parent.width; height: Math.round(parent.height * (launcher.labelled ? 0.52 : 0.68))
                text: Math.round(tile.root.llmTotal)
                color: launcher.selected ? launcher.accentText : tile.colors.panelText
                font.family: tile.colors.font; font.pixelSize: tile.root.u(24); font.weight: Font.DemiBold
                fontSizeMode: Text.Fit; minimumPixelSize: tile.root.u(8)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
            Text {
                width: parent.width; y: Math.round(parent.height * (launcher.labelled ? 0.52 : 0.68))
                height: Math.round(parent.height * (launcher.labelled ? 0.25 : 0.32))
                text: i18nd("cde-copper", "t/s")
                color: launcher.selected ? launcher.accentText : tile.colors.panelText
                font.family: tile.colors.font; font.pixelSize: tile.root.u(10)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
            Text {
                visible: launcher.labelled
                width: parent.width; y: Math.round(parent.height * 0.77); height: parent.height - y
                text: i18nd("cde-copper", "LLM")
                color: launcher.selected ? launcher.accentText : tile.colors.panelText
                font.family: tile.colors.font; font.pixelSize: tile.root.u(11); font.weight: tile.colors.weight
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
        }
    }
    HoverHandler { onHoveredChanged: tile.root.hoverSegment(tile, hovered) }
}
