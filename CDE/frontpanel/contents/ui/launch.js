// Launcher slots and the commands behind them.
//
// A slot is {label, icon, command, menu}. command is either a token that
// follows the desktop's own choice of application, an installed
// application ("app:<desktop id>"), or a shell command. menu names the
// subpanel the slot's arrow opens.
.pragma library

const LEFT = [
    {label: "Apps", icon: "cde-menu", command: "@applications", menu: "applications"},
    {label: "Files", icon: "folder", command: "@pcmanfm", menu: "places"},
    {label: "Terminal", icon: "utilities-terminal", command: "@terminal", menu: "terminals"},
    {label: "Editor", icon: "accessories-text-editor", command: "@editor", menu: "recent"}
];
const RIGHT = [
    {label: "Web", icon: "internet-web-browser", command: "@browser", menu: "bookmarks"},
    {label: "Mail", icon: "internet-mail", command: "@mail", menu: "mail"},
    {label: "System", icon: "preferences-system", command: "@settings", menu: "system"},
    {label: "Layouts", icon: "preferences-system-windows", command: "@layouts", menu: "layouts"},
    {label: "Trash", icon: "user-trash", command: "@trash", menu: ""}
];

// Shown in the settings, in this order.
const PRESETS = [
    {text: "Default web browser", value: "@browser", icon: "internet-web-browser"},
    {text: "Default mail client", value: "@mail", icon: "internet-mail"},
    {text: "Default file manager", value: "@files", icon: "folder"},
    {text: "PCManFM (follows the Motif style best)", value: "@pcmanfm", icon: "system-file-manager"},
    {text: "XFile (Motif, as CDE's dtfile)", value: "@xfile", icon: "system-file-manager"},
    {text: "Terminal", value: "@terminal", icon: "utilities-terminal"},
    {text: "Default text editor", value: "@editor", icon: "accessories-text-editor"},
    {text: "Calendar", value: "@calendar", icon: "view-calendar"},
    {text: "System Settings", value: "@settings", icon: "preferences-system"},
    {text: "Trash", value: "@trash", icon: "user-trash"},
    {text: "Help Center", value: "@help", icon: "help-browser"},
    {text: "Saved layouts", value: "@layouts", icon: "preferences-system-windows"},
    {text: "Applications menu", value: "@applications", icon: "cde-menu"},
    {text: "Arrange windows around the console", value: "@arrange", icon: "view-split-left-right"},
    {text: "Installed application…", value: "app:", icon: "application-x-executable"},
    {text: "Custom command…", value: "", icon: "system-run"}
];

const MENUS = [
    {text: "None", value: ""},
    {text: "Applications", value: "applications"},
    {text: "Places", value: "places"},
    {text: "System", value: "system"},
    {text: "Help", value: "help"},
    {text: "Mail", value: "mail"},
    {text: "Terminals", value: "terminals"},
    {text: "Layouts", value: "layouts"},
    {text: "Bookmarks", value: "bookmarks"},
    {text: "Recent files", value: "recent"}
];

// The subpanel that suits a program, for the settings page.
function menuFor(command) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token === "@browser") return "bookmarks";
    if (token === "@mail") return "mail";
    if (token === "@terminal") return "terminals";
    if (token === "@layouts") return "layouts";
    if (token === "@editor" || token.indexOf("app:") === 0) return "recent";
    if (token === "@files" || token === "@pcmanfm" || token === "@xfile" || token === "@trash") return "places";
    if (token === "@settings") return "system";
    if (token === "@help") return "help";
    if (token === "@applications") return "applications";
    return "";
}

function parse(json, fallback) {
    if (!json)
        return fallback.map(slot => Object.assign({}, slot));
    try {
        const list = JSON.parse(json);
        if (Array.isArray(list))
            return list.filter(s => s && typeof s === "object").map(s => ({
                label: String(s.label || ""), icon: String(s.icon || "application-x-executable"),
                command: String(s.command || ""), menu: String(s.menu || "")}));
    } catch (e) {
        console.warn("CDE console: unreadable launcher list, using defaults:", e);
    }
    return fallback.map(slot => Object.assign({}, slot));
}

function presetFor(command) {
    if (command.indexOf("app:") === 0)
        return "app:";
    const head = command.split(" ")[0];
    return PRESETS.some(p => p.value === head && p.value !== "") ? head : "";
}

function quote(s) {
    return "'" + String(s).replace(/\x27/g, "'\\''") + "'";
}

// One argument for the shell: "~/x" expands to the home directory and
// "xdg:DOCUMENTS" to the user's (localised) documents folder.
function argument(s) {
    if (s.indexOf("xdg:") === 0)
        return "\"$(xdg-user-dir " + s.substring(4).replace(/[^A-Z]/g, "") + ")\"";
    if (s === "~" || s.indexOf("~/") === 0)
        return "\"$HOME\"" + (s.length > 1 ? quote(s.substring(1)) : "");
    return quote(s);
}

// What each token starts: the desktop's default for a MIME type or URL
// scheme (System Settings › Default Applications), then installed
// fallbacks in order. "$@" stands for the slot's arguments.
const TOKENS = {
    "@browser": {what: "A web browser", query: "xdg-settings get default-web-browser",
                 programs: ["firefox", "chromium-browser", "chromium", "google-chrome", "falkon", "konqueror"]},
    "@mail": {what: "A mail client", query: "xdg-mime query default x-scheme-handler/mailto",
              programs: ["kmail", "thunderbird", "evolution"]},
    "@files": {what: "A file manager", query: "xdg-mime query default inode/directory",
               programs: ["dolphin", "pcmanfm-qt", "nautilus", "thunar", "xdg-open"], home: true},
    // The console's file manager: PCManFM-Qt takes the Kvantum controls,
    // the GTK PCManFM the GTK theme; without either the desktop's default.
    "@pcmanfm": {what: "PCManFM", programs: ["pcmanfm-qt", "pcmanfm", "dolphin", "xdg-open"], home: true},
    "@xfile": {what: "XFile", programs: ["xfile"], home: true},
    "@trash": {what: "A file manager", query: "xdg-mime query default inode/directory",
               programs: ["dolphin", "kioclient exec"], fixed: "trash:/"},
    "@editor": {what: "A text editor", query: "xdg-mime query default text/plain",
                programs: ["kate", "kwrite", "gnome-text-editor", "gedit", "mousepad", "featherpad"]},
    "@terminal": {what: "A terminal", terminal: true,
                  programs: ["konsole --profile 'CDE Copper'", "xdg-terminal-exec", "gnome-terminal", "xterm"]},
    "@calendar": {what: "A calendar application",
                  programs: ["merkuro-calendar", "korganizer", "gnome-calendar", "thunderbird -calendar"]},
    "@contacts": {what: "An address book",
                  programs: ["kaddressbook", "merkuro-contact", "gnome-contacts", "thunderbird -addressbook"]},
    "@settings": {what: "System Settings", programs: ["systemsettings"]},
    "@help": {what: "Help Center", programs: ["khelpcenter", "xdg-open https://docs.kde.org"]}
};

// A missing program is reported as a desktop notification instead of
// failing silently.
function missing(what, translate) {
    const title = translate("%1 is not installed", what);
    const body = translate("Choose another program in the console settings (right-click › Configure).");
    return "notify-send -a " + quote(translate("CDE Front Console")) + " -i dialog-warning " + quote(title)
        + " " + quote(body) + " 2>/dev/null"
        + " || kdialog --passivepopup " + quote(title) + " 8";
}

function binary(program) {
    return program.split(" ")[0];
}

// Shell for one token: default handler, else the first installed fallback.
// With probe set, nothing is started; it prints ok or missing instead.
function chain(token, args, probe, translate) {
    const spec = TOKENS[token];
    args = spec.fixed || args || (spec.home ? "\"$HOME\"" : "");
    let shell = "";
    if (spec.query) {
        const desktop = probe ? "true" : "gtk-launch \"$id\" " + args + " 2>/dev/null || kstart --application \"$id\" " + args + " 2>/dev/null";
        shell += "id=$(" + spec.query + " 2>/dev/null); if [ -n \"$id\" ] && { " + desktop + "; }; then " + (probe ? "echo ok" : ":") + "; ";
    }
    if (spec.terminal) {
        // Plasma's configured terminal first; Konsole gets the theme's profile.
        shell += "t=$(kreadconfig6 --group General --key TerminalApplication 2>/dev/null); t=${t:-konsole}; "
            + "if [ \"${t##*/}\" != konsole ] && command -v \"${t%% *}\" >/dev/null 2>&1; then " + (probe ? "echo ok" : "$t " + args) + "; ";
    }
    spec.programs.forEach((program, i) => {
        const keyword = shell === "" && i === 0 ? "if" : "elif";
        shell += keyword + " command -v " + binary(program) + " >/dev/null 2>&1; then " + (probe ? "echo ok" : program + " " + args) + "; ";
    });
    return shell + "else " + (probe ? "echo missing" : missing(spec.what === "XFile" ? spec.what : translate(spec.what), translate)) + "; fi";
}

// The shell command for a slot command. "@applications" is handled by the
// console itself and never reaches this.
// extra: further arguments taken literally (a bookmark's URL, a file path
// with spaces); they are quoted, not split.
// The D-Bus caller under the names distributions give it; a shell
// expression, so resolve() and check() take it as such, not as a program.
const DBUS = "$(command -v qdbus6 || command -v qdbus-qt6 || command -v qdbus)";

function resolve(command, extra, translate) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token.indexOf("$(") === 0)
        return command + ((extra || []).length ? " " + extra.map(quote).join(" ") : "");
    const rest = command.trim().substring(token.length).trim();
    const words = (rest ? rest.split(/\s+/).map(argument) : []).concat((extra || []).map(quote));
    const args = words.join(" ");
    if (TOKENS[token])
        return chain(token, args, false, translate);
    if (token === "@terminals")
        return terminalSet(rest, translate);
    if (token === "@arrange")
        return DBUS + " org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut 'CDE Copper: Arrange Around Console'";
    if (token.indexOf("app:") === 0) {
        const id = quote(token.substring(4));
        return "gtk-launch " + id + " " + args + " 2>/dev/null || kstart --application " + id + " " + args + " 2>/dev/null || "
            + missing(translate("The application %1", token.substring(4)), translate);
    }
    // A custom command: check its program before running it.
    const full = command + ((extra || []).length ? " " + extra.map(quote).join(" ") : "");
    return "if command -v " + quote(token) + " >/dev/null 2>&1; then " + full + "; else " + missing(token, translate) + "; fi";
}

// Terminal sets ("@terminals three|four|seven"): the window arrangement
// script is told which set comes, then the Konsole windows start in the
// order of its places. "split" is one window holding two terminals side by
// side, from a Konsole layout file.
const TERMINAL_SETS = {
    three: {shortcut: "CDE Copper: Three Terminals", windows: ["plain", "plain", "plain"]},
    four: {shortcut: "CDE Copper: Four Terminals", windows: ["split", "plain", "plain"]},
    seven: {shortcut: "CDE Copper: Seven Terminals", windows: ["plain", "plain", "plain", "split", "plain", "plain"]}
};
const SPLIT_LAYOUT = '{"Orientation": "Horizontal", "Widgets": [{"SessionRestoreId": 0}, {"SessionRestoreId": 0}]}';

function terminalSet(kind, translate) {
    const set = TERMINAL_SETS[kind] || TERMINAL_SETS.three;
    const konsole = "konsole --profile 'CDE Copper'";
    const starts = set.windows.map(w => (w === "split" ? konsole + " --layout \"$layout\"" : konsole) + " & sleep 0.3").join("; ");
    return "if command -v konsole >/dev/null 2>&1; then "
        + "layout=\"${XDG_RUNTIME_DIR:-/tmp}/cde-copper-split.json\"; printf '%s' " + quote(SPLIT_LAYOUT) + " > \"$layout\"; "
        + DBUS + " org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut " + quote(set.shortcut) + "; "
        + starts + "; "
        + "else " + missing("Konsole", translate) + "; fi";
}

// For the settings page: prints ok when something can run the command.
function check(command) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token === "") return "echo missing";
    if (token === "@terminals") return "command -v konsole >/dev/null 2>&1 && echo ok || echo missing";
    if (token === "@applications" || token === "@layouts" || token === "@arrange" || token.indexOf("$(") === 0) return "echo ok";
    if (TOKENS[token]) return chain(token, "", true);
    if (token.indexOf("app:") === 0) {
        const file = quote(token.substring(4).replace(/\.desktop$/, "") + ".desktop");
        return "for d in \"${XDG_DATA_HOME:-$HOME/.local/share}\" $(echo \"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}\" | tr : ' ') /var/lib/flatpak/exports/share; do "
            + "[ -f \"$d/applications/\"" + file + " ] && { echo ok; exit 0; }; done; echo missing";
    }
    return "command -v " + quote(token) + " >/dev/null 2>&1 && echo ok || echo missing";
}

// Detach from the executable data engine, which waits for its process.
// KillMode=process: gtk-launch and kstart hand the program over and exit at
// once; with systemd's default the program would be killed with them as the
// rest of the unit's control group.
// systemd expands ${NAME} in the command line itself (an unknown name to
// nothing, as "${f#$p/}" or "${XDG_RUNTIME_DIR:-/tmp}"); "$$" is its
// literal dollar, so the shell gets the script as written.
function detached(shell) {
    const script = "[ -n \"$DISPLAY$WAYLAND_DISPLAY\" ] && [ -n \"$DBUS_SESSION_BUS_ADDRESS\" ] || exit 0; " + shell;
    return "systemd-run --user --collect --quiet -p KillMode=process -- sh -c "
        + quote(script.replace(/\$/g, "$$$$"));
}

// Translate shipped labels at presentation time; keep user labels and app names.
function slotLabel(slot, translate) {
    // A shipped label stays one when the tile gets another program (Files
    // with XFile, say); anything typed by the user is kept as it is.
    const preset = LEFT.concat(RIGHT).find(p => p.label === slot.label);
    return preset ? translate(slot.label) : slot.label;
}

// Dropping onto a tile (DropTarget.qml).

// What a tile does with dropped files: "open" passes them to its program,
// "folder" opens their folders, "terminal" starts a terminal in the first
// one's folder, "trash" moves them to the trash; "" takes no files.
function fileAction(command) {
    const token = String(command || "").trim().split(/\s+/)[0] || "";
    if (token === "@trash") return "trash";
    if (token === "@files" || token === "@pcmanfm" || token === "@xfile") return "folder";
    if (token === "@terminal") return "terminal";
    if (token === "@editor" || token === "@browser" || token.indexOf("app:") === 0) return "open";
    // Other tokens, D-Bus expressions and the console's own menus take none.
    if (token === "" || token.charAt(0) === "@" || token.indexOf("$(") === 0) return "";
    return "open";
}

// A local file's path for file: URLs (percent-decoded), anything else as
// the URL itself; "" for a file URL on another host.
function localPath(url) {
    const s = String(url);
    const m = /^file:\/\/([^/]*)(\/.*)$/.exec(s);
    if (!m) return s.indexOf("file:") === 0 ? "" : s;
    if (m[1] !== "" && m[1] !== "localhost") return "";
    try { return decodeURIComponent(m[2]); } catch (e) { return ""; }
}

// The shell for files dropped on a slot, "" when the slot takes none.
function dropCommand(command, urls, translate) {
    const action = fileAction(command);
    const list = (urls || []).map(String).filter(u => u !== "");
    if (action === "" || list.length === 0) return "";
    if (action === "trash")
        return "if command -v kioclient >/dev/null 2>&1; then kioclient move " + list.map(quote).join(" ") + " trash:/; "
            + "elif command -v gio >/dev/null 2>&1; then gio trash -- " + list.map(quote).join(" ") + "; "
            + "else " + missing("kioclient", translate) + "; fi";
    const local = list.map(localPath);
    if (action === "open") {
        const args = local.filter(p => p !== "");
        return args.length ? resolve(command, args, translate) : "";
    }
    // Folders and terminals: local paths only, a file stands for its folder.
    const paths = local.filter(p => p.charAt(0) === "/");
    if (paths.length === 0) return "";
    const token = command.trim().split(/\s+/)[0];
    if (action === "terminal")
        return "d=" + quote(paths[0]) + "; [ -d \"$d\" ] || d=$(dirname -- \"$d\"); cd -- \"$d\" && { "
            + chain(token, "", false, translate) + "; }";
    // Files from one folder come one after the other: open it once.
    return "set --; last=; for p in " + paths.map(quote).join(" ") + "; do [ -d \"$p\" ] || p=$(dirname -- \"$p\"); "
        + "[ \"$p\" = \"$last\" ] && continue; last=$p; set -- \"$@\" \"$p\"; done; "
        + chain(token, "\"$@\"", false, translate);
}

// The desktop id of an application entry: "applications:<id>.desktop", or
// a desktop file under an applications directory (subdirectories joined
// with "-", as the Desktop Entry spec has it). "" for anything else, so a
// .desktop file elsewhere is treated as a plain file.
function desktopId(url) {
    const s = String(url);
    if (s.indexOf("applications:") === 0)
        return s.substring(13).replace(/^\/+/, "").replace(/\.desktop$/, "");
    const path = localPath(s);
    const m = /\/applications\/(.+)\.desktop$/.exec(path);
    return path.charAt(0) === "/" && m ? m[1].split("/").join("-") : "";
}

// Shell printing the [Desktop Entry] lines of an application by id.
function desktopEntryQuery(id) {
    const file = quote(id.split("-").join("/") + ".desktop");
    const flat = quote(id + ".desktop");
    return "for d in \"${XDG_DATA_HOME:-$HOME/.local/share}\" $(echo \"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}\" | tr : ' ') /var/lib/flatpak/exports/share; do "
        + "for f in \"$d/applications/\"" + flat + " \"$d/applications/\"" + file + "; do "
        + "[ -f \"$f\" ] && { sed -n '/^\\[Desktop Entry\\]/,/^\\[/p' \"$f\" | grep -E '^(Name(\\[[^]]*\\])?|Icon)='; exit 0; }; done; done";
}

// The slot an application dropped on a tile becomes: name (first word, as
// the settings page does) and icon from its desktop entry, in the user's
// language (locale as "de_DE"); the old slot's mail menu is kept.
function desktopSlot(id, entry, locale, old) {
    const values = {};
    String(entry || "").split("\n").forEach(line => {
        const i = line.indexOf("=");
        if (i > 0 && !(line.substring(0, i) in values)) values[line.substring(0, i)] = line.substring(i + 1).trim();
    });
    const lang = String(locale || "").split(".")[0];
    const name = values["Name[" + lang + "]"] || values["Name[" + lang.split("_")[0] + "]"] || values.Name || id;
    return {label: name.split(" ")[0], icon: values.Icon || "application-x-executable",
            command: "app:" + id, menu: old && old.menu === "mail" ? "mail" : "recent"};
}

// The two launcher lists after a tile moved, possibly to the other side:
// it takes the place of the tile it was dropped on. Returns {left, right}
// as new arrays; the inputs are left alone.
function moved(left, right, fromSide, fromIndex, toSide, toIndex) {
    const lists = {left: left.slice(), right: right.slice()};
    const from = lists[fromSide], to = lists[toSide];
    if (!from || !to || fromIndex < 0 || fromIndex >= from.length) return lists;
    const item = from.splice(fromIndex, 1)[0];
    to.splice(Math.max(0, Math.min(toIndex, to.length)), 0, item);
    return lists;
}

// One slot replaced; a new array.
function replaced(list, index, slot) {
    const result = list.slice();
    if (index >= 0 && index < result.length) result[index] = Object.assign({}, slot);
    return result;
}

// The configuration text for a launcher list (leftLaunchers,
// rightLaunchers), in the form parse() reads.
function serialize(list) {
    return JSON.stringify(list.map(s => ({label: String(s.label || ""), icon: String(s.icon || ""),
                                          command: String(s.command || ""), menu: String(s.menu || "")})));
}

// The drag payload of a tile being moved: "left:2".
const TILE_MIME = "application/x-cde-copper-launcher";
function tileRef(side, index) {
    return side + ":" + index;
}
function parseTileRef(text) {
    const m = /^(left|right):(\d+)$/.exec(String(text || ""));
    return m ? {side: m[1], index: Number(m[2])} : null;
}

// Extraction-only markers for strings translated by the QML caller.
function I18N_NOOP(text) { return text; }
const TRANSLATABLE_STRINGS = [
    I18N_NOOP("Apps"),
    I18N_NOOP("Files"),
    I18N_NOOP("Terminal"),
    I18N_NOOP("Editor"),
    I18N_NOOP("Web"),
    I18N_NOOP("Mail"),
    I18N_NOOP("System"),
    I18N_NOOP("Help"),
    I18N_NOOP("Trash"),
    I18N_NOOP("Default web browser"),
    I18N_NOOP("Default mail client"),
    I18N_NOOP("Default file manager"),
    I18N_NOOP("PCManFM (follows the Motif style best)"),
    I18N_NOOP("XFile (Motif, as CDE's dtfile)"),
    I18N_NOOP("Default text editor"),
    I18N_NOOP("Calendar"),
    I18N_NOOP("System Settings"),
    I18N_NOOP("Help Center"),
    I18N_NOOP("Applications menu"),
    I18N_NOOP("Arrange windows around the console"),
    I18N_NOOP("Installed application…"),
    I18N_NOOP("Custom command…"),
    I18N_NOOP("None"),
    I18N_NOOP("Applications"),
    I18N_NOOP("Places"),
    I18N_NOOP("Bookmarks"),
    I18N_NOOP("Terminals"),
    I18N_NOOP("Layouts"),
    I18N_NOOP("Saved layouts"),
    I18N_NOOP("Recent files"),
    I18N_NOOP("A web browser"),
    I18N_NOOP("A mail client"),
    I18N_NOOP("A file manager"),
    I18N_NOOP("A text editor"),
    I18N_NOOP("A terminal"),
    I18N_NOOP("A calendar application"),
    I18N_NOOP("An address book"),
    I18N_NOOP("%1 is not installed"),
    I18N_NOOP("Choose another program in the console settings (right-click › Configure)."),
    I18N_NOOP("CDE Front Console"),
    I18N_NOOP("The application %1")
];
