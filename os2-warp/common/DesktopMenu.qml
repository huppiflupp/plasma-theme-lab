pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtCore
import Qt.labs.folderlistmodel
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
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

    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground

    function open(anchor) {
        levels = []; current = [];
        visualParent = anchor;
        visible = true;
        Qt.callLater(() => { anchorX = Math.max(0, anchor.mapToGlobal(0, 0).x - menu.x); });
    }
    function close() { visible = false; levels = []; }
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
            rows.push({name: label(desktopItems.get(i, "fileName")), url: desktopItems.get(i, "fileUrl"),
                       isDir: desktopItems.get(i, "fileIsDir"),
                       icon: iconFor(desktopItems.get(i, "fileName"), desktopItems.get(i, "fileIsDir"))});
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

    mainItem: Item {
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
        kind: "frame"
        // Standing on a bottom panel, y follows the height: the cap must
        // not follow y back, or the box collapsed to a line.
        // Deeper levels move up to fit (their y is clamped), so only the
        // root box opening downwards is capped by where it starts.
        height: Math.min(list.contentHeight + 6, level === 0 && menu.location !== PlasmaCore.Types.BottomEdge ? frame.height - y : frame.height)
        MouseArea { anchors.fill: parent }   // a click on the frame stays in the menu
        ListView {
            id: list
            anchors.fill: parent; anchors.margins: 3
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
                r.push({name: menu.label(entries.get(i, "fileName")), url: entries.get(i, "fileUrl"),
                        isDir: entries.get(i, "fileIsDir"), icon: menu.iconFor(entries.get(i, "fileName"), entries.get(i, "fileIsDir"))});
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
