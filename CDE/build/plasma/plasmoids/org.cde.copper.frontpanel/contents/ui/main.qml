pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
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
    // The Meta key: Plasma activates the panel applet that provides
    // org.kde.plasma.launchermenu (metadata.json) on the active screen.
    activationTogglesExpanded: false
    property Item appsTile: null
    // Subpanels stay open while the pointer is on them or on the segment
    // that opened them (DESIGN-SPEC §8); opened or used from the keyboard,
    // they stay until Escape or a second click.
    property Item hoveredSegment: null
    property Item popupSegment: null
    function hoverSegment(segment, hovered) {
        if (hovered) hoveredSegment = segment;
        else if (hoveredSegment === segment) hoveredSegment = null;
    }
    component Keeper: Timer {
        property var dialog
        property Item segment
        property bool inside: false
        property bool keyboard: false
        readonly property bool keep: inside || keyboard || (segment !== null && root.hoveredSegment === segment)
        interval: 450
        running: dialog && dialog.visible && !keep
        onTriggered: if (dialog) dialog.visible = false
        // The pointer on the segment when it opens: a click, not a key.
        function opened() { keyboard = !(segment !== null && root.hoveredSegment === segment); }
    }
    Connections {
        target: Plasmoid
        function onActivated() { root.openApplications(root.appsTile || root.fullRepresentationItem); }
    }
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    property string popupTitle: ""
    property var entries: []
    property date now: new Date()
    property string activeSection: ""
    property string networkState: i18nd("cde-copper", "Network")
    property string volumeState: i18nd("cde-copper", "Audio")
    property int volume: 0
    property bool muted: false
    readonly property string dbus: "$(command -v qdbus6 || command -v qdbus-qt6 || command -v qdbus)"
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
        else if (slot.command) run(Launch.resolve(slot.command, [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)));
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
        case "places": openSection(i18nd("cde-copper", "Places"), placesEntries(slot), anchor); break;
        case "system": openSection(i18nd("cde-copper", "System"), systemEntries(), anchor); break;
        case "help": openSection(i18nd("cde-copper", "Help"), helpEntries(), anchor); break;
        case "mail": openSection(i18nd("cde-copper", "Mail"), mailEntries(slot), anchor); break;
        case "bookmarks": openListing("bookmarks", i18nd("cde-copper", "Bookmarks"), slot, anchor); break;
        case "recent": openListing("recent", i18nd("cde-copper", "Recent Files"), slot, anchor); break;
        }
    }
    // Bookmarks and recent files come from contents/code/menus.py, which
    // knows where browsers and editors keep them.
    property var pendingListing: null
    readonly property string helper: decodeURIComponent(Qt.resolvedUrl("../code/menus.py").toString().replace(/^file:\/\//, ""))
    function openListing(kind, title, slot, anchor) {
        if (popup.visible && activeSection === title + slot.command) { popup.visible = false; return; }
        pendingListing = {title: title, slot: slot, anchor: anchor, kind: kind};
        listings.connectSource("python3 " + Launch.quote(helper) + " " + kind + " " + Launch.quote(slot.command));
    }
    function showListing(stdout) {
        const request = pendingListing;
        pendingListing = null;
        if (!request) return;
        let result = {app: "", items: []};
        try { result = JSON.parse(stdout); } catch (e) { console.warn("CDE listing:", e, stdout); }
        const list = result.items.map(item => ({label: item.label, icon: item.icon, command: request.slot.command,
                                                args: item.args, tip: item.tip}));
        if (list.length === 0)
            list.push({label: request.kind === "bookmarks" ? i18nd("cde-copper", "No bookmarks found") : i18nd("cde-copper", "No recent files"), icon: "dialog-information", command: ""});
        openSection(request.title + (result.app ? " – " + result.app : ""), list, request.anchor);
        activeSection = request.title + request.slot.command;
    }
    P5Support.DataSource {
        id: listings
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            root.showListing(data.stdout);
        }
    }

    function openApplications(anchor) {
        popup.visible = false;
        if (appMenu.opened) appMenu.close();
        else appMenu.open(anchor || root.fullRepresentationItem);
    }
    function entry(label, icon, command) { return {label: label, icon: icon, command: command}; }
    // The places open in the slot's file manager (XFile, if that is the
    // tile's); XFile has no trash, so the trash stays the desktop's.
    function placesEntries(slot) {
        const files = slot && slot.command.indexOf("@xfile") === 0 ? "@xfile"
                    : slot && slot.command.indexOf("@pcmanfm") === 0 ? "@pcmanfm" : "@files";
        return [entry(i18nd("cde-copper", "Home"), "user-home", files + " ~"),
                entry(i18nd("cde-copper", "Documents"), "folder-documents", files + " xdg:DOCUMENTS"),
                entry(i18nd("cde-copper", "Downloads"), "folder-download", files + " xdg:DOWNLOAD"),
                entry(i18nd("cde-copper", "Pictures"), "folder-pictures", files + " xdg:PICTURES"),
                entry(i18nd("cde-copper", "File System"), "drive-harddisk", files + " /"),
                entry(i18nd("cde-copper", "Trash"), "user-trash", "@trash")];
    }
    function systemEntries() {
        return [entry(i18nd("cde-copper", "System Settings"), "preferences-system", "@settings"),
                entry(i18nd("cde-copper", "Style Manager…"), "preferences-desktop-color", "@style"),
                entry(i18nd("cde-copper", "Arrange Windows"), "view-split-left-right", "@arrange"),
                entry(i18nd("cde-copper", "Audio"), "audio-volume-high", "@settings kcm_pulseaudio"),
                entry(i18nd("cde-copper", "Network"), "network-workgroup", "@settings kcm_networkmanagement"),
                entry(i18nd("cde-copper", "Display"), "computer", "@settings kcm_kscreen"),
                entry(i18nd("cde-copper", "Lock Screen"), "system-lock-screen", dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock"),
                entry(i18nd("cde-copper", "Leave Session..."), "system-log-out", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptAll")];
    }
    // The mail client's own command with a bare mailto: opens a new message
    // in Thunderbird, KMail and Evolution alike.
    function mailEntries(slot) {
        const mail = slot.command || "@mail";
        return [entry(i18nd("cde-copper", "New Message"), "mail-message-new", mail + " mailto:"),
                entry(i18nd("cde-copper", "Open Mail"), "internet-mail", mail),
                entry(i18nd("cde-copper", "Appointments"), "view-calendar", "@calendar"),
                entry(i18nd("cde-copper", "Address Book"), "x-office-address-book", "@contacts")];
    }
    function helpEntries() {
        return [entry(i18nd("cde-copper", "Help Center"), "help-browser", "@help"),
                entry(i18nd("cde-copper", "Keyboard Shortcuts"), "preferences-desktop-keyboard", "@settings kcm_keys"),
                entry(i18nd("cde-copper", "System Information"), "computer", "kinfocenter"),
                entry(i18nd("cde-copper", "About CDE Copper"), "cde-menu", "xdg-open https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE")];
    }
    function configurePanel() {
        const modes = ["none", "autohide", "dodgewindows"];
        const mode = modes[Math.max(0, Math.min(2, Plasmoid.configuration.visibilityMode))];
        const edges = ["bottom", "top", "left", "right"];
        const chosen = Plasmoid.configuration.edge;
        const edge = chosen >= 0 && chosen < 4 ? edges[chosen] : (Plasmoid.configuration.topEdge ? "top" : "bottom");
        const height = Math.round(128 * consoleColors.unit);
        // Upright the console runs the full height, so the window list has room.
        const length = edge === "left" || edge === "right" ? "fill" : "fit";
        // Plasma reserves the screen edge that reveals a hidden panel when the
        // hiding mode is set, and does not move it with the panel: moved
        // afterwards (or in the same breath), the console could not be brought
        // back. So: place it while it stays visible, then hide it.
        const ours = "for (var p of panels()) { for (var w of p.widgets()) { if (w.type === 'org.cde.copper.frontpanel') { ";
        const place = ours + "p.hiding = 'none'; p.location = '" + edge + "'; p.height = " + height + "; p.lengthMode = '" + length + "'; p.alignment = 'center'; p.offset = 0; } } }";
        runner.connectSource(dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(place));
        pendingHiding = mode === "none" ? "" : ours + "p.hiding = '" + mode + "'; } } }";
        if (pendingHiding) hidingTimer.restart();
    }
    // The palette tool in the profile (installed with the theme).
    readonly property string tool: decodeURIComponent(StandardPaths.writableLocation(StandardPaths.GenericDataLocation).toString().replace(/^file:\/\//, "")) + "/cde-copper/tool/manage.py"
    // A colour scheme chosen in System Settings changes these colours; if it
    // is a CDE palette, the tool brings Kvantum, the Plasma surfaces and the
    // backdrop along. Unchanged palettes cost nothing: the tool compares.
    readonly property string schemeKey: consoleColors.panel + consoleColors.window + consoleColors.highlight + consoleColors.field
    onSchemeKeyChanged: { schemeTimer.restart(); workspaceReads = 0; workspaceTimer.restart(); }
    // The palette's workspace colours, written by the tool with each palette
    // (cde-copper/workspaces.json); read at start and after a scheme change.
    property var workspaceColours: []
    readonly property string workspaceFile: decodeURIComponent(StandardPaths.writableLocation(StandardPaths.GenericDataLocation).toString().replace(/^file:\/\//, "")) + "/cde-copper/workspaces.json"
    // Read three times, 3 s apart: the tool may still be writing the file
    // when the colours change. A scheme that is not CDE's has none.
    property int workspaceReads: 0
    Timer {
        id: workspaceTimer
        interval: 3000; running: true; repeat: true
        onTriggered: {
            workspaceReader.connectSource("case \"$(kreadconfig6 --group General --key ColorScheme)\" in CDE*) cat " + Launch.quote(root.workspaceFile)
                                          + " ;; *) echo '[]' ;; esac");
            if (++root.workspaceReads >= 3) stop();
        }
    }
    P5Support.DataSource {
        id: workspaceReader
        engine: "executable"
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            try { root.workspaceColours = JSON.parse(data.stdout); } catch (e) { root.workspaceColours = []; }
        }
    }
    Timer {
        id: schemeTimer
        interval: 2000
        onTriggered: root.run("python3 " + Launch.quote(root.tool) + " palette --follow-scheme --notify")
    }

    property string pendingHiding: ""
    Timer {
        id: hidingTimer
        interval: 1500
        onTriggered: if (root.pendingHiding) runner.connectSource(root.dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(root.pendingHiding))
    }

    // The tray beside the console would show a second volume control; the
    // console's own one (wheel, click for slider and mute) replaces it.
    function syncTray() {
        const hide = Plasmoid.configuration.hideTrayVolume;
        // With hideTrayIcons every entry the tray knows goes to its hidden
        // list: the tray beside the console shrinks to its arrow (and what
        // asks for attention), the entries open from the console's button.
        const icons = Plasmoid.configuration.hideTrayIcons;
        // Applications' status icons are not in the tray's list; their ids
        // come from the helper (statusIds, refreshed by trayIds below).
        // The entries the console hid itself are recorded in its own
        // settings (trayHiddenByConsole); switching the option off takes out
        // only those, so what the user hid in the tray stays hidden.
        const script = "function list(w, key) { var v = w.readConfig(key, []); return typeof v === 'string' ? (v ? v.split(',') : []) : v; }"
            + " for (var p of panels()) { var ours = p.widgets().filter(function (w) { return w.type === 'org.cde.copper.frontpanel'; })[0]; if (!ours) continue;"
            + " ours.currentConfigGroup = ['General']; var mine = list(ours, 'trayHiddenByConsole');"
            + " for (var w of p.widgets()) { if (w.type !== 'org.kde.plasma.systemtray') continue; w.currentConfigGroup = ['General'];"
            + " var items = w.readConfig('extraItems', []); if (typeof items === 'string') items = items ? items.split(',') : [];"
            + " var has = items.indexOf('org.kde.plasma.volume') >= 0;"
            + (hide ? " if (has) w.writeConfig('extraItems', items.filter(function (i) { return i !== 'org.kde.plasma.volume'; }));"
                    : " if (!has && items.length) { items.push('org.kde.plasma.volume'); w.writeConfig('extraItems', items); }")
            + " var now = list(w, 'hiddenItems');"
            + (icons ? " var add = list(w, 'knownItems').concat(" + JSON.stringify(root.statusIds) + ").filter(function (i, k, all) { return now.indexOf(i) < 0 && all.indexOf(i) === k; });"
                       + " if (add.length) { w.writeConfig('hiddenItems', now.concat(add)); ours.writeConfig('trayHiddenByConsole', mine.concat(add)); }"
                     : " if (mine.length) { w.writeConfig('hiddenItems', now.filter(function (i) { return mine.indexOf(i) < 0; })); ours.writeConfig('trayHiddenByConsole', []); }")
            + " } }";
        runner.connectSource(dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(script));
    }
    function setVolume(percent) {
        const value = Math.max(0, Math.min(150, Math.round(percent)));
        root.volume = value;
        runner.connectSource("wpctl set-volume @DEFAULT_AUDIO_SINK@ " + value + "%");
    }

    // "Arbeitsfläche 1", "Desktop 1": Plasma's default names only repeat
    // the number the button already shows.
    function workspaceLabel(index) {
        const name = (desktops.desktopNames[index] || "").trim();
        const n = String(index + 1);
        // Upright the buttons are narrow: the number only, the name in the tooltip.
        if (root.vertical || name === "" || name === n || new RegExp("^\\D*\\s" + n + "$").test(name)) return n;
        return n + "  " + name;
    }
    Connections {
        target: Plasmoid.configuration
        function onVisibilityModeChanged() { root.configurePanel(); }
        function onTopEdgeChanged() { root.configurePanel(); }
        function onEdgeChanged() { root.configurePanel(); }
        function onConsoleScaleChanged() { root.configurePanel(); }
        function onHideTrayVolumeChanged() { root.syncTray(); }
        function onHideTrayIconsChanged() { root.syncTray(); root.placeTray(); }
        function onPanelFrameChanged() { root.placePanelFrame(); }
        // The Style page's choice, taken by the settings dialog's Apply/OK.
        function onStyleRequestChanged() {
            let request = null;
            try { request = JSON.parse(Plasmoid.configuration.styleRequest); } catch (e) { return; }
            if (!request || !request.palette) return;
            let command = "python3 " + Launch.quote(root.tool) + " palette --notify --palette " + Launch.quote(request.palette);
            if (request.backdrop) command += " --backdrop " + Launch.quote(request.backdrop) + " --backdrop-scale " + Math.max(1, Math.min(3, request.scale || 1));
            if (["outlined", "floating", "slim"].indexOf(request.progress) >= 0) command += " --progress " + request.progress;
            if (/^(copper|palette|white|#[0-9a-fA-F]{6})$/.test(request.cursor || "")) command += " --cursor " + Launch.quote(request.cursor);
            if (request.lockscreen === "cde" || request.lockscreen === "plasma") command += " --lockscreen " + request.lockscreen;
            if (typeof request.windowShadow === "boolean") command += " --window-shadow " + (request.windowShadow ? "on" : "off");
            root.run(command);
        }
    }

    Component.onCompleted: {
        if (Plasmoid.configuration.consoleScale !== 1) configurePanel();
        // The tray fills its item list on its first start; look once it has.
        trayTimer.start();
    }
    // Plasma's tray has no setting to drop its arrow. With its entries
    // behind the console's button, its container in the panel's layout is
    // hidden instead; the tray keeps running for notifications and its popup.
    // What placeTray() changed, to put back when the option is switched off.
    property var trayLayoutSpacing: null
    property var hiddenTray: null
    function placeTray() {
        const layout = root.parent ? root.parent.parent : null;
        if (!layout || !layout.children) return;
        const hide = Plasmoid.configuration.hideTrayIcons;
        for (const item of layout.children) {
            const applet = item.applet ? item.applet.plasmoid : null;
            if (!applet || applet.pluginName !== "org.kde.plasma.systemtray") continue;
            if (hide) { item.visible = false; root.hiddenTray = item; }
            else if (root.hiddenTray === item) { item.visible = true; root.hiddenTray = null; }
        }
        // The panel's layout keeps its spacing after the console, before an
        // invisible end spacer: four pixels more panel on one side.
        if (hide && root.trayLayoutSpacing === null) {
            root.trayLayoutSpacing = [layout.columnSpacing, layout.rowSpacing];
            layout.columnSpacing = 0; layout.rowSpacing = 0;
        } else if (!hide && root.trayLayoutSpacing !== null) {
            layout.columnSpacing = root.trayLayoutSpacing[0]; layout.rowSpacing = root.trayLayoutSpacing[1];
            root.trayLayoutSpacing = null;
        }
    }
    // The panel's own background (the theme's panel-background frame) behind
    // the console. Without it the console stands on the desktop by itself;
    // the panel keeps its size, so the margin around stays, transparent.
    // Hidden by scale, not opacity: Plasma binds the frames' opacity to its
    // adaptive panel opacity, and an assignment would break that binding.
    function placePanelFrame() {
        let item = root.parent;
        while (item && item.parent) item = item.parent;     // the panel window's root
        const show = Plasmoid.configuration.panelFrame;
        function walk(node, depth) {
            if (!node || depth > 3 || !node.children) return;
            for (const child of node.children) {
                if (child.imagePath !== undefined && String(child.imagePath).indexOf("panel-background") >= 0) child.scale = show ? 1 : 0;
                else walk(child, depth + 1);
            }
        }
        walk(item, 0);
    }
    Timer { id: trayTimer; interval: 4000; onTriggered: { root.placeTray(); root.placePanelFrame(); trayIds.connectSource("python3 " + Launch.quote(root.helper) + " tray"); } }
    // Applications add status icons while the session runs: look again
    // every half minute while the tray's entries are kept behind the button.
    property var statusIds: []
    Timer {
        interval: 30000; repeat: true
        running: Plasmoid.configuration.hideTrayIcons
        onTriggered: trayIds.connectSource("python3 " + Launch.quote(root.helper) + " tray")
    }
    P5Support.DataSource {
        id: trayIds
        engine: "executable"
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            let ids = [];
            try { ids = JSON.parse(data.stdout); } catch (e) {}
            if (!root.traySynced || JSON.stringify(ids) !== JSON.stringify(root.statusIds)) {
                root.statusIds = ids; root.traySynced = true; root.syncTray();
            }
        }
    }
    property bool traySynced: false

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
        connectedSources: ["timeout 3s env LC_ALL=C nmcli -t -f STATE general", "timeout 3s wpctl get-volume @DEFAULT_AUDIO_SINK@"]
        onNewData: function(sourceName, data) {
            if (sourceName.indexOf("nmcli") >= 0) root.networkState = data.stdout.trim() === "connected" ? i18nd("cde-copper", "Connected") : i18nd("cde-copper", "Offline");
            else {
                const match = data.stdout.match(/Volume: ([0-9.]+)/);
                root.muted = data.stdout.indexOf("MUTED") >= 0;
                if (match) root.volume = Math.round(Number(match[1]) * 100);
                root.volumeState = root.muted ? i18nd("cde-copper", "Muted") : match ? root.volume + "%" : i18nd("cde-copper", "Audio");
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
        groupMode: Plasmoid.configuration.groupWindows ? TaskManager.TasksModel.GroupApplications : TaskManager.TasksModel.GroupDisabled
        groupInline: false
        // Group from the second window on, not only when the strip is full.
        groupingWindowTasksThreshold: -1
        sortMode: TaskManager.TasksModel.SortVirtualDesktop
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    // Upright at the left or right screen edge, across at the top or bottom.
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property bool atRight: Plasmoid.location === PlasmaCore.Types.RightEdge
    // The subpanel arrows point to where the subpanels open.
    readonly property string arrowGlyph: {
        switch (Plasmoid.location) {
        case PlasmaCore.Types.TopEdge: return "▾";
        case PlasmaCore.Types.LeftEdge: return "▸";
        case PlasmaCore.Types.RightEdge: return "◂";
        default: return "▴";
        }
    }
    function u(pixels) { return Math.round(pixels * consoleColors.unit); }

    // A launcher tile with its subpanel arrow: arrow above the tile across,
    // beside it (towards the screen) upright.
    component Slot: GridLayout {
        id: slot
        required property var modelData
        rows: root.vertical ? 1 : 2
        columns: root.vertical ? 2 : 1
        rowSpacing: 1; columnSpacing: 1
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.preferredWidth: root.vertical ? -1 : root.u(68)
        Layout.preferredHeight: root.vertical ? root.u(62) : -1
        ConsoleButton {
            id: arrow
            Layout.row: 0
            Layout.column: root.vertical && !root.atRight ? 1 : 0
            Layout.fillWidth: !root.vertical; Layout.fillHeight: root.vertical
            Layout.preferredHeight: root.vertical ? -1 : root.u(13)
            Layout.preferredWidth: root.vertical ? root.u(13) : -1
            text: ""
            enabled: slot.modelData.menu !== ""
            opacity: enabled ? 1 : 0.35
            Accessible.name: slot.modelData.menu ? i18nd("cde-copper", "Open %1", i18nd("cde-copper", (Launch.MENUS.find(m => m.value === slot.modelData.menu) || {text: slot.modelData.menu}).text)) : ""
            selected: popup.visible && popup.visualParent === arrow
            contentItem: Text {
                text: root.arrowGlyph
                color: consoleColors.panelText; font.pixelSize: root.u(12)
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
            onClicked: { root.popupSegment = slot; root.openMenu(slot.modelData, arrow); }
        }
        ConsoleButton {
            id: launcher
            Layout.row: root.vertical ? 0 : 1
            Layout.column: root.vertical && !root.atRight ? 0 : (root.vertical ? 1 : 0)
            Layout.fillWidth: true; Layout.fillHeight: true
            text: Launch.slotLabel(slot.modelData, text => i18nd("cde-copper", text)); iconName: slot.modelData.icon
            onClicked: root.launch(slot.modelData, launcher)
            // The Applications tile, where the Meta key opens the menu.
            Component.onCompleted: if (slot.modelData.command === "@applications") root.appsTile = launcher
        }
        HoverHandler { onHoveredChanged: root.hoverSegment(slot, hovered) }
    }

    component ClockTile: ConsoleButton {
        id: clock
        Layout.fillWidth: root.vertical; Layout.fillHeight: !root.vertical
        Layout.preferredWidth: root.vertical ? -1 : root.u(92)
        Layout.preferredHeight: root.vertical ? root.u(72) : -1
        surface: consoleColors.window
        selected: calendar.visible
        Accessible.name: Qt.formatDateTime(root.now, Qt.locale().dateTimeFormat(Locale.LongFormat))
        onClicked: {
            if (Plasmoid.configuration.clockOpensApp) root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)));
            else { calendar.visualParent = clock; calendar.visible = !calendar.visible; }
        }
        HoverHandler { onHoveredChanged: root.hoverSegment(clock, hovered) }
        contentItem: ClockFace {
            style: Plasmoid.configuration.clockStyle
            dial: Plasmoid.configuration.clockDial
            seconds: Plasmoid.configuration.clockSeconds
            segmentShadow: Plasmoid.configuration.clockSegmentShadow
            segmentEdge: Plasmoid.configuration.clockSegmentEdge
            now: root.now
            ink: clock.selected ? consoleColors.highlightText : consoleColors.windowText
            // Lit segments and the second hand: the selection (copper) colour,
            // swapped while the tile itself is highlighted.
            accent: clock.selected ? consoleColors.highlightText : consoleColors.highlight
            dialColor: consoleColors.field
            tile: clock.selected ? consoleColors.highlight : consoleColors.window
            font: consoleColors.font
        }
    }

    component Workspaces: Bevel {
        Layout.fillWidth: root.vertical; Layout.fillHeight: !root.vertical
        Layout.preferredWidth: root.vertical ? -1 : root.u(192)
        Layout.preferredHeight: root.vertical ? root.u(72) : -1
        surface: Motif.shades(consoleColors.panel).bottom; sunken: true
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 4; spacing: 3
            Text {
                Layout.fillWidth: true; text: i18nd("cde-copper", "WORKSPACES"); color: Motif.shades(consoleColors.panel).top
                font.pixelSize: root.u(9); font.family: consoleColors.font; horizontalAlignment: Text.AlignHCenter
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
                        implicitWidth: root.u(root.vertical ? 40 : 70); implicitHeight: root.u(23)
                        text: root.workspaceLabel(index)
                        Accessible.name: i18nd("cde-copper", "Workspace %1 %2", index + 1, desktops.desktopNames[index] || "")
                        selected: desktops.currentDesktop === modelData
                        // As in CDE, each workspace in a colour of its own.
                        readonly property var own: Plasmoid.configuration.workspaceColours && root.workspaceColours.length
                                                   ? root.workspaceColours[index % root.workspaceColours.length] : null
                        surface: own ? own.bg : consoleColors.panel
                        foreground: own ? own.fg : consoleColors.panelText
                        accent: own ? own.sel : consoleColors.highlight
                        accentText: own ? own.fg : consoleColors.highlightText
                        onClicked: root.run(root.dbus + " org.kde.KWin /KWin setCurrentDesktop " + (index + 1))
                    }
                }
            }
        }
    }

    // Four small buttons in the space of one launcher with its arrow: the
    // tray's hidden icons, the console's settings, lock and show desktop.
    component SessionButtons: GridLayout {
        rows: 2; columns: 2
        rowSpacing: 1; columnSpacing: 1
        Layout.fillWidth: root.vertical; Layout.fillHeight: !root.vertical
        Layout.preferredWidth: root.vertical ? -1 : root.u(68)
        Layout.preferredHeight: root.vertical ? root.u(62) : -1
        SmallButton {
            iconName: "arrow-up"; Accessible.name: i18nd("cde-copper", "Hidden Icons")
            onClicked: root.showHiddenIcons()
        }
        SmallButton {
            iconName: "configure"; Accessible.name: i18nd("cde-copper", "Configure Front Console")
            onClicked: Plasmoid.internalAction("configure").trigger()
        }
        SmallButton {
            iconName: "system-lock-screen"; Accessible.name: i18nd("cde-copper", "Lock Screen")
            onClicked: root.run(root.dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock")
        }
        SmallButton {
            iconName: "user-desktop"; Accessible.name: i18nd("cde-copper", "Show Desktop")
            // KWin's D-Bus showDesktop(bool) is accepted but does nothing in
            // Plasma 6.7; its own "Show Desktop" shortcut toggles reliably.
            onClicked: root.run(root.dbus + " org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut 'Show Desktop'")
        }
    }
    // A quarter launcher: the icon follows the button, whole pixels.
    component SmallButton: ConsoleButton {
        id: small
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.preferredWidth: 1; Layout.preferredHeight: 1
        implicitWidth: 0; implicitHeight: 0
        padding: 0; text: ""
        contentItem: Item {
            Kirigami.Icon {
                readonly property int side: Math.max(8, Math.floor(Math.min(small.width, small.height) * 0.6))
                width: side; height: side
                x: Math.round((parent.width - side) / 2); y: Math.round((parent.height - side) / 2)
                source: small.iconName
                active: false
                // Not snapped down to 16/22/32: the icon grows with the console.
                roundToIconSize: false
            }
        }
    }
    // Opens the system tray's popup (hidden icons) the way a click on it does.
    function showHiddenIcons() {
        for (const applet of Plasmoid.containment.applets) {
            if (applet && applet.pluginName === "org.kde.plasma.systemtray") { applet.activated(); return; }
        }
    }

    component TaskStrip: ListView {
        id: taskList
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.minimumHeight: root.vertical ? root.u(80) : 0
        orientation: root.vertical ? ListView.Vertical : ListView.Horizontal
        spacing: 3; clip: true
        model: tasks
        delegate: ConsoleButton {
            required property int index
            required property var model
            width: root.vertical ? taskList.width
                 : Math.min(root.u(220), Math.max(root.u(120), (taskList.width - (taskList.count - 1) * 3) / Math.max(1, taskList.count)))
            height: root.vertical ? root.u(24) : taskList.height
            horizontal: true; iconSize: root.u(18)
            readonly property int windows: model.IsGroupParent ? model.ChildCount : 1
            text: windows > 1 ? i18nd("cde-copper", "%1× %2", windows, model.AppName || model.display) : (model.display || i18nd("cde-copper", "Window"))
            Accessible.name: windows > 1 ? root.groupTitles(index).join("\n") : text
            iconName: ""
            Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: root.u(18); height: width; source: parent.model.decoration; active: false }
            leftPadding: root.u(30)
            selected: Boolean(model.IsActive)
            onClicked: {
                if (windows > 1) { root.cycleGroup(index, windows); return; }
                const idx = tasks.makeModelIndex(index);
                if (model.IsActive) tasks.requestToggleMinimized(idx); else tasks.requestActivate(idx);
            }
        }
    }

    // A group's button brings its windows forward in turn: the one after
    // the active one, or the first.
    function cycleGroup(row, count) {
        let active = -1;
        for (let i = 0; i < count; i++)
            if (tasks.data(tasks.makeModelIndex(row, i), TaskManager.AbstractTasksModel.IsActive)) active = i;
        tasks.requestActivate(tasks.makeModelIndex(row, (active + 1) % count));
    }
    function groupTitles(row) {
        const titles = [];
        const count = tasks.data(tasks.makeModelIndex(row), TaskManager.AbstractTasksModel.ChildCount) || 0;
        for (let i = 0; i < count; i++) titles.push(tasks.data(tasks.makeModelIndex(row, i), Qt.DisplayRole));
        return titles;
    }

    component VolumeButton: ConsoleButton {
        id: status
        Layout.fillWidth: root.vertical; Layout.fillHeight: !root.vertical
        // As wide as a launcher, so it lines up with the tiles above it.
        Layout.preferredWidth: root.vertical ? -1 : root.u(68)
        Layout.preferredHeight: root.vertical ? root.u(26) : -1
        text: root.volumeState; iconSize: root.u(18); horizontal: true
        iconName: root.muted ? "audio-volume-muted" : "audio-volume-high"
        Accessible.name: i18nd("cde-copper", "Volume %1, %2", root.volumeState, root.networkState)
        onClicked: { volumePopup.visualParent = status; volumePopup.visible = !volumePopup.visible; }
        HoverHandler { onHoveredChanged: root.hoverSegment(status, hovered) }
        WheelHandler {
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: event => root.setVolume(root.volume + (event.angleDelta.y > 0 ? 5 : -5))
        }
    }

    fullRepresentation: Bevel {
        id: frontConsole
        // Across: as wide as its tiles, 116 high. Upright: 116 wide, and as
        // tall as the screen allows, the window list taking the rest.
        implicitWidth: root.vertical ? root.u(116) : content.implicitWidth + 10
        implicitHeight: root.vertical ? content.implicitHeight + 10 : root.u(116)
        // The panel sizes itself from these.
        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: implicitHeight
        Layout.preferredHeight: implicitHeight
        Layout.maximumHeight: root.vertical ? Number.POSITIVE_INFINITY : implicitHeight
        Layout.fillHeight: root.vertical
        surface: consoleColors.panel
        ColumnLayout {
            id: content
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            GridLayout {
                // One row of tiles across, one column upright.
                flow: root.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
                rowSpacing: 4; columnSpacing: 4
                Layout.fillWidth: true; Layout.fillHeight: !root.vertical
                ClockTile {}
                Repeater { model: root.leftSlots; delegate: Slot {} }
                Workspaces {}
                Repeater { model: root.rightSlots; delegate: Slot {} }
                SessionButtons {}
            }
            GridLayout {
                flow: root.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
                rowSpacing: 3; columnSpacing: 3
                Layout.fillWidth: true
                Layout.fillHeight: root.vertical
                Layout.preferredHeight: root.vertical ? -1 : root.u(24)
                Layout.maximumHeight: root.vertical ? Number.POSITIVE_INFINITY : root.u(24)
                Text {
                    Layout.fillWidth: root.vertical
                    Layout.preferredWidth: root.vertical ? -1 : root.u(92)
                    text: Plasmoid.configuration.consoleLabel; color: consoleColors.panelText
                    font.pixelSize: root.u(9); font.family: consoleColors.font; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                }
                TaskStrip {}
                VolumeButton {}
            }
        }
    }

    AppMenu {
        id: appMenu
        appsModel: categoryApps
        onFindRequested: { applications.visualParent = root.fullRepresentationItem; applications.visible = true; }
        onRunRequested: root.run(root.dbus + " org.kde.krunner /App org.kde.krunner.App.display")
    }

    Keeper { id: calendarKeeper; dialog: calendar; segment: calendar.visualParent; inside: calendarHover.hovered }
    Keeper { id: volumeKeeper; dialog: volumePopup; segment: volumePopup.visualParent; inside: volumeHover.hovered }
    Keeper { id: popupKeeper; dialog: popup; segment: root.popupSegment; inside: popupHover.hovered }

    PlasmaCore.Dialog {
        id: calendar
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        mainItem: CalendarPanel {
            HoverHandler { id: calendarHover }
            Keys.onPressed: calendarKeeper.keyboard = true
            pluginsManager: eventPlugins
            onCloseRequested: calendar.visible = false
            onOpenCalendar: { calendar.visible = false; root.run(Launch.resolve(Plasmoid.configuration.calendarCommand || "@calendar", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg))); }
        }
        onVisibleChanged: if (visible) { calendarKeeper.opened(); mainItem.forceActiveFocus(); }
    }

    PlasmaCore.Dialog {
        id: volumePopup
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        onVisibleChanged: if (visible) { volumeKeeper.opened(); volumeBody.forceActiveFocus(); }
        mainItem: Bevel {
            id: volumeBody
            HoverHandler { id: volumeHover }
            Keys.onPressed: volumeKeeper.keyboard = true
            width: 276; height: 168
            surface: consoleColors.window
            focus: true
            Keys.onEscapePressed: volumePopup.visible = false
            Keys.onUpPressed: root.setVolume(root.volume + 5)
            Keys.onDownPressed: root.setVolume(root.volume - 5)
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 5; spacing: 4
                Bevel {
                    Layout.fillWidth: true; Layout.preferredHeight: 27; surface: consoleColors.highlight
                    Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Audio  %1", root.volumeState); color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
                }
                Slider {
                    Layout.fillWidth: true
                    from: 0; to: 100; stepSize: 1
                    value: Math.min(100, root.volume)
                    enabled: !root.muted
                    onMoved: root.setVolume(value)
                    Accessible.name: i18nd("cde-copper", "Volume")
                }
                RowLayout {
                    Layout.fillWidth: true
                    ConsoleButton {
                        Layout.fillWidth: true; implicitHeight: 38; horizontal: true; iconSize: 22
                        text: root.muted ? i18nd("cde-copper", "Unmute") : i18nd("cde-copper", "Mute"); iconName: root.muted ? "audio-volume-high" : "audio-volume-muted"
                        surface: consoleColors.window; foreground: consoleColors.windowText
                        selected: root.muted
                        onClicked: { root.muted = !root.muted; runner.connectSource("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"); }
                    }
                    ConsoleButton {
                        Layout.fillWidth: true; implicitHeight: 38; horizontal: true; iconSize: 22
                        text: i18nd("cde-copper", "Settings…"); iconName: "preferences-system"
                        surface: consoleColors.window; foreground: consoleColors.windowText
                        onClicked: { volumePopup.visible = false; root.run(Launch.resolve("@settings kcm_pulseaudio", [], (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg))); }
                    }
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
        onVisibleChanged: if (visible) { popupKeeper.opened(); popupBody.forceActiveFocus(); }
        mainItem: Bevel {
            id: popupBody
            HoverHandler { id: popupHover }
            Keys.onPressed: popupKeeper.keyboard = true
            width: 320; height: 41 + root.entries.length * 38
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
                        enabled: modelData.command !== ""
                        Accessible.name: modelData.tip || modelData.label
                        onClicked: {
                            popup.visible = false;
                            // The style manager is a page of the console's settings.
                            if (modelData.command === "@style") Plasmoid.internalAction("configure").trigger();
                            else root.run(Launch.resolve(modelData.command, modelData.args, (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)));
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
                    Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Find Application"); color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 13 }
                }
                TextField {
                    id: appSearch
                    Layout.fillWidth: true; placeholderText: i18nd("cde-copper", "Search")
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
                        text: model.display || i18nd("cde-copper", "Application")
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
