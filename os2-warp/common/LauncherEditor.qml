pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.iconthemes as KIconThemes
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.kicker as Kicker
import "launch.js" as Launch

// Editing a list of launchers, after CDE Copper's tiles page
// (CDE/frontpanel/contents/ui/configLaunchers.qml, 1.0.0): one row per
// launcher with its icon, label and program (a token that follows the
// desktop's default program, an installed application, or a command),
// reordered with the arrows. With drawers (the LaunchPad) every launcher
// opens the list of its drawer below it, edited the same way.
//
// The list comes in as `entries` and goes out through `edited`; the page
// stores it in the plasmoid's configuration.
ColumnLayout {
    id: editor
    property var entries: []
    property bool drawers: false
    property string addLabel: i18nd("warp-legacy", "Add launcher")
    signal edited(var list)
    property var openDrawers: []
    spacing: Kirigami.Units.smallSpacing

    function copy() { return entries.map(s => Object.assign({}, s, {drawer: (s.drawer || []).map(d => Object.assign({}, d))})); }
    // path: [index] for a launcher, [index, sub] for an entry of its drawer.
    function listOf(list, path) { return path.length > 1 ? list[path[0]].drawer : list; }
    function change(path, values) {
        const list = copy();
        Object.assign(listOf(list, path)[path[path.length - 1]], values);
        edited(list);
    }
    function move(path, delta) {
        const list = copy(), items = listOf(list, path), i = path[path.length - 1];
        const target = Math.max(0, Math.min(items.length - 1, i + delta));
        if (target === i) return;
        items.splice(target, 0, items.splice(i, 1)[0]);
        edited(list);
    }
    function remove(path) {
        const list = copy();
        listOf(list, path).splice(path[path.length - 1], 1);
        edited(list);
    }
    function add(drawerOf) {
        const list = copy();
        const item = {label: "Web", icon: "internet-web-browser", command: "@browser", drawer: []};
        (drawerOf >= 0 ? list[drawerOf].drawer : list).push(item);
        edited(list);
    }
    function tr(text) { return i18nd("warp-legacy", text); }

    // Picking an installed application: its desktop id becomes the command,
    // its name the label, the Icon= of its desktop file the icon.
    property var pickPath: []
    P5Support.DataSource {
        id: iconLookup
        engine: "executable"
        onNewData: function(source, data) {
            const icon = data.stdout.trim();
            if (icon && editor.pickPath.length) editor.change(editor.pickPath, {icon: icon});
            disconnectSource(source);
        }
    }
    function lookupIcon(id) {
        const file = Launch.quote(id.replace(/\.desktop$/, "") + ".desktop");
        iconLookup.connectSource("for d in \"${XDG_DATA_HOME:-$HOME/.local/share}\" $(echo \"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}\" | tr : ' ') /var/lib/flatpak/exports/share; do "
            + "f=\"$d/applications/\"" + file + "; [ -f \"$f\" ] && sed -n 's/^Icon=//p' \"$f\" | head -n1 && break; done");
    }
    // Plasma 6.7's flat AppsModel at the menu root stays empty; the root
    // model's "All Applications" row lists every installed application
    // (found in CDE Copper).
    Kicker.RootModel {
        id: menuRoot
        flat: true; sorted: true; autoPopulate: true
        appNameFormat: 0
        showAllApps: true; showAllAppsCategorized: false
        showRecentApps: false; showRecentDocs: false; showPowerSession: false
        showSeparators: false; showFavoritesPlaceholder: false
    }
    Dialog {
        id: picker
        title: editor.tr("Choose an application")
        modal: true
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 24
        height: Kirigami.Units.gridUnit * 26
        standardButtons: Dialog.Cancel
        onOpened: { search.text = ""; search.forceActiveFocus(); }
        ColumnLayout {
            anchors.fill: parent
            TextField { id: search; Layout.fillWidth: true; placeholderText: editor.tr("Search") }
            ListView {
                id: apps
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                model: menuRoot.count > 0 ? menuRoot.modelForRow(0) : null
                ScrollBar.vertical: ScrollBar {}
                delegate: ItemDelegate {
                    required property var model
                    width: apps.width - 12
                    visible: search.text === "" || (model.display || "").toLowerCase().indexOf(search.text.toLowerCase()) >= 0
                    height: visible ? implicitHeight : 0
                    text: model.display || ""
                    icon.source: model.decoration
                    onClicked: {
                        const id = String(model.favoriteId || "").replace(/^applications:/, "").replace(/\.desktop$/, "");
                        if (id) {
                            editor.change(editor.pickPath, {command: "app:" + id, label: model.display || id});
                            editor.lookupIcon(id);
                        }
                        picker.close();
                    }
                }
            }
        }
    }
    KIconThemes.IconDialog {
        id: iconDialog
        onIconNameChanged: if (iconName && editor.pickPath.length) editor.change(editor.pickPath, {icon: iconName})
    }

    component EntryRow: RowLayout {
        id: row
        required property var item
        required property var path
        readonly property int last: path[path.length - 1]
        readonly property string preset: Launch.presetFor(item.command)
        // Kept in the editor: every edit rebuilds the rows.
        readonly property bool expanded: editor.openDrawers.indexOf(path[0]) >= 0
        spacing: Kirigami.Units.smallSpacing
        Layout.leftMargin: path.length > 1 ? Kirigami.Units.gridUnit * 2 : 0
        Button {
            icon.name: row.item.icon
            icon.width: Kirigami.Units.iconSizes.medium; icon.height: Kirigami.Units.iconSizes.medium
            ToolTip.text: editor.tr("Choose icon"); ToolTip.visible: hovered
            onClicked: { editor.pickPath = row.path; iconDialog.open(); }
        }
        TextField {
            Layout.preferredWidth: Kirigami.Units.gridUnit * 8
            text: editor.tr(row.item.label)
            placeholderText: editor.tr("Label")
            onEditingFinished: if (text !== editor.tr(row.item.label)) editor.change(row.path, {label: text})
        }
        ComboBox {
            // The wheel scrolls the page; it must not change a value in passing.
            wheelEnabled: false
            Layout.preferredWidth: Kirigami.Units.gridUnit * 11
            model: Launch.PRESETS.map(p => editor.tr(p.text))
            currentIndex: Math.max(0, Launch.PRESETS.findIndex(p => p.value === row.preset))
            onActivated: index => {
                const p = Launch.PRESETS[index];
                if (p.value === "app:") { editor.pickPath = row.path; picker.open(); }
                else if (p.value === "") editor.change(row.path, {command: row.item.command.indexOf("@") === 0 ? "" : row.item.command});
                else editor.change(row.path, {command: p.value, icon: p.icon});
            }
        }
        TextField {
            Layout.fillWidth: true
            Layout.minimumWidth: Kirigami.Units.gridUnit * 8
            visible: row.preset === "" || row.preset === "app:"
            readOnly: row.preset === "app:"
            text: row.item.command
            placeholderText: editor.tr("Command, e.g. firefox --private-window")
            onEditingFinished: if (!readOnly && text !== row.item.command) editor.change(row.path, {command: text})
        }
        Item { Layout.fillWidth: true; visible: !(row.preset === "" || row.preset === "app:") }
        ToolButton {
            visible: editor.drawers && row.path.length === 1
            icon.name: row.expanded ? "go-up" : "go-down"
            text: i18nd("warp-legacy", "Drawer (%1)", (row.item.drawer || []).length)
            display: AbstractButton.TextBesideIcon
            onClicked: editor.openDrawers = row.expanded ? editor.openDrawers.filter(i => i !== row.path[0]) : editor.openDrawers.concat([row.path[0]])
        }
        ToolButton { icon.name: "arrow-up"; enabled: row.last > 0; onClicked: editor.move(row.path, -1); ToolTip.text: editor.tr("Move up"); ToolTip.visible: hovered }
        ToolButton { icon.name: "arrow-down"; onClicked: editor.move(row.path, 1); ToolTip.text: editor.tr("Move down"); ToolTip.visible: hovered }
        ToolButton { icon.name: "list-remove"; onClicked: editor.remove(row.path); ToolTip.text: editor.tr("Remove"); ToolTip.visible: hovered }
    }

    Repeater {
        model: editor.entries
        ColumnLayout {
            id: block
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            EntryRow { id: top; item: block.modelData; path: [block.index]; Layout.fillWidth: true }
            Repeater {
                model: top.expanded ? (block.modelData.drawer || []) : []
                EntryRow {
                    required property var modelData
                    required property int index
                    item: modelData; path: [block.index, index]
                    Layout.fillWidth: true
                }
            }
            Button {
                visible: top.expanded
                Layout.leftMargin: Kirigami.Units.gridUnit * 2
                text: editor.tr("Add to drawer"); icon.name: "list-add"
                onClicked: editor.add(block.index)
            }
        }
    }
    Button { text: editor.addLabel; icon.name: "list-add"; onClicked: editor.add(-1) }
    Label {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        opacity: 0.75
        text: editor.tr("\"Default …\" entries follow the programs chosen in System Settings › Default Applications. A custom command runs through the shell.")
    }
}
