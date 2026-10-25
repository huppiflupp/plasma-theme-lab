// RISC Legacy: the command line (F12) along the bottom of the screen, as
// RISC OS's command line opens below the desktop (DESIGN.md §9). Konsole
// sets the window's title from the profile only after the window is
// mapped, too late for a window rule, so the title is watched here: a
// window whose caption starts with "*Command line" is laid along the
// bottom of its screen's work area, full width, a third of its height,
// without frame, above other windows, left out of task lists.
function place(w) {
    if (!w || !w.normalWindow || String(w.caption).indexOf("*Command line") !== 0) return;
    var area = workspace.clientArea(KWin.MaximizeArea, w);
    var h = Math.round(area.height / 3);
    w.noBorder = true;
    w.keepAbove = true;
    w.skipTaskbar = true;
    w.skipPager = true;
    w.frameGeometry = {x: area.x, y: area.y + area.height - h, width: area.width, height: h};
}
function watch(w) {
    if (!w) return;
    place(w);
    w.captionChanged.connect(function () { place(w); });
}
workspace.windowList().forEach(watch);
workspace.windowAdded.connect(watch);
