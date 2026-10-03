// The layout this shell builds when a global theme brings none for it:
// Plasma looks for <shell>-layout.js in the global theme, then for this
// file. CDE Copper's global themes carry their own; every other one (Breeze
// and the rest only ship org.kde.plasma.desktop-layout.js) gets Plasma's
// default panel here, as under Plasma's own shell, instead of a desktop
// without any panel.
loadTemplate("org.kde.plasma.desktop.defaultPanel")

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = 'org.kde.image';
}
