pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.ksysguard.sensors as Sensors
import "motif.js" as Motif

// The session block: an arrow strip like the launchers' over square
// quarter buttons, two to a column. The arrow opens the tray's hidden
// icons; which quarters there are is a setting (smallButtons), and how
// they look another (smallStyle):
//   family       all quarters alike, the meters among the keys
//   instruments  the same, the meters sunken in the clock's colours
//   led          the meters as one LED field over a row of keys
//   panel        the meters as one panel of bars beside the keys
// Upright the LED field and the panel have no room: instruments then.
GridLayout {
    id: session
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    rows: session.root.vertical ? 1 : 2
    columns: session.root.vertical ? 2 : 1
    rowSpacing: 1; columnSpacing: 1
    Layout.fillWidth: session.root.vertical; Layout.fillHeight: !session.root.vertical
    // The side of one square, from the space beside the arrow strip.
    readonly property int quarter: Math.max(10, Math.floor(((session.root.vertical ? width : height) - session.root.u(13) - 2) / 2))
    readonly property string style: {
        const wanted = Plasmoid.configuration.smallStyle;
        if (["instruments", "led", "panel"].indexOf(wanted) < 0) return "family";
        return session.root.vertical && wanted !== "instruments" ? "instruments" : wanted;
    }
    readonly property var meters: session.root.smallButtons.filter(k => k === "load" || k === "llm")
    readonly property var keys: session.root.smallButtons.filter(k => k !== "load" && k !== "llm")
    // The LED field and the panel gather the meters; without any, keys only.
    readonly property bool grouped: (style === "led" || style === "panel") && meters.length > 0
    readonly property bool ledRow: grouped && style === "led"
    readonly property var gridKinds: grouped ? keys : session.root.smallButtons
    readonly property int pairs: Math.max(1, Math.ceil(gridKinds.length / 2))
    // The LED field: about two quarters for each meter's digits.
    readonly property int ledColumns: Math.max(gridKinds.length, 2 * meters.length)
    // The panel: a bar per reading (the cluster's, the processor's, the memory's).
    readonly property int barCount: (meters.indexOf("llm") >= 0 ? 1 : 0) + (meters.indexOf("load") >= 0 ? 2 : 0)
    readonly property int panelWidth: grouped && style === "panel" ? Math.round(quarter * (0.35 + 0.45 * barCount)) : 0
    readonly property int blockWidth: ledRow ? ledColumns * quarter + ledColumns - 1
        : (panelWidth > 0 ? panelWidth + (gridKinds.length > 0 ? 1 : 0) : 0)
          + (gridKinds.length > 0 ? pairs * quarter + pairs - 1 : 0)
    Layout.preferredWidth: session.root.vertical ? -1 : blockWidth
    Layout.preferredHeight: session.root.vertical ? pairs * quarter + pairs - 1 : -1
    ConsoleButton {
        Layout.row: 0
        Layout.column: session.root.vertical && !session.root.atRight ? 1 : 0
        Layout.fillWidth: !session.root.vertical; Layout.fillHeight: session.root.vertical
        Layout.preferredHeight: session.root.vertical ? -1 : session.root.u(13)
        Layout.preferredWidth: session.root.vertical ? session.root.u(13) : -1
        text: ""
        Accessible.name: i18nd("cde-copper", "Hidden Icons")
        contentItem: Text {
            text: session.root.arrowGlyph
            color: session.colors.panelText; font.pixelSize: session.root.u(12)
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
        onClicked: session.root.showHiddenIcons()
    }
    RowLayout {
        Layout.row: session.root.vertical ? 0 : 1
        Layout.column: session.root.vertical && !session.root.atRight ? 0 : (session.root.vertical ? 1 : 0)
        Layout.alignment: Qt.AlignCenter
        Layout.preferredWidth: session.root.vertical ? 2 * session.quarter + 1 : session.blockWidth
        Layout.preferredHeight: session.root.vertical ? session.pairs * session.quarter + session.pairs - 1 : 2 * session.quarter + 1
        spacing: 1
        Loader {
            active: session.grouped && session.style === "panel"
            visible: active
            Layout.fillHeight: true
            Layout.preferredWidth: session.panelWidth
            sourceComponent: Instruments { root: session.root; colors: session.colors; bars: true; kinds: session.meters }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            spacing: 1
            Loader {
                active: session.ledRow
                visible: active
                Layout.fillWidth: true
                // Without keys below the field takes the whole height.
                Layout.fillHeight: session.gridKinds.length === 0
                Layout.preferredHeight: session.quarter
                sourceComponent: Instruments { root: session.root; colors: session.colors; bars: false; kinds: session.meters }
            }
            GridLayout {
                visible: session.gridKinds.length > 0
                Layout.fillWidth: true; Layout.fillHeight: true
                // Across: columns of two, filled top to bottom; upright:
                // rows of two. Under the LED field the keys stand in one row.
                flow: session.root.vertical ? GridLayout.LeftToRight : GridLayout.TopToBottom
                rows: session.root.vertical ? session.pairs : session.ledRow ? 1 : 2
                columns: session.root.vertical ? 2 : session.ledRow ? session.gridKinds.length : session.pairs
                rowSpacing: 1; columnSpacing: 1
                Repeater {
                    model: session.gridKinds
                    delegate: Loader {
                        required property string modelData
                        required property int index
                        // An odd last quarter takes both places of its pair: no gap.
                        readonly property bool stretched: !session.ledRow && index === session.gridKinds.length - 1 && index % 2 === 0
                        Layout.rowSpan: stretched && !session.root.vertical ? 2 : 1
                        Layout.columnSpan: stretched && session.root.vertical ? 2 : 1
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Layout.preferredWidth: 1; Layout.preferredHeight: 1
                        sourceComponent: modelData === "load" ? loadMeter : modelData === "llm" ? llmMeterComponent : quarterButton
                        onLoaded: {
                            if (item.kind !== undefined) item.kind = modelData;
                            else item.well = Qt.binding(() => session.style === "instruments");
                        }
                    }
                }
            }
        }
    }
    Component { id: llmMeterComponent; LlmMeter { root: session.root; colors: session.colors } }
    Component { id: loadMeter; LoadMeter { root: session.root; colors: session.colors } }
    Component { id: quarterButton; QuarterButton { root: session.root } }

    // One of the session block's quarters, by kind.
    component QuarterButton: SmallButton {
        id: quarter
        // The console (main.qml): given, never looked up.
        required property var root
        property string kind: ""
        iconName: {
            switch (kind) {
            case "configure": return "cde-console-configure";
            case "lock": return "system-lock-screen";
            case "desktop": return "user-desktop";
            case "volume": return quarter.root.muted ? "audio-volume-muted" : "audio-volume-high";
            case "network": return quarter.root.networkIcon;
            case "logout": return "system-log-out";
            }
            return "";
        }
        Accessible.name: {
            switch (kind) {
            case "configure": return i18nd("cde-copper", "Configure Front Console");
            case "lock": return i18nd("cde-copper", "Lock Screen");
            case "desktop": return i18nd("cde-copper", "Show Desktop");
            case "volume": return i18nd("cde-copper", "Volume %1", quarter.root.volumeState);
            case "network": return quarter.root.networkState;
            case "logout": return i18nd("cde-copper", "Leave Session...");
            }
            return "";
        }
        onClicked: {
            switch (kind) {
            case "configure": Plasmoid.internalAction("configure").trigger(); break;
            case "lock": quarter.root.run(quarter.root.dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock"); break;
            // KWin's D-Bus showDesktop(bool) is accepted but does nothing in
            // Plasma 6.7; its own "Show Desktop" shortcut toggles reliably.
            case "desktop": quarter.root.run(quarter.root.dbus + " org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut 'Show Desktop'"); break;
            case "volume": quarter.root.volumeDialog.visualParent = quarter; quarter.root.volumeDialog.visible = !quarter.root.volumeDialog.visible; break;
            case "network": quarter.root.networkDialog.visualParent = quarter; quarter.root.networkDialog.visible = !quarter.root.networkDialog.visible; break;
            case "logout": quarter.root.run(quarter.root.dbus + " org.kde.LogoutPrompt /LogoutPrompt promptAll"); break;
            }
        }
        HoverHandler { onHoveredChanged: if (quarter.kind === "volume" || quarter.kind === "network") quarter.root.hoverSegment(quarter, hovered) }
        WheelHandler {
            enabled: quarter.kind === "volume"
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: event => quarter.root.setVolume(quarter.root.volume + (event.angleDelta.y > 0 ? 5 : -5))
        }
    }

    component LlmMeter: ConsoleButton {
        id: llmMeter
        // The console (main.qml) and its colours: given, never looked up.
        required property var root
        required property var colors
        implicitWidth: 0; implicitHeight: 0
        padding: 0; text: ""
        Accessible.name: i18nd("cde-copper", "LLM cluster: %1 t/s", Math.round(llmMeter.root.llmTotal))
        Binding { target: llmMeter.root; property: "llmSmallVisible"; value: llmMeter.visible && llmMeter.Window.window !== null && llmMeter.Window.window.visible; restoreMode: Binding.RestoreBindingOrValue }
        // As an instrument (smallStyle): sunken, the clock's colours.
        surface: llmMeter.well ? llmMeter.colors.window : llmMeter.colors.panel
        readonly property color ink: selected ? llmMeter.colors.highlightText : llmMeter.well ? llmMeter.colors.highlight : llmMeter.colors.panelText
        selected: llmMeter.root.llmDialog.visible && llmMeter.root.llmDialog.visualParent === llmMeter
        onClicked: llmMeter.root.toggleLlm(llmMeter, llmMeter)
        HoverHandler { onHoveredChanged: llmMeter.root.hoverSegment(llmMeter, hovered) }
        contentItem: Item {
            readonly property int side: Math.min(width, height)
            Text {
                x: 0; y: Math.round(parent.height * 0.12); width: parent.width
                text: Math.round(llmMeter.root.llmTotal)
                horizontalAlignment: Text.AlignHCenter
                color: llmMeter.ink; font.family: llmMeter.colors.font
                font.pixelSize: Math.max(7, Math.round(parent.side * 0.36)); font.weight: Font.DemiBold
                fontSizeMode: Text.Fit; minimumPixelSize: 6
            }
            Text {
                x: 0; y: Math.round(parent.height * 0.59); width: parent.width
                text: i18nd("cde-copper", "t/s")
                horizontalAlignment: Text.AlignHCenter
                color: llmMeter.ink; font.family: llmMeter.colors.font
                font.pixelSize: Math.max(6, Math.round(parent.side * 0.2))
            }
        }
    }

    // CPU and memory load as two sunken Motif meters (Plasma's own sensors,
    // ksystemstats), a click opens the system monitor.
    component LoadMeter: ConsoleButton {
        id: meter
        // The console (main.qml) and its colours: given, never looked up.
        required property var root
        required property var colors
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.preferredWidth: 1; Layout.preferredHeight: 1
        implicitWidth: 0; implicitHeight: 0
        padding: 0; text: ""
        readonly property int cpuLoad: Math.round(Math.max(0, Math.min(100, Number(cpuSensor.value) || 0)))
        readonly property int memLoad: Math.round(Math.max(0, Math.min(100, Number(memSensor.value) || 0)))
        Accessible.name: i18nd("cde-copper", "Processor %1 %, memory %2 %", cpuLoad, memLoad)
        onClicked: meter.root.run("plasma-systemmonitor || ksysguard")
        // As an instrument (smallStyle): sunken, the clock's colours.
        surface: meter.well ? meter.colors.window : meter.colors.panel
        Sensors.Sensor { id: cpuSensor; sensorId: "cpu/all/usage"; updateRateLimit: 2000 }
        Sensors.Sensor { id: memSensor; sensorId: "memory/physical/usedPercent"; updateRateLimit: 2000 }
        contentItem: Item {
            id: gauges
            // Whole pixels at every console size.
            readonly property int side: Math.min(width, height)
            readonly property int barWidth: Math.max(4, Math.round(side * 0.2))
            readonly property int barHeight: Math.max(8, Math.round(side * 0.56))
            readonly property int labelSize: Math.max(6, Math.round(side * 0.2))
            Row {
                anchors.centerIn: parent
                spacing: Math.max(2, Math.round(gauges.side * 0.12))
                Repeater {
                    model: [{label: "C", load: meter.cpuLoad}, {label: "M", load: meter.memLoad}]
                    delegate: Column {
                        required property var modelData
                        spacing: 1
                        Bevel {
                            sunken: true
                            surface: meter.well ? Motif.shades(meter.colors.window).bottom : meter.colors.field
                            width: gauges.barWidth; height: gauges.barHeight
                            Rectangle {
                                x: 2; width: parent.width - 4
                                readonly property int room: parent.height - 4
                                height: Math.round(room * modelData.load / 100)
                                y: 2 + room - height
                                color: meter.colors.highlight
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.label
                            font.family: meter.colors.font; font.pixelSize: gauges.labelSize; font.weight: Font.DemiBold
                            color: meter.well ? meter.colors.highlight : meter.colors.panelText
                        }
                    }
                }
            }
        }
    }

    // A quarter launcher: the icon follows the button, whole pixels.
    component SmallButton: ConsoleButton {
        id: small
        // For CDE Copper's own icons under another icon theme.
        property string fallbackName: iconName === "cde-console-configure" ? "configure" : ""
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.preferredWidth: 1; Layout.preferredHeight: 1
        implicitWidth: 0; implicitHeight: 0
        padding: 0; text: ""
        contentItem: Item {
            Kirigami.Icon {
                readonly property int side: Math.max(8, Math.floor(Math.min(small.width, small.height) * 0.6))
                width: side; height: side
                x: Math.round((parent.width - side) / 2); y: Math.round((parent.height - side) / 2)
                source: small.iconName
                fallback: small.fallbackName
                active: false
                // Not snapped down to 16/22/32: the icon grows with the console.
                roundToIconSize: false
            }
        }
    }
}
