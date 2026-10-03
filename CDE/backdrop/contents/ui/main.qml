import QtQuick
import QtCore
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager
import org.kde.kirigami as Kirigami

// CDE backdrops as a wallpaper type: the pattern tiled pixel for pixel.
// Plasma's picture wallpaper scales a picture to the screen before tiling,
// which blows a 64-pixel tile up into a blur; here every pixel stays one
// (or "Pixel size" of them, for 200 % screens).
//
// The tiles are coloured with the applied palette by CDE Copper's tool and
// kept in ~/.local/share/cde-copper/backdrops/<palette>/; the package itself
// carries the Copper set as a fallback.
//
// As in CDE, every workspace can have its own backdrop (PerWorkspace): the
// pattern follows the current virtual desktop; workspaces beyond the list
// show the general one.
//
// "picture:<key>" instead of a pattern shows one of CDE Copper's pictures
// (the wallpaper packages org.cde.copper.<key>) across the screen, its dark
// version under a dark palette.
WallpaperItem {
    id: root
    TaskManager.VirtualDesktopInfo { id: desktops }
    readonly property int workspace: desktops.desktopIds.indexOf(desktops.currentDesktop)
    readonly property var perWorkspace: root.configuration.Workspaces || []
    readonly property string backdrop: (root.configuration.PerWorkspace && workspace >= 0 && perWorkspace[workspace])
                                       || root.configuration.Backdrop || "Pebbles"
    readonly property string paletteName: root.configuration.Palette || "Copper"
    readonly property int pixel: Math.max(1, Math.min(4, root.configuration.PixelSize || 1))
    readonly property string profileTile: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/cde-copper/backdrops/" + paletteName + "/" + backdrop + ".png"
    readonly property string packageTile: Qt.resolvedUrl("../images/Copper/" + backdrop + ".png")
    readonly property bool isPicture: backdrop.startsWith("picture:")
    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property string picture: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/wallpapers/org.cde.copper." + backdrop.slice(8) + "/contents/" + (dark ? "images_dark" : "images") + "/3840x2160.jpg"

    Rectangle {
        anchors.fill: parent
        color: root.configuration.Color
    }
    // Loads the tile once at its natural size; the visible copy scales it by
    // whole pixels. Falls back to the packaged Copper tile.
    // A flag rather than assigning the source, so the binding survives a
    // change of workspace or backdrop.
    property bool fallback: false
    onBackdropChanged: fallback = false
    onPaletteNameChanged: fallback = false
    Image {
        anchors.fill: parent
        visible: root.isPicture
        source: root.isPicture ? root.picture : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        // Decoded at screen size, not at 3840 x 2160.
        sourceSize.width: width
        sourceSize.height: height
    }
    Image {
        id: probe
        visible: false
        cache: false
        source: root.isPicture ? "" : root.fallback ? root.packageTile : root.profileTile
        onStatusChanged: if (status === Image.Error && !root.fallback) root.fallback = true
    }
    Image {
        anchors.fill: parent
        visible: !root.isPicture && probe.status === Image.Ready
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
