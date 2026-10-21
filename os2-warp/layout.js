// Warp Legacy's desktop layout (DESIGN.md §4–§6), applied only when the
// user asks for the global theme's layout. Since 21.10.2026 the Neon
// concept's (reference/neon-2026.png): the Warp Taskbar along the bottom
// with Plasma's system tray and clock, the Control Strip on the right edge,
// the Tab Launcher as a drawer at the top left. The arrangement with the
// Warp Bar along the top and the LaunchPad below (the one before, used for
// the screenshots) is tools/demo-scene.sh --panels screenshots.
// build.py replaces @PICTURE@ with the variant's wallpaper package.
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();

var bar = new Panel;
bar.screen = 0;
bar.location = 'bottom';
bar.height = 32;
bar.hiding = 'none';
bar.floating = false;
bar.addWidget('org.warplegacy.taskbar');
// Status icons, and Plasma's notifications, which only show while a tray
// exists in some panel.
bar.addWidget('org.kde.plasma.systemtray');
bar.addWidget('org.kde.plasma.digitalclock');

var strip = new Panel;
strip.screen = 0;
strip.location = 'right';
strip.height = 130;
strip.hiding = 'none';
strip.floating = false;
strip.addWidget('org.warplegacy.controlstrip');

// The Tab Launcher's drawer (common/PanelsPage.qml adds it the same way):
// its own panel, length "custom" from 10 px so it shrinks to its tab when
// slid in; windows may go below it.
var drawer = new Panel;
drawer.screen = 0;
drawer.location = 'top';
drawer.alignment = 'left';
drawer.height = 94;
drawer.hiding = 'windowsgobelow';
drawer.floating = false;
drawer.lengthMode = 'custom';
drawer.minimumLength = 10;
drawer.maximumLength = screenGeometry(0).width;
drawer.addWidget('org.warplegacy.tablauncher');

// userDataPath() alone is the home folder (VM, 20.10.2026); 'data' is
// ~/.local/share, where install.sh puts the wallpaper packages.
var picture = 'file://' + userDataPath('data', 'wallpapers/@PICTURE@/');
for (var d of desktops()) {
    d.wallpaperPlugin = 'org.kde.image';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
    d.writeConfig('Image', picture);
}
