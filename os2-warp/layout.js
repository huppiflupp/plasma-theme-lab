// Warp Legacy's desktop layout (DESIGN.md §4–§6), applied only when the
// user asks for the global theme's layout: the Warp Bar along the top with
// Plasma's system tray and clock, the LaunchPad floating at the bottom
// centre, the Control Strip on the right edge. The Tab Launcher is left
// out: it would share the bottom edge with the LaunchPad; it can be added.
// build.py replaces @PICTURE@ with the variant's wallpaper package.
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();

var top = new Panel;
top.screen = 0;
top.location = 'top';
top.height = 28;
top.hiding = 'none';
top.floating = false;
top.addWidget('org.warplegacy.warpbar');
top.addWidget('org.kde.plasma.panelspacer');
// Status icons, and Plasma's notifications, which only show while a tray
// exists in some panel.
top.addWidget('org.kde.plasma.systemtray');
top.addWidget('org.kde.plasma.digitalclock');

var strip = new Panel;
strip.screen = 0;
strip.location = 'right';
strip.height = 130;
strip.hiding = 'none';
strip.floating = false;
strip.addWidget('org.warplegacy.controlstrip');

var pad = new Panel;
pad.screen = 0;
pad.location = 'bottom';
pad.alignment = 'center';
pad.lengthMode = 'fit';
pad.height = 76;
// Windows may go below the LaunchPad, as below OS/2's floating LaunchPad
// window: reserving the bottom edge cut the Control Strip short above it
// (Plasma reserves the full width for a bottom panel).
pad.hiding = 'windowsgobelow';
pad.floating = true;
pad.addWidget('org.warplegacy.launchpad');

// userDataPath() alone is the home folder (VM, 20.10.2026); 'data' is
// ~/.local/share, where install.sh puts the wallpaper packages.
var picture = 'file://' + userDataPath('data', 'wallpapers/@PICTURE@/');
for (var d of desktops()) {
    d.wallpaperPlugin = 'org.kde.image';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
    d.writeConfig('Image', picture);
}
