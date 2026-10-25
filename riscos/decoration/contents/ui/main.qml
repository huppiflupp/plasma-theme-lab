import QtQuick
import org.kde.kwin.decoration

// The RISC OS window frame (DESIGN.md §3):
//  - one black line round the window and between the tools, no sizing
//    border: RISC OS sizes windows from the corner tool; KWin's invisible
//    extended borders take that part here;
//  - the title row: Back and Close on the left, Iconise and Toggle size on
//    the right (the order comes from kwinrc, set by the global theme), the
//    title bar between them, the title centred;
//  - the pictures (art/, toolart.py per variant) over the title colour of
//    the colour scheme, as the Wimp plots its tool sprites over colour 12,
//    cream, for the window with the input focus;
//  - 1x or 2x pixels: 2x from a title font of about 16 px up, or as set.
Decoration {
    id: root

    readonly property Style style: Style {}

    DecorationOptions { id: options; deco: decoration }
    FontMetrics { id: metrics; font: options.titleFont }

    // 0 automatic, 1 or 2: the pictures' pixel size.
    property int scaleSetting: 0
    readonly property int px: scaleSetting > 0 ? scaleSetting : (metrics.height >= 22 ? 2 : 1)
    readonly property string sfx: px === 2 ? "@2x" : ""
    readonly property bool maximized: decoration.client.maximized
    readonly property int line: 1
    readonly property int tool: 20 * px
    // RISC OS 4's sprites carry their black outline on all four sides; the
    // Wimp lays them one pixel over each other, and the outline is the
    // window's line (Style.qml: shared). The drawn sets leave it to us.
    readonly property bool shared: style.shared
    readonly property int gap: shared ? -px : line
    readonly property int inset: shared ? 0 : line
    readonly property int titleHeight: shared ? tool : tool + 2 * line

    function art(name) { return Qt.resolvedUrl("art/" + name + sfx + ".png"); }

    function readBorders() {
        const side = decorationSettings.borderSize === DecorationOptions.BorderNone
            || decorationSettings.borderSize === DecorationOptions.BorderNoSides ? 0 : root.line;
        borders.setBorders(side);
        borders.setTitle(root.titleHeight);
        maximizedBorders.setTitle(root.titleHeight - root.inset);
        // RISC OS has no sizing border; the mouse still finds one.
        extendedBorders.setAllBorders(6);
    }
    function readConfig() {
        root.scaleSetting = decoration.readConfig("pixelScale", 0);
    }
    onTitleHeightChanged: readBorders()
    Timer { interval: 2000; running: true; repeat: true; onTriggered: root.readConfig() }

    // ---- frame: black --------------------------------------------------
    Rectangle {
        anchors.fill: parent
        color: root.style.line
    }

    // ---- title row -----------------------------------------------------
    Item {
        id: titleRow
        x: root.maximized ? 0 : root.inset
        y: root.maximized ? 0 : root.inset
        width: parent.width - 2 * x
        height: root.tool

        ButtonGroup {
            id: leftButtons
            spacing: root.gap
            explicitSpacer: root.tool / 2
            menuButton: menuButtonComponent
            appMenuButton: appMenuButtonComponent
            minimizeButton: minimizeButtonComponent
            maximizeButton: maximizeButtonComponent
            keepBelowButton: keepBelowButtonComponent
            keepAboveButton: keepAboveButtonComponent
            helpButton: helpButtonComponent
            shadeButton: shadeButtonComponent
            allDesktopsButton: allDesktopsButtonComponent
            closeButton: closeButtonComponent
            buttons: options.titleButtonsLeft
            anchors { left: parent.left; top: parent.top }
        }
        // The title bar: the title colour, the texture over it, the caps.
        Item {
            id: captionBar
            anchors {
                left: leftButtons.right; leftMargin: leftButtons.width > 0 ? root.gap : 0
                right: rightButtons.left; rightMargin: rightButtons.width > 0 ? root.gap : 0
                top: parent.top; bottom: parent.bottom
            }
            Rectangle {
                anchors.fill: parent
                color: options.titleBarColor
            }
            Image {
                id: capLeft
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                source: root.art("tleft")
                smooth: false
            }
            Image {
                id: capRight
                anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
                source: root.art("tright")
                smooth: false
            }
            Image {
                anchors { left: capLeft.right; right: capRight.left; top: parent.top }
                height: parent.height / 2
                source: root.art("tmidt")
                fillMode: Image.Tile
                smooth: false
            }
            Image {
                anchors { left: capLeft.right; right: capRight.left; bottom: parent.bottom }
                height: parent.height / 2
                source: root.art("tmidb")
                fillMode: Image.Tile
                smooth: false
            }
            Text {
                anchors.fill: parent
                anchors.leftMargin: 4 * root.px
                anchors.rightMargin: 4 * root.px
                text: decoration.client.caption
                textFormat: Text.PlainText
                font: options.titleFont
                color: options.fontColor
                elide: Text.ElideMiddle
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
        ButtonGroup {
            id: rightButtons
            spacing: root.gap
            explicitSpacer: root.tool / 2
            menuButton: menuButtonComponent
            appMenuButton: appMenuButtonComponent
            minimizeButton: minimizeButtonComponent
            maximizeButton: maximizeButtonComponent
            keepBelowButton: keepBelowButtonComponent
            keepAboveButton: keepAboveButtonComponent
            helpButton: helpButtonComponent
            shadeButton: shadeButtonComponent
            allDesktopsButton: allDesktopsButtonComponent
            closeButton: closeButtonComponent
            buttons: options.titleButtonsRight
            anchors { right: parent.right; top: parent.top }
        }
        Component.onCompleted: decoration.installTitleItem(titleRow)
    }

    Component { id: menuButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonMenu } }
    Component { id: appMenuButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonApplicationMenu } }
    Component { id: minimizeButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonMinimize } }
    Component { id: maximizeButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonMaximizeRestore } }
    Component { id: keepBelowButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonKeepBelow } }
    Component { id: keepAboveButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonKeepAbove } }
    Component { id: helpButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonQuickHelp } }
    Component { id: shadeButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonShade } }
    Component { id: allDesktopsButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonOnAllDesktops } }
    Component { id: closeButtonComponent; ToolButton { buttonType: DecorationOptions.DecorationButtonClose } }

    Component.onCompleted: {
        readConfig();
        readBorders();
    }
    Connections {
        target: decoration
        function onConfigChanged() { root.readConfig(); }
    }
    Connections {
        target: decorationSettings
        function onBorderSizeChanged() { root.readBorders(); }
    }
}
