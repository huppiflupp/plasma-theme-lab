import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

// One icon on the iconbar: the picture, its name below. RISC OS shows no
// hover; a pressed icon is drawn inverted for as long as the button is
// down, the program in front keeps a faint frame.
Item {
    id: item
    property string iconName: ""
    property string fallback: ""
    property var iconSource: null
    property string text: ""
    property string tip: ""
    property int size: 34
    property int labelHeight: 14
    // How wide the name may grow (window titles get more room).
    property real labelWidth: size * 2.6
    property bool active: false
    signal select()
    signal adjust()
    signal menu()

    implicitWidth: Math.max(size, label.visible ? Math.min(label.implicitWidth, labelWidth) : 0) + 8
    implicitHeight: size + labelHeight
    Layout.preferredWidth: implicitWidth
    Layout.fillHeight: true

    Rectangle {
        anchors.centerIn: picture
        width: picture.width + 6; height: picture.height + 6
        color: "transparent"
        border.width: 1
        border.color: Kirigami.Theme.textColor
        opacity: item.active ? 0.35 : 0
    }
    Kirigami.Icon {
        id: picture
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.max(2, (parent.height - item.size - item.labelHeight) / 2)
        width: item.size; height: item.size
        source: item.iconSource !== null ? item.iconSource : item.iconName
        fallback: item.fallback
        selected: mouse.pressed && mouse.pressedButtons & Qt.LeftButton
    }
    Text {
        id: label
        visible: item.text !== "" && item.labelHeight > 0
        anchors { top: picture.bottom; horizontalCenter: parent.horizontalCenter }
        width: Math.min(implicitWidth, item.labelWidth)
        text: item.text
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        color: Kirigami.Theme.textColor
        font.family: Kirigami.Theme.defaultFont.family
        font.pixelSize: Math.max(9, Math.round(item.labelHeight * 0.78))
    }
    // Plasma's tooltip: a window of its own beside the panel. A QQC2
    // tooltip stays inside the panel window, lies over the icons and
    // swallows the next click.
    PlasmaCore.ToolTipArea {
        anchors.fill: parent
        mainText: item.tip
        active: item.tip !== ""
        MouseArea {
            id: mouse
            anchors.fill: parent
            // RISC OS's buttons: Select (left), Menu (middle), Adjust (right).
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            onClicked: mouse => mouse.button === Qt.MiddleButton ? item.menu()
                              : mouse.button === Qt.RightButton ? item.adjust() : item.select()
        }
    }
}
