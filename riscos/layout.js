// RISC Legacy's desktop layout (DESIGN.md §5), applied only when the user
// asks for the global theme's layout: the iconbar along the bottom of the
// first screen, full width, with Plasma's system tray at its right end
// (status icons, and the notifications, which only show while a tray
// exists in some panel). build.py replaces @PICTURE@ with the variant's
// wallpaper package.
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();

var bar = new Panel;
bar.screen = 0;
bar.location = 'bottom';
bar.height = 64;
bar.hiding = 'none';
bar.floating = false;
bar.addWidget('org.risclegacy.iconbar');
bar.addWidget('org.kde.plasma.systemtray');

// userDataPath() alone is the home folder; 'data' is ~/.local/share,
// where install.sh puts the wallpaper packages.
var picture = 'file://' + userDataPath('data', 'wallpapers/@PICTURE@/');
for (var d of desktops()) {
    d.wallpaperPlugin = 'org.kde.image';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
    d.writeConfig('Image', picture);
}
