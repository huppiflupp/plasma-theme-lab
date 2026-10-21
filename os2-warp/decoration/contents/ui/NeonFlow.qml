import QtQuick

// Neon's frame line in slow motion (setting flowFrame, the user's wish
// 21.10.2026): the variant's dark edge, the pink accent and the cyan light
// lie once round the window and drift clockwise, one round in about a
// minute and a half; a single travelling spot was thought too much. Only
// the active window moves (running), so KWin redraws one frame at a time,
// and that only twenty times a second: the colours shift a few pixels per
// step, too little to see as a jump.
Item {
    id: flow
    property color light
    property color dark
    property color accent
    property bool running: false
    property real phase: 0
    readonly property real seconds: 90

    Timer {
        interval: 50
        repeat: true
        running: flow.running && flow.visible
        onTriggered: flow.phase = (flow.phase + interval / 1000 / flow.seconds) % 1
    }

    readonly property real perimeter: Math.max(1, 2 * (width + height))
    // Mixed along the hue, the short way round: pink to cyan through
    // violet and blue. Mixed as RGB they met in a pale, almost white
    // lavender (the user's remark 21.10.2026).
    function mix(a, b, t) {
        let d = b.hsvHue - a.hsvHue;
        if (d > 0.5) d -= 1;
        if (d < -0.5) d += 1;
        const h = ((a.hsvHue + d * t) % 1 + 1) % 1;
        return Qt.hsva(h, a.hsvSaturation + (b.hsvSaturation - a.hsvSaturation) * t,
                       a.hsvValue + (b.hsvValue - a.hsvValue) * t, 1);
    }
    // The colour at u pixels along the edge, clockwise from the top left:
    // dark, pink, cyan and back to dark over the whole way round.
    function at(u) {
        const t = (((u / perimeter - phase) % 1) + 1) % 1 * 3;
        const colours = [dark, accent, light, dark];
        const i = Math.min(2, Math.floor(t));
        return mix(colours[i], colours[i + 1], t - i);
    }
    // Stop s (0..5) of side k: 0 top, 1 right, 2 bottom, 3 left. The
    // gradients run left to right and top to bottom; the way round runs
    // back along the bottom and up the left side.
    function stop(k, s) {
        const f = s / 5;
        const u = k === 0 ? f * width
                : k === 1 ? width + f * height
                : k === 2 ? width + height + (1 - f) * width
                : 2 * width + height + (1 - f) * height;
        return at(u);
    }

    Rectangle {
        width: parent.width; height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: flow.stop(0, 0) }
            GradientStop { position: 0.2; color: flow.stop(0, 1) }
            GradientStop { position: 0.4; color: flow.stop(0, 2) }
            GradientStop { position: 0.6; color: flow.stop(0, 3) }
            GradientStop { position: 0.8; color: flow.stop(0, 4) }
            GradientStop { position: 1.0; color: flow.stop(0, 5) }
        }
    }
    Rectangle {
        x: parent.width - 1; width: 1; height: parent.height
        gradient: Gradient {
            GradientStop { position: 0.0; color: flow.stop(1, 0) }
            GradientStop { position: 0.2; color: flow.stop(1, 1) }
            GradientStop { position: 0.4; color: flow.stop(1, 2) }
            GradientStop { position: 0.6; color: flow.stop(1, 3) }
            GradientStop { position: 0.8; color: flow.stop(1, 4) }
            GradientStop { position: 1.0; color: flow.stop(1, 5) }
        }
    }
    Rectangle {
        y: parent.height - 1; width: parent.width; height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: flow.stop(2, 0) }
            GradientStop { position: 0.2; color: flow.stop(2, 1) }
            GradientStop { position: 0.4; color: flow.stop(2, 2) }
            GradientStop { position: 0.6; color: flow.stop(2, 3) }
            GradientStop { position: 0.8; color: flow.stop(2, 4) }
            GradientStop { position: 1.0; color: flow.stop(2, 5) }
        }
    }
    Rectangle {
        width: 1; height: parent.height
        gradient: Gradient {
            GradientStop { position: 0.0; color: flow.stop(3, 0) }
            GradientStop { position: 0.2; color: flow.stop(3, 1) }
            GradientStop { position: 0.4; color: flow.stop(3, 2) }
            GradientStop { position: 0.6; color: flow.stop(3, 3) }
            GradientStop { position: 0.8; color: flow.stop(3, 4) }
            GradientStop { position: 1.0; color: flow.stop(3, 5) }
        }
    }
}
