pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtCore
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import org.kde.plasma.private.kicker as Kicker
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
    Connections {
        target: Plasmoid
        function onActivated() { root.openApplications(root.appsTile || root.fullRepresentationItem); }
    }
    // Every setting of this console also goes to cdecopperrc [Console]. The
    // applet's own configuration lives in the panel layout and is gone the
    // moment a global theme (or apply.sh --panel) rebuilds the panels; the
    // layout script reads this file and hands the values to the new console.
    // Lists are written in KConfig's comma form, so writeConfig in the
    // layout script can pass them through unchanged.
    Connections {
        target: Plasmoid.configuration
        function onValueChanged(key, value) {
            if (key === "everyScreen") return;   // kept as [Console] AllScreens by placeConsoles
            const text = Array.isArray(value) ? value.join(",") : String(value);
            root.run("kwriteconfig6 --file cdecopperrc --group Console --key " + key + " " + Launch.quote(text));
        }
    }
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    // On the screen edge (not floating) the panel containment gives the
    // console no margins at all, so it reaches the edge (Plasma's own
    // facility for edge-to-edge applets; found by Codex in plasma-desktop's
    // panel containment). Floating keeps the margins.
    Plasmoid.constraintHints: Plasmoid.configuration.floating ? Plasmoid.NoHint : Plasmoid.CanFillArea

    property string popupTitle: ""
    property var entries: []
    property date now: new Date()
    property string activeSection: ""
    property string networkState: i18nd("cde-copper", "Network")
    // "wifi", "wired" or "" (offline), the connection's name, WLAN signal 0-100
    property string networkKind: ""
    property string networkName: ""
    property int networkSignal: 0
    // The WLAN device to join with: a free one, else the connected one (one
    // card: switching networks; a card sending a hotspot stays untouched).
    property string wifiDevice: ""
    readonly property string networkIcon: networkKind === "wired" ? "network-wired-activated"
        : networkKind !== "wifi" ? "network-offline"
        : networkSignal >= 75 ? "network-wireless-signal-excellent" : networkSignal >= 50 ? "network-wireless-signal-good"
        : networkSignal >= 25 ? "network-wireless-signal-ok" : "network-wireless-signal-weak"
    // The session block's small buttons, the known ones in the chosen order.
    readonly property var smallKinds: ["configure", "lock", "desktop", "load", "llm", "volume", "network", "logout"]
    readonly property var smallButtons: {
        const chosen = (Plasmoid.configuration.smallButtons || []).filter(k => smallKinds.indexOf(k) >= 0);
        return chosen.length ? chosen : ["configure"];
    }
    property string volumeState: i18nd("cde-copper", "Audio")
    property int volume: 0
    property bool muted: false
    readonly property string dbus: Launch.DBUS
    readonly property var leftSlots: Launch.parse(Plasmoid.configuration.leftLaunchers, Launch.LEFT)
    readonly property var rightSlots: Launch.parse(Plasmoid.configuration.rightLaunchers, Launch.RIGHT)
    // Open windows as the strip under the tiles, as a window tile beside
    // the launchers (left or right) whose list opens like a subpanel, or as
    // small icons under each workspace's button. Without the strip its row
    // goes, and the console is lower. The workspaces' own setting comes
    // first while the switcher is shown; hidden, the strip or tile again.
    readonly property string windowDisplay: {
        if (Plasmoid.configuration.showWorkspaces) {
            const own = Plasmoid.configuration.workspaceWindows;
            if (own === "icons") return "workspaces";
            if (own === "pager") return "pager";
        }
        const wanted = Plasmoid.configuration.windowDisplay;
        return ["tileLeft", "tileRight"].indexOf(wanted) >= 0 ? wanted : "strip";
    }
    readonly property bool stripHidden: windowDisplay !== "strip"
    // Whichever setting hides or brings back the strip: the panel's height.
    onStripHiddenChanged: configurePanel()

    // Every colour comes from the active colour scheme: the console is the
    // Complementary set (CDE colour set 8 with a CDE palette), popups use
    // Window/View, the selection is the active-window colour.
    Item { id: complementary; Kirigami.Theme.colorSet: Kirigami.Theme.Complementary; Kirigami.Theme.inherit: false }
    Item { id: windowSet; Kirigami.Theme.colorSet: Kirigami.Theme.Window; Kirigami.Theme.inherit: false }
    Item { id: viewSet; Kirigami.Theme.colorSet: Kirigami.Theme.View; Kirigami.Theme.inherit: false }
    QtObject {
        id: consoleColors
        readonly property color panel: complementary.Kirigami.Theme.backgroundColor
        // Hard contrast (setting): pure black, or white on a dark surface.
        readonly property bool hard: Plasmoid.configuration.hardContrast
        // Labels in semibold with hard contrast: thin small type was the
        // other half of the weak contrast, beside the colours.
        readonly property int weight: hard ? Font.DemiBold : Font.Normal
        readonly property color panelText: hard ? Motif.stark(panel) : complementary.Kirigami.Theme.textColor
        readonly property color window: windowSet.Kirigami.Theme.backgroundColor
        readonly property color windowText: hard ? Motif.stark(window) : windowSet.Kirigami.Theme.textColor
        readonly property color field: viewSet.Kirigami.Theme.backgroundColor
        readonly property color fieldText: hard ? Motif.stark(field) : viewSet.Kirigami.Theme.textColor
        readonly property color highlight: windowSet.Kirigami.Theme.highlightColor
        readonly property color highlightText: hard ? Motif.stark(highlight) : windowSet.Kirigami.Theme.highlightedTextColor
        readonly property string font: Kirigami.Theme.defaultFont.family
        readonly property date now: root.now
        // Console scale (settings): every size below is a multiple of it.
        readonly property real unit: Math.max(0.5, Math.min(3, Plasmoid.configuration.consoleScale || 1))
    }

    function run(command) {
        runner.connectSource(Launch.detached(command));
    }
    // Not detached: short commands whose end is of no interest (wpctl).
    function execute(command) {
        runner.connectSource(command);
    }
    // Launchers changed on the console itself (DropTarget.qml): written
    // as the settings page writes them; leftSlots and rightSlots follow.
    function storeLaunchers(lists) {
        Plasmoid.configuration.leftLaunchers = Launch.serialize(lists.left);
        Plasmoid.configuration.rightLaunchers = Launch.serialize(lists.right);
    }
    function moveLauncher(fromSide, fromIndex, toSide, toIndex) {
        storeLaunchers(Launch.moved(leftSlots, rightSlots, fromSide, fromIndex, toSide, toIndex));
    }
    function replaceLauncher(side, index, slot) {
        storeLaunchers({left: side === "left" ? Launch.replaced(leftSlots, index, slot) : leftSlots,
                        right: side === "right" ? Launch.replaced(rightSlots, index, slot) : rightSlots});
    }
    function launch(slot, anchor) {
        if (slot.command === "@applications") openApplications(anchor);
        else if (slot.command === "@layouts") openLayouts(anchor);
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
        case "layouts": openLayouts(anchor); break;
        case "terminals": openSection(i18nd("cde-copper", "Terminals"), terminalEntries(slot), anchor); break;
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
                entry(i18nd("cde-copper", "Help Center"), "help-browser", "@help"),
                entry(i18nd("cde-copper", "Lock Screen"), "system-lock-screen", dbus + " org.freedesktop.ScreenSaver /ScreenSaver Lock"),
                entry(i18nd("cde-copper", "Leave Session..."), "system-log-out", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptAll"),
                entry(i18nd("cde-copper", "Restart..."), "system-reboot", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptReboot"),
                entry(i18nd("cde-copper", "Shut Down..."), "system-shutdown", dbus + " org.kde.LogoutPrompt /LogoutPrompt promptShutDown")];
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
    // A new terminal, or a set of them in their places (see arrange/):
    // three around the console, four on the other screen, or both.
    function terminalEntries(slot) {
        const list = [entry(i18nd("cde-copper", "New Terminal"), "utilities-terminal", slot.command || "@terminal"),
                      entry(i18nd("cde-copper", "Three Terminals Around the Console"), "view-split-left-right", "@terminals three")];
        if (Qt.application.screens.length > 1) {
            list.push(entry(i18nd("cde-copper", "Four Terminals on the Other Screen"), "view-grid", "@terminals four"));
            list.push(entry(i18nd("cde-copper", "Seven Terminals on Both Screens"), "view-grid", "@terminals seven"));
        } else {
            list.push(entry(i18nd("cde-copper", "Four Terminals"), "view-grid", "@terminals four"));
        }
        return list;
    }
    // Saved window layouts (contents/code/layouts.py): a preview of the
    // screens, the name and the applications; a click restores the layout.
    property var layoutList: []
    readonly property string layoutsHelper: decodeURIComponent(Qt.resolvedUrl("../code/layouts.py").toString().replace(/^file:\/\//, ""))
    function openLayouts(anchor) {
        popup.visible = false;
        if (layoutsPopup.visible && layoutsPopup.visualParent === anchor) { layoutsPopup.visible = false; return; }
        layoutsPopup.visualParent = anchor;
        layoutSource.connectSource("python3 " + Launch.quote(layoutsHelper) + " list");
        layoutsPopup.visible = true;
    }
    function saveLayout() {
        layoutsPopup.visible = false;
        // The screenshot for the preview is taken once the popup is gone.
        run("sleep 0.6; python3 " + Launch.quote(layoutsHelper) + " save --title " + Launch.quote(i18nd("cde-copper", "Save Layout"))
            + " --label " + Launch.quote(i18nd("cde-copper", "Name of the layout:")));
    }
    function restoreLayout(id) {
        layoutsPopup.visible = false;
        run("python3 " + Launch.quote(layoutsHelper) + " restore " + Launch.quote(id));
    }
    function deleteLayout(id) {
        run("python3 " + Launch.quote(layoutsHelper) + " delete " + Launch.quote(id));
        layoutList = layoutList.filter(l => l.id !== id);
    }
    P5Support.DataSource {
        id: layoutSource
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            let list = [];
            try { list = JSON.parse(data.stdout); }
            catch (e) { console.warn("CDE layouts:", e, data.stderr); }
            // Unchanged, the cards (and their previews) stay as they are.
            if (JSON.stringify(list) !== JSON.stringify(root.layoutList)) root.layoutList = list;
        }
    }
    function helpEntries() {
        return [entry(i18nd("cde-copper", "Help Center"), "help-browser", "@help"),
                entry(i18nd("cde-copper", "Keyboard Shortcuts"), "preferences-desktop-keyboard", "@settings kcm_keys"),
                entry(i18nd("cde-copper", "System Information"), "computer", "kinfocenter"),
                entry(i18nd("cde-copper", "About CDE Copper"), "cde-menu", "xdg-open https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE")];
    }
    // One console, or one on every screen: consoles are added to screens
    // without one (as the panel this one sits in) or removed from all
    // screens but the first that has one. The choice goes to cdecopperrc,
    // where the global theme's layout script reads it.
    function placeConsoles() {
        const every = Plasmoid.configuration.everyScreen;
        run("kwriteconfig6 --file cdecopperrc --group Console --key AllScreens " + (every ? "true" : "false"));
        const script = "var every = " + (every ? "true" : "false") + "; var have = {}; var proto = null; var keep = -1;"
            + " for (var p of panels()) for (var w of p.widgets()) if (w.type === 'org.cde.copper.frontpanel') {"
            + " have[p.screen] = true; if (!proto || p.screen < proto.screen) proto = p; if (keep < 0 || p.screen < keep) keep = p.screen; }"
            + " if (proto && every) { for (var s = 0; s < screenCount; ++s) if (!have[s]) {"
            + " var n = new Panel; n.screen = s; n.location = proto.location; n.height = proto.height;"
            + " n.lengthMode = proto.lengthMode; n.floating = proto.floating; n.hiding = proto.hiding; n.alignment = 'center';"
            + " var c = n.addWidget('org.cde.copper.frontpanel'); c.currentConfigGroup = ['General'];"
            + " var saved = ConfigFile('cdecopperrc', 'Console'); for (var k of saved.keys) if (k !== 'AllScreens') c.writeConfig(k, saved.readEntry(k));"
            + " c.writeConfig('everyScreen', true);"
            + " if (n.screen !== s) n.remove(); } }"
            + " if (proto && !every) { for (var q of panels()) { var mine = false;"
            + " for (var x of q.widgets()) if (x.type === 'org.cde.copper.frontpanel') mine = true;"
            + " if (mine && q.screen !== keep) q.remove(); } }";
        runner.connectSource(dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(script));
    }
    function configurePanel() {
        const modes = ["none", "autohide", "dodgewindows"];
        const mode = modes[Math.max(0, Math.min(2, Plasmoid.configuration.visibilityMode))];
        const edges = ["bottom", "top", "left", "right"];
        const chosen = Plasmoid.configuration.edge;
        const edge = chosen >= 0 && chosen < 4 ? edges[chosen] : (Plasmoid.configuration.topEdge ? "top" : "bottom");
        // Floating, Plasma keeps a gap and the panel some air around the
        // console; on the edge the panel is exactly the console's height,
        // so the console sits on the screen edge.
        // Floating, Plasma keeps a gap to the edge and the panel some air
        // around the console; on the edge the panel is exactly the console
        // (CanFillArea, below, drops the containment's margins).
        // The window tile drops the strip's row: 28 lower.
        const height = Math.round(((Plasmoid.configuration.floating ? 128 : 116) - (root.stripHidden ? 28 : 0)) * consoleColors.unit);
        // Upright the console runs the full height, so the window list has
        // room; with the window tile it is as tall as its tiles.
        const length = (edge === "left" || edge === "right") && !root.stripHidden ? "fill" : "fit";
        // Plasma reserves the screen edge that reveals a hidden panel when the
        // hiding mode is set, and does not move it with the panel: moved
        // afterwards (or in the same breath), the console could not be brought
        // back. So: place it while it stays visible, then hide it.
        const ours = "for (var p of panels()) { for (var w of p.widgets()) { if (w.type === 'org.cde.copper.frontpanel') { ";
        const place = ours + "p.hiding = 'none'; p.location = '" + edge + "'; p.height = " + height + "; p.lengthMode = '" + length + "'; p.alignment = 'center'; p.offset = 0; p.floating = " + (Plasmoid.configuration.floating ? "true" : "false") + "; } } }";
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
        onTriggered: root.run(root.toolCommand("palette --follow-scheme --notify"))
    }

    property string pendingHiding: ""
    Timer {
        id: hidingTimer
        interval: 1500
        onTriggered: if (root.pendingHiding) runner.connectSource(root.dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(root.pendingHiding))
    }

    function setVolume(percent) {
        const value = Math.max(0, Math.min(150, Math.round(percent)));
        root.volume = value;
        root.volumeState = root.muted ? i18nd("cde-copper", "Muted") : value + "%";
        runner.connectSource("wpctl set-volume @DEFAULT_AUDIO_SINK@ " + value + "%");
    }
    function readNetwork(stdout) {
        const parts = stdout.split("---");
        let kind = "", name = "", signal = 0, wifi = "", free = "";
        for (const line of (parts[0] || "").split("\n")) {
            const f = root.terseFields(line);
            if (f.length < 4) continue;
            if (f[0] === "wifi" && f[1] === "disconnected" && !free) free = f[3];
            if (f[1] !== "connected") continue;
            if (f[0] === "ethernet" && kind !== "wired") { kind = "wired"; name = f[2]; }
            else if (f[0] === "wifi") { wifi = wifi || f[3]; if (!kind) { kind = "wifi"; name = f[2]; } }
        }
        root.wifiDevice = free || wifi;
        // Not NetworkManager's (an Ubuntu cloud image leaves the cable to
        // systemd-networkd): the default route tells cable or WLAN.
        if (!kind) {
            const route = (parts[2] || "").match(/ dev (\S+)/);
            if (route) { name = route[1]; kind = name.indexOf("wl") === 0 ? "wifi" : "wired"; }
        }
        for (const line of (parts[1] || "").split("\n"))
            if (line.indexOf("*:") === 0) signal = Number(line.slice(2)) || 0;
        root.networkKind = kind; root.networkName = name; root.networkSignal = signal;
        root.networkState = !kind ? i18nd("cde-copper", "Offline")
            : kind === "wifi" ? i18nd("cde-copper", "WLAN %1, %2 %", name, signal) : i18nd("cde-copper", "Cable %1", name);
    }
    // nmcli's terse form (":" inside a field escaped) as its fields; here and
    // in the network popup's list.
    function terseFields(line) {
        const out = [];
        let field = "";
        for (let i = 0; i < line.length; i++) {
            if (line[i] === "\\" && i + 1 < line.length) { field += line[++i]; continue; }
            if (line[i] === ":") { out.push(field); field = ""; continue; }
            field += line[i];
        }
        out.push(field);
        return out;
    }
    function readVolume(stdout) {
        const match = stdout.match(/Volume: ([0-9.]+)/);
        root.muted = stdout.indexOf("MUTED") >= 0;
        if (match) root.volume = Math.round(Number(match[1]) * 100);
        root.volumeState = root.muted ? i18nd("cde-copper", "Muted") : match ? root.volume + "%" : i18nd("cde-copper", "Audio");
    }

    // The number, or the label from the console's settings; KWin's names
    // stay in the tooltips (Accessible.name).
    function workspaceLabel(index) {
        const own = ((Plasmoid.configuration.workspaceLabels || [])[index] || "").trim();
        return own !== "" ? own : String(index + 1);
    }
    // The switcher owns the workspace count: KWin gets as many workspaces as
    // configured (1-8). The buttons show numbers only, so the names KWin
    // keeps ("Arbeitsfläche 1", "Two", whatever the user chose) never mix
    // on the console; they stay in the tooltips. New workspaces are named
    // by their number.
    function syncWorkspaces() {
        if (!Plasmoid.configuration.showWorkspaces) return;
        const want = Math.max(1, Math.min(8, Plasmoid.configuration.workspaceCount));
        const ids = desktops.desktopIds;
        const vdm = root.dbus + " org.kde.KWin /VirtualDesktopManager ";
        for (let i = ids.length; i < want; i++) run(vdm + "createDesktop " + i + " " + (i + 1));
        for (let i = ids.length - 1; i >= want; i--) run(vdm + "removeDesktop " + Launch.quote(ids[i]));
    }
    Timer { id: workspaceSync; interval: 1500; onTriggered: root.syncWorkspaces() }
    Connections {
        target: Plasmoid.configuration
        function onWorkspaceCountChanged() { root.syncWorkspaces(); }
        function onShowWorkspacesChanged() { root.syncWorkspaces(); }
        function onVisibilityModeChanged() { root.configurePanel(); }
        function onTopEdgeChanged() { root.configurePanel(); }
        function onEdgeChanged() { root.configurePanel(); }
        function onConsoleScaleChanged() { root.configurePanel(); }
        function onFloatingChanged() { root.configurePanel(); }
        function onEveryScreenChanged() { root.placeConsoles(); }
        // The Style page's choice, taken by the settings dialog's Apply/OK.
        function onStyleRequestChanged() {
            let request = null;
            try { request = JSON.parse(Plasmoid.configuration.styleRequest); } catch (e) { return; }
            if (!request || !request.palette) return;
            let command = root.toolCommand("palette --notify --palette " + Launch.quote(request.palette));
            if (request.backdrop) command += " --backdrop " + Launch.quote(request.backdrop) + " --backdrop-scale " + Math.max(1, Math.min(3, request.scale || 1));
            if (["outlined", "floating", "slim"].indexOf(request.progress) >= 0) command += " --progress " + request.progress;
            if (/^(copper|palette|white|#[0-9a-fA-F]{6})$/.test(request.cursor || "")) command += " --cursor " + Launch.quote(request.cursor);
            if (request.lockscreen === "cde" || request.lockscreen === "plasma") command += " --lockscreen " + request.lockscreen;
            if (typeof request.windowShadow === "boolean") command += " --window-shadow " + (request.windowShadow ? "on" : "off");
            if (typeof request.patternColour === "boolean") command += " --pattern-colour " + (request.patternColour ? "palette" : "cde");
            root.run(command);
        }
    }

    // The KDE Store edition has no manage.py: palettes come from System
    // Settings there, and the tool's commands are skipped.
    function toolCommand(args) {
        return "[ -f " + Launch.quote(tool) + " ] && python3 " + Launch.quote(tool) + " " + args;
    }
    // The store edition brings its translations in the package; KDE looks
    // for the cde-copper catalogue in the user's locale folder, so they are
    // copied there (taking effect from the next start of the shell).
    readonly property string packageLocale: decodeURIComponent(Qt.resolvedUrl("../locale").toString().replace(/^file:\/\//, ""))
    function installTranslations() {
        run("p=" + Launch.quote(packageLocale) + "; d=\"${XDG_DATA_HOME:-$HOME/.local/share}/locale\"; "
            + "for f in \"$p\"/*/LC_MESSAGES/cde-copper.mo; do [ -f \"$f\" ] || continue; "
            + "l=\"${f#\"$p\"/}\"; mkdir -p \"$d/${l%/*}\" && cp -u \"$f\" \"$d/$l\"; done");
    }

    Component.onCompleted: {
        // 0.8.9-0.8.11 kept the workspace views in windowDisplay.
        const legacy = {workspaces: "icons", pager: "pager"}[Plasmoid.configuration.windowDisplay];
        if (legacy) {
            Plasmoid.configuration.workspaceWindows = legacy;
            Plasmoid.configuration.windowDisplay = "strip";
        }
        installTranslations();
        if (Plasmoid.configuration.consoleScale !== 1 || !Plasmoid.configuration.floating || stripHidden) configurePanel();
        workspaceSync.start();
    }

    Kicker.AppsModel { id: categoryApps; flat: false; sorted: true; autoPopulate: true; showSeparators: false; appletInterface: Plasmoid }

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
        // The devices (type, state, connection), then the WLAN in use with its
        // signal; nmcli's cached scan, no new one.
        connectedSources: ["sh -c 'timeout 3s env LC_ALL=C nmcli -t -f TYPE,STATE,CONNECTION,DEVICE device; echo ---; timeout 3s env LC_ALL=C nmcli -t -f IN-USE,SIGNAL device wifi list --rescan no; echo ---; ip -o route show default'",
                           "timeout 3s wpctl get-volume @DEFAULT_AUDIO_SINK@"]
        onNewData: function(sourceName, data) {
            if (sourceName.indexOf("nmcli") >= 0) root.readNetwork(data.stdout);
            else root.readVolume(data.stdout);
        }
    }
    // Changes from elsewhere (keys, the tray, other programs) at once: the
    // watcher returns with the first sink event from PipeWire's pulse
    // server, or after 20 s; then the volume is read and it watches again.
    // Without pactl it only waits, and the 5 s poll above stays.
    P5Support.DataSource {
        id: volumeWatch
        engine: "executable"
        readonly property string watch: "if command -v pactl >/dev/null; then timeout 20s sh -c 'LC_ALL=C stdbuf -oL pactl subscribe | { grep -m1 -q \" on sink \"; pkill -P $$ -x pactl; }'; else sleep 20; fi"
        readonly property string query: "timeout 3s wpctl get-volume @DEFAULT_AUDIO_SINK@"
        connectedSources: [watch]
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            if (sourceName === query) { root.readVolume(data.stdout); return; }
            connectSource(query);
            Qt.callLater(() => connectSource(watch));
        }
    }
    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: activities }
    TaskManager.TasksModel {
        id: tasks
        virtualDesktop: desktops.currentDesktop
        activity: activities.currentActivity
        screenGeometry: Plasmoid.containment.screenGeometry
        // The strip shows this workspace's windows; the tile's list all of
        // them, each with its workspace.
        filterByVirtualDesktop: !root.stripHidden
        filterByActivity: true
        // With one console per screen, each lists the windows on its own
        // screen; a single console lists the windows of all screens.
        filterByScreen: Plasmoid.configuration.windowsOnThisScreen && Plasmoid.configuration.everyScreen
        groupMode: Plasmoid.configuration.groupWindows && !root.stripHidden ? TaskManager.TasksModel.GroupApplications : TaskManager.TasksModel.GroupDisabled
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

    // All screens together, as one workspace spans them; with one console
    // per screen listing only its own windows, that screen.
    readonly property rect desktopArea: {
        if (tasks.filterByScreen) return Plasmoid.containment.screenGeometry;
        const all = Qt.application.screens;
        if (!all.length) return Qt.rect(0, 0, 1920, 1080);
        let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
        for (const s of all) {
            left = Math.min(left, s.virtualX); top = Math.min(top, s.virtualY);
            right = Math.max(right, s.virtualX + s.width); bottom = Math.max(bottom, s.virtualY + s.height);
        }
        return Qt.rect(left, top, right - left, bottom - top);
    }

    // The console's parts and popups live in files of their own beside this
    // one. Each is given this root (and consoleColors) as a property and
    // reaches the shared models and popups through these, never by id.
    readonly property TaskManager.TasksModel taskModel: tasks
    readonly property TaskManager.VirtualDesktopInfo desktopInfo: desktops
    readonly property Item taskMenu: windowMenu
    readonly property PlasmaCore.Dialog sectionDialog: popup
    readonly property PlasmaCore.Dialog windowsDialog: windowsPopup
    readonly property PlasmaCore.Dialog llmDialog: llmPopup
    readonly property PlasmaCore.Dialog volumeDialog: volumePopup
    readonly property PlasmaCore.Dialog networkDialog: networkPopup
    readonly property PlasmaCore.Dialog calendarDialog: calendar

    property var llmNodes: []
    property real llmTotal: 0
    property real llmPeak: 1
    property bool llmFetching: false
    property bool llmSmallVisible: false
    property bool llmTileVisible: false
    readonly property bool llmVisible: llmSmallVisible || llmTileVisible
    property Item llmPopupSegment: null
    function toggleLlm(anchor, segment) {
        const close = llmPopup.visible && llmPopup.visualParent === anchor;
        llmPopupSegment = segment;
        llmPopup.visualParent = anchor;
        llmPopup.visible = !close;
    }
    readonly property string llmHelper: decodeURIComponent(Qt.resolvedUrl("../code/llmverbund.py").toString().replace(/^file:\/\//, ""))
    readonly property string llmCommand: "python3 " + Launch.quote(llmHelper) + " " + Launch.quote(Plasmoid.configuration.llmHosts)
    function fetchLlm() {
        if (!llmVisible || llmFetching) return;
        llmFetching = true;
        llmSource.connectSource(llmCommand);
    }
    onLlmVisibleChanged: { if (llmVisible) fetchLlm(); else llmPopup.visible = false; }
    Connections {
        target: Plasmoid.configuration
        function onLlmHostsChanged() { root.llmNodes = []; root.llmTotal = 0; root.fetchLlm(); }
    }
    Timer { interval: 3000; repeat: true; running: root.llmVisible; onTriggered: root.fetchLlm() }
    P5Support.DataSource {
        id: llmSource
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            root.llmFetching = false;
            if (sourceName !== root.llmCommand) { root.fetchLlm(); return; }
            try {
                const result = JSON.parse(data.stdout);
                root.llmNodes = result.nodes;
                root.llmTotal = result.total;
                for (const node of result.nodes) root.llmPeak = Math.max(root.llmPeak, node.tokens_per_second);
            } catch (e) { root.llmNodes = []; root.llmTotal = 0; }
        }
    }
    // Opens the system tray's popup (hidden icons) the way a click on it does.
    function showHiddenIcons() {
        for (const applet of Plasmoid.containment.applets) {
            if (applet && applet.pluginName === "org.kde.plasma.systemtray") { applet.activated(); return; }
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

    // The window active last: the open list takes the focus, and tile and
    // list should still show the window the user came from.
    property var activeWindowIcon: null
    property string activeWindowTitle: ""
    property string activeWindowId: ""
    Connections {
        target: tasks
        function onActiveTaskChanged() {
            if (!tasks.activeTask.valid) return;
            root.activeWindowIcon = tasks.data(tasks.activeTask, Qt.DecorationRole);
            root.activeWindowTitle = tasks.data(tasks.activeTask, Qt.DisplayRole) || "";
            root.activeWindowId = String(tasks.data(tasks.activeTask, TaskManager.AbstractTasksModel.WinIdList));
        }
        // A window closed: forget it once nothing in the list is it.
        function onCountChanged() {
            for (let i = 0; i < tasks.count; i++)
                if (String(tasks.data(tasks.makeModelIndex(i), TaskManager.AbstractTasksModel.WinIdList)) === root.activeWindowId) return;
            root.activeWindowIcon = null; root.activeWindowTitle = ""; root.activeWindowId = "";
        }
    }
    // The next (or previous) window after the active one comes forward.
    function stepWindow(delta) {
        const count = tasks.count;
        if (count === 0) return;
        let active = -1;
        for (let i = 0; i < count; i++)
            if (tasks.data(tasks.makeModelIndex(i), TaskManager.AbstractTasksModel.IsActive)) active = i;
        const next = active < 0 ? (delta > 0 ? 0 : count - 1) : (active + delta + count) % count;
        tasks.requestActivate(tasks.makeModelIndex(next));
    }
    // Bumped whenever the windows change, for bindings that read the model
    // through tasks.data() rather than as a view's delegate.
    property int windowRevision: 0
    Connections {
        target: tasks
        function onDataChanged() { root.windowRevision++; }
        function onRowsInserted() { root.windowRevision++; }
        function onRowsRemoved() { root.windowRevision++; }
        function onRowsMoved() { root.windowRevision++; }
        function onModelReset() { root.windowRevision++; }
    }
    // The model rows of the windows on one workspace, those on all of them
    // included.
    function windowRows(desktop, revision) {
        const rows = [];
        if (root.windowDisplay !== "workspaces" && root.windowDisplay !== "pager") return rows;
        for (let i = 0; i < tasks.count; i++) {
            const idx = tasks.makeModelIndex(i);
            if (tasks.data(idx, TaskManager.AbstractTasksModel.IsOnAllVirtualDesktops)
                    || (tasks.data(idx, TaskManager.AbstractTasksModel.VirtualDesktops) || []).indexOf(desktop) >= 0)
                rows.push(i);
        }
        return rows;
    }
    // The workspace a window is on, as its button shows it; "∗" on all of
    // them, nothing with a single workspace.
    function windowWorkspace(onAll, ids) {
        if (desktops.desktopIds.length < 2) return "";
        if (onAll) return "∗";
        const index = desktops.desktopIds.indexOf((ids || [])[0]);
        return index >= 0 ? root.workspaceLabel(index) : "";
    }

    fullRepresentation: Bevel {
        id: frontConsole
        // Across: as wide as its tiles, 116 high. Upright: 116 wide, and as
        // tall as the screen allows, the window list taking the rest.
        implicitWidth: root.vertical ? root.u(116) : content.implicitWidth + 10
        implicitHeight: root.vertical ? content.implicitHeight + 10 : root.u(root.stripHidden ? 88 : 116)
        // The panel sizes itself from these.
        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: implicitHeight
        Layout.preferredHeight: implicitHeight
        Layout.maximumHeight: root.vertical && !root.stripHidden ? Number.POSITIVE_INFINITY : implicitHeight
        Layout.fillHeight: root.vertical && !root.stripHidden
        surface: consoleColors.panel
        ColumnLayout {
            id: content
            anchors.fill: parent; anchors.margins: 5; spacing: 4
            GridLayout {
                // One row of tiles across, one column upright.
                flow: root.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
                rowSpacing: 4; columnSpacing: 4
                Layout.fillWidth: true; Layout.fillHeight: !root.vertical
                ClockTile { root: root; colors: consoleColors }
                Repeater { model: root.leftSlots; delegate: Slot { root: root; colors: consoleColors; side: "left" } }
                WindowTile { root: root; colors: consoleColors; visible: root.windowDisplay === "tileLeft" }
                Workspaces { root: root; colors: consoleColors }
                WindowTile { root: root; colors: consoleColors; visible: root.windowDisplay === "tileRight" }
                Repeater { model: root.rightSlots; delegate: Slot { root: root; colors: consoleColors; side: "right" } }
                LlmTile { root: root; colors: consoleColors; visible: Plasmoid.configuration.llmTile }
                SessionButtons { root: root; colors: consoleColors }
            }
            GridLayout {
                visible: !root.stripHidden
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
                    font.weight: consoleColors.weight
                }
                TaskStrip { root: root }
                VolumeButton { root: root; visible: root.smallButtons.indexOf("volume") < 0 }
            }
        }
    }

    AppMenu {
        id: appMenu
        appsModel: categoryApps
        onFindRequested: { applications.visualParent = root.fullRepresentationItem; applications.visible = true; }
        onRunRequested: root.run(root.dbus + " org.kde.krunner /App org.kde.krunner.App.display")
    }
    FindPopup { id: applications; colors: consoleColors }
    // The subpanels; each keeps itself open while the pointer is on it or on
    // the segment that opened it (Keeper.qml).
    SectionPopup { id: popup; root: root; colors: consoleColors }
    WindowsPopup { id: windowsPopup; root: root; colors: consoleColors }
    // A task button's window menu (right click).
    TaskMenu { id: windowMenu; tasksModel: tasks; desktopInfo: desktops; workspaceLabel: i => root.workspaceLabel(i) }
    LayoutsPopup { id: layoutsPopup; root: root; colors: consoleColors }
    CalendarPopup { id: calendar; root: root }
    VolumePopup { id: volumePopup; root: root; colors: consoleColors }
    NetworkPopup { id: networkPopup; root: root; colors: consoleColors }
    LlmPopup { id: llmPopup; root: root; colors: consoleColors }
    TrayControl { root: root }
}
