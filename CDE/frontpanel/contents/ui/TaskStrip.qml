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
    Layout.minimumHeight: taskList.root.vertical ? taskList.root.u(80) : 0
    orientation: taskList.root.vertical ? ListView.Vertical : ListView.Horizontal
    spacing: 3; clip: true
    model: taskList.root.taskModel
    delegate: ConsoleButton {
        id: taskButton
        required property int index
        required property var model
        width: taskList.root.vertical ? taskList.width
             : Math.min(taskList.root.u(220), Math.max(taskList.root.u(120), (taskList.width - (taskList.count - 1) * 3) / Math.max(1, taskList.count)))
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
