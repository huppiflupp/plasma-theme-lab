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

"$HIER/../tools/fix-index-theme.py" "$ZIEL"
"$HIER/../tools/gen-symbolic-aliase.py" "$ZIEL"

echo
echo "Fertig. Danach: ./build.py && ./install.sh"
