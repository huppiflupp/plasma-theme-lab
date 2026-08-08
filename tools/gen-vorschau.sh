#!/usr/bin/env bash
# Ersetzt die schematischen Vorschaubilder durch echte Screenshots.
#
# Fuer jede Variante: in der Test-VM anwenden, Sitzung neu starten,
# ein paar Fenster oeffnen, Bildschirmfoto machen, zuschneiden.
#
#   ./gen-vorschau.sh              # alle Varianten
#   ./gen-vorschau.sh teal lilac   # nur diese
#
# Der Sitzungsneustart je Variante ist nicht wegzuoptimieren: KWin laedt
# Aurorae-Themen ausschliesslich beim Start. Ohne Neustart traegt jedes
# Bild die Titelleiste der vorherigen Variante - und genau die ist das
# auffaelligste Merkmal.
#
# Dauer: rund zwei Minuten je Variante.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"
THEME="$LAB/nt-legacy"
BREITE=1920
HOEHE=1080

varianten=("$@")
if [ ${#varianten[@]} -eq 0 ]; then
    mapfile -t varianten < <(cd "$THEME" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('\n'.join(m.VARIANTEN))
")
fi

lnf_fuer() {
    (cd "$THEME" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.ids(sys.argv[1])['lnf'])
" "$1")
}

warte_auf_vm() {
    for _ in $(seq 1 30); do
        "$VMCTL" ssh 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1 && return 0
        sleep 10
    done
    return 1
}

echo "Uebertrage aktuellen Stand …"
"$VMCTL" push "$THEME/" /home/tester/nt-legacy/ >/dev/null 2>&1
"$VMCTL" ssh 'cd nt-legacy && ./install.sh >/dev/null 2>&1' || {
    echo "FEHLER: Installation in der VM fehlgeschlagen" >&2; exit 1; }

for v in "${varianten[@]}"; do
    lnf="$(lnf_fuer "$v")"
    ziel="$THEME/look-and-feel/$lnf/contents/previews"
    echo
    echo "=== $v ==="

    "$VMCTL" ssh "cd nt-legacy && ./apply.sh $v >/dev/null 2>&1" || {
        echo "  uebersprungen (apply.sh fehlgeschlagen)"; continue; }

    # Neu anmelden, damit die Fensterdekoration greift
    "$VMCTL" ssh 'sudo systemctl reboot' >/dev/null 2>&1
    sleep 45
    warte_auf_vm || { echo "  VM kam nicht zurueck"; continue; }
    sleep 30

    "$VMCTL" ssh "
        kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
        # 16:9, damit die Kachel im Auswahldialog nicht beschneidet
        kscreen-doctor output.1.mode.${BREITE}x${HOEHE}@60 >/dev/null 2>&1
        sleep 4
        # Vier Fenster, versetzt gestapelt: das oberste ist aktiv, die
        # anderen inaktiv - so sieht man beide Titelleistenfarben und
        # gleich mehrere Programme auf einem Bild.
        #
        # Reihenfolge von hinten nach vorn. PCManFM-Qt kommt zuletzt,
        # weil es das Symbolset und die Statusleiste zeigt - das ist das
        # Aushaengeschild.
        (setsid konsole     >/dev/null 2>&1 &); sleep 9
        (setsid kolourpaint >/dev/null 2>&1 &); sleep 9
        (setsid dragon      >/dev/null 2>&1 &); sleep 9
        (setsid pcmanfm-qt  >/dev/null 2>&1 &); sleep 12
    " >/dev/null 2>&1

    virsh -c qemu:///system send-key plasma-lab KEY_LEFTSHIFT >/dev/null 2>&1
    sleep 3

    roh="$(mktemp --suffix=.png)"
    "$VMCTL" shot "$roh" >/dev/null 2>&1
    if [ ! -s "$roh" ]; then
        echo "  kein Bildschirmfoto"; rm -f "$roh"; continue
    fi

    mkdir -p "$ziel"

    # Vollbild fuer die Grossansicht - dort ist Platz genug.
    magick "$roh" -resize "${BREITE}x${HOEHE}!" -quality 88 \
        "$ziel/fullscreenpreview.jpg"

    # Fuer die Kachel einen Ausschnitt statt der ganzen Flaeche: bei
    # 600x337 waeren die Fenster sonst unlesbar klein und die halbe
    # Kachel leerer Schreibtisch. Der Ausschnitt sitzt mittig, wo die
    # Fenster stehen, und zeigt Titelleiste, Fensterinhalt und ein
    # Stueck Panel - also genau das, was die Variante ausmacht.
    magick "$roh" -gravity center -crop 62%x62%+0-40 +repage \
        -resize 600x337^ -gravity center -extent 600x337 \
        "$ziel/preview.png"
    cp "$ziel/preview.png" "$ziel/lockscreen.png"
    cp "$ziel/preview.png" "$ziel/splash.png"
    rm -f "$roh"

    echo "  $(basename "$ziel")/preview.png  (aus echtem Bildschirmfoto)"
    "$VMCTL" ssh 'pkill pcmanfm-qt; pkill dragon; pkill kolourpaint; pkill konsole' >/dev/null 2>&1
done

echo
echo "Fertig. Die Bilder liegen in nt-legacy/look-and-feel/*/contents/previews/."
