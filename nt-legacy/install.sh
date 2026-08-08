#!/usr/bin/env bash
# Installiert NT Legacy.
#
# Fasst ausschliesslich $HOME an, fragt nie nach sudo, und sichert vorher
# die Konfiguration. Damit ist die Installation in jedem Fall umkehrbar -
# das ist der Unterschied zwischen einem Theme, das man ausprobieren
# kann, und einem, bei dem man vorher ueberlegt.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"

LNF_ID="com.github.huppiflupp.nt-legacy"
STYLE_ID="nt-legacy"

# ── Sicherung ────────────────────────────────────────────────────────────
BACKUP="$DATEN/nt-legacy/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
# kcminputrc gehoert dazu - sonst bleibt der Mauszeiger nach dem
# Zuruecksetzen auf NT Legacy stehen.
for f in plasma-org.kde.plasma.desktop-appletsrc plasmarc kdeglobals \
         kwinrc ksplashrc kcminputrc; do
    if [ -f "$HOME/.config/$f" ]; then
        cp -a "$HOME/.config/$f" "$BACKUP/"
    else
        # Datei gibt es noch nicht - der haeufige Fall auf einem frischen
        # Konto. Ohne Vermerk wuesste restore.sh nicht, dass sie hinterher
        # wieder verschwinden muss, und unsere Werte blieben darin stehen.
        echo "$f" >> "$BACKUP/.war-nicht-vorhanden"
    fi
done
cat > "$BACKUP/restore.sh" <<'EOF'
#!/usr/bin/env bash
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in "$HERE"/*; do
    n="$(basename "$f")"
    case "$n" in restore.sh|README|.war-nicht-vorhanden) continue ;; esac
    cp -a "$f" "$HOME/.config/$n"; echo "  $n"
done

# Dateien, die es vor der Installation nicht gab, muessen wieder weg -
# sonst bleiben unsere Werte darin stehen. Genau so ueberlebten frueher
# Plasma-Stil und Mauszeiger ein restore.sh.
if [ -f "$HERE/.war-nicht-vorhanden" ]; then
    while read -r n; do
        [ -n "$n" ] && [ -f "$HOME/.config/$n" ] && {
            rm -f "$HOME/.config/$n"
            echo "  $n entfernt (gab es vorher nicht)"
        }
    done < "$HERE/.war-nicht-vorhanden"
fi

# Fensterdekoration ausdruecklich zuruecksetzen. Zeigt kwinrc auf ein
# geloeschtes Aurorae-Thema, zeichnet KWin GAR KEINE Titelleiste - kein
# Fallback, kein Schliessknopf. In der Test-VM belegt.
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key library org.kde.breeze 2>/dev/null || true
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key theme Breeze 2>/dev/null || true

rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"
echo ""
echo "Wiederhergestellt. Ab- und wieder anmelden."
EOF
chmod +x "$BACKUP/restore.sh"
echo "Sicherung: $BACKUP"

# ── Installation ─────────────────────────────────────────────────────────
# kpackagetool6 statt cp -r: es prueft die Metadaten, legt unter der
# richtigen Id ab und kann sauber wieder deinstallieren.
installiere() {
    local typ="$1" pfad="$2" ziel="$3"
    # Erst -u (Upgrade), dann -r + -i. Das Upgrade scheitert, wenn das
    # Verzeichnis zwar da, das Paket aber nicht registriert ist - dann
    # scheitert auch -i mit "existiert bereits". Ohne diesen Weg schlaegt
    # jede zweite Installation fehl.
    if kpackagetool6 -t "$typ" -u "$pfad" >/dev/null 2>&1; then
        return 0
    fi
    kpackagetool6 -t "$typ" -r "$(basename "$pfad")" >/dev/null 2>&1 || true
    rm -rf "$ziel"
    kpackagetool6 -t "$typ" -i "$pfad" >/dev/null
}

echo "Plasma Styles …"
for d in "$HIER"/desktoptheme/*/; do
    n="$(basename "$d")"
    installiere Plasma/Theme "${d%/}" "$DATEN/plasma/desktoptheme/$n"
    echo "  $n"
done

echo "Farbschema …"
install -Dm644 "$HIER/color-schemes/"*.colors -t "$DATEN/color-schemes/"

if [ -d "$HIER/icons" ]; then
    echo "Symbole …"
    mkdir -p "$DATEN/icons"
    cp -r "$HIER/icons/"* "$DATEN/icons/"
    # Ohne aktualisierten Cache zeigt Plasma teils noch die alten Symbole
    command -v gtk-update-icon-cache >/dev/null && \
        gtk-update-icon-cache -q -t -f "$DATEN/icons/NTLegacy" 2>/dev/null || true
fi

if [ -d "$HIER/cursors" ]; then
    echo "Mauszeiger …"
    mkdir -p "$DATEN/icons"
    cp -r "$HIER/cursors/"* "$DATEN/icons/"
fi

if [ -d "$HIER/wallpapers" ]; then
    echo "Hintergrundbild …"
    mkdir -p "$DATEN/wallpapers"
    cp -r "$HIER/wallpapers/"* "$DATEN/wallpapers/"
fi

if [ -d "$HIER/aurorae" ]; then
    echo "Fensterdekoration …"
    mkdir -p "$DATEN/aurorae/themes"
    cp -r "$HIER/aurorae/"* "$DATEN/aurorae/themes/"
fi

echo "Globale Designs …"
for d in "$HIER"/look-and-feel/*/; do
    n="$(basename "$d")"
    installiere Plasma/LookAndFeel "${d%/}" "$DATEN/plasma/look-and-feel/$n"
    echo "  $n"
done

# Das Icon-Theme muss hart gesetzt werden. Plasma zieht die uebrigen
# Vorgaben aus contents/defaults zur Laufzeit (Plasma Style, Farbschema,
# Anwendungsstil greifen so), beim Icon-Theme aber nicht - gemessen: mit
# Fallback blieben Breeze-Icons stehen, erst kwriteconfig6 brachte die
# Chicago95-Symbole. Die alten Werte liegen in der Sicherung oben.
kwriteconfig6 --file kdeglobals --group Icons --key Theme NTLegacy

# Der Render-Cache traegt die Themeversion im Namen. Ohne Loeschen sieht
# man nach einem Update das alte Theme und sucht den Fehler woanders.
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"

cat <<EOF

Fertig.

  Anwenden:     plasma-apply-lookandfeel --apply com.github.huppiflupp.nt-legacy
                (Varianten: …-lilac, …-desert)
  oder:         Systemeinstellungen > Farben & Design > Globales Design

Das Design wirkt erst nach einem Ab- und Wiederanmelden vollstaendig.

  Rueckweg:     $BACKUP/restore.sh
EOF
