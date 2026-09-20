pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.taskmanager as TaskManager
import org.kde.plasma.private.kicker as Kicker

PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Layout.minimumWidth: 760
    Layout.preferredWidth: 1040
    Layout.maximumWidth: 1040
    Layout.minimumHeight: 116
    Layout.preferredHeight: 116
    Layout.maximumHeight: 116
    property string popupTitle: ""
    property var entries: []
    property date now: new Date()
    property string activeSection: ""
    property string networkState: "Network"
    property string volumeState: "Audio"
    readonly property string dbus: "qdbus-qt6"

    function run(command) {
        if (command.indexOf("kstart ") === 0) command = "systemd-run --user --collect --quiet -- " + command.substring(7);
        runner.connectSource(command);
    }
    function openSection(title, list, anchor) {
        if (popup.visible && activeSection === title) { popup.visible = false; return; }
        popupTitle = title; entries = list; activeSection = title;
        popup.visualParent = anchor;
        popup.visible = true;
    }
    function entry(label, icon, command) { return {label: label, icon: icon, command: command}; }
    function configurePanel() {
        const modes = ["none", "autohide", "dodgewindows"];
        const mode = modes[Math.max(0, Math.min(2, Plasmoid.configuration.visibilityMode))];
        const edge = Plasmoid.configuration.topEdge ? "top" : "bottom";
        const script = "for (var p of panels()) { for (var w of p.widgets()) { if (w.type === 'org.cde.copper.frontpanel') { p.hiding = '" + mode + "'; p.location = '" + edge + "'; } } }";
        run(dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + "'" + script.replace(/'/g, "'\\''") + "'");
    }
    Connections {
        target: Plasmoid.configuration
        function onVisibilityModeChanged() { root.configurePanel(); }
        function onTopEdgeChanged() { root.configurePanel(); }
    }
    function appEntries() {
        return [entry("All Applications...", "cde-menu", "@applications"),
                entry("File Manager", "folder", "kstart dolphin"),
                entry("Terminal", "utilities-terminal", "kstart konsole --profile 'CDE Copper'"),
                entry("Text Editor", "accessories-text-editor", "kstart kate"),
                entry("Web Browser", "internet-web-browser", "xdg-open https://www.kde.org"),
                entry("System Settings", "preferences-system", "kstart systemsettings"),
                entry("Run Application...", "edit-find", dbus + " org.kde.krunner /App org.kde.krunner.App.display")];
    }
    Kicker.AppsModel { id: allApps; flat: true; sorted: true; autoPopulate: true; appletInterface: Plasmoid }
    function fileEntries() {
        return [entry("Home", "user-home", "kstart dolphin ~"),
                entry("Documents", "folder-documents", "kstart dolphin ~/Documents"),
                entry("Downloads", "folder-download", "kstart dolphin ~/Downloads"),
                entry("Pictures", "folder-pictures", "kstart dolphin ~/Pictures"),
                entry("File System", "drive-harddisk", "kstart dolphin /"),
                entry("Trash", "user-trash", "kstart dolphin trash:/")];
    }
    function systemEntries() {
        return [entry("System Settings", "preferences-system", "kstart systemsettings"),
                entry("Audio", "audio-volume-high", "kstart systemsettings kcm_pulseaudio"),
                entry("Network", "network-workgroup", "kstart systemsettings kcm_networkmanagement"),
                entry("Display", "computer", "kstart systemsettings kcm_kscreen"),
                entry("Lock Screen", "system-lock-screen", dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock"),
                entry("Leave Session...", "system-log-out", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptAll")];
    }
    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0) console.warn("CDE action:", sourceName, data.stderr);
            disconnectSource(sourceName);
        }
    }
    P5Support.DataSource {
        engine: "executable"
        interval: 5000
        connectedSources: ["LC_ALL=C nmcli -t -f STATE general", "wpctl get-volume @DEFAULT_AUDIO_SINK@"]
        onNewData: function(sourceName, data) {
            if (sourceName.indexOf("nmcli") >= 0) root.networkState = data.stdout.trim() === "connected" ? "Connected" : "Offline";
            else {
                const match = data.stdout.match(/Volume: ([0-9.]+)/);
                root.volumeState = data.stdout.indexOf("MUTED") >= 0 ? "Muted" : match ? Math.round(Number(match[1])*100) + "%" : "Audio";
            }
        }
    }
    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.TasksModel {
        id: tasks
        virtualDesktop: desktops.currentDesktop
        filterByVirtualDesktop: true
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    fullRepresentation: Bevel {
        id: frontConsole
        implicitWidth: 1040; implicitHeight: 116
        surface: "#367785"
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 4
                Bevel {
                    Layout.preferredWidth: 92; Layout.fillHeight: true
                    surface: "#86a4aa"
                    Column {
                        anchors.centerIn: parent; spacing: 0
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "ddd").toUpperCase(); color: "#38565c"; font.pixelSize: 10; font.family: "Noto Sans" }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "HH:mm"); color: "#10262b"; font.pixelSize: 24; font.family: "Noto Sans Mono" }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "dd MMM").toUpperCase(); color: "#10262b"; font.pixelSize: 10; font.family: "Noto Sans" }
                    }
                }
                Repeater {
                    model: [
                        {label: "Tools", icon: "cde-menu", command: "", group: "Applications"},
                        {label: "Files", icon: "folder", command: "kstart dolphin", group: "Places"},
                        {label: "Terminal", icon: "utilities-terminal", command: "kstart konsole --profile 'CDE Copper'", group: "Terminal"},
                        {label: "Editor", icon: "accessories-text-editor", command: "kstart kate", group: "Editor"}
                    ]
                    delegate: ColumnLayout {
                        id: leftModule
                        required property var modelData
                        Layout.fillWidth: true; Layout.preferredWidth: 68; Layout.fillHeight: true; spacing: 1
                        ConsoleButton {
                            id: arrow
                            text: ""; Layout.fillWidth: true; Layout.preferredHeight: 13
                            Accessible.name: "Open " + leftModule.modelData.group
                            contentItem: Text { text: "▴"; color: "#c9dedb"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            onClicked: root.openSection(leftModule.modelData.group, leftModule.modelData.group === "Places" ? root.fileEntries() : root.appEntries(), arrow)
                        }
                        ConsoleButton {
                            id: launch
                            Layout.fillWidth: true; Layout.fillHeight: true
                            text: leftModule.modelData.label; iconName: leftModule.modelData.icon
                            selected: popup.visible && (popup.visualParent === arrow || popup.visualParent === launch)
                            onClicked: leftModule.modelData.command ? root.run(leftModule.modelData.command) : root.openSection("Applications", root.appEntries(), launch)
                        }
                    }
                }
                Bevel {
                    Layout.preferredWidth: 192; Layout.fillHeight: true
                    surface: "#174c55"; sunken: true
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 4; spacing: 3
                        Text {
                            Layout.fillWidth: true; text: "WORKSPACES"; color: "#c9dedb"
                            font.pixelSize: 9; horizontalAlignment: Text.AlignHCenter
                        }
                        GridLayout {
                            columns: 2; rowSpacing: 3; columnSpacing: 3
                            Layout.fillWidth: true; Layout.fillHeight: true
                            Repeater {
                                model: desktops.desktopIds
                                delegate: ConsoleButton {
                                    required property int index
                                    required property var modelData
                                    Layout.fillWidth: true; Layout.fillHeight: true
                                    implicitWidth: 70; implicitHeight: 23
                                    text: (index + 1) + "  " + (desktops.desktopNames[index] || "Workspace")
                                    selected: desktops.currentDesktop === modelData
                                    onClicked: root.run(root.dbus + " org.kde.KWin /KWin setCurrentDesktop " + (index + 1))
                                }
                            }
                        }
                    }
                }
                Repeater {
                    model: [
                        {label: "Web", icon: "internet-web-browser", command: "xdg-open https://www.kde.org", group: "Internet"},
                        {label: "Mail", icon: "internet-mail", command: "xdg-email", group: "Mail"},
                        {label: "System", icon: "preferences-system", command: "kstart systemsettings", group: "System"},
                        {label: "Trash", icon: "user-trash", command: "kstart dolphin trash:/", group: "Places"}
                    ]
                    delegate: ColumnLayout {
                        id: rightModule
                        required property var modelData
                        Layout.fillWidth: true; Layout.preferredWidth: 68; Layout.fillHeight: true; spacing: 1
                        ConsoleButton {
                            id: rightArrow
                            text: ""; Layout.fillWidth: true; Layout.preferredHeight: 13
                            Accessible.name: "Open " + rightModule.modelData.group
                            contentItem: Text { text: "▴"; color: "#c9dedb"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            onClicked: root.openSection(rightModule.modelData.group, rightModule.modelData.group === "Places" ? root.fileEntries() : root.systemEntries(), rightArrow)
                        }
                        ConsoleButton {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            text: rightModule.modelData.label; iconName: rightModule.modelData.icon
                            selected: popup.visible && popup.visualParent === rightArrow
                            onClicked: root.run(rightModule.modelData.command)
                        }
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 38; Layout.fillHeight: true; spacing: 3
                    ConsoleButton {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        iconName: "system-lock-screen"; text: ""; iconSize: 23
                        Accessible.name: "Lock Screen"
                        onClicked: root.run(root.dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock")
                    }
                    ConsoleButton {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        iconName: "computer"; text: ""; iconSize: 23
                        Accessible.name: "Show Desktop"
                        onClicked: root.run(root.dbus + " org.kde.KWin /KWin showDesktop \"$(if [ \"$(" + root.dbus + " org.kde.KWin /KWin org.kde.KWin.showingDesktop)\" = true ]; then echo false; else echo true; fi)\"")
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true; Layout.preferredHeight: 24; Layout.maximumHeight: 24; spacing: 3
                Text {
                    Layout.preferredWidth: 92; text: "CDE / COPPER"; color: "#d0ded9"
                    font.pixelSize: 9; font.family: "Noto Sans"; horizontalAlignment: Text.AlignHCenter
                }
                ListView {
                    id: taskList
                    Layout.fillWidth: true; Layout.fillHeight: true
                    orientation: ListView.Horizontal; spacing: 3; clip: true
                    model: tasks
                    delegate: ConsoleButton {
                        required property int index
                        required property var model
                        width: Math.min(220, Math.max(120, (taskList.width - (taskList.count-1)*3) / Math.max(1, taskList.count)))
                        height: 24; horizontal: true; iconSize: 18
                        text: model.display || "Window"
                        iconName: model.AppId && model.AppId.indexOf("konsole") >= 0 ? "utilities-terminal" : model.AppId && model.AppId.indexOf("dolphin") >= 0 ? "folder" : model.AppId && model.AppId.indexOf("kate") >= 0 ? "accessories-text-editor" : "application-x-executable"
                        selected: Boolean(model.IsActive)
                        onClicked: {
                            const idx = tasks.makeModelIndex(index);
                            if (model.IsActive) tasks.requestToggleMinimized(idx); else tasks.requestActivate(idx);
                        }
                    }
                }
                ConsoleButton {
                    id: status
                    Layout.preferredWidth: 104; Layout.fillHeight: true
                    text: root.volumeState; iconName: "audio-volume-high"; iconSize: 18; horizontal: true
                    Accessible.name: root.networkState + ", volume " + root.volumeState + ", session controls"
                    onClicked: root.openSection("Session", root.systemEntries(), status)
                }
            }
        }
    }

    PlasmaCore.Dialog {
        id: popup
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        onVisibleChanged: if (visible) popupBody.forceActiveFocus()
        mainItem: Bevel {
            id: popupBody
            width: 276; height: 41 + root.entries.length * 38
            surface: "#86a4aa"
            focus: true
            Keys.onEscapePressed: popup.visible = false
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 5; spacing: 2
                Bevel {
                    Layout.fillWidth: true; Layout.preferredHeight: 27; surface: "#e8874f"
                    Text { anchors.centerIn: parent; text: root.popupTitle; color: "#10262b"; font.pixelSize: 12; font.weight: Font.DemiBold }
                }
                Repeater {
                    model: root.entries
                    delegate: ConsoleButton {
                        required property var modelData
                        Layout.fillWidth: true; Layout.fillHeight: true
                        text: modelData.label; iconName: modelData.icon
                        horizontal: true; iconSize: 28; surface: "#86a4aa"; foreground: "#10262b"
                        onClicked: {
                            popup.visible = false;
                            if (modelData.command === "@applications") {
                                applications.visualParent = popup.visualParent;
                                applications.visible = true;
                            } else root.run(modelData.command);
                        }
                    }
                }
            }
        }
    }
    PlasmaCore.Dialog {
        id: applications
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        onVisibleChanged: if (visible) appSearch.forceActiveFocus()
        mainItem: Bevel {
            width: 340; height: 480; surface: "#86a4aa"
            Keys.onEscapePressed: applications.visible = false
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 5
                Bevel {
                    surface: "#e8874f"; Layout.fillWidth: true; Layout.preferredHeight: 29
                    Text { anchors.centerIn: parent; text: "Applications"; color: "#10262b"; font.pixelSize: 13 }
                }
                TextField {
                    id: appSearch
                    Layout.fillWidth: true; placeholderText: "Search"
                    color: "#10262b"; font.pixelSize: 13
                    background: Bevel { sunken: true; surface: "#c4d2d0" }
                    onAccepted: {
                        for (let i = 0; i < appList.count; i++) {
                            const item = appList.itemAtIndex(i);
                            if (item && item.visible) { allApps.trigger(i, "", null); applications.visible = false; break; }
                        }
                    }
                }
                ListView {
                    id: appList
                    Layout.fillWidth: true; Layout.fillHeight: true
                    clip: true; model: allApps; spacing: 2
                    ScrollBar.vertical: ScrollBar {}
                    delegate: ConsoleButton {
                        required property int index
                        required property var model
                        width: appList.width - 14
                        visible: appSearch.text.length === 0 || text.toLowerCase().indexOf(appSearch.text.toLowerCase()) >= 0
                        height: visible ? 37 : 0
                        text: model.display || "Application"
                        iconName: "application-x-executable"
                        horizontal: true; iconSize: 26; surface: "#86a4aa"; foreground: "#10262b"
                        onClicked: { allApps.trigger(index, "", null); applications.visible = false; }
                    }
                }
            }
        }
    }
}
