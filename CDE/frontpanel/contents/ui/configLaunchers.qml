pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.iconthemes as KIconThemes
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.kicker as Kicker
import "launch.js" as Launch

// Everything the console holds, in its order on the screen: which program
// each tile starts, its label and icon, and the subpanel its arrow opens
// (tiles left of the workspace switch and right of it are two lists; both
// can grow, shrink and be reordered), then the block of small buttons.
ConfigPage {
    id: page
    // The small buttons' block (the session block) and the cluster tile:
    // the rest of what the console holds, in its order on the screen.
    property var cfg_smallButtons: []
    property string cfg_smallStyle: "family"
    property string cfg_batteryMeter: "auto"
    property alias cfg_llmHosts: llmHosts.text
    property bool cfg_hideTrayIcons: true
    property alias cfg_hideTrayVolume: hideVolume.checked
    property alias cfg_trayIconsOnly: trayIconsOnly.checked
    readonly property var smallStyles: [
        {value: "family", short: i18nd("cde-copper", "All alike"), text: i18nd("cde-copper", "All alike, the meters among the keys")},
        {value: "instruments", short: i18nd("cde-copper", "Sunken meters"), text: i18nd("cde-copper", "Meters sunken, in the clock's colours")},
        {value: "led", short: i18nd("cde-copper", "LED field"), text: i18nd("cde-copper", "Meters as an LED field over the keys")},
        {value: "panel", short: i18nd("cde-copper", "Bar panel"), text: i18nd("cde-copper", "Meters as a panel of bars beside the keys")}]
    readonly property var smallChoices: [
        {kind: "configure", text: i18nd("cde-copper", "Console settings")},
        {kind: "lock", text: i18nd("cde-copper", "Lock screen")},
        {kind: "desktop", text: i18nd("cde-copper", "Show desktop")},
        {kind: "load", text: i18nd("cde-copper", "Load meter"), tip: i18nd("cde-copper", "Processor and memory")},
        {kind: "llm", text: i18nd("cde-copper", "LLM cluster"), tip: i18nd("cde-copper", "Tokens per second of llama.cpp servers")},
        {kind: "volume", text: i18nd("cde-copper", "Volume"), tip: i18nd("cde-copper", "Without it the volume sits in the strip's row")},
        {kind: "network", text: i18nd("cde-copper", "Network"), tip: i18nd("cde-copper", "WLAN or cable")},
        {kind: "logout", text: i18nd("cde-copper", "Leave session")}]
    function setSmall(kind, on) {
        const chosen = smallChoices.map(c => c.kind)
            .filter(k => k === kind ? on : (cfg_smallButtons || []).indexOf(k) >= 0);
        cfg_smallButtons = chosen.length ? chosen : ["configure"];
    }
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
        const target = Math.max(0, Math.min(list.length - 1, index + delta));
        if (target === index) return;
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

    // Plasma 6.7's flat AppsModel at the menu root stays empty; the root
    // model's "All Applications" row (the first, as nothing else is shown)
    // lists every installed application.
    Kicker.RootModel {
        id: menuRoot
        flat: true; sorted: true; autoPopulate: true
        appNameFormat: 0
        showAllApps: true; showAllAppsCategorized: false
        showRecentApps: false; showRecentDocs: false; showPowerSession: false
        showSeparators: false; showFavoritesPlaceholder: false
    }
    readonly property var installed: menuRoot.count > 0 ? menuRoot.modelForRow(0) : null

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
                clip: true; model: page.installed
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
                            // A mail tile keeps its mail subpanel with the chosen client.
                            const slot = (page.pickSide === "left" ? page.leftSlots : page.rightSlots)[page.pickIndex] || {};
                            page.edit(page.pickSide, page.pickIndex, {command: "app:" + id, label: (model.display || id).split(" ")[0], menu: slot.menu === "mail" ? "mail" : "recent"});
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
        // Dragged by its grip the row follows the pointer; let go, it takes
        // the place it was dropped on. The arrows stay for the keyboard.
        property real shift: 0
        transform: Translate { y: editor.shift }
        z: grip.pressed ? 10 : 0
        opacity: grip.pressed ? 0.8 : 1
        Kirigami.Icon {
            source: "handle-sort"
            isMask: true
            color: Kirigami.Theme.textColor
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium; Layout.preferredHeight: width
            MouseArea {
                id: grip
                anchors.fill: parent
                cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                preventStealing: true
                hoverEnabled: true
                property real startY
                onPressed: mouse => startY = mapToItem(editor.parent, 0, mouse.y).y
                onPositionChanged: mouse => { if (pressed) editor.shift = mapToItem(editor.parent, 0, mouse.y).y - startY; }
                onReleased: {
                    const delta = Math.round(editor.shift / (editor.height + Kirigami.Units.largeSpacing));
                    editor.shift = 0;
                    if (delta !== 0) page.move(editor.side, editor.index, delta);
                }
                onCanceled: editor.shift = 0
                ToolTip.text: i18nd("cde-copper", "Drag to reorder"); ToolTip.visible: containsMouse && !pressed
            }
        }
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
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: i18nd("cde-copper", "Small buttons at the end") }
        GridLayout {
            columns: 2
            columnSpacing: Kirigami.Units.gridUnit * 2
            Repeater {
                model: page.smallChoices
                delegate: CheckBox {
                    required property var modelData
                    text: modelData.text
                    checked: (page.cfg_smallButtons || []).indexOf(modelData.kind) >= 0
                    onToggled: page.setSmall(modelData.kind, checked)
                    ToolTip.text: modelData.tip || ""
                    ToolTip.visible: hovered && ToolTip.text !== ""
                }
            }
        }
        Kirigami.FormLayout {
            Layout.fillWidth: true
            // The battery joins the load meter as a third reading.
            ComboBox {
                id: batteryMeter
                Kirigami.FormData.label: i18nd("cde-copper", "Battery:")
                enabled: (page.cfg_smallButtons || []).indexOf("load") >= 0
                readonly property var values: ["auto", "always", "never"]
                model: [i18nd("cde-copper", "In the load meter while on battery"),
                        i18nd("cde-copper", "Always in the load meter"),
                        i18nd("cde-copper", "Not shown")]
                currentIndex: Math.max(0, values.indexOf(page.cfg_batteryMeter))
                onActivated: index => page.cfg_batteryMeter = values[index]
                ToolTip.text: i18nd("cde-copper", "Only on computers with a battery; needs the load meter")
                ToolTip.visible: hovered
            }
            RowLayout {
                Kirigami.FormData.label: i18nd("cde-copper", "Style:")
                spacing: Kirigami.Units.smallSpacing
                Repeater {
                    model: page.smallStyles
                    delegate: ChoiceCard {
                        id: styleCard
                        required property var modelData
                        implicitWidth: Kirigami.Units.gridUnit * 9
                        caption: modelData.short
                        checked: page.cfg_smallStyle === modelData.value
                        onClicked: page.cfg_smallStyle = modelData.value
                        ToolTip.text: modelData.text; ToolTip.visible: hovered
                        StyleSketch {
                            anchors.fill: parent; anchors.margins: 4
                            style: styleCard.modelData.value
                            face: Qt.tint(Kirigami.Theme.backgroundColor, Qt.alpha(Kirigami.Theme.textColor, 0.3))
                            ink: Kirigami.Theme.textColor
                            lamp: Kirigami.Theme.highlightColor
                        }
                    }
                }
            }
            ComboBox {
                Kirigami.FormData.label: i18nd("cde-copper", "Status icons:")
                model: [i18nd("cde-copper", "Behind the block's arrow button"), i18nd("cde-copper", "Beside the console")]
                currentIndex: page.cfg_hideTrayIcons ? 0 : 1
                onActivated: index => page.cfg_hideTrayIcons = index === 0
            }
            CheckBox {
                id: trayIconsOnly
                text: i18nd("cde-copper", "Icons only in the status popup, names as tooltips")
            }
            CheckBox {
                id: hideVolume
                text: i18nd("cde-copper", "Volume only in the console")
            }
            Label {
                Layout.maximumWidth: Kirigami.Units.gridUnit * 26
                wrapMode: Text.WordWrap
                font: Kirigami.Theme.smallFont
                opacity: 0.7
                text: i18nd("cde-copper", "The tray leaves out its own volume icon.")
            }
            Item { Kirigami.FormData.isSection: true }
            Advanced { id: advanced }
            TextField {
                id: llmHosts
                visible: advanced.open
                Layout.fillWidth: true
                Kirigami.FormData.label: i18nd("cde-copper", "LLM hosts:")
            }
            Label {
                visible: advanced.open
                Layout.maximumWidth: Kirigami.Units.gridUnit * 26
                wrapMode: Text.WordWrap
                font: Kirigami.Theme.smallFont
                opacity: 0.7
                text: i18nd("cde-copper", "For the LLM cluster's small button and its tile (a tile's program \"LLM cluster\"). Comma-separated name=http://host:port or name=ssh:PORT (SSH runs curl on that host). Only llama.cpp server ports; empty shows no cluster.")
            }
        }
    }
}
