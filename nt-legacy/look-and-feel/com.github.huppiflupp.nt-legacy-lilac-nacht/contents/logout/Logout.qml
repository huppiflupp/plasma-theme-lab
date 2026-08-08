import QtQuick
import org.kde.plasma.components as PlasmaComponents

Item {
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal cancelRequested()
    signal lockScreenRequested()

    property string mode
    property var currentAction

    Rectangle {
        anchors.fill: parent
        color: "#0a1012"
        opacity: 0.55
        MouseArea { anchors.fill: parent; onClicked: root.cancelRequested() }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 340
        height: 150
        color: "#2a3234"
        border.color: "#0a1012"
        border.width: 1

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }
            height: 22
            color: "#5c4a78"
            Text {
                anchors { left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }
                text: i18n("Beenden")
                color: "#ffffff"
                font.bold: true
            }
        }

        Row {
            anchors.centerIn: parent
            spacing: 10
            PlasmaComponents.Button {
                text: i18n("Abmelden"); onClicked: root.logoutRequested()
            }
            PlasmaComponents.Button {
                text: i18n("Neu starten"); onClicked: root.rebootRequested()
            }
            PlasmaComponents.Button {
                text: i18n("Herunterfahren"); onClicked: root.haltRequested()
            }
        }

        PlasmaComponents.Button {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter
                       bottomMargin: 10 }
            text: i18n("Abbrechen")
            onClicked: root.cancelRequested()
        }
    }
}
