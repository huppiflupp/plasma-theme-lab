#!/usr/bin/env bash
# Wendet eine NT-Legacy-Variante an.
#
#   ./apply.sh              # Grundfassung (Petrol)
#   ./apply.sh lilac        # Flieder
#   ./apply.sh desert       # Wueste
#   ./apply.sh teal-nacht   # Nachtfassung (auch lilac-nacht, desert-nacht)
#   ./apply.sh teal --rot   # mit rotem Mauszeiger
#
# Warum es dieses Skript gibt:
#
# Ein Look-and-Feel-Paket bringt seine Vorgaben in contents/defaults mit,
# und in der Theorie zieht Plasma sie daraus. In der Praxis - gemessen in
# der Test-VM ueber mehrere Sitzungsneustarts - greift davon nichts
# zuverlaessig: plasmarc/Theme, kdeglobals/ColorScheme, widgetStyle und
# Icons/Theme blieben leer, obwohl LookAndFeelPackage korrekt gesetzt war
# und die defaults-Datei die richtigen Werte enthielt.
#
# Deshalb setzt dieses Skript jede Ebene ausdruecklich. Das ist
# unschoen, aber es ist der Unterschied zwischen "Theme wirkt" und
# "Theme wirkt nicht".

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANTE="${1:-teal}"
ROT=false
[[ "${2:-}" == "--rot" || "${1:-}" == "--rot" ]] && ROT=true
[[ "$VARIANTE" == "--rot" ]] && VARIANTE="teal"

case "$VARIANTE" in
    teal)         KURZ="NTLegacy"            ;;
    lilac)        KURZ="NTLegacyLilac"       ;;
    desert)       KURZ="NTLegacyDesert"      ;;
    teal-nacht)   KURZ="NTLegacyNacht"       ;;
    lilac-nacht)  KURZ="NTLegacyLilacNacht"  ;;
    desert-nacht) KURZ="NTLegacyDesertNacht" ;;
    *) echo "Unbekannte Variante '$VARIANTE'." >&2
       echo "Moeglich: teal, lilac, desert und je -nacht" >&2
       exit 1 ;;
esac

# Style- und Paketnamen folgen dem Variantennamen; nur die Grundfassung
# traegt kein Suffix.
if [ "$VARIANTE" = "teal" ]; then
    STYLE="nt-legacy"; LNF_SUFFIX=""
else
    STYLE="nt-legacy-$VARIANTE"; LNF_SUFFIX="-$VARIANTE"
fi

LNF="com.github.huppiflupp.nt-legacy${LNF_SUFFIX}"
ZEIGER="${KURZ}_cursors"
$ROT && ZEIGER="${KURZ}Rot_cursors"

if $ROT; then echo "Wende an: $KURZ (roter Zeiger)"; else echo "Wende an: $KURZ"; fi

# Globales Design zuerst - es setzt den Rahmen, den Rest praezisieren wir
plasma-apply-lookandfeel --apply "$LNF" >/dev/null 2>&1 || true

kwriteconfig6 --file plasmarc   --group Theme   --key name          "$STYLE"
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   "$KURZ"
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle   Windows
kwriteconfig6 --file kdeglobals --group Icons   --key Theme         NTLegacy
kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage "$LNF"
kwriteconfig6 --file kcminputrc --group Mouse   --key cursorTheme   "$ZEIGER"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae.v2
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$KURZ"

# Fetter Titel im aktiven Fenster. Das fuenfte Feld ist das Gewicht:
# 50 normal, 75 fett. Aurorae kennt dafuer keine eigene Option.
kwriteconfig6 --file kdeglobals --group WM --key activeFont   "Noto Sans,10,-1,5,75,0,0,0,0,0"
kwriteconfig6 --file kdeglobals --group WM --key inactiveFont "Noto Sans,10,-1,5,50,0,0,0,0,0"

# Der Render-Cache traegt Themename und -version. Ohne Loeschen sieht man
# nach einem Update das alte Bild und sucht den Fehler an der falschen Stelle.
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"

# Shell neu starten, damit Plasma Style und Farben sofort greifen.
# Die Fensterdekoration braucht trotzdem eine neue Sitzung - KWin laedt
# Aurorae-Themes nur beim Start.
if command -v systemctl >/dev/null; then
    systemctl --user restart plasma-plasmashell.service 2>/dev/null || true
fi

cat <<EOF

Angewendet.

  Damit die Fensterdekoration greift, einmal ab- und wieder anmelden.
  KWin laedt Aurorae-Themes ausschliesslich beim Sitzungsstart.

  Zurueck:   ~/.local/share/nt-legacy/backup-*/restore.sh
EOF
