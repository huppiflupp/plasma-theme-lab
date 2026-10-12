#!/usr/bin/env bash
# Runs a theme through the test VM and records what happens.
#
#   ./run-theme-test.sh <theme-directory> [<install-command>]
#
# Sequence: back to the snapshot 'clean' -> copy the theme in ->
# install -> apply -> screenshot -> reboot -> screenshot ->
# uninstall -> check whether the initial state is back.
#
# The reboot is the most important step and the one most often
# skipped: a broken theme usually only shows up at the next
# login.

set -uo pipefail   # no -e: a failed step is a
                   # test result, not a reason to abort

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"

THEME_DIR="${1:?Usage: $0 <theme-directory> [<install-command>]}"
INSTALL_CMD="${2:-./install.sh}"

[ -d "$THEME_DIR" ] || { echo "ERROR: $THEME_DIR does not exist"; exit 1; }

NAME="$(basename "$THEME_DIR")"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$LAB/tests/runs/$NAME-$STAMP"
mkdir -p "$OUT/screenshots"
REPORT="$OUT/report.md"

step=0
note() { echo -e "$*" | tee -a "$REPORT"; }
ssh_() { "$VMCTL" ssh "$@" 2>&1; }
shot() {
    step=$((step+1))
    local file="$OUT/screenshots/$(printf '%02d' $step)-$1.png"
    "$VMCTL" shot "$file" >/dev/null 2>&1
    echo "  Screenshot: ${file#$LAB/}"
}

{
    echo "# Test run: $NAME"
    echo
    echo "- Time: $(date -Is)"
    echo "- Source: \`$THEME_DIR\`"
    echo "- Install command: \`$INSTALL_CMD\`"
    echo
} > "$REPORT"

# ---------------------------------------------------------------------------
note "## 1. Restore the initial state"
# Without a reset, the second run tests on the leftovers of the first.
if ! "$VMCTL" reset >/dev/null 2>&1; then
    note "ERROR: resetting to snapshot 'clean' failed."
    note "Does the snapshot exist? \`vm/vmctl.sh snap list\`"
    exit 1
fi
note "VM reset to snapshot 'clean'."

BEFORE="$(ssh_ 'for k in \
    "plasmarc Theme name" \
    "kdeglobals General ColorScheme" \
    "kdeglobals KDE widgetStyle" \
    "kdeglobals Icons Theme" \
    "kdeglobals KDE LookAndFeelPackage" \
    "kwinrc org.kde.kdecoration2 library"; do
      set -- $k; echo "$1/$2/$3 = $(kreadconfig6 --file $1 --group $2 --key $3)"
    done')"
note "\n<details><summary>Configuration before</summary>\n\n\`\`\`\n$BEFORE\n\`\`\`\n</details>"
shot initial-state

# ---------------------------------------------------------------------------
note "\n## 2. Transfer and install the theme"
# The trailing slashes are not cosmetic: without them rsync creates
# the source directory INSIDE the target (/home/tester/theme/niceos9/) instead
# of copying its contents in - and then the install command cannot
# find its own install.sh.
"$VMCTL" push "${THEME_DIR%/}/" "/home/tester/theme/" >/dev/null 2>&1 \
    || { note "ERROR while copying."; exit 1; }
if ! ssh_ 'test -d /home/tester/theme' >/dev/null 2>&1; then
    note "ERROR: /home/tester/theme is missing after copying."; exit 1
fi

# The installation runs without a terminal. An installer that asks
# interactively would hang - so either prepared answers from
# $ANSWERS or stdin from /dev/null, plus a timeout as an emergency brake.
#
#   ANSWERS='y\ny\nn\nn\nn\n' ./run-theme-test.sh ../niceos9
#
if [ -n "${ANSWERS:-}" ]; then
    note "\nPrepared answers to the installer's questions: \`$ANSWERS\`"
    LOG_INSTALL="$(ssh_ "cd /home/tester/theme && printf '%b' '$ANSWERS' | timeout 300 $INSTALL_CMD")"
else
    LOG_INSTALL="$(ssh_ "cd /home/tester/theme && timeout 300 $INSTALL_CMD < /dev/null")"
fi
RC=$?
note "\nExit code: \`$RC\`"
[ "$RC" -eq 124 ] && note "**Timeout** - the installer is probably waiting for input."
note "\n<details><summary>Installer output</summary>\n\n\`\`\`\n$LOG_INSTALL\n\`\`\`\n</details>"

# ---------------------------------------------------------------------------
note "\n## 3. What was installed?"
NEW="$(ssh_ 'find ~/.local/share/plasma ~/.local/share/color-schemes \
    ~/.local/share/aurorae ~/.local/share/icons ~/.local/share/wallpapers \
    -maxdepth 2 -mindepth 1 -newer /etc/plasma-lab-ready 2>/dev/null | sort')"
note "\n\`\`\`\n${NEW:-(nothing found)}\n\`\`\`"

# Changes outside $HOME are the real risk.
SYS="$(ssh_ 'sudo find /usr/share/sddm /usr/share/plymouth /boot/grub2 /etc/sddm.conf.d \
    -newer /etc/plasma-lab-ready 2>/dev/null | head -30')"
if [ -n "$SYS" ]; then
    note "\n**Warning - changed outside \$HOME:**\n\n\`\`\`\n$SYS\n\`\`\`"
else
    note "\nNo changes outside \$HOME. Good."
fi

# ---------------------------------------------------------------------------
note "\n## 4. Apply the theme"
# kpackagetool6 writes a status line ("Listing KPackageType: ... in ...")
# to the same output as the package names. Real ids contain
# neither spaces nor colons - that is what we filter on.
LNF="$(ssh_ 'kpackagetool6 -t Plasma/LookAndFeel -l 2>/dev/null' \
       | grep -E '^[A-Za-z0-9][A-Za-z0-9._+-]*$' | head -20)"
note "\nAvailable global themes:\n\n\`\`\`\n${LNF:-(none found)}\n\`\`\`"

TARGET="$(echo "$LNF" | grep -iv breeze | head -1)"
if [ -n "$TARGET" ]; then
    note "\nApplying: \`$TARGET\` (deliberately WITHOUT --resetLayout)"
    APPLY="$(ssh_ "plasma-apply-lookandfeel --apply '$TARGET'")"
    note "\n\`\`\`\n$APPLY\n\`\`\`"
    sleep 15
    shot after-apply

    # Cross-check: did anything change at all? An identical
    # image means applying had no effect - exactly the case
    # the first run of this harness missed, because it only
    # looked at "plasmashell is still running".
    A="$OUT/screenshots/01-initial-state.png"
    B="$OUT/screenshots/02-after-apply.png"
    if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then
        note "\n**The screen is unchanged.** Applying had no visible effect."
    else
        note "\nThe screen has changed visibly."
    fi

    ACTUAL="$(ssh_ 'echo "Plasma Style : $(kreadconfig6 --file plasmarc --group Theme --key name)"
echo "Color scheme : $(kreadconfig6 --file kdeglobals --group General --key ColorScheme)"
echo "Global theme : $(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)"
echo "Icons        : $(kreadconfig6 --file kdeglobals --group Icons --key Theme)"
echo "Decoration   : $(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)"
echo "Style        : $(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)"')"
    note "\nWhat was actually set:\n\n\`\`\`\n$ACTUAL\n\`\`\`"
    note "\nFor comparison, the target values from \`contents/defaults\`:\n"
    EXPECTED="$(ssh_ "cat ~/.local/share/plasma/look-and-feel/$TARGET/contents/defaults 2>/dev/null")"
    note "\`\`\`ini\n${EXPECTED:-(no defaults file)}\n\`\`\`"
else
    note "\nNo custom global theme found - skipped."
fi

# ---------------------------------------------------------------------------
note "\n## 5. Is the shell still running?"
SHELL_ST="$(ssh_ 'systemctl --user is-active plasma-plasmashell.service; \
                  systemctl --user show plasma-plasmashell.service -p NRestarts --value')"
note "\n\`\`\`\n$SHELL_ST\n\`\`\`"
case "$SHELL_ST" in
    active*) note "\nplasmashell is running." ;;
    *)       note "\n**plasmashell is NOT running.** That is a failure." ;;
esac

ERRORS="$(ssh_ 'journalctl --user -u plasma-plasmashell.service --since "-10 min" \
    -p warning --no-pager 2>/dev/null | tail -25')"
[ -n "$ERRORS" ] && note "\n<details><summary>Warnings in the journal</summary>\n\n\`\`\`\n$ERRORS\n\`\`\`\n</details>"

# ---------------------------------------------------------------------------
note "\n## 6. Reboot - does the theme survive a new session?"
# The most important test. Many themes look fine until you log out.
ssh_ 'sudo systemctl reboot' >/dev/null 2>&1
sleep 20
ready=false
for _ in $(seq 1 30); do
    if "$VMCTL" ssh 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1; then ready=true; break; fi
    sleep 10
done
if $ready; then
    sleep 25                       # time for autologin and session startup
    note "\nVM is reachable again after the reboot."
    AFTER_ST="$(ssh_ 'systemctl --user is-active plasma-plasmashell.service')"
    note "plasmashell: \`$AFTER_ST\`"
    shot after-reboot
else
    note "\n**The VM did not come back after the reboot.** Severe."
    shot reboot-failed
fi

# ---------------------------------------------------------------------------
note "\n## 7. Uninstallation"
if ssh_ 'test -x /home/tester/theme/uninstall.sh' >/dev/null 2>&1; then
    # The uninstaller asks the same questions as the installer.
    # Without answers it selects nothing and removes nothing - and the
    # test would wrongly report "nothing left" or "nothing checked".
    ANSWERS_UNINSTALL="${ANSWERS_UNINSTALL:-${ANSWERS:-}}"
    if [ -n "$ANSWERS_UNINSTALL" ]; then
        LOG_UNINST="$(ssh_ "cd /home/tester/theme && printf '%b' '$ANSWERS_UNINSTALL' | timeout 180 ./uninstall.sh")"
    else
        LOG_UNINST="$(ssh_ 'cd /home/tester/theme && timeout 180 ./uninstall.sh < /dev/null')"
    fi
    note "\n<details><summary>Output</summary>\n\n\`\`\`\n$LOG_UNINST\n\`\`\`\n</details>"

    AFTER="$(ssh_ 'for k in \
        "plasmarc Theme name" \
        "kdeglobals General ColorScheme" \
        "kdeglobals KDE widgetStyle" \
        "kdeglobals Icons Theme" \
        "kdeglobals KDE LookAndFeelPackage" \
        "kwinrc org.kde.kdecoration2 library"; do
          set -- $k; echo "$1/$2/$3 = $(kreadconfig6 --file $1 --group $2 --key $3)"
        done')"
    note "\n### Configuration: before versus after\n"
    DIFF="$(diff <(echo "$BEFORE") <(echo "$AFTER"))"
    if [ -z "$DIFF" ]; then
        note "Identical - the uninstallation is complete."
    else
        # Not every difference is a flaw. On a fresh account
        # the keys are not set at all; Plasma then silently uses
        # Breeze. If an uninstall.sh sets them explicitly to Breeze,
        # the result is the same - and safer, because a key
        # pointing to a deleted theme costs you the title bar.
        #
        # Therefore: if the values AFTER point to Breeze, that is
        # fine. If they still point to the tested theme, it is not.
        if echo "$DIFF" | grep -qiE '^\+.*(nt-legacy|NTLegacy)'; then
            note "**FLAW - the configuration still points to the theme:**\n\n\`\`\`diff\n$DIFF\n\`\`\`"
        else
            note "Difference, but harmless: the keys are now set"
            note "explicitly to Breeze instead of empty. The effect is the same.\n"
            note "<details><summary>Diff</summary>\n\n\`\`\`diff\n$DIFF\n\`\`\`\n</details>"
        fi
    fi
    REST="$(ssh_ 'find ~/.local/share/plasma ~/.local/share/aurorae ~/.local/share/color-schemes \
        -maxdepth 2 -mindepth 1 2>/dev/null | sort')"
    [ -n "$REST" ] && note "\nLeftover files:\n\n\`\`\`\n$REST\n\`\`\`"
else
    note "\nNo \`uninstall.sh\` present - cannot be checked."
fi

shot end

note "\n---\n\nReport: \`${REPORT#$LAB/}\`"
echo
echo "Done. Report: $REPORT"
