pragma ComponentBehavior: Bound
import QtQuick
import org.kde.plasma.plasma5support as P5Support
import "launch.js" as Launch
import "motif.js" as Motif

// Drop site on a launcher tile, laid over it (anchors.fill: parent), as
// CDE's Front Panel controls took dropped files:
//   files                   go to the tile's program (Launch.dropCommand):
//                           the editor opens them, the file manager their
//                           folder, the terminal starts there, the trash
//                           takes them
//   an application          (a desktop file from the menu or a file
//                           manager) becomes the tile's program
//   another tile            moves here; the tile is the drag source after
//                           a press-and-hold (draggable)
// While something it takes is over it, the tile shows Motif's drag-under
// feedback: sunken, framed in the selection colour.
DropArea {
    id: site
    // The tile's launcher slot and its place in the console.
    property var launcherSlot: ({})
    property string side: ""
    property int index: -1
    // Tiles can be dragged onto other tiles to reorder them, after a
    // press-and-hold on the tile (a click keeps launching).
    property bool draggable: false
    // The Applications tile (Meta key) keeps its program.
    property bool replaceable: site.launcherSlot.command !== "@applications"
    property color surface: consoleColors.panel
    property color accent: consoleColors.highlight
    property var translate: (text, arg) => arg === undefined ? i18nd("cde-copper", text) : i18nd("cde-copper", text, arg)

    // A shell command for the console to run (root.run, detached).
    signal runRequested(string command)
    // An application dropped: the slot to put in this tile's place.
    signal replaceLauncher(string desktopId, var newSlot)
    // A tile dropped here: from its place to this one.
    signal moveLauncher(string fromSide, int fromIndex, string toSide, int toIndex)

    // What the drag over the tile would do: "files", "application",
    // "tile" or "" (refused).
    property string kind: ""
    readonly property bool hot: containsDrag && kind !== ""

    function classify(drag) {
        if (drag.formats.indexOf(Launch.TILE_MIME) >= 0) {
            const from = Launch.parseTileRef(drag.getDataAsString(Launch.TILE_MIME));
            return from && !(from.side === site.side && from.index === site.index) && site.side !== "" ? "tile" : "";
        }
        if (!drag.hasUrls || drag.urls.length === 0) return "";
        if (drag.urls.length === 1 && Launch.desktopId(drag.urls[0]) !== "")
            return site.replaceable && site.index >= 0 ? "application" : "";
        return Launch.fileAction(site.launcherSlot.command || "") !== "" ? "files" : "";
    }
    onEntered: function(drag) {
        site.kind = site.classify(drag);
        drag.accepted = site.kind !== "";
        if (site.kind === "tile") drag.accept(Qt.MoveAction);
        else if (site.kind !== "") drag.accept(Qt.CopyAction);
    }
    onExited: site.kind = ""
    onDropped: function(drop) {
        const what = site.classify(drop);
        site.kind = "";
        if (what === "tile") {
            const from = Launch.parseTileRef(drop.getDataAsString(Launch.TILE_MIME));
            drop.accept(Qt.MoveAction);
            site.moveLauncher(from.side, from.index, site.side, site.index);
        } else if (what === "application") {
            drop.accept(Qt.CopyAction);
            site.lookup(Launch.desktopId(drop.urls[0]));
        } else if (what === "files") {
            const shell = Launch.dropCommand(site.launcherSlot.command, drop.urls.map(String), site.translate);
            drop.accept(Qt.CopyAction);
            if (shell) site.runRequested(shell);
        }
    }

    // Name and icon of a dropped application from its desktop entry.
    property string pendingId: ""
    function lookup(id) {
        site.pendingId = id;
        entryReader.connectSource(Launch.desktopEntryQuery(id));
    }
    P5Support.DataSource {
        id: entryReader
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source);
            if (site.pendingId === "") return;
            site.replaceLauncher(site.pendingId, Launch.desktopSlot(site.pendingId, data.stdout, Qt.locale().name, site.launcherSlot));
            site.pendingId = "";
        }
    }

    // Drag-under feedback: the tile pressed in, a frame in the selection
    // colour inside its bevel.
    Item {
        anchors.fill: parent
        visible: site.hot
        readonly property var shade: Motif.shades(site.surface)
        Rectangle { x: 1; y: 1; width: parent.width - 2; height: 1; color: parent.shade.bottom }
        Rectangle { x: 1; y: 1; width: 1; height: parent.height - 2; color: parent.shade.bottom }
        Rectangle { x: 2; y: parent.height - 2; width: parent.width - 3; height: 1; color: parent.shade.top }
        Rectangle { x: parent.width - 2; y: 2; width: 1; height: parent.height - 3; color: parent.shade.top }
        Rectangle {
            anchors.fill: parent; anchors.margins: 3
            color: Qt.rgba(site.accent.r, site.accent.g, site.accent.b, 0.18)
            border.color: site.accent; border.width: 2
        }
    }

    // The tile as drag source: holding its button pressed (Qt's
    // press-and-hold interval, 0.8 s) starts a system drag carrying its
    // place, with a picture of the tile under the pointer. A plain click,
    // even one that moves a little, still launches: the button skips its
    // click only after a hold. A DragHandler in here took every press
    // from the button, so nothing launched (09.10.2026); hence the hold.
    Connections {
        target: site.draggable ? site.parent : null
        ignoreUnknownSignals: true
        function onPressAndHold() { site.startDrag(); }
    }
    function startDrag() {
        const tile = site.parent || site;
        const hx = tile.pressX !== undefined ? tile.pressX : tile.width / 2;
        const hy = tile.pressY !== undefined ? tile.pressY : tile.height / 2;
        tile.grabToImage(result => {
            payload.Drag.imageSource = result.url;
            payload.Drag.hotSpot.x = hx;
            payload.Drag.hotSpot.y = hy;
            payload.Drag.active = true;
        });
    }
    Item {
        id: payload
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: ({[Launch.TILE_MIME]: Launch.tileRef(site.side, site.index)})
        Drag.onDragFinished: Drag.active = false
    }
}
