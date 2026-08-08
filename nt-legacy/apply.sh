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
SCHRIFT=false
for arg in "$@"; do
    [[ "$arg" == "--rot" ]] && ROT=true
    [[ "$arg" == "--schrift" ]] && SCHRIFT=true
done
[[ "$VARIANTE" == --* ]] && VARIANTE="teal"

# Die Kennungen kommen aus build.py, nicht aus einer zweiten Liste hier.
# Frueher standen sie doppelt - beim Hinzufuegen von win98/win2k wurde nur
# build.py gepflegt, und die neuen Varianten waren ueber apply.sh gar
# nicht erreichbar. Eine Wahrheit, kein Abgleich noetig.
KENNUNG=$(cd "$HIER" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTEN:
    print('UNBEKANNT ' + ' '.join(sorted(m.VARIANTEN)))
else:
    i = m.ids(v)
    print(i['schema'], i['style'], i['lnf'])
" "$VARIANTE")

if [ "${KENNUNG%% *}" = "UNBEKANNT" ]; then
    echo "Unbekannte Variante '$VARIANTE'." >&2
    echo "Moeglich: ${KENNUNG#UNBEKANNT }" >&2
    exit 1
fi
read -r KURZ STYLE LNF <<< "$KENNUNG"

# Trockenlauf: nur pruefen, ob die Variante existiert, nichts anwenden.
# Wird von pruefe.sh genutzt.
for arg in "$@"; do [[ "$arg" == "--nur-pruefen" ]] && exit 0; done

# Die Zeiger gibt es nur einmal fuer alle Varianten - sie unterscheiden
# sich in weiss und rot, nicht nach Farbwelt. Frueher stand hier
# "${KURZ}_cursors", was fuer fuenf von sechs Varianten ins Leere lief.
ZEIGER="NTLegacy_cursors"
$ROT && ZEIGER="NTLegacyRot_cursors"

# Ist das Theme ueberhaupt installiert? Ohne diese Pruefung meldet das
# Skript Erfolg, schreibt alle Schluessel auf nicht vorhandene Themes und
# verweist auf eine Sicherung, die es nie gab.
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
if [ ! -d "$DATEN/plasma/look-and-feel/$LNF" ]; then
    echo "FEHLER: '$LNF' ist nicht installiert." >&2
    echo "        Erst  ./install.sh  ausfuehren." >&2
    exit 1
fi
if [ ! -d "$DATEN/icons/$ZEIGER" ]; then
    echo "Hinweis: Mauszeiger '$ZEIGER' fehlt - der Systemzeiger bleibt." >&2
    ZEIGER=""
fi

if $ROT; then echo "Wende an: $KURZ (roter Zeiger)"; else echo "Wende an: $KURZ"; fi

# Globales Design zuerst - es setzt den Rahmen, den Rest praezisieren wir
plasma-apply-lookandfeel --apply "$LNF" >/dev/null 2>&1 || true

kwriteconfig6 --file plasmarc   --group Theme   --key name          "$STYLE"
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   "$KURZ"
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle   Windows
kwriteconfig6 --file kdeglobals --group Icons   --key Theme         NTLegacy
kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage "$LNF"
[ -n "$ZEIGER" ] && kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$ZEIGER"
# Den eigenen Startbildschirm aktivieren. Weder plasma-apply-lookandfeel
# noch die defaults setzen ihn - ohne diese Zeile laeuft Splash.qml nie.
kwriteconfig6 --file ksplashrc  --group KSplash --key Theme  "$LNF"
kwriteconfig6 --file ksplashrc  --group KSplash --key Engine KSplashQML
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae.v2
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$KURZ"

# Die Titelschrift wird hier bewusst NICHT geschrieben.
#
# Sie steht als Vorgabe in contents/defaults - dort wirkt sie einmal beim
# Anwenden des Globalen Designs, und danach behaelt der Nutzer seine
# Wahl in Systemeinstellungen > Schriftarten > Fensterueberschrift.
# Wuerde apply.sh sie bei jedem Aufruf setzen, waere diese Einstellung
# wirkungslos. Breeze setzt aus demselben Grund gar keine Schrift.
#
# Wer die fette NT-Titelschrift ausdruecklich will:
#   ./apply.sh <variante> --schrift

if $SCHRIFT; then
    # Das fuenfte Feld einer Qt-Schriftangabe ist das Gewicht: 50 normal,
    # 75 fett. Aurorae kennt dafuer keine eigene Option.
    kwriteconfig6 --file kdeglobals --group WM --key activeFont \
        "Noto Sans,10,-1,5,75,0,0,0,0,0"
    echo "  Titelschrift auf fett gesetzt."
fi

# Der Render-Cache traegt Themename und -version. Ohne Loeschen sieht man
# nach einem Update das alte Bild und sucht den Fehler an der falschen Stelle.
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"

# --- Uebernehmen, ohne die Shell abzuschiessen ---------------------------
#
# Frueher stand hier ein bedingungsloses
#   systemctl --user restart plasma-plasmashell.service
# Das ist die gefaehrlichste Zeile, die dieses Skript je hatte:
# plasma-plasmashell.service erlaubt drei Starts in 60 Sekunden
# (StartLimitBurst=3, StartLimitIntervalSec=60s), und der Sitzungsstart
# zaehlt als erster. Beim DRITTEN apply.sh innerhalb einer Minute gibt
# systemd auf - kein Panel, kein Desktop, kein Anwendungsstarter. Und es
# erholt sich nicht von selbst; in der Test-VM war der Bildschirm auch
# nach 100 Sekunden noch schwarz.
#
# Genau so klickt aber, wer Designs ausprobiert: drei Varianten
# hintereinander.
#
# Deshalb jetzt drei Stufen:
#   1. plasma-apply-* schalten zur Laufzeit um - so macht es auch die
#      Systemsteuerung, ganz ohne Neustart.
#   2. KWin bekommt ein reconfigure statt eines Neustarts.
#   3. Nur wenn plasmashell danach wirklich nicht laeuft, wird gestartet -
#      mit vorherigem reset-failed, damit der Zaehler nicht im Weg steht.

plasma-apply-desktoptheme "$STYLE"  >/dev/null 2>&1 || true
plasma-apply-colorscheme  "$KURZ"   >/dev/null 2>&1 || true

# KWin die Dekoration neu einlesen lassen. Das Aurorae-THEMA selbst laedt
# KWin allerdings nur beim Sitzungsstart - deshalb der Hinweis unten.
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 \
    || qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

if command -v systemctl >/dev/null; then
    if ! systemctl --user is-active --quiet plasma-plasmashell.service; then
        echo "  plasmashell laeuft nicht - starte neu."
        # Ohne reset-failed greift die Startbegrenzung und der Start
        # wird verweigert.
        systemctl --user reset-failed plasma-plasmashell.service 2>/dev/null || true
        systemctl --user start plasma-plasmashell.service 2>/dev/null || true
    fi
fi

cat <<EOF

Angewendet.

  Damit die Fensterdekoration greift, einmal ab- und wieder anmelden.
  KWin laedt Aurorae-Themes ausschliesslich beim Sitzungsstart.

  Zurueck:   ~/.local/share/nt-legacy/backup-*/restore.sh
EOF
