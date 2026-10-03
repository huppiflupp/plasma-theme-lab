# CDE Copper

A contemporary CDE/Motif workstation theme for KDE Plasma 6.

![CDE Copper in the Fedora lab VM](screenshots/desktop-arranged-1920.png)

The handoff's teal and copper palette meets a more traditional CDE silhouette:
a compact bottom front console, mwm window frames, square Motif controls,
hard bevels and original vector workstation icons. Copper identifies the active
window, selected workspace and focused controls. The desktop stays quiet teal,
or takes any of CDE's own 37 palettes and backdrops.

## Included

- KDE color scheme and 38 Plasma surface SVGs.
- Window frame after mwm/dtwm, as a QML Aurorae decoration: raised resize frame
  with separate corner handles, title bar of individually shadowed parts (window
  menu bar, title, minimize, maximize, close). Its colours come from the active
  colour scheme and its shadows from Motif's own shading rule, so it follows
  every palette. Title-bar height is adjustable; the buttons scale with it.
- Kvantum widget style with Motif controls: bevelled buttons, sunken fields,
  diamond radio buttons, copper focus frame, default button and selection,
  bevelled scrollbars with arrows, attached tabs and hard-edged menus.
- IBM Plex Sans Condensed for the interface and titles (semibold), IBM Plex
  Mono for Konsole and fixed-width text; both ship with the theme (SIL OFL).
- The front console (one per screen): clock with a month calendar and the day's
  appointments, configurable launcher tiles with subpanels, an Applications menu
  with cascading categories, Places, System and Help subpanels, four-workspace
  switcher, window task strip, audio level, network status, screen locking and
  session controls. The Plasma system tray sits beside it, so status icons
  (including the hidden ones behind its arrow) and notifications have a home.
- CDE's 37 colour palettes, shaded with Motif's algorithm, and CDE's 25 desktop
  backdrops, coloured with the chosen palette.
- A window arrangement around the console: terminals left and right, the main
  window in the middle above the console (Meta+Ctrl+C).
- Original SVG icon artwork and semantic aliases, with no embedded raster images.
- Konsole profile and color scheme, global-theme bundle, and teal wallpaper.
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

```sh
python3 manage.py palettes                       # list both
bash apply.sh --palette Broica                   # one of CDE's palettes
bash apply.sh --palette Copper --backdrop Pebbles
bash apply.sh --backdrop none                    # plain desktop colour again
bash apply.sh --backdrop WaterDrops --backdrop-scale 2   # for 200 % displays
```

A palette recolours everything: colour scheme, Plasma surfaces, Kvantum
controls, window frames, the console (CDE colour set 8) and, as in CDE, the
backdrop (set 3). Its files are generated when it is applied and replace the
previously applied palette. Text colours are chosen for contrast: every
text/background pair of every palette reaches at least 4.5:1, where Motif's
fixed threshold would put white on several mid-tone surfaces. A backdrop is
written once as a picture of the screen's size, so its pixels stay pixels
instead of being scaled up by Plasma.

## Configure the console

Right-click the console and choose its settings.

- **Front Console**: top or bottom edge; Always Visible, Auto-hide / Edge
  Reveal, or Dodge Windows; window list per screen; label; size (75–200 %,
  tiles, icons and text scale together).
- **Launchers**: the tiles left and right of the workspace switch. Each tile has
  a label, an icon, a program and the subpanel its arrow opens. Programs are
  "Default web browser", "Default mail client", "Default file manager",
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

Subpanels and menus accept Tab, Enter, Space, the arrow keys and Escape. The
task strip scrolls when many windows are open.

### Arrange windows around the console

Meta+Ctrl+C, the System subpanel's "Arrange Windows", or a tile with the
program "Arrange windows around the console": terminals take the space left
and right of the console down to the bottom of the screen, the active window
(or a web browser) stands in the middle above the console. Other windows stay
where they are.

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

Two settings: the title-bar height (0 follows the title font; the buttons
follow the height) and whether the whole frame takes the title colour (CDE) or
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
| `frontpanel/` | the console plasmoid |
| `arrange/` | the KWin script for the window arrangement |
| `fonts/` | IBM Plex |

Generated assets are under `build/`. All testing was performed in the
project's `plasma-lab` VM. See [TESTING.md](TESTING.md).

## Scope

This is version 0.2.0. The application style is a Kvantum theme, not a
compiled Qt style, so it needs Kvantum at run time. Third-party applications
can supply their own controls or client-side decorations. Less common icon
names fall back to Breeze and then hicolor; the console's core icons and common
file-manager icons are custom SVGs. Login/lock-screen replacement and a custom
cursor theme are outside this release. Native Plasma manages panel hiding and
screen-edge reveal; there is no separate retractable handle.

Popups from the console open at the size they first appear with: under Wayland
KWin does not move or resize them afterwards, so the Applications menu opens at
the full size of both of its levels and leaves the unused part transparent.

One console per screen is set up by `--panel`, but multiple physical monitors
have not been validated (the test VM shows only one output). Very narrow
logical screens below 800 px have not been validated either.

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
