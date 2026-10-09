import QtQuick

// A sketch of the small buttons' block in one style, for the settings
// page: four keys and two meters (load, cluster), drawn as the console
// draws them, only flat and in the system colours.
//
//   "family"       six squares alike, the meters' bars among the keys
//   "instruments"  the meters sunken, dark, with lit bars
//   "led"          the meters as a row of LED digits over the keys
//   "panel"        the meters as a panel of bars beside the keys
Canvas {
    id: sketch
    property string style: "family"
    property color face: "lightgray"     // a key's surface
    property color ink: "black"          // glyphs, edges
    property color lamp: "orange"        // lit bars and digits
    property color well: "#202020"       // a sunken meter's ground
    onStyleChanged: requestPaint()
    onFaceChanged: requestPaint()
    onLampChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const g = getContext("2d");
        g.reset();
        const gap = 2;
        // Two rows of squares, as tall as the sketch allows.
        const q = Math.floor(Math.min((height - gap) / 2, (width - 3 * gap) / 4.4));
        const left = Math.round((width - blockWidth(q, gap)) / 2);
        const top = Math.round((height - (2 * q + gap)) / 2);

        function key(x, y, w, h) {
            g.fillStyle = sketch.face;
            g.fillRect(x, y, w, h);
            g.fillStyle = Qt.lighter(sketch.face, 1.25);
            g.fillRect(x, y, w, 1); g.fillRect(x, y, 1, h);
            g.fillStyle = Qt.darker(sketch.face, 1.6);
            g.fillRect(x, y + h - 1, w, 1); g.fillRect(x + w - 1, y, 1, h);
            // A glyph: a small ring, as for lock, desktop, settings, leave.
            g.strokeStyle = sketch.ink; g.lineWidth = Math.max(1, q / 14);
            g.beginPath(); g.arc(x + w / 2, y + h / 2, Math.min(w, h) * 0.18, 0, 2 * Math.PI); g.stroke();
        }
        function bars(x, y, w, h, sunken, n, upright) {
            g.fillStyle = sunken ? sketch.well : sketch.face;
            g.fillRect(x, y, w, h);
            if (!sunken) { g.fillStyle = Qt.darker(sketch.face, 1.6); g.fillRect(x, y + h - 1, w, 1); g.fillRect(x + w - 1, y, 1, h); }
            const shares = [0.7, 0.4, 0.55];
            g.fillStyle = sunken ? sketch.lamp : sketch.ink;
            for (let i = 0; i < n; ++i) {
                if (upright) {
                    const bw = (w - 4) / n - 2, bh = (h - 6) * shares[i % 3];
                    g.fillRect(x + 3 + i * (bw + 2), y + h - 3 - bh, bw, bh);
                } else {
                    const bh = Math.max(2, (h - 6) / n - 2), bw = (w - 6) * shares[i % 3];
                    g.fillRect(x + 3, y + 3 + i * (bh + 2), bw, bh);
                }
            }
        }
        function digits(x, y, w, h, text) {
            g.fillStyle = sketch.well;
            g.fillRect(x, y, w, h);
            g.fillStyle = sketch.lamp;
            g.font = "bold " + Math.round(h * 0.62) + "px monospace";
            g.textAlign = "center"; g.textBaseline = "middle";
            g.fillText(text, x + w / 2, y + h / 2 + 1);
        }

        if (style === "led") {
            digits(left, top, 4 * q + 3 * gap, q, "42  17");
            for (let i = 0; i < 4; ++i) key(left + i * (q + gap), top + q + gap, q, q);
        } else if (style === "panel") {
            const pw = Math.round(q * 1.4);
            bars(left, top, pw, 2 * q + gap, true, 3, true);
            for (let i = 0; i < 4; ++i)
                key(left + pw + gap + Math.floor(i / 2) * (q + gap), top + (i % 2) * (q + gap), q, q);
        } else {
            // Columns of two, top to bottom: load, cluster, then the keys.
            const sunken = style === "instruments";
            for (let i = 0; i < 6; ++i) {
                const x = left + Math.floor(i / 2) * (q + gap), y = top + (i % 2) * (q + gap);
                if (i < 2) bars(x, y, q, q, sunken, i === 0 ? 2 : 1, false);
                else key(x, y, q, q);
            }
        }
    }
    function blockWidth(q, gap) {
        if (style === "led") return 4 * q + 3 * gap;
        if (style === "panel") return Math.round(q * 1.4) + gap + 2 * q + gap;
        return 3 * q + 2 * gap;
    }
}
