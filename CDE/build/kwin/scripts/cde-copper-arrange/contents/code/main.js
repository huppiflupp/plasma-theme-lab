// CDE Copper: arrange the windows around the front console.
//
// Terminals take the space left and right of the console, down to the
// bottom of the screen; the main window (the active one, or a web browser
// when a terminal is active) stands in the middle, above the console.
// Other windows are left alone. Without a console on the screen the
// columns are a quarter of the screen each.
//
// Shortcut Meta+Ctrl+C, or the console's System menu, or a tile with the
// command @arrange.

const TERMINALS = ["konsole", "org.kde.konsole", "xterm", "gnome-terminal", "gnome-terminal-server",
                   "org.gnome.terminal", "kitty", "alacritty", "foot", "wezterm", "org.wezfurlong.wezterm",
                   "xfce4-terminal", "terminator", "tilix", "com.gexperts.tilix", "qterminal", "ghostty", "com.mitchellh.ghostty"];
const BROWSERS = ["firefox", "org.mozilla.firefox", "chromium", "chromium-browser", "google-chrome",
                  "falkon", "org.kde.falkon", "konqueror", "brave-browser", "librewolf", "vivaldi-stable"];

function cls(w) {
    return String(w.resourceClass || "").toLowerCase();
}

function onThisDesktop(w) {
    const desks = w.desktops || [];
    return desks.length === 0 || desks.indexOf(workspace.currentDesktop) >= 0;
}

function arrange() {
    const output = workspace.activeScreen;
    const screen = workspace.clientArea(KWin.ScreenArea, output, workspace.currentDesktop);
    const windows = workspace.windowList().filter(w => w.output === output && onThisDesktop(w) && !w.minimized);
    const consoles = windows.filter(w => w.dock && w.frameGeometry.height < screen.height / 2);
    const normal = windows.filter(w => w.normalWindow && !w.skipTaskbar && w.moveable && w.resizeable);
    const terminals = normal.filter(w => TERMINALS.indexOf(cls(w)) >= 0);

    // The console's horizontal extent splits the screen into three columns.
    let left = screen.x + Math.round(screen.width / 4);
    let right = screen.x + screen.width - Math.round(screen.width / 4);
    let top = screen.y, bottom = screen.y + screen.height;
    if (consoles.length) {
        const c = consoles[0].frameGeometry;
        left = c.x; right = c.x + c.width;
        if (c.y > screen.y + screen.height / 2) bottom = c.y;   // console at the bottom
        else top = c.y + c.height;                              // console at the top
    }
    const gap = 4;

    let main = workspace.activeWindow;
    if (!main || terminals.indexOf(main) >= 0 || normal.indexOf(main) < 0)
        main = normal.find(w => BROWSERS.indexOf(cls(w)) >= 0) || normal.find(w => terminals.indexOf(w) < 0) || null;

    function place(w, x, y, width, height) {
        if (w.setMaximize) w.setMaximize(false, false);
        w.frameGeometry = {x: Math.round(x), y: Math.round(y), width: Math.round(width), height: Math.round(height)};
    }

    // Terminals alternate left and right and share each column's height.
    const columns = [[], []];
    terminals.forEach((w, i) => columns[i % 2].push(w));
    const spans = [[screen.x, left], [right, screen.x + screen.width]];
    columns.forEach((list, side) => {
        const [x0, x1] = spans[side];
        const height = (screen.height - gap * (list.length + 1)) / Math.max(1, list.length);
        list.forEach((w, i) => place(w, x0 + gap, screen.y + gap + i * (height + gap), x1 - x0 - 2 * gap, height));
    });

    if (main) {
        const x0 = terminals.length ? left : screen.x;
        const x1 = terminals.length ? right : screen.x + screen.width;
        place(main, x0 + gap, top + gap, x1 - x0 - 2 * gap, bottom - top - 2 * gap);
        workspace.activeWindow = main;
    }
}

registerShortcut("CDE Copper: Arrange Around Console", "CDE Copper: arrange windows around the front console",
                 "Meta+Ctrl+C", arrange);
