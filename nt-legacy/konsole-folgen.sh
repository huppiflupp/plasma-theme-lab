#!/usr/bin/env bash
# Zieht das Konsole-Farbschema dem Globalen Design nach.
#
#   ./konsole-folgen.sh            # einmal nachziehen
#   ./konsole-folgen.sh --zeigen   # nur sagen, was es taete
#
# Warum es das braucht:
#
# Konsole folgt dem Farbschema des Systems nicht. Das ist keine Luecke
# in diesem Theme, sondern eine Eigenschaft des Programms: Das Farbschema
# eines Terminals steht im PROFIL, und ein Profil ist eine Datei, die
# Konsole allein verwaltet. Plasma fasst sie beim Designwechsel nicht an,
# und Konsole hat keinen Schalter "dem System folgen".
#
# apply.sh stellt die Zeile deshalb selbst um. Nur: wer das Design ueber
# Systemeinstellungen > Design wechselt, ruft apply.sh nie auf - und
# genau das ist der uebliche Weg. Das Terminal blieb dann in der alten
# Farbwelt stehen, waehrend alles andere umsprang.
#
# Dieses Skript schliesst die Luecke. Es wird nicht dauernd ausgefuehrt,
# sondern von einer systemd-Pfadeinheit angestossen, wenn Plasma seine
# Vorgabendateien schreibt (siehe anmutung.sh).
#
# Grenze, die bleibt: Ein BEREITS OFFENES Konsole-Fenster behaelt seine
# Farben. Konsole liest das Profil beim Anlegen einer Sitzung; ein Weg,
# ihm von aussen ein erneutes Einlesen zu befehlen, existiert nicht
# (weder ueber D-Bus noch ueber ein Signal). Das naechste neue Fenster
# oder Unterfenster kommt richtig.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
KONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"

ZEIGEN=false
[ "${1:-}" = "--zeigen" ] && ZEIGEN=true

PROFIL="$DATEN/konsole/NT Legacy.profile"

# Die Zuordnung kommt aus build.py, nicht aus einer zweiten Liste hier.
# Im Arbeitsbaum liegt sie neben diesem Skript, installiert unter
# nt-legacy/. Fehlt sie, ist das kein Fehler des Nutzers, sondern ein
# unvollstaendiges Paket - deshalb eine Meldung und kein stilles Ende.
TABELLE=""
for kandidat in "$HIER/konsole-varianten.tsv" \
                "$DATEN/nt-legacy/konsole-varianten.tsv"; do
    [ -f "$kandidat" ] && { TABELLE="$kandidat"; break; }
done
if [ -z "$TABELLE" ]; then
    echo "konsole-folgen: konsole-varianten.tsv nicht gefunden." >&2
    exit 1
fi

# Welches Globale Design gilt gerade?
#
# ~/.config/kdedefaults/package ist die verlaesslichere Quelle: Plasma
# schreibt sie beim Anwenden, und sie enthaelt genau eine Zeile mit der
# Kennung. kdeglobals wird nachrangig gelesen - dort steht der Wert nur,
# wenn ihn jemand ausdruecklich gesetzt hat (etwa apply.sh).
DESIGN=""
if [ -f "$KONFIG/kdedefaults/package" ]; then
    DESIGN="$(tr -d '\r\n' < "$KONFIG/kdedefaults/package")"
fi
if [ -z "$DESIGN" ] && command -v kreadconfig6 >/dev/null; then
    DESIGN="$(kreadconfig6 --file kdeglobals --group KDE \
                           --key LookAndFeelPackage 2>/dev/null || true)"
fi
if [ -z "$DESIGN" ]; then
    $ZEIGEN && echo "Kein Globales Design ermittelbar - nichts zu tun."
    exit 0
fi

SCHEMA="$(awk -F'\t' -v d="$DESIGN" '$1 == d { print $2; exit }' "$TABELLE")"

# Ein fremdes Design ist der Normalfall, kein Fehler: Wer von NT Legacy
# auf Breeze wechselt, soll sein Terminal behalten. Es waere uebergriffig,
# ihm dann ein NT-Schema hineinzuschreiben - und genauso falsch, ihm das
# Breeze-Schema aufzuzwingen, das er vielleicht nie wollte.
if [ -z "$SCHEMA" ]; then
    $ZEIGEN && echo "'$DESIGN' gehoert nicht zu NT Legacy - Profil bleibt."
    exit 0
fi

if [ ! -f "$PROFIL" ]; then
    $ZEIGEN && echo "Profil '$PROFIL' fehlt - erst ./install.sh."
    exit 0
fi

ALT="$(kreadconfig6 --file "$PROFIL" --group Appearance \
                    --key ColorScheme 2>/dev/null || true)"

if [ "$ALT" = "$SCHEMA" ]; then
    $ZEIGEN && echo "Schon richtig: $DESIGN -> $SCHEMA"
    exit 0
fi

if $ZEIGEN; then
    echo "Wuerde setzen: $DESIGN -> $SCHEMA (steht auf '${ALT:-nichts}')"
    exit 0
fi

kwriteconfig6 --file "$PROFIL" --group Appearance --key ColorScheme "$SCHEMA"
echo "konsole-folgen: $DESIGN -> $SCHEMA"
