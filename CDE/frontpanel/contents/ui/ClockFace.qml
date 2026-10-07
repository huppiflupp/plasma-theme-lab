import QtQuick
import "motif.js" as Motif

// The clock tile's face, sized to whatever room the tile has: every size is
// taken from the face's own width and height, so it shrinks with the console
// (75 %) and fits the upright console.
//
//   style  "digital"   day, time and date in type
//          "segments"  a seven-segment time, unlit segments faintly visible
//          "ledmatrix" "flipclock" "vfd" "vfd-blue" "vfd-aqua" "flipdisc"
//          "panaplex" "panaplex-palette" "odometer" "pixel" "plasma"
//                      displays of their own kind, each in the colours of
//                      the real thing (red LEDs, blue-green phosphor ...);
//                      "pixel" and "panaplex-palette" take the palette
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
    property color lamp: "orange"        // the palette's glow, never swapped
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


    // ---- displays -----------------------------------------------------
    // Ten display types on one canvas. Everything scales from the room the
    // face has; the date goes below the time as with the segments.
    Item {
        id: displaysFace
        readonly property var kinds: ["ledmatrix", "flipclock", "vfd", "vfd-blue", "vfd-aqua", "flipdisc", "panaplex", "panaplex-palette", "odometer", "pixel", "plasma"]
        visible: kinds.indexOf(face.style) >= 0
        anchors.fill: parent
        readonly property bool showDate: face.height > 40
        readonly property int dateHeight: showDate ? Math.ceil(face.small * 1.3) : 0
        readonly property int gapBelow: showDate ? Math.round(face.height * 0.05) : 0
        Canvas {
            id: display
            width: Math.max(8, displaysFace.width)
            height: Math.max(8, displaysFace.height - displaysFace.dateHeight - displaysFace.gapBelow)
            x: 0; y: 0
            readonly property string text: Qt.formatDateTime(face.now, face.seconds ? "HHmmss" : "HHmm")
            onTextChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: face
                function onStyleChanged() { display.requestPaint(); }
                function onInkChanged() { display.requestPaint(); }
                function onAccentChanged() { display.requestPaint(); }
                function onDialColorChanged() { display.requestPaint(); }
                function onLampChanged() { display.requestPaint(); }
            }
            // Panaplex glowing in the palette's selection colour: the gas lit
            // bright enough to glow even under a dark palette, a whiter core,
            // the glass behind it nearly black with a trace of the hue.
            function paletteLook() {
                const c = Qt.color(face.lamp);
                const hue = Math.max(0, c.hslHue), sat = Math.max(0, c.hslSaturation), light = c.hslLightness;
                function hsla(hh, ss, ll, a) {
                    const q = Qt.hsla(hh, Math.min(1, ss), Math.max(0, Math.min(1, ll)), 1);
                    return "rgba(" + Math.round(q.r * 255) + "," + Math.round(q.g * 255) + "," + Math.round(q.b * 255) + "," + a + ")";
                }
                const on = Math.max(0.55, Math.min(0.68, light)), vivid = Math.max(0.6, sat);
                return {bg: hsla(hue, sat * 0.5, 0.04, 1), bezel: hsla(hue, sat * 0.4, 0.14, 1),
                        on: hsla(hue, vivid, on, 1), off: hsla(hue, vivid, on, 0.12),
                        core: hsla(hue, vivid * 0.6, Math.min(0.9, on + 0.25), 1),
                        blur: 0.12, passes: 2, grid: false};
            }
            readonly property var seg7: ["abcdef", "bc", "abdeg", "abcdg", "bcfg", "acdfg", "acdefg", "abc", "abcdefg", "abcdfg"]
            readonly property var dots: [
                ["01110","10001","10011","10101","11001","10001","01110"], ["00100","01100","00100","00100","00100","00100","01110"],
                ["01110","10001","00001","00010","00100","01000","11111"], ["11111","00010","00100","00010","00001","10001","01110"],
                ["00010","00110","01010","10010","11111","00010","00010"], ["11111","10000","11110","00001","00001","10001","01110"],
                ["00110","01000","10000","11110","10001","10001","01110"], ["11111","00001","00010","00100","01000","01000","01000"],
                ["01110","10001","10001","01110","10001","10001","01110"], ["01110","10001","10001","01111","00001","00010","01100"]]
            onPaint: {
                if (!displaysFace.visible) return;
                const ctx = getContext("2d");
                ctx.reset();
                const kind = face.style, W = width, H = height, text = display.text;
                const n = text.length, colons = n / 2 - 1;
                function bar(x, y, w, h, r) {   // rounded bar
                    r = Math.min(r, w / 2, h / 2);
                    ctx.beginPath();
                    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.arc(x + w - r, y + r, r, -Math.PI / 2, 0);
                    ctx.lineTo(x + w, y + h - r); ctx.arc(x + w - r, y + h - r, r, 0, Math.PI / 2);
                    ctx.lineTo(x + r, y + h); ctx.arc(x + r, y + h - r, r, Math.PI / 2, Math.PI);
                    ctx.lineTo(x, y + r); ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
                    ctx.closePath(); ctx.fill();
                }
                function disc(x, y, r) { ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.fill(); }
                function backdrop(colour, bezel) {
                    ctx.fillStyle = colour; ctx.fillRect(0, 0, W, H);
                    if (bezel) { ctx.strokeStyle = bezel; ctx.lineWidth = 1; ctx.strokeRect(0.5, 0.5, W - 1, H - 1); }
                }
                function glow(colour, blur) { ctx.shadowColor = colour; ctx.shadowBlur = blur; }
                function noGlow() { ctx.shadowBlur = 0; ctx.shadowColor = "transparent"; }

                // ---- dot grids: LED matrix, flip-disc, pixel ----
                if (kind === "ledmatrix" || kind === "flipdisc" || kind === "pixel") {
                    const cols = n * 6 - 1 + colons * 2;
                    const p = Math.max(2, Math.floor(Math.min((W - 4) / cols, (H - 4) / 7)));
                    const x0 = Math.round((W - cols * p) / 2), y0 = Math.round((H - 7 * p) / 2);
                    if (kind === "ledmatrix") backdrop("#0b0b0b", "#262626");
                    if (kind === "flipdisc") backdrop("#141414", "#333333");
                    const r = p * (kind === "flipdisc" ? 0.46 : 0.42);
                    let col = 0;
                    const cells = [];
                    for (let i = 0; i < n; i++) {
                        const bits = display.dots[Number(text[i])];
                        for (let ry = 0; ry < 7; ry++) for (let rx = 0; rx < 5; rx++) cells.push([col + rx, ry, bits[ry][rx] === "1"]);
                        col += 6;
                        if (i % 2 === 1 && i < n - 1) { cells.push([col, 2, true]); cells.push([col, 4, true]); col += 2; }
                    }
                    if (kind !== "pixel") {   // unlit dots first
                        ctx.fillStyle = kind === "ledmatrix" ? "#28100a" : "#1e1e1e";
                        for (let cx = 0; cx < cols; cx++) for (let cy = 0; cy < 7; cy++)
                            if (!(cx % 6 === 5 && cx < n * 6 - 1)) disc(x0 + cx * p + p / 2, y0 + cy * p + p / 2, r);
                    }
                    if (kind === "ledmatrix") glow("#ff2a1a", p * 0.9);
                    for (const c of cells) {
                        if (!c[2]) continue;
                        const cx = x0 + c[0] * p, cy = y0 + c[1] * p;
                        if (kind === "ledmatrix") { ctx.fillStyle = "#ff2a1a"; disc(cx + p / 2, cy + p / 2, r); }
                        else if (kind === "flipdisc") {
                            ctx.fillStyle = "#f2d33c"; disc(cx + p / 2, cy + p / 2, r);
                            if (p >= 6) { ctx.fillStyle = "#fff3a0"; disc(cx + p / 2 - r * 0.25, cy + p / 2 - r * 0.25, r * 0.35); }
                        } else {
                            ctx.fillStyle = face.ink.toString(); ctx.fillRect(cx, cy, p - 1, p - 1);
                            if (p >= 4) { ctx.fillStyle = face.accent.toString(); ctx.fillRect(cx + 1, cy + 1, p - 2, p - 2); }
                        }
                    }
                    noGlow();
                    return;
                }

                // ---- segments: VFD and Panaplex ----
                const plex = kind.indexOf("panaplex") === 0;
                if (kind.indexOf("vfd") === 0 || plex) {
                    const units = n * 0.5 + (n - 1) * 0.15 + colons * 0.25;
                    const h = Math.max(8, Math.floor(Math.min(H * 0.84, (W - 6) / units)));
                    const w = Math.round(h * 0.5), s = Math.round(h * 0.15), cw = Math.round(h * 0.25);
                    const t = Math.max(1, Math.round(h * (plex ? 0.07 : 0.1)));
                    let x = Math.round((W - (n * w + (n - 1) * s + colons * cw)) / 2);
                    const y = Math.round((H - h) / 2), mid = y + h / 2;
                    const look = {
                        "vfd":      {bg: "#06121a", bezel: "#12303a", on: "#9df7ff", off: "rgba(120,200,210,0.16)", blur: 0.15, passes: 2, grid: true},
                        "vfd-blue": {bg: "#020a16", bezel: "#0a1a33", on: "#e8fbff", off: "rgba(120,200,210,0.12)", blur: 0.15, passes: 2, grid: true, tint: "rgba(20,60,160,0.2)"},
                        "vfd-aqua": {bg: "#000000", bezel: "#111111", on: "#66e6ff", off: "rgba(120,200,210,0.08)", blur: 0.32, passes: 3, grid: false},
                        "panaplex": {bg: "#0a0806", bezel: "#2a2018", on: "#ff6a2a", off: "rgba(255,106,42,0.12)", blur: 0.12, passes: 2, grid: false, core: "#ffd0a0"},
                        "panaplex-palette": display.paletteLook()
                    }[kind];
                    backdrop(look.bg, look.bezel);
                    function segment(key, xd, lit) {
                        const inner = w - 2 * t, upper = mid - t / 2 - (y + t), lower = (y + h - t) - (mid + t / 2);
                        const g = 1;
                        const box = {a: [xd + t + g, y, inner - 2 * g, t], g: [xd + t + g, mid - t / 2, inner - 2 * g, t], d: [xd + t + g, y + h - t, inner - 2 * g, t],
                                     f: [xd, y + t + g, t, upper - 2 * g], b: [xd + w - t, y + t + g, t, upper - 2 * g],
                                     e: [xd, mid + t / 2 + g, t, lower - 2 * g], c: [xd + w - t, mid + t / 2 + g, t, lower - 2 * g]}[key];
                        if (plex) {
                            ctx.fillStyle = lit ? look.on : look.off;
                            bar(box[0], box[1], box[2], box[3], t / 2);
                            if (lit && t >= 3) { ctx.fillStyle = look.core; const k = Math.max(1, Math.floor(t / 3));
                                if (box[2] > box[3]) bar(box[0] + 1, box[1] + (t - k) / 2, box[2] - 2, k, k / 2); else bar(box[0] + (t - k) / 2, box[1] + 1, k, box[3] - 2, k / 2); }
                        } else {
                            ctx.fillStyle = lit ? look.on : look.off;
                            bar(box[0], box[1], box[2], box[3], t / 2);
                        }
                    }
                    // Unlit, then the lit ones with their glow (several passes thicken it).
                    let xd = x;
                    for (let i = 0; i < n; i++) {
                        for (const key of "abcdefg") if (display.seg7[Number(text[i])].indexOf(key) < 0) segment(key, xd, false);
                        xd += w + s; if (i % 2 === 1 && i < n - 1) xd += cw;
                    }
                    for (let pass = 0; pass < look.passes; pass++) {
                        glow(look.on, h * look.blur * (pass === 0 ? 2 : 1));
                        xd = x;
                        for (let i = 0; i < n; i++) {
                            for (const key of "abcdefg") if (display.seg7[Number(text[i])].indexOf(key) >= 0) segment(key, xd, true);
                            xd += w + s;
                            if (i % 2 === 1 && i < n - 1) {
                                ctx.fillStyle = look.on;
                                disc(xd + cw / 2 - s / 2, y + h * 0.3, t / 2); disc(xd + cw / 2 - s / 2, y + h * 0.7, t / 2);
                                xd += cw;
                            }
                        }
                    }
                    noGlow();
                    if (look.grid && h > 20) { ctx.fillStyle = "rgba(0,0,0,0.18)"; for (let gy = 3; gy < H; gy += 5) ctx.fillRect(1, gy, W - 2, 1); }
                    if (look.tint) { ctx.fillStyle = look.tint; ctx.fillRect(1, 1, W - 2, H - 2); }
                    return;
                }

                // ---- type: flip clock, odometer, plasma ----
                const gap = Math.max(1, Math.round(W * 0.015));
                if (kind === "flipclock") {
                    backdrop("#2a2a2a", "#444444");
                    const cw = Math.round(H * 0.3);
                    const card = Math.floor((W - 4 - colons * cw - (n - 1) * gap) / n);
                    const px = Math.floor(H * 0.78);
                    ctx.font = "700 " + px + "px '" + face.font + "'"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    let x = Math.round((W - (n * card + (n - 1) * gap + colons * cw)) / 2);
                    for (let i = 0; i < n; i++) {
                        ctx.fillStyle = "#111111"; bar(x, 2, card, H - 4, Math.max(1, H * 0.06));
                        ctx.fillStyle = "#1a1a1a"; ctx.fillRect(x, 2, card, H / 2 - 2);
                        ctx.fillStyle = "#f2f2f2"; ctx.fillText(text[i], x + card / 2, H / 2 + 1);
                        ctx.fillStyle = "#2a2a2a"; ctx.fillRect(x, Math.round(H / 2) - 1, card, 2);
                        x += card + gap;
                        if (i % 2 === 1 && i < n - 1) { ctx.fillStyle = "#dddddd"; disc(x + cw / 2 - gap / 2, H * 0.38, H * 0.04); disc(x + cw / 2 - gap / 2, H * 0.62, H * 0.04); x += cw; }
                    }
                    return;
                }
                if (kind === "odometer") {
                    const frame = Motif.shades(face.dialColor);
                    ctx.fillStyle = face.dialColor.toString(); ctx.fillRect(0, 0, W, H);
                    const cw = Math.round(H * 0.3);
                    const drum = Math.floor((W - 6 - colons * cw - (n - 1) * gap) / n);
                    const top = 2, dh = H - 4;
                    let x = Math.round((W - (n * drum + (n - 1) * gap + colons * cw)) / 2);
                    ctx.fillStyle = "#1a1a1a"; ctx.fillRect(x - 3, top - 2 + 2, n * drum + (n - 1) * gap + colons * cw + 6, dh);
                    const px = Math.floor(dh * 0.62);
                    ctx.font = "700 " + px + "px 'IBM Plex Mono'"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    for (let i = 0; i < n; i++) {
                        const grad = ctx.createLinearGradient(0, top, 0, top + dh);
                        grad.addColorStop(0, "#5a5a5a"); grad.addColorStop(0.5, "#ededed"); grad.addColorStop(1, "#5a5a5a");
                        ctx.fillStyle = grad; ctx.fillRect(x, top, drum, dh);
                        ctx.save(); ctx.beginPath(); ctx.rect(x, top, drum, dh); ctx.clip();
                        const v = Number(text[i]);
                        ctx.fillStyle = "#111111"; ctx.fillText(String(v), x + drum / 2, top + dh / 2);
                        ctx.fillStyle = "#555555";
                        ctx.fillText(String((v + 9) % 10), x + drum / 2, top + dh / 2 - dh * 0.72);
                        ctx.fillText(String((v + 1) % 10), x + drum / 2, top + dh / 2 + dh * 0.72);
                        ctx.restore();
                        ctx.strokeStyle = "#000000"; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, top + 0.5, drum - 1, dh - 1);
                        x += drum + gap;
                        if (i % 2 === 1 && i < n - 1) { ctx.fillStyle = "#2a2a2a"; ctx.fillRect(x + cw * 0.35, top + 2, cw * 0.3, dh - 4); x += cw; }
                    }
                    return;
                }
                if (kind === "plasma") {
                    backdrop("#1a0a0a", "#3a1a1a");
                    const shown = face.seconds ? Qt.formatDateTime(face.now, "HH:mm:ss") : Qt.formatDateTime(face.now, "HH:mm");
                    const px = Math.floor(Math.min(H * 0.8, (W - 6) / (shown.length * 0.5)));
                    ctx.font = "600 " + px + "px '" + face.font + "'"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    for (let pass = 0; pass < 3; pass++) {
                        glow("#ff4a2a", px * (pass === 0 ? 0.35 : 0.12));
                        ctx.fillStyle = "#ff4a2a"; ctx.fillText(shown, W / 2, H / 2 + 1);
                    }
                    noGlow();
                    if (H > 24) {
                        ctx.fillStyle = "rgba(0,0,0,0.27)"; for (let gy = 0; gy < H; gy += 3) ctx.fillRect(0, gy, W, 1);
                        ctx.fillStyle = "rgba(0,0,0,0.16)"; for (let gx = 0; gx < W; gx += 3) ctx.fillRect(gx, 0, 1, H);
                    }
                }
            }
        }
        Text {
            visible: displaysFace.showDate
            x: Math.round((displaysFace.width - width) / 2)
            y: display.y + display.height + displaysFace.gapBelow
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
