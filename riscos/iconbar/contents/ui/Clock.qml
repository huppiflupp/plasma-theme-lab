import QtQuick
import org.kde.kirigami as Kirigami

// RISC OS's clock on the iconbar (!Alarm): the time in a white field with
// a black line, sunk into the bar; "2:23pm" as RISC OS writes it, or the
// locale's own short time.
Item {
    id: clock
    property bool riscos: false
    property date now: new Date()
    signal clicked()
    implicitWidth: text.implicitWidth + height * 0.9
    implicitHeight: 26
    Timer {
        interval: 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: clock.now = new Date()
    }
    // The bevel round the field: dark above and left, light below and right.
    Rectangle {
        anchors.fill: parent
        color: Kirigami.Theme.disabledTextColor
        Rectangle {
            x: 1; y: 1; width: parent.width - 1; height: parent.height - 1
            color: Kirigami.Theme.backgroundColor
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
        }
        Rectangle {
            x: 1; y: 1; width: parent.width - 2; height: parent.height - 2
            color: Kirigami.Theme.textColor
            Rectangle {
                anchors.fill: parent; anchors.margins: 1
                color: Kirigami.Theme.backgroundColor
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
            }
        }
    }
    Text {
        id: text
        anchors.centerIn: parent
        text: clock.riscos ? Qt.formatTime(clock.now, "h:mmap").toLowerCase()
                           : Qt.formatTime(clock.now, Qt.locale().timeFormat(Locale.ShortFormat))
        color: Kirigami.Theme.textColor
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        font.family: Kirigami.Theme.defaultFont.family
        font.pixelSize: Math.round(clock.height * 0.55)
    }
    MouseArea { anchors.fill: parent; onClicked: clock.clicked() }
}
