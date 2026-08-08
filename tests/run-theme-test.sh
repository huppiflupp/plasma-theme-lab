#!/usr/bin/env bash
# Spielt ein Theme in der Test-VM durch und haelt fest, was passiert.
#
#   ./run-theme-test.sh <theme-verzeichnis> [<installbefehl>]
#
# Ablauf: zurueck auf den Snapshot 'clean' -> Theme hineinkopieren ->
# installieren -> anwenden -> Screenshot -> neu starten -> Screenshot ->
# deinstallieren -> pruefen, ob der Ausgangszustand wieder da ist.
#
# Der Neustart ist der wichtigste Schritt und wird am haeufigsten
# uebersprungen: Ein kaputtes Theme faellt meist erst beim naechsten
# Anmelden auf.

set -uo pipefail   # kein -e: ein fehlgeschlagener Schritt ist ein
                   # Testergebnis, kein Grund zum Abbruch

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"

THEME_DIR="${1:?Aufruf: $0 <theme-verzeichnis> [<installbefehl>]}"
INSTALL_CMD="${2:-./install.sh}"

[ -d "$THEME_DIR" ] || { echo "FEHLER: $THEME_DIR gibt es nicht"; exit 1; }

NAME="$(basename "$THEME_DIR")"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$LAB/tests/laeufe/$NAME-$STAMP"
mkdir -p "$OUT/screenshots"
BERICHT="$OUT/bericht.md"

schritt=0
notiz() { echo -e "$*" | tee -a "$BERICHT"; }
ssh_() { "$VMCTL" ssh "$@" 2>&1; }
shot() {
    schritt=$((schritt+1))
    local datei="$OUT/screenshots/$(printf '%02d' $schritt)-$1.png"
    "$VMCTL" shot "$datei" >/dev/null 2>&1
    echo "  Screenshot: ${datei#$LAB/}"
}

{
    echo "# Testlauf: $NAME"
    echo
    echo "- Zeitpunkt: $(date -Is)"
    echo "- Quelle: \`$THEME_DIR\`"
    echo "- Installbefehl: \`$INSTALL_CMD\`"
    echo
} > "$BERICHT"

# ---------------------------------------------------------------------------
notiz "## 1. Ausgangszustand herstellen"
# Ohne Reset testet der zweite Durchlauf auf den Resten des ersten.
if ! "$VMCTL" reset >/dev/null 2>&1; then
    notiz "FEHLER: Zuruecksetzen auf Snapshot 'clean' fehlgeschlagen."
    notiz "Gibt es den Snapshot? \`vm/vmctl.sh snap list\`"
    exit 1
fi
notiz "VM auf Snapshot 'clean' zurueckgesetzt."

VORHER="$(ssh_ 'for k in \
    "plasmarc Theme name" \
    "kdeglobals General ColorScheme" \
    "kdeglobals KDE widgetStyle" \
    "kdeglobals Icons Theme" \
    "kdeglobals KDE LookAndFeelPackage" \
    "kwinrc org.kde.kdecoration2 library"; do
      set -- $k; echo "$1/$2/$3 = $(kreadconfig6 --file $1 --group $2 --key $3)"
    done')"
notiz "\n<details><summary>Konfiguration vorher</summary>\n\n\`\`\`\n$VORHER\n\`\`\`\n</details>"
shot ausgangszustand

# ---------------------------------------------------------------------------
notiz "\n## 2. Theme uebertragen und installieren"
# Die Schraegstriche am Ende sind nicht kosmetisch: ohne sie legt rsync
# das Quellverzeichnis IM Ziel an (/home/tester/theme/niceos9/) statt
# dessen Inhalt hineinzukopieren - und dann findet der Installbefehl
# seine eigene install.sh nicht.
"$VMCTL" push "${THEME_DIR%/}/" "/home/tester/theme/" >/dev/null 2>&1 \
    || { notiz "FEHLER beim Kopieren."; exit 1; }
if ! ssh_ 'test -d /home/tester/theme' >/dev/null 2>&1; then
    notiz "FEHLER: /home/tester/theme fehlt nach dem Kopieren."; exit 1
fi

# Die Installation laeuft ohne Terminal. Ein Installer, der interaktiv
# nachfragt, wuerde haengen - deshalb entweder vorbereitete Antworten aus
# $ANTWORTEN oder stdin aus /dev/null, dazu ein Timeout als Notbremse.
#
#   ANTWORTEN='y\ny\nn\nn\nn\n' ./run-theme-test.sh ../niceos9
#
if [ -n "${ANTWORTEN:-}" ]; then
    notiz "\nVorbereitete Antworten auf die Installer-Rueckfragen: \`$ANTWORTEN\`"
    LOG_INSTALL="$(ssh_ "cd /home/tester/theme && printf '%b' '$ANTWORTEN' | timeout 300 $INSTALL_CMD")"
else
    LOG_INSTALL="$(ssh_ "cd /home/tester/theme && timeout 300 $INSTALL_CMD < /dev/null")"
fi
RC=$?
notiz "\nRueckgabewert: \`$RC\`"
[ "$RC" -eq 124 ] && notiz "**Zeitueberschreitung** - der Installer wartet vermutlich auf eine Eingabe."
notiz "\n<details><summary>Ausgabe des Installers</summary>\n\n\`\`\`\n$LOG_INSTALL\n\`\`\`\n</details>"

# ---------------------------------------------------------------------------
notiz "\n## 3. Was wurde installiert?"
NEU="$(ssh_ 'find ~/.local/share/plasma ~/.local/share/color-schemes \
    ~/.local/share/aurorae ~/.local/share/icons ~/.local/share/wallpapers \
    -maxdepth 2 -mindepth 1 -newer /etc/plasma-lab-ready 2>/dev/null | sort')"
notiz "\n\`\`\`\n${NEU:-(nichts gefunden)}\n\`\`\`"

# Aenderungen ausserhalb von $HOME sind das eigentliche Risiko.
SYS="$(ssh_ 'sudo find /usr/share/sddm /usr/share/plymouth /boot/grub2 /etc/sddm.conf.d \
    -newer /etc/plasma-lab-ready 2>/dev/null | head -30')"
if [ -n "$SYS" ]; then
    notiz "\n**Achtung - ausserhalb von \$HOME veraendert:**\n\n\`\`\`\n$SYS\n\`\`\`"
else
    notiz "\nKeine Aenderungen ausserhalb von \$HOME. Gut."
fi

# ---------------------------------------------------------------------------
notiz "\n## 4. Theme anwenden"
# kpackagetool6 schreibt eine Statuszeile ("KPackageType wird aufgelistet:
# ... in ...") auf dieselbe Ausgabe wie die Paketnamen. Echte Ids
# enthalten weder Leerzeichen noch Doppelpunkte - danach wird gefiltert.
LNF="$(ssh_ 'kpackagetool6 -t Plasma/LookAndFeel -l 2>/dev/null' \
       | grep -E '^[A-Za-z0-9][A-Za-z0-9._+-]*$' | head -20)"
notiz "\nVerfuegbare globale Designs:\n\n\`\`\`\n${LNF:-(keines gefunden)}\n\`\`\`"

ZIEL="$(echo "$LNF" | grep -iv breeze | head -1)"
if [ -n "$ZIEL" ]; then
    notiz "\nWende an: \`$ZIEL\` (bewusst OHNE --resetLayout)"
    ANWENDEN="$(ssh_ "plasma-apply-lookandfeel --apply '$ZIEL'")"
    notiz "\n\`\`\`\n$ANWENDEN\n\`\`\`"
    sleep 15
    shot nach-anwenden

    # Gegenprobe: hat sich ueberhaupt etwas geaendert? Ein identisches
    # Bild heisst, dass das Anwenden wirkungslos war - genau der Fall,
    # den der erste Durchlauf dieses Harness uebersehen hat, weil er nur
    # auf "plasmashell laeuft noch" geachtet hat.
    A="$OUT/screenshots/01-ausgangszustand.png"
    B="$OUT/screenshots/02-nach-anwenden.png"
    if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then
        notiz "\n**Der Bildschirm ist unveraendert.** Das Anwenden hatte keine sichtbare Wirkung."
    else
        notiz "\nDer Bildschirm hat sich sichtbar veraendert."
    fi

    IST="$(ssh_ 'echo "Plasma Style : $(kreadconfig6 --file plasmarc --group Theme --key name)"
echo "Farbschema   : $(kreadconfig6 --file kdeglobals --group General --key ColorScheme)"
echo "Globales Des.: $(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)"
echo "Icons        : $(kreadconfig6 --file kdeglobals --group Icons --key Theme)"
echo "Dekoration   : $(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)"
echo "Stil         : $(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)"')"
    notiz "\nWas tatsaechlich gesetzt wurde:\n\n\`\`\`\n$IST\n\`\`\`"
    notiz "\nZum Vergleich das Soll aus \`contents/defaults\`:\n"
    SOLL="$(ssh_ "cat ~/.local/share/plasma/look-and-feel/$ZIEL/contents/defaults 2>/dev/null")"
    notiz "\`\`\`ini\n${SOLL:-(keine defaults-Datei)}\n\`\`\`"
else
    notiz "\nKein eigenes globales Design gefunden - uebersprungen."
fi

# ---------------------------------------------------------------------------
notiz "\n## 5. Laeuft die Shell noch?"
SHELL_ST="$(ssh_ 'systemctl --user is-active plasma-plasmashell.service; \
                  systemctl --user show plasma-plasmashell.service -p NRestarts --value')"
notiz "\n\`\`\`\n$SHELL_ST\n\`\`\`"
case "$SHELL_ST" in
    active*) notiz "\nplasmashell laeuft." ;;
    *)       notiz "\n**plasmashell laeuft NICHT.** Das ist ein Fehlschlag." ;;
esac

FEHLER="$(ssh_ 'journalctl --user -u plasma-plasmashell.service --since "-10 min" \
    -p warning --no-pager 2>/dev/null | tail -25')"
[ -n "$FEHLER" ] && notiz "\n<details><summary>Warnungen im Journal</summary>\n\n\`\`\`\n$FEHLER\n\`\`\`\n</details>"

# ---------------------------------------------------------------------------
notiz "\n## 6. Neustart - ueberlebt das Theme eine neue Sitzung?"
# Der wichtigste Test. Viele Themes sehen bis zum Abmelden gut aus.
ssh_ 'sudo systemctl reboot' >/dev/null 2>&1
sleep 20
bereit=false
for _ in $(seq 1 30); do
    if "$VMCTL" ssh 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1; then bereit=true; break; fi
    sleep 10
done
if $bereit; then
    sleep 25                       # Zeit fuer Autologin und Sitzungsaufbau
    notiz "\nVM ist nach dem Neustart wieder erreichbar."
    NACH_ST="$(ssh_ 'systemctl --user is-active plasma-plasmashell.service')"
    notiz "plasmashell: \`$NACH_ST\`"
    shot nach-neustart
else
    notiz "\n**Die VM kam nach dem Neustart nicht zurueck.** Schwerwiegend."
    shot neustart-fehlgeschlagen
fi

# ---------------------------------------------------------------------------
notiz "\n## 7. Deinstallation"
if ssh_ 'test -x /home/tester/theme/uninstall.sh' >/dev/null 2>&1; then
    # Der Uninstaller stellt dieselben Rueckfragen wie der Installer.
    # Ohne Antworten waehlt er nichts aus und raeumt nichts weg - und der
    # Test wuerde faelschlich "nichts uebrig" oder "nichts geprueft" melden.
    ANTWORTEN_UNINSTALL="${ANTWORTEN_UNINSTALL:-${ANTWORTEN:-}}"
    if [ -n "$ANTWORTEN_UNINSTALL" ]; then
        LOG_UNINST="$(ssh_ "cd /home/tester/theme && printf '%b' '$ANTWORTEN_UNINSTALL' | timeout 180 ./uninstall.sh")"
    else
        LOG_UNINST="$(ssh_ 'cd /home/tester/theme && timeout 180 ./uninstall.sh < /dev/null')"
    fi
    notiz "\n<details><summary>Ausgabe</summary>\n\n\`\`\`\n$LOG_UNINST\n\`\`\`\n</details>"

    NACHHER="$(ssh_ 'for k in \
        "plasmarc Theme name" \
        "kdeglobals General ColorScheme" \
        "kdeglobals KDE widgetStyle" \
        "kdeglobals Icons Theme" \
        "kdeglobals KDE LookAndFeelPackage" \
        "kwinrc org.kde.kdecoration2 library"; do
          set -- $k; echo "$1/$2/$3 = $(kreadconfig6 --file $1 --group $2 --key $3)"
        done')"
    notiz "\n### Konfiguration: vorher gegen nachher\n"
    DIFF="$(diff <(echo "$VORHER") <(echo "$NACHHER"))"
    if [ -z "$DIFF" ]; then
        notiz "Deckungsgleich - die Deinstallation ist vollstaendig."
    else
        notiz "**Unterschiede - die Deinstallation raeumt nicht auf:**\n\n\`\`\`diff\n$DIFF\n\`\`\`"
    fi
    REST="$(ssh_ 'find ~/.local/share/plasma ~/.local/share/aurorae ~/.local/share/color-schemes \
        -maxdepth 2 -mindepth 1 2>/dev/null | sort')"
    [ -n "$REST" ] && notiz "\nUebriggebliebene Dateien:\n\n\`\`\`\n$REST\n\`\`\`"
else
    notiz "\nKein \`uninstall.sh\` vorhanden - nicht pruefbar."
fi

shot ende

notiz "\n---\n\nBericht: \`${BERICHT#$LAB/}\`"
echo
echo "Fertig. Bericht: $BERICHT"
