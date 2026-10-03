pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

// The Applications menu: categories, each cascading into its applications,
// built from the Kicker model the Plasma menus use, so it follows installed
// and removed applications.
//
// One Plasma dialog holds both levels: the category list, and to its right,
// level with the chosen category, the box of its applications. A second
// window for the submenu (Qt's nested Menu, a second Dialog, Kicker's
// SubMenu) was tried first; under Wayland from a panel KWin placed it at
// 0,0 with its first size and never moved it. The dialog itself also keeps
// the size it was first shown with, so it opens at the full size of both
// levels; the part not in use is transparent. Keyboard: Up/Down,
// Right/Enter opens or launches, Left goes back, Escape closes.
Item {
    id: menu
    property var appsModel
    signal findRequested()
    signal runRequested()
    readonly property bool opened: categories.visible
    property int current: -1
    property int subCurrent: -1
    property var subModel: null
    property real subTop: 0
    readonly property bool cascaded: subModel !== null
    property bool wantSub: false
    // Kicker replaces its category models whenever the application
    // database changes (a package installed, kbuildsycoca); the old one is
    // destroyed and this property turns null. Fetch the new one.
    onSubModelChanged: if (subModel === null && wantSub && categories.visible) Qt.callLater(() => select(current))
    readonly property int fixedRows: 2

    property real anchorOffset: 0
    function open(anchor) {
        current = -1; subCurrent = -1;
        categories.visualParent = anchor;
        categories.visible = true;
        // Upright, the dialog may be pushed against the screen edge; line the
        // list up with the tile wherever the dialog ended up.
        Qt.callLater(() => { anchorOffset = anchor.mapToGlobal(0, 0).y - categories.y; });
    }
    function close() {
        wantSub = false;
        subModel = null;
        categories.visible = false;
    }
    function rowCount() { return fixedRows + (appsModel ? appsModel.count : 0); }
    function select(index) {
        current = index;
        subCurrent = -1;
        const category = index - fixedRows;
        const row = category >= 0 ? categoryRows.itemAt(category) : null;
        wantSub = Boolean(row && row.cascade);
        if (wantSub) {
            subModel = appsModel.modelForRow(category);
            subTop = row.y;
        } else {
            subModel = null;
        }
    }
    function activate(index) {
        if (index === 0) { close(); findRequested(); }
        else if (index === 1) { close(); runRequested(); }
        else select(index);
    }
    function launch(row) {
        if (!subModel) return;
        subModel.trigger(row, "", null);
        close();
    }

    PlasmaCore.Dialog {
        id: categories
        visible: false
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        location: Plasmoid.location
        hideOnWindowDeactivate: true
        backgroundHints: PlasmaCore.Types.NoBackground
        onVisibleChanged: if (visible) body.forceActiveFocus(); else { menu.wantSub = false; menu.subModel = null; }
        mainItem: Item {
            id: frame
            readonly property real subHeight: Math.min((menu.subModel ? menu.subModel.count : 0) * 30, 620) + 10
            readonly property int edge: Plasmoid.location
            readonly property bool upright: edge === PlasmaCore.Types.LeftEdge || edge === PlasmaCore.Types.RightEdge
            readonly property real subY: Math.max(0, Math.min(body.y + menu.subTop, height - subHeight))
            // Plasma centres the dialog on the tile. Across: keep the category
            // list in the middle, with room for the applications box on either
            // side. Upright: the list sits against the console, the box away
            // from it, both centred vertically on the tile.
            width: upright ? body.width + appsBox.width - 2 : body.width + 2 * (appsBox.width - 2)
            height: Math.max(body.height, 630)
            Bevel {
                id: body
                // Next to the console.
                x: frame.edge === PlasmaCore.Types.LeftEdge ? 0 : appsBox.width - 2
                y: frame.upright ? Math.max(0, Math.min(frame.height - height, menu.anchorOffset))
                 : frame.edge === PlasmaCore.Types.TopEdge ? 0 : frame.height - height
                width: 250
                height: column.implicitHeight + 10
                surface: consoleColors.window
                focus: true
                Keys.onEscapePressed: menu.close()
                Keys.onUpPressed: {
                    if (menu.cascaded && menu.subCurrent >= 0) menu.subCurrent = Math.max(0, menu.subCurrent - 1);
                    else menu.select(Math.max(0, menu.current - 1));
                }
                Keys.onDownPressed: {
                    if (menu.cascaded && menu.subCurrent >= 0) menu.subCurrent = Math.min(menu.subModel.count - 1, menu.subCurrent + 1);
                    else menu.select(Math.min(menu.rowCount() - 1, menu.current + 1));
                }
                Keys.onRightPressed: if (menu.cascaded) menu.subCurrent = Math.max(0, menu.subCurrent)
                Keys.onLeftPressed: menu.subCurrent = -1
                Keys.onReturnPressed: menu.subCurrent >= 0 ? menu.launch(menu.subCurrent) : menu.activate(menu.current)
                Keys.onEnterPressed: menu.subCurrent >= 0 ? menu.launch(menu.subCurrent) : menu.activate(menu.current)
                ColumnLayout {
                    id: column
                    x: 5; y: 5; width: parent.width - 10
                    spacing: 0
                    Bevel {
                        Layout.fillWidth: true; Layout.preferredHeight: 27; Layout.bottomMargin: 3
                        surface: consoleColors.highlight
                        Text { anchors.centerIn: parent; text: i18nd("cde-copper", "Applications"); color: consoleColors.highlightText; font.family: consoleColors.font; font.pixelSize: 12; font.weight: Font.DemiBold }
                    }
                    MenuRow {
                        Layout.fillWidth: true
                        glyph: "edit-find"; label: i18nd("cde-copper", "Find Application…")
                        highlighted: menu.current === 0
                        onHovered: menu.select(0)
                        onActivated: menu.activate(0)
                    }
                    MenuRow {
                        Layout.fillWidth: true
                        glyph: "system-run"; label: i18nd("cde-copper", "Run Command…")
                        highlighted: menu.current === 1
                        onHovered: menu.select(1)
                        onActivated: menu.activate(1)
                    }
                    // Motif separator: an etched double line.
                    Item {
                        Layout.fillWidth: true; Layout.preferredHeight: 8
                        Rectangle { y: 3; width: parent.width; height: 1; color: body.shade.bottom }
                        Rectangle { y: 4; width: parent.width; height: 1; color: body.shade.top }
                    }
                    Repeater {
                        id: categoryRows
                        model: menu.appsModel
                        delegate: MenuRow {
                            required property int index
                            required property var model
                            Layout.fillWidth: true
                            glyph: model.decoration
                            label: model.display || ""
                            cascade: model.hasChildren !== false
                            highlighted: menu.current === index + menu.fixedRows
                            onHovered: menu.select(index + menu.fixedRows)
                            onActivated: menu.select(index + menu.fixedRows)
                        }
                    }
                }
            }

            Bevel {
                id: appsBox
                visible: menu.cascaded
                x: frame.edge === PlasmaCore.Types.RightEdge ? 0 : body.x + body.width - 2
                y: frame.subY
                width: 290
                height: frame.subHeight
                surface: consoleColors.window
                ListView {
                    id: apps
                    x: 5; y: 5; width: parent.width - 10; height: parent.height - 10
                    clip: true
                    model: menu.subModel
                    interactive: contentHeight > height
                    ScrollBar.vertical: ScrollBar { policy: apps.interactive ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff }
                    currentIndex: menu.subCurrent
                    onCurrentIndexChanged: if (currentIndex >= 0) positionViewAtIndex(currentIndex, ListView.Contain)
                    delegate: MenuRow {
                        required property int index
                        required property var model
                        width: apps.width - (apps.interactive ? 14 : 0)
                        glyph: model.decoration
                        label: model.display || ""
                        highlighted: menu.subCurrent === index
                        onHovered: menu.subCurrent = index
                        onActivated: menu.launch(index)
                    }
                }
            }
        }
    }
}
