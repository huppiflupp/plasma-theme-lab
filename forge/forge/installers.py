"""The three shell scripts in the package: install.sh, uninstall.sh, install-system.sh.

User and system layer are separate (guide/01): install.sh needs no sudo and
cannot break the boot; install-system.sh backs up before every change and
can take everything back with --revert.

Deleting only with ${VAR:?} protection and only paths that begin with an
expected root — an empty or spoilt manifest must never hit more than the
theme's own files.
"""
import os

COMMON = '''set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
THEME="{theme}"
VARIANTS="{ids}"
FONT="{font}"
BUTTONS_LEFT="{bl}"
BUTTONS_RIGHT="{br}"
pick() {{
    case "$1" in
{vmap}
    *) echo "Unknown variant: $1 (there are: $VARIANTS)" >&2; exit 2 ;;
    esac
}}
# A running plasmashell reads the font list once, at its start: fonts put
# in, replaced or removed under it come out as garbled glyphs or another
# font (RISC Legacy and Warp Legacy in the Fedora VM, 26.10.2026). After a
# change of fonts it is restarted; KWin takes them at the next login.
restart_shell() {{
    [ -n "${{DBUS_SESSION_BUS_ADDRESS:-}}" ] && [ -n "${{WAYLAND_DISPLAY:-}}${{DISPLAY:-}}" ] || return 0
    if [ -S "${{XDG_RUNTIME_DIR:-/nonexistent}}/systemd/private" ] && command -v systemctl >/dev/null 2>&1 \\
       && {{ systemctl --user -q is-active plasma-plasmashell 2>/dev/null \\
            || systemctl --user -q is-failed plasma-plasmashell 2>/dev/null; }}; then
        # Several restarts in a row ran into systemd's start limit.
        systemctl --user reset-failed plasma-plasmashell 2>/dev/null || true
        systemctl --user restart plasma-plasmashell || true
    elif pgrep -xu "$(id -u)" plasmashell >/dev/null 2>&1; then
        kquitapp6 plasmashell >/dev/null 2>&1 || true
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            pgrep -xu "$(id -u)" plasmashell >/dev/null 2>&1 || break
            sleep 0.5
        done
        setsid -f plasmashell >/dev/null 2>&1 </dev/null
    fi
}}
'''

INSTALL = '''#!/usr/bin/env bash
# {name} — installs into your own user account only, without sudo.
#   ./install.sh                  copy the files to ~/.local/share
#   ./install.sh --apply <var>    and apply them (variants: {ids})
# Undo: ./uninstall.sh
{common}
D="${{XDG_DATA_HOME:-$HOME/.local/share}}"
C="${{XDG_CONFIG_HOME:-$HOME/.config}}"
STATE="$D/theme-forge/$THEME"
mkdir -p "$STATE"
MAN="$STATE/manifest"
: > "$MAN.new"
copy_tree() {{   # source target
    [ -d "$HERE/$1" ] || return 0
    (cd "$HERE/$1" && find . -type f) | while read -r f; do
        mkdir -p "$(dirname "$2/$f")"
        # A new inode instead of overwriting: plasmashell keeps files mapped.
        cp --remove-destination "$HERE/$1/$f" "$2/$f"
        echo "$2/${{f#./}}" >> "$MAN.new"
    done
}}
copy_tree color-schemes            "$D/color-schemes"
copy_tree plasma/desktoptheme      "$D/plasma/desktoptheme"
copy_tree plasma/look-and-feel     "$D/plasma/look-and-feel"
copy_tree aurorae/themes           "$D/aurorae/themes"
copy_tree wallpapers               "$D/wallpapers"
copy_tree konsole                  "$D/konsole"
copy_tree icons                    "$D/icons"
copy_tree fonts                    "$D/fonts/theme-forge-$THEME"
mv "$MAN.new" "$MAN"
# cp -a keeps the source's directory dates, by which fontconfig judges a
# directory: fresh dates, a forced rebuild.
find "$D/fonts/theme-forge-$THEME" -type d -exec touch {{}} + 2>/dev/null || true
fc-cache -f "$D/fonts" >/dev/null 2>&1 || true
echo "Installed: $(wc -l < "$MAN") files (list: $MAN)"

if [ "${{1:-}}" = "--apply" ]; then
    VAR="${{2:-{first}}}"; pick "$VAR"
    BK="$STATE/backup"
    if [ ! -d "$BK" ]; then     # only the FIRST backup counts
        mkdir -p "$BK"
        for f in {configs}; do
            if [ -f "$C/$f" ]; then cp -a "$C/$f" "$BK/$f"; else touch "$BK/$f.absent"; fi
        done
        kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage > "$BK/lookandfeel" 2>/dev/null || true
    fi
    plasma-apply-lookandfeel -a "$LNF"
    # What a global theme does not set (measured in the lab): button order,
    # title font, Konsole's default profile.
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft "$BUTTONS_LEFT"
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "$BUTTONS_RIGHT"
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "$FONT,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile "$KPROF.profile"
    IMG="$D/wallpapers/$WALL/contents/images/1920x1080.jpg"
    # A global theme does not replace a wallpaper another theme set
    # explicitly (VM with Warp Legacy, 24.10.2026), hence set here.
    plasma-apply-wallpaperimage "$D/wallpapers/$WALL" >/dev/null 2>&1 || true
    # A fresh icon cache, else KIconLoader still shows the old icons
    rm -f "$HOME/.cache/icon-cache.kcache"
    kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image \\
        --group General --key Image "file://$IMG"
    dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure || true
    echo "Applied: $LNF — complete only after logging out and back in."
fi
restart_shell
'''

UNINSTALL = '''#!/usr/bin/env bash
# {name} — removes the files and restores the configuration from before the
# first --apply.
{common}
D="${{XDG_DATA_HOME:-$HOME/.local/share}}"
C="${{XDG_CONFIG_HOME:-$HOME/.config}}"
STATE="$D/theme-forge/$THEME"
BK="$STATE/backup"
if [ -d "$BK" ]; then
    PREV="$(cat "$BK/lookandfeel" 2>/dev/null || true)"
    plasma-apply-lookandfeel -a "${{PREV:-org.kde.breeze.desktop}}" || true
    for f in {configs}; do
        if [ -f "$BK/$f" ]; then cp -a "$BK/$f" "${{C:?}}/$f"
        elif [ -f "$BK/$f.absent" ]; then rm -f -- "${{C:?}}/${{f:?}}"; fi
    done
fi
# Delete only files below $D, whatever the manifest says.
if [ -f "$STATE/manifest" ]; then
    while read -r f; do
        case "$f" in "${{D:?}}"/?*) rm -f -- "$f" ;; esac
    done < "$STATE/manifest"
fi
for d in plasma/desktoptheme plasma/look-and-feel aurorae/themes wallpapers fonts icons; do
    [ -d "${{D:?}}/$d" ] && find "${{D:?}}/$d" -mindepth 1 -type d -empty -delete
done
rm -f -- "${{STATE:?}}/manifest" "${{STATE:?}}"/backup/*
rmdir "${{STATE:?}}/backup" "${{STATE:?}}" 2>/dev/null || true
dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure || true
fc-cache -f >/dev/null 2>&1 || true
restart_shell
echo "Removed. Log out and back in for everything to be reset."
'''

SYSTEM = '''#!/usr/bin/env bash
# {name} — boot splash (Plymouth) and boot menu (GRUB).
# CAUTION: writes to /usr/share, /boot and /etc/default/grub and rebuilds the
# initramfs. A fault here can prevent booting. Make a backup first.
#   sudo ./install-system.sh <variant> [--plymouth] [--grub]   (without a switch: both)
#   sudo ./install-system.sh --revert
{common}
[ "$(id -u)" = 0 ] || {{ echo "Please run with sudo." >&2; exit 1; }}
BK="/var/lib/theme-forge/$THEME"
if [ -d /boot/grub2 ]; then GD=/boot/grub2; elif [ -d /boot/grub ]; then GD=/boot/grub; else GD=""; fi
regen_grub() {{
    if command -v grub2-mkconfig >/dev/null; then grub2-mkconfig -o "$GD/grub.cfg"
    elif command -v update-grub >/dev/null; then update-grub
    elif command -v grub-mkconfig >/dev/null; then grub-mkconfig -o "$GD/grub.cfg"
    else echo "WARNING: no grub-mkconfig found" >&2; fi
}}
regen_initrd() {{
    if command -v dracut-rebuild >/dev/null; then dracut-rebuild
    elif command -v dracut >/dev/null; then dracut --force
    elif command -v update-initramfs >/dev/null; then update-initramfs -u
    elif command -v mkinitcpio >/dev/null; then mkinitcpio -P
    fi
}}
# Removes only the theme's own folders (Plymouth/GRUB), never anything else.
remove_own() {{
    case "$1" in
        /usr/share/plymouth/themes/?*|/boot/grub2/themes/?*|/boot/grub/themes/?*) rm -r -- "$1" ;;
        *) echo "skipped (unexpected path): $1" >&2 ;;
    esac
}}
if [ "${{1:-}}" = "--revert" ]; then
    [ -d "$BK" ] || {{ echo "No backup in $BK." >&2; exit 1; }}
    if [ -f "$BK/default-grub" ]; then
        cp -a "$BK/default-grub" /etc/default/grub; regen_grub
    fi
    if [ -f "$BK/plymouth-theme" ]; then
        plymouth-set-default-theme "$(cat "$BK/plymouth-theme")" && regen_initrd
    fi
    if [ -f "$BK/installed" ]; then
        sort -u "$BK/installed" | while read -r d; do [ -e "$d" ] && remove_own "$d"; done
    fi
    rm -f -- "$BK"/default-grub "$BK"/plymouth-theme "$BK"/installed
    rmdir "$BK" 2>/dev/null || true
    echo "Reverted."
    exit 0
fi
VAR="${{1:-}}"; [ -n "$VAR" ] || {{ echo "Name a variant: $VARIANTS" >&2; exit 2; }}
pick "$VAR"; shift
DO_P=1; DO_G=1
if [ $# -gt 0 ]; then DO_P=0; DO_G=0; for a in "$@"; do
    case "$a" in --plymouth) DO_P=1 ;; --grub) DO_G=1 ;; esac; done; fi
# Check first: check everything, then change. Fedora does not bring
# Plymouth's script plugin by default (lab VM, 24.10.2026); without this
# check the script stopped in the middle of the Plymouth part.
problems=""
if [ $DO_P = 1 ]; then
    command -v plymouth-set-default-theme >/dev/null || problems="$problems\n- plymouth-set-default-theme is missing"
    found=""
    for d in /usr/lib64/plymouth /usr/lib/plymouth /usr/lib/x86_64-linux-gnu/plymouth /usr/lib/aarch64-linux-gnu/plymouth; do
        [ -f "$d/script.so" ] && found=1
    done
    [ -n "$found" ] || problems="$problems\n- Plymouth's script plugin is missing: Fedora 'sudo dnf install plymouth-plugin-script', Debian/Ubuntu 'sudo apt install plymouth-themes', Arch: in the package plymouth"
fi
if [ $DO_G = 1 ]; then
    [ -n "$GD" ] || problems="$problems\n- no GRUB directory (/boot/grub2 or /boot/grub)"
    [ -f /etc/default/grub ] || problems="$problems\n- /etc/default/grub is missing"
    command -v grub2-mkconfig >/dev/null || command -v grub-mkconfig >/dev/null || command -v update-grub >/dev/null \
        || problems="$problems\n- grub-mkconfig is missing"
fi
if [ -n "$problems" ]; then
    printf "Nothing changed. Fix first:%b\n" "$problems" >&2
    printf "To install one part: --plymouth or --grub\n" >&2
    exit 1
fi
mkdir -p "$BK"; touch "$BK/installed"
if [ $DO_P = 1 ]; then
    [ -f "$BK/plymouth-theme" ] || plymouth-set-default-theme > "$BK/plymouth-theme"
    [ -e "/usr/share/plymouth/themes/$PLY" ] && remove_own "/usr/share/plymouth/themes/$PLY"
    cp -r "$HERE/system/plymouth/$PLY" /usr/share/plymouth/themes/
    echo "/usr/share/plymouth/themes/$PLY" >> "$BK/installed"
    plymouth-set-default-theme "$PLY"
    echo "rebuilding the initramfs …"; regen_initrd
    # Fedora turns Plymouth on with rhgb, Debian/Ubuntu/Arch with splash.
    grep -qwE 'splash|rhgb' /proc/cmdline || echo "NOTE: neither 'splash' nor 'rhgb' on the kernel command line — Plymouth then stays invisible."
fi
if [ $DO_G = 1 ]; then
    [ -f "$BK/default-grub" ] || cp -a /etc/default/grub "$BK/default-grub"
    mkdir -p "$GD/themes"
    [ -e "$GD/themes/$GRUBT" ] && remove_own "$GD/themes/$GRUBT"
    cp -r "$HERE/system/grub/$GRUBT" "$GD/themes/"
    echo "$GD/themes/$GRUBT" >> "$BK/installed"
    # Under Secure Boot GRUB (2.06 on) loads no font files — then name the
    # built-in Unifont, else the name points nowhere (measured in the lab
    # VM; CDE/TESTING.md describes the same).
    sb=0
    for f in /sys/firmware/efi/efivars/SecureBoot-*; do
        [ -f "$f" ] && [ "$(od -An -t u1 -j4 -N1 "$f" | tr -d ' ')" = 1 ] && sb=1
    done
    if [ $sb = 1 ]; then
        sed -i -E 's/^(\\s*(item_)?font = )".*"/\\1"Unifont Regular 16"/' "$GD/themes/$GRUBT/theme.txt"
        echo "Secure Boot is on: GRUB loads no font files, the menu uses the built-in Unifont."
    fi
    sed -i '/^GRUB_THEME=/d' /etc/default/grub
    echo "GRUB_THEME=\\"$GD/themes/$GRUBT/theme.txt\\"" >> /etc/default/grub
    # GRUB_TERMINAL_OUTPUT=console turns graphics off — then no theme shows.
    sed -i 's/^\\(GRUB_TERMINAL\\(_OUTPUT\\)\\?=.*console.*\\)/#\\1  # theme-forge/' /etc/default/grub
    grep -q '^GRUB_GFXMODE=' /etc/default/grub || echo 'GRUB_GFXMODE=auto' >> /etc/default/grub
    regen_grub
fi
echo "Done. Undo: sudo $0 --revert"
'''

CONFIGS = "kdeglobals kwinrc plasmarc ksplashrc kcminputrc kscreenlockerrc konsolerc"


def write_all(spec, pkg, variants):
    ids = " ".join(v.v["id"] for v in variants)
    vmap = "\n".join(f'    {v.v["id"]}) LNF={v.lnf}; PLY={v.id}; GRUBT={v.camel}; WALL={v.id}; KPROF={v.camel} ;;'
                     for v in variants)
    from . import fonts
    d = spec["decoration"]
    common = COMMON.format(theme=spec["id"], ids=ids, vmap=vmap, font=fonts.CATALOG[spec["font"]][0],
                           bl=d["buttons_left"].replace("_", ""), br=d["buttons_right"].replace("_", ""))
    args = dict(name=spec["name"], ids=ids, common=common, first=variants[0].v["id"], configs=CONFIGS)
    for fname, tmpl in (("install.sh", INSTALL), ("uninstall.sh", UNINSTALL),
                        ("install-system.sh", SYSTEM)):
        path = os.path.join(pkg, fname)
        with open(path, "w") as f:
            f.write(tmpl.format(**args))
        os.chmod(path, 0o755)
