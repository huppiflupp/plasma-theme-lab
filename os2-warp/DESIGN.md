# OS/2 Warp 4 for Plasma — design specification

A Plasma 6 theme after IBM OS/2 Warp 4 (1996), extended by the two panels
that Stardock Object Desktop added on many Warp 4 machines. Everything here
is measured from the reference screenshots in `reference/` (see the table at
the end); where a screenshot does not show something, the spec says so
instead of guessing.

The theme is separate from `CDE/` and `nt-legacy/` (see the repository's
CLAUDE.md): code taken from CDE Copper is **copied** into `os2-warp/` and
adapted here, never referenced.

## 1. Licence and names

The theme goes to the KDE Store, so it ships nothing of IBM's or Stardock's:

- **No original assets.** Icons, the Warp 4 "swirl" wallpaper, the OS/2 Warp
  logo and the WarpSans font are copyrighted. We draw our own in the same
  style (§9) and use a free font (§2).
- **Names.** "OS/2" and "Warp" are IBM trademarks, "Object Desktop" is
  Stardock's. The working directory is `os2-warp/`; the published name is
  still open (see §10). Inside the theme the panels get generic names:
  *Warp Bar* (WarpCenter), *LaunchPad*, *Control Strip* (Object Desktop's
  right-hand panel), *Tab Launcher* (Tab LaunchPad).

## 2. Look: colours, edges, type

### Palette (Warp 4 default scheme)

| Role | Colour | Source |
|---|---|---|
| Surface (dialogs, panels, buttons) | `#cccccc` | WarpCenter `#cecece`, Warp 3 `#d7d7d7` (JPEG noise in the Warp 4 shot) |
| Light edge | `#ffffff` | |
| Dark edge | `#808080` | |
| Outer dark edge | `#000000` | buttons only, see below |
| Window background (lists, entry fields) | `#ffffff` | Warp 4 shows a slightly warm `#fafff9`, JPEG |
| Active title bar | `#2400a8` | Warp 4 measured `#2301a4` (mean over the window list title); Warp 3 `#0000a0` |
| Active title text | `#ffffff` | |
| Inactive title bar | `#808080`, text `#cccccc` | Tab LaunchPad title in the Warp 4 shot |
| Selection in lists | `#808080`, text white | Warp 4 window list: grey bar behind the selected entry |
| Selection in menus | `#2400a8`, text white | WarpCenter menus |
| Desktop (no wallpaper) | `#00a0a0` | Warp 3 teal; Warp 4 default is the blue swirl |

Optional later: the Warp 3 teal desktop and the Warp 4 swirl as two
wallpapers of the same theme.

### Edges

OS/2 does **not** use CDE's computed Motif shading: the edges are fixed
colours, independent of the surface.

- **Raised button**: 1 px outer edge (white top/left, black bottom/right),
  inside it 1 px (surface top/left, `#808080` bottom/right). Pressed: the
  two inverted, contents 1 px down and right.
- **Default button** (LaunchPad, "Run" in the window list): an extra black
  1 px frame around it.
- **Sunken field** (entry fields, lists, the gauges of the Control Strip):
  `#808080` top/left, white bottom/right, inside it 1 px black top/left.
- **Panel/frame**: 1 px white top/left, 1 px `#808080` bottom/right
  (thinner than a button).

So `CDE/frontpanel/contents/ui/motif.js` and `Bevel.qml` are **not** taken
over; `os2-warp/` gets a `Bevel.qml` of its own with the fixed rule above.

### Type

WarpSans (Warp 4) and Helv (Warp 3) are narrow, bitmap-like sans faces at
9 pt. Candidates under a free licence, to be compared in the VM: a narrow
sans with clear hinting at 9–10 pt. Decide by screenshot, not by name.
Bold text appears only in the window title (Warp 4) and the active tab.

Menus and buttons underline the accelerator letter ("_Sperren",
"_Fensterliste").

## 3. Window decoration

From the Warp 4 window list (window list reference, 800×600):

```
┌─────────────────────────────────────────────────────────┐
│ [▾] ███████ Window List ██████████████████  [×] [▫] [□] │
├─────────────────────────────────────────────────────────┤
```

- **Left**: the system menu button, a small icon of the program (Warp 4) or
  a horizontal bar (Warp 3). Click: window menu; double-click: close.
- **Title**: a blue bar that does *not* fill the whole frame, it is inset
  between the buttons with a 2 px surface gap; text left-aligned, bold, white.
- **Right**, in this order: **close (×)**, **minimise/hide (small square)**,
  **maximise (large square)**. Warp 4 puts the close button *left* of the
  other two — an OS/2 trait worth keeping.
- **Buttons**: square, raised (§2), about the title height, flat grey with
  a dark glyph; no hover colour.
- **Frame**: 4 px sizing border in the surface colour with a light outer
  and a dark inner line.
- Inactive window: title bar mid grey `#808080`, text light grey.

Implemented as an Aurorae theme (like NT Legacy), not as a QML decoration.

## 4. The Warp Bar (WarpCenter), top edge

From the WarpCenter reference (640×480):

- A **panel on the top edge**, full width, about 24 px high at 640×480
  (≈ 28 px at 96 dpi on a modern screen), surface grey, raised.
- From the left:
  1. **Desktop button** with the OS/2 Warp word mark (here: our own mark).
     Opens the **desktop menu**: the objects on the desktop (Assistance
     Center, Connections, OS/2 System, Programs …), separator, more entries.
     Folders cascade into submenus — down to the folders of the drives
     (`Drive C ▸ CID ▸ …`, `TCPIP ▸ SAMPLES ▸ ETC ▸`). This is the core of
     the WarpCenter and should work the same here: a cascading menu over
     the desktop folder and, below a separator, the mounted drives.
  2. **Window list** button: a menu of the open windows (Ctrl+click in the
     original opens a process list; optional).
  3. **Lock-up** (padlock).
  4. **Find** (torch).
  5. **Shut down** (computer with a red stroke).
  6. Then the **trays**: rows of program icons; a small button switches
     between several trays (Warp 4 has more than one).
  7. On the right a **status area** (not visible in the reference, cut off
     after "AM"): clock and date as text; in the original also CPU load,
     disk space and battery as small sunken displays.
- Menus: surface grey, entries with 16 px icon, highlight blue `#2400a8`
  with white text, submenu arrow ▸ on the right, separators as an etched
  line.

## 5. The LaunchPad, bottom centre

From the Warp 3 reference (640×480, German labels):

- A **floating panel**, centred above the bottom edge, surface grey with a
  panel frame (§2).
- **Left: two columns of text buttons**, two rows each:
  `Sperren | Suchen…` / `Systemabschluß… | Fensterliste`
  (English: Lock / Find… / Shut down… / Window list).
- **Right: large icon buttons** (about 32×32 icon in a 40×40 button), each
  with a **drawer button** above it: a narrow raised bar, with a small ▵
  when the drawer has content, empty when it has none.
- A **drawer** opens upwards above its button: a column of further icon
  buttons with their own close bar ▿ at the top.
- The LaunchPad can also be vertical and can carry the text buttons or not
  (OS/2 settings); for a start: horizontal, with text buttons.

This is the part closest to CDE Copper's front console (subpanels = drawers,
SessionButtons = the text buttons), and the place where most code is
copied (§8).

## 6. The Control Strip (Object Desktop), right edge

From the Warp 4 reference with Object Desktop, right edge, top to bottom:

1. **Virtual desktops**: one tile per desktop with a thumbnail of the
   desktop (wallpaper and window outlines), its number bottom right
   ("1.", "2." …). Under each tile a narrow bar, red under the current
   desktop, black under the others. Four desktops, stacked vertically.
2. **Launch list**: a column of buttons, each icon + label, left-aligned:
   Notes, Command Prompts, Information, Drives, OS/2 System, Programs,
   Desktop. Text is cut off at the edge ("Command Pror") — the strip has a
   fixed width (≈ 90 px at 800×600).
3. **Gauges**: one row per meter, label left, sunken bar right:
   `Swap: 40M` (red fill), `C: 5.5M`, `D: 5.9M` … (grey fill, the free part
   teal). Here: swap, and one row per mounted file system (free space).
4. **Digital clock**: black field, cyan seven-segment digits `1:28:33`.
   (CDE Copper's `SegmentDigits.qml` can be copied for this.)

## 7. The Tab Launcher (Tab LaunchPad), bottom left

From the Warp 4 reference with Object Desktop:

- A **normal window-like panel** with its own title bar (`Tab LaunchPad -
  Tab View`, inactive grey here), so it looks like a window but is a panel.
- A **row of tabs**: Tasks, Main, Applications, Utilities, Communications,
  Internet, Multimedia, Games, Miscellaneous. The active tab bold and
  joined to the page below.
- Below, a **row of icon buttons** (32×32 icons in square raised buttons,
  without labels) for the programs of the active tab. "Tasks" shows the
  open windows instead of launchers.
- Natural mapping: tabs = categories of the application menu, plus "Main"
  for the user's favourites and "Tasks" for the windows.
- A **drawer**, after Mac OS 9's Control Strip: a tab at its right end
  slides it out of the screen to the left and back, closed only the tab
  shows; the state is kept (`collapsed`). It is a panel of its own at the
  bottom left (top left when a taskbar runs along the bottom), above the
  windows without taking room from them, without panel background, its
  length following the drawer (length mode "custom" from 10 px).

## 8. What comes from CDE Copper

Copied into `os2-warp/` and adapted (with a note of the CDE commit it was
taken from), not referenced:

| From `CDE/frontpanel/contents/ui/` | For |
|---|---|
| `launch.js`, `windows.js` | starting programs, the launcher jumps to an open window (all panels) |
| `SectionPopup.qml` | LaunchPad drawers |
| `SessionButtons.qml` (the actions, not the look) | LaunchPad text buttons, Warp Bar lock/shut down |
| `WindowsPopup.qml`, `TaskMenu.qml` | window list, window menu |
| `Workspaces.qml` (logic) | Control Strip desktop tiles |
| `SegmentDigits.qml` | Control Strip clock |
| `AppMenu.qml`, `code/menus.py` | desktop menu, Tab Launcher categories |
| `TrayControl.qml`, `VolumePopup.qml`, `NetworkPopup.qml` | Warp Bar tray |

**Not** taken over: `motif.js`, `Bevel.qml` (other edge rule), `main.qml`
(other layout), the `cdecopperrc` mirror, the LLM cluster.

## 9a. The Neon variant

After the user's concept `reference/neon-2026.png` ("OS/2 Warp 2026",
Downloads/OS2): the same building blocks as the classic variant, at night.

| Role | Colour | Measured |
|---|---|---|
| Desktop | `#0a152e` | desktop between the windows |
| Window body, panels | `#0c1438` | window list body `#141749`, control panel `#091634` |
| Title bar | `#06123f` (active), `#0b1430` (inactive) | `#001246`; no separate coloured bar, the title sits on the frame |
| Light edge (top, left) | `#48cffe` cyan | the frame's bright line, x=128 |
| Dark edge (bottom, right) | `#7a4dff` violet | the glow shifts from cyan to violet towards the bottom right |
| Glow around frames | `#1f4fff`, fading out over ~8 px | |
| Text | `#e8f0ff`, secondary `#9fb4e0` | |
| Selection | `#1a6fe0`, text white | active workspace cell, active task |
| Accent text, meters | `#3ad0ff` | clock, CPU/RAM bars |
| Pink accent | `#ff4fd8` | bottom right corners of the frames, the streak under the title (Neon frame: top/left cyan, bottom/right cyan → violet → pink; the title line cyan → pink → violet, fading out) |

So OS/2's rule (light top left, dark bottom right) stays: the "light" is
cyan, the "dark" violet, and both glow. Buttons in the title bar are
outlined squares with white glyphs. The concept orders them `_ □ ×`;
Warp Legacy keeps OS/2's `× ▫ □` in both variants, so the variants differ
in colour only (the order is a KWin setting the user can change).

The concept also shows a bottom taskbar (Start, workspaces 1–4, tasks,
tray, clock) and a right-hand widget with clock and CPU/RAM/disk meters,
the Control Strip of §6 in neon. The IBM logo and the "OS/2 WARP 2026"
word mark in the concept are not taken over (§1).

Icons: glossy, glowing, blue-violet-cyan with orange accents, drawn for a
dark background. Our own set (plan step 7).

## 9. Icons and wallpaper

Our own drawings in the Warp 4 manner: 32×32 and 16×16, a limited palette
(the 16 VGA colours plus a few greys), hard pixel edges, light from the top
left, a black outline. Yellow folders, the "OS/2 System" computer, drives,
the shredder, the padlock, the torch. As SVG on a pixel grid, so they stay
crisp at 1× and scale at 2×.

Wallpaper: our own blue swirl in the manner of Warp 4 (generated), and the
plain teal of Warp 3.

## 10. Open questions for the user

- The published name (trademarks, §1).
- Warp 4 swirl or Warp 3 teal as the default.
- German or English labels by default (the reference shows both; Plasma's
  language decides, as with CDE Copper).

## References

| File | What it shows |
|---|---|
| `reference/warp4-objectdesktop.jpg` | Warp 4 with Object Desktop: window list, Control Strip, Tab LaunchPad (Britannica, 800×600) |
| `reference/warp4-warpcenter.png` | WarpCenter with the cascading desktop menu (toastytech.com, 640×480) |
| `reference/warp3-launchpad.png` | Warp 3 LaunchPad and windows, German (movq.de, 640×480) |
| `reference/os2-lockup-neon.gif` | OS/2 lock-up screen with neon tubes (gekk.info, 320×240) |
| `reference/neon-2026.png`, `classic-2026-a/b.png` | the user's "OS/2 Warp 2026" concepts (Downloads/OS2, 1536×1024) |

The screenshots are for measuring only: they are not in the repository
(`.gitignore`) or the theme package. `./fetch-reference.sh` fetches them.
