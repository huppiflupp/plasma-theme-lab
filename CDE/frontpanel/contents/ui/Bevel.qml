import QtQuick

Rectangle {
    id: root
    property bool sunken: false
    property color surface: "#2e7180"
    color: surface
    border.color: "#10262b"
    border.width: 1
    Rectangle { x: 1; y: 1; width: parent.width - 2; height: 1; color: root.sunken ? "#174c55" : "#b0cbcc" }
    Rectangle { x: 1; y: 1; width: 1; height: parent.height - 2; color: root.sunken ? "#174c55" : "#b0cbcc" }
    Rectangle { x: 2; y: parent.height - 2; width: parent.width - 3; height: 1; color: root.sunken ? "#b0cbcc" : "#174c55" }
    Rectangle { x: parent.width - 2; y: 2; width: 1; height: parent.height - 3; color: root.sunken ? "#b0cbcc" : "#174c55" }
}
