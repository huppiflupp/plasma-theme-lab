pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import org.kde.plasma.private.kicker as Kicker
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import "launch.js" as Launch
import "motif.js" as Motif

PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    property string popupTitle: ""
    property var entries: []
    property date now: new Date()
    property string activeSection: ""
    property string networkState: "Network"
    property string volumeState: "Audio"
    readonly property string dbus: "qdbus-qt6"
    readonly property var leftSlots: Launch.parse(Plasmoid.configuration.leftLaunchers, Launch.LEFT)
    readonly property var rightSlots: Launch.parse(Plasmoid.configuration.rightLaunchers, Launch.RIGHT)

    // Every colour comes from the active colour scheme: the console is the
    // Complementary set (CDE colour set 8 with a CDE palette), popups use
    // Window/View, the selection is the active-window colour.
    Item { id: complementary; Kirigami.Theme.colorSet: Kirigami.Theme.Complementary; Kirigami.Theme.inherit: false }
    Item { id: windowSet; Kirigami.Theme.colorSet: Kirigami.Theme.Window; Kirigami.Theme.inherit: false }
    Item { id: viewSet; Kirigami.Theme.colorSet: Kirigami.Theme.View; Kirigami.Theme.inherit: false }
    QtObject {
        id: consoleColors
        readonly property color panel: complementary.Kirigami.Theme.backgroundColor
        readonly property color panelText: complementary.Kirigami.Theme.textColor
        readonly property color window: windowSet.Kirigami.Theme.backgroundColor
        readonly property color windowText: windowSet.Kirigami.Theme.textColor
        readonly property color field: viewSet.Kirigami.Theme.backgroundColor
        readonly property color fieldText: viewSet.Kirigami.Theme.textColor
        readonly property color highlight: windowSet.Kirigami.Theme.highlightColor
        readonly property color highlightText: windowSet.Kirigami.Theme.highlightedTextColor
        readonly property string font: Kirigami.Theme.defaultFont.family
        readonly property date now: root.now
        // Console scale (settings): every size below is a multiple of it.
        readonly property real unit: Math.max(0.5, Math.min(3, Plasmoid.configuration.consoleScale || 1))
    }

    function run(command) {
        runner.connectSource(Launch.detached(command));
    }
    function launch(slot, anchor) {
        if (slot.command === "@applications") openApplications(anchor);
        else if (slot.command) run(Launch.resolve(slot.command));
    }
    function openSection(title, list, anchor) {
        if (popup.visible && activeSection === title) { popup.visible = false; return; }
        popupTitle = title; entries = list; activeSection = title;
        popup.visualParent = anchor;
        popup.visible = true;
    }
    function openMenu(slot, anchor) {
        switch (slot.menu) {
        case "applications": openApplications(anchor); break;
        case "places": openSection("Places", placesEntries(), anchor); break;
        case "system": openSection("System", systemEntries(), anchor); break;
        case "help": openSection("Help", helpEntries(), anchor); break;
        }
    }
    function openApplications(anchor) {
        popup.visible = false;
        if (appMenu.opened) appMenu.close();
        else appMenu.open(anchor || root.fullRepresentationItem);
    }
    function entry(label, icon, command) { return {label: label, icon: icon, command: command}; }
    function placesEntries() {
        return [entry("Home", "user-home", "@files ~"),
                entry("Documents", "folder-documents", "@files xdg:DOCUMENTS"),
                entry("Downloads", "folder-download", "@files xdg:DOWNLOAD"),
                entry("Pictures", "folder-pictures", "@files xdg:PICTURES"),
                entry("File System", "drive-harddisk", "@files /"),
                entry("Trash", "user-trash", "@trash")];
    }
    function systemEntries() {
        return [entry("System Settings", "preferences-system", "@settings"),
                entry("Arrange Windows", "view-split-left-right", "@arrange"),
                entry("Colours", "preferences-desktop-color", "@settings kcm_colors"),
                entry("Audio", "audio-volume-high", "@settings kcm_pulseaudio"),
                entry("Network", "network-workgroup", "@settings kcm_networkmanagement"),
                entry("Display", "computer", "@settings kcm_kscreen"),
                entry("Lock Screen", "system-lock-screen", dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock"),
                entry("Leave Session...", "system-log-out", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptAll")];
    }
    function helpEntries() {
        return [entry("Help Center", "help-browser", "@help"),
                entry("Keyboard Shortcuts", "preferences-desktop-keyboard", "@settings kcm_keys"),
                entry("System Information", "computer", "kinfocenter"),
                entry("About CDE Copper", "cde-menu", "xdg-open https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE")];
    }
    function configurePanel() {
        const modes = ["none", "autohide", "dodgewindows"];
        const mode = modes[Math.max(0, Math.min(2, Plasmoid.configuration.visibilityMode))];
        const edge = Plasmoid.configuration.topEdge ? "top" : "bottom";
        const height = Math.round(128 * consoleColors.unit);
        const script = "for (var p of panels()) { for (var w of p.widgets()) { if (w.type === 'org.cde.copper.frontpanel') { p.hiding = '" + mode + "'; p.location = '" + edge + "'; p.height = " + height + "; } } }";
        runner.connectSource(dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(script));
    }
    // "Arbeitsfläche 1", "Desktop 1": Plasma's default names only repeat
    // the number the button already shows.
    function workspaceLabel(index) {
        const name = (desktops.desktopNames[index] || "").trim();
        const n = String(index + 1);
        if (name === "" || name === n || new RegExp("^\\D*\\s" + n + "$").test(name)) return n;
        return n + "  " + name;
    }
    Connections {
        target: Plasmoid.configuration
        function onVisibilityModeChanged() { root.configurePanel(); }
        function onTopEdgeChanged() { root.configurePanel(); }
        function onConsoleScaleChanged() { root.configurePanel(); }
    }

    Component.onCompleted: if (Plasmoid.configuration.consoleScale !== 1) configurePanel()

    Kicker.AppsModel { id: allApps; flat: true; sorted: true; autoPopulate: true; appletInterface: Plasmoid }
    Kicker.AppsModel { id: categoryApps; flat: false; sorted: true; autoPopulate: true; showSeparators: false; appletInterface: Plasmoid }
    PlasmaCalendar.EventPluginsManager {
        id: eventPlugins
        Component.onCompleted: populateEnabledPluginsList(Plasmoid.configuration.enabledCalendarPlugins)
    }
    Connections {
        target: Plasmoid.configuration
        function onEnabledCalendarPluginsChanged() { eventPlugins.populateEnabledPluginsList(Plasmoid.configuration.enabledCalendarPlugins); }
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
    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: tasks
        virtualDesktop: desktops.currentDesktop
        activity: activities.currentActivity
        screenGeometry: Plasmoid.containment.screenGeometry
        filterByVirtualDesktop: true
        filterByActivity: true
        // With one console per screen, each lists the windows on its own screen.
        filterByScreen: Plasmoid.configuration.windowsOnThisScreen
        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    component Slot: ColumnLayout {
        id: slot
        required property var modelData
        Layout.fillWidth: true; Layout.preferredWidth: Math.round(68 * consoleColors.unit); Layout.fillHeight: true; spacing: 1
        ConsoleButton {
            id: arrow
            text: ""; Layout.fillWidth: true; Layout.preferredHeight: Math.round(13 * consoleColors.unit)
            enabled: slot.modelData.menu !== ""
            opacity: enabled ? 1 : 0.35
            Accessible.name: slot.modelData.menu ? "Open " + slot.modelData.menu : ""
            selected: popup.visible && popup.visualParent === arrow
            contentItem: Text {
                text: Plasmoid.configuration.topEdge ? "▾" : "▴"
                color: consoleColors.panelText; font.pixelSize: Math.round(12 * consoleColors.unit)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
            onClicked: root.openMenu(slot.modelData, arrow)
        }
        ConsoleButton {
            id: launcher
            Layout.fillWidth: true; Layout.fillHeight: true
            text: slot.modelData.label; iconName: slot.modelData.icon
            onClicked: root.launch(slot.modelData, launcher)
        }
    }

    fullRepresentation: Bevel {
        id: frontConsole
        implicitWidth: content.implicitWidth + 10
        implicitHeight: Math.round(116 * consoleColors.unit)
        // The panel sizes itself from these (lengthMode 'fit').
        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: implicitHeight
        Layout.preferredHeight: implicitHeight
        Layout.maximumHeight: implicitHeight
        surface: consoleColors.panel
        ColumnLayout {
            id: content
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 4
                ConsoleButton {
                    id: clock
                    Layout.preferredWidth: Math.round(92 * consoleColors.unit); Layout.fillHeight: true
                    surface: consoleColors.window
                    selected: calendar.visible
                    Accessible.name: Qt.formatDateTime(root.now, Qt.locale().dateTimeFormat(Locale.LongFormat))
                    onClicked: {
                        if (Plasmoid.configuration.clockOpensApp) root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar"));
                        else { calendar.visualParent = clock; calendar.visible = !calendar.visible; }
                    }
                    contentItem: Column {
                        spacing: 0
                        readonly property color ink: clock.selected ? consoleColors.highlightText : consoleColors.windowText
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "ddd").toUpperCase(); color: parent.ink; opacity: 0.8; font.pixelSize: Math.round(10 * consoleColors.unit); font.family: consoleColors.font }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "HH:mm"); color: parent.ink; font.pixelSize: Math.round(24 * consoleColors.unit); font.family: "IBM Plex Mono" }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDateTime(root.now, "dd MMM").toUpperCase(); color: parent.ink; font.pixelSize: Math.round(10 * consoleColors.unit); font.family: consoleColors.font }
                    }
                }
                Repeater { model: root.leftSlots; delegate: Slot {} }
                Bevel {
                    Layout.preferredWidth: Math.round(192 * consoleColors.unit); Layout.fillHeight: true
                    surface: Motif.shades(consoleColors.panel).bottom; sunken: true
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 4; spacing: 3
                        Text {
                            Layout.fillWidth: true; text: "WORKSPACES"; color: Motif.shades(consoleColors.panel).top
                            font.pixelSize: Math.round(9 * consoleColors.unit); font.family: consoleColors.font; horizontalAlignment: Text.AlignHCenter
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
                                    implicitWidth: Math.round(70 * consoleColors.unit); implicitHeight: Math.round(23 * consoleColors.unit)
                                    text: root.workspaceLabel(index)
                                    Accessible.name: "Workspace " + (index + 1) + " " + (desktops.desktopNames[index] || "")
                                    selected: desktops.currentDesktop === modelData
                                    onClicked: root.run(root.dbus + " org.kde.KWin /KWin setCurrentDesktop " + (index + 1))
                                }
                            }
                        }
                    }
                }
                Repeater { model: root.rightSlots; delegate: Slot {} }
                ColumnLayout {
                    Layout.preferredWidth: Math.round(38 * consoleColors.unit); Layout.fillHeight: true; spacing: 3
                    ConsoleButton {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        iconName: "system-lock-screen"; text: ""; iconSize: Math.round(23 * consoleColors.unit)
                        Accessible.name: "Lock Screen"
                        onClicked: root.run(root.dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock")
                    }
                    ConsoleButton {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        iconName: "computer"; text: ""; iconSize: Math.round(23 * consoleColors.unit)
                        Accessible.name: "Show Desktop"
                        onClicked: root.run(root.dbus + " org.kde.KWin /KWin showDesktop \"$(if [ \"$(" + root.dbus + " org.kde.KWin /KWin org.kde.KWin.showingDesktop)\" = true ]; then echo false; else echo true; fi)\"")
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true; Layout.preferredHeight: Math.round(24 * consoleColors.unit); Layout.maximumHeight: Math.round(24 * consoleColors.unit); spacing: 3
                Text {
                    Layout.preferredWidth: Math.round(92 * consoleColors.unit); text: Plasmoid.configuration.consoleLabel; color: consoleColors.panelText
                    font.pixelSize: Math.round(9 * consoleColors.unit); font.family: consoleColors.font; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                }
                ListView {
                    id: taskList
                    Layout.fillWidth: true; Layout.fillHeight: true
                    orientation: ListView.Horizontal; spacing: 3; clip: true
                    model: tasks
                    delegate: ConsoleButton {
                        required property int index
                        required property var model
                        width: Math.min(220 * consoleColors.unit, Math.max(120 * consoleColors.unit, (taskList.width - (taskList.count-1)*3) / Math.max(1, taskList.count)))
                        height: taskList.height; horizontal: true; iconSize: Math.round(18 * consoleColors.unit)
                        text: model.display || "Window"
                        iconName: ""
                        Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: Math.round(18 * consoleColors.unit); height: width; source: parent.model.decoration; active: false }
                        leftPadding: Math.round(30 * consoleColors.unit)
                        selected: Boolean(model.IsActive)
                        onClicked: {
                            const idx = tasks.makeModelIndex(index);
                            if (model.IsActive) tasks.requestToggleMinimized(idx); else tasks.requestActivate(idx);
                        }
                    }
                }
                ConsoleButton {
                    id: status
                    Layout.preferredWidth: Math.round(104 * consoleColors.unit); Layout.fillHeight: true
                    text: root.volumeState; iconName: "audio-volume-high"; iconSize: Math.round(18 * consoleColors.unit); horizontal: true
                    Accessible.name: root.networkState + ", volume " + root.volumeState + ", session controls"
                    onClicked: root.openSection("Session", root.systemEntries(), status)
                }
            }
        }
    }

    AppMenu {
        id: appMenu
        appsModel: categoryApps
        onFindRequested: { applications.visualParent = root.fullRepresentationItem; applications.visible = true; }
        onRunRequested: root.run(root.dbus + " org.kde.krunner /App org.kde.krunner.App.display")
    }

    PlasmaCore.Dialog {
        id: calendar
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        mainItem: CalendarPanel {
            pluginsManager: eventPlugins
            onCloseRequested: calendar.visible = false
            onOpenCalendar: { calendar.visible = false; root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar")); }
        }
        onVisibleChanged: if (visible) mainItem.forceActiveFocus()
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
            surface: consoleColors.window
            focus: true
            Keys.onEscapePressed: popup.visible = false
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 5; spacing: 2
                Bevel {
                    Layout.fillWidth: true; Layout.preferredHeight: 27; surface: consoleColors.highlight
                    Text { anchors.centerIn: parent; text: root.popupTitle; color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
                }
                Repeater {
                    model: root.entries
                    delegate: ConsoleButton {
                        required property var modelData
                        Layout.fillWidth: true; Layout.fillHeight: true
                        text: modelData.label; iconName: modelData.icon
                        horizontal: true; iconSize: 28; surface: consoleColors.window; foreground: consoleColors.windowText
                        onClicked: {
                            popup.visible = false;
                            root.run(Launch.resolve(modelData.command));
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
        onVisibleChanged: if (visible) { appSearch.text = ""; appSearch.forceActiveFocus(); }
        mainItem: Bevel {
            width: 340; height: 480; surface: consoleColors.window
            Keys.onEscapePressed: applications.visible = false
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 5
                Bevel {
                    surface: consoleColors.highlight; Layout.fillWidth: true; Layout.preferredHeight: 29
                    Text { anchors.centerIn: parent; text: "Find Application"; color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 13 }
                }
                TextField {
                    id: appSearch
                    Layout.fillWidth: true; placeholderText: "Search"
                    color: consoleColors.fieldText; font.pixelSize: 13
                    background: Bevel { sunken: true; surface: consoleColors.field }
                    Keys.onEscapePressed: applications.visible = false
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
                        iconName: ""
                        Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: 26; height: 26; source: parent.model.decoration; active: false }
                        leftPadding: 40
                        horizontal: true; surface: consoleColors.window; foreground: consoleColors.windowText
                        onClicked: { allApps.trigger(index, "", null); applications.visible = false; }
                    }
                }
            }
        }
    }
}
