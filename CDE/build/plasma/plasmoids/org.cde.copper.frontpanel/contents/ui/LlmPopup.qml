pragma ComponentBehavior: Bound
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

// The LLM cluster's subpanel: each node with its tokens per second, a bar
// against the best so far and its state, then the total.
PlasmaCore.Dialog {
    id: llmPopup
    // The console (main.qml) and its colours: given, never looked up.
    required property var root
    required property var colors
    visible: false
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.WindowStaysOnTopHint
    location: Plasmoid.location
    hideOnWindowDeactivate: true
    backgroundHints: PlasmaCore.Types.NoBackground
    onVisibleChanged: if (visible) { llmKeeper.opened(); llmBody.forceActiveFocus(); }
    function llmState(state) {
        switch (state) {
        case "running": return i18nd("cde-copper", "Running");
        case "busy": return i18nd("cde-copper", "Busy");
        case "sleeping": return i18nd("cde-copper", "Sleeping");
        default: return i18nd("cde-copper", "Unreachable");
        }
    }
    mainItem: Bevel {
        id: llmBody
        // A Dialog takes no children of its own: its helpers live in here.
        Keeper { id: llmKeeper; root: llmPopup.root; dialog: llmPopup; segment: llmPopup.root.llmPopupSegment; inside: llmHover.hovered }
        width: llmPopup.root.u(390); height: llmPopup.root.u(70 + 30 * llmPopup.root.llmNodes.length)
        surface: llmPopup.colors.window
        focus: true
        HoverHandler { id: llmHover }
        Keys.onPressed: llmKeeper.keyboard = true
        Keys.onEscapePressed: llmPopup.visible = false
        Column {
            x: llmPopup.root.u(8); y: llmPopup.root.u(8); width: parent.width - llmPopup.root.u(16); spacing: llmPopup.root.u(4)
            Text {
                text: i18nd("cde-copper", "LLM cluster")
                color: llmPopup.colors.windowText; font.family: llmPopup.colors.font; font.pixelSize: llmPopup.root.u(12); font.weight: Font.DemiBold
            }
            Repeater {
                model: llmPopup.root.llmNodes
                delegate: Item {
                    required property var modelData
                    width: parent.width; height: llmPopup.root.u(26)
                    Text { x: 0; width: llmPopup.root.u(85); elide: Text.ElideRight; text: modelData.name; color: llmPopup.colors.windowText; font.family: llmPopup.colors.font; font.pixelSize: llmPopup.root.u(11) }
                    Text { x: llmPopup.root.u(88); width: llmPopup.root.u(65); text: i18nd("cde-copper", "%1 t/s", Math.round(modelData.tokens_per_second)); color: llmPopup.colors.windowText; font.family: llmPopup.colors.font; font.pixelSize: llmPopup.root.u(11) }
                    Bevel {
                        x: llmPopup.root.u(155); y: llmPopup.root.u(3); width: llmPopup.root.u(90); height: llmPopup.root.u(12); sunken: true; surface: llmPopup.colors.field
                        Rectangle { x: 2; y: 2; height: parent.height - 4; width: Math.round((parent.width - 4) * modelData.tokens_per_second / llmPopup.root.llmPeak); color: llmPopup.colors.highlight }
                    }
                    Text { x: llmPopup.root.u(253); text: llmPopup.llmState(modelData.state); color: llmPopup.colors.windowText; font.family: llmPopup.colors.font; font.pixelSize: llmPopup.root.u(11) }
                }
            }
            Text {
                text: i18nd("cde-copper", "Total: %1 t/s", Math.round(llmPopup.root.llmTotal))
                color: llmPopup.colors.windowText; font.family: llmPopup.colors.font; font.pixelSize: llmPopup.root.u(12); font.weight: Font.DemiBold
            }
        }
    }
}
