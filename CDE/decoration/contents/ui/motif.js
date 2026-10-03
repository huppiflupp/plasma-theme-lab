// Motif shading: the select, top-shadow and bottom-shadow colours that
// Motif derives from a background (CalculateColorsRGB in lib/Xm/Color.c,
// default thresholds dark 20, light 93). The same rule as palettes.py, so
// the decoration matches whichever colour scheme is active.
.pragma library

const MAX = 65535;
const PCT = Math.floor(MAX / 100);

function channels(c) {
    return [Math.round(c.r * MAX), Math.round(c.g * MAX), Math.round(c.b * MAX)];
}

function brightness(v) {
    const intensity = Math.floor((v[0] + v[1] + v[2]) / 3);
    const luminosity = Math.floor(0.30 * v[0] + 0.59 * v[1] + 0.11 * v[2]);
    return Math.floor((intensity * 75 + luminosity * 25) / 100);
}

function shades(c) {
    const v = channels(c);
    const level = brightness(v);
    let ts, bs, sel;
    if (level < 20 * PCT) {
        sel = v.map(x => x + Math.floor(15 * (MAX - x) / 100));
        bs = v.map(x => x + Math.floor(30 * (MAX - x) / 100));
        ts = v.map(x => x + Math.floor(50 * (MAX - x) / 100));
    } else if (level > 93 * PCT) {
        sel = v.map(x => x - Math.floor(x * 15 / 100));
        bs = v.map(x => x - Math.floor(x * 40 / 100));
        ts = v.map(x => x - Math.floor(x * 20 / 100));
    } else {
        // C truncates towards zero; Math.floor would darken one percent too much.
        const fBs = 60 + Math.trunc(level * (40 - 60) / MAX);
        const fTs = 50 + Math.trunc(level * (60 - 50) / MAX);
        sel = v.map(x => x - Math.floor(x * 15 / 100));
        bs = v.map(x => x - Math.floor(x * fBs / 100));
        ts = v.map(x => x + Math.floor(fTs * (MAX - x) / 100));
    }
    const q = a => Qt.rgba(a[0] / MAX, a[1] / MAX, a[2] / MAX, 1);
    return {top: q(ts), bottom: q(bs), select: q(sel)};
}

function mix(a, b, t) {
    return Qt.rgba(a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t, 1);
}
