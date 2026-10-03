pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.iconthemes as KIconThemes
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.kicker as Kicker
import "launch.js" as Launch

// Which program each console tile starts, its label and icon, and the
// subpanel its arrow opens. Tiles left of the workspace switch and right
// of it are two lists; both can grow, shrink and be reordered.
KCM.SimpleKCM {
    id: page
    property string cfg_leftLaunchers
    property string cfg_rightLaunchers
    property var leftSlots: Launch.parse(cfg_leftLaunchers, Launch.LEFT)
    property var rightSlots: Launch.parse(cfg_rightLaunchers, Launch.RIGHT)

    function store(side, list) {
        if (side === "left") { leftSlots = list; cfg_leftLaunchers = JSON.stringify(list); }
        else { rightSlots = list; cfg_rightLaunchers = JSON.stringify(list); }
    }
    function edit(side, index, change) {
        const list = (side === "left" ? leftSlots : rightSlots).map(s => Object.assign({}, s));
        Object.assign(list[index], change);
        store(side, list);
    }
    function move(side, index, delta) {
        const list = (side === "left" ? leftSlots : rightSlots).slice();
        const target = index + delta;
        if (target < 0 || target >= list.length) return;
        const item = list.splice(index, 1)[0];
        list.splice(target, 0, item);
        store(side, list);
    }
    function removeAt(side, index) {
        const list = (side === "left" ? leftSlots : rightSlots).slice();
        list.splice(index, 1);
        store(side, list);
    }
    function add(side) {
        const list = (side === "left" ? leftSlots : rightSlots).slice();
        list.push({label: "Web", icon: "internet-web-browser", command: "@browser", menu: ""});
        store(side, list);
    }

    // Picking an installed application: its desktop id becomes the command,
    // its name the label, the Icon= of its desktop file the icon.
    property string pickSide: ""
    property int pickIndex: -1
    P5Support.DataSource {
        id: iconLookup
        engine: "executable"
        onNewData: function(source, data) {
            const icon = data.stdout.trim();
            if (icon && page.pickIndex >= 0) page.edit(page.pickSide, page.pickIndex, {icon: icon});
            disconnectSource(source);
        }
    }
    function lookupIcon(id) {
        const file = Launch.quote(id.replace(/\.desktop$/, "") + ".desktop");
        iconLookup.connectSource("for d in \"${XDG_DATA_HOME:-$HOME/.local/share}\" $(echo \"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}\" | tr : ' ') /var/lib/flatpak/exports/share; do "
            + "f=\"$d/applications/\"" + file + "; [ -f \"$f\" ] && sed -n 's/^Icon=//p' \"$f\" | head -n1 && break; done");
    }

    // Is the program behind each tile installed? command -> "ok"/"missing".
    property var availability: ({})
    property var probes: ({})
    P5Support.DataSource {
        id: prober
        engine: "executable"
        onNewData: function(source, data) {
            const command = page.probes[source];
            const result = Object.assign({}, page.availability);
            result[command] = data.stdout.trim() === "ok" ? "ok" : "missing";
            page.availability = result;
            disconnectSource(source);
        }
    }
    function probe(command) {
        const shell = Launch.check(command);
        const map = Object.assign({}, probes);
        map[shell] = command;
        probes = map;
        prober.connectSource(shell);
    }

    Kicker.AppsModel { id: installed; flat: true; sorted: true; autoPopulate: true }

    Dialog {
        id: picker
        title: i18nd("cde-copper", "Choose an application")
        modal: true
        anchors.centerIn: parent
        width: Math.min(page.width - 40, Kirigami.Units.gridUnit * 26)
        height: Math.min(page.height - 40, Kirigami.Units.gridUnit * 28)
        standardButtons: Dialog.Cancel
        onOpened: { search.text = ""; search.forceActiveFocus(); }
        ColumnLayout {
            anchors.fill: parent
            TextField { id: search; Layout.fillWidth: true; placeholderText: i18nd("cde-copper", "Search") }
            ListView {
                id: apps
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; model: installed
                ScrollBar.vertical: ScrollBar {}
                delegate: ItemDelegate {
                    required property var model
                    required property int index
                    width: apps.width - 12
                    visible: search.text === "" || (model.display || "").toLowerCase().indexOf(search.text.toLowerCase()) >= 0
                    height: visible ? implicitHeight : 0
                    text: model.display || ""
                    icon.source: model.decoration
                    onClicked: {
                        const id = String(model.favoriteId || "").replace(/^applications:/, "").replace(/\.desktop$/, "");
                        if (id) {
                            page.edit(page.pickSide, page.pickIndex, {command: "app:" + id, label: (model.display || id).split(" ")[0], menu: "recent"});
                            page.lookupIcon(id);
                        }
                        picker.close();
                    }
                }
            }
        }
    }

    KIconThemes.IconDialog {
        id: iconDialog
        onIconNameChanged: if (iconName && page.pickIndex >= 0) page.edit(page.pickSide, page.pickIndex, {icon: iconName})
    }

    component SlotEditor: RowLayout {
        id: editor
        required property var modelData
        required property int index
        property string side
        readonly property string preset: Launch.presetFor(modelData.command)
        readonly property string found: page.availability[modelData.command] || ""
        spacing: Kirigami.Units.smallSpacing
        Component.onCompleted: page.probe(modelData.command)
        onModelDataChanged: page.probe(modelData.command)
        Button {
            icon.name: editor.modelData.icon
            icon.width: Kirigami.Units.iconSizes.medium; icon.height: Kirigami.Units.iconSizes.medium
            ToolTip.text: i18nd("cde-copper", "Choose icon"); ToolTip.visible: hovered
            onClicked: { page.pickSide = editor.side; page.pickIndex = editor.index; iconDialog.open(); }
        }
        TextField {
            Layout.preferredWidth: Kirigami.Units.gridUnit * 6
            text: Launch.slotLabel(editor.modelData, text => i18nd("cde-copper", text))
            placeholderText: i18nd("cde-copper", "Label")
            onEditingFinished: if (text !== Launch.slotLabel(editor.modelData, value => i18nd("cde-copper", value))) page.edit(editor.side, editor.index, {label: text})
        }
        ComboBox {
            id: program
            Layout.preferredWidth: Kirigami.Units.gridUnit * 11
            model: Launch.PRESETS.map(p => Object.assign({}, p, {text: i18nd("cde-copper", p.text)}))
            textRole: "text"
            currentIndex: Math.max(0, Launch.PRESETS.findIndex(p => p.value === editor.preset))
            onActivated: index => {
                const p = Launch.PRESETS[index];
                if (p.value === "app:") { page.pickSide = editor.side; page.pickIndex = editor.index; picker.open(); }
                else if (p.value === "") page.edit(editor.side, editor.index, {command: editor.modelData.command.indexOf("@") === 0 ? "" : editor.modelData.command});
                else page.edit(editor.side, editor.index, {command: p.value, icon: p.icon, menu: Launch.menuFor(p.value)});
            }
        }
        TextField {
            Layout.fillWidth: true
            Layout.minimumWidth: Kirigami.Units.gridUnit * 8
            visible: editor.preset === "" || editor.preset === "app:"
            readOnly: editor.preset === "app:"
            text: editor.modelData.command
            placeholderText: i18nd("cde-copper", "Command, e.g. firefox --private-window")
            onEditingFinished: if (!readOnly && text !== editor.modelData.command) page.edit(editor.side, editor.index, {command: text})
        }
        Item { Layout.fillWidth: true; visible: !(editor.preset === "" || editor.preset === "app:") }
        ComboBox {
            Layout.preferredWidth: Kirigami.Units.gridUnit * 7
            model: Launch.MENUS.map(m => Object.assign({}, m, {text: i18nd("cde-copper", m.text)}))
            textRole: "text"
            currentIndex: Math.max(0, Launch.MENUS.findIndex(m => m.value === editor.modelData.menu))
            onActivated: index => page.edit(editor.side, editor.index, {menu: Launch.MENUS[index].value})
            ToolTip.text: i18nd("cde-copper", "Subpanel opened by the arrow above the tile"); ToolTip.visible: hovered
        }
        Kirigami.Icon {
            Layout.preferredWidth: Kirigami.Units.iconSizes.small; Layout.preferredHeight: width
            source: editor.found === "missing" ? "dialog-warning" : editor.found === "ok" ? "dialog-ok-apply" : ""
            HoverHandler { id: stateHover }
            ToolTip.visible: stateHover.hovered && editor.found !== ""
            ToolTip.text: editor.found === "missing" ? i18nd("cde-copper", "Not installed: this tile would only show a notification. Choose another program.") : i18nd("cde-copper", "Installed")
        }
        ToolButton { icon.name: "go-up"; enabled: editor.index > 0; onClicked: page.move(editor.side, editor.index, -1); ToolTip.text: i18nd("cde-copper", "Move left"); ToolTip.visible: hovered }
        ToolButton { icon.name: "go-down"; onClicked: page.move(editor.side, editor.index, 1); ToolTip.text: i18nd("cde-copper", "Move right"); ToolTip.visible: hovered }
        ToolButton { icon.name: "list-remove"; onClicked: page.removeAt(editor.side, editor.index); ToolTip.text: i18nd("cde-copper", "Remove"); ToolTip.visible: hovered }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Left of the workspace switch") }
        Repeater { model: page.leftSlots; delegate: SlotEditor { side: "left" } }
        Button { text: i18nd("cde-copper", "Add tile"); icon.name: "list-add"; onClicked: page.add("left") }
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Right of the workspace switch") }
        Repeater { model: page.rightSlots; delegate: SlotEditor { side: "right" } }
        Button { text: i18nd("cde-copper", "Add tile"); icon.name: "list-add"; onClicked: page.add("right") }
        Kirigami.Separator { Layout.fillWidth: true }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            opacity: 0.75
            text: i18nd("cde-copper", "\"Default …\" entries follow the applications chosen in System Settings › Default Applications. A custom command runs through the shell; app:<desktop id> starts an installed application.")
        }
        Button {
            text: i18nd("cde-copper", "Restore default tiles")
            icon.name: "edit-undo"
            onClicked: { page.cfg_leftLaunchers = ""; page.cfg_rightLaunchers = ""; page.leftSlots = Launch.parse("", Launch.LEFT); page.rightSlots = Launch.parse("", Launch.RIGHT); }
        }
    }
}
