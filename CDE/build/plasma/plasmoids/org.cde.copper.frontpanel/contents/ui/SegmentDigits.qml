import QtQuick

// A row of seven-segment digits for the console's readouts (the session
// block's LED field), drawn like the clock's segment face: whole pixels,
// unlit segments faintly shown. A space is a digit with nothing lit.
Canvas {
    id: digits
    property string text: ""
    property int digitHeight: 12
    property color accent: "orange"     // lit segments
    property color ink: "black"         // unlit segments, faintly
    property bool shadow: true

    // Proportions as ClockFace.qml's geometry().
    readonly property int t: digitHeight < 14 ? 1 : Math.max(2, Math.round(digitHeight * 0.09))
    readonly property int w: Math.max(2 * t + 3, Math.round(digitHeight * 0.5))
    readonly property int s: Math.max(1, Math.round(digitHeight * 0.1))
    width: text.length * w + Math.max(0, text.length - 1) * s
    height: digitHeight
    antialiasing: false
    onTextChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onAccentChanged: requestPaint()
    onInkChanged: requestPaint()
    readonly property var lit: ["abcdef", "bc", "abdeg", "abcdg", "bcfg", "acdfg", "acdefg", "abc", "abcdefg", "abcdfg"]
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        const h = digitHeight, gap = 1, cut = t >= 3 ? 1 : 0;
        const mid = Math.round((h - t) / 2);
        const on = accent.toString();
        const off = Qt.rgba(ink.r, ink.g, ink.b, 0.13).toString();
        for (const pass of shadow ? [false, true] : [true]) {
            ctx.fillStyle = pass ? on : off;
            for (let i = 0; i < text.length; i++) {
                const x = i * (w + s);
                const segs = text[i] === " " ? "" : lit[Number(text[i])] || "";
                const inner = w - 2 * t, upper = mid - t, lower = h - t - mid - t;
                const parts = {
                    a: [x + t, 0, inner, t, true], g: [x + t, mid, inner, t, true], d: [x + t, h - t, inner, t, true],
                    f: [x, t, t, upper, false], b: [x + w - t, t, t, upper, false],
                    e: [x, mid + t, t, lower, false], c: [x + w - t, mid + t, t, lower, false]
                };
                for (const key in parts) {
                    if ((segs.indexOf(key) >= 0) !== pass) continue;
                    const p = parts[key];
                    if (p[4]) {
                        ctx.fillRect(p[0] + gap + cut, p[1], p[2] - 2 * gap - 2 * cut, t);
                        if (cut) ctx.fillRect(p[0] + gap, p[1] + 1, p[2] - 2 * gap, t - 2);
                    } else {
                        ctx.fillRect(p[0], p[1] + gap + cut, t, p[3] - 2 * gap - 2 * cut);
                        if (cut) ctx.fillRect(p[0] + 1, p[1] + gap, t - 2, p[3] - 2 * gap);
                    }
                }
            }
        }
    }
}
