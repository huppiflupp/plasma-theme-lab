import QtQuick
import org.kde.kwin.decoration

// One window tool. RISC OS has four in the title row: Back (here KWin's
// "keep below", the nearest it has), Close, Iconise (minimize) and Toggle
// size (maximize). Pressed, the Wimp shows the tool's pressed sprite;
// held toggles (keep below) stay pressed. Other KWin buttons borrow the
// nearest picture.
DecorationButton {
    id: button
    readonly property string picture: {
        switch (buttonType) {
        case DecorationOptions.DecorationButtonClose: return "close";
        case DecorationOptions.DecorationButtonMinimize: return "iconise";
        case DecorationOptions.DecorationButtonMaximizeRestore: return "toggle";
        case DecorationOptions.DecorationButtonKeepBelow: return "back";
        case DecorationOptions.DecorationButtonKeepAbove: return "back";
        case DecorationOptions.DecorationButtonShade: return "iconise";
        default: return "toggle";
        }
    }
    readonly property bool down: pressed || toggled
    width: visible ? root.tool : 0
    height: root.tool

    Image {
        anchors.fill: parent
        source: root.art((button.down ? "p" : "") + button.picture)
        smooth: false
    }
}
