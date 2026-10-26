#!/usr/bin/env bash
# Take Warp Legacy back out: first the desktop as it was (the settings
# install.sh --apply recorded, the panels from before --layout, the global
# theme in use before), then the files install.sh recorded. Without a
# record the desktop falls back to Breeze, so it never points at deleted
# packages (STRUCTURE.md, finding 5: the old NiceOS9 uninstaller left an
# empty tray and a theme that no longer existed).
set -euo pipefail
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/warp-legacy-install"
UNSET=$'\x01unset'
[ -f "$STATE/files" ] || { echo "Warp Legacy is not installed." >&2; exit 1; }
in_session() { [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] && [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; }
# The day/night follower first, so that restoring the settings below does
# not wake it.
if [ -S "${XDG_RUNTIME_DIR:-/nonexistent}/systemd/private" ] && command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now warp-legacy-follow.path >/dev/null 2>&1 || true
fi
# LibreOffice's colours come out only while it is closed (it writes its
# configuration back on exit), so nothing is touched before that.
LO_APPLY="$DATA/warp-legacy/libreoffice/libreoffice-apply"
if [ -x "$LO_APPLY" ] && pgrep -u "$(id -u)" -x soffice.bin >/dev/null 2>&1 \
   && "$LO_APPLY" status 2>/dev/null | grep -q "^extension: installed"; then
    echo "LibreOffice is running; close it first, Warp Legacy's colours have to come out of it." >&2
    exit 1
fi
# Firefox profiles are the user's: firefox-apply.sh is never run here. But
# the script goes with the rest, so a profile still wearing Warp Legacy
# stops the uninstall while the script to take it off is still there (the
# note pointed at a deleted file, Kubuntu VM, 21.10.2026).
# --keep-firefox: leave the profile as it is and go on.
FIREFOX_APPLY="$DATA/warp-legacy/browser/firefox-apply.sh"
if [ "${1:-}" != "--keep-firefox" ] && [ -x "$FIREFOX_APPLY" ] \
   && "$FIREFOX_APPLY" status --all 2>/dev/null | grep -qE "^(neon|classic)"; then
    echo "Firefox still wears Warp Legacy. Take it off first (with Firefox closed):" >&2
    echo "    $FIREFOX_APPLY remove" >&2
    echo "or keep it: $0 --keep-firefox" >&2
    exit 1
fi

current=$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)
previous=
if [ -f "$STATE/settings.before" ]; then
    previous=$(awk -F'\t' '$1 == "kdeglobals" && $3 == "LookAndFeelPackage" {print $4}' "$STATE/settings.before")
fi
[ "$previous" = "$UNSET" ] && previous=
case "$current" in
    org.warplegacy.*)
        target=${previous:-org.kde.breeze.desktop}
        case "$target" in org.warplegacy.*) target=org.kde.breeze.desktop ;; esac
        plasma-apply-lookandfeel --apply "$target" >/dev/null 2>&1 || true ;;
esac

# The recorded values, or the key removed where there was none.
if [ -f "$STATE/settings.before" ]; then
    while IFS=$'\t' read -r file groups key value; do
        args=(); IFS='>' read -ra parts <<< "$groups"
        for g in "${parts[@]}"; do args+=(--group "$g"); done
        if [ "$value" = "$UNSET" ]; then
            kwriteconfig6 --file "$file" "${args[@]}" --key "$key" --delete
        else
            kwriteconfig6 --file "$file" "${args[@]}" --key "$key" "$value"
        fi
    done < "$STATE/settings.before"
else
    # No record: at least nothing may name what is about to be deleted.
    case "$(kreadconfig6 --file kdeglobals --group Icons --key Theme)" in WarpLegacy*) kwriteconfig6 --file kdeglobals --group Icons --key Theme --delete ;; esac
    case "$(kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme)" in WarpLegacy*) kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme --delete ;; esac
    case "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)" in kwin4_decoration_qml_warplegacy*)
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme Breeze ;; esac
    case "$(kreadconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image)" in *org.warplegacy.*)
        kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image --delete ;; esac
fi

# The panels from before --layout: plasmashell writes its own on exit, so it
# is stopped while the old file goes back.
if [ -f "$STATE/appletsrc.before" ]; then
    # Without a systemd user manager (OpenRC and the like) plasmashell is a
    # plain process: kquitapp6 ends it, setsid starts it again.
    running=
    if in_session && [ -S "${XDG_RUNTIME_DIR:-/nonexistent}/systemd/private" ] && command -v systemctl >/dev/null 2>&1; then
        if systemctl --user -q is-active plasma-plasmashell 2>/dev/null; then
            running=systemd; systemctl --user stop plasma-plasmashell
        fi
    elif in_session && pgrep -xu "$(id -u)" plasmashell >/dev/null 2>&1; then
        running=plain; kquitapp6 plasmashell >/dev/null 2>&1
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            pgrep -xu "$(id -u)" plasmashell >/dev/null 2>&1 || break
            sleep 0.5
        done
    fi
    cp -a "$STATE/appletsrc.before" "$CONFIG/plasma-org.kde.plasma.desktop-appletsrc"
    [ -f "$STATE/plasmashellrc.before" ] && cp -a "$STATE/plasmashellrc.before" "$CONFIG/plasmashellrc"
    # Started again at the end, once the fonts are gone too: one restart
    # instead of two.
fi

if [ -f "$STATE/kvantum.kvconfig.before" ]; then
    mkdir -p "$CONFIG/Kvantum"
    cp -a "$STATE/kvantum.kvconfig.before" "$CONFIG/Kvantum/kvantum.kvconfig"
elif [ -f "$CONFIG/Kvantum/kvantum.kvconfig" ]; then
    case "$(kreadconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme)" in
        WarpLegacy*|Warp|WarpNeon|WarpNeonBlue) kwriteconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme --delete ;;
    esac
    # install.sh made the file when there was none: an empty one goes again.
    # (nothing in it but group headers and blank lines)
    if ! grep -qvE '^[[:space:]]*(\[.*\])?[[:space:]]*$' "$CONFIG/Kvantum/kvantum.kvconfig"; then
        rm -f "$CONFIG/Kvantum/kvantum.kvconfig"
        rmdir "$CONFIG/Kvantum" 2>/dev/null || true
    fi
fi
# The workspaces install.sh added, the last ones first; KWin moves their
# windows to the remaining ones.
if [ -f "$STATE/desktops.before" ] && in_session; then
    before=$(cat "$STATE/desktops.before")
    number=$(kreadconfig6 --file kwinrc --group Desktops --key Number)
    while [ -n "$number" ] && [ "$number" -gt "$before" ] && [ "$before" -ge 1 ]; do
        id=$(kreadconfig6 --file kwinrc --group Desktops --key "Id_$number")
        [ -n "$id" ] || break
        dbus-send --session --type=method_call --dest=org.kde.KWin /VirtualDesktopManager \
            org.kde.KWin.VirtualDesktopManager.removeDesktop string:"$id" 2>/dev/null || break
        sleep 0.3
        number=$((number - 1))
    done
fi
in_session && dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure 2>/dev/null || true

# The System Monitor's chart colours: ours out, so it generates its own
# from the highlight again; colours the user chose stay.
if [ -f "$DATA/warp-legacy/warp-legacy-sysmon" ] && command -v python3 >/dev/null 2>&1; then
    python3 "$DATA/warp-legacy/warp-legacy-sysmon" --reset || true
fi

remove() {   # remove <base> <list>: the files, then directories left empty
    while IFS= read -r f; do rm -f "$1/$f"; done < "$2"
    sed 's|/[^/]*$||' "$2" | sort -ru | while IFS= read -r d; do
        rmdir -p --ignore-fail-on-non-empty "$1/$d" 2>/dev/null || true
    done
}
# LibreOffice: the colours chosen before, the extension out.
[ -x "$LO_APPLY" ] && command -v python3 >/dev/null 2>&1 && { "$LO_APPLY" remove || true; }
remove "$DATA" "$STATE/files"
[ -f "$STATE/config-files" ] && remove "$CONFIG" "$STATE/config-files"
# Plasma's cache of the Plasma style.
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}"/plasma_theme_warp-legacy*.kcache
# What the Warp menu wrote while in use (common/DesktopMenu.qml): the
# programs started from its search; not in the file list.
rm -f "$DATA/warp-legacy/launched"
# warp-legacy-switch's note of the Neon last used.
rm -f "$CONFIG/warplegacyrc"
rmdir "$DATA/warp-legacy" 2>/dev/null || true
# A package from the store's "Get New…" is the whole archive, install.sh
# and build/ beside the global theme (package.py); with the theme's files
# removed above, the folder is left without metadata.json, and one such
# folder showed every global theme in System Settings as "Breeze" (NT
# Legacy, UPLOAD.md). Fedora VM, 25.10.2026.
for dir in "$DATA"/plasma/look-and-feel/org.warplegacy.*; do
    [ -d "$dir" ] && [ ! -f "$dir/metadata.json" ] && rm -rf -- "$dir"
done
# What the follower wrote while in use.
rm -f "$DATA/warp-legacy/followed"
rmdir "$DATA/warp-legacy" 2>/dev/null || true
rm -rf "$STATE"
# The fonts are gone: fontconfig and a running plasmashell learn of it (the
# shell reads the font list only at its start; install.sh).
fc-cache -f >/dev/null 2>&1 || true
case "${running:-}" in
    systemd) systemctl --user reset-failed plasma-plasmashell 2>/dev/null || true
             systemctl --user start plasma-plasmashell ;;
    plain) setsid -f plasmashell >/dev/null 2>&1 </dev/null ;;
esac
if [ -z "${running:-}" ] && in_session; then
    if [ -S "${XDG_RUNTIME_DIR:-/nonexistent}/systemd/private" ] && command -v systemctl >/dev/null 2>&1 \
       && { systemctl --user -q is-active plasma-plasmashell 2>/dev/null \
            || systemctl --user -q is-failed plasma-plasmashell 2>/dev/null; }; then
        # Several restarts in a row (uninstall, then install) ran into
        # systemd's start limit and left no shell at all (VM, 26.10.2026).
        systemctl --user reset-failed plasma-plasmashell 2>/dev/null || true
        systemctl --user restart plasma-plasmashell
    elif pgrep -xu "$(id -u)" plasmashell >/dev/null 2>&1; then
        kquitapp6 plasmashell >/dev/null 2>&1; sleep 2; setsid -f plasmashell >/dev/null 2>&1 </dev/null
    fi
fi
command -v systemctl >/dev/null 2>&1 && systemctl --user daemon-reload 2>/dev/null || true
echo "Warp Legacy removed. Log out and back in for every part to take effect."
