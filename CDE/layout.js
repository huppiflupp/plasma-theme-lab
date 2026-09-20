// Applied only when the user explicitly requests the CDE console layout.
var existing = panels();
for (var i = 0; i < existing.length; ++i) existing[i].remove();
var panel = new Panel;
panel.location = 'bottom';
panel.alignment = 'center';
panel.height = 128;
panel.lengthMode = 'custom';
panel.minimumLength = Math.min(1060, screenGeometry(0).width - 32);
panel.maximumLength = panel.minimumLength;
panel.length = panel.minimumLength;
panel.floating = true;
panel.hiding = 'none';
panel.addWidget('org.cde.copper.frontpanel');
for (var d of desktops()) {
    d.wallpaperPlugin = 'org.kde.color';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];
    d.writeConfig('Color', '#086875');
}
