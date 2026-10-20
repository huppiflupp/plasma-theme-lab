import QtQuick

// Neon's frame line (DESIGN.md §9a, measured on reference/neon-2026.png):
// cyan along the left and most of the top, as OS/2's white; both right
// corners glow pink (the top edge turns from about 200° to 290° hue over
// its last fifth); the bottom runs from cyan through violet into pink, the
// right edge from pink through violet back to pink.
Item {
    id: frame
    property color light
    property color dark
    property color accent
    Rectangle {
        width: parent.width; height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: frame.light }
            GradientStop { position: 0.78; color: frame.light }
            GradientStop { position: 1.0; color: frame.accent }
        }
    }
    Rectangle { width: 1; height: parent.height; color: frame.light }
    Rectangle {
        y: parent.height - 1; width: parent.width; height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: frame.light }
            GradientStop { position: 0.55; color: frame.dark }
            GradientStop { position: 1.0; color: frame.accent }
        }
    }
    Rectangle {
        x: parent.width - 1; width: 1; height: parent.height
        gradient: Gradient {
            GradientStop { position: 0.0; color: frame.accent }
            GradientStop { position: 0.4; color: frame.dark }
            GradientStop { position: 1.0; color: frame.accent }
        }
    }
}
