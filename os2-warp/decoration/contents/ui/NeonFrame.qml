import QtQuick

// Neon's frame line (DESIGN.md §9a, after reference/neon-2026.png): the
// light edge cyan along the top and left, as OS/2's white; the bottom and
// right run from cyan through violet into pink towards the bottom right
// corner, where the concept's windows glow magenta.
Item {
    id: frame
    property color light
    property color dark
    property color accent
    // Bottom and right: a line from where the light edge ends to the corner.
    Rectangle { width: parent.width; height: 1; color: frame.light }
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
            GradientStop { position: 0.0; color: frame.light }
            GradientStop { position: 0.55; color: frame.dark }
            GradientStop { position: 1.0; color: frame.accent }
        }
    }
}
