import QtQuick
import QtCore
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager
import org.kde.kirigami as Kirigami
import "backdrops.js" as Backdrops

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
    // Same file names when the tool draws the tiles again (another pattern
    // colour, the same palette applied anew): the revision makes the address
    // new, so the image is read again.
    readonly property string revision: root.configuration.Revision ? "?r=" + root.configuration.Revision : ""
    readonly property int pixel: Math.max(1, Math.min(4, root.configuration.PixelSize || 1))
    // Material tiles (wallpapers/tiles) are JPEGs: "<key>" is tinted per
    // palette by the tool like the patterns, "natural:<key>" is the tile as
    // photographed, straight from the package.
    readonly property bool natural: backdrop.startsWith("natural:")
    readonly property string key: natural ? backdrop.slice(8) : backdrop
    readonly property bool isTile: Backdrops.TILES.some(t => t.key === key)
    readonly property string suffix: isTile ? ".jpg" : ".png"
    readonly property string profile: StandardPaths.writableLocation(StandardPaths.GenericDataLocation) + "/cde-copper/backdrops/"
    readonly property string profileTile: natural ? Qt.resolvedUrl("../images/tiles/" + key + ".jpg")
        : profile + paletteName + "/" + key + suffix
    // The palette in use, whatever this desktop's settings name.
    readonly property string currentTile: natural ? profileTile : profile + "current/" + key + suffix
    readonly property string packageTile: natural ? profileTile : Qt.resolvedUrl("../images/Copper/" + key + suffix)
    readonly property bool isPicture: backdrop.startsWith("picture:")
    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property string picture: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
        + "/wallpapers/org.cde.copper." + backdrop.slice(8) + "/contents/" + (dark ? "images_dark" : "images") + "/3840x2160.jpg"

    Rectangle {
        anchors.fill: parent
        color: root.configuration.Color
    }
    // Loads the tile once at its natural size; the visible copy scales it by
    // whole pixels. Falls back to the palette in use ("current"), then to
    // the packaged Copper tile. A step counter rather than assigning the
    // source, so the binding survives a change of workspace or backdrop;
    // stepped after the failed load, not inside it (a binding loop there
    // left the desktop without any tile).
    property int fallback: 0
    onBackdropChanged: fallback = 0
    onPaletteNameChanged: fallback = 0
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
        source: root.isPicture ? "" : [root.profileTile, root.currentTile, root.packageTile][root.fallback] + root.revision
        onStatusChanged: if (status === Image.Error && root.fallback < 2) Qt.callLater(() => { if (status === Image.Error && root.fallback < 2) root.fallback++; })
    }
    Image {
        anchors.fill: parent
        visible: !root.isPicture && probe.status === Image.Ready
        source: probe.source
        cache: false
        smooth: false
        // The screen-high gradients (Concave, Convex, Sky*: narrow and tall)
        // run across and stretch down; everything else, the square material
        // tiles included, repeats both ways.
        readonly property bool tall: probe.implicitHeight >= 512 && probe.implicitWidth < probe.implicitHeight
        fillMode: tall ? Image.TileHorizontally : Image.Tile
        sourceSize.width: probe.implicitWidth * root.pixel
        sourceSize.height: tall ? -1 : probe.implicitHeight * root.pixel
    }
}
