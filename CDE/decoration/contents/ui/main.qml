import QtQuick
import org.kde.kwin.decoration
import "motif.js" as Motif

// CDE Copper window frame, after mwm/dtwm:
//  - a raised resize frame whose corners are separate handles, cut off from
//    the edges by grooves one title height plus one border from each corner;
//  - a title bar made of individually shadowed parts: window menu, title,
//    minimize, maximize (and close, which KDE users expect);
//  - every colour comes from the active colour scheme (WM active/inactive
//    title colour), the shadows from Motif's own shading rule, so any CDE
//    palette applied as a colour scheme carries through.
Decoration {
    id: root
    alpha: false

    DecorationOptions { id: options; deco: decoration }
    FontMetrics { id: metrics; font: options.titleFont }

    property bool coloredBorder: true
    property int fixedTitleHeight: 0
    property int edge: 6
    readonly property int bevel: 2
    readonly property int inner: 1
    readonly property bool maximized: decoration.client.maximized
    // From the title font unless a height is configured; the buttons are
    // squares of this height, so they scale with it.
    readonly property int titleHeight: fixedTitleHeight >= 16 ? fixedTitleHeight : Math.max(24, Math.ceil(metrics.height) + 12)
    readonly property int corner: titleHeight + edge

    readonly property color frameColor: options.titleBarColor
    readonly property color inkColor: options.fontColor
    readonly property var shade: {
        const s = Motif.shades(frameColor);
        s.hover = Motif.mix(frameColor, s.top, 0.22);
        return s;
    }
    readonly property color borderFace: coloredBorder ? frameColor : options.borderColor
    readonly property var borderShade: coloredBorder ? shade : Motif.shades(options.borderColor)

    function readBorderSize() {
        let side = 6;
        switch (decorationSettings.borderSize) {
        case DecorationOptions.BorderNone: side = 0; break;
        case DecorationOptions.BorderNoSides: side = 0; break;
        case DecorationOptions.BorderTiny: side = 4; break;
        case DecorationOptions.BorderLarge: side = 8; break;
        case DecorationOptions.BorderVeryLarge: side = 10; break;
        case DecorationOptions.BorderHuge: side = 14; break;
        case DecorationOptions.BorderVeryHuge: side = 18; break;
        case DecorationOptions.BorderOversized: side = 24; break;
        }
        root.edge = side;
        const frame = side > 0 ? side : 0;
        borders.setBorders(frame);
        if (decorationSettings.borderSize === DecorationOptions.BorderNoSides) {
            borders.setSideBorders(0);
            borders.bottom = 0;
        }
        borders.setTitle(Math.max(frame, root.bevel) + root.titleHeight);
        maximizedBorders.setTitle(root.titleHeight);
        // Keep at least 6 px to grab even when the visible frame is thin.
        extendedBorders.setAllBorders(Math.max(0, 6 - frame));
    }
    function readConfig() {
        root.coloredBorder = decoration.readConfig("coloredBorder", true);
        root.fixedTitleHeight = decoration.readConfig("titleHeight", 0);
    }
    onTitleHeightChanged: readBorderSize()

    // ---- frame -----------------------------------------------------------
    Bevel {
        id: frame
        anchors.fill: parent
        visible: !root.maximized && root.edge > 0
        color: root.borderFace
        light: root.borderShade.top
        dark: root.borderShade.bottom
        thickness: root.bevel

        // Grooves that cut the corner handles off the edges: a dark line
        // ending one part, a light line starting the next.
        Repeater {
            model: [
                {x: root.corner - 1, y: 0, w: 1, h: root.edge, a: true},
                {x: root.corner, y: 0, w: 1, h: root.edge, a: false},
                {x: frame.width - root.corner - 1, y: 0, w: 1, h: root.edge, a: true},
                {x: frame.width - root.corner, y: 0, w: 1, h: root.edge, a: false},
                {x: root.corner - 1, y: frame.height - root.edge, w: 1, h: root.edge, a: true},
                {x: root.corner, y: frame.height - root.edge, w: 1, h: root.edge, a: false},
                {x: frame.width - root.corner - 1, y: frame.height - root.edge, w: 1, h: root.edge, a: true},
                {x: frame.width - root.corner, y: frame.height - root.edge, w: 1, h: root.edge, a: false},
                {x: 0, y: root.corner - 1, w: root.edge, h: 1, a: true},
                {x: 0, y: root.corner, w: root.edge, h: 1, a: false},
                {x: 0, y: frame.height - root.corner - 1, w: root.edge, h: 1, a: true},
                {x: 0, y: frame.height - root.corner, w: root.edge, h: 1, a: false},
                {x: frame.width - root.edge, y: root.corner - 1, w: root.edge, h: 1, a: true},
                {x: frame.width - root.edge, y: root.corner, w: root.edge, h: 1, a: false},
                {x: frame.width - root.edge, y: frame.height - root.corner - 1, w: root.edge, h: 1, a: true},
                {x: frame.width - root.edge, y: frame.height - root.corner, w: root.edge, h: 1, a: false}
            ]
            Rectangle {
                required property var modelData
                visible: root.edge >= 4
                x: modelData.x; y: modelData.y; width: modelData.w; height: modelData.h
                color: modelData.a ? root.borderShade.bottom : root.borderShade.top
            }
        }

        // Title bar and client sit together in a one-pixel sunken well, as
        // in mwm: dark on top and left, light at the bottom and right. Without
        // it the raised frame and the raised title parts run into each other.
        Item {
            x: root.edge - root.inner
            y: root.edge - root.inner
            width: frame.width - 2 * x
            height: frame.height - 2 * y
            visible: root.edge > root.inner
            Rectangle { width: parent.width; height: 1; color: root.borderShade.bottom }
            Rectangle { width: 1; height: parent.height; color: root.borderShade.bottom }
            Rectangle { y: parent.height - 1; width: parent.width; height: 1; color: root.borderShade.top; visible: !decoration.client.shaded }
            Rectangle { x: parent.width - 1; width: 1; height: parent.height; color: root.borderShade.top }
        }
    }
    // A maximized window keeps only its title bar, on the frame colour.
    Rectangle {
        anchors.fill: parent
        visible: root.maximized
        color: root.frameColor
    }

    // ---- title bar -------------------------------------------------------
    Item {
        id: titleRow
        x: root.maximized ? 0 : Math.max(root.edge, root.bevel)
        y: root.maximized ? 0 : Math.max(root.edge, root.bevel)
        width: parent.width - 2 * x
        height: root.titleHeight

        ButtonGroup {
            id: leftButtons
            spacing: 0
            explicitSpacer: root.titleHeight / 2
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
        Bevel {
            id: captionBar
            anchors { left: leftButtons.right; right: rightButtons.left; top: parent.top; bottom: parent.bottom }
            color: root.frameColor
            light: root.shade.top
            dark: root.shade.bottom
            thickness: root.bevel
            Text {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                text: decoration.client.caption
                textFormat: Text.PlainText
                font: options.titleFont
                color: root.inkColor
                elide: Text.ElideMiddle
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering
            }
        }
        ButtonGroup {
            id: rightButtons
            spacing: 0
            explicitSpacer: root.titleHeight / 2
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

    Component { id: menuButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonMenu; size: root.titleHeight } }
    Component { id: appMenuButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonApplicationMenu; size: root.titleHeight } }
    Component { id: minimizeButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonMinimize; size: root.titleHeight } }
    Component { id: maximizeButtonComponent; MotifButton { objectName: "maximizeButton"; buttonType: DecorationOptions.DecorationButtonMaximizeRestore; size: root.titleHeight } }
    Component { id: keepBelowButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonKeepBelow; size: root.titleHeight } }
    Component { id: keepAboveButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonKeepAbove; size: root.titleHeight } }
    Component { id: helpButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonQuickHelp; size: root.titleHeight } }
    Component { id: shadeButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonShade; size: root.titleHeight } }
    Component { id: allDesktopsButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonOnAllDesktops; size: root.titleHeight } }
    Component { id: closeButtonComponent; MotifButton { buttonType: DecorationOptions.DecorationButtonClose; size: root.titleHeight } }

    Component.onCompleted: {
        readBorderSize();
        readConfig();
    }
    Connections {
        target: decoration
        function onConfigChanged() { root.readConfig(); }
    }
    Connections {
        target: decorationSettings
        function onBorderSizeChanged() { root.readBorderSize(); }
    }
}
