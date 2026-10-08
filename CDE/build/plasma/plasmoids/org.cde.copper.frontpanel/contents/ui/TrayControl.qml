import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import "launch.js" as Launch

// The panel around the console: the system tray beside it (its volume
// entry, its icons behind the console's button) and the panel's frame.
// Not drawn; it only reaches into the panel's layout.
Item {
    id: tray
    // The console (main.qml): given, never looked up. Its parents are the
    // panel's layout and window, where the tray and the frame live.
    required property var root
    Connections {
        target: Plasmoid.configuration
        function onHideTrayVolumeChanged() { tray.syncTray(); }
        function onHideTrayIconsChanged() { tray.syncTray(); tray.placeTray(); }
        // The network button chosen or dropped: the tray's network entry follows.
        function onSmallButtonsChanged() { tray.syncTray(); }
        function onPanelFrameChanged() { tray.placePanelFrame(); }
    }
    // The tray beside the console would show a second volume control; the
    // console's own one (wheel, click for slider and mute) replaces it.
    function syncTray() {
        const hide = Plasmoid.configuration.hideTrayVolume;
        // With hideTrayIcons every entry the tray knows goes to its hidden
        // list: the tray beside the console shrinks to its arrow (and what
        // asks for attention), the entries open from the console's button.
        const icons = Plasmoid.configuration.hideTrayIcons;
        // With the entries behind the button, the list is kept short: the
        // tray's entries the console covers itself (its network button) or
        // that are set up once and never opened again (weather, input
        // methods, screen layout, vaults) are switched off in the tray
        // (taken out of extraItems), recorded in the tray's own settings
        // (cdeDisabledItems) and put back when the option goes off. One the
        // user switches on again in the tray's settings stays on: only
        // entries not yet recorded are taken out.
        const smallButtons = Plasmoid.configuration.smallButtons || [];
        const curated = ["org.kde.plasma.weather", "org.kde.plasma.keyboardlayout", "org.kde.plasma.manage-inputmethod",
                         "org.kde.kscreen", "org.kde.plasma.vault"]
            .concat(smallButtons.indexOf("network") >= 0 ? ["org.kde.plasma.networkmanagement"] : []);
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
            + (hide ? " if (has) items = items.filter(function (i) { return i !== 'org.kde.plasma.volume'; });"
                    : " if (!has && items.length) items.push('org.kde.plasma.volume');")
            + " var off = list(w, 'cdeDisabledItems'); var curated = " + JSON.stringify(curated) + ";"
            + (icons ? " var out = curated.filter(function (i) { return items.indexOf(i) >= 0 && off.indexOf(i) < 0; });"
                       + " if (out.length) { items = items.filter(function (i) { return out.indexOf(i) < 0; }); w.writeConfig('cdeDisabledItems', off.concat(out)); }"
                     : " if (off.length) { off.forEach(function (i) { if (items.indexOf(i) < 0) items.push(i); }); w.writeConfig('cdeDisabledItems', []); }")
            + " w.writeConfig('extraItems', items);"
            + " var now = list(w, 'hiddenItems');"
            + (icons ? " var add = list(w, 'knownItems').concat(" + JSON.stringify(tray.statusIds) + ").filter(function (i, k, all) { return now.indexOf(i) < 0 && all.indexOf(i) === k; });"
                       + " if (add.length) { w.writeConfig('hiddenItems', now.concat(add)); ours.writeConfig('trayHiddenByConsole', mine.concat(add)); }"
                     : " if (mine.length) { w.writeConfig('hiddenItems', now.filter(function (i) { return mine.indexOf(i) < 0; })); ours.writeConfig('trayHiddenByConsole', []); }")
            + " } }";
        tray.root.execute(tray.root.dbus + " org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript " + Launch.quote(script));
    }
    // Plasma's tray has no setting to drop its arrow. With its entries
    // behind the console's button, its container in the panel's layout is
    // hidden instead; the tray keeps running for notifications and its popup.
    // What placeTray() changed, to put back when the option is switched off.
    property var trayLayoutSpacing: null
    property var hiddenTray: null
    function placeTray() {
        const layout = tray.root.parent ? tray.root.parent.parent : null;
        if (!layout || !layout.children) return;
        const hide = Plasmoid.configuration.hideTrayIcons;
        for (const item of layout.children) {
            const applet = item.applet ? item.applet.plasmoid : null;
            if (!applet || applet.pluginName !== "org.kde.plasma.systemtray") continue;
            if (hide) { item.visible = false; tray.hiddenTray = item; }
            else if (tray.hiddenTray === item) { item.visible = true; tray.hiddenTray = null; }
        }
        // The panel's layout keeps its spacing after the console, before an
        // invisible end spacer: four pixels more panel on one side.
        if (hide && tray.trayLayoutSpacing === null) {
            tray.trayLayoutSpacing = [layout.columnSpacing, layout.rowSpacing];
            layout.columnSpacing = 0; layout.rowSpacing = 0;
        } else if (!hide && tray.trayLayoutSpacing !== null) {
            layout.columnSpacing = tray.trayLayoutSpacing[0]; layout.rowSpacing = tray.trayLayoutSpacing[1];
            tray.trayLayoutSpacing = null;
        }
    }
    // The panel's own background (the theme's panel-background frame) behind
    // the console. Without it the console stands on the desktop by itself;
    // the panel keeps its size, so the margin around stays, transparent.
    // Hidden by scale, not opacity: Plasma binds the frames' opacity to its
    // adaptive panel opacity, and an assignment would break that binding.
    function placePanelFrame() {
        let item = tray.root.parent;
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
    // The tray fills its item list on its first start; look once it has.
    Timer { id: trayTimer; interval: 4000; running: true; onTriggered: { tray.placeTray(); tray.placePanelFrame(); trayIds.connectSource("python3 " + Launch.quote(tray.root.helper) + " tray"); } }
    // Applications add status icons while the session runs: look again
    // every half minute while the tray's entries are kept behind the button.
    property var statusIds: []
    Timer {
        interval: 30000; repeat: true
        running: Plasmoid.configuration.hideTrayIcons
        onTriggered: trayIds.connectSource("python3 " + Launch.quote(tray.root.helper) + " tray")
    }
    P5Support.DataSource {
        id: trayIds
        engine: "executable"
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName);
            let ids = [];
            try { ids = JSON.parse(data.stdout); } catch (e) {}
            if (!tray.traySynced || JSON.stringify(ids) !== JSON.stringify(tray.statusIds)) {
                tray.statusIds = ids; tray.traySynced = true; tray.syncTray();
            }
        }
    }
    property bool traySynced: false
}
