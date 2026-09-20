#!/usr/bin/env bash
# Holt ein fremdes Icon-Set und bereitet es fuer NT Legacy auf.
#
#   ./fetch-icons.sh              # Chicago95 (Vorgabe, wie bisher)
#   ./fetch-icons.sh se98         # SE98 - Win98-SE-Stil, viel groesser
#   ./fetch-icons.sh beide
#
# Keines der beiden Sets liegt im Repository, und keines ist Teil der
# Weitergabe - Begruendung in ATTRIBUTION.md. Kurz: Chicago95 hat keine
# LICENSE-Datei, SE98 hat eine (GPL-2.0), bezeichnet sich in seiner
# eigenen README aber als "manual copy-paste fork" von Chicago95 mit
# Material aus dem MicroSoft-Memphis-Projekt. Ein GPL-Stempel deckt nur,
# was der Setzende selbst geschaffen hat. Lies das, bevor du das Theme
# weitergibst.
#
# Fuer den eigenen Rechner ist beides unbedenklich: Die Sets landen in
# ~/.local/share/icons und sind in den Systemeinstellungen waehlbar.

set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Wo liegen die Werkzeuge aus tools/?
#
# Zwei Lagen, und beide sind normal: im Arbeitsbaum neben nt-legacy/, im
# ausgelieferten Archiv als nt-legacy/tools/. Bis 0.2.7 stand hier fest
# "$HIER/../tools" - aus dem Archiv heraus lief das ins Leere, gemeldet
# aus der Community: "line 65: /nt-legacy/../tools/fix-index-theme.py:
# No such file or directory". Und weil das erst in Zeile 65 auffiel, war
# der Klon von Chicago95 schon gelaufen.
if [ -d "$HIER/tools" ]; then
    WERKZEUGE="$HIER/tools"
else
    WERKZEUGE="$HIER/../tools"
fi
for w in fix-index-theme.py gen-symbolic-aliase.py gen-icon-aliase.py; do
    if [ ! -f "$WERKZEUGE/$w" ]; then
        echo "FEHLER: $w fehlt (gesucht in $WERKZEUGE)." >&2
        echo "        Dieses Skript braucht das Verzeichnis tools/." >&2
        echo "        Es steckt im Gesamtarchiv und im Quelltext:" >&2
        echo "        https://github.com/huppiflupp/nt-legacy" >&2
        exit 1
    fi
done

WELCHE="${1:-chicago95}"
case "$WELCHE" in
    chicago95|se98|beide) ;;
    -h|--hilfe|--help)
        # Der Kopfkommentar bis zur ersten Zeile, die keiner mehr ist.
        # Mit fester Zeilenspanne stand hier "set -euo pipefail" mit drin.
        awk 'NR>1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"
        exit 0 ;;
    *)
        echo "FEHLER: unbekannte Quelle '$WELCHE'." >&2
        echo "        Moeglich: chicago95, se98, beide" >&2
        exit 1 ;;
esac

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Beiden Saetzen gemeinsam: Sektionen ergaenzen, symbolische Aliase, die
# von Dolphin geforderten Namen. Ohne den letzten Schritt sind die
# Ansichtsmodi in der Werkzeugleiste Breeze-Symbole mitten in der
# Pixelart.
nachbereiten() {
    local ziel="$1"
    "$WERKZEUGE/fix-index-theme.py"     "$ziel"
    "$WERKZEUGE/gen-symbolic-aliase.py" "$ziel"
    "$WERKZEUGE/gen-icon-aliase.py"     "$ziel"
}

hole_chicago95() {
    local ziel="$HIER/icons/NTLegacy"

    echo "Hole Chicago95 (nur den Icon-Ordner) …"
    git clone --depth 1 --filter=blob:none --sparse \
        https://github.com/grassmunk/Chicago95.git "$TMP/c95" 2>&1 | tail -1
    git -C "$TMP/c95" sparse-checkout set Icons/Chicago95 >/dev/null

    rm -rf "$ziel"
    mkdir -p "$(dirname "$ziel")"
    cp -r "$TMP/c95/Icons/Chicago95" "$ziel"
    rm -f "$ziel/icon-theme.cache"
    find "$ziel" \( -name '*.html' -o -name '*.old' \) -delete

    echo "Passe index.theme an …"
    python3 - "$ziel" <<'PY'
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
        z="$ziel/places/scalable/$f"
        if [ -L "$z" ] && readlink "$z" | grep -q open; then rm -f "$z"; fi
    done

    # status/symbolic als Scalable 8..512 gewinnt gegen alle Fixed-Groessen
    # und liefert 16px-Bitmaps hochskaliert - besonders im Systemabschnitt.
    python3 - "$ziel" <<'PY2'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
m = re.search(r"\[status/symbolic\][^\[]*", s)
if m:
    p.write_text(s.replace(m.group(0),
        "[status/symbolic]\nSize=16\nContext=Status\nType=Fixed\n\n"))
PY2

    nachbereiten "$ziel"
    echo "  -> $ziel"
}

hole_se98() {
    local ziel="$HIER/icons/NTLegacySE98"

    echo "Hole SE98 (nur den Icon-Ordner) …"
    git clone --depth 1 --filter=blob:none --sparse \
        https://www.opencode.net/nestoris/Win98SE.git "$TMP/se98" 2>&1 | tail -1
    git -C "$TMP/se98" sparse-checkout set SE98 >/dev/null

    rm -rf "$ziel"
    mkdir -p "$(dirname "$ziel")"
    cp -a "$TMP/se98/SE98" "$ziel"
    rm -f "$ziel/icon-theme.cache"

    # SE98 fuehrt seine Werkzeuge und Vorschautabellen im Themenbaum mit:
    # awk-Skripte, icons.html je Kontext, Groessenlisten, ein template.
    # Nichts davon ist ein Icon. Die .icon-Dateien bleiben - das sind
    # gueltige Freedesktop-Metadaten.
    find "$ziel" \( -name '*.html' -o -name '*.md' -o -name '*.awk' \
                 -o -name '*.sh' -o -name 'sizes_brief' -o -name 'sizes_md' \
                 -o -name 'template' -o -name 'file.data' -o -name 'apps.txt' \
                 -o -name 'table_grassmunk' \) -delete

    echo "Passe index.theme an …"
    python3 - "$ziel" <<'PY3'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()

s = re.sub(r"^Name=.*$", "Name=NT Legacy (SE98)", s, count=1, flags=re.M)

# Die uebersetzten Comment-Zeilen (26 Sprachen) beschreiben ein anderes
# Theme, als hier steht. Raus damit, eine Zeile genuegt.
s = re.sub(r"^Comment\[[^\]]+\]=.*\n", "", s, flags=re.M)
s = re.sub(r"^Comment=.*$",
           "Comment=Windows-98-SE-Icons fuer Plasma 6, auf Basis von SE98 "
           "(nestoris) - nicht Teil der Weitergabe, siehe ATTRIBUTION.md",
           s, count=1, flags=re.M)

# "Breeze" gross gibt es als Verzeichnis nicht. Das Theme heisst breeze,
# klein - auf jeder Distribution. Die Rueckfallkette lief also ins Leere:
# was SE98 nicht hat, landete direkt bei hicolor, und hicolor ist fast
# leer. Reihenfolge wie im uebrigen Theme, breeze zuerst.
if re.search(r"^Inherits=", s, re.M):
    s = re.sub(r"^Inherits=.*$", "Inherits=breeze,Adwaita,hicolor",
               s, count=1, flags=re.M)
else:
    s = s.replace("[Icon Theme]", "[Icon Theme]\nInherits=breeze,Adwaita,hicolor", 1)

p.write_text(s)
PY3

    nachbereiten "$ziel"
    echo "  -> $ziel"
}

case "$WELCHE" in
    chicago95) hole_chicago95 ;;
    se98)      hole_se98 ;;
    beide)     hole_chicago95; echo; hole_se98 ;;
esac

echo
echo "Fertig. Danach: ./build.py && ./install.sh"
