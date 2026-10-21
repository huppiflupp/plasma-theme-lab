#!/usr/bin/env bash
# Give Firefox the Warp Legacy look without a signed add-on, per profile:
#
#   firefox-apply.sh neon|neon-blue|classic [--profile DIR | --all] [--system-titlebar]
#   firefox-apply.sh remove       [--profile DIR | --all]
#   firefox-apply.sh status
#
# What it does, and nothing else:
#   <profile>/chrome/warp-legacy/      our userChrome.css, userContent.css, state
#   <profile>/chrome/userChrome.css    one marked @import block (file created
#   <profile>/chrome/userContent.css   if missing, never overwritten)
#   <profile>/user.js                  one marked block enabling
#                                      toolkit.legacyUserProfileCustomizations.stylesheets
#                                      (and, with --system-titlebar,
#                                      browser.tabs.inTitlebar=0: Plasma's frame)
# "remove" takes all of it back, including the prefs Firefox copied into
# prefs.js. Firefox must be closed (it rewrites prefs.js on exit).
# Default profiles: those Firefox starts with ([Install…] Default=, else
# Default=1) in every profile root found (native, XDG, Flatpak, Snap).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARK_BEGIN=">>> warp-legacy: added by firefox-apply.sh, undo with \"firefox-apply.sh remove\" >>>"
MARK_END="<<< warp-legacy <<<"
PREF_CSS="toolkit.legacyUserProfileCustomizations.stylesheets"
PREF_TITLE="browser.tabs.inTitlebar"

die() { echo "firefox-apply: $*" >&2; exit 1; }
usage() { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

action="${1:-}"; shift || true
case "$action" in neon|neon-blue|classic|remove|status) ;; -h|--help|"") usage 0 ;; *) usage 1 ;; esac
profiles=() all=0 titlebar=0
while [ $# -gt 0 ]; do
    case "$1" in
        --profile) [ $# -ge 2 ] || die "--profile needs a directory"; profiles+=("$(cd "$2" && pwd)"); shift ;;
        --all) all=1 ;;
        --system-titlebar) titlebar=1 ;;
        -h|--help) usage 0 ;;
        *) die "unknown option: $1" ;;
    esac
    shift
done

# The generated CSS: next to this script (installed build), or in the build
# tree when run from the sources.
css_dir() {
    local d
    for d in "$HERE/userchrome/$1" "$HERE/../build/warp-legacy/browser/userchrome/$1"; do
        [ -f "$d/userChrome.css" ] && { echo "$d"; return; }
    done
    if [ -f "$HERE/build_browser.py" ]; then
        python3 "$HERE/build_browser.py" >&2
        echo "$HERE/../build/warp-legacy/browser/userchrome/$1"; return
    fi
    die "no built userChrome.css for '$1' (run build.py first)"
}

roots() {
    local r
    for r in "$HOME/.mozilla/firefox" "$HOME/.config/mozilla/firefox" \
             "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox" \
             "$HOME/.var/app/org.mozilla.firefox/config/mozilla/firefox" \
             "$HOME/snap/firefox/common/.mozilla/firefox"; do
        [ -f "$r/profiles.ini" ] && echo "$r"
    done
    return 0
}

# Profiles of one root: the install defaults, else Default=1, or all of them.
root_profiles() {
    awk -v root="$1" -v all="$2" -F= '
        function flush() { if (path != "") { p = (rel == "1" ? root "/" path : path)
                               allp[p] = 1; if (def == "1") dflt[p] = 1
                               if (sect ~ /^Install/) inst[p] = 1 } path = ""; rel = "1"; def = "" }
        /^\[/ { flush(); sect = substr($0, 2, length($0) - 2); next }
        $1 == "Path" { path = substr($0, 6) }
        $1 == "IsRelative" { rel = $2 }
        $1 == "Default" { if (sect ~ /^Install/) { p = $2; if (p !~ /^\//) p = root "/" p; inst[p] = 1 } else def = $2 }
        END { flush(); n = 0
              if (all == "1") { for (p in allp) print p; exit }
              for (p in inst) { print p; n++ }
              if (n == 0) for (p in dflt) print p }' "$1/profiles.ini" | sort -u
}

if [ ${#profiles[@]} -eq 0 ]; then
    while read -r root; do
        while read -r p; do [ -d "$p" ] && profiles+=("$p"); done < <(root_profiles "$root" "$all")
    done < <(roots)
fi
[ ${#profiles[@]} -gt 0 ] || die "no Firefox profile found (start Firefox once first)"

in_use() {   # Firefox holds <profile>/lock (a symlink "host:+pid") while running
    local target pid
    target=$(readlink "$1/lock" 2>/dev/null) || return 1
    pid=${target##*+}
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && return 0
    pgrep -x firefox >/dev/null 2>&1 || pgrep -x firefox-bin >/dev/null 2>&1
}

strip_block() {   # remove our marked block from a file, in place
    [ -f "$1" ] || return 0
    awk -v b="$MARK_BEGIN" -v e="$MARK_END" '
        index($0, b) { skip = 1; next } skip && index($0, e) { skip = 0; next } !skip' "$1" > "$1.warp-tmp"
    cat "$1.warp-tmp" > "$1" && rm -f "$1.warp-tmp"
}

has_block() { [ -f "$1" ] && grep -qF "$MARK_BEGIN" "$1"; }
blank() { ! grep -q '[^[:space:]]' "$1"; }
state_get() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -1 || true; }
pref_line() { grep -F "user_pref(\"$2\"," "$1/prefs.js" 2>/dev/null | head -1 || true; }

add_import() {   # $1 file, $2 our file name; @import must precede other rules
    local f="$1" block
    block="/* $MARK_BEGIN */
@import url(\"warp-legacy/$2\");
/* $MARK_END */"
    has_block "$f" && return 0
    if [ ! -e "$f" ]; then
        printf '%s\n' "$block" > "$f"; echo "created_$2=1" >> "$STATE"
    elif head -1 "$f" | grep -q '^@charset'; then
        { head -1 "$f"; printf '%s\n' "$block"; tail -n +2 "$f"; } > "$f.warp-tmp" && cat "$f.warp-tmp" > "$f" && rm -f "$f.warp-tmp"
    else
        { printf '%s\n' "$block"; cat "$f"; } > "$f.warp-tmp" && cat "$f.warp-tmp" > "$f" && rm -f "$f.warp-tmp"
    fi
}

apply() {
    local prof="$1" src="$2" chrome="$1/chrome"
    STATE="$chrome/warp-legacy/state"
    if [ ! -f "$STATE" ]; then   # first apply: remember what was there before
        local made=0
        [ -d "$chrome" ] || made=1
        mkdir -p "$chrome/warp-legacy"
        {
            echo "created_chrome=$made"
            echo "pref_css_before=$(pref_line "$prof" "$PREF_CSS")"
            echo "pref_title_before=$(pref_line "$prof" "$PREF_TITLE")"
            [ -e "$prof/user.js" ] && echo "created_userjs=0" || echo "created_userjs=1"
        } > "$STATE"
    fi
    cp "$src/userChrome.css" "$src/userContent.css" "$chrome/warp-legacy/"
    # dropping --system-titlebar on a re-apply: give the title bar back
    if [ "$(state_get "$STATE" titlebar)" = 1 ] && [ "$titlebar" = 0 ]; then
        restore_pref "$prof" "$PREF_TITLE" "$(state_get "$STATE" pref_title_before)"
    fi
    sed -i '/^variant=/d;/^titlebar=/d' "$STATE"
    echo "variant=$VARIANT" >> "$STATE"
    echo "titlebar=$titlebar" >> "$STATE"
    add_import "$chrome/userChrome.css" userChrome.css
    add_import "$chrome/userContent.css" userContent.css
    strip_block "$prof/user.js"
    {
        echo "// $MARK_BEGIN"
        echo "user_pref(\"$PREF_CSS\", true);"
        if [ "$titlebar" = 1 ]; then echo "user_pref(\"$PREF_TITLE\", 0);"; fi
        echo "// $MARK_END"
    } >> "$prof/user.js"
    echo "Warp Legacy ($VARIANT) applied: $prof"
}

restore_pref() {   # drop the pref from prefs.js, put back the line from before
    local prefs="$1/prefs.js" name="$2" before="$3"
    [ -f "$prefs" ] || return 0
    grep -vF "user_pref(\"$name\"," "$prefs" > "$prefs.warp-tmp" || true
    if [ -n "$before" ]; then printf '%s\n' "$before" >> "$prefs.warp-tmp"; fi
    cat "$prefs.warp-tmp" > "$prefs" && rm -f "$prefs.warp-tmp"
}

remove() {
    local prof="$1" chrome="$1/chrome" f
    STATE="$chrome/warp-legacy/state"
    if [ ! -f "$STATE" ] && ! has_block "$prof/user.js"; then
        echo "Not applied: $prof"; return
    fi
    for f in userChrome.css userContent.css; do
        if has_block "$chrome/$f"; then
            strip_block "$chrome/$f"
            [ "$(state_get "$STATE" "created_$f")" = 1 ] && blank "$chrome/$f" && rm -f "$chrome/$f" || true
        fi
    done
    strip_block "$prof/user.js"
    [ "$(state_get "$STATE" created_userjs)" = 1 ] && [ -f "$prof/user.js" ] && blank "$prof/user.js" && rm -f "$prof/user.js" || true
    if [ -f "$STATE" ]; then
        restore_pref "$prof" "$PREF_CSS" "$(state_get "$STATE" pref_css_before)"
        if [ "$(state_get "$STATE" titlebar)" = 1 ]; then
            restore_pref "$prof" "$PREF_TITLE" "$(state_get "$STATE" pref_title_before)"
        fi
        local made; made=$(state_get "$STATE" created_chrome)
        rm -rf "$chrome/warp-legacy"
        [ "$made" = 1 ] && rmdir "$chrome" 2>/dev/null || true
    fi
    echo "Warp Legacy removed: $prof"
}

if [ "$action" = status ]; then
    for p in "${profiles[@]}"; do
        v=$(state_get "$p/chrome/warp-legacy/state" variant)
        echo "${v:-none}  $p"
    done
    exit 0
fi

for p in "${profiles[@]}"; do
    in_use "$p" && die "Firefox is running with $p - close it first (it rewrites prefs.js on exit)"
done
if [ "$action" = remove ]; then
    for p in "${profiles[@]}"; do remove "$p"; done
else
    VARIANT="$action"
    src=$(css_dir "$action")
    for p in "${profiles[@]}"; do apply "$p" "$src"; done
    echo "Start Firefox to see it. Undo: $0 remove"
fi
