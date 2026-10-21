import QtQuick
import org.kde.kwin.decoration

// Warp Legacy window frame, after OS/2 Warp 4 (DESIGN.md §3):
//  - a grey sizing border with OS/2's fixed edges, white outside, grey inside;
//  - in the title row the window menu (the program's icon) on the left, the
//    buttons on the right (close, hide, maximize: the order comes from
//    kwinrc, set by the global theme); between them the title bar, inset
//    with a gap of surface grey, not reaching under the buttons;
//  - colours from the colour scheme: the title bar is the WM title colour,
//    the frame the Window background; the edges and the Neon variant's glow
//    from Style.qml, which build.py writes per variant.
Decoration {
    id: root
    alpha: style.glowWidth > 0

    // Referred to as root.style by WarpButton.
    readonly property Style style: Style {}

    DecorationOptions { id: options; deco: decoration }
    FontMetrics { id: metrics; font: options.titleFont }
    SystemPalette { id: system; colorGroup: SystemPalette.Active }

    property int fixedTitleHeight: 0
    // The buttons' look (WarpButton.qml): 0 Warp 4, 1 glyphs only, 2 diamond,
    // 3 window corners, 4 neon tube, 5 tile.
    property int buttonStyle: 0
    property int edge: 4
    readonly property int gap: 2
    readonly property bool maximized: decoration.client.maximized
    readonly property int titleHeight: fixedTitleHeight > 0 ? Math.max(12, fixedTitleHeight) : Math.max(18, Math.ceil(metrics.height) + 4)
    readonly property int buttonSize: titleHeight - 2
    readonly property color surface: system.window
    readonly property color titleColor: options.titleBarColor
    readonly property color inkColor: options.fontColor
    // The glow lies in the padding outside the frame, where Aurorae draws
    // the window's shadow; a maximized window has none.
    readonly property int glow: root.maximized ? 0 : style.glowWidth
    onGlowChanged: setPadding()
    function setPadding() {
        padding.left = root.glow; padding.top = root.glow;
        padding.right = root.glow; padding.bottom = root.glow;
    }

    function readBorderSize() {
        let side = 4;
        switch (decorationSettings.borderSize) {
        case DecorationOptions.BorderNone: side = 0; break;
        case DecorationOptions.BorderNoSides: side = 0; break;
        case DecorationOptions.BorderTiny: side = 3; break;
        case DecorationOptions.BorderLarge: side = 6; break;
        case DecorationOptions.BorderVeryLarge: side = 8; break;
        case DecorationOptions.BorderHuge: side = 12; break;
        case DecorationOptions.BorderVeryHuge: side = 16; break;
        case DecorationOptions.BorderOversized: side = 22; break;
        }
        root.edge = side;
        borders.setBorders(side);
        if (decorationSettings.borderSize === DecorationOptions.BorderNoSides) {
            borders.setSideBorders(0);
            borders.bottom = 0;
        }
        borders.setTitle(Math.max(side, 2) + root.titleHeight + 1);
        maximizedBorders.setTitle(root.titleHeight + 1);
        extendedBorders.setAllBorders(Math.max(0, 6 - side));
    }
    function readConfig() {
        root.fixedTitleHeight = decoration.readConfig("titleHeight", 0);
        root.buttonStyle = decoration.readConfig("buttonStyle", 0);
    }
    onTitleHeightChanged: readBorderSize()
    // The theme's settings dialog (config.ui) saves without telling KWin:
    // open windows kept their old buttons, only new ones took the change
    // (VM, 21.10.2026). Read again now and then; nothing redraws unless a
    // value changed.
    Timer { interval: 2000; running: true; repeat: true; onTriggered: root.readConfig() }

    // ---- glow ------------------------------------------------------------
    // Rings fading outwards, strongest at the frame: neon light on the desktop.
    Repeater {
        model: root.glow
        Rectangle {
            required property int index
            readonly property int n: index + 1
            x: root.glow - n; y: root.glow - n
            width: parent.width - 2 * x; height: parent.height - 2 * y
            color: "transparent"
            border.width: 1
            border.color: style.glow
            opacity: 0.55 * Math.pow(1 - index / root.glow, 2)
        }
    }

    // Everything but the glow: the window with its frame.
    Item {
    id: area
    x: root.glow; y: root.glow
    width: parent.width - 2 * root.glow
    height: parent.height - 2 * root.glow

    // ---- frame -----------------------------------------------------------
    Rectangle {
        anchors.fill: parent
        color: root.surface
    }
    // Neon (an accent colour in Style.qml): gradient edges with pink towards
    // the bottom right instead of OS/2's two flat colours.
    readonly property bool neon: style.accent.a > 0
    NeonFrame {
        anchors.fill: parent
        visible: area.neon && !root.maximized && root.edge > 0
        light: style.light; dark: style.dark; accent: style.accent
        NeonFrame {
            x: root.edge - 1; y: root.edge - 1
            width: parent.width - 2 * x; height: parent.height - 2 * y
            visible: root.edge > 1
            opacity: 0.6
            light: style.light; dark: style.dark; accent: style.accent
        }
    }
    Bevel {
        anchors.fill: parent
        visible: !area.neon && !root.maximized && root.edge > 0
        kind: "frame"
        light: style.light; dark: style.dark; ink: style.ink
        color: root.surface
        // A second, inner line: grey at the top and left, white at the bottom
        // and right, where the border meets the window.
        Bevel {
            x: root.edge - 1; y: root.edge - 1
            width: parent.width - 2 * x; height: parent.height - 2 * y
            visible: root.edge > 1
            kind: "frame"; sunken: true
            light: style.light; dark: style.dark; ink: style.ink
            color: "transparent"
        }
    }

    // ---- title row -------------------------------------------------------
    Item {
        id: titleRow
        x: root.maximized ? 0 : Math.max(root.edge, 2)
        y: root.maximized ? 0 : Math.max(root.edge, 2)
        width: parent.width - 2 * x
        height: root.titleHeight

        ButtonGroup {
            id: leftButtons
            spacing: 1
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
            anchors { left: parent.left; leftMargin: 1; top: parent.top; topMargin: 1 }
        }
        Rectangle {
            id: captionBar
            anchors {
                left: leftButtons.right; leftMargin: root.gap
                right: rightButtons.left; rightMargin: root.gap + 1
                top: parent.top; bottom: parent.bottom
            }
            color: root.titleColor
            Text {
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                text: decoration.client.caption
                textFormat: Text.PlainText
                font: options.titleFont
                color: root.inkColor
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering
            }
        }
        ButtonGroup {
            id: rightButtons
            spacing: 1
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
            anchors { right: parent.right; rightMargin: 1; top: parent.top; topMargin: 1 }
        }
        Component.onCompleted: decoration.installTitleItem(titleRow)
    }
    // The line between the title row and the window; in Neon a streak of
    // light from cyan through pink, fading out to the right as the
    // concept's (reference/neon-2026.png, "Workplace Shell - Desktop").
    Rectangle {
        x: titleRow.x; y: titleRow.y + titleRow.height
        width: titleRow.width; height: 1
        color: style.dark
        gradient: area.neon ? streak : null
        Gradient {
            id: streak
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: style.light }
            GradientStop { position: 0.35; color: style.accent }
            GradientStop { position: 0.7; color: style.dark }
            GradientStop { position: 1.0; color: Qt.rgba(style.dark.r, style.dark.g, style.dark.b, 0.25) }
        }
    }
    }

    Component { id: menuButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonMenu; size: root.buttonSize } }
    Component { id: appMenuButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonApplicationMenu; size: root.buttonSize } }
    Component { id: minimizeButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonMinimize; size: root.buttonSize } }
    Component { id: maximizeButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonMaximizeRestore; size: root.buttonSize } }
    Component { id: keepBelowButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonKeepBelow; size: root.buttonSize } }
    Component { id: keepAboveButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonKeepAbove; size: root.buttonSize } }
    Component { id: helpButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonQuickHelp; size: root.buttonSize } }
    Component { id: shadeButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonShade; size: root.buttonSize } }
    Component { id: allDesktopsButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonOnAllDesktops; size: root.buttonSize } }
    Component { id: closeButtonComponent; WarpButton { buttonType: DecorationOptions.DecorationButtonClose; size: root.buttonSize } }

    Component.onCompleted: {
        readBorderSize();
        readConfig();
        setPadding();
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
