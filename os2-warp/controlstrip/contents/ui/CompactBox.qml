pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

// The Control Strip as the box of the user's Neon concept
// (reference/neon-2026.png, top right): a mark, the time and date, CPU,
// memory and disk with thin bars, a curve of the processor's last minute,
// a motto. Our mark is "Warp Legacy"; the concept's OS/2 word mark is
// IBM's (DESIGN.md §1).
//
// No frame of its own: the panel's background is the frame. Drawn as a
// Bevel the box had a second frame inside the panel's (the user's remark,
// compared with the concept, 21.10.2026).
Item {
    id: box
    required property var root
    implicitHeight: column.implicitHeight + 16
    readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property color dark: neon ? "#7a4dff" : "#808080"
    readonly property color bright: box.neon ? "#cfeeff" : Kirigami.Theme.textColor
    readonly property color cyan: box.neon ? "#3ad0ff" : Kirigami.Theme.linkColor
    readonly property color lavender: box.neon ? "#e2b8ff" : Kirigami.Theme.highlightColor

    // A thin line of light between the parts: cyan into pink, fading out.
    component Divider: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.1) }
            GradientStop { position: 0.4; color: box.cyan }
            GradientStop { position: 0.8; color: box.neon ? "#ff4fd8" : box.dark }
            GradientStop { position: 1.0; color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.1) }
        }
    }
    // A reading: name, percent, a thin bar.
    component Meter: RowLayout {
        id: meter
        property string name
        property real part
        spacing: 6
        Text { text: meter.name; color: box.cyan; font.pixelSize: 13; Layout.preferredWidth: 32 }
        Text {
            text: Math.round(meter.part * 100) + "%"
            color: box.cyan; font.pixelSize: 13
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 36
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.35)
            Rectangle {
                x: 1; y: 1; height: parent.height - 2
                width: Math.max(0, (parent.width - 2) * Math.min(1, meter.part))
                color: box.cyan
            }
        }
    }

    ColumnLayout {
        id: column
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
        spacing: 6

        // The mark: a globe behind "Warp" and the year.
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            Kirigami.Icon {
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                width: 50; height: 50
                source: "internet-web-browser"
                opacity: 0.85
            }
            Text {
                id: word
                y: 2
                text: "WARP"
                font.family: Kirigami.Theme.defaultFont.family
                font.pixelSize: 28; font.bold: true; font.italic: true
                color: box.cyan
                style: box.neon ? Text.Outline : Text.Normal
                styleColor: Qt.rgba(0.16, 0.36, 1, 0.45)
            }
            // "Legacy" in a bold italic Times, as the user asked; fontconfig
            // gives the metric twin (Liberation Serif) where Times New
            // Roman is not installed, which is the free one we rely on.
            Text {
                anchors.top: word.bottom; anchors.topMargin: -8
                x: 18
                text: "Legacy"
                font.family: "Times New Roman"
                font.pixelSize: 24; font.bold: true; font.italic: true
                color: box.lavender
            }
        }
        Divider {}
        Text {
            text: Qt.formatTime(box.root.now, "hh:mm")
            color: box.bright
            font.pixelSize: 30; font.weight: Font.Light
        }
        Text {
            Layout.topMargin: -6
            text: Qt.formatDate(box.root.now, "dd.MM.yyyy")
            color: box.cyan; font.pixelSize: 15
        }
        Text {
            Layout.topMargin: -6
            text: Qt.locale().toString(box.root.now, "ddd, d. MMM")
            color: box.cyan; font.pixelSize: 11; opacity: 0.85
        }
        Divider {}
        Meter { Layout.fillWidth: true; name: "CPU"; part: box.root.cpu }
        Meter { Layout.fillWidth: true; name: "RAM"; part: box.root.memoryPart }
        Meter { Layout.fillWidth: true; name: "/"; part: box.root.rootPart }
        // The processor's last minute.
        Canvas {
            id: curve
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            readonly property var points: box.root.cpuHistory
            onPointsChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.35).toString();
                ctx.beginPath(); ctx.moveTo(0, height - 0.5); ctx.lineTo(width, height - 0.5); ctx.stroke();
                const n = points.length;
                if (n < 2) return;
                ctx.strokeStyle = box.cyan.toString();
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                for (let i = 0; i < n; i++) {
                    const x = width * i / 29, y = height - 2 - (height - 4) * points[i];
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.stroke();
            }
        }
        Text {
            visible: text !== ""
            Layout.fillWidth: true
            Layout.topMargin: 4
            text: box.root.tr(Plasmoid.configuration.motto)
            color: box.cyan
            font.pixelSize: 14; font.italic: true
            wrapMode: Text.WordWrap
        }
    }
}
