#!/usr/bin/env python3
"""Saved window layouts for the CDE front console.

    layouts.py list
    layouts.py save [--title T] [--label L] [--name N]
    layouts.py restore <id>
    layouts.py delete <id>

"save" records the windows of the current workspace on every screen: the
application (its desktop file), the screen, position and size, and the
stacking order; for Konsole windows also the split views, each view's
working directory and the tabs. A screenshot of all screens becomes the
preview. The name is asked for afterwards (kdialog), suggested from the
applications; --title and --label are the dialog's translated texts,
--name skips the question.

"restore" puts windows of the layout that are still open back in their
places and starts the missing ones: Konsole with its splits and folders,
other applications through their desktop file. Contents (browser tabs,
documents, running commands) are not restored.

"list" prints the saved layouts as JSON, newest first.

The window data comes from KWin: a short-lived KWin script reports it over
D-Bus to this program, which owns org.cde.copper.Layouts meanwhile.
Needs PyGObject (Gio); the layouts live in ~/.local/share/cde-copper-layouts.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from gi.repository import Gio, GLib

HOME = Path.home()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
STORE = DATA_HOME / "cde-copper-layouts"
BUS = "org.cde.copper.Layouts"
PATH = "/Layouts"
INTERFACE = """<node><interface name="org.cde.copper.Layouts">
<method name="Report"><arg type="s" name="message" direction="in"/></method>
</interface></node>"""
PLUGIN = "cde-copper-layout-session"
KONSOLE = "org.kde.konsole"


def bus():
    return Gio.bus_get_sync(Gio.BusType.SESSION, None)


def call(conn, service, path, interface, method, signature=None, args=None, timeout=5000):
    """A D-Bus call; the unpacked reply, or None when it fails."""
    try:
        reply = conn.call_sync(service, path, interface, method,
                               GLib.Variant(signature, args) if signature else None,
                               None, Gio.DBusCallFlags.NONE, timeout, None)
        return reply.unpack() if reply is not None else ()
    except GLib.Error:
        return None


class KWinSession:
    """Runs a KWin script that talks back through Report(json)."""

    def __init__(self, conn):
        self.conn = conn
        self.messages = []
        self.loop = GLib.MainLoop()
        self.handler = None
        self.registration = None

    def __enter__(self):
        owner = call(self.conn, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                     "RequestName", "(su)", (BUS, 4))
        if not owner or owner[0] != 1:
            raise RuntimeError("another layout is being saved or restored")
        info = Gio.DBusNodeInfo.new_for_xml(INTERFACE)
        register = getattr(self.conn, "register_object_with_closures2", None) or self.conn.register_object
        self.registration = register(PATH, info.interfaces[0], self._called, None, None)
        return self

    def __exit__(self, *exc):
        self.unload()
        if self.registration:
            self.conn.unregister_object(self.registration)
        call(self.conn, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
             "ReleaseName", "(s)", (BUS,))

    def _called(self, conn, sender, path, interface, method, params, invocation):
        invocation.return_value(None)
        try:
            message = json.loads(params.unpack()[0])
        except (ValueError, IndexError):
            return
        self.messages.append(message)
        if self.handler and self.handler(message):
            self.loop.quit()

    def load(self, script):
        self.unload()
        folder = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir())
        path = folder / (PLUGIN + ".js")
        path.write_text(script, encoding="utf-8")
        loaded = call(self.conn, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "loadScript",
                      "(ss)", (str(path), PLUGIN))
        if not loaded or loaded[0] < 0:
            raise RuntimeError("KWin did not load the layout script")
        call(self.conn, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "start")

    def unload(self):
        call(self.conn, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", "unloadScript", "(s)", (PLUGIN,))

    def wait(self, handler, seconds):
        """Runs until handler(message) returns True or the time is up."""
        self.handler = handler
        expired = []

        def timeout():
            expired.append(True)
            self.loop.quit()
            return False

        timer = GLib.timeout_add(int(seconds * 1000), timeout)
        self.loop.run()
        if not expired:
            GLib.source_remove(timer)
        self.handler = None


# The KWin side. REPORT sends one JSON message back.
REPORT = """
function report(message) {
    callDBus("%s", "%s", "org.cde.copper.Layouts", "Report", JSON.stringify(message));
}
""" % (BUS, PATH)

CAPTURE = REPORT + """
function onWorkspace(w) {
    const desks = w.desktops || [];
    return desks.length === 0 || desks.indexOf(workspace.currentDesktop) >= 0;
}
const screens = workspace.screens.map(s => ({name: s.name, x: s.geometry.x, y: s.geometry.y,
                                             width: s.geometry.width, height: s.geometry.height}));
const windows = [];
workspace.stackingOrder.forEach((w, z) => {
    if (!w.normalWindow || w.skipTaskbar || w.minimized || !onWorkspace(w)) return;
    const g = w.frameGeometry, s = w.output.geometry;
    windows.push({id: String(w.internalId), pid: w.pid, desktopFile: String(w.desktopFileName || ""),
                  cls: String(w.resourceClass || ""), caption: String(w.caption || ""),
                  output: w.output.name, screen: workspace.screens.indexOf(w.output),
                  outputSize: {width: s.width, height: s.height},
                  x: Math.round(g.x - s.x), y: Math.round(g.y - s.y),
                  width: Math.round(g.width), height: Math.round(g.height),
                  fullScreen: !!w.fullScreen, z: z});
});
report({kind: "windows", screens: screens, windows: windows});
"""

# Places the layout's windows: open ones at once, new ones as they appear
# (the restoring program starts them one after the other).
RESTORE = REPORT + """
const LAYOUT = %s;
const entries = LAYOUT.windows;
const placed = entries.map(() => null);

function key(text) { return String(text || "").toLowerCase().replace(/\\.desktop$/, ""); }
function entryKey(e) { return key(e.desktopFile || e.cls); }
function windowKey(w) { return key(w.desktopFileName || w.resourceClass); }
function onWorkspace(w) {
    const desks = w.desktops || [];
    return desks.length === 0 || desks.indexOf(workspace.currentDesktop) >= 0;
}

// The saved screen by name, else by position, else the first; the place is
// scaled when that screen has another size now.
function slot(e) {
    const screens = workspace.screens;
    const output = screens.find(s => s.name === e.output) || screens[e.screen] || screens[0];
    const g = output.geometry;
    const sx = g.width / (e.outputSize.width || g.width), sy = g.height / (e.outputSize.height || g.height);
    return {output: output, x: Math.round(g.x + e.x * sx), y: Math.round(g.y + e.y * sy),
            width: Math.round(e.width * sx), height: Math.round(e.height * sy)};
}

function put(w, s, fullScreen) {
    if (w.minimized) w.minimized = false;
    if (w.fullScreen && !fullScreen) w.fullScreen = false;
    if (w.setMaximize) w.setMaximize(false, false);
    if (w.output !== s.output) workspace.sendClientToScreen(w, s.output);
    if (!onWorkspace(w)) w.desktops = [workspace.currentDesktop];
    w.frameGeometry = {x: s.x, y: s.y, width: s.width, height: s.height};
    if (fullScreen) w.fullScreen = true;
}

function place(w, i) {
    const s = slot(entries[i]);
    placed[i] = w;
    put(w, s, entries[i].fullScreen);
    // Applications that restore their own size once shown keep the place.
    const since = Date.now();
    const hold = () => {
        if (Date.now() - since > 3000) { w.frameGeometryChanged.disconnect(hold); return; }
        const g = w.frameGeometry;
        if (!entries[i].fullScreen && (g.x !== s.x || g.y !== s.y || g.width !== s.width || g.height !== s.height))
            put(w, s, false);
    };
    w.frameGeometryChanged.connect(hold);
}

// Saved stacking order, the topmost window active.
function restack() {
    entries.map((e, i) => i).sort((a, b) => entries[a].z - entries[b].z).forEach(i => {
        if (placed[i]) workspace.activeWindow = placed[i];
    });
}

const taken = [];
function free(w) {
    return w.normalWindow && !w.skipTaskbar && taken.indexOf(w) < 0;
}
const open = workspace.stackingOrder.slice();
// The same window first (still open since saving), then the same title,
// then any window of the application; a terminal is only taken with its
// title (it names the folder), else a new one opens with folders and splits.
[(w, e) => String(w.internalId) === e.id,
 (w, e) => windowKey(w) === entryKey(e) && w.caption === e.caption,
 (w, e) => windowKey(w) === entryKey(e) && !e.konsole].forEach(test => {
    entries.forEach((e, i) => {
        if (placed[i]) return;
        const w = open.find(w => free(w) && test(w, e));
        if (w) { taken.push(w); place(w, i); }
    });
});

const missing = entries.map((e, i) => i).filter(i => !placed[i]);
if (missing.length === 0) restack();
report({kind: "missing", indices: missing});

workspace.windowAdded.connect(w => {
    if (!free(w)) return;
    const i = missing.find(i => !placed[i] && entryKey(entries[i]) === windowKey(w));
    if (i === undefined) return;
    taken.push(w);
    place(w, i);
    if (missing.every(i => placed[i])) restack();
    report({kind: "placed", index: i, pid: w.pid});
});
"""


def desktop_name(app_id):
    """The Name= of an installed application, or the id."""
    name = app_id if app_id.endswith(".desktop") else app_id + ".desktop"
    dirs = [DATA_HOME] + [Path(d) for d in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if d]
    dirs += [HOME / ".local/share/flatpak/exports/share", Path("/var/lib/flatpak/exports/share")]
    for d in dirs:
        path = d / "applications" / name
        if path.is_file():
            try:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("Name="):
                        return line[5:].strip()
            except OSError:
                pass
    return None


# Konsole: "(0)[1|(2){3|4}]" is splitter 0 holding view 1 beside splitter 2,
# which holds views 3 and 4 one above the other.
def parse_views(text):
    position = 0

    def node():
        nonlocal position
        if text[position] == "(":
            end = text.index(")", position)
            splitter = int(text[position + 1:end])
            position = end + 1
            opening = text[position]
            closing = "]" if opening == "[" else "}"
            position += 1
            children = [node()]
            while text[position] == "|":
                position += 1
                children.append(node())
            assert text[position] == closing
            position += 1
            return {"splitter": splitter, "horizontal": opening == "[", "children": children}
        match = re.match(r"\d+", text[position:])
        position += match.end()
        return {"view": int(match.group())}

    return node()


def konsole_windows(conn, pid):
    """Konsole's D-Bus windows of one process: their tabs as view trees with
    each view's working directory, and the current session's title."""
    service = "org.kde.konsole-%d" % pid
    introspection = call(conn, service, "/Windows", "org.freedesktop.DBus.Introspectable", "Introspect")
    if not introspection:
        return []
    result = []
    for number in re.findall(r'<node name="(\d+)"', introspection[0]):
        path = "/Windows/" + number
        window = "org.kde.konsole.Window"
        hierarchy = call(conn, service, path, window, "viewHierarchy")
        current = call(conn, service, path, window, "currentSession")
        if not hierarchy or not current:
            continue
        tabs = []
        sessions = {}
        for text in hierarchy[0]:
            try:
                tree = parse_views(text)
            except (AssertionError, ValueError, IndexError, AttributeError):
                continue
            tabs.append(tree)

        def visit(node):
            if "view" in node:
                if call(conn, service, path, window, "setCurrentView", "(i)", (node["view"],)) is not None:
                    session = call(conn, service, path, window, "currentSession")
                    if session:
                        sessions[node["view"]] = session[0]
                return
            proportions = call(conn, service, path, window, "getSplitProportions", "(i)", (node["splitter"],))
            node["proportions"] = list(proportions[0]) if proportions else []
            for child in node["children"]:
                visit(child)

        for tree in tabs:
            visit(tree)
        # Back to the session that was current.
        call(conn, service, path, window, "setCurrentSession", "(i)", (current[0],))

        def describe(node):
            if "view" not in node and len(node["children"]) == 1:
                return describe(node["children"][0])
            if "view" not in node:
                return {"horizontal": node["horizontal"], "proportions": node.get("proportions", []),
                        "children": [describe(c) for c in node["children"]]}
            session = sessions.get(node["view"])
            leaf = {"directory": str(HOME), "profile": ""}
            if session is not None:
                spath = "/Sessions/%d" % session
                shell = call(conn, service, spath, "org.kde.konsole.Session", "processId")
                profile = call(conn, service, spath, "org.kde.konsole.Session", "profile")
                if shell:
                    try:
                        leaf["directory"] = os.readlink("/proc/%d/cwd" % shell[0])
                    except OSError:
                        pass
                if profile:
                    leaf["profile"] = profile[0]
            return leaf

        title = call(conn, service, "/Sessions/%d" % current[0], "org.kde.konsole.Session", "title", "(i)", (1,))
        result.append({"title": title[0] if title else "", "tabs": [describe(t) for t in tabs]})
    return result


def summary(windows):
    counts = {}
    for w in windows:
        app = w.get("desktopFile") or w.get("cls")
        name = desktop_name(app) if app else None
        name = name or w.get("cls") or "?"
        counts[name] = counts.get(name, 0) + 1
    return ", ".join(("%d× %s" % (n, name)) if n > 1 else name
                     for name, n in sorted(counts.items(), key=lambda item: -item[1]))


def save(title, label, name=None):
    conn = bus()
    with KWinSession(conn) as session:
        result = {}
        session.load(CAPTURE)
        session.wait(lambda m: m.get("kind") == "windows" and result.update(m) is None, 5)
    if not result:
        raise RuntimeError("KWin did not report the windows")
    windows = result["windows"]
    for w in windows:
        if key(w) == KONSOLE:
            matches = konsole_windows(conn, w["pid"])
            # One window per process, or the one whose title begins the caption.
            match = (matches[0] if len(matches) == 1 else
                     next((m for m in matches if m["title"] and w["caption"].startswith(m["title"])), None))
            if match:
                w["konsole"] = match["tabs"]
    layout_id = time.strftime("%Y%m%d-%H%M%S")
    folder = STORE / layout_id
    folder.mkdir(parents=True, exist_ok=True)
    # The preview: all screens as they are now.
    screenshot = folder / "screen.png"
    try:
        subprocess.run(["spectacle", "-b", "-n", "-f", "-o", str(screenshot)], timeout=20,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass
    suggested = summary(windows) or layout_id
    if name is None:
        try:
            answer = subprocess.run(["kdialog", "--title", title, "--inputbox", label, suggested],
                                    capture_output=True, text=True)
        except OSError:
            answer = subprocess.CompletedProcess([], 0, suggested, "")
    else:
        answer = subprocess.CompletedProcess([], 0, name, "")
    if answer.returncode != 0:
        shutil.rmtree(folder, ignore_errors=True)
        return
    name = answer.stdout.strip() or suggested
    layout = {"name": name, "created": time.time(), "screens": result["screens"], "windows": windows}
    (folder / "layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False), encoding="utf-8")


def key(w):
    return (w.get("desktopFile") or w.get("cls") or "").lower().removesuffix(".desktop")


def konsole_layout(node):
    """A Konsole layout file's tree for one tab."""
    if "children" not in node:
        return {"SessionRestoreId": 0, "WorkingDirectory": node.get("directory") or str(HOME)}
    return {"Orientation": "Horizontal" if node["horizontal"] else "Vertical",
            "Widgets": [konsole_layout(c) for c in node["children"]]}


def leaves(node):
    return [node] if "children" not in node else [leaf for c in node["children"] for leaf in leaves(c)]


def start(w, index):
    """Starts the program of a saved window; returns the Konsole tabs still
    to open in it (the first tab comes from the layout file)."""
    if key(w) == KONSOLE:
        tabs = w.get("konsole") or [{"directory": str(HOME), "profile": ""}]
        first = leaves(tabs[0])[0]
        command = ["konsole"]
        if first.get("profile"):
            command += ["--profile", first["profile"]]
        if "children" in tabs[0]:
            layout_file = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()) / ("cde-copper-layout-%d.json" % index)
            layout_file.write_text(json.dumps(konsole_layout(tabs[0])), encoding="utf-8")
            command += ["--layout", str(layout_file)]
        else:
            command += ["--workdir", first.get("directory") or str(HOME)]
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return tabs[1:]
    app = w.get("desktopFile")
    if app:
        subprocess.Popen(["gtk-launch", app.removesuffix(".desktop")], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    elif w.get("cls") and shutil.which(w["cls"].lower()):
        subprocess.Popen([w["cls"].lower()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    return []


def more_tabs(conn, pid, tabs):
    """Further Konsole tabs, one per view (their splits are not rebuilt)."""
    if not tabs:
        return
    service = "org.kde.konsole-%d" % pid
    for _ in range(20):
        if call(conn, service, "/Windows/1", "org.kde.konsole.Window", "sessionCount") is not None:
            break
        time.sleep(0.25)
    first = call(conn, service, "/Windows/1", "org.kde.konsole.Window", "currentSession")
    for tab in tabs:
        for leaf in leaves(tab):
            call(conn, service, "/Windows/1", "org.kde.konsole.Window", "newSession", "(ss)",
                 (leaf.get("profile") or "", leaf.get("directory") or str(HOME)))
    if first:
        call(conn, service, "/Windows/1", "org.kde.konsole.Window", "setCurrentSession", "(i)", (first[0],))


def restore(layout_id):
    folder = STORE / layout_id
    layout = json.loads((folder / "layout.json").read_text(encoding="utf-8"))
    windows = layout["windows"]
    conn = bus()
    with KWinSession(conn) as session:
        state = {}
        session.load(RESTORE % json.dumps(layout))
        session.wait(lambda m: m.get("kind") == "missing" and state.update(m) is None, 8)
        for index in state.get("indices", []):
            tabs = start(windows[index], index)
            done = {}
            session.wait(lambda m: m.get("kind") == "placed" and m.get("index") == index
                         and done.update(m) is None, 10)
            if done and tabs:
                more_tabs(conn, done["pid"], tabs)
        # Late resizes of the last windows are still held for a moment.
        time.sleep(3)


def listing():
    result = []
    if STORE.is_dir():
        for folder in STORE.iterdir():
            try:
                layout = json.loads((folder / "layout.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            image = folder / "screen.png"
            result.append({"id": folder.name, "name": layout.get("name", folder.name),
                           "created": layout.get("created", 0), "windows": len(layout.get("windows", [])),
                           "apps": summary(layout.get("windows", [])),
                           "image": str(image) if image.is_file() else ""})
    result.sort(key=lambda item: -item["created"])
    print(json.dumps(result, ensure_ascii=False))


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    action = argv[1]
    if action == "list":
        listing()
    elif action == "save":
        options = dict(zip(argv[2::2], argv[3::2]))
        save(options.get("--title", "Save Layout"), options.get("--label", "Name of the layout:"), options.get("--name"))
    elif action in ("restore", "delete") and len(argv) == 3 and re.fullmatch(r"[\w.-]+", argv[2]):
        if action == "restore":
            restore(argv[2])
        else:
            shutil.rmtree(STORE / argv[2], ignore_errors=True)
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except RuntimeError as error:
        print("layouts.py:", error, file=sys.stderr)
        sys.exit(1)
