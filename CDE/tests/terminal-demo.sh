#!/usr/bin/env bash
clear
printf '\n  C D E   /   C O P P E R\n'
printf '  ________________________________\n\n'
printf '  A contemporary UNIX workstation\n\n'
printf '  Desktop      KDE Plasma 6\n'
printf '  Session      Wayland\n'
printf '  Decoration   Motif / Aurorae\n'
printf '  Icons        Scalable SVG\n\n'
printf '  '
for c in 44 46 47 43 41; do printf '\033[%sm    \033[0m' "$c"; done
printf '\n\n'
exec bash --norc
