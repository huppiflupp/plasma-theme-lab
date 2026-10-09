pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// The open windows as a strip of buttons under the tiles (one per group
// of an application's windows when grouped).
ListView {
    id: taskList
    // The console (main.qml): given, never looked up.
    required property var root
    Layout.fillWidth: true; Layout.fillHeight: true
    // Upright, the strip takes what the tiles leave of the screen, at least
    // one button; more windows scroll. A larger minimum pushed the console
    // past the screen's lower edge.
    Layout.minimumHeight: taskList.root.vertical ? taskList.root.u(24) : 0
    orientation: taskList.root.vertical ? ListView.Vertical : ListView.Horizontal
    spacing: 3; clip: true
    model: taskList.root.taskModel
    // The buttons' width, worked out once the view has settled: bound
    // straight to the view's width it looped while the console turned
    // between across and upright.
    property real buttonWidth: 0
    function fitButtons() {
        buttonWidth = root.vertical ? width
            : Math.min(root.u(220), Math.max(root.u(120), (width - (count - 1) * 3) / Math.max(1, count)));
    }
    onWidthChanged: Qt.callLater(fitButtons)
    onCountChanged: Qt.callLater(fitButtons)
    Connections { target: taskList.root; function onVerticalChanged() { Qt.callLater(taskList.fitButtons); } }
    Component.onCompleted: fitButtons()
    delegate: ConsoleButton {
        id: taskButton
        required property int index
        required property var model
        width: taskList.buttonWidth
        height: taskList.root.vertical ? taskList.root.u(24) : taskList.height
        horizontal: true; iconSize: taskList.root.u(18)
        readonly property int windows: model.IsGroupParent ? model.ChildCount : 1
        text: windows > 1 ? i18nd("cde-copper", "%1× %2", windows, model.AppName || model.display) : (model.display || i18nd("cde-copper", "Window"))
        Accessible.name: windows > 1 ? taskList.root.groupTitles(index).join("\n") : text
        iconName: ""
        Kirigami.Icon { x: 7; anchors.verticalCenter: parent.verticalCenter; width: taskList.root.u(18); height: width; source: parent.model.decoration; active: false }
        leftPadding: taskList.root.u(30)
        selected: Boolean(model.IsActive)
        onClicked: {
            if (windows > 1) { taskList.root.cycleGroup(index, windows); return; }
            const idx = taskList.root.taskModel.makeModelIndex(index);
            if (model.IsActive) taskList.root.taskModel.requestToggleMinimized(idx); else taskList.root.taskModel.requestActivate(idx);
        }
        // The window menu. A MouseArea, not a TapHandler: it takes the
        // press, so the panel's own context menu does not open as well;
        // the left button is not accepted and stays the button's.
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onPressed: taskList.root.taskMenu.open(taskButton.index, taskButton)
        }
    }
}
