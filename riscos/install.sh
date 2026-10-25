#!/usr/bin/env bash
# Install RISC Legacy for the current user (no root): copy build/ into
# ~/.local/share and build/config into ~/.config, recording every file, so
# uninstall.sh removes exactly those. After Warp Legacy's install.sh.
#
#   ./install.sh                     install all variants
#   ./install.sh --apply [variant]   … and switch to one: classic (default),
#                                    4, 2026, 2026-dark, pi, iyonix, acorn,
#                                    graphite
#   … --layout                       also replace the panels with the
#                                    iconbar along the bottom
#
# Before the first --apply it writes down every setting it is about to
# change (settings.before) and, before the first --layout, the panels
# (appletsrc.before); uninstall.sh puts them back.
set -euo pipefail
APPLY=; VARIANT=classic; LAYOUT=
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -d "$HERE/build" ] || python3 "$HERE/build.py"
TABLE="$HERE/build/risc-legacy/variants"
for arg in "$@"; do
    case "$arg" in
        --apply) APPLY=1 ;;
        --layout) LAYOUT=--resetLayout ;;
        -*) echo "Unknown option: $arg (see the head of $0)" >&2; exit 2 ;;
        *) grep -q "^$arg	" "$TABLE" || { echo "No variant \"$arg\"; there are: $(cut -f1 "$TABLE" | tr '\n' ' ')" >&2; exit 2; }
           VARIANT=$arg ;;
    esac
done
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/risc-legacy-install"
mkdir -p "$STATE"
# The lists only grow: a later install that brings fewer files must not
# make uninstall.sh forget earlier ones.
{ cat "$STATE/files" 2>/dev/null; (cd "$HERE/build" && find . -path ./config -prune -o ! -type d -print | sed 's|^\./||'); } \
    | sort -u > "$STATE/files.new" && mv "$STATE/files.new" "$STATE/files"
{ cat "$STATE/config-files" 2>/dev/null; (cd "$HERE/build/config" && find . ! -type d | sed 's|^\./||'); } \
    | sort -u > "$STATE/config-files.new" && mv "$STATE/config-files.new" "$STATE/config-files"
# Kvantum's file as it was before, once; no file: a marker.
if [ ! -f "$STATE/kvantum.kvconfig.before" ] && [ ! -f "$STATE/kvantum.none" ]; then
    if [ -f "$CONFIG/Kvantum/kvantum.kvconfig" ]; then
        case "$(kreadconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme)" in
            RiscLegacy*) : ;;
            *) cp -a "$CONFIG/Kvantum/kvantum.kvconfig" "$STATE/kvantum.kvconfig.before" ;;
        esac
    else
        : > "$STATE/kvantum.none"
    fi
fi
# --remove-destination: a running plasmashell keeps the old copy of a file
# it has mapped instead of reading one rewritten under it (Warp Legacy).
mkdir -p "$DATA"
for entry in "$HERE"/build/*; do
    [ "$(basename "$entry")" = config ] || cp -a --remove-destination "$entry" "$DATA/"
done
mkdir -p "$CONFIG" && cp -a --remove-destination "$HERE/build/config/." "$CONFIG/"
fc-cache -f "$DATA/fonts/risc-legacy" >/dev/null 2>&1 || true
echo "Installed $(cat "$STATE/files" "$STATE/config-files" | wc -l) files"
command -v kvantummanager >/dev/null 2>&1 || \
    echo "Note: Kvantum is not installed; programs keep their own style (package: kvantum or qt6-style-kvantum)." >&2

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
plasmarc	Theme	name"
UNSET=$'\x01unset'
record() {
    [ -f "$STATE/settings.before" ] && return
    case "$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)" in
        org.risclegacy.*)
            echo "Note: RISC Legacy was applied before without a record; uninstall.sh will fall back to Breeze." >&2
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
    IFS=$'\t' read -r _ LNF KVANTUM ICONS PICTURE DECORATION SCHEME STYLE < <(grep "^$VARIANT	" "$TABLE")
    plasma-apply-lookandfeel --apply "$LNF" $LAYOUT
    # The frame, the colours and the Plasma style written out as well: the
    # global theme's defaults left kwinrc without the decoration (Fedora
    # VM, 25.10.2026).
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "$DECORATION"
    plasma-apply-colorscheme "$SCHEME" >/dev/null 2>&1 || kwriteconfig6 --file kdeglobals --group General --key ColorScheme "$SCHEME"
    plasma-apply-desktoptheme "$STYLE" >/dev/null 2>&1 || kwriteconfig6 --file plasmarc --group Theme --key name "$STYLE"
    # The global theme carries the decoration but not the button order:
    # RISC OS has Back and Close on the left, Iconise and Toggle size on
    # the right (DESIGN.md §3).
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft BX
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight IA
    # Widget style and icons written to kdeglobals as well: from the global
    # theme's defaults alone they did not reach the programs (Warp Legacy).
    if [ -e /usr/lib64/qt6/plugins/styles/libkvantum.so ] || [ -e /usr/lib/qt6/plugins/styles/libkvantum.so ] \
       || [ -e /usr/lib/x86_64-linux-gnu/qt6/plugins/styles/libkvantum.so ]; then
        kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum
    fi
    kwriteconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme "$KVANTUM"
    kwriteconfig6 --file kdeglobals --group Icons --key Theme "$ICONS"
    dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 2>/dev/null || true
    UI_FONT="TeX Gyre Heros,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    for key in font menuFont toolBarFont; do
        kwriteconfig6 --file kdeglobals --group General --key "$key" "$UI_FONT"
    done
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "$UI_FONT"
    # The variant's picture: without --layout the global theme leaves the
    # desktop's picture as it was.
    if [ -z "$LAYOUT" ] && command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
        plasma-apply-wallpaperimage "$DATA/wallpapers/$PICTURE" >/dev/null 2>&1 || true
    fi
    dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure 2>/dev/null || true
    echo "Applied $LNF. Log out and back in for every part to take effect."
fi
