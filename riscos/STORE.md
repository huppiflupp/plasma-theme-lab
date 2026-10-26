# KDE Store (draft)

Not uploaded yet (26.10.2026). One entry, like Warp Legacy: the global
theme with install.sh beside it, all variants and wallpapers inside.

| Entry | File | Category |
|---|---|---|
| **RISC Legacy** | `risc-legacy-<version>.tar.xz` | Global Themes (Plasma 6) |

Licence GPL-2.0-or-later (the RISC OS 4 window tools: Apache 2.0, RISC OS
Open, with LICENSE and NOTICE in the archive).

## Pictures (to make)

From the Fedora VM, English session, 1920×1080:

1. RISC Legacy (classic) with the iconbar, a Filer window and an iconised
   window on the iconbar.
2. **The command line (F12)** along the bottom: `*Help`, then `*Cat` and
   `*Ex` in the home directory — shows what the star commands are.
3. **A Task Window (Ctrl+F12)** beside a Filer window: `*Dir Documents`,
   `*Cat`, and an ordinary `ls | head` to show that bash is underneath.
4. The iconbar's menus: a program's menu (Menu on its icon) and the Apps
   menu.
5. Day and night: the same desktop at day and after the switch (2026 and
   2026 Dark on Fenland; classic on Limestone and Graphite at night).
6. The variants side by side (the previews in `previews/`).

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
