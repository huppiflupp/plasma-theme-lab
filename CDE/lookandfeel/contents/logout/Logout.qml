import QtQuick
import "../splash" as Splash

// The logout dialog after CDE's dtsession "Logout Confirmation": a Motif
// dialog over the dimmed desktop. ksmserver-logout-greeter provides maysd,
// sdtype, ShutdownType, spdMethods, canLogout and softwareUpdatePending and
// connects the signals below; after `timeout` seconds the action it was
// called for is carried out, as in Plasma's own dialog. Colours and logo
// are the start-up screen's, which follow the palette.
Item {
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal haltUpdateRequested()
    onSuspendRequested: actionSent = true
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal rebootUpdateRequested()
    onCancelRequested: actionSent = true
    signal cancelRequested()
    onLockScreenRequested: actionSent = true
    signal lockScreenRequested()
    signal cancelSoftwareUpdateRequested()

    Splash.Colours { id: colours }
    readonly property string font: "IBM Plex Sans Condensed"
    property real timeout: 30
    property real remainingTime: timeout
    readonly property bool showAll: sdtype === ShutdownType.ShutdownTypeDefault
    // What the dialog was called for, and what the countdown does.
    readonly property string action: sdtype === ShutdownType.ShutdownTypeReboot ? "restart"
                                    : sdtype === ShutdownType.ShutdownTypeHalt ? "halt" : "logout"
    property bool actionSent: false
    function act(what) {
        if (actionSent || ((what === "restart" || what === "halt") ? !maysd : !canLogout)) return;
        actionSent = true;
        if (what === "restart") softwareUpdatePending ? rebootUpdateRequested() : rebootRequested();
        else if (what === "halt") softwareUpdatePending ? haltUpdateRequested() : haltRequested();
        else logoutRequested();
    }

    Timer {
        interval: 1000; running: !root.actionSent; repeat: true
        onTriggered: if (--root.remainingTime <= 0) root.act(root.action)
    }

    Keys.onEscapePressed: root.cancelRequested()
    Keys.onReturnPressed: root.act(root.action)
    Keys.onEnterPressed: root.act(root.action)
    focus: true

    component Bevel: Rectangle {
        property bool sunken: false
        property int depth: 2
        color: colours.face
        Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: parent.depth; color: parent.sunken ? colours.dark : colours.light }
        Rectangle { anchors { left: parent.left; top: parent.top; bottom: parent.bottom } width: parent.depth; color: parent.sunken ? colours.dark : colours.light }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: parent.depth; color: parent.sunken ? colours.light : colours.dark }
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: parent.depth; color: parent.sunken ? colours.light : colours.dark }
    }

    component MotifButton: Rectangle {
        id: button
        property alias text: label.text
        property bool isDefault: false
        signal clicked()
        implicitWidth: Math.max(96, label.implicitWidth + 28)
        implicitHeight: 34
        // The default button: a thin dark ring with a pixel of air, as a
        // lighter take on Motif's sunken default frame.
        color: "transparent"
        border.width: isDefault ? 1 : 0
        border.color: colours.dark
        Bevel {
            anchors.fill: parent; anchors.margins: button.isDefault ? 2 : 0
            sunken: mouse.pressed
            Text {
                id: label
                anchors.centerIn: parent
                font.family: root.font; font.pixelSize: 14
                color: colours.ink
            }
        }
        MouseArea { id: mouse; anchors.fill: parent; onClicked: button.clicked() }
    }

    // Clicking beside the dialog cancels, as Plasma's does.
    Rectangle {
        anchors.fill: parent
        color: "black"
        opacity: 0.45
        MouseArea { anchors.fill: parent; onClicked: root.cancelRequested() }
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.max(520, buttons.implicitWidth + 44)
        height: body.implicitHeight + 70
        color: colours.ink
        MouseArea { anchors.fill: parent }   // keeps clicks inside from cancelling
        Bevel {
            anchors.fill: parent; anchors.margins: 1
            Bevel {
                id: title
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                height: 26
                color: colours.title
                Text {
                    anchors.centerIn: parent
                    text: root.action === "restart" ? i18nd("cde-copper", "Restart") : root.action === "halt" ? i18nd("cde-copper", "Shut Down") : i18nd("cde-copper", "Log Out")
                    font.family: root.font; font.pixelSize: 14; font.weight: Font.DemiBold
                    color: colours.titleText
                }
            }
            Column {
                id: body
                anchors { left: parent.left; right: parent.right; top: title.bottom; margins: 20 }
                spacing: 16
                Row {
                    spacing: 16
                    Image { source: "../splash/images/logo.svg"; width: 56; height: 56; sourceSize: Qt.size(56, 56) }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 4
                        Text {
                            text: root.action === "restart" ? i18nd("cde-copper", "Restart the computer?") : root.action === "halt" ? i18nd("cde-copper", "Shut down the computer?") : i18nd("cde-copper", "End the session?")
                            font.family: root.font; font.pixelSize: 18; color: colours.ink
                        }
                        Text {
                            readonly property int seconds: Math.max(0, Math.ceil(root.remainingTime))
                            text: root.action === "restart" ? (softwareUpdatePending ? i18ndp("cde-copper", "Installing updates and restarting in %1 second.", "Installing updates and restarting in %1 seconds.", seconds) : i18ndp("cde-copper", "Restarting in %1 second.", "Restarting in %1 seconds.", seconds))
                                : root.action === "halt" ? (softwareUpdatePending ? i18ndp("cde-copper", "Installing updates and shutting down in %1 second.", "Installing updates and shutting down in %1 seconds.", seconds) : i18ndp("cde-copper", "Shutting down in %1 second.", "Shutting down in %1 seconds.", seconds))
                                : i18ndp("cde-copper", "Logging out in %1 second.", "Logging out in %1 seconds.", seconds)
                            font.family: root.font; font.pixelSize: 13; color: colours.ink; opacity: 0.8
                        }
                    }
                }
                Row {
                    id: buttons
                    anchors.right: parent.right
                    spacing: 8
                    MotifButton { text: i18nd("cde-copper", "Lock"); visible: root.showAll; onClicked: root.lockScreenRequested() }
                    MotifButton { text: i18nd("cde-copper", "Sleep"); visible: root.showAll && spdMethods.SuspendState; onClicked: root.suspendRequested(2) }
                    MotifButton { text: i18nd("cde-copper", "Hibernate"); visible: root.showAll && spdMethods.HibernateState; onClicked: root.suspendRequested(4) }
                    MotifButton {
                        text: i18nd("cde-copper", "Restart"); isDefault: root.action === "restart"
                        visible: maysd && (root.showAll || root.action === "restart")
                        onClicked: root.act("restart")
                    }
                    MotifButton {
                        text: i18nd("cde-copper", "Shut Down"); isDefault: root.action === "halt"
                        visible: maysd && (root.showAll || root.action === "halt")
                        onClicked: root.act("halt")
                    }
                    MotifButton {
                        text: i18nd("cde-copper", "Log Out"); isDefault: root.action === "logout"
                        visible: canLogout && (root.showAll || root.action === "logout")
                        onClicked: root.act("logout")
                    }
                    MotifButton { text: i18nd("cde-copper", "Cancel"); onClicked: root.cancelRequested() }
                }
            }
        }
    }
}
