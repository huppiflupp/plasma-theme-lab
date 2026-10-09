pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.calendar as PlasmaCalendar

ConfigPage {
    id: page
    property alias cfg_clockOpensApp: opensApp.checked
    property alias cfg_calendarCommand: command.text
    property var cfg_enabledCalendarPlugins: []
    property string cfg_clockStyle: "digital"
    property string cfg_clockDial: "cde"
    property alias cfg_clockSeconds: seconds.checked
    property alias cfg_clockSegmentEdge: segmentEdge.checked
    property alias cfg_clockSegmentShadow: segmentShadow.checked
    readonly property var styles: [{text: i18nd("cde-copper", "Digital"), value: "digital"}, {text: i18nd("cde-copper", "Seven-segment"), value: "segments"},
                                   {text: i18nd("cde-copper", "Analog"), value: "analog"},
                                   {text: i18nd("cde-copper", "LED matrix (red)"), value: "ledmatrix"}, {text: i18nd("cde-copper", "Flip clock"), value: "flipclock"},
                                   {text: i18nd("cde-copper", "VFD (blue-green)"), value: "vfd"}, {text: i18nd("cde-copper", "VFD behind blue glass"), value: "vfd-blue"},
                                   {text: i18nd("cde-copper", "VFD aqua, wide halo"), value: "vfd-aqua"}, {text: i18nd("cde-copper", "Flip-disc (yellow)"), value: "flipdisc"},
                                   {text: i18nd("cde-copper", "Panaplex (gas discharge)"), value: "panaplex"}, {text: i18nd("cde-copper", "Panaplex in the palette's colour"), value: "panaplex-palette"}, {text: i18nd("cde-copper", "Odometer drums"), value: "odometer"},
                                   {text: i18nd("cde-copper", "Pixel type (palette)"), value: "pixel"}, {text: i18nd("cde-copper", "Plasma screen"), value: "plasma"}]
    readonly property var dials: [{text: i18nd("cde-copper", "CDE (round, as dtclock)"), value: "cde"}, {text: i18nd("cde-copper", "Motif (square well)"), value: "motif"},
                                  {text: i18nd("cde-copper", "Roman numerals"), value: "roman"}, {text: i18nd("cde-copper", "Plain (no dial)"), value: "plain"}]

    // Each style as a small running clock, in the system colours (the
    // console's palette is not known here). The name stays as a caption.
    property date now: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: page.now = new Date() }
    component FaceChoice: ChoiceCard {
        id: choice
        required property var modelData
        property string style
        property string dial
        caption: modelData.text
        ClockFace {
            anchors.fill: parent; anchors.margins: 2
            style: choice.style; dial: choice.dial
            now: page.now
            seconds: page.cfg_clockSeconds
            segmentShadow: page.cfg_clockSegmentShadow
            segmentEdge: page.cfg_clockSegmentEdge
            ink: Kirigami.Theme.textColor
            accent: Kirigami.Theme.highlightColor
            lamp: Kirigami.Theme.highlightColor
            dialColor: Kirigami.Theme.backgroundColor
            tile: Kirigami.Theme.alternateBackgroundColor
        }
    }

    PlasmaCalendar.EventPluginsManager {
        id: manager
        Component.onCompleted: populateEnabledPluginsList(page.cfg_enabledCalendarPlugins)
    }

    Kirigami.FormLayout {
        GridLayout {
            Kirigami.FormData.label: i18nd("cde-copper", "Clock display:")
            columns: 5
            columnSpacing: Kirigami.Units.smallSpacing; rowSpacing: Kirigami.Units.smallSpacing
            Repeater {
                model: page.styles
                delegate: FaceChoice {
                    style: modelData.value
                    dial: page.cfg_clockDial
                    checked: page.cfg_clockStyle === modelData.value
                    onClicked: page.cfg_clockStyle = modelData.value
                }
            }
        }
        RowLayout {
            Kirigami.FormData.label: i18nd("cde-copper", "Dial:")
            visible: page.cfg_clockStyle === "analog"
            spacing: Kirigami.Units.smallSpacing
            Repeater {
                model: page.dials
                delegate: FaceChoice {
                    style: "analog"
                    dial: modelData.value
                    checked: page.cfg_clockDial === modelData.value
                    onClicked: page.cfg_clockDial = modelData.value
                }
            }
        }
        CheckBox { id: seconds; text: i18nd("cde-copper", "Show seconds") }
        CheckBox {
            id: segmentShadow
            text: i18nd("cde-copper", "Unlit segments faintly visible")
            enabled: page.cfg_clockStyle === "segments"
        }
        CheckBox {
            id: segmentEdge
            text: i18nd("cde-copper", "Black edge around lit segments")
            enabled: page.cfg_clockStyle === "segments"
        }
        Label {
            text: i18nd("cde-copper", "Colours follow the palette: dial in the text-field colour, hands in the text colour,\nsecond hand and lit segments in the selection colour.")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true }
        RadioButton {
            Kirigami.FormData.label: i18nd("cde-copper", "Clicking the clock:")
            text: i18nd("cde-copper", "Shows the month and the day's events")
            checked: !opensApp.checked
        }
        RadioButton { id: opensApp; text: i18nd("cde-copper", "Opens the calendar application") }
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Events from") }
        ColumnLayout {
            Repeater {
                model: manager.model
                delegate: CheckBox {
                    // Roles through model.*: "display" would clash with
                    // AbstractButton.display.
                    required property var model
                    readonly property string pluginId: model.pluginId
                    text: model.display
                    checked: page.cfg_enabledCalendarPlugins.indexOf(pluginId) >= 0
                    onToggled: {
                        const list = page.cfg_enabledCalendarPlugins.filter(id => id !== pluginId);
                        if (checked) list.push(pluginId);
                        page.cfg_enabledCalendarPlugins = list;
                    }
                }
            }
        }
        Label {
            text: i18nd("cde-copper", "Appointments come from KOrganizer/Akonadi (\"PIM Events\").")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
        Item { Kirigami.FormData.isSection: true }
        Advanced { id: advanced }
        TextField {
            id: command
            visible: advanced.open
            Kirigami.FormData.label: i18nd("cde-copper", "Calendar application:")
            placeholderText: "@calendar"
            Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        }
        Label {
            visible: advanced.open
            text: i18nd("cde-copper", "@calendar starts Merkuro or KOrganizer, whichever is installed.\nAny command or app:<desktop id> works too.")
            opacity: 0.7
            font: Kirigami.Theme.smallFont
        }
    }
}
