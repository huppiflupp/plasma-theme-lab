import QtQuick
import QtQuick.Effects
import org.kde.kwin.decoration
import org.kde.kirigami as Kirigami

// One title-bar button. The window menu button shows the program's icon
// (Warp 4; Warp 3 had a bar). The others in one of six looks (setting
// buttonStyle, root.buttonStyle), after the design sheet of 21.10.2026:
//  0 Warp 4:        raised grey square, cross, small and large square
//  1 glyphs only:   Warp 4's glyphs straight on the title row
//  2 diamond:       a raised square stood on its corner, fine glyphs
//  3 window corners: raised square; maximize as four corners
//  4 neon tube:     Neon: glowing glyphs, no body; classic: a flat frame
//  5 tile:          as the taskbar's buttons: a tile with an outline
// Neon draws the glyphs in every look as tube 4 does: cyan with a glow,
// close in pink.
DecorationButton {
    id: button
    property real size
    readonly property bool maximized: decoration.client.maximized
    readonly property bool down: pressed || (toggled && buttonType !== DecorationOptions.DecorationButtonMaximizeRestore)
    readonly property bool isMenu: buttonType === DecorationOptions.DecorationButtonMenu
    readonly property int look: root.buttonStyle
    readonly property bool neon: root.style.accent.a > 0
    readonly property string kind: buttonType === DecorationOptions.DecorationButtonClose ? "close"
        : buttonType === DecorationOptions.DecorationButtonMinimize ? "min"
        : buttonType === DecorationOptions.DecorationButtonMaximizeRestore ? (maximized ? "restore" : "max")
        : ""
    readonly property color ink: neon ? (kind === "close" ? root.style.accent : root.style.light) : root.style.glyph
    width: visible ? size : 0
    height: size

    // ---- the body ----------------------------------------------------
    Bevel {
        anchors.fill: parent
        visible: !button.isMenu && (button.look === 0 || button.look === 3
            || (button.kind === "" && button.look !== 1))
        color: root.surface
        light: root.style.light; dark: root.style.dark; ink: root.style.ink
        sunken: button.down
    }
    // Neon tube in classic: a flat frame, pressed in when down.
    Bevel {
        anchors.fill: parent
        visible: !button.isMenu && button.kind !== "" && button.look === 4 && !button.neon
        kind: "frame"; sunken: button.down
        color: root.surface
        light: root.style.light; dark: root.style.dark; ink: root.style.ink
    }
    // Tile: Neon after the taskbar (TaskTab.qml), classic grey with a line.
    Rectangle {
        anchors.fill: parent
        visible: !button.isMenu && button.kind !== "" && button.look === 5
        gradient: Gradient {
            GradientStop { position: 0; color: button.neon ? (button.down ? "#08112c" : "#12306e") : root.surface }
            GradientStop { position: 1; color: button.neon ? (button.down ? "#12306e" : "#08112c") : root.surface }
        }
        border.width: 1
        border.color: button.neon ? button.ink : root.style.ink
    }
    // Diamond: OS/2's raised edges along the four slanted sides.
    Canvas {
        id: diamond
        anchors.fill: parent
        visible: !button.isMenu && button.kind !== "" && button.look === 2
        readonly property var state: [button.down, button.size, root.surface, button.neon]
        onStateChanged: requestPaint()
        onPaint: {
            const c = getContext("2d");
            c.reset();
            const m = width / 2, r = width / 2 - 0.5;
            c.beginPath();
            c.moveTo(m, m - r); c.lineTo(m + r, m); c.lineTo(m, m + r); c.lineTo(m - r, m);
            c.closePath();
            c.fillStyle = root.surface;
            c.fill();
            const lit = String(root.style.light);
            const shade = String(button.neon ? root.style.dark : root.style.ink);
            c.lineWidth = button.neon ? 1.5 : 1;
            c.strokeStyle = button.down ? shade : lit;
            c.beginPath(); c.moveTo(m - r, m); c.lineTo(m, m - r); c.lineTo(m + r, m); c.stroke();
            c.strokeStyle = button.down ? lit : shade;
            c.beginPath(); c.moveTo(m + r, m); c.lineTo(m, m + r); c.lineTo(m - r, m); c.stroke();
            if (!button.neon) {
                c.strokeStyle = String(root.style.dark);
                c.beginPath(); c.moveTo(m + r - 1.5, m); c.lineTo(m, m + r - 1.5); c.lineTo(m - r + 1.5, m); c.stroke();
            }
        }
    }

    Kirigami.Icon {
        visible: button.isMenu
        anchors.centerIn: parent
        width: Math.round(button.size * 0.8); height: width
        source: decoration.client.icon
        roundToIconSize: false
    }

    // ---- the glyph ---------------------------------------------------
    Canvas {
        id: glyph
        visible: button.kind !== ""
        anchors.fill: parent
        anchors.leftMargin: button.down ? 1 : 0
        anchors.topMargin: button.down ? 1 : 0
        opacity: button.enabled ? 1 : 0.4
        readonly property var state: [button.kind, button.look, button.size, button.ink, root.surface, button.neon, button.down]
        onStateChanged: requestPaint()
        // Neon: the tube's glow around the glyph.
        layer.enabled: button.neon
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: button.ink
            shadowBlur: 0.7
            shadowOpacity: 1
            shadowHorizontalOffset: 0
            shadowVerticalOffset: 0
            blurMax: 8
        }
        onPaint: {
            const c = getContext("2d");
            c.reset();
            const s = Math.round(button.size);
            const ink = String(button.ink);
            const look = button.look;
            // the glyph set: Warp 4's (0, 1), the fine one (2, 4, 5) or the
            // corners (3); the diamond draws smaller, inside its edges
            const set = look === 3 ? "corners" : (look === 0 || look === 1) ? "warp" : "fine";
            const o = look === 2 ? 2 : 0, g = s - 2 * o;
            c.fillStyle = ink;
            c.strokeStyle = ink;
            const box = (x, y, w, h, top) => {
                c.fillRect(x, y, w, top); c.fillRect(x, y + h - 1, w, 1);
                c.fillRect(x, y, 1, h); c.fillRect(x + w - 1, y, 1, h);
            };
            const cross = (r, lw) => {
                c.lineWidth = lw;
                c.beginPath();
                c.moveTo(s / 2 - r, s / 2 - r); c.lineTo(s / 2 + r, s / 2 + r);
                c.moveTo(s / 2 + r, s / 2 - r); c.lineTo(s / 2 - r, s / 2 + r);
                c.stroke();
            };
            // the area behind a square in front (restore)
            const behind = String(look === 5 && button.neon ? "#0f2760" : root.surface);
            const kind = button.kind;
            if (set === "warp") {
                if (kind === "close") cross(Math.round(s * 0.25), Math.max(2, Math.round(s / 9)));
                else if (kind === "min") {
                    const w = Math.max(4, Math.round(s * 0.3));
                    box(Math.round((s - w) / 2), Math.round((s - w) / 2), w, w, 2);
                } else if (kind === "max") {
                    const w = Math.round(s * 0.6);
                    box(Math.round((s - w) / 2), Math.round((s - w) / 2), w, w, 2);
                } else {
                    const w = Math.round(s * 0.42), x = Math.round((s - w) / 2);
                    box(x + 2, x - 2, w, w, 2);
                    c.fillStyle = look === 1 ? "transparent" : behind;
                    if (look !== 1) c.fillRect(x - 2, x + 2, w, w);
                    c.fillStyle = ink;
                    box(x - 2, x + 2, w, w, 2);
                }
            } else if (set === "fine") {
                const m = o + Math.round(g * 0.28);
                if (kind === "close") cross(Math.round(g * 0.22), 1.2);
                else if (kind === "min") c.fillRect(m, s - m - 1, s - 2 * m, 1);
                else if (kind === "max") box(m, m, s - 2 * m, s - 2 * m, 1);
                else {
                    const w = Math.round(g * 0.36), x = Math.round((s - w) / 2);
                    box(x + 2, x - 2, w, w, 1);
                    if (look !== 4) { c.fillStyle = behind; c.fillRect(x - 2, x + 2, w, w); c.fillStyle = ink; }
                    box(x - 2, x + 2, w, w, 1);
                }
            } else {
                // corners
                const a = Math.round(s * 0.22), b = s - 1 - a, L = Math.max(3, Math.round(s * 0.22));
                if (kind === "close") cross(Math.round(s * 0.22), 1.5);
                else if (kind === "min") {
                    const y = s - a - 1;
                    c.fillRect(a + 1, y, s - 2 * a - 2, 1);
                    c.fillRect(a + 1, y - 2, 1, 3); c.fillRect(s - a - 2, y - 2, 1, 3);
                } else {
                    // max: corners pointing out; restore: pointing in
                    const out = kind === "max";
                    const p = out ? [a, b] : [a + L - 1, b - L + 1];
                    for (const [x, y, dx, dy] of [[p[0], p[0], 1, 1], [p[1], p[0], -1, 1], [p[0], p[1], 1, -1], [p[1], p[1], -1, -1]]) {
                        const sx = out ? dx : -dx, sy = out ? dy : -dy;
                        c.fillRect(Math.min(x, x + sx * (L - 1)), y, L, 1);
                        c.fillRect(x, Math.min(y, y + sy * (L - 1)), 1, L);
                    }
                }
            }
        }
    }
    Text {
        visible: button.kind === "" && !button.isMenu && text !== ""
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: button.down ? 1 : 0
        anchors.verticalCenterOffset: button.down ? 1 : 0
        opacity: button.enabled ? 1 : 0.4
        color: button.ink
        font.pixelSize: Math.round(button.size * 0.55)
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

    Component.onCompleted: {
        if (buttonType === DecorationOptions.DecorationButtonQuickHelp)
            visible = Qt.binding(() => decoration.client.providesContextHelp);
        if (buttonType === DecorationOptions.DecorationButtonApplicationMenu)
            visible = Qt.binding(() => decoration.client.hasApplicationMenu);
    }
}
