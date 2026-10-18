// Windows dragged in the workspace switcher (WindowDrag.qml, Workspaces.qml).
//
// A drag carries the window's id (TasksModel's WinIdList: KWin's internal
// id on Wayland, the X window id on X11) and where on the window it was
// taken, as fractions of its size, so that the window lands under the
// pointer as it was held.

.pragma library

const WINDOW_MIME = "application/x-cde-copper-window";

function windowRef(id, fx, fy) {
    return JSON.stringify({id: String(id), fx: clamp(fx, 0, 1), fy: clamp(fy, 0, 1)});
}

function parseWindowRef(text) {
    try {
        const ref = JSON.parse(String(text));
        if (!ref || typeof ref.id !== "string" || ref.id === "") return null;
        return {id: ref.id, fx: clamp(Number(ref.fx), 0, 1), fy: clamp(Number(ref.fy), 0, 1)};
    } catch (e) {
        return null;
    }
}

function clamp(value, low, high) {
    return isFinite(value) ? Math.max(low, Math.min(high, value)) : (low + high) / 2;
}

// The window's new top left corner, in the desktop's coordinates, for a
// drop at (x, y) on a map of the area drawn at scale.
function droppedAt(ref, frame, area, scale, x, y) {
    return {x: Math.round(area.x + x / scale - ref.fx * frame.width),
            y: Math.round(area.y + y / scale - ref.fy * frame.height)};
}

// KWin script that moves the window with this id so that its top left
// corner lies at (x, y), kept within the work area of the screen it lands
// on. A maximized or full-screen window is sent to that screen instead and
// stays as it is. The panel's task model cannot place windows on Wayland.
function moveScript(id, x, y) {
    return "(function () {"
        + " var id = " + JSON.stringify(String(id).replace(/[{}]/g, "")) + ", x = " + Math.round(x) + ", y = " + Math.round(y) + ";"
        + " var list = workspace.windowList();"
        + " for (var i = 0; i < list.length; i++) { var w = list[i];"
        + " if (String(w.internalId).replace(/[{}]/g, '') !== id && String(w.windowId) !== id) continue;"
        + " var g = w.frameGeometry;"
        + " var output = workspace.screenAt({x: x + Math.min(g.width, 40) / 2, y: y + 10}) || w.output;"
        + " var area = workspace.clientArea(KWin.MaximizeArea, output, workspace.currentDesktop);"
        + " var here = workspace.clientArea(KWin.MaximizeArea, w.output, workspace.currentDesktop);"
        + " var filling = w.fullScreen || (g.width >= here.width && g.height >= here.height);"
        + " if (filling) { if (output !== w.output) workspace.sendClientToScreen(w, output); return; }"
        + " var nx = Math.max(area.x, Math.min(x, area.x + area.width - Math.min(g.width, area.width)));"
        + " var ny = Math.max(area.y, Math.min(y, area.y + area.height - Math.min(g.height, area.height)));"
        + " w.frameGeometry = {x: nx, y: ny, width: g.width, height: g.height};"
        + " return; } })();";
}

// Shell command that runs a KWin script once: written to a file, loaded
// under a name of its own, started, unloaded. dbus is the qdbus command.
function kwinCommand(script, dbus, quote) {
    return "f=$(mktemp --suffix=.js) || exit 1; n=cde-copper-move-$(date +%s%N);"
        + " printf '%s' " + quote(script) + " > \"$f\";"
        + " d=" + dbus + ";"
        + " $d org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript \"$f\" \"$n\" >/dev/null"
        + " && $d org.kde.KWin /Scripting org.kde.kwin.Scripting.start;"
        + " sleep 1; $d org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript \"$n\" >/dev/null; rm -f \"$f\"";
}
