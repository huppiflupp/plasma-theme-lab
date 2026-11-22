# CDE Copper's own palettes

Same format as CDE's `.dp` files in `../cde/`: eight background colours as
16-bit X colours, in CDE's roles (active frame, inactive frame, workspace,
text fields, windows, menus and dialogs, fourth workspace button, front
panel). Motif's rules derive the rest.

One extension, read only here: a line `fg=#rrggbb` sets the text colour of
every set instead of Motif's black or white; `palettes.py` moves it toward
black or white until it reads at 4.5:1 on each background (Darkroom's red).

All dark, with light text and one accent in set 1, except the two IRIX
schemes below. GPL-2.0-or-later like the rest of the theme.

## IRIX schemes

`IndigoMagic.dp` (IRIX 6.5's default scheme) and `Gotham.dp` (its dark one)
take their colours from SGI's scheme files as transcribed, at gamma 1.7, by
wlRIX (https://github.com/wlRIX/wlrix-assets, `palette/classic.json` and
`palette/gotham.json`, MIT). Only colour values are taken, no files. IRIX
names some eighty colour roles; they map onto CDE's eight sets like this:

| Set | CDE role | IRIX role | IndigoMagic | Gotham |
|---|---|---|---|---|
| 1 | active frame | wmActiveBackground | `#a59f80` | `#817b5c` |
| 2 | inactive frame | wmBackground | `#808080` | `#5c5c5c` |
| 3 | workspace | ImdDarkGrey (IndigoMagic), BasicBackground at 65 % (Gotham, as wlRIX) | `#555555` | `#1b1b1b` |
| 4 | text fields | TextFieldBackground | `#b98e8e` | `#3c283c` |
| 5 | windows | BasicBackground | `#c1c1c1` | `#2a2a2a` |
| 6 | menus, dialogs | ImdMenubarBackground (IndigoMagic), ReadOnlyBackground (Gotham) | `#d6d6d6` | `#383838` |
| 7 | fourth workspace button | AlternateBackground5 | `#5680ab` | `#2b2b5a` |
| 8 | front panel | ButtonBackground | `#999999` | `#494949` |

IndigoMagic sets `fg=#000000`: IRIX's TextForeground was black on every
surface, where Motif would pick white on the darker sets. Black stays on all
sets but the workspace, where it is lightened to `#cccccc` (4.6:1). Gotham
keeps Motif's choice, so its active title text is black (4.9:1) where IRIX
drew white (4.2:1). Buttons darker than
the panel behind them, a mark of the IRIX look, are lost: CDE has no colour
set of its own for buttons.
