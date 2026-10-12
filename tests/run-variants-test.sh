#!/usr/bin/env bash
# Runs through all variants of a theme - each with a real reboot.
#
#   ./run-variants-test.sh              # all from build.py
#   ./run-variants-test.sh teal desert  # only these
#   ./run-variants-test.sh --quick      # only the switching test, without reboots
#
# Why every variant needs a reboot: KWin loads Aurorae themes
# only at session start. Without a reboot every window wears
# the title bar of the previous variant - and that of all things is the
# most conspicuous feature. A test without a reboot therefore checks exactly
# what it is not supposed to check.
#
# In addition, at the end: quick switching without a reboot. That was once
# the road to the black desktop - plasma-plasmashell.service allows
# three starts in 60 seconds, and the session start counts as the first.
# But that is exactly how someone trying out themes clicks.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"
THEME="$LAB/nt-legacy"

QUICK_ONLY=false
[ "${1:-}" = "--quick" ] && { QUICK_ONLY=true; shift; }

variants=("$@")
if [ ${#variants[@]} -eq 0 ]; then
    mapfile -t variants < <(cd "$THEME" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('\n'.join(m.VARIANTEN))
")
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$LAB/tests/runs/variants-$STAMP"
mkdir -p "$OUT/screenshots"
REPORT="$OUT/report.md"
note() { echo -e "$*" | tee -a "$REPORT"; }

ssh_() { "$VMCTL" ssh "$@" 2>&1; }

wait_for_vm() {
    for _ in $(seq 1 40); do
        ssh_ 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1 && return 0
        sleep 8
    done
    return 1
}

errors=0
report_error() { note "  **ERROR:** $*"; errors=$((errors + 1)); }

{
    echo "# Variant test"
    echo
    echo "- Time: $(date -Is)"
    echo "- Variants: ${variants[*]}"
    echo
} > "$REPORT"

# ── Preparation ──────────────────────────────────────────────────────────
note "## Preparation"
"$VMCTL" push "$THEME/" /home/tester/nt-legacy/ >/dev/null 2>&1
if ! ssh_ 'cd nt-legacy && ./install.sh' >/dev/null 2>&1; then
    note "Installation failed - aborting."
    exit 1
fi
note "Theme installed.\n"

# ── Part 1: each variant with a reboot ───────────────────────────────────
declare -A COLOUR
if ! $QUICK_ONLY; then
    note "## Part 1 - each variant with a session restart\n"
    note "| Variant | applied | Shell | KWin | Decoration | Panel colour |"
    note "|---|---|---|---|---|---|"

    for v in "${variants[@]}"; do
        applied="ok"
        ssh_ "cd nt-legacy && ./apply.sh $v" >/dev/null 2>&1 || applied="ERROR"

        ssh_ 'sudo systemctl reboot' >/dev/null 2>&1
        sleep 45
        if ! wait_for_vm; then
            note "| $v | $applied | **VM did not come back** | - | - | - |"
            report_error "$v: VM not reachable after the reboot"
            continue
        fi
        sleep 18

        shell=$(ssh_ 'systemctl --user is-active plasma-plasmashell.service' | tr -d '\r')
        kwin=$(ssh_ 'pgrep -x kwin_wayland >/dev/null && echo running || echo DEAD' | tr -d '\r')
        # Does the decoration point to a theme that really exists?
        deco=$(ssh_ 'th=$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)
            d=${th#__aurorae__svg__}
            if [ -d "$HOME/.local/share/aurorae/themes/$d" ]; then echo "ok"
            else echo "MISSING:$d"; fi' | tr -d '\r')

        # Open a window BEFORE the image is taken.
        #
        # Without a window the screenshot shows only the desktop and
        # panel - and the title bar is missing, of all things the
        # feature in which the variants differ most.
        # Because of this, the first run reported teal-nacht, win98-nacht and
        # win2k-nacht as practically identical, although their title bars
        # are #176b78, #000080 and #0a246a.
        ssh_ 'pkill dolphin 2>/dev/null; (setsid dolphin >/dev/null 2>&1 &)' >/dev/null 2>&1
        sleep 12
        image="$OUT/screenshots/$v.png"
        "$VMCTL" shot "$image" >/dev/null 2>&1
        colour=$(magick "$image" -format "%[pixel:p{960,1050}]" info: 2>/dev/null \
                | sed 's/srgb//' || echo "?")
        COLOUR[$v]="$colour"

        row="| $v | $applied | $shell | $kwin | $deco | \`$colour\` |"
        note "$row"
        [ "$shell" = "active" ] || report_error "$v: plasmashell is '$shell'"
        [ "$kwin" = "running" ] || report_error "$v: kwin_wayland is not running"
        [ "$deco" = "ok" ]      || report_error "$v: decoration $deco"
    done

    # ── Do the variants differ at all? ───────────────────────────────────
    note "\n### Can the variants be told apart?\n"
    note "Two variants with an identical screenshot would be a sign"
    note "that one of them was not applied at all.\n"
    duplicates=0
    files=("$OUT"/screenshots/*.png)
    for ((i = 0; i < ${#files[@]}; i++)); do
        for ((j = i + 1; j < ${#files[@]}; j++)); do
            # RMSE instead of AE: gives a normalised value between 0 and 1
            # and not a pixel count in scientific notation that
            # Bash arithmetic chokes on - "5.7462e+09" became "5" via
            # ${d%%.*} and was thus counted as a hit.
            d=$(magick compare -metric RMSE "${files[i]}" "${files[j]}" null: 2>&1 \
                | grep -oP '\(\K[0-9.]+(?=\))' | head -1)
            [ -z "$d" ] && continue
            a="$(basename "${files[i]}" .png)"; b="$(basename "${files[j]}" .png)"
            # Two thresholds, because they are two different statements:
            #
            # Nearly zero means the second variant was not
            # applied at all - an error.
            #
            # Small but clearly above zero means it was applied
            # and merely looks similar to the other. That can even be right:
            # win98-nacht and win2k-nacht are at 0.015, because
            # their title bars are #000080 and #0a246a - historically
            # correct and still hard to tell apart. That is a
            # design question, not a defect, and is only noted.
            if awk -v x="$d" 'BEGIN{exit !(x < 0.002)}'; then
                note "  **ERROR: $a and $b are practically identical** (RMSE $d)"
                note "  - one of the two was probably not applied at all"
                duplicates=$((duplicates + 1))
            elif awk -v x="$d" 'BEGIN{exit !(x < 0.02)}'; then
                note "  Note: $a and $b are very similar (RMSE $d) -"
                note "  both were applied, it is a design question."
            fi
        done
    done
    [ "$duplicates" -eq 0 ] && note "  All variants differ clearly." \
                            || errors=$((errors + duplicates))
fi

# ── Part 2: quick switching ──────────────────────────────────────────────
note "\n## Part 2 - quick switching without a reboot\n"
note "Three variants in a row, without a pause. This used to lead to the"
note "black desktop on the third call within 60 seconds, because systemd only allows"
note "three starts per minute and the session start counts as the first.\n"

three=("${variants[@]:0:3}")
for v in "${three[@]}"; do
    ssh_ "cd nt-legacy && ./apply.sh $v" >/dev/null 2>&1
    note "  applied: $v"
done
sleep 8
shell=$(ssh_ 'systemctl --user is-active plasma-plasmashell.service' | tr -d '\r')
note "\nplasmashell afterwards: **$shell**"
if [ "$shell" != "active" ]; then
    report_error "After three quick switches plasmashell is no longer running ('$shell')"
    note "\nJournal:"
    note "\`\`\`\n$(ssh_ 'journalctl --user -u plasma-plasmashell.service -n 12 --no-pager')\n\`\`\`"
fi
"$VMCTL" shot "$OUT/screenshots/after-quick-switch.png" >/dev/null 2>&1

# Is anything visible at all? Otherwise a black screen goes
# unnoticed - the services can be running and still draw nothing.
mean=$(magick "$OUT/screenshots/after-quick-switch.png" -format "%[fx:mean]" info: 2>/dev/null)
note "Image brightness: $mean (close to 0 = black screen)"
awk -v m="$mean" 'BEGIN{exit !(m < 0.03)}' 2>/dev/null && \
    report_error "Screen is practically black after switching"

# ── Result ───────────────────────────────────────────────────────────────
note "\n---\n"
if [ "$errors" -eq 0 ]; then
    note "## Result: all checks passed"
else
    note "## Result: $errors issue(s)"
fi
note "\nReport: \`${REPORT#$LAB/}\`"
echo
echo "Done. Report: $REPORT"
exit $((errors > 0))
