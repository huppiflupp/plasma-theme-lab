// Launcher slots and the commands behind them.
//
// A slot is {label, icon, command, menu}. command is either a token that
// follows the desktop's own choice of application, an installed
// application ("app:<desktop id>"), or a shell command. menu names the
// subpanel the slot's arrow opens.
.pragma library

const LEFT = [
    {label: "Apps", icon: "cde-menu", command: "@applications", menu: "applications"},
    {label: "Files", icon: "folder", command: "@files", menu: "places"},
    {label: "Terminal", icon: "utilities-terminal", command: "@terminal", menu: ""},
    {label: "Editor", icon: "accessories-text-editor", command: "@editor", menu: "recent"}
];
const RIGHT = [
    {label: "Web", icon: "internet-web-browser", command: "@browser", menu: "bookmarks"},
    {label: "Mail", icon: "internet-mail", command: "@mail", menu: "mail"},
    {label: "System", icon: "preferences-system", command: "@settings", menu: "system"},
    {label: "Help", icon: "help-browser", command: "@help", menu: "help"},
    {label: "Trash", icon: "user-trash", command: "@trash", menu: ""}
];

// Shown in the settings, in this order.
const PRESETS = [
    {text: "Default web browser", value: "@browser", icon: "internet-web-browser"},
    {text: "Default mail client", value: "@mail", icon: "internet-mail"},
    {text: "Default file manager", value: "@files", icon: "folder"},
    {text: "XFile (Motif, as CDE's dtfile)", value: "@xfile", icon: "system-file-manager"},
    {text: "Terminal", value: "@terminal", icon: "utilities-terminal"},
    {text: "Default text editor", value: "@editor", icon: "accessories-text-editor"},
    {text: "Calendar", value: "@calendar", icon: "view-calendar"},
    {text: "System Settings", value: "@settings", icon: "preferences-system"},
    {text: "Trash", value: "@trash", icon: "user-trash"},
    {text: "Help Center", value: "@help", icon: "help-browser"},
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
    {text: "Bookmarks", value: "bookmarks"},
    {text: "Recent files", value: "recent"}
];

// The subpanel that suits a program, for the settings page.
function menuFor(command) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token === "@browser") return "bookmarks";
    if (token === "@mail") return "mail";
    if (token === "@editor" || token.indexOf("app:") === 0) return "recent";
    if (token === "@files" || token === "@xfile" || token === "@trash") return "places";
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
    return "'" + String(s).replace(/'/g, "'\\''") + "'";
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
function missing(what) {
    return "notify-send -a 'CDE Front Console' -i dialog-warning " + quote(what + " is not installed")
        + " 'Choose another program in the console settings (right-click › Configure).' 2>/dev/null"
        + " || kdialog --passivepopup " + quote(what + " is not installed") + " 8";
}

function binary(program) {
    return program.split(" ")[0];
}

// Shell for one token: default handler, else the first installed fallback.
// With probe set, nothing is started; it prints ok or missing instead.
function chain(token, args, probe) {
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
    return shell + "else " + (probe ? "echo missing" : missing(spec.what)) + "; fi";
}

// The shell command for a slot command. "@applications" is handled by the
// console itself and never reaches this.
// extra: further arguments taken literally (a bookmark's URL, a file path
// with spaces); they are quoted, not split.
function resolve(command, extra) {
    const token = command.trim().split(/\s+/)[0] || "";
    const rest = command.trim().substring(token.length).trim();
    const words = (rest ? rest.split(/\s+/).map(argument) : []).concat((extra || []).map(quote));
    const args = words.join(" ");
    if (TOKENS[token])
        return chain(token, args, false);
    if (token === "@arrange")
        return "qdbus-qt6 org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut 'CDE Copper: Arrange Around Console'";
    if (token.indexOf("app:") === 0) {
        const id = quote(token.substring(4));
        return "gtk-launch " + id + " " + args + " 2>/dev/null || kstart --application " + id + " " + args + " 2>/dev/null || "
            + missing("The application " + token.substring(4));
    }
    // A custom command: check its program before running it.
    const full = command + ((extra || []).length ? " " + extra.map(quote).join(" ") : "");
    return "if command -v " + quote(token) + " >/dev/null 2>&1; then " + full + "; else " + missing(token) + "; fi";
}

// For the settings page: prints ok when something can run the command.
function check(command) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token === "") return "echo missing";
    if (token === "@applications" || token === "@arrange") return "echo ok";
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
function detached(shell) {
    return "systemd-run --user --collect --quiet -p KillMode=process -- sh -c " + quote(shell);
}
