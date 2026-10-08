pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import "launch.js" as Launch

// The network's subpanel: the WLANs around (a click joins one or drops
// the one in use), the radio switch and the network settings.
PlasmaCore.Dialog {
    id: networkPopup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { networkKeeper.opened(); networkBody.forceActiveFocus(); networkPopup.networkTries = 1; networkScan.connectSource(networkScan.command); }
    // The WLANs around, for the network popup: in use, SSID, signal, security
    // (nmcli's terse form, ":" inside a field escaped), then the radio, then
    // the saved connections. Read when the popup opens and every 10 s while
    // it is open; the first read asks for a fresh scan if the list is old.
    property var networks: []
    // Right after opening the scan it starts is still running and the list
    // comes back empty: ask again shortly, a few times, before "none".
    property int networkTries: 0
    readonly property bool networkSearching: networks.length === 0 && networkTries > 0 && networkTries < 4
    property bool wifiRadio: true
    property var savedConnections: []
    function readNetworks(stdout) {
        const parts = stdout.split("---\n");
        const seen = {};
        for (const line of (parts[0] || "").split("\n")) {
            const f = networkPopup.root.terseFields(line);
            if (f.length < 5 || !f[1]) continue;
            // A device sending the network itself (a hotspot) lists it in use
            // at 0 %: in use counts only with a signal.
            const signal = Number(f[2]) || 0;
            const active = f[0] === "*" && signal > 0;
            const entry = {ssid: f[1], signal: signal, secure: f[3] !== "" && f[3] !== "--", active: active, device: active ? f[4] : ""};
            const known = seen[entry.ssid];
            if (!known) seen[entry.ssid] = entry;
            else seen[entry.ssid] = {ssid: entry.ssid, signal: Math.max(known.signal, entry.signal), secure: known.secure || entry.secure,
                                     active: known.active || entry.active, device: known.device || entry.device};
        }
        networkPopup.networks = Object.values(seen).sort((a, b) => (b.active - a.active) || (b.signal - a.signal));
        networkPopup.wifiRadio = (parts[1] || "").trim() !== "disabled";
        networkPopup.savedConnections = (parts[2] || "").split("\n").filter(n => n).map(n => networkPopup.root.terseFields(n)[0]);
    }
    function signalIcon(signal) {
        return signal >= 75 ? "network-wireless-signal-excellent" : signal >= 50 ? "network-wireless-signal-good"
             : signal >= 25 ? "network-wireless-signal-ok" : "network-wireless-signal-weak";
    }
    // A saved network comes up by its connection; a new one is joined, and
    // Plasma's own agent asks for the passphrase if it needs one.
    function joinNetwork(ssid) {
        const device = networkPopup.root.wifiDevice ? " ifname " + Launch.quote(networkPopup.root.wifiDevice) : "";
        const command = networkPopup.savedConnections.indexOf(ssid) >= 0 ? "nmcli connection up id " + Launch.quote(ssid) + device
                                                                  : "nmcli device wifi connect " + Launch.quote(ssid) + device;
        networkPopup.root.run(command);
    }
    mainItem: Bevel {
        id: networkBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: networkKeeper; root: networkPopup.root; dialog: networkPopup; segment: networkPopup.visualParent; inside: networkHover.hovered }
        Timer { id: networkRetry; interval: 1500; onTriggered: networkScan.connectSource(networkScan.command) }
        P5Support.DataSource {
            id: networkScan
            engine: "executable"
            readonly property string command: "sh -c 'export LC_ALL=C; timeout 8s nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY,DEVICE device wifi list --rescan auto; echo ---; timeout 3s nmcli -t -f WIFI radio; echo ---; timeout 3s nmcli -t -f NAME connection show'"
            onNewData: function(sourceName, data) {
                disconnectSource(sourceName);
                networkPopup.readNetworks(data.stdout);
                if (networkPopup.networks.length === 0 && networkPopup.networkTries > 0 && networkPopup.networkTries < 4 && networkPopup.visible) {
                    networkPopup.networkTries++;
                    networkRetry.restart();
                }
            }
        }
        Timer { interval: 10000; repeat: true; running: networkPopup.visible; onTriggered: networkScan.connectSource(networkScan.command) }
        HoverHandler { id: networkHover }
        Keys.onPressed: networkKeeper.keyboard = true
        readonly property int rows: Math.max(1, Math.min(8, networkPopup.networks.length))
        width: 320; height: 41 + 4 + rows * 36 + 44
        surface: networkPopup.colors.window
        focus: true
        Keys.onEscapePressed: networkPopup.visible = false
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            Bevel {
                Layout.fillWidth: true; Layout.preferredHeight: 27; surface: networkPopup.colors.highlight
                Text { anchors.centerIn: parent; text: networkPopup.root.networkState; color: networkPopup.colors.highlightText; font.family: networkPopup.colors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Text {
                visible: networkPopup.networks.length === 0
                Layout.fillWidth: true; Layout.fillHeight: true
                text: !networkPopup.wifiRadio ? i18nd("cde-copper", "WLAN is switched off")
                    : networkPopup.networkSearching ? i18nd("cde-copper", "Searching for WLANs…") : i18nd("cde-copper", "No WLAN found")
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                color: networkPopup.colors.windowText; font.family: networkPopup.colors.font; font.pixelSize: 12
            }
            ListView {
                id: networkList
                visible: networkPopup.networks.length > 0
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; spacing: 2
                model: networkPopup.networks
                ScrollBar.vertical: ScrollBar { policy: networkList.contentHeight > networkList.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }
                delegate: ConsoleButton {
                    id: networkEntry
                    required property var modelData
                    width: networkList.width - (networkList.contentHeight > networkList.height ? 12 : 0)
                    height: 34
                    horizontal: true; surface: networkPopup.colors.window; foreground: networkPopup.colors.windowText
                    text: modelData.ssid
                    Accessible.name: i18nd("cde-copper", "%1, signal %2 %", modelData.ssid, modelData.signal)
                    iconName: ""
                    leftPadding: 36; rightPadding: 56
                    selected: modelData.active
                    Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: 22; height: 22; source: networkPopup.signalIcon(networkEntry.modelData.signal); active: false }
                    Row {
                        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        spacing: 4
                        Kirigami.Icon { visible: networkEntry.modelData.secure; width: 14; height: 14; source: "system-lock-screen"; active: false; anchors.verticalCenter: parent.verticalCenter }
                        Text {
                            text: networkEntry.modelData.signal + "%"
                            color: networkEntry.selected ? networkPopup.colors.highlightText : networkPopup.colors.windowText
                            font.family: networkPopup.colors.font; font.pixelSize: 11
                        }
                    }
                    // The one in use: a click disconnects it.
                    onClicked: {
                        networkPopup.visible = false;
                        if (modelData.active) networkPopup.root.run("nmcli device disconnect " + Launch.quote(modelData.device));
                        else networkPopup.joinNetwork(modelData.ssid);
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                ConsoleButton {
                    Layout.fillWidth: true; implicitHeight: 36; horizontal: true; iconSize: 20
                    text: networkPopup.wifiRadio ? i18nd("cde-copper", "WLAN off") : i18nd("cde-copper", "WLAN on")
                    iconName: networkPopup.wifiRadio ? "network-wireless-disconnected" : "network-wireless"
                    surface: networkPopup.colors.window; foreground: networkPopup.colors.windowText
                    onClicked: {
                        networkPopup.wifiRadio = !networkPopup.wifiRadio;
                        networkPopup.root.run("nmcli radio wifi " + (networkPopup.wifiRadio ? "on" : "off"));
                        networkScan.connectSource(networkScan.command);
                    }
                }
                ConsoleButton {
                    Layout.fillWidth: true; implicitHeight: 36; horizontal: true; iconSize: 20
                    text: i18nd("cde-copper", "Settings…"); iconName: "preferences-system-network"
                    surface: networkPopup.colors.window; foreground: networkPopup.colors.windowText
                    onClicked: { networkPopup.visible = false; networkPopup.root.run(Launch.resolve("@settings kcm_networkmanagement", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg))); }
                }
            }
        }
    }
}
