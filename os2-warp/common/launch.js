// Launchers and the commands behind them.
//
// Copied from CDE/frontpanel/contents/ui/launch.js (CDE Copper 1.0.0,
// 43c53c15) and cut down to what the LaunchPad needs: the tokens that
// follow the desktop's own choice of program, installed applications
// ("app:<desktop id>"), shell commands, and starting them detached. CDE's
// terminal sets, layouts and drop handling are not taken over.
//
// A launcher is {label, icon, command, drawer}; drawer is a list of
// launchers without drawers of their own. Shared by the LaunchPad and the
// Warp Bar (build.py copies it into both).
.pragma library

// After Warp 3's LaunchPad (drives, OS/2 window, help, shredder), in
// today's terms.
const DEFAULTS = [
    {label: "Files", icon: "system-file-manager", command: "@files", drawer: [
        {label: "Home", icon: "user-home", command: "@files ~"},
        {label: "Documents", icon: "folder-documents", command: "@files xdg:DOCUMENTS"},
        {label: "Downloads", icon: "folder-download", command: "@files xdg:DOWNLOAD"},
        {label: "Pictures", icon: "folder-pictures", command: "@files xdg:PICTURES"}]},
    {label: "Terminal", icon: "utilities-terminal", command: "@terminal", drawer: [
        {label: "Text Editor", icon: "accessories-text-editor", command: "@editor"},
        {label: "System Settings", icon: "preferences-system", command: "@settings"}]},
    {label: "Web", icon: "internet-web-browser", command: "@browser", drawer: [
        {label: "Mail", icon: "internet-mail", command: "@mail"}]},
    {label: "Help", icon: "help-browser", command: "@help", drawer: []},
    {label: "Trash", icon: "user-trash", command: "@trash", drawer: []}
];

function entry(s) {
    return {label: String(s.label || ""), icon: String(s.icon || "application-x-executable"),
            command: String(s.command || "")};
}

function parse(json, fallback) {
    fallback = fallback || DEFAULTS;
    if (json) {
        try {
            const list = JSON.parse(json);
            if (Array.isArray(list))
                return list.filter(s => s && typeof s === "object").map(s => Object.assign(entry(s), {
                    drawer: Array.isArray(s.drawer) ? s.drawer.filter(d => d && typeof d === "object").map(entry) : []}));
        } catch (e) {
            console.warn("LaunchPad: unreadable launcher list, using defaults:", e);
        }
    }
    return fallback.map(s => Object.assign(entry(s), {drawer: (s.drawer || []).map(entry)}));
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
// fallbacks in order.
const TOKENS = {
    "@browser": {what: "A web browser", query: "xdg-settings get default-web-browser",
                 programs: ["firefox", "chromium-browser", "chromium", "google-chrome", "falkon", "konqueror"]},
    "@mail": {what: "A mail client", query: "xdg-mime query default x-scheme-handler/mailto",
              programs: ["kmail", "thunderbird", "evolution"]},
    "@files": {what: "A file manager", query: "xdg-mime query default inode/directory",
               programs: ["dolphin", "pcmanfm-qt", "nautilus", "thunar", "xdg-open"], home: true},
    "@trash": {what: "A file manager", query: "xdg-mime query default inode/directory",
               programs: ["dolphin", "kioclient exec"], fixed: "trash:/"},
    "@editor": {what: "A text editor", query: "xdg-mime query default text/plain",
                programs: ["kate", "kwrite", "gnome-text-editor", "gedit", "mousepad", "featherpad"]},
    "@terminal": {what: "A terminal", terminal: true,
                  programs: ["konsole", "xdg-terminal-exec", "gnome-terminal", "xterm"]},
    "@settings": {what: "System Settings", programs: ["systemsettings"]},
    "@help": {what: "Help Center", programs: ["khelpcenter", "xdg-open https://docs.kde.org"]}
};

// A missing program is reported as a desktop notification instead of
// failing silently.
function missing(what, translate) {
    const title = translate("%1 is not installed", what);
    const body = translate("Choose another program in the LaunchPad settings (right-click › Configure).");
    return "notify-send -a " + quote(translate("LaunchPad")) + " -i dialog-warning " + quote(title)
        + " " + quote(body) + " 2>/dev/null"
        + " || kdialog --passivepopup " + quote(title) + " 8";
}

function binary(program) {
    return program.split(" ")[0];
}

// Shell for one token: default handler, else the first installed fallback.
function chain(token, args, translate) {
    const spec = TOKENS[token];
    args = spec.fixed || args || (spec.home ? "\"$HOME\"" : "");
    let shell = "";
    if (spec.query)
        shell += "id=$(" + spec.query + " 2>/dev/null); if [ -n \"$id\" ] && { gtk-launch \"$id\" " + args
            + " 2>/dev/null || kstart --application \"$id\" " + args + " 2>/dev/null; }; then :; ";
    if (spec.terminal)
        // Plasma's configured terminal first.
        shell += "t=$(kreadconfig6 --group General --key TerminalApplication 2>/dev/null); t=${t:-konsole}; "
            + "if command -v \"${t%% *}\" >/dev/null 2>&1; then $t " + args + "; ";
    spec.programs.forEach((program, i) => {
        const keyword = shell === "" && i === 0 ? "if" : "elif";
        shell += keyword + " command -v " + binary(program) + " >/dev/null 2>&1; then " + program + " " + args + "; ";
    });
    return shell + "else " + missing(translate(spec.what), translate) + "; fi";
}

// The D-Bus caller under the names distributions give it.
const DBUS = "$(command -v qdbus6 || command -v qdbus-qt6 || command -v qdbus)";

// The shell command for a launcher command.
function resolve(command, translate) {
    const token = command.trim().split(/\s+/)[0] || "";
    if (token.indexOf("$(") === 0)
        return command;
    const rest = command.trim().substring(token.length).trim();
    const args = (rest ? rest.split(/\s+/).map(argument) : []).join(" ");
    if (TOKENS[token])
        return chain(token, args, translate);
    if (token.indexOf("app:") === 0) {
        const id = quote(token.substring(4));
        return "gtk-launch " + id + " " + args + " 2>/dev/null || kstart --application " + id + " " + args + " 2>/dev/null || "
            + missing(translate("The application %1", token.substring(4)), translate);
    }
    return "if command -v " + quote(token) + " >/dev/null 2>&1; then " + command + "; else " + missing(token, translate) + "; fi";
}

// Detach from the executable data engine, which waits for its process
// (KillMode=process: gtk-launch and kstart hand over and exit at once).
// "$$" is systemd's literal dollar.
function detached(shell) {
    const script = "[ -n \"$DISPLAY$WAYLAND_DISPLAY\" ] && [ -n \"$DBUS_SESSION_BUS_ADDRESS\" ] || exit 0; " + shell;
    return "systemd-run --user --collect --quiet -p KillMode=process -- sh -c "
        + quote(script.replace(/\$/g, "$$$$"));
}

// The desktop id of a task's launcher URL ("applications:<id>.desktop" or a
// desktop file under an applications directory).
function desktopId(url) {
    const s = String(url);
    if (s.indexOf("applications:") === 0)
        return s.substring(13).replace(/^\/+/, "").replace(/\.desktop$/, "");
    const m = /\/applications\/(.+)\.desktop$/.exec(s);
    return m ? m[1].split("/").join("-") : "";
}

// Shipped labels, for translation.
function I18N_NOOP(text) { return text; }
const TRANSLATABLE_STRINGS = [
    I18N_NOOP("Files"), I18N_NOOP("Home"), I18N_NOOP("Documents"), I18N_NOOP("Downloads"), I18N_NOOP("Pictures"),
    I18N_NOOP("Terminal"), I18N_NOOP("Text Editor"), I18N_NOOP("System Settings"), I18N_NOOP("Web"),
    I18N_NOOP("Mail"), I18N_NOOP("Help"), I18N_NOOP("Trash")
];
