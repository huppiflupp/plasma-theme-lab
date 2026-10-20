pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtCore
import Qt.labs.folderlistmodel
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

// The Warp Bar's desktop menu (DESIGN.md §4): the objects on the desktop,
// then home, the root file system and mounted media; every folder cascades
// into its contents, down as far as the folders go, as the WarpCenter's
// menu walks from "Drive C" into its directories.
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
    // Level 1 and deeper: {url, top}; level 0 is the desktop.
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
    // Hovering a folder opens it one level further; anything deeper closes.
    function hover(level, row, url, isDir, top) {
        const c = current.slice(0, level); c[level] = row; current = c;
        // The Repeater rebuilds every box when levels changes: leave it be
        // while the pointer moves within what is already open.
        const open = levels.length === level + 1 && String(levels[level].url) === String(url);
        if ((isDir && open) || (!isDir && levels.length === level)) return;
        const kept = levels.slice(0, level);
        levels = isDir ? kept.concat([{url: url, top: top}]) : kept;
    }
    // A click opens: a folder in the file manager, a file with its program
    // (kioclient also starts .desktop entries).
    function activate(url, isDir) {
        const path = localPath(url);
        close();
        if (isDir)
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
    // The desktop's objects, a separator, then the drives.
    readonly property var rootRows: {
        const rows = [];
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
            y: 0
            width: menu.columnWidth
            rows: menu.rootRows
            level: 0
        }
        // Level 1 and deeper: one box per open folder, beside the previous.
        Repeater {
            model: menu.levels
            FolderBox {
                required property var modelData
                required property int index
                level: index + 1
                url: modelData.url
                x: Math.min(rootBox.x + (index + 1) * (menu.columnWidth - 2), frame.width - width)
                rowTop: modelData.top
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
        height: Math.min(list.contentHeight + 6, frame.height - y)
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
                cascade: modelData.isDir === true
                highlighted: menu.current[box.level] === index
                onHovered: menu.hover(box.level, index, modelData.url, modelData.isDir, box.y + y - list.contentY)
                onActivated: menu.activate(modelData.url, modelData.isDir)
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

    // One row: icon, name, ▸ for a folder; highlighted in the selection
    // colour (Warp 4: blue with white text).
    component MenuEntry: Item {
        id: entry
        property bool separator: false
        property string text
        property string iconName
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
            visible: !entry.separator && entry.iconName !== ""
            x: 4; anchors.verticalCenter: parent.verticalCenter
            width: 16; height: 16
            source: entry.iconName
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
