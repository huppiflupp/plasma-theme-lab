pragma ComponentBehavior: Bound
import QtQuick
import "motif.js" as Motif

// The graphics processor's load, drawn one of four ways (gpuStyle) into
// whatever room it is given: a quarter of the session block, a cell of the
// LED field or of the bar panel. Colours come from the caller, all from the
// palette: lit for the load (the highlight), ink for the scale, the needle
// and the peak (the text colour), well for sunken channels. What is drawn
// inside a channel (the memory, the grid) takes black or white towards the
// well's colour instead: the text colour can be as dark as a sunken well.
//   bars    two upright channels, load and graphics memory
//   trace   the load of the last minute as a curve
//   dial    a needle instrument, 0 to 100, the last tenth marked
//   ladder  ten segments with the peak held, across or upright
Item {
    id: gauge
    property string style: "bars"
    property real load: 0               // per cent
    property real memory: -1            // share 0..1, below 0 unknown
    property real peak: 0               // per cent, falling slowly
    property var history: []            // per cent, oldest first
    property color lit: "orange"
    property color ink: "black"
    property color well: "grey"
    property string label: "G"
    property int labelSize: 8
    property string font: ""
    // The faint unlit segment, as SegmentDigits draws it.
    readonly property color faint: Qt.rgba(ink.r, ink.g, ink.b, 0.13)
    readonly property color inWell: Motif.mix(well, Motif.stark(well), 0.7)
    readonly property bool across: width > height * 1.3
    readonly property int labelRoom: label !== "" && !(style === "ladder" && across) ? labelSize + 1 : 0
    readonly property int roomHeight: Math.max(4, height - labelRoom)

    Text {
        id: caption
        visible: gauge.label !== ""
        text: gauge.style === "trace" && gauge.width >= gauge.labelSize * 5 ? gauge.label + " " + Math.round(gauge.load) + "%" : gauge.label
        color: gauge.lit
        font.family: gauge.font; font.pixelSize: gauge.labelSize; font.weight: Font.DemiBold
        x: gauge.style === "ladder" && gauge.across ? 0 : Math.round((gauge.width - width) / 2)
        y: gauge.style === "ladder" && gauge.across ? Math.round((gauge.height - height) / 2) : gauge.height - gauge.labelSize - 1
        height: gauge.labelSize + 1
        verticalAlignment: Text.AlignVCenter
    }

    // Load and memory: two sunken channels side by side, as the load meter's.
    Row {
        id: channels
        visible: gauge.style === "bars"
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: Math.max(1, Math.round(gauge.width * 0.06))
        readonly property int channel: Math.max(5, Math.min(Math.round(gauge.roomHeight * 0.4), Math.round(gauge.width * (gauge.memory >= 0 ? 0.24 : 0.4))))
        Repeater {
            model: gauge.memory >= 0 ? [gauge.load / 100, gauge.memory] : [gauge.load / 100]
            delegate: Bevel {
                id: channel
                required property real modelData
                required property int index
                sunken: true
                surface: gauge.well
                width: channels.channel; height: gauge.roomHeight
                Rectangle {
                    x: 2; width: parent.width - 4
                    readonly property int room: parent.height - 4
                    height: Math.round(room * Math.max(0, Math.min(1, channel.modelData)))
                    y: 2 + room - height
                    color: channel.index === 0 ? gauge.lit : gauge.inWell
                }
            }
        }
    }

    // The last minute: a curve over a faint grid in a sunken channel.
    Bevel {
        visible: gauge.style === "trace"
        sunken: true
        surface: gauge.well
        width: gauge.width; height: gauge.roomHeight
        Canvas {
            id: trace
            x: 2; y: 2; width: parent.width - 4; height: parent.height - 4
            readonly property var points: gauge.history
            onPointsChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onVisibleChanged: if (visible) requestPaint()
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                const w = width, h = height, n = points.length;
                ctx.strokeStyle = Qt.rgba(gauge.inWell.r, gauge.inWell.g, gauge.inWell.b, 0.35).toString();
                ctx.lineWidth = 1;
                for (const v of [25, 50, 75]) {
                    const y = Math.round(h - h * v / 100) + 0.5;
                    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
                }
                if (n < 2) return;
                const px = i => w * i / (n - 1);
                const py = v => h - Math.max(1, h * Math.max(0, Math.min(100, v)) / 100);
                ctx.beginPath(); ctx.moveTo(0, h);
                for (let i = 0; i < n; i++) ctx.lineTo(px(i), py(points[i]));
                ctx.lineTo(w, h); ctx.closePath();
                ctx.fillStyle = Qt.rgba(gauge.lit.r, gauge.lit.g, gauge.lit.b, 0.3).toString();
                ctx.fill();
                ctx.beginPath();
                for (let i = 0; i < n; i++) i ? ctx.lineTo(px(i), py(points[i])) : ctx.moveTo(0, py(points[0]));
                ctx.strokeStyle = gauge.lit.toString();
                ctx.lineWidth = Math.max(1, Math.round(h / 24));
                ctx.stroke();
            }
        }
    }

    // A needle instrument: half a circle, ticks every ten, the last tenth lit;
    // the needle in ink, which reads on any face.
    Canvas {
        id: dial
        visible: gauge.style === "dial"
        width: gauge.width; height: gauge.roomHeight
        property real shown: gauge.load
        Behavior on shown { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
        onShownChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onVisibleChanged: if (visible) requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const R = Math.max(4, Math.min(width / 2 - 2, height - 3));
            const cx = width / 2, cy = height - 2 - Math.max(1, R * 0.08);
            const at = v => Math.PI * (1 + v / 100);
            ctx.lineCap = "butt";
            ctx.strokeStyle = gauge.lit.toString();
            ctx.lineWidth = Math.max(2, R * 0.14);
            ctx.beginPath(); ctx.arc(cx, cy, R - ctx.lineWidth / 2, at(90), at(100)); ctx.stroke();
            ctx.strokeStyle = gauge.ink.toString();
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.arc(cx, cy, R, at(0), at(100)); ctx.stroke();
            for (let v = 0; v <= 100; v += 10) {
                const len = v % 50 ? R * 0.14 : R * 0.26;
                ctx.beginPath();
                ctx.moveTo(cx + R * Math.cos(at(v)), cy + R * Math.sin(at(v)));
                ctx.lineTo(cx + (R - len) * Math.cos(at(v)), cy + (R - len) * Math.sin(at(v)));
                ctx.stroke();
            }
            const v = Math.max(0, Math.min(100, shown)), tip = R * 0.86;
            ctx.strokeStyle = gauge.ink.toString();
            ctx.lineWidth = Math.max(1.5, R * 0.09);
            ctx.lineCap = "round";
            ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + tip * Math.cos(at(v)), cy + tip * Math.sin(at(v))); ctx.stroke();
            ctx.fillStyle = gauge.ink.toString();
            ctx.beginPath(); ctx.arc(cx, cy, Math.max(1.5, R * 0.12), 0, 2 * Math.PI); ctx.fill();
        }
    }

    // Ten segments, lit with the load, the peak held in ink; whole pixels.
    Item {
        id: ladder
        visible: gauge.style === "ladder"
        readonly property int count: 10
        readonly property int gap: 1
        readonly property int start: gauge.across && gauge.label !== "" ? caption.width + Math.max(2, Math.round(gauge.labelSize * 0.4)) : 0
        readonly property int length: gauge.across ? gauge.width - start : gauge.roomHeight
        readonly property int step: Math.max(2, Math.floor((length + gap) / count))
        readonly property int thick: gauge.across ? Math.max(4, Math.min(gauge.height, Math.round(step * 1.6)))
                                                  : Math.max(4, Math.min(gauge.width, Math.round(gauge.width * 0.4)))
        readonly property int litCount: Math.round(Math.max(0, Math.min(100, gauge.load)) / 10)
        readonly property int peakIndex: Math.min(count - 1, Math.ceil(gauge.peak / 10) - 1)
        x: gauge.across ? start : Math.round((gauge.width - thick) / 2)
        y: gauge.across ? Math.round((gauge.height - thick) / 2) : 0
        width: gauge.across ? length : thick
        height: gauge.across ? thick : length
        Repeater {
            model: ladder.count
            delegate: Rectangle {
                required property int index
                readonly property int along: index * ladder.step
                x: gauge.across ? along : 0
                y: gauge.across ? 0 : ladder.length - along - (ladder.step - ladder.gap)
                width: gauge.across ? ladder.step - ladder.gap : ladder.thick
                height: gauge.across ? ladder.thick : ladder.step - ladder.gap
                color: index < ladder.litCount ? gauge.lit
                     : index === ladder.peakIndex && ladder.peakIndex >= ladder.litCount ? gauge.ink : gauge.faint
            }
        }
    }
}
