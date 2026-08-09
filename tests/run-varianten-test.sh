#!/usr/bin/env bash
# Spielt alle Varianten eines Themes durch - jede mit echtem Neustart.
#
#   ./run-varianten-test.sh              # alle aus build.py
#   ./run-varianten-test.sh teal desert  # nur diese
#   ./run-varianten-test.sh --schnell    # nur der Umschalttest, ohne Neustarts
#
# Warum je Variante ein Neustart sein muss: KWin laedt Aurorae-Themes
# ausschliesslich beim Sitzungsstart. Ohne Neustart traegt jedes Fenster
# die Titelleiste der vorherigen Variante - und ausgerechnet die ist das
# auffaelligste Merkmal. Ein Test ohne Neustart prueft also das, was er
# gerade nicht pruefen soll.
#
# Zusaetzlich am Ende: schnelles Umschalten ohne Neustart. Das war einmal
# der Weg in den schwarzen Desktop - plasma-plasmashell.service erlaubt
# drei Starts in 60 Sekunden, und der Sitzungsstart zaehlt als erster.
# Genau so klickt aber, wer Designs ausprobiert.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"
THEME="$LAB/nt-legacy"

SCHNELL_NUR=false
[ "${1:-}" = "--schnell" ] && { SCHNELL_NUR=true; shift; }

varianten=("$@")
if [ ${#varianten[@]} -eq 0 ]; then
    mapfile -t varianten < <(cd "$THEME" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('\n'.join(m.VARIANTEN))
")
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$LAB/tests/laeufe/varianten-$STAMP"
mkdir -p "$OUT/screenshots"
BERICHT="$OUT/bericht.md"
notiz() { echo -e "$*" | tee -a "$BERICHT"; }

ssh_() { "$VMCTL" ssh "$@" 2>&1; }

warte_auf_vm() {
    for _ in $(seq 1 40); do
        ssh_ 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1 && return 0
        sleep 8
    done
    return 1
}

fehler=0
melde() { notiz "  **FEHLER:** $*"; fehler=$((fehler + 1)); }

{
    echo "# Variantentest"
    echo
    echo "- Zeitpunkt: $(date -Is)"
    echo "- Varianten: ${varianten[*]}"
    echo
} > "$BERICHT"

# ── Vorbereitung ─────────────────────────────────────────────────────────
notiz "## Vorbereitung"
"$VMCTL" push "$THEME/" /home/tester/nt-legacy/ >/dev/null 2>&1
if ! ssh_ 'cd nt-legacy && ./install.sh' >/dev/null 2>&1; then
    notiz "Installation fehlgeschlagen - Abbruch."
    exit 1
fi
notiz "Theme installiert.\n"

# ── Teil 1: jede Variante mit Neustart ───────────────────────────────────
declare -A FARBE
if ! $SCHNELL_NUR; then
    notiz "## Teil 1 - jede Variante mit Sitzungsneustart\n"
    notiz "| Variante | angewendet | Shell | KWin | Dekoration | Panelfarbe |"
    notiz "|---|---|---|---|---|---|"

    for v in "${varianten[@]}"; do
        anwenden="ok"
        ssh_ "cd nt-legacy && ./apply.sh $v" >/dev/null 2>&1 || anwenden="FEHLER"

        ssh_ 'sudo systemctl reboot' >/dev/null 2>&1
        sleep 45
        if ! warte_auf_vm; then
            notiz "| $v | $anwenden | **VM kam nicht zurueck** | - | - | - |"
            melde "$v: VM nach dem Neustart nicht erreichbar"
            continue
        fi
        sleep 18

        shell=$(ssh_ 'systemctl --user is-active plasma-plasmashell.service' | tr -d '\r')
        kwin=$(ssh_ 'pgrep -x kwin_wayland >/dev/null && echo laeuft || echo TOT' | tr -d '\r')
        # Zeigt die Dekoration auf ein Theme, das es wirklich gibt?
        deko=$(ssh_ 'th=$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)
            d=${th#__aurorae__svg__}
            if [ -d "$HOME/.local/share/aurorae/themes/$d" ]; then echo "ok"
            else echo "FEHLT:$d"; fi' | tr -d '\r')

        bild="$OUT/screenshots/$v.png"
        "$VMCTL" shot "$bild" >/dev/null 2>&1
        farbe=$(magick "$bild" -format "%[pixel:p{960,1050}]" info: 2>/dev/null \
                | sed 's/srgb//' || echo "?")
        FARBE[$v]="$farbe"

        zeile="| $v | $anwenden | $shell | $kwin | $deko | \`$farbe\` |"
        notiz "$zeile"
        [ "$shell" = "active" ] || melde "$v: plasmashell ist '$shell'"
        [ "$kwin" = "laeuft" ]  || melde "$v: kwin_wayland laeuft nicht"
        [ "$deko" = "ok" ]      || melde "$v: Dekoration $deko"
    done

    # ── Unterscheiden sich die Varianten ueberhaupt? ─────────────────────
    notiz "\n### Sind die Varianten unterscheidbar?\n"
    notiz "Zwei Varianten mit identischem Bildschirmfoto waeren ein Zeichen,"
    notiz "dass eine davon gar nicht angewendet wurde.\n"
    doppelt=0
    dateien=("$OUT"/screenshots/*.png)
    for ((i = 0; i < ${#dateien[@]}; i++)); do
        for ((j = i + 1; j < ${#dateien[@]}; j++)); do
            # RMSE statt AE: liefert einen normierten Wert zwischen 0 und 1
            # und nicht eine Pixelzahl in wissenschaftlicher Notation, an
            # der sich Bash-Arithmetik verschluckt - "5.7462e+09" wurde von
            # ${d%%.*} zu "5" und damit als Treffer gewertet.
            d=$(magick compare -metric RMSE "${dateien[i]}" "${dateien[j]}" null: 2>&1 \
                | grep -oP '\(\K[0-9.]+(?=\))' | head -1)
            [ -z "$d" ] && continue
            if awk -v x="$d" 'BEGIN{exit !(x < 0.02)}'; then
                notiz "  **$(basename "${dateien[i]}" .png)** und **$(basename "${dateien[j]}" .png)**: RMSE nur $d"
                doppelt=$((doppelt + 1))
            fi
        done
    done
    [ "$doppelt" -eq 0 ] && notiz "  Alle Varianten unterscheiden sich deutlich." \
                         || fehler=$((fehler + doppelt))
fi

# ── Teil 2: schnelles Umschalten ─────────────────────────────────────────
notiz "\n## Teil 2 - schnelles Umschalten ohne Neustart\n"
notiz "Drei Varianten in Folge, ohne Pause. Frueher fuehrte der dritte"
notiz "Aufruf in 60 Sekunden zum schwarzen Desktop, weil systemd nur drei"
notiz "Starts je Minute erlaubt und der Sitzungsstart als erster zaehlt.\n"

drei=("${varianten[@]:0:3}")
for v in "${drei[@]}"; do
    ssh_ "cd nt-legacy && ./apply.sh $v" >/dev/null 2>&1
    notiz "  angewendet: $v"
done
sleep 8
shell=$(ssh_ 'systemctl --user is-active plasma-plasmashell.service' | tr -d '\r')
notiz "\nplasmashell danach: **$shell**"
if [ "$shell" != "active" ]; then
    melde "Nach drei schnellen Wechseln laeuft plasmashell nicht mehr ('$shell')"
    notiz "\nJournal:"
    notiz "\`\`\`\n$(ssh_ 'journalctl --user -u plasma-plasmashell.service -n 12 --no-pager')\n\`\`\`"
fi
"$VMCTL" shot "$OUT/screenshots/nach-schnellwechsel.png" >/dev/null 2>&1

# Ist ueberhaupt noch etwas zu sehen? Ein schwarzer Schirm faellt sonst
# nicht auf - die Dienste koennen laufen und trotzdem nichts zeichnen.
mittel=$(magick "$OUT/screenshots/nach-schnellwechsel.png" -format "%[fx:mean]" info: 2>/dev/null)
notiz "Bildhelligkeit: $mittel (nahe 0 = schwarzer Schirm)"
awk -v m="$mittel" 'BEGIN{exit !(m < 0.03)}' 2>/dev/null && \
    melde "Bildschirm ist praktisch schwarz nach dem Umschalten"

# ── Ergebnis ─────────────────────────────────────────────────────────────
notiz "\n---\n"
if [ "$fehler" -eq 0 ]; then
    notiz "## Ergebnis: alle Pruefungen bestanden"
else
    notiz "## Ergebnis: $fehler Beanstandung(en)"
fi
notiz "\nBericht: \`${BERICHT#$LAB/}\`"
echo
echo "Fertig. Bericht: $BERICHT"
exit $((fehler > 0))
