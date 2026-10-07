# CDE Copper's own palettes

Same format as CDE's `.dp` files in `../cde/`: eight background colours as
16-bit X colours, in CDE's roles (active frame, inactive frame, workspace,
text fields, windows, menus and dialogs, fourth workspace button, front
panel). Motif's rules derive the rest.

One extension, read only here: a line `fg=#rrggbb` sets the text colour of
every set instead of Motif's black or white; `palettes.py` moves it toward
black or white until it reads at 4.5:1 on each background (Darkroom's red).

All dark, with light text and one accent in set 1. GPL-2.0-or-later like
the rest of the theme.
