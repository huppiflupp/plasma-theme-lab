import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_visibilityMode: visibility.currentIndex
    property alias cfg_topEdge: topEdge.checked
    property alias cfg_windowsOnThisScreen: thisScreen.checked
    property alias cfg_consoleLabel: label.text
    property real cfg_consoleScale: 1.0
    Kirigami.FormLayout {
        ComboBox {
            id: visibility
            Kirigami.FormData.label: "Visibility:"
            model: ["Always visible", "Auto-hide / edge reveal", "Dodge windows"]
        }
        CheckBox { id: topEdge; text: "Top edge"; Kirigami.FormData.label: "Position:" }
        CheckBox {
            id: thisScreen
            Kirigami.FormData.label: "Window list:"
            text: "Only windows on this console's screen"
        }
        TextField { id: label; Kirigami.FormData.label: "Console label:" }
        SpinBox {
            Kirigami.FormData.label: "Size:"
            Layout.minimumWidth: Kirigami.Units.gridUnit * 7
            from: 75; to: 200; stepSize: 25
            value: Math.round(cfg_consoleScale * 100)
            textFromValue: value => value + " %"
            valueFromText: text => parseInt(text)
            onValueModified: cfg_consoleScale = value / 100
        }
    }
}
