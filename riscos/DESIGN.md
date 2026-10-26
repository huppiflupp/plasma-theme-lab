# RISC Legacy — design notes

RISC OS (Acorn, 1987–today) for Plasma 6: RISC OS 3 and 4 as close as the
sources and screenshots allow, then the same desktop taken on to 2026, light
and dark. Working name; the theme shares no files with CDE/, os2-warp/ or
nt-legacy/ (the repository's CLAUDE.md).

## 1. Sources

- **RISC OS source code** (Apache 2.0 since 2018, RISC OS Open Ltd;
  upstream gitlab.riscosopen.org, mirrored at
  github.com/TimothyEBaldwin/RISC_OS_Linux_Source). The Wimp's tool sprites
  are in `RiscOS/Sources/Desktop/Wimp/Resources/<country>/<machine>/Tools`:
  `RO400` (RISC OS 4), `Morris4`/`Ursula`/`Iyonix`/`Sovereign` (one set,
  the RISC PC/A7000 line), `Raspberry` (RISC OS 5, 8-bit sprites that expect
  a palette not in the file), `Lazarus`/`NC2` (the Network Computer), and
  `Germany/Ursula/Tools2D` (RISC OS 2/3.0's flat tools).
  `tools/rospr.py` reads the sprite format (1–32 bpp, old and new mode
  words, 1-bit and alpha masks); `vendor/riscos-open/` holds the decoded
  RO400 and Tools2D sets with the licence.
- **Screenshots** (the user's, `~/Downloads/RiscOS`, 25.10.2026; not in the
  repository): RISC OS 3.x configuration windows and the task manager
  (bitmap system font), RISC OS 4 with the stone texture and Homerton,
  RISC OS 5 / RISC OS Pi on the green raspberry backdrop, a themed desktop.

## 2. Colours

The Wimp's sixteen desktop colours (RISC OS 3 Style Guide; the same values
in the source's default palette):

| # | colour | use |
|---|---|---|
| 0 | `#ffffff` | white: fields, light edge |
| 1 | `#dddddd` | window background, iconbar, unfocused title (RO3) |
| 2 | `#bbbbbb` | unfocused title under RO4's texture, groove |
| 3 | `#999999` | scroll well |
| 4 | `#777777` | dark edge, desktop |
| 5–6 | `#555555`, `#333333` | text 2, complementary |
| 7 | `#000000` | lines, text, menu highlight |
| 8 | `#004499` | dark blue: list selection, accent (see below) |
| 9 | `#eeee00` | yellow: RO4's pressed tools |
| 10, 13 | `#00cc00`, `#558800` | greens |
| 11 | `#dd0000` | red: radio dot |
| 12 | `#eeeebb` | cream: title of the window with the input focus |
| 14, 15 | `#ffbb00`, `#00bbff` | orange, light blue |

Measured in the screenshots: the work area is exactly `#dddddd` (RO3: 55 %
of all pixels in the configuration screenshot), lines `#000000`, edges
`#ffffff` and `#bbbbbb`.

**Selection.** RISC OS highlights menu entries black with white text, and
the Kvantum style keeps that (`menu_selection`). Plasma's selection colour
is also the accent, and Breeze's folder icons take the accent on: with
black, every folder was black (VM, 25.10.2026). Lists therefore select in
colour 8, the Wimp's dark blue, and Kvantum draws the list selection half
way to the surface, because views without the focus (Dolphin's places)
write the selected row in black.

**2026** keeps grey and cream, warmer (`#e9e9e4`, cream `#f1e7b4`), the
accent a brighter dark blue `#1f5fbf`. **Dark** turns the cream into brass
(`#6a5d2e` with `#f6efc8` text), so the window with the focus still carries
RISC OS's colour.

## 3. Window frame

RISC OS windows have no sizing border: one black line round the window and
between the tools; the size tool sits in the corner where the scroll bars
meet (the program's, not the frame's). In the title row, left to right:

`Back` · `Close` · title bar (title centred) · `Iconise` · `Toggle size`

Tools are 20 × 20 pixels at 90 dpi plus the black line (the sprites'
"22" sets, square pixels). The decoration draws 20 px, or 40 px from a
title font of about 16 px (setting "Tool size").

KWin has no "send to back" button; Back is "keep below" (`B`), the nearest
there is. Button order `BX` / `IA` (install.sh writes it; Plasma's global
theme does not).

**The title bar is texture over colour.** RO4's `tbarmidt`/`tbarmidb`
sprites (upper and lower half, 128 × 10, tiled) are mostly transparent:
where they are, the Wimp's title colour shows, colour 12 for the focused
window. So the decoration paints the colour scheme's title colour and the
sprite over it, which is RISC OS's own mechanism; RO3 is the same without
specks.

`tools/toolart.py` makes the pictures per variant:

- **classic** — drawn: grey face, white/grey bevel, glyphs engraved (dark
  line, white edge below right); pressed: bevel inverted, glyph a pixel
  down-right.
- **select** — RO400's sprites unchanged (pressed: yellow glyph).
- **modern / dark** — drawn at 8× and scaled: rounded tools, soft bevel,
  2.2 px glyphs, pressed glyph in RISC OS yellow; the title a soft sheen.

## 4. Typeface

Homerton (Acorn's Helvetica), Trinity (Times) and Corpus (Courier) are not
free. TeX Gyre Heros (GUST Font License, a Helvetica) stands in for
Homerton, at the same weight for titles and text, as RISC OS has it.

## 5. Iconbar

`iconbar/`, a plasmoid along the bottom of the screen, full width:

- left: the filing systems with their names below — Discs (`/`), Home,
  mounted media (`/run/media/<user>`), and Apps, which opens the cascading
  application menu (copied from Warp Legacy's menu);
- right: the running programs, one icon per program (grouped), the program
  in front with a faint frame; Select brings forward or iconises, Adjust
  (middle button) opens another window;
- the clock in a sunken white field (`2:23pm` with clockStyle=riscos, the
  locale's time by default), and the task manager icon;
- Plasma's system tray after the iconbar (notifications need a tray).

No hover effects (RISC OS has none); a pressed icon is drawn selected.

## 6. Programs (Kvantum)

`kvantum.py`, copied from Warp Legacy's: buttons with a black outline and
the white/grey bevel; the default action button in a cream ring (RISC OS
marks the button Return presses so); radio buttons with a red dot, as
RISC OS 3's configuration windows; progress bars in the Wimp's green.

## 8. Icons

The user's rules (25.10.2026): every icon, correctly scaled, no picture
twice. `iconkit/` draws every meaning Breeze has (2 577 at its largest sizes, its symlinks
counted as synonyms) anew as SVG in two colour worlds, after RISC OS's own
sprites: **ro4** (`RiscLegacy`, classic, 4 and the palettes: pale green
folders, grey, black outline, flat colour) and **ro5** (`RiscLegacy2026`,
2026 and Dark: blue folders, saturated colours, soft gradients). Each icon
exists large (scalable, 24 px and up) and small (16 and 22 px: thicker
lines, no text, less detail). `build_icons.py` reports coverage and every
pair of meanings that came out identical. The original 34 px sprites
(`vendor/riscos-open/Sprites-*`) remain the reference, no longer shipped
as icons: scaled up they were pixelated (the user, 25.10.2026).

## 9. Handling (RISC OS's way of working)

RISC OS (RISC OS Open's GUI comparison, the Style Guide): three buttons —
**Select** (left) chooses and opens, **Menu** (middle) opens a menu where
the pointer is (no menu bars; menus carry a title), **Adjust** (right) does
the complementary thing (move a window without raising it, close a Filer
window and open its parent). Applications are directories named `!Name`;
started, they put an icon on the iconbar: Select opens the window, Menu
the program's menu (Info, Choices, Quit). "Apps" on the iconbar is the
applications directory. Saving is dragging a file icon from a save box into
a Filer window. F12 opens the command line at the bottom of the screen,
`*` prompt and star commands (`*Cat`, `*Dir`, `*Run` …); Ctrl+F12 a Task
Window, the command line as an ordinary window.

What RISC Legacy takes over:

| RISC OS | here |
|---|---|
| Select / Menu / Adjust on iconbar icons | open or iconise / the program's menu with its name as title (New window, Iconise, Quit) / another window |
| Apps | Select and Menu: the cascading menu; Adjust: the applications as a Filer window (`applications:/`) |
| Menu on the desktop (Pinboard) | the desktop's menu (`ActionPlugins/0 MiddleButton`) |
| Menu on a title bar | the window's menu (`CommandActiveTitlebar2`) |
| Filer: double-click, a window per directory | `SingleClick=false`, Dolphin opens folders from outside in a new window |
| F12 command line | Konsole profile "RISC Legacy Command Line", white on black, laid along the bottom (third of the screen, no frame) by the KWin script `risclegacy-commandline` (a window rule came too late: Konsole sets its title after mapping) |
| Ctrl+F12 Task Window | Konsole profile "RISC Legacy Task Window", black on white; Plasma's "show desktop dashboard" gives Ctrl+F12 up |
| star commands | `shell/starrc` on bash: only words with `*` are RISC OS commands (`*Cat` lists, `cat` stays Unix's), as aliases so a file named like a command is not globbed |

Not taken over: saving by dragging (every program's own save dialog
would have to take part) and Menu inside other programs' windows (their
own middle-button use). install.sh records every setting it changes;
uninstall.sh restores them.

## 7. Open

- RO4's texture on the iconbar and the window backgrounds (Kvantum can tile
  a picture), the Pinboard backdrop.
- Menus with a title bar, as RISC OS's.
- An icon set (RISC OS's sprites are in the sources too, `Sprites22`).
- More palettes.

## 10. Backdrops, day and night

Every backdrop is a pair (`wallpapers/<stem>.jpg` and `<stem>-dark.jpg`),
shipped as one wallpaper package with `images/` and `images_dark/`: Plasma
shows the night half under a dark colour scheme. The pairs come from
`tools/gen-wallpapers.py` (Krea-2 on ai395): one half from a prompt, the
other from it — a stone only graded into the other light (the model would
invent new veins), a scene graded and then worked over by the model at low
denoise (the light in the sky), so the switch changes the light, not the
place. Quiet surfaces only: the granite of 0.1 was too busy.

Plasma's day/night switching swaps global themes; `install.sh --apply`
sets the variant and its partner (`DefaultLightLookAndFeel`,
`DefaultDarkLookAndFeel`): 2026 ↔ 2026 Dark, Graphite at night for the
other light variants, Classic by day for Graphite. The global themes
carry no `[Wallpaper]`, so a switch keeps the desktop's picture. The
follower (`shell/follow`, started by `risclegacy-follow.path` on every
change of kdeglobals) puts in what the global theme leaves out: Kvantum,
the frame, icons, Plasma style.

Contrast: `tools/contrast-sheet.py` lays the desktop icons on every
picture and measures how much of each icon's outline ring disappears.
Night pictures keep the band where the icons sit above ~0.045 relative
luminance; icons that were bare lines (network, shutdown) got bodies.
