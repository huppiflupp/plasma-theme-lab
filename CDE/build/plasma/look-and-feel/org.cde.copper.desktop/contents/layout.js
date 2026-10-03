// Applied only when the user explicitly requests the CDE console layout.
//
// One console per screen. Creating a single panel lets Plasma pick the
// screen, and the other screens stay without a console; NT Legacy measured
// exactly that (screenCount=2, panels().length=1). From the second screen
// on, a console is kept only if it really sits there: setScreen can fail,
// and stacked consoles on one screen would be worse than one too few. The
// first is never removed.
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();
for (var s = 0; s < screenCount; ++s) {
    var panel = new Panel;
    panel.screen = s;
    panel.location = 'bottom';
    panel.alignment = 'center';
    panel.height = 128;
    // The console sizes itself from its tiles; the panel follows.
    panel.lengthMode = 'fit';
    panel.floating = true;
    panel.hiding = 'none';
    panel.addWidget('org.cde.copper.frontpanel');
    // The system tray beside the console: status icons (and the hidden
    // ones behind its arrow), and Plasma's notifications, which are only
    // shown at all while a tray exists in some panel.
    if (s === 0) panel.addWidget('org.kde.plasma.systemtray');
    if (s > 0 && panel.screen !== s) panel.remove();
}
for (var d of desktops()) {
    d.wallpaperPlugin = 'org.kde.color';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];
    d.writeConfig('Color', '#086875');
}
