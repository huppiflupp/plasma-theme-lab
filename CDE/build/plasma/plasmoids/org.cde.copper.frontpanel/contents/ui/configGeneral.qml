import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// The console itself: where it stands and how it looks. What it holds is
// on the Tiles page, the windows on the Windows and Workspaces page.
ConfigPage {
    id: page
    property alias cfg_visibilityMode: visibility.currentIndex
    property bool cfg_topEdge
    property int cfg_edge: -1
    property alias cfg_floating: floating.checked
    property alias cfg_everyScreen: everyScreen.checked
    property real cfg_consoleScale: 1.0
    property alias cfg_launcherLabels: launcherLabels.checked
    property alias cfg_hardContrast: hardContrast.checked
    property alias cfg_panelFrame: panelFrame.checked
    property alias cfg_consoleLabel: label.text

    // A short label on the control, the explanation below it in quiet type.
    component Hint: Label {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 26
        wrapMode: Text.WordWrap
        font: Kirigami.Theme.smallFont
        opacity: 0.7
    }

    Kirigami.FormLayout {
        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Placement") }
        ComboBox {
            // The wheel scrolls the page; it must not change a value in passing.
            wheelEnabled: false
            Kirigami.FormData.label: i18nd("cde-copper", "Screen edge:")
            model: [i18nd("cde-copper", "Bottom"), i18nd("cde-copper", "Top"), i18nd("cde-copper", "Left"), i18nd("cde-copper", "Right")]
            currentIndex: page.cfg_edge >= 0 ? page.cfg_edge : (page.cfg_topEdge ? 1 : 0)
            onActivated: index => { page.cfg_edge = index; page.cfg_topEdge = index === 1; }
        }
        CheckBox {
            id: floating
            text: i18nd("cde-copper", "Floating")
        }
        Hint { text: i18nd("cde-copper", "With a gap from the screen edge.") }
        ComboBox {
            id: visibility
            wheelEnabled: false
            Kirigami.FormData.label: i18nd("cde-copper", "Visibility:")
            model: [i18nd("cde-copper", "Always visible"), i18nd("cde-copper", "Auto-hide / edge reveal"), i18nd("cde-copper", "Dodge windows")]
        }
        CheckBox {
            id: everyScreen
            Kirigami.FormData.label: i18nd("cde-copper", "Screens:")
            text: i18nd("cde-copper", "A console on every screen")
        }
        Hint { text: i18nd("cde-copper", "Otherwise one console, on the primary screen.") }

        Item { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18nd("cde-copper", "Appearance") }
        SpinBox {
            wheelEnabled: false
            Kirigami.FormData.label: i18nd("cde-copper", "Size:")
            Layout.minimumWidth: Kirigami.Units.gridUnit * 7
            from: 75; to: 200; stepSize: 25
            value: Math.round(page.cfg_consoleScale * 100)
            textFromValue: value => value + " %"
            valueFromText: text => parseInt(text)
            onValueModified: page.cfg_consoleScale = value / 100
        }
        CheckBox {
            id: launcherLabels
            Kirigami.FormData.label: i18nd("cde-copper", "Tiles:")
            text: i18nd("cde-copper", "Names under the icons")
        }
        Hint { text: i18nd("cde-copper", "Without them the icons are larger and the names show as tooltips.") }
        CheckBox {
            id: hardContrast
            Kirigami.FormData.label: i18nd("cde-copper", "Text:")
            text: i18nd("cde-copper", "Hard contrast")
        }
        Hint { text: i18nd("cde-copper", "Black, or white on dark surfaces, instead of the palette's text colours.") }
        CheckBox {
            id: panelFrame
            Kirigami.FormData.label: i18nd("cde-copper", "Panel:")
            text: i18nd("cde-copper", "Frame behind the console")
        }

        Item { Kirigami.FormData.isSection: true }
        Advanced { id: advanced }
        TextField {
            id: label
            visible: advanced.open
            Kirigami.FormData.label: i18nd("cde-copper", "Console label:")
        }
        Hint { visible: advanced.open; text: i18nd("cde-copper", "The small caption under the clock.") }
    }
}
