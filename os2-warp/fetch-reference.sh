#!/usr/bin/env bash
# The screenshots DESIGN.md is measured from. Copyrighted (IBM, Stardock,
# the photographers), so they stay out of the repository and the package.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p reference
fetch() { [ -s "reference/$1" ] || curl -fsSL -A "Mozilla/5.0" -o "reference/$1" "$2"; }
fetch warp4-objectdesktop.jpg https://cdn.britannica.com/00/258500-050-244F0C3A/IBM-OS2-Warp-4-operating-system.jpg
fetch warp4-warpcenter.png    http://toastytech.com/guis/os24_warpbar.png
fetch warp3-launchpad.png     https://movq.de/blog/postings/2020-11-11/0/warp3-qemu.png
ls -l reference
