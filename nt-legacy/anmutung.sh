#!/usr/bin/env bash
# Stellt Programmeinstellungen auf die NT-Anmutung um - ausdruecklich
# getrennt vom Theme.
#
#   ./anmutung.sh            # anwenden
#   ./anmutung.sh --zurueck  # auf die vorherigen Werte zuruecksetzen
#   ./anmutung.sh --zeigen   # nur anzeigen, was gesetzt wuerde
#
# Warum das nicht in apply.sh steht:
#
# Ein Plasma-Theme darf Aussehen setzen - Farben, Rahmen, Dekoration. Es
# darf nicht die Einstellungen fremder Programme ueberschreiben. Wer ein
# Design ausprobiert, rechnet nicht damit, dass hinterher seine
# Dolphin-Konfiguration eine andere ist. Genau solche stillen
# Nebenwirkungen sind der Grund, warum ein Theme ein System unbrauchbar
# machen kann.
#
# Deshalb: eigenes Skript, ausdruecklicher Aufruf, vollstaendiger Rueckweg.

set -euo pipefail

DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
SICHERUNG="$DATEN/nt-legacy/anmutung-vorher.conf"

# Datei : Gruppe : Schluessel : NT-Wert : Begruendung
#
# Bewusst kurz gehalten. Jeder Eintrag hier ist ein Eingriff in ein
# fremdes Programm und muss sich rechtfertigen lassen.
EINSTELLUNGEN=(
  "dolphinrc:General:ShowStatusBar:FullWidth:durchgehende Statusleiste statt schwebendem Kaestchen"
  # PCManFM-Qt als Dateimanager. Gruende, gemessen in der Test-VM:
  #   - Qt6, also greift der Widget-Stil vollstaendig
  #   - echte Menueleiste statt Hamburger-Knopf
  #   - freier Speicherplatz als Text ueber die volle Breite; Dolphin
  #     zeichnet dort eine KCapacityBar, die sich selbst zeichnet und
  #     weder Palette noch Widget-Stil folgt (silberne Kapsel)
  "mimeapps.list:Default Applications:inode/directory:pcmanfm-qt.desktop:PCManFM-Qt als Dateimanager"
  # Ohne diesen Eintrag findet pcmanfm-qt das Icon-Thema nicht und faellt
  # auf oxygen zurueck - mitten im NT-Theme.
  "pcmanfm-qt/default/settings.conf:System:FallbackIconThemeName:NTLegacy:Icon-Thema fuer PCManFM-Qt"
  # Konsole auf das mitgelieferte Profil: Liberation Mono und ein
  # Farbschema aus den Farben der jeweiligen Fassung. install.sh legt
  # beides nur ab, aktiviert wird es erst hier. Das eigene Profil des
  # Nutzers bleibt bestehen und ist im Menue weiter waehlbar.
  "konsolerc:Desktop Entry:DefaultProfile:NT Legacy.profile:Konsole nutzt das NT-Profil"
  # Kate ohne die Textvorschau am rechten Rand.
  #
  # Was dort wie eine sehr breite Bildlaufleiste aussieht, ist keine:
  # Es ist Kates "Minimap", eine verkleinerte Darstellung des ganzen
  # Dokuments, die KTextEditor ANSTELLE der Bildlaufleiste zeichnet -
  # 60 Pixel breit statt der 16 des Widget-Stils. Sie kommt nicht vom
  # Theme, und kein Farbschema und kein Widget-Stil macht sie schmaler.
  #
  # Der Schluessel heisst "Scroll Bar MiniMap" - ohne Leerzeichen
  # zwischen Mini und Map, anders als die drei verwandten Schluessel
  # daneben ("Scroll Bar Mini Map All", "Scroll Bar Mini Map Width").
  # Nachgelesen in ktexteditor/src/utils/kateconfig.cpp; geraten haette
  # man es falsch, und ein falscher Schluessel wird stillschweigend
  # angelegt und nie gelesen.
  #
  # Die Gruppe gilt fuer die Anwendung, nicht fuer KTextEditor: Kate
  # liest aus katerc, KWrite aus kwriterc. Deshalb beide.
  "katerc:KTextEditor View:Scroll Bar MiniMap:false:Kate: schmale Bildlaufleiste statt Textvorschau"
  "kwriterc:KTextEditor View:Scroll Bar MiniMap:false:KWrite: dasselbe"
)

# FeatherPad als einfacher Texteditor - nur wenn vorhanden.
#
# Kate ist eine Entwicklungsumgebung: Projektleiste, LSP-Client,
# Sitzungen, Terminal. Wer eine Notiz aufschreiben will, bekommt davon
# nichts geschenkt. FeatherPad ist das Gegenstueck und kommt Notepad am
# naechsten - echte Menueleiste, kein Werkzeugkasten, keine Seitenleisten.
#
# Und es ist eine Qt-Anwendung: der Widget-Stil "Windows" greift
# vollstaendig, das Fenster sieht aus wie der Rest des Themes. Die
# GTK-Kandidaten (Mousepad, L3afpad, gedit) tun das nicht - sie
# zeichnen sich selbst und bleiben ein Fremdkoerper.
#
# Bewusst nur, wenn es installiert ist. Ein Design darf keine Pakete
# nachziehen, und ein Vorgabeprogramm, das es nicht gibt, ergibt beim
# Doppelklick auf eine .txt eine Fehlermeldung statt eines Editors.
if command -v featherpad >/dev/null 2>&1; then
    EINSTELLUNGEN+=(
      "mimeapps.list:Default Applications:text/plain:featherpad.desktop:FeatherPad fuer einfachen Text"
    )
    FEATHERPAD=true
else
    FEATHERPAD=false
fi

# ── Konsole dem Designwechsel nachziehen ─────────────────────────────────
#
# Das Farbschema des Terminals steht im Profil, und Plasma fasst Profile
# beim Designwechsel nicht an - Konsole kennt kein "dem System folgen".
# apply.sh stellt die Zeile um; wer das Design aber ueber die
# Systemeinstellungen wechselt, ruft apply.sh nie auf, und das Terminal
# bleibt in der alten Farbwelt stehen.
#
# Deshalb eine systemd-Pfadeinheit: Sie loest aus, wenn Plasma seine
# Vorgabendateien schreibt, und stoesst konsole-folgen.sh an. Kein
# laufender Prozess, keine Abhaengigkeit ausser systemd - das haben
# beide Test-VMs, Fedora wie EndeavourOS.
#
# Beobachtet werden zwei Stellen, und beide werden gebraucht:
# ~/.config/kdedefaults/package traegt die Kennung des Globalen Designs
# und wird von Plasma beim Anwenden neu geschrieben; kdeglobals faengt
# den Fall ab, dass jemand nur das Farbschema umstellt.
#
# Die Pfade stehen ausgeschrieben in der Einheit, nicht als %h: wer
# XDG_DATA_HOME verlegt hat, bekaeme sonst eine Einheit, die ins Leere
# zeigt - und systemd meldet das erst beim Ausloesen, in einem Protokoll,
# in das niemand schaut.
DIENST_VERZ="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
DIENST_NAME="nt-legacy-konsole"

dienst_ein() {
    local skript="$DATEN/nt-legacy/bin/konsole-folgen.sh"
    if [ ! -x "$skript" ]; then
        echo "  Hinweis: $skript fehlt - erst ./install.sh." >&2
        return
    fi
    if ! command -v systemctl >/dev/null; then
        echo "  Hinweis: kein systemd - Konsole folgt dem Design nur ueber" >&2
        echo "           ./apply.sh." >&2
        return
    fi
    mkdir -p "$DIENST_VERZ"
    cat > "$DIENST_VERZ/$DIENST_NAME.service" <<DIENST
[Unit]
Description=NT Legacy: Konsole-Farbschema dem Globalen Design nachziehen

[Service]
Type=oneshot
ExecStart=$skript
DIENST
    cat > "$DIENST_VERZ/$DIENST_NAME.path" <<PFAD
[Unit]
Description=NT Legacy: auf einen Wechsel des Globalen Designs warten

[Path]
PathChanged=${XDG_CONFIG_HOME:-$HOME/.config}/kdedefaults/package
PathChanged=${XDG_CONFIG_HOME:-$HOME/.config}/kdeglobals
Unit=$DIENST_NAME.service

[Install]
WantedBy=default.target
PFAD
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable --now "$DIENST_NAME.path" >/dev/null 2>&1 || true
    if systemctl --user is-active --quiet "$DIENST_NAME.path"; then
        echo "  Konsole folgt jetzt dem Designwechsel ($DIENST_NAME.path)."
    else
        echo "  Hinweis: $DIENST_NAME.path laeuft nicht." >&2
        echo "           systemctl --user status $DIENST_NAME.path" >&2
    fi
}

dienst_aus() {
    command -v systemctl >/dev/null || return 0
    systemctl --user disable --now "$DIENST_NAME.path" >/dev/null 2>&1 || true
    rm -f "$DIENST_VERZ/$DIENST_NAME.path" "$DIENST_VERZ/$DIENST_NAME.service"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "  $DIENST_NAME entfernt."
}

zeigen() {
    printf '%-12s %-10s %-16s %s\n' "Datei" "Gruppe" "Schluessel" "Wert"
    for e in "${EINSTELLUNGEN[@]}"; do
        IFS=: read -r datei gruppe schluessel wert grund <<< "$e"
        printf '%-12s %-10s %-16s %s\n' "$datei" "$gruppe" "$schluessel" "$wert"
        printf '%-40s %s\n' "" "$grund"
    done
    printf '%-12s %-10s %-16s %s\n' "systemd" "user" "$DIENST_NAME" "path+service"
    printf '%-40s %s\n' "" "Konsole folgt dem Wechsel des Globalen Designs"
}

zurueck() {
    if [ ! -f "$SICHERUNG" ]; then
        echo "Keine Sicherung unter $SICHERUNG - nichts zurueckzusetzen." >&2
        exit 1
    fi
    while IFS=: read -r datei gruppe schluessel wert; do
        [ -z "${datei:-}" ] && continue
        if [ -z "$wert" ]; then
            # Der Schluessel war vorher gar nicht gesetzt. Loeschen, nicht
            # auf einen erratenen Vorgabewert setzen - sonst steht dort
            # hinterher etwas, das der Nutzer nie gewaehlt hat.
            kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" --delete
            echo "  $datei/$gruppe/$schluessel  entfernt (war nicht gesetzt)"
        else
            kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" "$wert"
            echo "  $datei/$gruppe/$schluessel  -> $wert"
        fi
    done < "$SICHERUNG"
    rm -f "$SICHERUNG"
    dienst_aus
    echo
    echo "Zurueckgesetzt. Offene Programme einmal neu starten."
}

case "${1:-}" in
    --zeigen)  zeigen; exit 0 ;;
    --zurueck) zurueck; exit 0 ;;
    "")        ;;
    *)         echo "Unbekannte Option '$1'. Moeglich: --zeigen, --zurueck" >&2; exit 1 ;;
esac

# --- Anwenden ------------------------------------------------------------

if [ -f "$SICHERUNG" ]; then
    echo "Hinweis: Es gibt bereits eine Sicherung - die alten Werte bleiben"
    echo "         erhalten, damit --zurueck weiterhin den Urzustand trifft."
else
    mkdir -p "$(dirname "$SICHERUNG")"
    : > "$SICHERUNG"
    for e in "${EINSTELLUNGEN[@]}"; do
        IFS=: read -r datei gruppe schluessel _wert _grund <<< "$e"
        # Leerer Wert heisst: war nicht gesetzt. Den Unterschied zwischen
        # "nicht gesetzt" und "auf den Vorgabewert gesetzt" muss die
        # Sicherung festhalten, sonst ist der Rueckweg ungenau.
        alt=$(kreadconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" 2>/dev/null || true)
        echo "$datei:$gruppe:$schluessel:$alt" >> "$SICHERUNG"
    done
fi

for e in "${EINSTELLUNGEN[@]}"; do
    IFS=: read -r datei gruppe schluessel wert grund <<< "$e"
    kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" "$wert"
    echo "  $datei: $schluessel = $wert"
    echo "      $grund"
done

dienst_ein

if ! $FEATHERPAD; then
    cat <<EOF

  Fuer einfachen Text bleibt Kate die Vorgabe. Wer lieber einen
  schlichten Editor moechte - eine Menueleiste, sonst nichts, wie
  Notepad - installiert FeatherPad und ruft dieses Skript noch einmal:

      sudo dnf install featherpad     # oder: sudo pacman -S featherpad
      ./anmutung.sh

EOF
fi

cat <<EOF

Angewendet. Betroffene Programme einmal neu starten.

  Kate und Konsole lesen ihre Einstellungen beim Start. Ein offenes
  Fenster behaelt deshalb sein bisheriges Aussehen - und Kate schreibt
  seine Einstellungen beim Beenden zurueck, ueberschreibt also, was hier
  gesetzt wurde. Deshalb: erst schliessen, dann dieses Skript.

  Zurueck:  ./anmutung.sh --zurueck
  Gesichert: $SICHERUNG
EOF
