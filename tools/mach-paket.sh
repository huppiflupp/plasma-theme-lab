#!/usr/bin/env bash
# Schnuert die Archive fuer den KDE Store (store.kde.org / kde-look.org).
#
#   ./mach-paket.sh            # alle Archive nach dist/
#   ./mach-paket.sh --pruefen  # nur zeigen, was hineinkaeme
#
# Es entstehen zwei Sorten:
#
#   1. Ein Gesamtarchiv mit install.sh. Das ist der Weg, den fast alle
#      groesseren Themes gehen, weil ein Theme aus mehreren Ebenen
#      besteht (Plasma-Stil, Farbschema, Dekoration, Symbole, Zeiger) und
#      der Store je Eintrag nur eine Kategorie kennt.
#
#   2. Einzelarchive je Ebene. Nur damit funktioniert "Neue holen"
#      direkt in den Systemeinstellungen: KNewStuff entpackt das Archiv
#      an die passende Stelle und erwartet dort genau eine Ebene.
#
# Format tar.xz: kleiner als zip, unter Linux ueberall auspackbar, und
# es erhaelt die symbolischen Verweise. Das Symbolset besteht zu fast
# der Haelfte aus Verweisen - ein zip wuerde daraus Kopien machen und das
# Archiv unnoetig aufblaehen.

set -euo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME="$LAB/nt-legacy"
DIST="$LAB/dist"

VERSION="$(python3 -c "
import json
d = json.load(open('$THEME/look-and-feel/com.github.huppiflupp.nt-legacy/metadata.json'))
print(d['KPlugin']['Version'])
")"

PRUEFEN=false
[ "${1:-}" = "--pruefen" ] && PRUEFEN=true

# Was in KEIN Archiv gehoert.
#
# icons/ ist Chicago95 - Fremdmaterial mit ungeklaerter Lizenz, steht in
# .gitignore und darf unter keinen Umstaenden mit ausgeliefert werden.
# Deshalb steht es hier ausdruecklich noch einmal, statt sich auf die
# .gitignore zu verlassen: wer aus Versehen ein Archiv aus einem
# Arbeitsverzeichnis baut, in dem fetch-icons.sh gelaufen ist, soll es
# trotzdem nicht mit einpacken.
AUSSCHLUSS=(
    --exclude="icons"
    --exclude="__pycache__"
    --exclude="*.pyc"
    --exclude=".directory"
)

if $PRUEFEN; then
    echo "Version: $VERSION"
    echo
    echo "Ins Gesamtarchiv kaeme:"
    tar -cf /dev/null "${AUSSCHLUSS[@]}" -C "$LAB" nt-legacy -v 2>/dev/null \
        | sed 's|^nt-legacy/||' | awk -F/ 'NF<=2' | sort -u | head -30
    echo
    echo "Ausgeschlossen:"
    printf '  %s\n' "${AUSSCHLUSS[@]}"
    exit 0
fi

# Sicherung: nie ein Archiv mit Chicago95 bauen
if tar -cf /dev/null "${AUSSCHLUSS[@]}" -C "$LAB" nt-legacy -v 2>/dev/null \
        | grep -q "nt-legacy/icons/"; then
    echo "ABBRUCH: Chicago95-Symbole waeren im Archiv gelandet." >&2
    exit 1
fi

rm -rf "$DIST"
mkdir -p "$DIST"

# ── 1. Gesamtarchiv ──────────────────────────────────────────────────────
GESAMT="$DIST/nt-legacy-$VERSION.tar.xz"
tar -caf "$GESAMT" "${AUSSCHLUSS[@]}" -C "$LAB" nt-legacy
echo "  $(basename "$GESAMT")  $(du -h "$GESAMT" | cut -f1)   (Gesamtpaket mit install.sh)"

# ── 2. Einzelarchive je Ebene ────────────────────────────────────────────
#
# Struktur je Archiv: der Ordner, den KNewStuff erwartet, liegt direkt an
# der Wurzel. Also nt-legacy/ und nicht desktoptheme/nt-legacy/.
einzeln() {
    local name="$1" quelle="$2" ziel="$DIST/$3"
    [ -d "$quelle" ] || return 0
    tar -caf "$ziel" "${AUSSCHLUSS[@]}" -C "$(dirname "$quelle")" "$(basename "$quelle")"
    printf '  %-42s %6s   (%s)\n' "$(basename "$ziel")" \
        "$(du -h "$ziel" | cut -f1)" "$name"
}

# Plasma-Stile: alle zehn in ein Archiv, sonst muesste der Nutzer
# zehnmal herunterladen
tar -caf "$DIST/nt-legacy-plasma-styles-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/desktoptheme" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-plasma-styles-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-plasma-styles-$VERSION.tar.xz" | cut -f1)" "Plasma Style, 10 Varianten"

tar -caf "$DIST/nt-legacy-global-themes-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/look-and-feel" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-global-themes-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-global-themes-$VERSION.tar.xz" | cut -f1)" "Global Theme, 10 Varianten"

tar -caf "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/aurorae" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-window-decorations-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" | cut -f1)" "Aurorae, 10 Varianten"

einzeln "Symbole" "$THEME/icons-nt/NTLegacyIcons" "nt-legacy-icons-$VERSION.tar.xz"

tar -caf "$DIST/nt-legacy-cursors-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/cursors" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-cursors-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-cursors-$VERSION.tar.xz" | cut -f1)" "Mauszeiger, hell und rot"

# Farbschemata sind einzelne Dateien - der Store nimmt sie auch so,
# aber gebuendelt ist es fuer den Nutzer weniger Arbeit.
tar -caf "$DIST/nt-legacy-color-schemes-$VERSION.tar.xz" \
    -C "$THEME/color-schemes" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-color-schemes-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-color-schemes-$VERSION.tar.xz" | cut -f1)" "Farbschemata, 10 Varianten"

# ── Pruefsummen ──────────────────────────────────────────────────────────
(cd "$DIST" && sha256sum *.tar.xz > SHA256SUMS)

echo
echo "Fertig: $DIST"
echo "Pruefsummen in dist/SHA256SUMS"
