pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.ksysguard.sensors as Sensors
import "motif.js" as Motif

// The meters gathered in one sunken field in the clock's colours: as LED
// digits (the cluster's tokens per second, processor and memory load in
// per cent) or as a panel of bars. Each reading is its own button.
Bevel {
    id: field
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    property bool bars: false
    property var kinds: []
    readonly property bool hasLlm: kinds.indexOf("llm") >= 0
    readonly property var readings: (hasLlm ? ["llm"] : []).concat(kinds.indexOf("load") >= 0 ? ["cpu", "mem"] : [])
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
                readonly property int value: llm ? Math.round(field.root.llmTotal) : modelData === "cpu" ? field.cpuLoad : field.memLoad
                // Bars: the cluster against its best so far, load in per cent.
                readonly property real share: llm ? Math.min(1, field.root.llmTotal / Math.max(1, field.root.llmPeak)) : value / 100
                readonly property string unit: llm ? i18nd("cde-copper", "t/s") : modelData === "cpu" ? "C" : "M"
                Layout.fillWidth: true; Layout.fillHeight: true
                // The cluster's three digits want more room than two.
                Layout.preferredWidth: field.bars ? 1 : llm ? 5 : 3
                implicitWidth: 0; implicitHeight: 0
                padding: 0; text: ""
                Accessible.name: llm ? i18nd("cde-copper", "LLM cluster: %1 t/s", value)
                               : modelData === "cpu" ? i18nd("cde-copper", "Processor %1 %", value) : i18nd("cde-copper", "Memory %1 %", value)
                selected: llm && field.root.llmDialog.visible && field.root.llmDialog.visualParent === reading
                onClicked: llm ? field.root.toggleLlm(reading, reading) : field.root.run("plasma-systemmonitor || ksysguard")
                HoverHandler { onHoveredChanged: if (reading.llm) field.root.hoverSegment(reading, hovered) }
                background: Rectangle {
                    color: reading.selected ? field.colors.highlight
                         : reading.hovered ? Motif.mix(field.colors.window, Motif.shades(field.colors.window).top, 0.25) : "transparent"
                }
                readonly property color lit: selected ? field.colors.highlightText : field.colors.highlight
                contentItem: Item {
                    id: face
                    readonly property int labelSize: Math.max(6, Math.round(Math.min(height * 0.3, field.root.u(9))))
                    // LED: digits beside their unit, as large as the field allows.
                    Row {
                        visible: !field.bars
                        anchors.centerIn: parent
                        spacing: Math.max(1, Math.round(face.height * 0.08))
                        SegmentDigits {
                            anchors.bottom: parent.bottom
                            digitHeight: Math.max(9, Math.round(face.height * 0.7))
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
                        visible: field.bars
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
