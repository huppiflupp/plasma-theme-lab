#!/usr/bin/env bash
# Take RISC Legacy back out: first the desktop as it was (the settings
# install.sh --apply recorded, the panels from before --layout, the global
# theme in use before), then the files install.sh recorded. Without a
# record the desktop falls back to Breeze, so it never points at deleted
# packages. After Warp Legacy's uninstall.sh.
set -euo pipefail
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/risc-legacy-install"
UNSET=$'\x01unset'
[ -f "$STATE/files" ] || { echo "RISC Legacy is not installed." >&2; exit 1; }
in_session() { [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] && [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; }

current=$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)
previous=
if [ -f "$STATE/settings.before" ]; then
    previous=$(awk -F'\t' '$1 == "kdeglobals" && $3 == "LookAndFeelPackage" {print $4}' "$STATE/settings.before")
fi
[ "$previous" = "$UNSET" ] && previous=
case "$current" in
    org.risclegacy.*)
        target=${previous:-org.kde.breeze.desktop}
        case "$target" in org.risclegacy.*) target=org.kde.breeze.desktop ;; esac
        plasma-apply-lookandfeel --apply "$target" >/dev/null 2>&1 || true ;;
esac

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
    case "$(kreadconfig6 --file kdeglobals --group Icons --key Theme)" in RiscLegacy*) kwriteconfig6 --file kdeglobals --group Icons --key Theme --delete ;; esac
    case "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)" in kwin4_decoration_qml_risclegacy*)
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme Breeze ;; esac
fi

# The panels from before --layout; plasmashell writes its own on exit, so
# it is stopped while the old file goes back (without systemd: kquitapp6
# and setsid, as Warp Legacy does).
if [ -f "$STATE/appletsrc.before" ]; then
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
    case "$running" in
        systemd) systemctl --user start plasma-plasmashell ;;
        plain) setsid -f plasmashell >/dev/null 2>&1 </dev/null ;;
    esac
fi

if [ -f "$STATE/kvantum.kvconfig.before" ]; then
    mkdir -p "$CONFIG/Kvantum"
    cp -a "$STATE/kvantum.kvconfig.before" "$CONFIG/Kvantum/kvantum.kvconfig"
elif [ -f "$CONFIG/Kvantum/kvantum.kvconfig" ]; then
    case "$(kreadconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme)" in
        RiscLegacy*) kwriteconfig6 --file "$CONFIG/Kvantum/kvantum.kvconfig" --group General --key theme --delete ;;
    esac
    if ! grep -qvE '^[[:space:]]*(\[.*\])?[[:space:]]*$' "$CONFIG/Kvantum/kvantum.kvconfig"; then
        rm -f "$CONFIG/Kvantum/kvantum.kvconfig"
        rmdir "$CONFIG/Kvantum" 2>/dev/null || true
    fi
fi
in_session && dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure 2>/dev/null || true

remove() {   # remove <base> <list>: the files, then directories left empty
    while IFS= read -r f; do rm -f "$1/$f"; done < "$2"
    sed 's|/[^/]*$||' "$2" | sort -ru | while IFS= read -r d; do
        rmdir -p --ignore-fail-on-non-empty "$1/$d" 2>/dev/null || true
    done
}
remove "$DATA" "$STATE/files"
[ -f "$STATE/config-files" ] && remove "$CONFIG" "$STATE/config-files"
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}"/plasma_theme_risc-legacy*.kcache
# What the Apps menu wrote while in use: the programs started from its search.
rm -f "$DATA/risc-legacy/launched"
rmdir "$DATA/risc-legacy" 2>/dev/null || true
rm -rf "$STATE"
echo "RISC Legacy removed. Log out and back in for every part to take effect."
