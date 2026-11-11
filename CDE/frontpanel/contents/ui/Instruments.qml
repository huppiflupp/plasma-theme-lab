pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.ksysguard.sensors as Sensors
import "motif.js" as Motif

// The meters gathered in one sunken field in the clock's colours: as LED
// digits (the cluster's tokens per second, processor and memory load in
// per cent) or as a panel of bars. Each reading is its own button. The
// graphics processor is drawn by GpuGauge in the style chosen (gpuStyle),
// or, joined with the cluster, as a lamp and a stripe on its digits.
Bevel {
    id: field
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    property bool bars: false
    property var kinds: []
    readonly property bool hasLlm: kinds.indexOf("llm") >= 0
    // The graphics processor on the cluster's digits instead of a reading.
    property bool gpuJoined: false
    readonly property var readings: (hasLlm ? ["llm"] : []).concat(kinds.indexOf("load") >= 0 ? ["cpu", "mem"] : [])
        .concat(kinds.indexOf("gpu") >= 0 ? ["gpu"] : [])
        .concat(kinds.indexOf("load") >= 0 && field.root.batteryShown ? ["bat"] : [])
    // Room for the graphics processor's reading, against a bar's or two digits'.
    readonly property real gpuWeight: field.bars ? {bars: 1.5, trace: 2.5, dial: 2.5, ladder: 1}[field.root.gpuGauge]
                                                 : {bars: 2, trace: 5, dial: 3.5, ladder: 5}[field.root.gpuGauge]
    readonly property int cpuLoad: Math.round(Math.max(0, Math.min(100, Number(cpuSensor.value) || 0)))
    readonly property int memLoad: Math.round(Math.max(0, Math.min(100, Number(memSensor.value) || 0)))
    sunken: true
    surface: field.colors.window
    Sensors.Sensor { id: cpuSensor; sensorId: "cpu/all/usage"; updateRateLimit: 2000 }
    Sensors.Sensor { id: memSensor; sensorId: "memory/physical/usedPercent"; updateRateLimit: 2000 }
    Binding { when: field.hasLlm; target: field.root; property: "llmSmallVisible"; value: field.visible && field.Window.window !== null && field.Window.window.visible; restoreMode: Binding.RestoreBindingOrValue }
    RowLayout {
        anchors.fill: parent; anchors.margins: 2
        spacing: 0
        Repeater {
            model: field.readings
            delegate: ConsoleButton {
                id: reading
                required property string modelData
                readonly property bool llm: modelData === "llm"
                readonly property bool bat: modelData === "bat"
                readonly property bool gpu: modelData === "gpu"
                readonly property bool joined: llm && field.gpuJoined && !field.bars
                readonly property int value: llm ? Math.round(field.root.llmTotal) : modelData === "cpu" ? field.cpuLoad
                                           : bat ? field.root.batteryPercent : gpu ? Math.round(field.root.gpuLoad) : field.memLoad
                // Bars: the cluster against its best so far, load in per cent.
                readonly property real share: llm ? Math.min(1, field.root.llmTotal / Math.max(1, field.root.llmPeak)) : value / 100
                readonly property string unit: llm ? i18nd("cde-copper", "t/s") : modelData === "cpu" ? "C" : bat ? "B" : gpu ? "G" : "M"
                Layout.fillWidth: true; Layout.fillHeight: true
                // The cluster's three digits want more room than two.
                Layout.preferredWidth: gpu ? Math.round(3 * field.gpuWeight) : field.bars ? 3 : llm ? (joined ? 21 : 15) : 9
                implicitWidth: 0; implicitHeight: 0
                padding: 0; text: ""
                Accessible.name: llm ? i18nd("cde-copper", "LLM cluster: %1 t/s", value) + (joined ? ", " + field.root.gpuText : "")
                               : gpu ? field.root.gpuText
                               : modelData === "cpu" ? i18nd("cde-copper", "Processor %1 %", value)
                               : bat ? field.root.batteryText : i18nd("cde-copper", "Memory %1 %", value)
                selected: llm && field.root.llmDialog.visible && field.root.llmDialog.visualParent === reading
                onClicked: llm ? field.root.toggleLlm(reading, reading)
                         : bat ? field.root.run("systemsettings kcm_powerdevilprofilesconfig")
                         : field.root.run("plasma-systemmonitor || ksysguard")
                HoverHandler { onHoveredChanged: if (reading.llm) field.root.hoverSegment(reading, hovered) }
                background: Rectangle {
                    color: reading.selected ? field.colors.highlight
                         : reading.hovered ? Motif.mix(field.colors.window, Motif.shades(field.colors.window).top, 0.25) : "transparent"
                }
                readonly property color lit: selected ? field.colors.highlightText : field.colors.highlight
                contentItem: Item {
                    id: face
                    readonly property int labelSize: Math.max(6, Math.round(Math.min(height * 0.3, field.root.u(9))))
                    // The graphics processor in its own style; in the LED field
                    // it fills the cell, in the panel it stands over its letter.
                    GpuGauge {
                        visible: reading.gpu
                        anchors.fill: parent
                        anchors.topMargin: field.bars ? 1 : Math.max(2, Math.round(face.height * 0.12))
                        anchors.bottomMargin: anchors.topMargin
                        anchors.leftMargin: Math.max(2, Math.round(face.height * 0.1)); anchors.rightMargin: anchors.leftMargin
                        style: field.root.gpuGauge
                        load: field.root.gpuLoad; memory: field.root.gpuMemory
                        peak: field.root.gpuPeak; history: field.root.gpuHistory
                        lit: reading.lit; ink: reading.selected ? field.colors.highlightText : field.colors.windowText
                        well: Motif.shades(field.colors.window).bottom
                        label: "G"; labelSize: face.labelSize; font: field.colors.font
                    }
                    // Joined with the cluster: a lamp before the digits, lit
                    // while the graphics processor works, its load as a stripe.
                    Bevel {
                        id: gpuLamp
                        visible: reading.joined
                        readonly property bool busy: field.root.gpuLoad >= 8
                        sunken: !busy
                        surface: busy ? reading.lit : Motif.shades(field.colors.window).bottom
                        x: Math.max(2, Math.round(face.height * 0.12))
                        width: Math.round(lampText.implicitWidth + face.labelSize * 0.8); height: Math.round(face.labelSize * 1.5)
                        y: Math.round(leds.y + (leds.height - height) / 2)
                        Text {
                            id: lampText
                            anchors.centerIn: parent
                            text: i18nd("cde-copper", "GPU")
                            color: gpuLamp.busy ? field.colors.highlightText : field.colors.windowText
                            font.family: field.colors.font; font.pixelSize: Math.max(6, Math.round(face.labelSize * 0.85)); font.weight: Font.DemiBold
                        }
                    }
                    Item {
                        visible: reading.joined
                        x: gpuLamp.x; width: face.width - 2 * x
                        height: Math.max(2, Math.round(face.height * 0.08))
                        y: face.height - height - Math.max(1, Math.round(face.height * 0.06))
                        Rectangle { anchors.fill: parent; color: Qt.rgba(field.colors.windowText.r, field.colors.windowText.g, field.colors.windowText.b, 0.13) }
                        Rectangle { width: Math.round(parent.width * Math.min(100, field.root.gpuLoad) / 100); height: parent.height; color: reading.lit }
                    }
                    // LED: digits beside their unit, as large as the field allows.
                    Row {
                        id: leds
                        visible: !field.bars && !reading.gpu
                        anchors.verticalCenterOffset: reading.joined ? -Math.round(face.height * 0.06) : 0
                        anchors.horizontalCenterOffset: reading.joined ? Math.round(gpuLamp.width / 2) : 0
                        anchors.centerIn: parent
                        spacing: Math.max(1, Math.round(face.height * 0.08))
                        SegmentDigits {
                            anchors.bottom: parent.bottom
                            digitHeight: Math.max(9, Math.round(face.height * (reading.joined ? 0.6 : 0.7)))
                            text: {
                                const places = reading.llm ? 3 : 2;
                                const shown = String(Math.min(reading.value, Math.pow(10, places) - 1));
                                return " ".repeat(Math.max(0, places - shown.length)) + shown;
                            }
                            accent: reading.lit
                            ink: field.colors.windowText
                        }
                        Text {
                            anchors.bottom: parent.bottom
                            text: reading.unit
                            color: reading.lit
                            font.family: field.colors.font; font.pixelSize: face.labelSize; font.weight: Font.DemiBold
                        }
                    }
                    // Panel: an upright bar over its letter.
                    Column {
                        visible: field.bars && !reading.gpu
                        anchors.centerIn: parent
                        spacing: 1
                        Bevel {
                            anchors.horizontalCenter: parent.horizontalCenter
                            sunken: true
                            surface: Motif.shades(field.colors.window).bottom
                            width: Math.max(5, Math.round(face.width * 0.55))
                            height: Math.max(8, face.height - face.labelSize - 3)
                            Rectangle {
                                x: 2; width: parent.width - 4
                                readonly property int room: parent.height - 4
                                height: Math.round(room * reading.share)
                                y: 2 + room - height
                                color: reading.lit
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: reading.llm ? "L" : reading.unit
                            color: reading.lit
                            font.family: field.colors.font; font.pixelSize: face.labelSize; font.weight: Font.DemiBold
                        }
                    }
                }
            }
        }
    }
}
