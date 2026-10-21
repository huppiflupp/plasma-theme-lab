pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtCore
import Qt.labs.folderlistmodel
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.kicker as Kicker
import "launch.js" as Launch

// The Warp menu (DESIGN.md §4), opened by the Warp Bar's desktop button and
// the taskbar's Start button: Programs, cascading through the application
// menu's categories (Plasma's own model, so it follows what is installed),
// System Settings, then the objects on the desktop, home, the root file
// system and mounted media; every folder cascades into its contents, down
// as far as the folders go, as the WarpCenter's menu walks from "Drive C"
// into its directories.
//
// All levels live in ONE dialog, side by side. A window per submenu was
// what CDE Copper tried first for its applications menu: under Wayland,
// opened from a panel, KWin put the second window at 0,0 and never moved
// it (CDE/frontpanel/contents/ui/AppMenu.qml). So the dialog is as large as
// the screen below the bar, transparent where no level is, and a click
// there closes the menu as a click beside any menu does.
//
// Typing finds programs (as CDE Copper's applications menu does, whose
// FindPopup.qml this follows: Plasma's application search, the one KRunner
// uses, through Kicker's RunnerModel with only "krunner_services"; written
// anew here, nothing of CDE/ is referenced). The field sits at the root
// box's edge nearest the panel and has the keyboard as soon as the menu
// opens, so Meta, "kon", Return starts Konsole: the best match is
// highlighted at once, Up/Down choose another, Escape closes.
PlasmaCore.Dialog {
    id: menu
    required property rect screenRect
    // Run a shell command (main.qml's runner).
    property var run: function(shell) {}
    readonly property int columnWidth: 240
    readonly property int rowHeight: 24
    // Level 1 and deeper: {url, top, row} for a folder, {path, top, row}
    // for a part of the application menu (the rows leading to it from
    // categories); level 0 is the root.
    property var levels: []
    property var current: []          // the highlighted row per level
    property real anchorX: 0
    // The search: what is typed, the match highlighted (best first), and
    // Return pressed before the matches arrived (they come asynchronously).
    property string query: ""
    property int hit: 0
    property bool launchPending: false
    readonly property bool fromBottom: menu.location === PlasmaCore.Types.BottomEdge
    readonly property var search: Kicker.RunnerModel {
        appletInterface: Plasmoid
        runners: ["krunner_services"]
        mergeResults: true
        query: menu.query
    }
    readonly property var matches: search.count > 0 ? search.modelForRow(0) : null
    // The matches in our order, as rows of the runner's model. Plasma's
    // relevance put Kontact before Konsole for "kon" (VM, 21.10.2026), so
    // the name decides first: the name itself, then names beginning with
    // what was typed, then a word of the name beginning with it, then the
    // rest (found by generic name or keywords) in the runner's order;
    // within a class the program started more often from here first, then
    // the shorter name, then the alphabet.
    // How often each program was started from the search: the last 300
    // starts, one name per line, in ~/.local/share/warp-legacy/launched
    // (QML may not read or write files, so a shell does).
    property var launches: ({})
    readonly property string historyFile: "\"${XDG_DATA_HOME:-$HOME/.local/share}/warp-legacy/launched\""
    readonly property var history: P5Support.DataSource {
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source);
            const counts = {};
            String(data.stdout || "").split("\n").forEach(n => { if (n) counts[n] = (counts[n] || 0) + 1; });
            menu.launches = counts;
        }
    }
    function readHistory() { history.connectSource("sh -c " + quote("cat " + historyFile + " 2>/dev/null")); }
    function remember(name) {
        const f = historyFile;
        history.connectSource("sh -c " + quote("mkdir -p \"$(dirname " + f + ")\" && printf '%s\\n' " + quote(name)
            + " >> " + f + " && tail -n 300 " + f + " > " + f + ".new && mv " + f + ".new " + f + "; cat " + f));
    }
    property int matchesGeneration: 0
    readonly property var matchesWatch: Connections {
        target: menu.matches
        function onModelReset() { menu.matchesGeneration++; }
        function onRowsInserted() { menu.matchesGeneration++; }
        function onRowsRemoved() { menu.matchesGeneration++; }
        function onCountChanged() { menu.matchesGeneration++; }
    }
    function matchName(row) { return String(matches.data(matches.index(row, 0), Qt.DisplayRole) || ""); }
    readonly property var order: {
        matchesGeneration;
        const m = matches, q = query.trim().toLowerCase();
        if (!m || !q) return [];
        const rows = [];
        for (let i = 0; i < m.count; i++) {
            const name = matchName(i), low = name.toLowerCase();
            const rank = low === q ? 0 : low.indexOf(q) === 0 ? 1
                       : low.split(/[\s\-–_.()]+/).some(w => w.indexOf(q) === 0) ? 2 : 3;
            rows.push({row: i, rank: rank, name: low, used: launches[name] || 0});
        }
        rows.sort((a, b) => a.rank - b.rank || b.used - a.used
                  || (a.rank < 3 ? a.name.length - b.name.length || a.name.localeCompare(b.name) : 0)
                  || a.row - b.row);
        return rows.map(r => r.row);
    }
    readonly property int matchCount: order.length
    // The text the matches shown belong to: the runner starts after a short
    // delay, so right after a key the list is still the previous text's.
    property string matchedQuery: ""
    onQueryChanged: {
        hit = 0;
        matchedQuery = "";
        if (query !== "" && levels.length) { levels = []; current = []; }
    }
    onOrderChanged: {
        hit = 0;
        if (launchPending) Qt.callLater(launchHit);
    }
    readonly property var searchWatch: Connections {
        target: menu.search
        function onQueryingChanged() {
            if (menu.search.querying) return;
            menu.matchedQuery = menu.query;
            if (menu.launchPending) Qt.callLater(menu.launchHit);
        }
    }
    // Should the runner never report (nothing to do for this text), Return
    // still starts what is there after a moment.
    readonly property var pendingTimer: Timer {
        interval: 1500
        running: menu.launchPending
        onTriggered: { menu.matchedQuery = menu.query; menu.launchHit(); }
    }
    // Start the highlighted match (Return); the best when nothing else is.
    // Return before the matches for the whole text arrived waits for them.
    function launchHit() {
        if (query === "") return;
        if (search.querying || matchedQuery !== query) { launchPending = true; return; }
        if (matchCount === 0) { launchPending = false; return; }
        launchPending = false;
        remember(matchName(order[Math.max(0, Math.min(hit, matchCount - 1))]));
        matches.trigger(order[Math.max(0, Math.min(hit, matchCount - 1))], "", null);
        close();
    }

    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground

    function open(anchor) {
        levels = []; current = [];
        query = ""; hit = 0; launchPending = false; finder.text = "";
        readHistory();
        visualParent = anchor;
        visible = true;
        Qt.callLater(() => {
            anchorX = Math.max(0, anchor.mapToGlobal(0, 0).x - menu.x);
            finder.forceActiveFocus();
        });
    }
    function close() { visible = false; levels = []; query = ""; launchPending = false; }
    onVisibleChanged: if (visible) finder.forceActiveFocus()
    function localPath(url) {
        const s = String(url);
        return s.indexOf("file://") === 0 ? decodeURIComponent(s.substring(7)) : s;
    }
    function quote(s) { return "'" + String(s).replace(/\x27/g, "'\\''") + "'"; }
    // Hovering a folder or a category opens it one level further (next():
    // {url} or {path}); anything else (next null) closes what lies deeper.
    function hover(level, row, next, top) {
        const c = current.slice(0, level); c[level] = row; current = c;
        // The Repeater rebuilds every box when levels changes, and the row
        // under the pointer reports a hover again: what this row opened
        // stays as it is, matched by row.
        const here = levels.length > level ? levels[level] : null;
        if (next && here && here.row === row) {
            if (levels.length > level + 1) levels = levels.slice(0, level + 1);
            return;
        }
        if (!next && levels.length === level) return;
        const kept = levels.slice(0, level);
        levels = next ? kept.concat([Object.assign({top: top, row: row}, next())]) : kept;
    }
    // A click opens: a folder in the file manager, a file with its program
    // (kioclient also starts .desktop entries), a command as a launcher does.
    function activate(row) {
        if (row.command) { close(); run(Launch.resolve(row.command, (text, ...args) => i18nd("warp-legacy", text, ...args))); return; }
        if (!row.url || row.apps) return;
        const path = localPath(row.url);
        close();
        if (row.isDir)
            run("xdg-open " + quote(path));
        else
            run("kioclient exec " + quote(path) + " 2>/dev/null || xdg-open " + quote(path));
    }
    function iconFor(name, isDir) {
        if (isDir) return "folder";
        const ext = name.indexOf(".") >= 0 ? name.split(".").pop().toLowerCase() : "";
        if (ext === "desktop") return "application-x-executable";
        if (["png", "jpg", "jpeg", "gif", "svg", "webp"].indexOf(ext) >= 0) return "image-x-generic";
        if (["mp4", "mkv", "webm", "avi", "mov"].indexOf(ext) >= 0) return "video-x-generic";
        if (["mp3", "ogg", "flac", "wav", "opus"].indexOf(ext) >= 0) return "audio-x-generic";
        if (ext === "pdf") return "application-pdf";
        if (["zip", "tar", "gz", "xz", "zst", "7z"].indexOf(ext) >= 0) return "application-x-archive";
        if (["txt", "md", "conf", "ini", "log", "sys", "bat"].indexOf(ext) >= 0) return "text-plain";
        return "unknown";
    }
    function label(name) { return String(name).replace(/\.desktop$/, ""); }
    // A .desktop entry shows its Name= and Icon= (in the user's language),
    // not its file name: "01-arbeitsplatz" with a generic icon before.
    // Read per folder with one shell call and kept; QML may not read files.
    property var entryInfo: ({})          // path -> {name, icon}
    property var asked: ({})              // folder path -> true
    readonly property var reader: P5Support.DataSource {
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source);
            const info = Object.assign({}, menu.entryInfo);
            String(data.stdout || "").split("\n").forEach(line => {
                const f = line.split("\t");
                if (f.length === 3) info[f[0]] = {name: f[1], icon: f[2]};
            });
            menu.entryInfo = info;
        }
    }
    function readEntries(folderUrl) {
        const dir = localPath(folderUrl).replace(/\/$/, "");
        if (!dir || asked[dir]) return;
        const a = Object.assign({}, asked); a[dir] = true; asked = a;
        const lang = Qt.locale().name;                 // de_DE
        const short = lang.split("_")[0];
        const field = k => "sed -n " + quote("/^\\[Desktop Entry\\]/,/^\\[/{s/^" + k + "=//p}") + " \"$f\" | head -n1";
        reader.connectSource("sh -c " + quote("for f in " + quote(dir) + "/*.desktop; do [ -f \"$f\" ] || continue; "
            + "n=$(" + field("Name\\[" + lang + "\\]") + "); [ -n \"$n\" ] || n=$(" + field("Name\\[" + short + "\\]") + "); "
            + "[ -n \"$n\" ] || n=$(" + field("Name") + "); i=$(" + field("Icon") + "); "
            + "printf '%s\\t%s\\t%s\\n' \"$f\" \"$n\" \"$i\"; done"));
    }
    // Name and icon of a row: from the entry when it is a .desktop file.
    function rowFor(fileName, fileUrl, isDir, folderUrl) {
        const path = localPath(fileUrl);
        const desktop = !isDir && /\.desktop$/.test(fileName);
        // Later, not inside the binding that builds the rows: reading
        // marks the folder as asked, which re-ran that binding (a loop).
        if (desktop) Qt.callLater(readEntries, folderUrl);
        const info = desktop ? entryInfo[path] : null;
        return {name: info && info.name ? info.name : label(fileName), url: fileUrl, isDir: isDir,
                icon: info && info.icon ? info.icon : iconFor(fileName, isDir)};
    }

    readonly property url desktopUrl: StandardPaths.writableLocation(StandardPaths.DesktopLocation)
    readonly property url homeUrl: StandardPaths.writableLocation(StandardPaths.HomeLocation)
    readonly property string user: localPath(homeUrl).split("/").pop()
    // A Dialog's default property is its main item: the models are held
    // as properties.
    readonly property FolderListModel desktopItems: FolderListModel { folder: menu.desktopUrl; showDirsFirst: true; showHidden: false }
    readonly property FolderListModel media: FolderListModel { folder: "file:///run/media/" + menu.user; showFiles: false }
    // The application menu's categories (as the Tab Launcher's tabs).
    // appletInterface as the Tab Launcher has it: without, the model stayed
    // empty and Programs opened nothing (VM, 20.10.2026).
    readonly property var categories: Kicker.AppsModel { flat: false; sorted: true; autoPopulate: true; showSeparators: false; appletInterface: Plasmoid }
    // A part of the application menu is looked up by its path of rows, never
    // kept: every refresh of categories (each change to the application
    // database) deletes all its submodels. A kept submodel went dead under
    // the open menu, its box shrank to a line and every click fell through
    // and closed the menu (VM, 20.10.2026: two programs with different
    // menu settings rebuilt the database every second).
    property int appsGeneration: 0
    readonly property var appsWatch: Connections {
        target: menu.categories
        function onModelReset() { menu.appsGeneration++; }
    }
    function appsAt(path) {
        let m = categories;
        for (let i = 0; m && i < path.length; i++) m = m.modelForRow(path[i]);
        return m;
    }
    // Programs and System Settings, the desktop's objects, then the drives.
    readonly property var rootRows: {
        const rows = [
            {name: i18nd("warp-legacy", "Programs"), apps: categories, icon: "applications-other"},
            {name: i18nd("warp-legacy", "System Settings"), command: "@settings", icon: "preferences-system"},
            {separator: true}
        ];
        for (let i = 0; i < desktopItems.count; i++)
            rows.push(rowFor(desktopItems.get(i, "fileName"), desktopItems.get(i, "fileUrl"),
                             desktopItems.get(i, "fileIsDir"), desktopUrl));
        rows.push({separator: true});
        rows.push({name: i18nd("warp-legacy", "Home"), url: homeUrl, isDir: true, icon: "user-home"});
        rows.push({name: i18nd("warp-legacy", "Root file system"), url: "file:///", isDir: true, icon: "drive-harddisk"});
        // A folder that does not exist makes FolderListModel list another
        // one (the home folder, in the VM without /run/media/<user>): only
        // entries really below /run/media count.
        for (let j = 0; j < media.count; j++)
            if (String(media.get(j, "filePath")).indexOf("/run/media/") === 0)
                rows.push({name: media.get(j, "fileName"), url: media.get(j, "fileUrl"), isDir: true, icon: "drive-removable-media"});
        return rows;
    }

    mainItem: FocusScope {
        id: frame
        width: menu.screenRect.width
        height: menu.screenRect.height - 40
        focus: true
        Keys.onEscapePressed: menu.close()
        // Beside the menus: close, as a click beside any menu does.
        MouseArea { anchors.fill: parent; onPressed: menu.close() }

        // Level 0: the desktop and the drives.
        MenuBox {
            id: rootBox
            x: Math.min(menu.anchorX, frame.width - width)
            // Opened from a panel along the bottom (the taskbar), the menu
            // stands on the panel and grows upwards.
            y: menu.location === PlasmaCore.Types.BottomEdge ? frame.height - height : 0
            width: menu.columnWidth
            rows: menu.rootRows
            level: 0
            readonly property bool searching: menu.query !== ""
            readonly property real fieldSpace: finder.height + 3
            rowsHidden: searching
            headTop: menu.fromBottom ? 0 : fieldSpace
            headBottom: menu.fromBottom ? fieldSpace : 0
            bodyHeight: searching ? Math.max(menu.rowHeight, Math.min(results.contentHeight, 14 * menu.rowHeight)) : rowsHeight

            // The search field: sunken, as OS/2's entry fields.
            Bevel {
                id: finderBox
                kind: "field"
                // An entry field's colours (the View set): white in Warp 4.
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                x: 3; width: parent.width - 6; height: finder.height
                y: menu.fromBottom ? parent.height - height - 3 : 3
                Kirigami.Icon {
                    x: 5; anchors.verticalCenter: parent.verticalCenter
                    width: 16; height: 16
                    source: "system-search"
                }
                TextInput {
                    id: finder
                    x: 26; width: parent.width - x - 6
                    height: menu.rowHeight + 2
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true
                    focus: true
                    font: Kirigami.Theme.defaultFont
                    color: Kirigami.Theme.textColor
                    selectionColor: Kirigami.Theme.highlightColor
                    selectedTextColor: Kirigami.Theme.highlightedTextColor
                    text: menu.query
                    onTextEdited: menu.query = text
                    Keys.onEscapePressed: menu.close()
                    Keys.onReturnPressed: menu.launchHit()
                    Keys.onEnterPressed: menu.launchHit()
                    Keys.onUpPressed: if (menu.matchCount > 0) menu.hit = Math.max(0, menu.hit - 1)
                    Keys.onDownPressed: if (menu.matchCount > 0) menu.hit = Math.min(menu.matchCount - 1, menu.hit + 1)
                    Text {
                        visible: finder.text === ""
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        text: i18nd("warp-legacy", "Type to find a program")
                        font: Kirigami.Theme.defaultFont
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
            // The matches, best first; the highlighted one starts on Return.
            ListView {
                id: results
                visible: rootBox.searching
                x: 3; width: parent.width - 6
                y: menu.fromBottom ? 3 : rootBox.fieldSpace + 3
                height: parent.height - rootBox.fieldSpace - 6
                clip: true
                model: menu.order
                currentIndex: menu.hit
                onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)
                interactive: contentHeight > height
                delegate: MenuEntry {
                    required property var modelData
                    required property int index
                    width: results.width
                    text: { menu.matchesGeneration; return menu.matchName(modelData); }
                    iconSource: { menu.matchesGeneration; return menu.matches ? menu.matches.data(menu.matches.index(modelData, 0), Qt.DecorationRole) : null; }
                    highlighted: menu.hit === index
                    onHovered: menu.hit = index
                    onActivated: { menu.hit = index; menu.launchHit(); }
                }
            }
            Text {
                visible: rootBox.searching && menu.matchCount === 0 && !menu.search.querying
                x: 30; y: results.y
                height: menu.rowHeight
                verticalAlignment: Text.AlignVCenter
                text: i18nd("warp-legacy", "No programs found")
                font: Kirigami.Theme.defaultFont
                color: Kirigami.Theme.disabledTextColor
            }
        }
        // Level 1 and deeper: one box per open folder or category, beside
        // the previous.
        Repeater {
            model: menu.levels
            Loader {
                id: level
                required property var modelData
                required property int index
                x: Math.min(rootBox.x + (index + 1) * (menu.columnWidth - 2), frame.width - menu.columnWidth)
                sourceComponent: modelData.path ? appsLevel : folderLevel
                Component {
                    id: folderLevel
                    FolderBox { level: level.index + 1; url: level.modelData.url; rowTop: level.modelData.top }
                }
                Component {
                    id: appsLevel
                    AppsBox { level: level.index + 1; path: level.modelData.path; rowTop: level.modelData.top }
                }
            }
        }
    }

    // A level's box of rows, from a list of {name, url, isDir, icon} or
    // {separator}.
    component MenuBox: Bevel {
        id: box
        property var rows: []
        property int level: 0
        // Room above or below the rows (the root box's search field), the
        // height of what the box shows, and the rows hidden (searching).
        property real headTop: 0
        property real headBottom: 0
        property bool rowsHidden: false
        readonly property real rowsHeight: list.contentHeight
        property real bodyHeight: rowsHeight
        kind: "frame"
        // Standing on a bottom panel, y follows the height: the cap must
        // not follow y back, or the box collapsed to a line.
        // Deeper levels move up to fit (their y is clamped), so only the
        // root box opening downwards is capped by where it starts.
        height: Math.min(bodyHeight + headTop + headBottom + 6, level === 0 && menu.location !== PlasmaCore.Types.BottomEdge ? frame.height - y : frame.height)
        MouseArea { anchors.fill: parent }   // a click on the frame stays in the menu
        ListView {
            id: list
            visible: !box.rowsHidden
            anchors.fill: parent; anchors.margins: 3
            anchors.topMargin: 3 + box.headTop; anchors.bottomMargin: 3 + box.headBottom
            clip: true
            model: box.rows
            interactive: contentHeight > height
            ScrollBar.vertical: ScrollBar { policy: list.interactive ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
            delegate: MenuEntry {
                required property var modelData
                required property int index
                width: list.width - (list.interactive ? 14 : 0)
                separator: modelData.separator === true
                text: modelData.name || ""
                iconName: modelData.icon || ""
                cascade: modelData.isDir === true || modelData.apps !== undefined
                highlighted: menu.current[box.level] === index
                onHovered: menu.hover(box.level, index,
                                      modelData.apps ? () => ({path: []}) : modelData.isDir ? () => ({url: modelData.url}) : null,
                                      box.y + y - list.contentY)
                onActivated: menu.activate(modelData)
            }
        }
    }

    // A folder's level: its contents, folders first.
    component FolderBox: MenuBox {
        id: folderBox
        property url url
        property real rowTop: 0
        y: Math.max(0, Math.min(rowTop, frame.height - height))
        width: menu.columnWidth
        FolderListModel { id: entries; folder: folderBox.url; showDirsFirst: true; showHidden: false; sortCaseSensitive: false }
        rows: {
            const r = [];
            for (let i = 0; i < entries.count; i++)
                r.push(menu.rowFor(entries.get(i, "fileName"), entries.get(i, "fileUrl"),
                                   entries.get(i, "fileIsDir"), folderBox.url));
            if (!r.length && entries.status === FolderListModel.Ready)
                r.push({name: i18nd("warp-legacy", "(empty)"), url: "", isDir: false, icon: ""});
            return r;
        }
    }

    // A part of the application menu: categories cascade, programs start.
    component AppsBox: Bevel {
        id: appsBox
        property var path: []
        readonly property var appsModel: { menu.appsGeneration; return menu.appsAt(path); }
        property int level: 1
        property real rowTop: 0
        kind: "frame"
        y: Math.max(0, Math.min(rowTop, frame.height - height))
        width: menu.columnWidth
        height: Math.min(appsList.contentHeight + 6, frame.height)
        MouseArea { anchors.fill: parent }
        ListView {
            id: appsList
            anchors.fill: parent; anchors.margins: 3
            clip: true
            model: appsBox.appsModel
            interactive: contentHeight > height
            ScrollBar.vertical: ScrollBar { policy: appsList.interactive ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
            delegate: MenuEntry {
                required property var model
                required property int index
                width: appsList.width - (appsList.interactive ? 14 : 0)
                text: model.display || ""
                iconSource: model.decoration
                cascade: model.hasChildren === true
                highlighted: menu.current[appsBox.level] === index
                onHovered: menu.hover(appsBox.level, index,
                                      model.hasChildren ? () => ({path: appsBox.path.concat([index])}) : null,
                                      appsBox.y + y - appsList.contentY)
                onActivated: if (!model.hasChildren) { appsBox.appsModel.trigger(index, "", null); menu.close(); }
            }
        }
    }

    // One row: icon, name, ▸ for a folder; highlighted in the selection
    // colour (Warp 4: blue with white text).
    component MenuEntry: Item {
        id: entry
        property bool separator: false
        property string text
        property string iconName
        property var iconSource: null     // a QIcon from the application menu
        property bool cascade: false
        property bool highlighted: false
        signal hovered()
        signal activated()
        height: separator ? 8 : menu.rowHeight
        Rectangle {
            visible: entry.separator
            y: 3; width: parent.width; height: 1; color: Kirigami.Theme.disabledTextColor
        }
        Rectangle {
            visible: !entry.separator
            anchors.fill: parent
            color: entry.highlighted ? Kirigami.Theme.highlightColor : "transparent"
        }
        Kirigami.Icon {
            visible: !entry.separator && (entry.iconName !== "" || entry.iconSource !== null)
            x: 4; anchors.verticalCenter: parent.verticalCenter
            width: 16; height: 16
            source: entry.iconSource !== null ? entry.iconSource : entry.iconName
        }
        Text {
            visible: !entry.separator
            x: 26; width: parent.width - x - 16
            anchors.verticalCenter: parent.verticalCenter
            text: entry.text
            elide: Text.ElideRight
            font: Kirigami.Theme.defaultFont
            color: entry.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
        }
        Text {
            visible: entry.cascade
            anchors.right: parent.right; anchors.rightMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            text: "▸"
            color: entry.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
        }
        MouseArea {
            anchors.fill: parent
            enabled: !entry.separator && entry.text !== ""
            hoverEnabled: true
            onEntered: entry.hovered()
            onClicked: entry.activated()
        }
    }
}
