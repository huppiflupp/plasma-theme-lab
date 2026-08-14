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

# ── Ein Paket je Archiv, wo KNewStuff es so verlangt ─────────────────────
#
# Aus der Community: wer das Global Theme ueber "Neue holen" installiert,
# bekommt fuenf bis sechs namenlose Eintraege und kein einziges NT-Design.
# Nachgestellt und bestaetigt.
#
# Der Grund steht in den knsrc-Dateien von Plasma. Zwei Sorten:
#
#   Uncompress=archive   entpackt stumpf ins Zielverzeichnis. Zehn
#                        Ordner nebeneinander sind hier richtig -
#                        Aurorae, Symbole, Zeiger, Farbschemata.
#   Uncompress=kpackage  reicht das Archiv an kpackagetool weiter, und
#                        das erwartet GENAU EIN Paket, dessen
#                        metadata.json an der Archivwurzel liegt.
#                        So arbeiten Global Themes und Plasma-Stile.
#
# Unser Buendelarchiv hatte zehn Paketordner an der Wurzel und keine
# metadata.json daneben. kpackagetool nimmt dann das Archiv selbst fuer
# das Paket, benennt es nach der Datei und haengt eine Nummer an:
#
#   $ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-global-themes.tar.xz
#   Erfolgreich installiert: .../look-and-feel/nt-legacy-global-themes-0/
#
# Ein Ordner ohne metadata.json - das Design fehlt, der Eintrag bleibt
# namenlos, und jeder neue Versuch legt den naechsten daneben. Bei den
# Plasma-Stilen schlaegt schon die Installation fehl ("Das Paket wird
# als ungueltig betrachtet").
#
# Deshalb je Variante ein eigenes Archiv. Im Store werden daraus zehn
# Dateien an einem Eintrag, aus denen sich der Nutzer eine aussucht -
# das ist dort die uebliche Form fuer Designs mit mehreren Fassungen.
# Der Dateiname traegt die Farbwelt, nicht die volle Paketkennung. Im
# Store steht der Nutzer vor einer Liste von zwanzig Dateien; dort hilft
# "desert-nacht" und nicht "com.github.huppiflupp.nt-legacy-desert-nacht".
kurzname() {
    local b="$1"
    b="${b#com.github.huppiflupp.}"
    b="${b#nt-legacy}"
    b="${b#-}"
    echo "${b:-teal}"
}

paket_je_variante() {
    local name="$1" quelle="$2" praefix="$3"
    local n=0
    for d in "$quelle"/*/; do
        [ -d "$d" ] || continue
        local b; b="$(basename "$d")"
        tar -caf "$DIST/$praefix-$(kurzname "$b")-$VERSION.tar.xz" \
            "${AUSSCHLUSS[@]}" -C "$quelle" "$b"
        n=$((n + 1))
    done
    printf '  %-42s %6s   (%s)\n' "$praefix-*-$VERSION.tar.xz" "$n Stk" "$name"
}

paket_je_variante "Plasma Style, je Variante ein Archiv" \
    "$THEME/desktoptheme" "nt-legacy-plasma-style"
paket_je_variante "Global Theme, je Variante ein Archiv" \
    "$THEME/look-and-feel" "nt-legacy-global-theme"

# Aurorae laeuft ueber Uncompress=archive - hier ist ein Buendel richtig.
tar -caf "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/aurorae" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-window-decorations-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" | cut -f1)" "Aurorae, 10 Varianten"

# Beide Symbolsaetze in ein Archiv. Der Symbol-Downloader laeuft ueber
# Uncompress=true, entpackt also stumpf nach ~/.local/share/icons/ - zwei
# Ordner nebeneinander sind dort richtig. Und wer nur den hellen zieht,
# steht mit jeder Nachtfassung wieder vor dem dunklen Systemabschnitt.
tar -caf "$DIST/nt-legacy-icons-$VERSION.tar.xz" "${AUSSCHLUSS[@]}" \
    -C "$THEME/icons-nt" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-icons-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-icons-$VERSION.tar.xz" | cut -f1)" \
    "Symbole, hell und Nachtfassung"

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

# ── Bildschirmfotos fuer die Store-Galerie ───────────────────────────────
#
# Sie werden hier miterzeugt und nicht von Hand hineinkopiert. Grund: Das
# Skript raeumt dist/ zu Beginn ab. Wer die Bilder nebenher hineinlegt,
# verliert sie beim naechsten Lauf - genau das ist einmal passiert.
mkdir -p "$DIST/screenshots"
anzahl=0
for d in "$THEME"/look-and-feel/*/; do
    n="$(basename "$d" | sed 's/com.github.huppiflupp.//')"
    voll="$d/contents/previews/fullscreenpreview.jpg"
    [ -f "$voll" ] || continue
    cp "$voll" "$DIST/screenshots/$n.jpg"
    anzahl=$((anzahl + 1))
done

# ── Tag/Nacht in einem Bild ──────────────────────────────────────────────
#
# Jede Farbwelt gibt es in einer Tag- und einer Nachtfassung. Nebeneinander
# in der Galerie sagt das wenig: zwei fast gleiche Bilder, und wer nicht
# genau hinsieht, haelt das zweite fuer eine Wiederholung. Deshalb ein
# Bild je Farbwelt, diagonal von oben rechts nach unten links geteilt -
# oben links Tag, unten rechts Nacht. Im Store ist das die uebliche
# Darstellung fuer Themes mit zwei Fassungen.
#
# Das funktioniert nur, weil gen-vorschau.sh die Fenster fuer jede
# Variante an dieselbe Stelle setzt: gleiche Programme, gleiche
# Reihenfolge, gleiche Aufloesung. Die Fensterkanten laufen ueber den
# Schnitt hinweg durch, und man sieht denselben Bildschirm zweimal
# eingefaerbt statt zwei verschiedene Aufnahmen.
diagonal() {
    local tag="$1" nacht="$2" ziel="$3"
    local b h
    # Das \n ist Pflicht: ohne Zeilenende liefert read einen Fehlerstatus,
    # und set -e beendet das Skript wortlos mitten im Lauf.
    read -r b h < <(magick identify -format '%w %h\n' "$tag")

    # Der Umweg ueber CopyOpacity statt einer Maske als drittes Bild bei
    # -composite: Letzteres wertet die Maske nicht zuverlaessig aus, das
    # Ergebnis war einfarbig das Tagbild. So ist die Maske ausdruecklich
    # der Alphakanal des Tagbilds, und darueber gibt es nichts zu raten.
    magick "$tag" \
        \( -size "${b}x${h}" xc:black -fill white \
           -draw "polygon 0,0 ${b},0 0,${h}" \) \
        -alpha off -compose CopyOpacity -composite "$tmp/oben.png"

    # Die helle Linie auf der Schnittkante ist nicht Zierrat: ohne sie
    # wirkt der Uebergang bei den dunkleren Farbwelten wie ein
    # Bildfehler, weil Tag- und Nachtflaeche dort aehnlich hell sind.
    magick "$nacht" "$tmp/oben.png" -compose Over -composite \
        -stroke "#e8e8e8" -strokewidth 3 -draw "line ${b},0 0,${h}" \
        -quality 88 "$ziel"
}

# Zu welchem Tagbild gehoert welche Nacht? Die Grundfassung heisst
# nt-legacy.jpg, ihre Nachtfassung aber nt-legacy-teal-nacht.jpg - der
# Name traegt die Farbwelt, den die Grundfassung im Namen weglaesst.
nachtbild_zu() {
    local tag="$1"
    case "$(basename "$tag")" in
        nt-legacy.jpg) echo "$(dirname "$tag")/nt-legacy-teal-nacht.jpg" ;;
        *)             echo "${tag%.jpg}-nacht.jpg" ;;
    esac
}

if command -v magick >/dev/null && [ "$anzahl" -gt 0 ]; then
    tmp="$(mktemp -d)"
    paare=0
    kacheln=()

    # Grundfassung zuerst, der Rest alphabetisch - dieselbe Reihenfolge
    # wie spaeter in der Galerie.
    tagbilder=("$DIST/screenshots/nt-legacy.jpg")
    for b in "$DIST"/screenshots/nt-legacy-*.jpg; do
        case "$b" in *-nacht.jpg) continue ;; esac
        tagbilder+=("$b")
    done

    for tag in "${tagbilder[@]}"; do
        [ -f "$tag" ] || continue
        nacht="$(nachtbild_zu "$tag")"
        [ -f "$nacht" ] || continue
        paare=$((paare + 1))
        name="$(basename "${tag%.jpg}" | sed 's/^nt-legacy-*//')"
        [ -z "$name" ] && name="teal"

        diagonal "$tag" "$nacht" \
            "$(printf '%s/screenshots/%02d-tag-nacht-%s.jpg' "$DIST" "$paare" "$name")"
        anzahl=$((anzahl + 1))

        # Fuer die Uebersichtskachel wird nicht das fertige Vollbild
        # verkleinert, sondern erst zugeschnitten und dann geteilt. Sonst
        # laeuft die Schnittkante schraeg durch die Kachel statt von Ecke
        # zu Ecke, und der Effekt geht verloren.
        for seite in tag nacht; do
            [ "$seite" = tag ] && q="$tag" || q="$nacht"
            magick "$q" -gravity center -crop 68%x68%+0-30 +repage \
                   -resize 640x360^ -gravity center -extent 640x360 \
                   "$tmp/kachel-$seite.png" 2>/dev/null
        done
        diagonal "$tmp/kachel-tag.png" "$tmp/kachel-nacht.png" \
                 "$tmp/kachel-$paare.jpg"
        kacheln+=("$tmp/kachel-$paare.jpg")
    done

    # Dazu ein Uebersichtsbild: alle Farbwelten auf einer Kachel. Das ist
    # in einer Galerie meist das erste, was jemand ansieht - eine Reihe
    # fast gleicher Vollbilder sagt weniger als ein Bild, das die
    # Bandbreite zeigt.
    #
    # Fuenf geteilte Kacheln statt zehn ganzer: jede ist doppelt so
    # gross, und die zehn Fassungen sind trotzdem alle darauf.
    #
    # Raster 3x2, nicht 5x1: nebeneinander ergaebe das einen 2860 Pixel
    # breiten, 430 hohen Streifen - in der Galerieuebersicht ist davon
    # nichts mehr zu erkennen. Der sechste Platz bleibt dabei uebrig und
    # bekommt eine Beschriftung, sonst sieht die Luecke nach Fehler aus.
    if [ ${#kacheln[@]} -gt 0 ]; then
        magick -size 640x360 xc:"#3a4446" -gravity center \
            -fill "#dfe6e6" -pointsize 46 -annotate +0-30 "NT Legacy" \
            -fill "#9fb0b0" -pointsize 24 -annotate +0+30 "five palettes, day and night" \
            "$tmp/kachel-text.jpg" 2>/dev/null \
            && kacheln+=("$tmp/kachel-text.jpg")

        magick montage "${kacheln[@]}" -tile 3x2 -geometry +6+6 \
            -background "#3a4446" "$DIST/screenshots/00-uebersicht.jpg" 2>/dev/null \
            && anzahl=$((anzahl + 1))
    fi
    rm -rf "$tmp"
fi
echo "  screenshots/                               $(du -sh "$DIST/screenshots" | cut -f1)   ($anzahl Bilder)"

# ── Pruefsummen ──────────────────────────────────────────────────────────
(cd "$DIST" && sha256sum *.tar.xz > SHA256SUMS)

echo
echo "Fertig: $DIST"
echo "Pruefsummen in dist/SHA256SUMS"
