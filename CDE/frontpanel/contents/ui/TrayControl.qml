import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
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
        function onTrayIconsOnlyChanged() { tray.fitPopupLater(); }
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
            + " for (var p of panels()) { var ours = p.widgets().filter(function (w) { return w.id === " + Plasmoid.id + "; })[0]; if (!ours) continue;"
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
            tray.trayItem = item.applet;
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
    // Plasma's tray popup is never smaller than 24 by 24 grid units: room
    // for an entry's own view (notifications, KDE Connect). With the grid
    // of entries alone its lower half stays empty. While the grid shows,
    // the console lowers the popup's minimum to the grid's rows and
    // resizes the window to it; with an entry's view open, Plasma's size
    // comes back. The minimum is the popup's Layout attached property,
    // the one Plasma's dialog reads (libplasma AppletPopup). The tray
    // builds its dialog itself (no fullRepresentationItem); its root item
    // in the panel exposes the grid (hiddenLayout) and its state.
    property var trayItem: null                             // the tray's root item in the panel
    readonly property var trayState: trayItem && trayItem.systemTrayState ? trayItem.systemTrayState : null
    readonly property var popupGrid: trayItem && trayItem.hiddenLayout ? trayItem.hiddenLayout : null
    property real popupFullWidth: 0                         // Plasma's minimum, kept for entries' views
    property real popupFullHeight: 0
    property real gridCellHeight: 0                         // Plasma's row height, kept for the labelled grid
    property bool gridStyled: false                         // the grid's cells set by the console
    Connections {
        target: tray.trayState
        ignoreUnknownSignals: true
        function onExpandedChanged() { if (tray.trayState.expanded) { tray.fitPasses = 0; tray.fitPopupLater(); } }
        function onActiveAppletChanged() { tray.fitPopupLater(); }
    }
    Connections {
        target: tray.popupGrid
        ignoreUnknownSignals: true
        function onCountChanged() { tray.fitPopupLater(); }
    }
    // After the popup's layout has settled: the grid's position needs it.
    // The first pass measures the heading with its former text and the
    // items without a size; it runs again until nothing changes (at most
    // three times per opening).
    Timer { id: fitTimer; interval: 80; onTriggered: tray.fitPopup() }
    function fitPopupLater() { fitTimer.restart(); }
    property int fitPasses: 0
    property real lastFitWidth: 0
    property real lastFitHeight: 0
    // The popup (the dialog's main item) above the grid: the one with the
    // entries' container.
    function popupOf(grid) {
        let item = grid;
        while (item && item.plasmoidContainer === undefined) item = item.parent;
        return item;
    }
    function fitPopup() {
        const grid = tray.popupGrid;
        const full = grid ? tray.popupOf(grid) : null;
        if (!full || !full.plasmoidContainer || !full.visible) return;
        const win = full.Window.window;
        if (!win || !win.visible) return;
        if (!tray.popupFullHeight) { tray.popupFullWidth = full.Layout.minimumWidth; tray.popupFullHeight = full.Layout.minimumHeight; }
        if (!tray.popupFullHeight) return;
        // The window's padding around the popup (the dialog's frame).
        const padW = Math.max(0, win.width - full.width), padH = Math.max(0, win.height - full.height);
        let w = tray.popupFullWidth, h = tray.popupFullHeight;
        const heading = tray.styleHeading(full);
        if (!full.plasmoidContainer.visible) {
            // Measured from what is laid out at once (implicit widths): on
            // the first opening the popup's items have no size yet, and a
            // scrollbar the view shows while the popup is still too small
            // would narrow the grid by a column.
            const fit = tray.styleGrid(grid, Math.round(tray.popupFullWidth * 5 / 6));
            const headW = heading ? Math.ceil(heading.implicitWidth + tray.root.u(12)) : 0;
            w = Math.max(fit.width, headW, tray.root.u(120));
            const rows = Math.max(1, Math.ceil(grid.count / fit.cols));
            const top = grid.mapToItem(full, 0, 0).y;
            h = Math.ceil(top + rows * grid.cellHeight + tray.root.u(8));
        }
        full.Layout.minimumWidth = w; full.Layout.minimumHeight = h;
        win.width = w + padW; win.height = h + padH;
        if ((w !== tray.lastFitWidth || h !== tray.lastFitHeight) && tray.fitPasses < 3) { tray.fitPasses++; tray.fitPopupLater(); }
        tray.lastFitWidth = w; tray.lastFitHeight = h;
    }
    // The popup's heading in the console's type: the title as on the
    // console's subpanels (its font, 12 units, semibold), its buttons
    // the height of a subpanel's title bar. Plasma's title, "Status and
    // Notifications", would hold the popup wider than its grid; over
    // the grid it reads "Status", an entry's view keeps the entry's
    // name. Returns the heading's row, for its width.
    function styleHeading(full) {
        for (const column of full.children) {
            if (column.spacing === undefined || !column.children.length) continue;
            const row = column.children[0];
            if (!row || row.spacing === undefined) continue;
            for (const item of row.children) {
                if (item.level !== undefined && item.text !== undefined) {
                    item.font.family = Kirigami.Theme.defaultFont.family;
                    item.font.pixelSize = tray.root.u(12); item.font.weight = Font.DemiBold;
                    item.text = Qt.binding(function() {
                        const state = tray.trayState;
                        return state && state.activeApplet ? state.activeApplet.plasmoid.title : i18nd("cde-copper", "Status");
                    });
                } else if (item.icon !== undefined && item.display !== undefined) {
                    item.implicitWidth = tray.root.u(26); item.implicitHeight = tray.root.u(26);
                    item.icon.width = tray.root.u(16); item.icon.height = tray.root.u(16);
                }
            }
            return row;
        }
        return null;
    }
    // Columns for a count of icons: around the square root, the one
    // leaving the fewest empty cells (13 icons: five columns, three rows).
    function bestColumns(count) {
        const base = Math.max(1, Math.ceil(Math.sqrt(count)));
        let best = base, empty = Infinity;
        for (let cols = base; cols <= base + 2; cols++) {
            const left = cols * Math.ceil(count / cols) - count;
            if (left < empty) { empty = left; best = cols; }
        }
        return Math.max(1, Math.min(count, best));
    }
    // The grid's cells; returns its columns and the width they take.
    // Plasma lays the entries out in two columns, icon and name side by
    // side, the icons at Kirigami's medium size, the names in the
    // system font. Here the entries take the console's measures: icons
    // as on a subpanel's entries (28 units), names in the console's
    // type, two columns across the width given. With "Icons only" the
    // icons shrink to 22 units in cells of 36, the grid takes the
    // columns bestColumns() gives and no more width than they need, and
    // every entry's name goes to its tooltip (Plasma shows one only
    // where it adds to the name). Switched off again, the cells and
    // names come back; a tooltip title Plasma had left empty stays empty
    // until the shell restarts.
    function styleGrid(grid, width) {
        const iconsOnly = Plasmoid.configuration.trayIconsOnly;
        if (!tray.gridCellHeight) tray.gridCellHeight = grid.cellHeight;
        const icon = tray.root.u(iconsOnly ? 22 : 28);
        let cols = 2, cell = 0;
        if (iconsOnly) {
            cell = Math.round(icon + 2 * 4 + tray.root.u(6));
            cols = tray.bestColumns(grid.count);
        }
        for (const loader of grid.contentItem.children) {
            const entry = loader.item;
            if (!entry || entry.iconContainer === undefined) continue;
            let label = null;
            for (const child of entry.children) {
                if (child.spacing !== undefined && child.children.length === 2) label = child.children[1];
            }
            if (!label) continue;
            entry.iconContainer.implicitWidth = icon; entry.iconContainer.implicitHeight = icon;
            label.font.family = Kirigami.Theme.defaultFont.family; label.font.pixelSize = tray.root.u(11);
            label.font.weight = Plasmoid.configuration.hardContrast ? Font.DemiBold : Font.Normal;
            if (iconsOnly) {
                cell = Math.max(cell, Math.round(icon + 2 * entry.margins + tray.root.u(6)));
                if (label.visible) {
                    label.visible = false;
                    entry.mainText = Qt.binding(function() { return entry.text; });
                    entry.active = true;
                }
            } else if (!label.visible) {
                label.visible = Qt.binding(function() { return entry.inHiddenLayout; });
                entry.mainText = "";
                entry.active = Qt.binding(function() { return entry.text != entry.mainText || entry.subText.length > 0; });
            }
        }
        if (iconsOnly) {
            grid.cellWidth = cell; grid.cellHeight = cell; tray.gridStyled = true;
            // A little over the cells: the view takes floor(width / cell) columns.
            return { cols: cols, width: cols * cell + 4 };
        }
        if (tray.gridStyled) {
            grid.cellWidth = Math.floor(width / cols); grid.cellHeight = tray.gridCellHeight; tray.gridStyled = false;
        }
        return { cols: cols, width: width };
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
