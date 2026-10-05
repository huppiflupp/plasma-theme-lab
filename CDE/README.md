# CDE Copper

A contemporary CDE/Motif workstation theme for KDE Plasma 6.

![CDE Copper in the Fedora lab VM](screenshots/desktop-arranged-1920.png)

The handoff's teal and copper palette meets a more traditional CDE silhouette:
a compact bottom front console, mwm window frames, square Motif controls,
hard bevels and original vector workstation icons. Copper identifies the active
window, selected workspace and focused controls. The desktop stays quiet teal,
or takes any of CDE's own 37 palettes and backdrops.

The console, its settings, the start-up, lock and logout screens speak
German where the system does (gettext domain `cde-copper`, `po/`); other
languages can be added as `po/<language>.po`.

## Included

- KDE color scheme and 38 Plasma surface SVGs.
- Window frame after mwm/dtwm, as a QML Aurorae decoration: raised resize frame
  with separate corner handles, title bar of individually shadowed parts (window
  menu bar, title, minimize, maximize, close), title and client together in a
  sunken well. Its colours come from the active
  colour scheme and its shadows from Motif's own shading rule, so it follows
  every palette. Title-bar height is adjustable; the buttons scale with it.
  A short hard shadow at the right and bottom (switchable in the console's
  Style page or the decoration's settings); inactive frames have a flatter
  bevel.
- Kvantum widget style with Motif controls: bevelled buttons, sunken fields,
  diamond radio buttons, copper focus frame, default button and selection,
  bevelled scrollbars with arrows, attached tabs and hard-edged menus.
- IBM Plex Sans Condensed for the interface and titles (semibold), IBM Plex
  Mono for Konsole and fixed-width text; both ship with the theme (SIL OFL).
- The front console (one per screen, at any screen edge): clock with a month
  calendar and the day's appointments, configurable launcher tiles with
  subpanels, an Applications menu with cascading categories (also on the
  Meta key), the browser's
  bookmarks, the editor's (or LibreOffice's) recently opened files, a Mail
  subpanel (new message, appointments, address book), Places, System and Help
  subpanels, four-workspace switcher (each button in a colour of the palette,
  as in CDE), window task strip (several windows of
  one application as one button, "3× Konsole"), volume
  control, and a launcher-wide block: its arrow strip opens the hidden tray
  icons, below it four square buttons for console settings, lock screen,
  show desktop and a load meter (processor and memory from Plasma's own
  sensors; a click opens the system monitor). The Plasma system tray
  stays in the console's panel for notifications, but by default it is out of
  sight: its entries open from the console's button; the tray's own volume
  icon is left out, since the console has one. By default the console stands
  by itself; the panel's own frame around it can be switched on.
- CDE's 37 colour palettes, shaded with Motif's algorithm, and CDE's 25 desktop
  backdrops, coloured with the chosen palette.
- A window arrangement around the console: terminals left and right, the main
  window in the middle above the console (Meta+Ctrl+C), and sets of three,
  four or seven terminals opened in their places from the Terminal subpanel.
- Mouse cursors after the X11 cursor font of CDE and Motif (arrow, I-beam,
  wristwatch, hand, crosshair, resize arrows...), 28 drawings under 99 names,
  pixel-exact at 24, 32, 48 and 64 px: slim black shapes on a coloured rim
  (copper, the palette's accent, white or any colour, chosen in the console's
  Style page) with a soft shadow.
- Original SVG icon artwork, 248 drawings under 652 names (applications,
  menu categories, actions, documents, devices, places, battery, network and
  other status icons), with no embedded raster images; the 59 most visible
  also as pixel versions for 16 and 22 px. Drawn in Copper's colours and
  recoloured with every palette, as CDE's icons took the palette's dynamic
  colours: outline, body, paper, dark accent and copper accent come from
  the palette, with a contrast floor against the console face and the text
  fields (on dark ones the bodies turn light, the outline stays dark).
  Monochrome "-symbolic" icons are coloured by Plasma itself.
- Konsole profile and color scheme, global-theme bundle with a Motif start-up
  screen, and teal wallpaper. A second global theme, CDE Night (CDE's
  NorthernSky palette), is set as the night theme of Plasma's day/night
  switching (Quick Settings), CDE Copper as the day theme; the console
  follows each switch with its controls, surfaces and desktop colour.
- CDE's lock screen: a Motif dialog on the palette's backdrop. Plasma 6 takes
  the lock screen from its shell package, so it comes as a shell package of
  its own (org.cde.copper.shell) that takes everything else from Plasma's;
  applying the theme switches to it, moving the panel and desktop
  configuration along (Style page › Lock screen switches back). It talks to
  the authenticator as Plasma's lock screen does (one entry per prompt, a
  short wait after a failure, fingerprint readers left alone). Global
  themes other than CDE's, applied with their layout while this shell
  runs, get Plasma's default panel from the shell's own default layout.
  A small systemd path unit (cde-copper-theme.path, set up by apply and
  removed by uninstall) lets the shell follow the global theme: switching
  to another global theme goes back to Plasma's shell and, if the layout
  was replaced, loads that theme's own layout there (NT Legacy's taskbar,
  Breeze's panel); switching back to CDE returns to CDE's shell.
- A GTK 3 and GTK 4 theme (CDECopper) from the same palette, so GTK
  programs such as Firefox or PCManFM get the Motif controls too; it is
  rebuilt with every palette. Libadwaita programs ignore GTK themes and only
  take Plasma's colours.
- System parts, installed apart with `sudo python3 system.py install` (and
  undone with `uninstall`): a Plymouth boot splash (a Motif dialog with a
  meter on the backdrop, the passphrase prompt of an encrypted disk in it)
  and a GRUB theme (the menu in a Motif window with a copper title bar, on
  one of the theme's pictures or the backdrop). Plymouth needs its script
  module (Fedora: plymouth-plugin-script); under Secure Boot GRUB loads no
  font files, so the menu then uses GRUB's own Unifont. Both take the
  colours of the palette you applied (`--palette` picks another); after
  switching palettes, run `install` again. GRUB keeps its graphics mode
  for the kernel (gfxpayload=keep), and its console, which it shows while
  loading the system, sits in the menu window instead of a black box over
  the screen (in the window colour where GRUB can colour it, black under
  Secure Boot).
- CDE's logout confirmation: a Motif dialog with lock, sleep, hibernate,
  restart, shut down and log out, the action it was called for as default
  button and a countdown, in the palette's colours.
- User-only installer, ownership manifest and configuration rollback.

## Install

Requires Plasma 6 / Qt 6, Aurorae, Python 3, `kbuildsycoca6`, Plasma apply
utilities, `qdbus-qt6` or `qdbus6`, and the Plasma 5 Support executable data
engine. The Motif controls need the Kvantum style engine (package `kvantum`);
without it the installer falls back to the built-in Qt Windows style and says
so. The fonts are installed per user and need `fc-cache`. Network/audio status uses NetworkManager's
`nmcli` and WirePlumber's `wpctl`. Launchers start `gtk-launch` or `kstart`;
appointments in the calendar come from KOrganizer/Akonadi when installed.

The release archive contains ready-built assets. From its extracted directory:

```sh
bash install.sh --dry-run
bash install.sh
bash apply.sh --panel
```

Log out and back in after applying. `--panel` explicitly replaces the current
panel layout with one console per screen (the system tray beside the first);
the installer backs up the previous layout first. Without that flag, your
current panels stay in place. The front console can also be added as a widget
through Plasma's normal widget picker.

### CDE palettes and backdrops

The 37 palettes of CDE are listed in **System Settings › Colours** as
"CDE Alpine" … "CDE Wheat", beside "CDE Copper". Choosing one there is enough:
the console notices the new colours and brings the rest along, the Plasma
surfaces, the Kvantum controls and the backdrop. Applications that are already
open take the new controls when restarted; a notification says so.

The **style manager** does the same from the console, after CDE's dtstyle:
System subpanel › Style Manager (or the console's settings › Style) shows
every palette as colour stripes and every backdrop pattern, and the style of
progress bars (outlined, floating in the groove, or slim); choosing and
pressing the settings dialog's Apply or OK applies them. In System Settings ›
Application Style the controls are listed as "CDE".

**XFile**, a Motif file manager (fastestcode.org, MIT licence), is the closest
thing to CDE's own dtfile on a current system: Motif widgets, bevels shaded
from the background like CDE's, an icon view and a path field. It is not
packaged by the distributions; built from source (it needs only X and Motif),
it joins in by itself: with every palette change the tool writes its X
resources (`~/XFile`: the palette's window, field and selection colours,
IBM Plex, the desktop's terminal, `xdg-open` for files) and, if the
installation brought no menu entry, adds one. A `~/XFile` of your own is left
alone (the theme marks its file in the first line). In the console, choose
"XFile (Motif, as CDE's dtfile)" for the Files tile; its Places subpanel then
opens in XFile too (the trash stays the desktop's, XFile has none).

CDE's 25 backdrops are a wallpaper type of their own: desktop settings ›
Wallpaper type **CDE Backdrop**, a grid of the patterns in the palette's
colours, a pixel size for 200 % screens and the colour behind the pattern.
They are tiled pixel for pixel; Plasma's picture wallpaper would scale the
small patterns up into a blur. As in CDE, every workspace can have a backdrop
of its own ("A backdrop for each workspace"): Plasma itself knows wallpapers
per screen and activity only, so the wallpaper follows the current virtual
desktop by itself.

28 picture wallpapers come along in 3840×2160, each with a dark version that
Plasma shows on its own while a dark colour scheme is active:

- **Copper Altai, Canopée, Cluster, Fluss, Kaskade**: low-poly landscapes after
  Plasma's own Altai, Canopée, Cluster, Flow and Cascade, in Copper's teal and copper.
- **CDE Monolith, Polarlicht, Mesa, Riff, Origami, Bauhaus, Weinberg, Orbit**:
  one CDE palette each, from Default to Neptune.
- **CDE Chipstadt, CAD, Molekül, Sequenz, Druckvorstufe, Schnittplatz, MRT,
  Mischpult, VLSI, Strömung**: what CDE workstations were used for in the 1990s.
- **CDE Kristall, Marmor, Düne**: abstract, after the most popular KDE Store wallpapers.
- **CDE Aquarell, Panorama**: late-1990s software box illustration.

All but Strömung are AI-generated decoration without logos or lettering;
Strömung is a computed potential flow around an airfoil.
`wallpapers/README.md` records how each was made.

They are backdrops too: the console's Style page and the "CDE Backdrop"
wallpaper list them after the patterns, the ones painted for the chosen
palette first, and "A backdrop for each workspace" takes pictures as well as
patterns (`--backdrop picture:origami` from a shell). Under a dark palette
the dark version is shown.

The same from a shell:

```sh
python3 manage.py palettes                        # list both
bash apply.sh --palette Broica                    # one of CDE's palettes
bash apply.sh --palette Copper --backdrop Pebbles
bash apply.sh --backdrop none                     # plain palette colour again
python3 ~/.local/share/cde-copper/tool/manage.py palette --palette Lilac --backdrop WaterDrops
```

The last form uses the copy of the tool that the installer puts into the
profile; it needs no extracted archive.

A palette recolours everything: colour scheme, Plasma surfaces, Kvantum
controls, window frames, the console (CDE colour set 8) and, as in CDE, the
backdrop (set 3). Its Plasma surfaces and Kvantum style are generated when it
is applied and replace those of the previously applied palette. Text colours
are chosen for contrast: every text/background pair of every palette reaches
at least 4.5:1, where Motif's fixed threshold would put white on several
mid-tone surfaces.

## Configure the console

Right-click the console and choose its settings.

- **Front Console**: bottom, top, left or right screen edge (upright at the
  sides, running the full screen height, subpanels opening towards the middle);
  Always Visible, Auto-hide / Edge Reveal, or Dodge Windows; window list per
  screen; floating with a gap or sitting on the screen edge; one console
  for all screens (default) or one on every screen; whether the
  tray's volume icon is left to the console; hard
  contrast (pure black text, white on dark surfaces, labels in semibold);
  label; size
  (75–200 %, tiles, icons and text scale together).
- **Launchers**: the tiles left and right of the workspace switch. Each tile has
  a label, an icon, a program and the subpanel its arrow opens (Applications,
  Places, System, Help, Mail, Bookmarks, Recent files). Programs are
  "Default web browser", "Default mail client", "Default file manager",
  PCManFM (the Files tile's default: PCManFM-Qt takes the Motif controls,
  else the GTK PCManFM, else the desktop's file manager), XFile,
  "Default text editor", terminal, calendar and so on, which follow
  System Settings › Default Applications, or an installed application picked
  from a list, or any command. A tick or a warning shows whether the program is
  installed. When the default is missing, a tile falls back to common
  alternatives (for the browser: Firefox, Chromium, Falkon, Konqueror, ...); if
  nothing is there, it shows a notification instead of failing silently.
- **Clock and Calendar**: clicking the clock shows a month view with the day's
  events, or starts the calendar application right away; which application
  ("@calendar": Merkuro or KOrganizer) and which event sources (appointments,
  holidays, astronomical events, alternate calendars).

**Bookmarks** (the Web tile's arrow) come from the browser the tile starts:
Firefox and LibreWolf, Chromium, Chrome, Brave, Vivaldi, Edge, Falkon and
Konqueror; the toolbar first. **Recent files** (the Editor tile's arrow) are the
files that tile's program opened last, collected from Plasma's activity
database (KDE programs such as Kate and KWrite), `recently-used.xbel` (GTK
programs) and LibreOffice's own list, split by module: a Writer tile shows text
documents, a Calc tile spreadsheets. Choosing another program in the settings
proposes the matching subpanel.

The volume button: click for a slider, Mute and the audio settings; the mouse
wheel changes the volume directly.

![The clock displays](screenshots/clock-faces-200.png)

**Clock and Calendar** also chooses the clock display: digital, seven-segment
(unlit segments faintly visible, both that and a black edge round the lit
ones can be switched)
or analog with one of four dials: CDE (round,
after CDE's own front-panel clock), Motif (a square sunken well), Roman
numerals, or plain marks on the tile. Seconds can be shown on every display.
The dial takes the text-field colour, hands and digits the text colour, the
second hand and lit segments the selection colour, so every palette dresses
the clock to match. All sizes follow the tile, so the clock fits at 75 % and
in the upright console.

Subpanels and menus accept Tab, Enter, Space, the arrow keys and Escape. The
task strip scrolls when many windows are open. Windows of one application share
a button ("3× Konsole", the titles in its tooltip); each click brings the next
of them forward. General › "Group windows of one application" turns this off.

### Arrange windows around the console

Meta+Ctrl+C, the System subpanel's "Arrange Windows", or a tile with the
program "Arrange windows around the console": terminals take the space left
and right of the console down to the bottom of the screen, the active window
(or a web browser) stands in the middle above the console. Other windows stay
where they are.

### Terminal sets

The arrow above the Terminal tile opens a new terminal or a whole set of
Konsole windows, each put in its place as it appears:

- **Three Terminals Around the Console**: left and right of the console down
  to the bottom edge, and the middle above the console, on the console's
  screen.
- **Four Terminals on the Other Screen**: one window across the top half,
  split into two terminals side by side, and two quarters below it. With one
  screen, on that screen above the console.
- **Seven Terminals on Both Screens**: both sets at once (two screens only).

The console starts the windows and the arrangement script places the next
terminal windows to appear, in the order they were started; it waits 20
seconds for them. The sets need Konsole (the split is a Konsole layout).

### File manager

Dolphin stays the default: it follows the Kvantum Motif controls and the icon
set, and has the most features. For a look closer to CDE's own dtfile,
**PCManFM-Qt** (package `pcmanfm-qt`) is the recommended alternative: a menu
bar, a plain single-pane window, and it takes the Motif controls, colours and
icons completely. Make it the default and the console's Files tile, Places and
Trash follow:

```sh
xdg-mime default pcmanfm-qt.desktop inode/directory
```

Xfe (`xfe`) looks even more like a 1990s workstation, but brings its own
toolkit and runs through XWayland, so it ignores the widget style and palette.

### Window frame

Two settings: the title-bar height (0 follows the title font, about 23 px with
IBM Plex at 10 pt; from 8 px, the buttons and the title text follow it) and whether the whole frame takes the title colour (CDE) or
only the title bar. The decoration ships a settings page for System Settings ›
Window Decorations; the same values can be set directly:

```sh
kwriteconfig6 --file auroraerc --group kwin4_decoration_qml_cdecopper --key titleHeight 32
kwriteconfig6 --file auroraerc --group kwin4_decoration_qml_cdecopper --key coloredBorder false
qdbus6 org.kde.KWin /KWin reconfigure
```

The frame width follows "Border size" in System Settings.

## Restore

```sh
bash uninstall.sh
```

This stops/restarts Plasma, restores the configuration saved before the first
installation, then removes only manifest-owned assets, including a generated
palette. Log out and back in to fully reload the original decoration and
application style. Backups remain in `~/.local/share/cde-copper-install/`;
later install cycles archive them beside it. Rollback restores whole saved
config files, including changes made since the installation. Inspect that
backup before uninstalling a long-lived installation.

An existing unowned `CDECopper` theme is never overwritten. Installation refuses
that collision. No root privileges are used for installation or removal.
Upgrading from 0.1.0 replaces the SVG window decoration with the QML one.

## Develop

All project-specific work lives here. The supplied handoff remains unchanged.

```sh
python3 build.py
python3 tests/verify.py
```

The SVG generators are CDE Copper's own copies under `tools/`; the build never
reaches outside this directory, and the release archive carries the same copies.
The theme shares a repository with NT Legacy, but the two are kept apart on
purpose: a change to one must not alter the other (see `tools/README.md`).

| Where | What |
|---|---|
| `build.py` | palette, colour scheme, Plasma surfaces, packages |
| `kvantum.py` | the Kvantum SVG and its configuration |
| `icons.py` | original icon geometry and aliases |
| `palettes.py`, `palettes/` | CDE palettes and Motif's shading |
| `backdrops.py`, `backdrops/` | CDE backdrops, coloured per palette |
| `decoration/` | the QML window frame |
| `backdrop/` | the "CDE Backdrop" wallpaper type |
| `wallpapers/` | the 28 picture wallpapers, light and dark, and the scripts that made them |
| `frontpanel/` | the console plasmoid; `contents/code/menus.py` reads bookmarks and recent files |
| `arrange/` | the KWin script for the window arrangement |
| `fonts/` | IBM Plex |

Generated assets are under `build/`. All testing was performed in the
project's `plasma-lab` VM. See [TESTING.md](TESTING.md).

## Scope

This is version 0.8.4. The application style is a Kvantum theme, not a
compiled Qt style, so it needs Kvantum at run time. Third-party applications
can supply their own controls or client-side decorations. The icon set covers
the installed applications, the menu categories and the common action,
document, device and status names; less common names fall back to Breeze and
then hicolor. A login screen (SDDM) is outside this release. Native Plasma manages panel hiding and
screen-edge reveal; there is no separate retractable handle.

Popups from the console open at the size they first appear with: under Wayland
KWin does not move or resize them afterwards, so the Applications menu opens at
the full size of both of its levels and leaves the unused part transparent.

One console per screen is set up by `--panel`, but multiple physical monitors
have not been validated (the test VM shows only one output). Very narrow
logical screens below 800 px have not been validated either.

## Where it falls short of the specification

Measured against the handoff (`CDE-Plasma-2027-Handoff/DESIGN-SPEC.md` and
`IMPLEMENTATION-GUIDE.md`). Some of these are decisions, the rest is not done.

Decided differently:

- **Front panel (§8).** The specification asks for a floating panel at the top,
  88–94 % of the screen wide, with a second row of Applications / Places /
  System / Help menus. CDE Copper keeps the compact classic console of CDE,
  centred and only as wide as its tiles, by choice of its user; its menus hang
  off the tiles' arrows. The console can sit at any edge.
- **Title bar (§5).** The specification gives 28–32 px title bars and 22–24 px
  buttons. On request the default is the title font + 6 px, about 23 px, with
  buttons of the same size; 28–32 px can be set in the decoration's settings.
- **Copper share (§2).** With "Colour the whole frame like the title bar" (on
  by default, as CDE does) the active window's frame is copper all round; for
  small windows this can exceed the 10–15 % the specification allows. Switch it
  off for copper title bars only. Not measured.

Not reached:

- **Icons (§7).** The drawings and the monochrome "-symbolic" set cover the
  common names, but Breeze knows several thousand: rarer ones (many
  application-specific actions and document types) still fall back to
  Breeze.
- **Hidden panel (§8).** The grip edge is KWin's edge mark, drawn by the
  theme as a raised bar in the palette's active colour: it shows while the
  pointer nears the edge, not all the time. Showing and hiding use
  Plasma's timing, not the 140–180 ms of the specification.
- **Keyboard and screen readers (§8, acceptance).** Tiles and menus carry
  accessible names and keys work in the subpanels, but full keyboard operation
  of auto-hide and of the Applications menu has not been verified, nor has a
  screen reader been used.
- **Theme coverage (phase 3).** No login screen theme yet (Fedora 44 uses
  Plasma's new login manager, not SDDM);
  notifications and calendar follow only through the Plasma surfaces.
- **Test matrix.** 150 % and 200 % scaling were checked for 0.1 only, not for
  the QML window frame, the console and the popups that came later. X11 was
  not tested; Wayland is.
- **"Plasma starts without QML errors" (acceptance).** Plasma starts, but its
  log shows warnings from the console's settings pages (Plasma offers every
  page every setting) and binding-loop warnings from Qt's menu items.

## Credits

Source and original artwork: GPL-2.0-or-later. IBM Plex Sans Condensed and IBM
Plex Mono are copyright IBM Corp. under the SIL Open Font License 1.1
(`fonts/IBMPlex/LICENSE-OFL.txt`). The CDE palettes (`palettes/cde/`) are part
of CDE, LGPL-2.0-or-later; the CDE backdrops (`backdrops/cde/`) and the
pictures made from them are CC BY-SA 3.0, attribution "The Open Group". The
shading follows `CalculateColorsRGB` from Motif's `lib/Xm/Color.c`
(LGPL-2.1-or-later). Plasma SVG generation reuses the lab's tools by
huppiflupp. CDE/Motif is the design inspiration; no CDE or Microsoft icon files
are copied. The supplied reference images are not installed or included in
the release.

Implementation follows KDE's [panel scripting API](https://develop.kde.org/docs/plasma/scripting/api/),
KWin's scripting and Aurorae QML APIs, and the QML API metadata installed in
the test VM.
