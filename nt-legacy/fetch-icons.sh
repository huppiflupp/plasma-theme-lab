#!/usr/bin/env bash
# Holt das Icon-Set und bereitet es fuer NT Legacy auf.
#
# Das Set ist ein Ableger von Chicago95. Es liegt nicht im Repository -
# Begruendung in ATTRIBUTION.md: Chicago95 hat keine LICENSE-Datei, und
# die Herkunft der Bitmaps ist ungeklaert. Lies das, bevor du das Theme
# weitergibst.

set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIEL="$HIER/icons/NTLegacy"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Hole Chicago95 (nur den Icon-Ordner) …"
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/grassmunk/Chicago95.git "$TMP/c95" 2>&1 | tail -1
git -C "$TMP/c95" sparse-checkout set Icons/Chicago95 >/dev/null

rm -rf "$ZIEL"
mkdir -p "$(dirname "$ZIEL")"
cp -r "$TMP/c95/Icons/Chicago95" "$ZIEL"
rm -f "$ZIEL/icon-theme.cache"
find "$ZIEL" \( -name '*.html' -o -name '*.old' \) -delete

echo "Passe index.theme an …"
python3 - "$ZIEL" <<'PY'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
s = s.replace("Name=Chicago95", "Name=NT Legacy")
s = re.sub(r"^Comment=.*$", "Comment=Windows-NT-4.0-Icons fuer Plasma 6, "
           "auf Basis von Chicago95", s, count=1, flags=re.M)
# Ohne Inherits faellt Plasma fuer jedes fehlende Icon auf hicolor
# zurueck - und hicolor ist fast leer.
if "Inherits=" not in s:
    s = s.replace("[Icon Theme]", "[Icon Theme]\nInherits=breeze,hicolor", 1)
p.write_text(s)
PY

# In Chicago95 zeigen folder.svg, inode-directory.svg und
# folder-symbolic.svg unter places/scalable auf folder_open.svg. Da
# scalable bis 256px gewinnt, zeigt Dolphin ab 64px fuer JEDEN
# geschlossenen Ordner einen offenen. Ohne die Symlinks greift
# places/48/folder.png, darueber Breeze - weniger falsch.
for f in folder.svg inode-directory.svg folder-symbolic.svg; do
    z="$ZIEL/places/scalable/$f"
    if [ -L "$z" ] && readlink "$z" | grep -q open; then rm -f "$z"; fi
done

# status/symbolic als Scalable 8..512 gewinnt gegen alle Fixed-Groessen
# und liefert 16px-Bitmaps hochskaliert - besonders im Systemabschnitt.
python3 - "$ZIEL" <<'PY2'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
m = re.search(r"\[status/symbolic\][^\[]*", s)
if m:
    p.write_text(s.replace(m.group(0),
        "[status/symbolic]\nSize=16\nContext=Status\nType=Fixed\n\n"))
PY2

"$HIER/../tools/fix-index-theme.py" "$ZIEL"
"$HIER/../tools/gen-symbolic-aliase.py" "$ZIEL"

# Chicago95 traegt GNOME-Namen (view-grid, view-list), Dolphin fordert
# aber view-list-icons, view-list-details, view-file-columns an. Ohne
# diese Verweise sind die Ansichtsmodi in der Werkzeugleiste Breeze-
# Symbole mitten in der Pixelart.
"$HIER/../tools/gen-icon-aliase.py" "$ZIEL"

echo
echo "Fertig. Danach: ./build.py && ./install.sh"
