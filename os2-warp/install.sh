#!/usr/bin/env bash
# Install Warp Legacy for the current user (no root): copy build/ into
# ~/.local/share and build/config into ~/.config, recording every file, so
# uninstall.sh removes exactly those. A Kvantum choice made before is kept
# aside and restored by uninstall.sh.
#
#   ./install.sh                 install both variants
#   ./install.sh --apply         … and switch to Warp Legacy
#   ./install.sh --apply neon    … and switch to Warp Legacy Neon
#   … --layout                   also replace the panels with Warp Legacy's
#                                (Warp Bar, LaunchPad, Control Strip)
#
# Before the first --apply it writes down every setting it is about to
# change (settings.before) and, before the first --layout, the panels
# (appletsrc.before); uninstall.sh puts them back. A desktop that already
# runs Warp Legacy without such a record is not recorded: its "before"
# would be Warp Legacy itself.
set -euo pipefail
APPLY=; VARIANT=; LAYOUT=
for arg in "$@"; do
    case "$arg" in
        --apply) APPLY=1 ;;
        --layout) LAYOUT=--resetLayout ;;
        neon) VARIANT=neon ;;
        *) echo "Unknown argument: $arg (see the head of $0)" >&2; exit 2 ;;
    esac
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/warp-legacy-install"
[ -d "$HERE/build" ] || python3 "$HERE/build.py"
mkdir -p "$STATE"
# The lists only grow: a later install that brings fewer files (a test
# build without icons) must not make uninstall.sh forget earlier ones.
{ cat "$STATE/files" 2>/dev/null; (cd "$HERE/build" && find . -path ./config -prune -o ! -type d -print | sed 's|^\./||'); } \
    | sort -u > "$STATE/files.new" && mv "$STATE/files.new" "$STATE/files"
{ cat "$STATE/config-files" 2>/dev/null; (cd "$HERE/build/config" && find . ! -type d | sed 's|^\./||'); } \
    | sort -u > "$STATE/config-files.new" && mv "$STATE/config-files.new" "$STATE/config-files"
if [ -f "$CONFIG/Kvantum/kvantum.kvconfig" ] && [ ! -f "$STATE/kvantum.kvconfig.before" ]; then
    cp -a "$CONFIG/Kvantum/kvantum.kvconfig" "$STATE/kvantum.kvconfig.before"
fi
mkdir -p "$DATA"
for entry in "$HERE"/build/*; do
    [ "$(basename "$entry")" = config ] || cp -a "$entry" "$DATA/"
done
mkdir -p "$CONFIG" && cp -a "$HERE/build/config/." "$CONFIG/"
echo "Installed $(cat "$STATE/files" "$STATE/config-files" | wc -l) files"
if ! command -v kvantummanager >/dev/null 2>&1; then
    echo "Note: Kvantum is not installed; programs keep their own style (package: kvantum)." >&2
fi
# file, groups (">"-separated), key: everything --apply changes.
SETTINGS="kdeglobals	General	ColorScheme
kdeglobals	General	font
kdeglobals	General	menuFont
kdeglobals	General	toolBarFont
kdeglobals	General	fixed
kdeglobals	WM	activeFont
kdeglobals	KDE	widgetStyle
kdeglobals	KDE	LookAndFeelPackage
kdeglobals	Icons	Theme
kwinrc	org.kde.kdecoration2	library
kwinrc	org.kde.kdecoration2	theme
kwinrc	org.kde.kdecoration2	ButtonsOnLeft
kwinrc	org.kde.kdecoration2	ButtonsOnRight
kwinrc	org.kde.kdecoration2	BorderSize
plasmarc	Theme	name
kscreenlockerrc	Greeter	WallpaperPlugin
kscreenlockerrc	Greeter>Wallpaper>org.kde.image>General	Image"
UNSET=$'\x01unset'
record() {
    [ -f "$STATE/settings.before" ] && return
    case "$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)" in
        org.warplegacy.*)
            echo "Note: Warp Legacy was applied before without a record; uninstall.sh will fall back to Breeze." >&2
            return ;;
    esac
    while IFS=$'\t' read -r file groups key; do
        args=(); IFS='>' read -ra parts <<< "$groups"
        for g in "${parts[@]}"; do args+=(--group "$g"); done
        value=$(kreadconfig6 --file "$file" "${args[@]}" --key "$key" --default "$UNSET")
        printf '%s\t%s\t%s\t%s\n' "$file" "$groups" "$key" "$value"
    done <<< "$SETTINGS" > "$STATE/settings.before"
}
if [ -n "$APPLY" ]; then
    record
    if [ -n "$LAYOUT" ] && [ ! -f "$STATE/appletsrc.before" ] && [ -f "$STATE/settings.before" ]; then
        cp -a "$CONFIG/plasma-org.kde.plasma.desktop-appletsrc" "$STATE/appletsrc.before" 2>/dev/null || true
        cp -a "$CONFIG/plasmashellrc" "$STATE/plasmashellrc.before" 2>/dev/null || true
    fi
    case "$VARIANT" in
        "")   LNF=org.warplegacy.desktop;      KVANTUM=WarpLegacy;     ICONS=breeze ;;
        neon) LNF=org.warplegacy.neon.desktop; KVANTUM=WarpLegacyNeon; ICONS=WarpLegacyNeon2026 ;;
    esac
    plasma-apply-lookandfeel --apply "$LNF" $LAYOUT
    # The global theme only carries the decoration's library and theme into
    # kdedefaults, not the button order; OS/2 puts close left of hide and
    # maximize (DESIGN.md §3).
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft M
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight XIA
    # widgetStyle in kdedefaults alone did not reach the programs (VM,
    # 20.10.2026); CDE Copper writes it to kdeglobals for the same reason.
    if [ -e /usr/lib64/qt6/plugins/styles/libkvantum.so ] || [ -e /usr/lib/qt6/plugins/styles/libkvantum.so ] \
       || [ -e /usr/lib/x86_64-linux-gnu/qt6/plugins/styles/libkvantum.so ]; then
        kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum
    fi
    kwriteconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme "$KVANTUM"
    # The same for the icon theme: programs kept Breeze although kdedefaults
    # named Warp Legacy Neon's. The classic variant has no set of its own
    # yet and takes Breeze.
    kwriteconfig6 --file kdeglobals --group Icons --key Theme "$ICONS"
    # The lock screen shows the neon tubes in both variants: OS/2's Lockup
    # was the same neon picture whatever the desktop looked like.
    kwriteconfig6 --file kscreenlockerrc --group Greeter --key WallpaperPlugin org.kde.image
    kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key Image "file://$DATA/wallpapers/org.warplegacy.neon-roehren/"
    # IBM Plex Sans Condensed (fonts/), bold titles. Written here as well:
    # like the widget style, the global theme's fonts did not reach every
    # program from kdedefaults alone.
    fc-cache -f "$DATA/fonts/WarpLegacy" >/dev/null 2>&1 || true
    UI_FONT="IBM Plex Sans Condensed,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    for key in font menuFont toolBarFont; do
        kwriteconfig6 --file kdeglobals --group General --key "$key" "$UI_FONT"
    done
    kwriteconfig6 --file kdeglobals --group General --key fixed "IBM Plex Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "IBM Plex Sans Condensed,10,-1,5,700,0,0,0,0,0,0,0,0,0,0,1"
    # Four workspaces, as the Control Strip shows them; KWin ignores
    # [Desktops] Number from the global theme, so they are created here.
    count=$(dbus-send --session --print-reply --dest=org.kde.KWin /VirtualDesktopManager \
        org.freedesktop.DBus.Properties.Get string:org.kde.KWin.VirtualDesktopManager string:count 2>/dev/null \
        | awk '/uint32/ {print $3}')
    [ -n "$count" ] && [ ! -f "$STATE/desktops.before" ] && [ -f "$STATE/settings.before" ] && echo "$count" > "$STATE/desktops.before"
    while [ -n "$count" ] && [ "$count" -lt 4 ]; do
        dbus-send --session --type=method_call --dest=org.kde.KWin /VirtualDesktopManager \
            org.kde.KWin.VirtualDesktopManager.createDesktop uint32:"$count" string:"" 2>/dev/null || break
        count=$((count + 1))
    done
    dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure 2>/dev/null || true
    echo "Applied. Log out and back in for every part to take effect."
fi
