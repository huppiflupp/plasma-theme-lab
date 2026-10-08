#!/usr/bin/env python3
"""Which running programs still show the old style after a palette change.

    stale.py PID...  ->  JSON {"PID": "live" | "restart" | "own", ...}

manage.py brings running programs along where it can: KDE programs get a
fresh Kvantum style and the new colours (refresh_running_windows), GTK 3
programs reload the GTK theme when its name changes (update_gtk). Everything
else keeps what it loaded at start:

  live     follows at once (Qt with KDE's platform theme, GTK 3)
  restart  takes the new style when started again (Qt without KDE's
           platform theme, GTK 4, Chromium and Electron, X11 and Motif
           programs, Java, unknown toolkits)
  own      keeps its own look either way (Flatpak sandboxes, libadwaita)

The toolkit is read from the libraries a process has mapped
(/proc/PID/maps); a process that cannot be read counts as "restart".
"""
import json
import os
from pathlib import Path
import sys

PROC = Path(os.environ.get("CDE_COPPER_PROC", "/proc"))


def libraries(pid):
    names = set()
    with open(PROC / str(pid) / "maps", errors="replace") as maps:
        for line in maps:
            path = line.rstrip("\n").split(None, 5)[5:]
            if path and path[0].startswith("/"):
                names.add(os.path.basename(path[0]))
    return names


def kind(pid):
    root = PROC / str(pid)
    try:
        if (root / "root/.flatpak-info").exists():
            return "own"
        libs = libraries(pid)
        exe = os.path.basename(os.readlink(root / "exe")) if (root / "exe").is_symlink() else ""
    except OSError:
        return "restart"
    has = lambda prefix: any(name.startswith(prefix) for name in libs)
    if has("libadwaita-1"):
        return "own"
    # Chromium and Electron map GTK too, but read its theme only at start.
    if has("libcef") or has("libelectron") or "chrom" in exe or "electron" in exe:
        return "restart"
    if has("KDEPlasmaPlatformTheme"):
        return "live"
    if has("libQt6Gui") or has("libQt5Gui"):
        return "restart"
    if has("libgtk-3."):
        return "live"
    return "restart"


def main(args):
    print(json.dumps({pid: kind(int(pid)) for pid in args if pid.isdigit()}))


if __name__ == "__main__":
    main(sys.argv[1:])
