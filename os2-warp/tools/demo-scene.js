// KWin script for demo-scene.sh: puts the demo windows where the Neon
// concept (reference/neon-2026.png, 1536x1024) has them, closes extra
// windows of the same program. Plain ES5, as CDE Copper's scripts.
(function () {
    // The concept's desktop is 1536 wide and 955 high (its taskbar below).
    var full = workspace.clientArea(KWin.FullScreenArea, workspace.activeScreen, workspace.currentDesktop);
    var work = workspace.clientArea(KWin.MaximizeArea, workspace.activeScreen, workspace.currentDesktop);
    // The right panel (control strip) reserves a strut over the full
    // height, so take the width from the screen, the height from the work area.
    var top = work.y, height = work.y + work.height - top;
    var sx = full.width / 1536, sy = height / 955;
    var gap = 8;

    // Docks that do not span the screen (the control strip): keep clear.
    var obstacles = [];
    var all = workspace.windowList();
    for (var i = 0; i < all.length; i++) {
        var d = all[i];
        if (d.dock && d.frameGeometry.width < full.width / 2 && d.frameGeometry.height < full.height / 2)
            obstacles.push(d.frameGeometry);
    }

    function cls(w) { return String(w.resourceClass).toLowerCase(); }
    function isDolphin(w) { return /dolphin/.test(cls(w)); }
    function isProjects(w) { return /Projekte/.test(String(w.caption)); }
    // match, x, y, width, height in the concept's pixels
    var places = [
        [function (w) { return isDolphin(w) && !isProjects(w); }, 125, 70, 585, 345],
        [function (w) { return /konsole/.test(cls(w)); }, 725, 70, 480, 350],
        [function (w) { return /firefox/.test(cls(w)); }, 125, 440, 740, 490],
        [function (w) { return isDolphin(w) && isProjects(w); }, 880, 430, 430, 235],
        [function (w) { return /systemsettings/.test(cls(w)); }, 915, 690, 590, 245]
    ];
    var used = [];

    function avoid(g) {
        for (var k = 0; k < obstacles.length; k++) {
            var o = obstacles[k];
            if (g.x + g.width <= o.x - gap || g.x >= o.x + o.width ||
                g.y + g.height <= o.y || g.y >= o.y + o.height + gap)
                continue;
            var below = o.y + o.height + gap - g.y;
            if (below < g.height / 4) g.y += below;          // just below it
            else g.width = o.x - gap - g.x;                  // narrower
        }
        return g;
    }

    for (var j = 0; j < all.length; j++) {
        var w = all[j];
        if (!w.normalWindow || w.skipTaskbar) continue;
        for (var p = 0; p < places.length; p++) {
            var pl = places[p];
            if (!pl[0](w)) continue;
            if (used[p]) { w.closeWindow(); break; }        // one per program
            used[p] = true;
            if (w.minimized) w.minimized = false;
            w.setMaximize(false, false);
            w.frameGeometry = avoid({
                x: full.x + Math.round(pl[1] * sx), y: top + Math.round(pl[2] * sy),
                width: Math.round(pl[3] * sx), height: Math.round(pl[4] * sy)
            });
            break;
        }
    }
})();
