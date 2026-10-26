#!/usr/bin/env bash
# Install Warp Legacy for the current user (no root): copy build/ into
# ~/.local/share and build/config into ~/.config, recording every file, so
# uninstall.sh removes exactly those. A Kvantum choice made before is kept
# aside and restored by uninstall.sh.
#
#   ./install.sh                 install the variants the archive brings
#                                (classic, or Neon and Neon Blue; the
#                                repository's build has all three)
#   ./install.sh --apply         … and switch to Warp Legacy (Neon in
#                                the Neon package, which has no classic)
#   ./install.sh --apply neon    … and switch to Warp Legacy Neon
#   ./install.sh --apply neon-blue  … and to Warp Legacy Neon Blue
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
        neon|neon-blue) VARIANT=$arg ;;
        *) echo "Unknown argument: $arg (see the head of $0)" >&2; exit 2 ;;
    esac
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/warp-legacy-install"
[ -d "$HERE/build" ] || python3 "$HERE/build.py"
# The packages bring one family each (package.py): the variant asked for
# must be in this one.
case "$VARIANT" in "") lnf=org.warplegacy.desktop ;; *) lnf=org.warplegacy.$VARIANT.desktop ;; esac
if [ ! -d "$HERE/build/plasma/look-and-feel/$lnf" ]; then
    if [ -z "$VARIANT" ] && [ -d "$HERE/build/plasma/look-and-feel/org.warplegacy.neon.desktop" ]; then
        VARIANT=neon
    else
        case "$VARIANT" in "") other="Warp Legacy" ;; *) other="Warp Legacy Neon" ;; esac
        echo "This archive does not bring that variant; it is in the package $other." >&2
        exit 2
    fi
fi
mkdir -p "$STATE"
# The lists only grow: a later install that brings fewer files (a test
# build without icons) must not make uninstall.sh forget earlier ones.
{ cat "$STATE/files" 2>/dev/null; (cd "$HERE/build" && find . -path ./config -prune -o ! -type d -print | sed 's|^\./||'); } \
    | sort -u > "$STATE/files.new" && mv "$STATE/files.new" "$STATE/files"
{ cat "$STATE/config-files" 2>/dev/null; (cd "$HERE/build/config" && find . ! -type d | sed 's|^\./||'); } \
    | sort -u > "$STATE/config-files.new" && mv "$STATE/config-files.new" "$STATE/config-files"
# Kvantum's file as it was before Warp Legacy, once: a second install saved
# the one the first had written (theme=WarpNeon), and uninstall.sh put
# that back (Kubuntu VM, 21.10.2026). No file: a marker, so uninstall.sh
# knows there was none.
if [ ! -f "$STATE/kvantum.kvconfig.before" ] && [ ! -f "$STATE/kvantum.none" ]; then
    if [ -f "$CONFIG/Kvantum/kvantum.kvconfig" ]; then
        case "$(kreadconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme)" in
            WarpLegacy*|Warp|WarpNeon|WarpNeonBlue) : ;;     # already ours: an install from before the record
            *) cp -a "$CONFIG/Kvantum/kvantum.kvconfig" "$STATE/kvantum.kvconfig.before" ;;
        esac
    else
        : > "$STATE/kvantum.none"
    fi
fi
# --remove-destination: an existing file is unlinked, not overwritten in
# place. A running plasmashell has the translation catalogue mapped; cp
# rewrote it under it and the next i18nd() crashed in gettext (SIGSEGV in
# _nl_find_msg, VM, 20.10.2026). Unlinked, the running process keeps the old
# copy until it lets go.
mkdir -p "$DATA"
for entry in "$HERE"/build/*; do
    [ "$(basename "$entry")" = config ] || cp -a --remove-destination "$entry" "$DATA/"
done
# The Kvantum themes' names before 21.10.2026 (now Warp, WarpNeon).
rm -rf "$CONFIG/Kvantum/WarpLegacy" "$CONFIG/Kvantum/WarpLegacyNeon"
mkdir -p "$CONFIG" && cp -a --remove-destination "$HERE/build/config/." "$CONFIG/"
sed -i "s|@SYNC@|$DATA/warp-legacy/warp-legacy-sync|" "$CONFIG/autostart/warp-legacy-sync.desktop"
sed -i "s|@FOLLOW@|$DATA/warp-legacy/warp-legacy-follow|" "$CONFIG/systemd/user/warp-legacy-follow.service"
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
kdeglobals	KDE	DefaultLightLookAndFeel
kdeglobals	KDE	DefaultDarkLookAndFeel
kdeglobals	Icons	Theme
kwinrc	org.kde.kdecoration2	library
kwinrc	org.kde.kdecoration2	theme
kwinrc	org.kde.kdecoration2	ButtonsOnLeft
kwinrc	org.kde.kdecoration2	ButtonsOnRight
kwinrc	org.kde.kdecoration2	BorderSize
konsolerc	Desktop Entry	DefaultProfile
kcminputrc	Mouse	cursorTheme
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
# A record from an older install lacks the keys added since: the cursor
# theme (21.10.2026), the day/night themes (26.10.2026). Recorded now,
# unless they are already Warp Legacy's.
complete_record() {
    [ -f "$STATE/settings.before" ] || return
    if ! grep -q $'^kcminputrc\tMouse\tcursorTheme\t' "$STATE/settings.before"; then
        value=$(kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme --default "$UNSET")
        case "$value" in WarpLegacy*) value=$UNSET ;; esac
        printf '%s\t%s\t%s\t%s\n' kcminputrc Mouse cursorTheme "$value" >> "$STATE/settings.before"
    fi
    for key in DefaultLightLookAndFeel DefaultDarkLookAndFeel; do
        grep -q $'^kdeglobals\tKDE\t'"$key"$'\t' "$STATE/settings.before" && continue
        value=$(kreadconfig6 --file kdeglobals --group KDE --key "$key" --default "$UNSET")
        case "$value" in org.warplegacy.*) value=$UNSET ;; esac
        printf '%s\t%s\t%s\t%s\n' kdeglobals KDE "$key" "$value" >> "$STATE/settings.before"
    done
}
if [ -n "$APPLY" ]; then
    record
    complete_record
    if [ -n "$LAYOUT" ] && [ ! -f "$STATE/appletsrc.before" ] && [ -f "$STATE/settings.before" ]; then
        cp -a "$CONFIG/plasma-org.kde.plasma.desktop-appletsrc" "$STATE/appletsrc.before" 2>/dev/null || true
        cp -a "$CONFIG/plasmashellrc" "$STATE/plasmashellrc.before" 2>/dev/null || true
    fi
    case "$VARIANT" in
        "")   LNF=org.warplegacy.desktop;      KVANTUM=Warp;           ICONS=WarpLegacy;         KONSOLE="Warp Legacy";      PICTURE=org.warplegacy.warp4-wirbel-violett ;;
        neon) LNF=org.warplegacy.neon.desktop; KVANTUM=WarpNeon;       ICONS=WarpLegacyNeon2026Violett; KONSOLE="Warp Legacy Neon (transparent)"; PICTURE=org.warplegacy.dunkel-lichtbogen-rechts ;;
        neon-blue) LNF=org.warplegacy.neon-blue.desktop; KVANTUM=WarpNeonBlue; ICONS=WarpLegacyNeon2026; KONSOLE="Warp Legacy Neon Blue (transparent)"; PICTURE=org.warplegacy.dunkel-lichtbogen-blau ;;
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
    # named Warp Legacy Neon's.
    kwriteconfig6 --file kdeglobals --group Icons --key Theme "$ICONS"
    # The cursors (Neon: cursors_neon.py), at once for the running session.
    case "$VARIANT" in neon) CURSORS=WarpLegacyNeonCursors ;; neon-blue) CURSORS=WarpLegacyNeonBlueCursors ;; *) CURSORS=breeze_cursors ;; esac
    if [ -d "$DATA/icons/$CURSORS" ] || [ -d "/usr/share/icons/$CURSORS" ]; then
        if command -v plasma-apply-cursortheme >/dev/null 2>&1; then
            plasma-apply-cursortheme "$CURSORS" >/dev/null 2>&1 || kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$CURSORS"
        else
            kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$CURSORS"
        fi
    fi
    # Running programs only learn of it when told: a Dolphin left open kept
    # the icons of a variant in between (VM, 21.10.2026). KIconLoader listens
    # for iconChanged on /KIconLoader.
    dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 2>/dev/null || true
    # Konsole after the concept's command prompt (build.py, KONSOLE).
    kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile "$KONSOLE.profile"
    # The System Monitor's chart colours: Plasma turns the highlight's hue
    # and stores the result per page, so Neon got orange disks
    # (session/warp-legacy-sysmon; colours the user chose stay).
    if command -v python3 >/dev/null 2>&1; then
        python3 "$DATA/warp-legacy/warp-legacy-sysmon" "$LNF" || echo "Note: System Monitor colours not set." >&2
    fi
    # The lock screen shows OS/2 Lockup's neon tubes: on black in Neon, on
    # OS/2's grey in classic. The greeter draws its clock in the Plasma
    # style's button text, black in classic: unreadable on the black tubes
    # (Kubuntu and Fedora VMs, 21.10.2026).
    case "$VARIANT" in neon*) LOCK=neon-roehren ;; *) LOCK=neon-roehren-hell ;; esac
    kwriteconfig6 --file kscreenlockerrc --group Greeter --key WallpaperPlugin org.kde.image
    kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key Image "file://$DATA/wallpapers/org.warplegacy.$LOCK/"
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
    # The variant's wallpaper (session/warp-wallpaper): without --layout the
    # global theme left the other variant's picture in place.
    [ -z "$LAYOUT" ] && sh "$DATA/warp-legacy/warp-wallpaper" "$PICTURE"
    # Day and night (DESIGN.md, day and night): Plasma's automatic
    # switching goes from classic by day to Neon at night and back, when
    # both are installed (the store packages bring one family each; alone,
    # a variant stays itself day and night). The pictures with a night half
    # (the raytracing ones) stay and show it; session/warp-legacy-follow
    # completes each switch.
    installed() { [ -d "$DATA/plasma/look-and-feel/$1" ]; }
    case "$VARIANT" in
        "") DAY=$LNF; NIGHT=$LNF; installed org.warplegacy.neon.desktop && NIGHT=org.warplegacy.neon.desktop ;;
        *)  NIGHT=$LNF; DAY=$LNF; installed org.warplegacy.desktop && DAY=org.warplegacy.desktop ;;
    esac
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultLightLookAndFeel "$DAY"
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultDarkLookAndFeel "$NIGHT"
    printf '%s\n' "$LNF" > "$DATA/warp-legacy/followed"
    if [ -S "${XDG_RUNTIME_DIR:-/nonexistent}/systemd/private" ] && command -v systemctl >/dev/null 2>&1; then
        systemctl --user daemon-reload
        systemctl --user enable --now warp-legacy-follow.path >/dev/null 2>&1 || true
    fi
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
    # LibreOffice's application colours (libreoffice/README.md): the
    # extension with both schemes, and the variant's chosen unless the user
    # picked colours of their own. Needs LibreOffice closed.
    LO_APPLY="$DATA/warp-legacy/libreoffice/libreoffice-apply"
    if [ -x "$LO_APPLY" ] && command -v soffice >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
        "$LO_APPLY" "${VARIANT:-classic}" --if-default \
            || echo "Note: LibreOffice colours not set; later: $LO_APPLY ${VARIANT:-classic}" >&2
    fi
    echo "Applied. Log out and back in for every part to take effect."
    echo "Firefox (optional): $DATA/warp-legacy/browser/firefox-apply.sh ${VARIANT:-classic}"
fi
