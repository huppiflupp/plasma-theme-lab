#!/usr/bin/env bash
# Set up the desktop of the user's Neon concept (reference/neon-2026.png)
# for screenshots: the column of desktop objects on the left, a project
# folder, and the windows where the concept has them. Run inside the
# Plasma session (the VM), after install.sh --apply. Adds files under the
# desktop folder and ~/Projekte, sets the desktop's icon layout (restarts
# plasmashell for that); the windows are ordinary ones. With --panels it
# first replaces all panels by one arrangement of Warp Legacy's (a demo:
# the old panels are not kept).
#
#   ./demo-scene.sh            objects and windows
#   ./demo-scene.sh --objects  only the desktop objects
#   ./demo-scene.sh --panels concept|classic|tabs [--objects]
#       concept  the Neon concept: Warp Taskbar at the bottom (32 px),
#                Control Strip as the compact box at the top right
#       classic  OS/2 Warp 4 with Object Desktop: Warp Bar along the top
#                (tray, clock), LaunchPad floating at the bottom centre,
#                Control Strip as the full strip on the right
#       tabs     as classic, plus the Tab Launcher at the bottom left
set -euo pipefail
mode= panels=
while [ $# -gt 0 ]; do
    case $1 in
        --objects) mode=--objects ;;
        --panels) panels=${2:-}; shift ;;
        --panels=*) panels=${1#*=} ;;
        *) echo "usage: $0 [--panels concept|classic|tabs] [--objects]" >&2; exit 2 ;;
    esac
    shift
done
case $panels in
    ''|concept|classic|tabs) ;;
    *) echo "unknown arrangement: $panels (concept, classic, tabs)" >&2; exit 2 ;;
esac
shell_up() {
    for _ in $(seq 30); do
        dbus-send --session --print-reply --dest=org.kde.plasmashell /PlasmaShell \
            org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 && return 0
        sleep 0.5
    done
    return 1
}

# The panels, as the page "Panels" of the plasmoids' settings adds them
# (common/PanelsPage.qml); the concept's taskbar at the user's 32 px, its
# compact box as the Control Strip shapes it itself (controlstrip main.qml).
if [ -n "$panels" ]; then
    js="panels().forEach(function(p) { p.remove(); });
function strip(layout) {
    var p = new Panel; p.screen = 0; p.location = 'right'; p.hiding = 'none';
    var w = p.addWidget('org.warplegacy.controlstrip');
    w.currentConfigGroup = ['General']; w.writeConfig('layout', layout);
    if (layout == 'compact') { p.lengthMode = 'fit'; p.alignment = 'left'; p.floating = true; p.height = 200; }
    else { p.lengthMode = 'fill'; p.floating = false; p.height = 130; }
}
function warpbar() {
    var p = new Panel; p.screen = 0; p.location = 'top'; p.height = 28; p.hiding = 'none'; p.floating = false;
    p.addWidget('org.warplegacy.warpbar'); p.addWidget('org.kde.plasma.panelspacer');
    p.addWidget('org.kde.plasma.systemtray'); p.addWidget('org.kde.plasma.digitalclock');
}
function launchpad() {
    var p = new Panel; p.screen = 0; p.location = 'bottom'; p.alignment = 'center'; p.lengthMode = 'fit';
    p.height = 76; p.hiding = 'none'; p.floating = true; p.addWidget('org.warplegacy.launchpad');
}
// Next to the LaunchPad (about 560 px wide, centred) the Tab Launcher's
// natural width (~790 px with all categories) runs under it; it gets the
// room left of the LaunchPad, its tab row scrolls anyway.
function tablauncher(beside) {
    var p = new Panel; p.screen = 0; p.location = 'bottom'; p.alignment = 'left'; p.lengthMode = 'fit';
    p.height = 112; p.hiding = 'none'; p.floating = true; p.addWidget('org.warplegacy.tablauncher');
    if (beside) {
        var room = Math.floor((screenGeometry(0).width - 600) / 2) - 24;
        p.lengthMode = 'custom'; p.minimumLength = room; p.maximumLength = room;
    }
}
function taskbar(height) {
    var p = new Panel; p.screen = 0; p.location = 'bottom'; p.height = height; p.hiding = 'none'; p.floating = false;
    p.addWidget('org.warplegacy.taskbar'); p.addWidget('org.kde.plasma.systemtray'); p.addWidget('org.kde.plasma.digitalclock');
}
"
    case $panels in
        concept) js="$js taskbar(32); strip('compact');" ;;
        classic) js="$js warpbar(); launchpad(); strip('strip');" ;;
        tabs)    js="$js warpbar(); tablauncher(true); launchpad(); strip('strip');" ;;
    esac
    systemctl --user is-active -q plasma-plasmashell.service \
        || systemctl --user start plasma-plasmashell.service
    shell_up || { echo "plasmashell does not answer" >&2; exit 1; }
    dbus-send --session --print-reply --type=method_call --dest=org.kde.plasmashell /PlasmaShell \
        org.kde.PlasmaShell.evaluateScript string:"$js" >/dev/null
    sleep 3
fi
DESKTOP=$(xdg-user-dir DESKTOP)
mkdir -p "$DESKTOP"

# The concept's column, top to bottom (numbered files keep the order).
entry() {   # entry <file> <name> <icon> <exec>
    cat > "$DESKTOP/$1.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$2
Icon=$3
Exec=$4
EOF
    chmod +x "$DESKTOP/$1.desktop"
}
link() {    # link <file> <name> <icon> <url>
    cat > "$DESKTOP/$1.desktop" <<EOF
[Desktop Entry]
Type=Link
Name=$2
Icon=$3
URL=$4
EOF
}
link  01-arbeitsplatz  "Arbeitsplatz"   user-desktop          "file://$DESKTOP"
link  02-computer      "Computer"       computer              "file:///"
link  03-netzwerk      "Netzwerk"       network-workgroup     "remote:/"
entry 04-internet      "Internet"       internet-web-browser  "firefox"
link  05-dateien       "Dateien"        folder                "file://$HOME"
entry 06-anwendungen   "Anwendungen"    applications-other    "krunner"
link  07-vorlagen      "Vorlagen"       folder-templates      "file://$(xdg-user-dir TEMPLATES)"
entry 08-einstellungen "Einstellungen"  preferences-system    "systemsettings"
entry 09-spiele        "Spiele"         applications-games    "kpat"
entry 10-herunterfahren "Herunterfahren" system-shutdown      "dbus-send --session --type=method_call --dest=org.kde.LogoutPrompt /LogoutPrompt org.kde.LogoutPrompt.promptShutDown"

# One column in this order. The folder view reads "positions" only at
# start and writes its own grid back on exit, so stop plasmashell, write
# the config, start it again.
appletsrc=~/.config/plasma-org.kde.plasma.desktop-appletsrc
res=$(kscreen-doctor -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' \
      | sed -n 's/.*Geometry: [0-9]*,[0-9]* \([0-9]*x[0-9]*\).*/\1/p' | head -1)
res=${res:-1280x800}
files=$(cd "$DESKTOP" && ls -1 [0-9][0-9]-*.desktop)
grid='"1","'$(echo "$files" | wc -l)'"'
row=0
for f in $files; do grid="$grid,\"desktop:/$f\",\"0\",\"$row\""; row=$((row + 1)); done
positions="{\"$res\":[$grid]}"
# Largest icons that still fit all objects in one column: Plasma's cell
# is icon + text lines * gridUnit (~18 px) + 12, below the 32 px taskbar.
# 48 px with two lines needs ~1080 px; at 800 px only 32 px, one line.
# The panels at the top and bottom edges take their height off; the
# Tab Launcher sits on the column itself.
count=$(echo "$files" | wc -l)
case $panels in
    classic) taken=118 ;;       # Warp Bar 28, LaunchPad 76 + its float
    tabs)    taken=158 ;;       # Warp Bar 28, Tab Launcher 112 + its float
    *)       taken=40 ;;
esac
avail=$(( ${res#*x} - taken ))
iconsize=1 textlines=1                          # 32 px
for c in "2 2 96" "2 1 78"; do                  # 48 px, two / one line
    set -- $c
    if [ $((avail / $3)) -ge "$count" ]; then iconsize=$1 textlines=$2; break; fi
done
set --
# Folder containments (the desktops), from the applets file.
ids=$(awk '/^\[Containments\]\[[0-9]+\]$/ { id = $0; gsub(/[^0-9]/, "", id) }
           /^plugin=org.kde.plasma.folder$/ && id != "" { print id }' "$appletsrc")
running=0
systemctl --user is-active -q plasma-plasmashell.service && running=1
if [ "$running" = 1 ]; then
    systemctl --user stop plasma-plasmashell.service
    sleep 1
fi
for id in $ids; do
    g=(--file "$appletsrc" --group Containments --group "$id" --group General)
    kwriteconfig6 "${g[@]}" --key sortMode -- -1
    kwriteconfig6 "${g[@]}" --key arrangement 1
    kwriteconfig6 "${g[@]}" --key iconSize "$iconsize"
    kwriteconfig6 "${g[@]}" --key textLines "$textlines"
    kwriteconfig6 "${g[@]}" --key positions "$positions"
done
if [ "$running" = 1 ]; then
    systemctl --user start plasma-plasmashell.service
    shell_up || true
    sleep 3
fi

# The concept's C:\Projects.
mkdir -p ~/Projekte/{Dokumente,Finanzen,Privat,Temp}
[ -f ~/Projekte/TODO.txt ] || printf 'Warp Legacy\n- Sperrbildschirm\n- Store-Paket\n' > ~/Projekte/TODO.txt

[ "${mode:-}" = "--objects" ] && exit 0

kwin() {
    dbus-send --session --print-reply --type=method_call --dest=org.kde.KWin /Scripting \
        "org.kde.kwin.Scripting.$1" "${@:2}" >/dev/null
}
kwin_run() {    # kwin_run <script file>: load under a fresh name, start, unload
    local name=warp-demo-scene-$(date +%s%N)
    kwin loadScript string:"$1" string:"$name"
    kwin start
    sleep 1
    kwin unloadScript string:"$name"
}

# The windows: one per program, so close what an earlier run left open.
# Closed through KWin first: a killed Firefox restores its old tabs.
progs='dolphin|konsole|systemsettings|firefox'
close=$(mktemp --suffix=.js)
cat > "$close" <<'EOF'
var list = workspace.windowList();
for (var i = 0; i < list.length; i++) {
    var w = list[i];
    if (w.normalWindow && /dolphin|konsole|systemsettings|firefox/i.test(String(w.resourceClass)))
        w.closeWindow();
}
EOF
kwin_run "$close"
rm -f "$close"
for _ in $(seq 20); do
    pgrep -x "$progs" >/dev/null || break
    sleep 0.5
done
pkill -x "$progs" 2>/dev/null || true
sleep 1
pkill -9 -x "$progs" 2>/dev/null || true
launch() { (setsid "$@" >/dev/null 2>&1 &); }
launch dolphin --new-window "$DESKTOP"
launch konsole --workdir "$HOME" --hold -e sh -c 'uname -srm; echo; lscpu | grep -E "^(Model name|CPU\(s\))"; free -h | head -2; echo; exec bash'
launch firefox --new-window about:blank
launch dolphin --new-window ~/Projekte
launch systemsettings
sleep 8

# Place them with demo-scene.js. Twice, for windows that came up late.
script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/demo-scene.js"
kwin_run "$script"
sleep 2
kwin_run "$script"
