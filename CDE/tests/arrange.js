// Run inside KWin in the disposable VM, never installed with the theme.
var windows = workspace.windowList();
var sw = workspace.virtualScreenSize.width;
var sh = workspace.virtualScreenSize.height;
for (var w of windows) {
    var name = String(w.resourceClass);
    if (name.indexOf('dolphin') >= 0) {
        w.frameGeometry = {x: Math.round(sw * .08), y: Math.round(sh * .16), width: Math.round(sw * .43), height: Math.round(sh * .58)};
    } else if (name.indexOf('konsole') >= 0) {
        w.frameGeometry = {x: Math.round(sw * .54), y: Math.round(sh * .23), width: Math.round(sw * .39), height: Math.round(sh * .46)};
        workspace.activeWindow = w;
    }
}
