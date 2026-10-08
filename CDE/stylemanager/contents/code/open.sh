#!/bin/sh
# Open the style manager, or bring its window forward if it is open:
# plasmawindowed runs once and ignores being started again.
applet=org.cde.copper.stylemanager
pid=$(pgrep -u "$(id -u)" -f "plasmawindowed $applet" | head -n 1)
[ -n "$pid" ] || exec plasmawindowed "$applet"
qdbus=$(command -v qdbus6 || command -v qdbus-qt6 || command -v qdbus) || exit 0
script=$(mktemp --suffix=.js) || exit 0
trap 'rm -f "$script"' EXIT
# To this workspace, out of the taskbar's minimised ones, and active.
cat > "$script" <<END
for (const w of workspace.windowList()) {
    if (w.pid !== $pid || !w.normalWindow) continue;
    w.minimized = false;
    if (!w.onAllDesktops) w.desktops = [workspace.currentDesktop];
    workspace.activeWindow = w;
}
END
name="cde-copper-raise-$$"
id=$("$qdbus" org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$script" "$name") || exit 0
"$qdbus" org.kde.KWin "/Scripting/Script$id" org.kde.kwin.Script.run
sleep 1
"$qdbus" org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null
