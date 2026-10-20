import QtQuick
import org.kde.kwin.decoration
import org.kde.kirigami as Kirigami

// One title-bar button after Warp 4: a raised grey square with a dark
// glyph, no hover colour. The window menu button shows the program's
// icon instead (Warp 4; Warp 3 had a bar).
DecorationButton {
    id: button
    property real size
    readonly property bool maximized: decoration.client.maximized
    readonly property bool down: pressed || (toggled && buttonType !== DecorationOptions.DecorationButtonMaximizeRestore)
    readonly property bool isMenu: buttonType === DecorationOptions.DecorationButtonMenu
    width: visible ? size : 0
    height: size

    Bevel {
        anchors.fill: parent
        visible: !button.isMenu
        color: root.surface
        light: root.style.light; dark: root.style.dark; ink: root.style.ink
        sunken: button.down
    }
    Kirigami.Icon {
        visible: button.isMenu
        anchors.centerIn: parent
        width: Math.round(button.size * 0.8); height: width
        source: decoration.client.icon
        roundToIconSize: false
    }

    Item {
        id: glyph
        visible: !button.isMenu
        anchors.fill: parent
        anchors.leftMargin: button.down ? 1 : 0
        anchors.topMargin: button.down ? 1 : 0
        opacity: button.enabled ? 1 : 0.4
        readonly property real s: button.size
        readonly property color ink: root.style.glyph

        // Minimize (OS/2 "hide"): a small hollow square.
        Rectangle {
            visible: button.buttonType === DecorationOptions.DecorationButtonMinimize
            width: Math.max(4, Math.round(glyph.s * 0.3)); height: width
            x: Math.round((glyph.s - width) / 2); y: Math.round((glyph.s - height) / 2)
            color: "transparent"; border.color: glyph.ink; border.width: 1
            Rectangle { x: 1; y: 1; width: parent.width - 2; height: 1; color: glyph.ink }
        }
        // Maximize: a large hollow square with a heavy top; restore: two.
        Repeater {
            model: button.buttonType !== DecorationOptions.DecorationButtonMaximizeRestore ? 0
                 : button.maximized ? 2 : 1
            Rectangle {
                required property int index
                readonly property real side: Math.round(glyph.s * (button.maximized ? 0.42 : 0.6))
                width: side; height: side
                x: Math.round((glyph.s - side) / 2) + (button.maximized ? (index ? -2 : 2) : 0)
                y: Math.round((glyph.s - side) / 2) + (button.maximized ? (index ? 2 : -2) : 0)
                color: root.surface; border.color: glyph.ink; border.width: 1
                Rectangle { x: 1; y: 1; width: parent.width - 2; height: 1; color: glyph.ink }
            }
        }
        // Close: Warp 4's cross, two strokes with a light edge.
        Item {
            visible: button.buttonType === DecorationOptions.DecorationButtonClose
            anchors.centerIn: parent
            width: Math.round(glyph.s * 0.5); height: width
            Repeater {
                model: [45, -45]
                Rectangle {
                    required property var modelData
                    anchors.centerIn: parent
                    width: parent.width * 1.35; height: Math.max(2, Math.round(glyph.s / 9))
                    rotation: modelData; color: glyph.ink; antialiasing: true
                }
            }
        }
        Text {
            visible: text !== ""
            anchors.centerIn: parent
            color: glyph.ink
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
