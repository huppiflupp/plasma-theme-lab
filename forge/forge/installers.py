"""Die drei Shell-Skripte im Paket: install.sh, uninstall.sh, install-system.sh.

Benutzer- und Systemschicht sind getrennt (guide/01): install.sh braucht kein
sudo und kann nichts am Start kaputtmachen; install-system.sh sichert vor
jeder Änderung und kann alles mit --revert zurücknehmen.

Löschen nur mit ${VAR:?}-Schutz und nur Pfade, die mit einer erwarteten
Wurzel beginnen — ein leeres oder verdorbenes Manifest darf nie mehr
treffen als die eigenen Dateien.
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
    *) echo "Unbekannte Variante: $1 (vorhanden: $VARIANTS)" >&2; exit 2 ;;
    esac
}}
'''

INSTALL = '''#!/usr/bin/env bash
# {name} — Installation nur im eigenen Benutzerkonto, ohne sudo.
#   ./install.sh                  Dateien nach ~/.local/share kopieren
#   ./install.sh --apply <var>    zusätzlich anwenden (Varianten: {ids})
# Rückgängig: ./uninstall.sh
{common}
D="${{XDG_DATA_HOME:-$HOME/.local/share}}"
C="${{XDG_CONFIG_HOME:-$HOME/.config}}"
STATE="$D/theme-forge/$THEME"
mkdir -p "$STATE"
MAN="$STATE/manifest"
: > "$MAN.new"
copy_tree() {{   # Quelle Ziel
    [ -d "$HERE/$1" ] || return 0
    (cd "$HERE/$1" && find . -type f) | while read -r f; do
        mkdir -p "$(dirname "$2/$f")"
        # Neue Inode statt Überschreiben: plasmashell hält Dateien gemappt.
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
fc-cache -f "$D/fonts" >/dev/null 2>&1 || true
echo "Installiert: $(wc -l < "$MAN") Dateien (Liste: $MAN)"

if [ "${{1:-}}" = "--apply" ]; then
    VAR="${{2:-{first}}}"; pick "$VAR"
    BK="$STATE/backup"
    if [ ! -d "$BK" ]; then     # nur die ERSTE Sicherung zählt
        mkdir -p "$BK"
        for f in {configs}; do
            if [ -f "$C/$f" ]; then cp -a "$C/$f" "$BK/$f"; else touch "$BK/$f.absent"; fi
        done
        kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage > "$BK/lookandfeel" 2>/dev/null || true
    fi
    plasma-apply-lookandfeel -a "$LNF"
    # Was ein Global Theme nicht setzt (im Lab gemessen): Knopfreihenfolge,
    # Titelschrift, Konsole-Standardprofil.
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft "$BUTTONS_LEFT"
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "$BUTTONS_RIGHT"
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "$FONT,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile "$KPROF.profile"
    IMG="$D/wallpapers/$WALL/contents/images/1920x1080.jpg"
    # Ein Global Theme ersetzt keinen Hintergrund, den ein anderes Theme fest
    # gesetzt hat (VM mit Warp Legacy, 24.10.2026) — daher ausdrücklich.
    plasma-apply-wallpaperimage "$D/wallpapers/$WALL" >/dev/null 2>&1 || true
    # Icon-Cache neu, sonst zeigt KIconLoader noch die alten Symbole
    rm -f "$HOME/.cache/icon-cache.kcache"
    kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image \\
        --group General --key Image "file://$IMG"
    dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure || true
    echo "Angewandt: $LNF — vollständig erst nach Ab- und Anmelden."
fi
'''

UNINSTALL = '''#!/usr/bin/env bash
# {name} — entfernt die Dateien und stellt die Konfiguration von vor dem
# ersten --apply wieder her.
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
# Nur Dateien unterhalb von $D löschen, egal was im Manifest steht.
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
echo "Entfernt. Ab- und Anmelden, damit alles zurückgesetzt ist."
'''

SYSTEM = '''#!/usr/bin/env bash
# {name} — Startbildschirm (Plymouth) und Bootmenü (GRUB).
# ACHTUNG: schreibt nach /usr/share, /boot und /etc/default/grub und baut die
# initramfs neu. Ein Fehler hier kann den Start verhindern. Vorher sichern.
#   sudo ./install-system.sh <variante> [--plymouth] [--grub]   (ohne Schalter: beides)
#   sudo ./install-system.sh --revert
{common}
[ "$(id -u)" = 0 ] || {{ echo "Bitte mit sudo starten." >&2; exit 1; }}
BK="/var/lib/theme-forge/$THEME"
if [ -d /boot/grub2 ]; then GD=/boot/grub2; elif [ -d /boot/grub ]; then GD=/boot/grub; else GD=""; fi
regen_grub() {{
    if command -v grub2-mkconfig >/dev/null; then grub2-mkconfig -o "$GD/grub.cfg"
    elif command -v update-grub >/dev/null; then update-grub
    elif command -v grub-mkconfig >/dev/null; then grub-mkconfig -o "$GD/grub.cfg"
    else echo "WARNUNG: kein grub-mkconfig gefunden" >&2; fi
}}
regen_initrd() {{
    if command -v dracut-rebuild >/dev/null; then dracut-rebuild
    elif command -v dracut >/dev/null; then dracut --force
    elif command -v update-initramfs >/dev/null; then update-initramfs -u
    elif command -v mkinitcpio >/dev/null; then mkinitcpio -P
    fi
}}
# Entfernt nur eigene Theme-Ordner (Plymouth/GRUB), nie etwas anderes.
remove_own() {{
    case "$1" in
        /usr/share/plymouth/themes/?*|/boot/grub2/themes/?*|/boot/grub/themes/?*) rm -r -- "$1" ;;
        *) echo "übersprungen (unerwarteter Pfad): $1" >&2 ;;
    esac
}}
if [ "${{1:-}}" = "--revert" ]; then
    [ -d "$BK" ] || {{ echo "Keine Sicherung in $BK." >&2; exit 1; }}
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
    echo "Zurückgesetzt."
    exit 0
fi
VAR="${{1:-}}"; [ -n "$VAR" ] || {{ echo "Variante angeben: $VARIANTS" >&2; exit 2; }}
pick "$VAR"; shift
DO_P=1; DO_G=1
if [ $# -gt 0 ]; then DO_P=0; DO_G=0; for a in "$@"; do
    case "$a" in --plymouth) DO_P=1 ;; --grub) DO_G=1 ;; esac; done; fi
# Vorabprüfung: erst alles prüfen, dann ändern. Fedora bringt das Script-
# Plugin von Plymouth nicht von Haus aus mit (Test-VM, 24.10.2026) — ohne
# diese Prüfung brach das Skript mitten im Plymouth-Teil ab.
problems=""
if [ $DO_P = 1 ]; then
    command -v plymouth-set-default-theme >/dev/null || problems="$problems\n- plymouth-set-default-theme fehlt"
    found=""
    for d in /usr/lib64/plymouth /usr/lib/plymouth /usr/lib/x86_64-linux-gnu/plymouth /usr/lib/aarch64-linux-gnu/plymouth; do
        [ -f "$d/script.so" ] && found=1
    done
    [ -n "$found" ] || problems="$problems\n- Plymouth-Script-Plugin fehlt: Fedora 'sudo dnf install plymouth-plugin-script', Debian/Ubuntu 'sudo apt install plymouth-themes', Arch: im Paket plymouth"
fi
if [ $DO_G = 1 ]; then
    [ -n "$GD" ] || problems="$problems\n- kein GRUB-Verzeichnis (/boot/grub2 oder /boot/grub)"
    [ -f /etc/default/grub ] || problems="$problems\n- /etc/default/grub fehlt"
    command -v grub2-mkconfig >/dev/null || command -v grub-mkconfig >/dev/null || command -v update-grub >/dev/null \
        || problems="$problems\n- grub-mkconfig fehlt"
fi
if [ -n "$problems" ]; then
    printf "Nichts geändert. Vorher beheben:%b\n" "$problems" >&2
    printf "Einzeln installieren: --plymouth oder --grub\n" >&2
    exit 1
fi
mkdir -p "$BK"; touch "$BK/installed"
if [ $DO_P = 1 ]; then
    [ -f "$BK/plymouth-theme" ] || plymouth-set-default-theme > "$BK/plymouth-theme"
    [ -e "/usr/share/plymouth/themes/$PLY" ] && remove_own "/usr/share/plymouth/themes/$PLY"
    cp -r "$HERE/system/plymouth/$PLY" /usr/share/plymouth/themes/
    echo "/usr/share/plymouth/themes/$PLY" >> "$BK/installed"
    plymouth-set-default-theme "$PLY"
    echo "initramfs wird neu gebaut …"; regen_initrd
    # Fedora schaltet Plymouth mit rhgb ein, Debian/Ubuntu/Arch mit splash.
    grep -qwE 'splash|rhgb' /proc/cmdline || echo "HINWEIS: weder 'splash' noch 'rhgb' in der Kernel-Befehlszeile — Plymouth bleibt dann unsichtbar."
fi
if [ $DO_G = 1 ]; then
    [ -f "$BK/default-grub" ] || cp -a /etc/default/grub "$BK/default-grub"
    mkdir -p "$GD/themes"
    [ -e "$GD/themes/$GRUBT" ] && remove_own "$GD/themes/$GRUBT"
    cp -r "$HERE/system/grub/$GRUBT" "$GD/themes/"
    echo "$GD/themes/$GRUBT" >> "$BK/installed"
    # Unter Secure Boot lädt GRUB (ab 2.06) keine Schriftdateien — dann die
    # eingebaute Unifont nennen, sonst bleibt der Name ins Leere zeigend
    # (gemessen in der Test-VM; CDE/TESTING.md beschreibt dasselbe).
    sb=0
    for f in /sys/firmware/efi/efivars/SecureBoot-*; do
        [ -f "$f" ] && [ "$(od -An -t u1 -j4 -N1 "$f" | tr -d ' ')" = 1 ] && sb=1
    done
    if [ $sb = 1 ]; then
        sed -i -E 's/^(\\s*(item_)?font = )".*"/\\1"Unifont Regular 16"/' "$GD/themes/$GRUBT/theme.txt"
        echo "Secure Boot ist an: GRUB lädt keine Schriftdateien, das Menü nutzt die eingebaute Unifont."
    fi
    sed -i '/^GRUB_THEME=/d' /etc/default/grub
    echo "GRUB_THEME=\\"$GD/themes/$GRUBT/theme.txt\\"" >> /etc/default/grub
    # GRUB_TERMINAL_OUTPUT=console schaltet die Grafik ab — dann sieht man kein Theme.
    sed -i 's/^\\(GRUB_TERMINAL\\(_OUTPUT\\)\\?=.*console.*\\)/#\\1  # theme-forge/' /etc/default/grub
    grep -q '^GRUB_GFXMODE=' /etc/default/grub || echo 'GRUB_GFXMODE=auto' >> /etc/default/grub
    regen_grub
fi
echo "Fertig. Rückgängig: sudo $0 --revert"
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
