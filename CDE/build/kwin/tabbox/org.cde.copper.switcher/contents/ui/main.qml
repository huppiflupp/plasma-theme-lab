// SPDX-FileCopyrightText: 2026 CDE Copper contributors
// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.kwin as KWin

KWin.TabBoxSwitcher {
    id: tabBox
    currentIndex: windows.currentIndex

    // Hard, square Motif edges, inside a one-pixel ink outline.
    component Bevel: Rectangle {
        id: bevel
        property bool sunken: false
        property color ink: Kirigami.Theme.textColor
        readonly property color light: Qt.tint(color, Qt.rgba(1, 1, 1, 0.45))
        readonly property color dark: Qt.tint(color, Qt.rgba(0, 0, 0, 0.50))
        readonly property color topEdge: sunken ? dark : light
        readonly property color bottomEdge: sunken ? light : dark
        border.width: 1
        border.color: ink
        Rectangle { x: 1; y: 1; width: parent.width - 2; height: 2; color: bevel.topEdge }
        Rectangle { x: 1; y: 1; width: 2; height: parent.height - 2; color: bevel.topEdge }
        Rectangle { x: 3; y: parent.height - 3; width: parent.width - 4; height: 2; color: bevel.bottomEdge }
        Rectangle { x: parent.width - 3; y: 3; width: 2; height: parent.height - 4; color: bevel.bottomEdge }
    }

    PlasmaCore.Dialog {
        location: PlasmaCore.Types.Floating
        backgroundHints: PlasmaCore.Dialog.NoBackground
        visible: tabBox.visible
        flags: Qt.Popup | Qt.X11BypassWindowManagerHint
        x: tabBox.screenGeometry.x + Math.round((tabBox.screenGeometry.width - face.width) / 2)
        y: tabBox.screenGeometry.y + Math.round((tabBox.screenGeometry.height - face.height) / 2)

        mainItem: Bevel {
            id: face
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            readonly property int margin: 8
            readonly property int tileWidth: 112
            readonly property int tileHeight: Math.max(84, 62 + Math.ceil(metrics.height))
            readonly property int columns: Math.max(1, Math.min(6, windows.count,
                Math.floor((tabBox.screenGeometry.width * 0.9 - 2 * margin) / tileWidth)))
            readonly property int rows: Math.max(1, Math.ceil(windows.count / columns))
            readonly property int visibleRows: Math.max(1, Math.min(rows,
                Math.floor((tabBox.screenGeometry.height * 0.8 - title.height - 3 * margin) / tileHeight)))
            width: columns * tileWidth + 2 * margin
            height: title.height + visibleRows * tileHeight + 3 * margin

            FontMetrics { id: metrics; font: Kirigami.Theme.defaultFont }

            Bevel {
                id: title
                x: face.margin
                y: face.margin
                width: face.width - 2 * face.margin
                height: Math.max(24, Math.ceil(metrics.height) + 8)
                color: Kirigami.Theme.highlightColor
                Text {
                    anchors.fill: parent
                    anchors.margins: 4
                    text: windows.currentItem ? windows.currentItem.caption : qsTr("No open windows")
                    textFormat: Text.PlainText
                    font: Kirigami.Theme.defaultFont
                    color: Kirigami.Theme.highlightedTextColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideMiddle
                }
            }

            GridView {
                id: windows
                x: face.margin
                y: title.y + title.height + face.margin
                width: face.columns * cellWidth
                height: face.visibleRows * cellHeight
                cellWidth: face.tileWidth
                cellHeight: face.tileHeight
                model: tabBox.model
                currentIndex: tabBox.currentIndex
                focus: true
                clip: true
                flow: GridView.LeftToRight
                keyNavigationWraps: true
                boundsBehavior: Flickable.StopAtBounds
                highlightMoveDuration: 0
                onCurrentIndexChanged: positionViewAtIndex(currentIndex, GridView.Contain)

                delegate: Item {
                    id: tile
                    property string caption: model.caption
                    readonly property bool selected: index === windows.currentIndex
                    width: windows.cellWidth
                    height: windows.cellHeight
                    Accessible.name: caption
                    Accessible.role: Accessible.ListItem
                    Accessible.selected: selected

                    Bevel {
                        anchors.fill: parent
                        anchors.margins: 2
                        visible: tile.selected
                        sunken: true
                        color: Kirigami.Theme.highlightColor
                    }
                    Kirigami.Icon {
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: 8
                        width: 48
                        height: 48
                        source: model.icon
                    }
                    Text {
                        x: 7
                        y: 60
                        width: parent.width - 14
                        height: metrics.height
                        text: tile.caption
                        textFormat: Text.PlainText
                        font: Kirigami.Theme.defaultFont
                        color: tile.selected ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                    }
                    TapHandler {
                        onSingleTapped: {
                            if (index === windows.currentIndex)
                                windows.model.activate(index);
                            else
                                windows.currentIndex = index;
                        }
                        onDoubleTapped: windows.model.activate(index)
                    }
                }
            }

            Connections {
                target: tabBox
                function onCurrentIndexChanged() { windows.currentIndex = tabBox.currentIndex; }
                function onVisibleChanged() {
                    if (tabBox.visible)
                        windows.positionViewAtIndex(windows.currentIndex, GridView.Contain);
                }
            }

            // KWin owns Tab/Alt release; arrow keys also work in its preview.
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Left) windows.moveCurrentIndexLeft();
                else if (event.key === Qt.Key_Right) windows.moveCurrentIndexRight();
                else if (event.key === Qt.Key_Up) windows.moveCurrentIndexUp();
                else if (event.key === Qt.Key_Down) windows.moveCurrentIndexDown();
                else return;
                event.accepted = true;
            }
        }
        onSceneGraphError: () => {} // Match KWin's recovery from a graphics reset.
    }
}
