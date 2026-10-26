# KDE Store (draft)

Not uploaded yet (26.10.2026); sources and release on GitHub:
https://github.com/huppiflupp/risc-legacy. One entry, like Warp Legacy: the global
theme with install.sh beside it, all variants and wallpapers inside.

| Entry | File | Category |
|---|---|---|
| **RISC Legacy** | `risc-legacy-<version>.tar.xz` | Global Themes (Plasma 6) |

Licence GPL-2.0-or-later (the RISC OS 4 window tools: Apache 2.0, RISC OS
Open, with LICENSE and NOTICE in the archive).

## Pictures

`screenshots/store/`, taken in the Fedora VM in an English session at
1920×1080 (26.10.2026):

| File | Shows |
|---|---|
| `1-filer-iconbar.png` | classic: two Filer windows, iconised windows with their title on the iconbar |
| `2-command-line-star-commands.png` | the command line (F12) along the bottom: `Dir`, `Help`, `Cat`, `Ex` |
| `3-task-window.png` | a Task Window (Ctrl+F12) beside a Filer: star commands and an ordinary `ls` |
| `4a-iconbar-program-menu.png` | Menu on a program's icon: its menu, titled with its name |
| `4b-apps-menu.png` | the Apps menu, cascading into the programs |
| `5a-2026-day.png`, `5b-2026-night.png` | 2026 by day and 2026 Dark at night, the same Fenland picture |
| `5c-classic-day.png`, `5d-classic-night-graphite.png` | classic on Limestone by day, Graphite at night |
| `variant-<key>.jpg` | the same scene in each of the eight variants |

The previews in System Settings › Global Theme (`previews/`) are made from
the variant pictures. Store order: 1, 2, 3, 4b, 5a/5b, then the variants.

## Description

RISC OS for Plasma 6. RISC OS 3 and 4 as close as the sources allow,
the same desktop taken on to 2026 in light and dark, and the palettes of
RISC OS Pi, the Iyonix, Acorn green and Graphite.

**What it brings**

- The window frame with RISC OS's tools (Back and Close on the left,
  Iconise and Toggle size on the right); RISC OS 4's stone tools from the
  published RISC OS sources.
- The iconbar along the bottom: Discs, Home, media and Apps on the left,
  the running programs on the right, iconised windows with their title.
- RISC OS's three mouse buttons: Select opens, Menu (middle) opens the
  menu where the pointer is, Adjust (right) does the other thing — on the
  iconbar, the desktop and the title bars.
- **The command line with star commands.** F12 opens RISC OS's command
  line along the bottom of the screen, Ctrl+F12 a Task Window. Every
  command starts with a star, as on the BBC Micro and in RISC OS:
  `*Cat` lists a directory, `*Dir` changes it, `*Ex` shows details,
  `*Copy`, `*Rename`, `*Wipe`, `*Type`, `*Run`, `*Free`, `*Help` … Bash is
  underneath: without a star everything works as always.
- An icon set of its own: every icon Breeze has, drawn anew in RISC OS's
  manner, in RISC OS 4's and RISC OS 5's colours.
- Wallpapers in pairs for Plasma's day/night switching: limestone,
  marble, the fens near Cambridge, raspberry leaves, frosted glass,
  acorns, slate.
- Programs styled with Kvantum: black outlines, the grey bevel, the cream
  ring round the default button, red radio dots.

**Install**: unpack, then `./install.sh --apply classic --layout` (or 4,
2026, 2026-dark, pi, iyonix, acorn, graphite). Every setting it changes
is recorded; `./uninstall.sh` puts them back. Needs Kvantum.

Not affiliated with RISC OS Open Ltd, RISC OS Developments or Acorn.
