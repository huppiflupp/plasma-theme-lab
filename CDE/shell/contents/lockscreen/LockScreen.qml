import QtQuick
import org.kde.plasma.private.sessions as Sessions

// The lock screen after CDE's: the backdrop of the palette and a Motif
// dialog asking for the password. Plasma 6 takes the lock screen from the
// shell package, not the global theme: this file is the one file of the
// shell package org.cde.copper.shell, which takes everything else from
// org.kde.plasma.desktop. kscreenlocker provides `authenticator` and
// `kscreenlocker_userName`; when this file fails to load it falls back to
// its own theme, so a mistake here never locks anyone out. The texts are
// English, as in the rest of the theme. Colours.qml and images/ are
// rewritten by CDE Copper's tool with every palette.
Item {
    id: root
    property bool capsLockOn: false
    property bool locked: false
    property bool authSucceeded: false
    property string notification: ""
    // The conversation as Plasma's own lock screen keeps it: authentication
    // starts when the screen shows, every secret prompt is answered by what
    // the user enters then (a second one, say a one-time code, gets its own
    // entry), a failure waits three seconds and starts again.
    property bool awaiting: false        // a secret prompt waits for an answer
    property bool answered: false        // this conversation got one already
    property bool pendingSubmit: false   // entered before the prompt came
    property string pendingPassword: ""
    property bool noPassword: false      // succeeded without any prompt
    function submit(secret) {
        if (graceTimer.running || authenticator.graceLocked) return;
        if (root.noPassword) { Qt.quit(); return; }
        if (root.awaiting) {
            root.awaiting = false;
            root.answered = true;
            root.pendingSubmit = false;
            root.pendingPassword = "";
            authenticator.respond(secret === undefined ? password.text : secret);
        } else if (!root.answered) {
            root.pendingSubmit = true;
            root.pendingPassword = password.text;
            if (!authenticator.busy) authenticator.startAuthenticating();
        }
    }
    Timer {
        id: graceTimer
        interval: 3000
        onTriggered: {
            password.selectAll();
            password.forceActiveFocus();
            authenticator.startAuthenticating();
        }
    }

    Colours { id: colours }
    readonly property string font: "IBM Plex Sans Condensed"

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
        implicitWidth: Math.max(110, label.implicitWidth + 32)
        implicitHeight: 34
        // The default button's extra sunken ring, as Motif draws it.
        // The default button: a thin dark ring with a pixel of air, as a
        // lighter take on Motif's sunken default frame.
        color: "transparent"
        border.width: isDefault ? 1 : 0
        border.color: colours.dark
        opacity: enabled ? 1 : 0.5
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

    Sessions.SessionManagement { id: sessions }

    Rectangle { anchors.fill: parent; color: colours.desktop }
    Image {
        anchors.fill: parent
        source: "images/backdrop.png"
        fillMode: Image.Tile
        smooth: false
    }

    Rectangle {
        id: dialog
        anchors.centerIn: parent
        width: 500; height: content.implicitHeight + 70
        color: colours.ink
        Bevel {
            anchors.fill: parent; anchors.margins: 1
            Bevel {
                id: title
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                height: 26
                color: colours.title
                Text {
                    anchors.centerIn: parent
                    text: i18nd("cde-copper", "Screen Locked")
                    font.family: root.font; font.pixelSize: 14; font.weight: Font.DemiBold
                    color: colours.titleText
                }
            }
            Column {
                id: content
                anchors { left: parent.left; right: parent.right; top: title.bottom; margins: 20 }
                spacing: 12
                Row {
                    spacing: 16
                    Image { source: "images/logo.svg"; width: 56; height: 56; sourceSize: Qt.size(56, 56) }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2
                        Text {
                            id: clock
                            font.family: root.font; font.pixelSize: 26; color: colours.ink
                            text: Qt.formatTime(new Date(), "HH:mm")
                            Timer { interval: 1000; running: true; repeat: true; onTriggered: clock.text = Qt.formatTime(new Date(), "HH:mm") }
                        }
                        Text {
                            font.family: root.font; font.pixelSize: 13; color: colours.ink
                            text: kscreenlocker_userName.length === 0 ? i18nd("cde-copper", "This display is locked.")
                                                                       : i18nd("cde-copper", "This display is locked by %1.", kscreenlocker_userName)
                        }
                    }
                }
                Bevel {
                    // The password field, sunken as a Motif text field.
                    sunken: true
                    width: parent.width; height: 34
                    color: colours.field
                    TextInput {
                        id: password
                        anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                        verticalAlignment: TextInput.AlignVCenter
                        echoMode: TextInput.Password
                        passwordCharacter: "●"
                        font.family: root.font; font.pixelSize: 15
                        color: colours.ink
                        selectionColor: colours.accent
                        enabled: !graceTimer.running && !authenticator.graceLocked
                        focus: true
                        text: PasswordSync.password
                        onTextChanged: PasswordSync.password = text
                        Keys.onReturnPressed: root.submit()
                        Keys.onEnterPressed: root.submit()
                        Keys.onEscapePressed: {
                            root.pendingSubmit = false;
                            root.pendingPassword = "";
                            text = "";
                            text = Qt.binding(() => PasswordSync.password);
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: password.text.length === 0
                            text: authenticator.promptForSecret || i18nd("cde-copper", "Password")
                            font: password.font; color: colours.ink; opacity: 0.5
                        }
                    }
                    // The accent ring of the focused field.
                    Rectangle { anchors.fill: parent; anchors.margins: 2; color: "transparent"; border.width: password.activeFocus ? 1 : 0; border.color: colours.accent }
                }
                Text {
                    width: parent.width
                    visible: text.length > 0
                    wrapMode: Text.Wrap
                    text: [root.notification, root.capsLockOn ? i18nd("cde-copper", "Caps Lock is on.") : ""].filter(t => t).join("\n")
                    font.family: root.font; font.pixelSize: 13; font.weight: Font.DemiBold
                    color: colours.ink
                }
                Row {
                    anchors.right: parent.right
                    spacing: 10
                    MotifButton {
                        visible: sessions.canSwitchUser
                        text: i18nd("cde-copper", "Switch User")
                        onClicked: sessions.switchUser()
                    }
                    MotifButton {
                        isDefault: true
                        enabled: !graceTimer.running && !authenticator.graceLocked
                        text: i18nd("cde-copper", "Unlock")
                        onClicked: root.submit()
                    }
                }
            }
        }
    }

    Connections {
        target: authenticator
        function onFailed(kind) {
            // Fingerprint or smart card readers fail on their own; only the
            // password conversation reports here.
            if (kind !== undefined && kind !== 0) return;
            root.notification = i18nd("cde-copper", "The password was not accepted.");
            root.awaiting = false;
            root.answered = false;
            root.pendingSubmit = false;
            root.pendingPassword = "";
            graceTimer.restart();
        }
        function onBusyChanged() {
            if (!authenticator.busy && !root.authSucceeded) {
                password.selectAll();
                password.forceActiveFocus();
            }
        }
        function onInfoMessageChanged() { root.notification = authenticator.infoMessage; }
        function onErrorMessageChanged() { root.notification = authenticator.errorMessage; }
        function onPromptChanged() { if (authenticator.prompt) root.notification = authenticator.prompt; }
        function onPromptForSecretChanged() {
            // A further secret prompt in the same conversation wants its own
            // entry, not the password again.
            if (root.answered) {
                password.text = "";
                password.text = Qt.binding(() => PasswordSync.password);
            }
            root.awaiting = true;
            password.forceActiveFocus();
            if (root.pendingSubmit) {
                const secret = root.pendingPassword;
                root.pendingSubmit = false;
                root.submit(secret);
            }
        }
        function onSucceeded() {
            // Without any prompt (an account with no password) Plasma asks
            // for a click instead of unlocking at once.
            if (authenticator.hadPrompt === false) {
                root.noPassword = true;
                root.notification = i18nd("cde-copper", "No password is needed: press Unlock.");
                return;
            }
            root.authSucceeded = true;
            Qt.quit();
        }
    }
    Component.onCompleted: {
        password.forceActiveFocus();
        authenticator.startAuthenticating();
    }
}
