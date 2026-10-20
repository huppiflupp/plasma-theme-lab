#!/usr/bin/env bash
# Set up the desktop of the user's Neon concept (reference/neon-2026.png)
# for screenshots: the column of desktop objects on the left, a project
# folder, and the windows where the concept has them. Run inside the
# Plasma session (the VM), after install.sh --apply. Adds files under the
# desktop folder and ~/Projekte, sets the desktop's icon layout (restarts
# plasmashell for that); the windows are ordinary ones.
#
#   ./demo-scene.sh            objects and windows
#   ./demo-scene.sh --objects  only the desktop objects
set -euo pipefail
mode=${1:-}
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
count=$(echo "$files" | wc -l)
avail=$(( ${res#*x} - 40 ))
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
    for _ in $(seq 30); do
        dbus-send --session --print-reply --dest=org.kde.plasmashell /PlasmaShell \
            org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 && break
        sleep 0.5
    done
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
