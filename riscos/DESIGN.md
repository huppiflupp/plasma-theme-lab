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

## 7. Open

- RO4's texture on the iconbar and the window backgrounds (Kvantum can tile
  a picture), the Pinboard backdrop.
- Menus with a title bar, as RISC OS's.
- An icon set (RISC OS's sprites are in the sources too, `Sprites22`).
- More palettes; generated backdrops.
