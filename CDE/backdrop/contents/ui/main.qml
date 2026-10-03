import QtQuick
import QtCore
import org.kde.plasma.plasmoid

// CDE backdrops as a wallpaper type: the pattern tiled pixel for pixel.
// Plasma's picture wallpaper scales a picture to the screen before tiling,
// which blows a 64-pixel tile up into a blur; here every pixel stays one
// (or "Pixel size" of them, for 200 % screens).
//
// The tiles are coloured with the applied palette by CDE Copper's tool and
// kept in ~/.local/share/cde-copper/backdrops/<palette>/; the package itself
// carries the Copper set as a fallback.
WallpaperItem {
    id: root
    readonly property string backdrop: root.configuration.Backdrop || "Pebbles"
    readonly property string paletteName: root.configuration.Palette || "Copper"
    readonly property int pixel: Math.max(1, Math.min(4, root.configuration.PixelSize || 1))
    readonly property string profileTile: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/cde-copper/backdrops/" + paletteName + "/" + backdrop + ".png"
    readonly property string packageTile: Qt.resolvedUrl("../images/Copper/" + backdrop + ".png")

    Rectangle {
        anchors.fill: parent
        color: root.configuration.Color
    }
    // Loads the tile once at its natural size; the visible copy scales it by
    // whole pixels. Falls back to the packaged Copper tile.
    Image {
        id: probe
        visible: false
        cache: false
        source: root.profileTile
        onStatusChanged: if (status === Image.Error && source !== root.packageTile) source = root.packageTile
    }
    Image {
        anchors.fill: parent
        visible: probe.status === Image.Ready
        source: probe.source
        cache: false
        smooth: false
        // The screen-high gradients (Concave, Convex, Sky*) run across and
        // stretch down; everything else repeats both ways.
        fillMode: probe.implicitHeight >= 512 ? Image.TileHorizontally : Image.Tile
        sourceSize.width: probe.implicitWidth * root.pixel
        sourceSize.height: probe.implicitHeight >= 512 ? -1 : probe.implicitHeight * root.pixel
    }
}
