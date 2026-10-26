# RISC Legacy

RISC OS for KDE Plasma 6: RISC OS 3 and 4 as close as the sources allow,
the same desktop taken on to 2026 in light and dark, and four more
palettes. The iconbar along the bottom, the window frame with RISC OS's
tools, the three mouse buttons Select, Menu and Adjust, and the command
line with its star commands.

Not affiliated with RISC OS Open Ltd, RISC OS Developments or Acorn. The
window tools of RISC OS 4 come from the RISC OS sources, which RISC OS Open
published under the Apache License 2.0 (`vendor/riscos-open/`, with its
LICENSE and NOTICE); everything else (icons, wallpapers, colours, the
iconbar) is drawn and written anew. The theme itself: GPL-2.0-or-later.

## Variants

| Variant | What it is | Wallpaper (day / night) |
|---|---|---|
| RISC Legacy | RISC OS 3: grey windows, a cream title for the window with the focus | Limestone |
| RISC Legacy 4 | RISC OS 4: the stone-textured window tools | Marble |
| RISC Legacy 2026 | RISC OS taken on to 2026, smooth and warm | Fenland at dawn / blue hour |
| RISC Legacy 2026 Dark | the same at night, the focus in brass | Fenland |
| RISC Legacy Pi | RISC OS Pi's green desktop, raspberry for selections | Raspberry leaves |
| RISC Legacy Iyonix | the Iyonix's blue | Frosted glass |
| RISC Legacy Acorn | RISC OS 4's stone with Acorn green | Acorns |
| RISC Legacy Graphite | classic RISC OS in darker greys | Slate |

Besides these seven, eighteen ray-traced wallpapers (POV-Ray): chrome
spheres on a chessboard, polyhedra, a marble Lipizzaner, singularities
on a board or a green grid — each by day and in moonlight.

Every wallpaper has a day and a night picture of the same scene. With
Plasma's automatic day/night switching (System Settings › Global Theme)
the desktop moves to the variant's night partner — 2026 Dark for 2026,
Graphite for the other light variants — and back in the morning; the
wallpaper changes its light, not its place.

## Handling: Select, Menu, Adjust

RISC OS uses all three mouse buttons: **Select** (left) chooses and opens,
**Menu** (middle) opens a menu where the pointer is — RISC OS has no menu
bars —, **Adjust** (right) does the complementary thing.

| Where | Select | Menu | Adjust |
|---|---|---|---|
| A program on the iconbar | bring forward, or iconise when in front | the program's menu, titled with its name | another window |
| Apps on the iconbar | the applications menu | the same | the applications as a Filer window |
| Discs, Home, media | a Filer window | | |
| The desktop | | the desktop's menu | |
| A title bar | | the window's menu | |

Folders open with a double click, each in a window of its own, as in RISC
OS's Filer. Iconised windows sit on the iconbar with their title.

## The command line and the star commands

RISC OS's command line is the **star command** line: every command starts
with a `*`, which is also its prompt. The star goes back to the BBC Micro,
where `*` in front of a line in BBC BASIC handed it to the operating
system; RISC OS kept it. Behind each command is a module in ROM or a
program (the Filer brings `*Filer_OpenDir`, for instance). Case does not
matter.

RISC Legacy brings both ways in:

- **F12** — the command line along the bottom of the screen, white on
  black, as RISC OS's F12 shows it;
- **Ctrl+F12** — a **Task Window**, the command line as an ordinary
  window, black on white.

Underneath is an ordinary bash: words that start with `*` are star
commands. As at RISC OS's `*` prompt, the star can be left out where bash
has no command of that name — `Cat`, `Dir`, `Ex`, `Help` —, while the
lower-case `cat` and `dir` stay Unix's. Everything else works as always.

| Star command | RISC OS | here |
|---|---|---|
| `*Cat [dir]` | list a directory | `ls -C` |
| `*Ex [dir]` | list with details | `ls -l` |
| `*Dir <dir>` | change directory | `cd` |
| `*Up`, `*Back` | parent / previous directory | `cd ..`, `cd -` |
| `*CDir <name>` | create a directory | `mkdir -p` |
| `*Copy a b` | copy | `cp -ri` (asks first) |
| `*Rename a b` | rename | `mv -i` |
| `*Delete <file>` | delete a file | `rm -i` |
| `*Wipe <obj>` | delete, also directories | `rm -rI` |
| `*Type <file>` | show a text file | `cat` |
| `*Run <prog>` | run a program | started detached |
| `*Filer_OpenDir [dir]` | open a Filer window | the file manager |
| `*Free` | free space | `df -h` |
| `*Time` | date and time | `date` |
| `*Modules` | loaded modules | the kernel's modules (`lsmod`) |
| `*Help [cmd]` | help | the list, or the command's manual |
| `*Desktop` | back to the desktop | closes the window |

An unknown star command answers `File '…' not found`, as RISC OS does.
When another program has F12 (Yakuake, for instance), install.sh leaves
it alone and says so; the command line is then in the menu.

## Install

```bash
./install.sh --apply classic --layout   # or 4, 2026, 2026-dark, pi, iyonix, acorn, graphite
```

`--apply` switches to a variant and sets up the handling above; `--layout`
also replaces the panels with the iconbar. Every setting it changes is
written down first; `./uninstall.sh` puts them back. Kvantum is needed for
the programs' style (package `kvantum`). The day/night follower uses the
systemd user manager; without it (OpenRC, runit) the switch changes
everything but the programs' Kvantum style.

Design notes for developers: [DESIGN.md](DESIGN.md).
