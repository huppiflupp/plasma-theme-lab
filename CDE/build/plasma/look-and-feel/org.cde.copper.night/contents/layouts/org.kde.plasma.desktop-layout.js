// Applied only when the user explicitly requests the CDE console layout.
//
// The panel's screen is set, not left to Plasma: a single new panel lands
// wherever Plasma picks. From the second screen on (one console per
// screen), a console is kept only if it really sits there: setScreen can
// fail, and stacked consoles on one screen would be worse than one too
// few. The first is never removed.
// One console by default, on the first screen (Plasma's primary); with
// "A console on every screen" in the console's settings (cdecopperrc
// [Console] AllScreens) one per screen.
var everyScreen = ConfigFile("cdecopperrc", "Console").readEntry("AllScreens") === "true";
var screens = everyScreen ? screenCount : 1;
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();
for (var s = 0; s < screens; ++s) {
    // Further screens only where Plasma has a desktop already: applied in a
    // running Plasma it does not know the second screen yet, and a panel
    // created there and removed again took the first one along (NT Legacy
    // measured it: screen -1, both screens black until plasmashell restarts).
    if (s > 0 && !desktopForScreen(s)) continue;
    var panel = new Panel;
    panel.screen = s;
    panel.location = 'bottom';
    panel.alignment = 'center';
    panel.height = 128;
    // The console sizes itself from its tiles; the panel follows.
    panel.lengthMode = 'fit';
    panel.floating = true;
    panel.hiding = 'none';
    var console = panel.addWidget('org.cde.copper.frontpanel');
    // The console's settings survive the rebuild: it mirrors every change
    // into cdecopperrc [Console] (see main.qml), the new console gets them back.
    // A further screen's console has its own changes in [Console-<screen>],
    // over the first one's.
    console.currentConfigGroup = ['General'];
    var groups = s > 0 ? ['Console', 'Console-' + s] : ['Console'];
    for (var g of groups) {
        var saved = ConfigFile('cdecopperrc', g);
        // keyList in Plasma 6.6 (Kubuntu 26.04); without any, or with no file
        // yet, there is nothing to hand back.
        var keys = saved.keyList || saved.keys || [];
        for (var k of keys) if (k !== 'AllScreens') console.writeConfig(k, saved.readEntry(k));
    }
    // The setting the consoles were placed by, or the console would offer
    // the choice the other way round.
    console.writeConfig('everyScreen', everyScreen);
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
