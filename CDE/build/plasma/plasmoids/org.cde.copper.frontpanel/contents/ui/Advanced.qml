import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

// A folded "Advanced" section at the end of a settings page: fields few
// people need (hosts, commands, captions) stay out of sight until opened.
ToolButton {
    readonly property bool open: checked
    checkable: true
    icon.name: checked ? "arrow-down" : "arrow-right"
    text: i18nd("cde-copper", "Advanced")
    font.bold: true
}
