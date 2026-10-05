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
//
// Terminal sets: the console's Terminal subpanel arms one of the sets below
// and then starts its terminals; the next terminal windows to appear are put
// in its places, in the order they were started.
//   three: left and right of the console down to the bottom edge, and the
//          middle above the console, on the console's screen
//   four:  a window across the top half (Konsole split in two) and two
//          quarters below it, on another screen if there is one
//   seven: both

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

// The console on a screen, or null.
function consoleOn(output) {
    const screen = workspace.clientArea(KWin.ScreenArea, output, workspace.currentDesktop);
    return workspace.windowList().find(w => w.dock && w.output === output
        && w.frameGeometry.height < screen.height / 2) || null;
}

// The three columns around the console; quarters of the screen without one.
function threeSlots(output) {
    const screen = workspace.clientArea(KWin.ScreenArea, output, workspace.currentDesktop);
    let left = screen.x + Math.round(screen.width / 4);
    let right = screen.x + screen.width - Math.round(screen.width / 4);
    let top = screen.y, bottom = screen.y + screen.height;
    const dock = consoleOn(output);
    if (dock) {
        const c = dock.frameGeometry;
        left = Math.round(c.x); right = Math.round(c.x + c.width);
        if (c.y > screen.y + screen.height / 2) bottom = Math.round(c.y);
        else top = Math.round(c.y + c.height);
    }
    return [{output: output, x: screen.x, y: screen.y, width: left - screen.x, height: screen.height},
            {output: output, x: left, y: top, width: right - left, height: bottom - top},
            {output: output, x: right, y: screen.y, width: screen.x + screen.width - right, height: screen.height}];
}

// The top half across, the bottom half in two; above or below a console on
// that screen.
function fourSlots(output) {
    const area = workspace.clientArea(KWin.MaximizeArea, output, workspace.currentDesktop);
    const half = Math.round(area.height / 2), mid = Math.round(area.width / 2);
    return [{output: output, x: area.x, y: area.y, width: area.width, height: half},
            {output: output, x: area.x, y: area.y + half, width: mid, height: area.height - half},
            {output: output, x: area.x + mid, y: area.y + half, width: area.width - mid, height: area.height - half}];
}

function slotsFor(kind) {
    const screens = workspace.screens;
    const home = screens.find(s => s === workspace.activeScreen && consoleOn(s))
        || screens.find(s => consoleOn(s)) || workspace.activeScreen;
    const other = screens.find(s => s !== home) || home;
    if (kind === "three") return threeSlots(home);
    if (kind === "four") return fourSlots(other);
    return threeSlots(home).concat(fourSlots(other));
}

// An armed set waits this long for its terminals.
const PATIENCE = 20000;
let pending = null;

function arm(kind) {
    pending = {slots: slotsFor(kind), windows: [], since: Date.now()};
}

function put(w, slot) {
    if (w.setMaximize) w.setMaximize(false, false);
    if (w.output !== slot.output) workspace.sendClientToScreen(w, slot.output);
    w.frameGeometry = {x: slot.x, y: slot.y, width: slot.width, height: slot.height};
}

function settle(set) {
    // Started in order, so the process ids are in order; a terminal that
    // keeps all its windows in one process leaves them in arrival order.
    const windows = set.windows.map((w, i) => ({w: w, i: i}))
        .sort((a, b) => (a.w.pid - b.w.pid) || (a.i - b.i)).map(e => e.w);
    windows.forEach((w, i) => {
        const slot = set.slots[i];
        put(w, slot);
        // Konsole restores its last size once it is shown; keep the place
        // for the first moments.
        const placed = Date.now();
        const hold = () => {
            if (Date.now() - placed > 3000) { w.frameGeometryChanged.disconnect(hold); return; }
            const g = w.frameGeometry;
            if (g.x !== slot.x || g.y !== slot.y || g.width !== slot.width || g.height !== slot.height) put(w, slot);
        };
        w.frameGeometryChanged.connect(hold);
    });
}

workspace.windowAdded.connect(w => {
    if (!pending) return;
    if (Date.now() - pending.since > PATIENCE) { pending = null; return; }
    if (!w.normalWindow || TERMINALS.indexOf(cls(w)) < 0) return;
    pending.windows.push(w);
    if (pending.windows.length === pending.slots.length) {
        const set = pending;
        pending = null;
        settle(set);
    }
});

registerShortcut("CDE Copper: Three Terminals", "CDE Copper: place the next three terminals around the console",
                 "", () => arm("three"));
registerShortcut("CDE Copper: Four Terminals", "CDE Copper: place the next four terminals on the other screen",
                 "", () => arm("four"));
registerShortcut("CDE Copper: Seven Terminals", "CDE Copper: place the next seven terminals on both screens",
                 "", () => arm("seven"));

registerShortcut("CDE Copper: Arrange Around Console", "CDE Copper: arrange windows around the front console",
                 "Meta+Ctrl+C", arrange);
