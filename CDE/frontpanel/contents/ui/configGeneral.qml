import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_visibilityMode: visibility.currentIndex
    property bool cfg_topEdge
    property int cfg_edge: -1
    property alias cfg_windowsOnThisScreen: thisScreen.checked
    property alias cfg_consoleLabel: label.text
    property real cfg_consoleScale: 1.0
    property alias cfg_hideTrayVolume: hideVolume.checked
    property alias cfg_hideTrayIcons: hideIcons.checked
    Kirigami.FormLayout {
        ComboBox {
            id: visibility
            Kirigami.FormData.label: "Visibility:"
            model: ["Always visible", "Auto-hide / edge reveal", "Dodge windows"]
        }
        ComboBox {
            Kirigami.FormData.label: "Screen edge:"
            model: ["Bottom", "Top", "Left", "Right"]
            currentIndex: cfg_edge >= 0 ? cfg_edge : (cfg_topEdge ? 1 : 0)
            onActivated: index => { cfg_edge = index; cfg_topEdge = index === 1; }
        }
        CheckBox {
            id: thisScreen
            Kirigami.FormData.label: "Window list:"
            text: "Only windows on this console's screen"
        }
        CheckBox {
            id: hideVolume
            Kirigami.FormData.label: "System tray:"
            text: "Leave the volume to the console"
        }
        CheckBox {
            id: hideIcons
            text: "Status icons only behind the console's button"
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
