import QtQuick
import org.kde.kwin.decoration

// One title-bar element in the Motif manner: a separately shadowed square.
// The glyphs are drawn with shadows too (mwm's raised bar and squares);
// only close, which mwm never had, and the rarer buttons use ink.
DecorationButton {
    id: button
    property real size
    property color face: root.frameColor
    property color ink: root.inkColor
    readonly property var shade: root.shade
    readonly property bool maximized: decoration.client.maximized
    readonly property bool down: pressed || (toggled && buttonType !== DecorationOptions.DecorationButtonMaximizeRestore)
    width: size
    height: size

    Bevel {
        anchors.fill: parent
        color: button.hovered && button.enabled ? button.shade.hover : button.face
        light: button.shade.top
        dark: button.shade.bottom
        sunken: button.down
        thickness: root.bevel
    }

    Item {
        id: glyph
        anchors.fill: parent
        anchors.leftMargin: button.down ? 1 : 0
        anchors.topMargin: button.down ? 1 : 0
        opacity: button.enabled ? 1 : 0.45
        readonly property real s: button.size

        // Window menu: mwm's horizontal raised bar.
        Bevel {
            visible: button.buttonType === DecorationOptions.DecorationButtonMenu
            width: Math.round(glyph.s * 0.56); height: Math.max(3, Math.round(glyph.s * 0.2))
            x: Math.round((glyph.s - width) / 2); y: Math.round((glyph.s - height) / 2)
            color: button.face; light: button.shade.top; dark: button.shade.bottom; thickness: 1
        }
        // Minimize: a small raised square.
        Bevel {
            visible: button.buttonType === DecorationOptions.DecorationButtonMinimize
            width: Math.max(3, Math.round(glyph.s * 0.24)); height: width
            x: Math.round((glyph.s - width) / 2); y: Math.round((glyph.s - height) / 2)
            color: button.face; light: button.shade.top; dark: button.shade.bottom; thickness: 1
        }
        // Maximize: a large raised square, pressed in while maximized.
        Bevel {
            visible: button.buttonType === DecorationOptions.DecorationButtonMaximizeRestore
            width: Math.round(glyph.s * 0.58); height: width
            x: Math.round((glyph.s - width) / 2); y: Math.round((glyph.s - height) / 2)
            color: button.face; light: button.shade.top; dark: button.shade.bottom; thickness: 1
            sunken: button.maximized
        }
        // Close: not part of mwm, drawn as a plain cross in the title ink.
        Item {
            visible: button.buttonType === DecorationOptions.DecorationButtonClose
            anchors.centerIn: parent
            width: Math.round(glyph.s * 0.46); height: width
            Rectangle { anchors.centerIn: parent; width: parent.width * 1.3; height: Math.max(2, Math.round(glyph.s / 12)); rotation: 45; color: button.ink; antialiasing: true }
            Rectangle { anchors.centerIn: parent; width: parent.width * 1.3; height: Math.max(2, Math.round(glyph.s / 12)); rotation: -45; color: button.ink; antialiasing: true }
        }
        Text {
            visible: text !== ""
            anchors.centerIn: parent
            color: button.ink
            font.pixelSize: Math.round(glyph.s * 0.55)
            font.bold: true
            text: {
                switch (button.buttonType) {
                case DecorationOptions.DecorationButtonOnAllDesktops: return "▣";
                case DecorationOptions.DecorationButtonKeepAbove: return "▴";
                case DecorationOptions.DecorationButtonKeepBelow: return "▾";
                case DecorationOptions.DecorationButtonShade: return "‒";
                case DecorationOptions.DecorationButtonQuickHelp: return "?";
                case DecorationOptions.DecorationButtonApplicationMenu: return "≡";
                default: return "";
                }
            }
        }
    }

    Component.onCompleted: {
        if (buttonType === DecorationOptions.DecorationButtonQuickHelp)
            visible = Qt.binding(() => decoration.client.providesContextHelp);
        if (buttonType === DecorationOptions.DecorationButtonApplicationMenu)
            visible = Qt.binding(() => decoration.client.hasApplicationMenu);
    }
}
