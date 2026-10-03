import QtQuick
import "motif.js" as Motif

// The clock tile's face, sized to whatever room the tile has: every size is
// taken from the face's own width and height, so it shrinks with the console
// (75 %) and fits the upright console.
//
//   style  "digital"   day, time and date in type
//          "segments"  a seven-segment time, unlit segments faintly visible
//          "analog"    hands on a dial:
//   dial   "cde"       round, after CDE's front-panel clock (dtclock)
//          "motif"     square, a sunken Motif well with hour bars
//          "roman"     round with Roman numerals
//          "plain"     no dial, four marks on the tile itself
Item {
    id: face
    property string style: "digital"
    property string dial: "cde"
    property bool seconds: false
    property bool segmentEdge: false     // black edge round lit segments
    property bool segmentShadow: true    // unlit segments faintly drawn
    property date now: new Date()
    property color ink: "black"          // text, hands, marks
    property real dim: 0.8               // the weekday, a little quieter
    property bool bold: false            // semibold date and weekday
    property color accent: "orange"      // second hand, lit segments
    property color dialColor: "white"    // the dial's surface
    property color tile: "gray"          // the tile around it
    property string font: "IBM Plex Sans Condensed"

    readonly property real small: Math.max(6, Math.min(height * 0.16, width / 6.5))

    // ---- digital ------------------------------------------------------
    Column {
        visible: face.style === "digital"
        anchors.centerIn: parent
        spacing: 0
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDateTime(face.now, "ddd").toUpperCase()
            color: face.ink; opacity: face.dim
            font.pixelSize: face.small; font.family: face.font; font.weight: face.bold ? Font.DemiBold : Font.Normal
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDateTime(face.now, face.seconds ? "HH:mm:ss" : "HH:mm")
            color: face.ink
            // Mono digits are 0.6 em wide: n characters need 0.6·n em.
            font.pixelSize: Math.max(7, Math.min(face.height * 0.42, face.width / ((face.seconds ? 8 : 5) * 0.62)))
            font.family: "IBM Plex Mono"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDateTime(face.now, "dd MMM").toUpperCase()
            color: face.ink
            font.pixelSize: face.small; font.family: face.font; font.weight: face.bold ? Font.DemiBold : Font.Normal
        }
    }

    // ---- seven segments -----------------------------------------------
    // Drawn on whole pixels only: integer canvas size and position, and every
    // segment an axis-aligned rectangle on the pixel grid. Bevelled segment
    // tips and a canvas at fractional size or position were smoothed by the
    // renderer, which at 125 % gave blurred segments with a dark fringe.
    Item {
        id: segmentsFace
        visible: face.style === "segments"
        anchors.fill: parent
        readonly property bool showDate: face.height > 40
        readonly property int dateHeight: showDate ? Math.ceil(face.small * 1.3) : 0
        readonly property int gapBelow: showDate ? Math.round(face.height * 0.05) : 0
        // Proportions of one digit cell, scaled from its height h.
        readonly property int digits: face.seconds ? 6 : 4
        readonly property int colons: face.seconds ? 2 : 1
        function geometry(h) {
            // Small digits draw one-pixel strokes; every segment keeps at
            // least three pixels between its one-pixel gaps (h >= 9).
            const t = h < 14 ? 1 : Math.max(2, Math.round(h * 0.09));   // stroke
            const w = Math.max(2 * t + 3, Math.round(h * 0.5));         // digit width
            const s = Math.max(1, Math.round(h * 0.1));           // digit spacing
            return {t: t, w: w, s: s, width: digits * w + (digits - 1) * s + colons * (t + s)};
        }
        // The largest digit height that fits the room, in whole pixels.
        readonly property int digitHeight: {
            let h = Math.max(9, Math.floor(Math.min(face.height - dateHeight - gapBelow, face.height * 0.62)));
            while (h > 9 && geometry(h).width + 2 > face.width) h--;
            return h;
        }
        readonly property var g: geometry(digitHeight)

        Canvas {
            id: segments
            // One pixel extra all round for the outline of the lit segments.
            width: segmentsFace.g.width + 2
            height: segmentsFace.digitHeight + 2
            x: Math.round((segmentsFace.width - width) / 2)
            y: Math.round((segmentsFace.height - height - segmentsFace.dateHeight - segmentsFace.gapBelow) / 2)
            antialiasing: false
            readonly property string text: Qt.formatDateTime(face.now, face.seconds ? "HHmmss" : "HHmm")
            onTextChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: face
                function onInkChanged() { segments.requestPaint(); }
                function onAccentChanged() { segments.requestPaint(); }
                function onSegmentEdgeChanged() { segments.requestPaint(); }
                function onSegmentShadowChanged() { segments.requestPaint(); }
            }
            // Segments a..g of a digit, as in the usual naming.
            readonly property var lit: ["abcdef", "bc", "abdeg", "abcdg", "bcfg", "acdfg", "acdefg", "abc", "abcdefg", "abcdfg"]
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                const geo = segmentsFace.g, h = segmentsFace.digitHeight, t = geo.t, w = geo.w;
                ctx.translate(1, 1);
                // Segments end one pixel short of each other, so they read as
                // separate bars, as on an LCD.
                const gap = 1;
                const mid = Math.round((h - t) / 2);
                const on = face.accent.toString();
                const off = Qt.rgba(face.ink.r, face.ink.g, face.ink.b, 0.13).toString();
                // Optionally, lit segments get a thin black edge, a pixel wide at every
                // size; it falls into the gap between segments, so it never
                // covers a neighbour.
                const edge = "black";
                function rect(x, y, rw, rh, grow) {
                    ctx.fillRect(x - grow, y - grow, rw + 2 * grow, rh + 2 * grow);
                }
                function digit(x, value, lit, grow) {
                    const segs = segments.lit[value];
                    const inner = w - 2 * t;                  // horizontal bar length
                    const upper = mid - t, lower = h - t - mid - t;
                    const parts = {
                        a: [x + t, 0, inner, t, true], g: [x + t, mid, inner, t, true], d: [x + t, h - t, inner, t, true],
                        f: [x, t, t, upper, false], b: [x + w - t, t, t, upper, false],
                        e: [x, mid + t, t, lower, false], c: [x + w - t, mid + t, t, lower, false]
                    };
                    ctx.fillStyle = grow ? edge : lit ? on : off;
                    for (const key in parts) {
                        if ((segs.indexOf(key) >= 0) !== lit) continue;
                        const p = parts[key];
                        // Shortened by the gap at both ends; from a 3-pixel
                        // stroke on, the ends are cut back a pixel at the
                        // edges - a bevelled tip that stays on the grid.
                        const horizontal = p[4];
                        const x0 = horizontal ? p[0] + gap : p[0], y0 = horizontal ? p[1] : p[1] + gap;
                        const len = (horizontal ? p[2] : p[3]) - 2 * gap;
                        const cut = t >= 3 ? 1 : 0;
                        if (horizontal) {
                            rect(x0 + cut, y0, len - 2 * cut, t, grow);
                            if (cut) rect(x0, y0 + 1, len, t - 2, grow);
                        } else {
                            rect(x0, y0 + cut, t, len - 2 * cut, grow);
                            if (cut) rect(x0 + 1, y0, t - 2, len, grow);
                        }
                    }
                }
                // Unlit segments, then the edges of the lit ones, then the lit.
                const passes = (face.segmentShadow ? [[false, 0]] : []).concat(face.segmentEdge ? [[true, 1], [true, 0]] : [[true, 0]]);
                for (const pass of passes) {
                    const lit = pass[0], grow = pass[1];
                    let x = 0;
                    for (let i = 0; i < text.length; i++) {
                        digit(x, Number(text[i]), lit, grow);
                        x += w + geo.s;
                        if (i % 2 === 1 && i < text.length - 1) {
                            // Colon: two square dots, a stroke wide, with one
                            // spacing on either side (as in geometry()).
                            if (lit) {
                                ctx.fillStyle = grow ? edge : on;
                                rect(x, Math.round(h * 0.28), t, t, grow);
                                rect(x, Math.round(h * 0.72) - t, t, t, grow);
                            }
                            x += t + geo.s;
                        }
                    }
                }
            }
        }
        Text {
            visible: segmentsFace.showDate
            x: Math.round((segmentsFace.width - width) / 2)
            y: segments.y + segments.height + segmentsFace.gapBelow
            text: Qt.formatDateTime(face.now, "ddd dd MMM").toUpperCase()
            color: face.ink
            font.pixelSize: face.small; font.family: face.font; font.weight: face.bold ? Font.DemiBold : Font.Normal
        }
    }

    // ---- analog -------------------------------------------------------
    Canvas {
        id: analog
        visible: face.style === "analog"
        readonly property real side: Math.min(face.width, face.height)
        width: side; height: side
        anchors.centerIn: parent
        readonly property int stamp: face.now.getHours() * 3600 + face.now.getMinutes() * 60 + (face.seconds ? face.now.getSeconds() : 0)
        onStampChanged: requestPaint()
        onSideChanged: requestPaint()
        Connections {
            target: face
            function onDialChanged() { analog.requestPaint(); }
            function onInkChanged() { analog.requestPaint(); }
            function onDialColorChanged() { analog.requestPaint(); }
            function onAccentChanged() { analog.requestPaint(); }
            function onStyleChanged() { analog.requestPaint(); }
        }
        onPaint: {
            if (face.style !== "analog") return;
            const ctx = getContext("2d");
            ctx.reset();
            const s = side, c = s / 2, r = s / 2 - 1;
            const shade = Motif.shades(face.dialColor);
            const ink = face.ink.toString(), accent = face.accent.toString();

            function line(angle, from, to, width, colour) {
                ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.lineCap = "butt";
                ctx.beginPath();
                ctx.moveTo(c + Math.sin(angle) * from, c - Math.cos(angle) * from);
                ctx.lineTo(c + Math.sin(angle) * to, c - Math.cos(angle) * to);
                ctx.stroke();
            }
            function hand(angle, length, width, tail, colour) {
                // A flat Motif hand: a long, slightly tapered bar.
                ctx.fillStyle = colour;
                ctx.save();
                ctx.translate(c, c);
                ctx.rotate(angle);
                ctx.beginPath();
                ctx.moveTo(-width / 2, tail); ctx.lineTo(-width * 0.35, -length);
                ctx.lineTo(width * 0.35, -length); ctx.lineTo(width / 2, tail);
                ctx.closePath();
                ctx.fill();
                ctx.restore();
            }

            if (face.dial === "motif") {
                // A square, sunken well with hour bars.
                const b = Math.max(1, Math.round(s / 24));
                ctx.fillStyle = face.dialColor.toString(); ctx.fillRect(0, 0, s, s);
                ctx.fillStyle = shade.bottom.toString(); ctx.fillRect(0, 0, s, b); ctx.fillRect(0, 0, b, s);
                ctx.fillStyle = shade.top.toString(); ctx.fillRect(0, s - b, s, b); ctx.fillRect(s - b, 0, b, s);
                for (let i = 0; i < 12; i++)
                    line(i * Math.PI / 6, r * (i % 3 === 0 ? 0.62 : 0.74), r * 0.88, Math.max(1, s / (i % 3 === 0 ? 22 : 40)), ink);
            } else if (face.dial === "plain") {
                for (let i = 0; i < 4; i++)
                    line(i * Math.PI / 2, r * 0.78, r * 0.98, Math.max(1.5, s / 26), ink);
            } else {
                // Round: raised rim, dial, minute and hour ticks.
                ctx.fillStyle = shade.top.toString();
                ctx.beginPath(); ctx.arc(c, c, r, Math.PI * 0.75, Math.PI * 1.75); ctx.fill();
                ctx.fillStyle = shade.bottom.toString();
                ctx.beginPath(); ctx.arc(c, c, r, Math.PI * 1.75, Math.PI * 2.75); ctx.fill();
                ctx.fillStyle = face.dialColor.toString();
                ctx.beginPath(); ctx.arc(c, c, r - Math.max(1.5, s / 28), 0, 2 * Math.PI); ctx.fill();
                if (face.dial === "roman") {
                    const numerals = ["XII", "III", "VI", "IX"];
                    ctx.fillStyle = ink;
                    ctx.font = "600 " + Math.max(5, Math.round(s * 0.15)) + "px '" + face.font + "'";
                    ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    for (let i = 0; i < 4; i++) {
                        const a = i * Math.PI / 2;
                        ctx.fillText(numerals[i], c + Math.sin(a) * r * 0.68, c - Math.cos(a) * r * 0.68);
                    }
                    for (let i = 0; i < 12; i++)
                        if (i % 3 !== 0) line(i * Math.PI / 6, r * 0.74, r * 0.86, Math.max(1, s / 40), ink);
                } else {
                    for (let i = 0; i < 60; i++) {
                        if (s < 48 && i % 5 !== 0) continue;   // too small for minute ticks
                        line(i * Math.PI / 30, r * (i % 5 === 0 ? 0.72 : 0.82), r * 0.88,
                             Math.max(1, s / (i % 15 === 0 ? 22 : i % 5 === 0 ? 34 : 70)), ink);
                    }
                }
            }
            const h = face.now.getHours() % 12, m = face.now.getMinutes(), sec = face.now.getSeconds();
            hand((h + m / 60) * Math.PI / 6, r * 0.5, Math.max(2, s / 13), r * 0.08, ink);
            hand((m + (face.seconds ? sec / 60 : 0)) * Math.PI / 30, r * 0.78, Math.max(1.5, s / 18), r * 0.08, ink);
            if (face.seconds) {
                line(sec * Math.PI / 30, -r * 0.15, r * 0.84, Math.max(1, s / 60), accent);
            }
            ctx.fillStyle = face.seconds ? accent : ink;
            ctx.beginPath(); ctx.arc(c, c, Math.max(1.5, s / 28), 0, 2 * Math.PI); ctx.fill();
        }
    }
}
