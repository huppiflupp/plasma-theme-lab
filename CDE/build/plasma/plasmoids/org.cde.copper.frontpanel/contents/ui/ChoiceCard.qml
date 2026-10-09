import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

// One choice of a settings page shown as a picture with its name below:
// the clock styles, the small buttons' styles. The picture is the card's
// content; a card in a group is checked by the page, not by itself.
AbstractButton {
    id: card
    property string caption
    property real pictureHeight: Kirigami.Units.gridUnit * 3.5
    default property alias picture: well.data
    implicitWidth: Kirigami.Units.gridUnit * 7
    implicitHeight: pictureHeight + label.implicitHeight + Kirigami.Units.smallSpacing * 3
    focusPolicy: Qt.StrongFocus
    Accessible.role: Accessible.RadioButton
    Accessible.name: caption
    ToolTip.text: caption; ToolTip.visible: hovered && label.truncated
    background: Rectangle {
        radius: Kirigami.Units.cornerRadius
        color: card.checked ? Qt.alpha(Kirigami.Theme.highlightColor, 0.25)
             : card.hovered ? Qt.alpha(Kirigami.Theme.highlightColor, 0.1) : "transparent"
        border.color: card.checked || card.visualFocus ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.2)
        border.width: card.checked ? 2 : 1
    }
    contentItem: Item {
        Rectangle {
            id: well
            x: Kirigami.Units.smallSpacing; y: Kirigami.Units.smallSpacing
            width: parent.width - 2 * x; height: card.pictureHeight
            color: Kirigami.Theme.alternateBackgroundColor
            clip: true
        }
        Label {
            id: label
            anchors { top: well.bottom; topMargin: Kirigami.Units.smallSpacing; left: parent.left; right: parent.right }
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            font: Kirigami.Theme.smallFont
            text: card.caption
        }
    }
}
