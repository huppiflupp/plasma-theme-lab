import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_visibilityMode: visibility.currentIndex
    property alias cfg_topEdge: topEdge.checked
    Kirigami.FormLayout {
        ComboBox {
            id: visibility
            Kirigami.FormData.label: "Visibility:"
            model: ["Always visible", "Auto-hide / edge reveal", "Dodge windows"]
        }
        CheckBox { id: topEdge; text: "Top edge"; Kirigami.FormData.label: "Position:" }
    }
}
