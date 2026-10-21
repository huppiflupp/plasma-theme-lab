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
    // Halfway from cyan to pink along the hue (violet-blue): straight from
    // one to the other the line passed a pale, almost white lavender (the
    // user's remark 21.10.2026).
    readonly property color between: {
        let d = accent.hsvHue - light.hsvHue;
        if (d > 0.5) d -= 1;
        if (d < -0.5) d += 1;
        return Qt.hsva(((light.hsvHue + d / 2) % 1 + 1) % 1, (light.hsvSaturation + accent.hsvSaturation) / 2,
                       (light.hsvValue + accent.hsvValue) / 2, 1);
    }
    Rectangle {
        width: parent.width; height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: frame.light }
            GradientStop { position: 0.78; color: frame.light }
            GradientStop { position: 0.89; color: frame.between }
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
