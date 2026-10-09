# CDE Copper verification

Testing was performed in the project VM (`plasma-lab`, Fedora 44, Plasma 6.7.4,
Qt 6.11.1, Wayland).

Checks completed:

- `python3 build.py` generated the theme, decoration, plasmoid, wallpaper,
  Konsole profile, and 196 build files.
- `tools/lint-plasma-svg.py build/plasma/desktoptheme/cde-copper` passed: 38 SVGs.
- `python3 tests/verify.py` passed all six tests: scalable SVG assets,
  self-contained byte-identical rebuild from a copy of `CDE/` alone, no
  reference to sibling themes, collision refusal, install/reinstall/rollback,
  and manifest tamper refusal.
- The live Plasma session loaded the theme without a plasmashell failure.
- Dolphin and Konsole showed the custom teal/copper surfaces and Aurorae frames.
- The front console showed launchers, workspace buttons, task buttons, live clock,
  audio status, subpanels, and the searchable Applications popup.
- Workspace switching and task activation were exercised through the VM input device.
- The display was checked at 100%, 150%, and 200% scaling; the 150% and 200%
  screenshots are in `screenshots/`.
- A 2560x1440 mode was added to the virtual output and the layout remained intact.
- `uninstall.sh` removed only manifest-owned files and restored the saved
  `kdeglobals` byte-for-byte. An unrelated icon theme remained untouched.

Checks of 2026-09-30 (fonts and Kvantum widget style), same VM at 1920x1080:

- `install.sh` put the fonts under `~/.local/share/fonts/CDECopper` (13 faces
  listed by `fc-list`) and the Kvantum theme under `~/.config/Kvantum/CDECopper`;
  `apply.sh` chose `widgetStyle=kvantum` because the plugin was present.
- After a reboot: Plex Sans Condensed in panel, titles (semibold) and dialogs,
  Plex Mono in Konsole.
- Dolphin's settings dialog showed bevelled buttons, the copper default button
  (`kdialog --yesnocancel`), sunken line edits with copper focus frame, attached
  tabs, check boxes, diamond radio buttons and a bevelled combo box; the
  hamburger menu showed the raised frame, separators and sub-menu arrows.
  Screenshots: `desktop-kvantum-1920.png`, `dialog-kvantum-1920.png`,
  `menu-kvantum-1280.png` (the menu shot predates the tighter menu margins).
- `tests/verify.py` covered the new install targets and the byte-identical
  rebuild from a copy of `CDE/` alone.
- Four `kioworker` core dumps appeared at the second the test killed Dolphin
  with `pkill`; none at any other time, so they are not attributed to the style.

Checks of 2026-10-03 (version 0.2.0), same VM at 1920x1080, upgraded in place
from the installed 0.1.0:

- `python3 tests/verify.py`: 12 tests pass on the host and in the VM. New:
  contrast of all 37 palettes, Motif shading against a value worked by hand,
  a palette build passing the Plasma SVG lint, every backdrop rendering,
  upgrade from 0.1.0 (the SVG decoration is removed, the QML one installed),
  palette files owned and replaced/removed with the manifest.
- The 0.1.0 installation in the VM was upgraded by `install.sh`; the old
  Aurorae SVG theme was removed, nothing else touched.
- Window frame: active and inactive frames, corner grooves, menu bar,
  minimize/maximize squares and close; maximize pressed in when maximized.
  Title height 32 px and "colour only the title bar" (`coloredBorder false`)
  set through `auroraerc` and seen in the VM. The settings page inside System
  Settings › Window Decorations was not opened.
- Palettes: `--palette Default` and `--palette Broica`: colour scheme, Plasma
  surfaces, Kvantum, window frames and console follow; the console background
  measured exactly CDE colour set 8 (#93abbf). Back to Copper restores the
  built-in set; the generated files of the previous palette are removed.
- Backdrops: `--backdrop Pebbles` with Default and Broica; pixels unscaled after
  writing a screen-size picture (Plasma scales a tile to the screen before
  tiling it). `--backdrop none` restores the plain colour.
- Console: default tiles; a changed list via the configuration applies at once
  and the console width follows; size 125 % (tiles, icons, text, panel height).
  Workspace 1 shows "1" instead of the truncated "Arbeitsfläche 1".
- Settings pages Front Console, Launchers (ticks for installed programs) and
  Clock and Calendar open and show their values.
- Launching: Files (default file manager, Dolphin in the home folder), Web
  (default browser, Firefox), Terminal, an application from the Applications
  submenu (KolourPaint). A tile with a missing program (`foobar`) shows a
  notification.
- Applications menu: categories with icons; hover and click open the
  cascade beside the category, also after the application database changed
  while the menu was open.
- Clock: month view (German day names), "Today", localized date; no real
  appointments were tested (no Akonadi data in the VM).
- System tray beside the console: status icons, the arrow for hidden ones,
  and notifications (without a tray Plasma showed none at all).
- Window arrangement (Meta+Ctrl+C, invoked through KGlobalAccel): two
  terminals left and right of the console down to the screen bottom, Dolphin
  in the middle above the console.
- Terminal sets (2026-10-05, VM with two outputs 1920×1080 and 1280×800):
  three, four and seven terminals from the Terminal subpanel each landed in
  their places at the first try (three columns around the console; top half
  split into two terminals, two quarters below on the second screen).
  Floating console: Plasma lowers it when a window touches it, leaving the
  float gap under the middle terminal.
- KDE Store edition (0.8.6, VM): the full installation removed (NT Legacy
  Lilac came back), the store archives installed as KDE installs them
  (kpackagetool6 for the packages, the archives unpacked into aurorae/themes,
  color-schemes, icons and ~/.icons/CDECopperCursors), then the global theme
  applied with its layout: Breeze widgets, CDE icons and cursors, the SVG
  frame, the Plasma style, the console with its tiles, the four KWin
  shortcuts of the arrangement script, seven terminals placed. The console's
  Style page shows the store notice and disables the palettes. The window
  switcher needed `[kwinrc][WindowSwitcher]` (TabBox is ignored there);
  workspaces are not set by a global theme. Not testable without uploading:
  KDE fetching the dependencies. Found on the way: systemd-run expanded
  `${...}` in the console's commands itself (now passed as `$$`).
- Saved layouts (0.8.5+, VM with two outputs): saving seven terminals and
  Firefox recorded screens, places, stacking, the Konsole splits (side by
  side, one above the other, nested), folders and profiles; restoring with
  everything closed gave the same geometry to the pixel and Firefox on top;
  with six terminals open, a saved /etc terminal and a /usr|/tmp split opened
  new instead of taking the open ones; with the second output switched off,
  its windows came to the first screen scaled. Saved, named (kdialog), listed
  with previews and deleted through the console. On the host, saving recognised
  a Chrome web app (WhatsApp) by its desktop file. An earlier card layout bound
  the button height to its inner layout and looped (plasmashell at 100 % CPU,
  aborted when restarted); the cards now compute their size.
- Console settings › Launchers › "Installed application…": the list was empty
  under Plasma 6.7 (Kicker.AppsModel); now from Kicker.RootModel, Thunderbird
  picked for the Mail tile keeps the Mail subpanel and starts.
- File managers tried in the theme for the recommendation: PCManFM-Qt and Xfe
  (installed for the test, removed afterwards).
- Each `pkill dolphin` in the test scripts left kioworker core dumps (signal 11)
  and DrKonqi tray entries, as on 2026-09-30; they appear only then.

Not verified: two physical screens (one console per screen is written but the
VM shows one output), real calendar appointments, the decoration settings page
in System Settings, keyboard navigation of the Applications menu, bookmarks of
browsers other than Firefox in a live profile (Chromium's format is covered by
the tests).

Checks of 2026-10-03 afternoon (version 0.2.1, after feedback), same VM:

- `python3 tests/verify.py`: 15 tests pass. New: Firefox bookmarks from a
  made-up `places.sqlite` (toolbar first, no duplicates, no `place:` queries),
  nested Chromium bookmarks, recent files from the activity database,
  `recently-used.xbel` and LibreOffice's pick list (paths with spaces, deleted
  files left out, Writer and Calc kept apart).
- Window frame: the raised frame and the raised title parts ran into each
  other at the top (no dark edge between them) and the title's lower edge was
  doubled; title and client now share one sunken well. Checked at 4x
  magnification on both top corners.
- Bookmarks of the VM's Firefox profile (`~/.config/mozilla/firefox`) in the Web
  tile's subpanel; recent files of KWrite (the VM's default editor; Kate is
  not installed) in the Editor tile's subpanel, opened from there; a tile set to
  LibreOffice Writer lists the document Writer opened last.
- The tray's volume icon is removed once the tray has started; the console's
  volume popup (slider, Mute, Settings) opens.
- Console at the left and the right edge: upright layout, arrows pointing to
  the screen, Applications menu and cascade opening towards the middle, lined up
  with the Apps tile; clock and calendar. Back at the bottom the console is
  centred again (Plasma kept the side offset before).
- The console was found at the top edge in the VM, as set while it was tried
  out; the top edge works, and the VM was left there.

Checks of 2026-10-03 (version 0.2.2, clock), same VM:

- Digital, seven-segment (with and without seconds) and the four analog dials
  at 100 % and 75 % console size, and in the upright console at the left edge;
  every display stays inside its tile, the type and dials scaling with it.
  Checked in Copper only; the colours come from the same theme colours as the
  rest of the console.
- Seven-segment, reworked: the segments are whole-pixel rectangles on a
  canvas of whole-pixel size and position, so lit and unlit segments cover
  each other exactly and nothing blurs. Checked at 100, 125 and 150 % console
  size, and at 125 % with seconds; before, 125 % gave soft edges and unlit
  segments offset against the lit ones.
- Lit segments and colon can carry a black edge one pixel wide (Clock and
  Calendar › "Black edge around lit segments", off by default); it lies in
  the one-pixel gap between segments and covers no neighbour. Checked at 75,
  100, 125 and 150 %, and at 125 % with seconds. At 75 and 100 % the strokes
  are two pixels and the edge makes them look like little boxes, hence off.
- Lock and show desktop are now four quarter-size buttons in the space of one
  launcher: hidden icons (top left), console settings, lock, show desktop.
  Their icons scale with the console (checked at 75, 125 and 150 %; before,
  they were snapped to Kirigami's 22-pixel size). The hidden-icons button
  opens the tray's popup with the hidden entries, as its arrow does.
- "Status icons only behind the console's button" (General, on by default):
  every entry the tray knows and every application's status icon (read over
  D-Bus, every 30 s) goes to the tray's hidden list, and the tray's place in
  the panel's layout is hidden, arrow and all (Plasma has no setting for the
  arrow; the tray itself stays, for notifications). Nothing is left beside the
  console; its button opens the tray's popup with every entry, Discover's
  update icon included.
- Popup size (2026-10-09, ubuntu-lab, Plasma 6.6): with seven entries the
  popup opens 360 by 210 pixels instead of Plasma's 432 by 432 (the grid's
  four rows plus heading); opening Notifications brings 432 by 432 back,
  the back arrow shrinks it again, closing with Esc and reopening gives the
  small size at once (Plasma stores the last size in popupWidth/popupHeight).
  Checked with QMP clicks and hypervisor screenshots; no QML warnings.
- "Icons only in the status popup, names as tooltips" (Tiles page, off by
  default; 2026-10-09, ubuntu-lab): switched on by Plasma script while the
  shell ran, the next opening shows the seven entries as one row of icons,
  the popup about 360 by 100 pixels; hovering Clipboard shows its name
  and the clipboard's text as tooltip; a click opens the entry's view at
  Plasma's full size, the back arrow returns to the icon row. Switched
  off again, the two-column grid with names comes back at once (its row
  height and cell width restored); the tooltip of an entry whose name
  Plasma had left out of it stays off, as before.
- Popup in the console's measures (2026-10-09, ubuntu-lab): title 12 units
  semibold in the console's font, its buttons 26 units high, entry icons
  28 units with names in 11 units, 22 units without names in cells of 38;
  with names the popup is 360 by 190 for seven entries, without 360 by 75.
  No QML warnings in the journal.
- Compact icon grid (2026-10-09, ubuntu-lab, Slate): without names the
  seven entries sit in four columns and two rows under the title "Status",
  the popup about 150 by 110 pixels, on the first opening too (the fit
  runs again after the heading's text and the items' sizes have settled);
  Notifications opens at full size with its own title, the back arrow
  returns to the compact grid. No QML warnings.
- Symbolic icons follow the colour scheme (2026-10-09, ubuntu-lab, palette
  Slate): Plasma's tray prefers an entry's "-symbolic" icon where the theme
  has one (Solaar's battery-010, onedrive's folder, the brightness applet),
  and before 6816acc those kept the ink colour baked into their stylesheet,
  dark on a dark palette. With FollowsColorScheme=true the brightness and
  power entries show in the scheme's text colour on Slate; the coloured
  entries (bell, clipboard, KDE Connect) and the console's launcher icons
  keep the palette's colours. apply.sh --palette Slate in the VM set the
  scheme, then stopped at konsolerc ("State[$d]" line, configparser);
  the shell was restarted by hand.
- Volume button as wide as a launcher, lined up under the small buttons.
- Mail subpanel: New Message (the mail client with a bare mailto:),
  Open Mail, Appointments (the calendar application), Address Book. The
  subpanel opens; the VM has no mail client, so the entries themselves were
  not run.
- Window grouping: four Konsole windows show as one button "4× Konsole";
  three clicks brought three different ones forward in turn.
- Seven-segment with "Unlit segments faintly visible" off: only the lit
  segments are drawn.
- Style page (reported: unusable): choosing a palette had no effect on the
  dialog, Apply stayed greyed out and the page's own button sat below the
  fold. Now a choice enables Apply; Neptune → Copper applied the scheme,
  Plasma style, Kvantum and XFile's resources. The backdrop pixel size stops
  at 3, as the tool does.
- Application Style listed "kvantum" and "kvantum-dark", identical (the
  second loads a Kvantum theme's dark variant; CDE's palettes have none).
  The theme now installs kstyle/themes/kvantum.themerc (shown as "CDE") and
  kvantum-dark.themerc with Hidden=true, which System Settings honours
  (plasma-workspace 6.7.4, kcms/style/stylesmodel.cpp). Checked in the VM:
  the list shows "CDE", no second entry. Side effect: while CDE Copper is
  installed, any Kvantum theme is listed under that name.
- Progress bars: the filled part was a flat copper area. Ten variants were
  drawn on a proof sheet (screenshots/progress-varianten.png); three are
  built in and chosen in the console's Style page or with
  `manage.py palette --progress outlined|floating|slim`: outlined (dark
  edge, one-pixel bevel; the default), floating (a pixel inside the groove,
  two-pixel bevel), slim (8 px). Kvantum draws the filled part over the whole
  bar, groove edge included, so its frame repeats the groove's top, bottom
  and left edge (asymmetric: the right end carries only the fill's rings).
  All three checked in a kdialog progress window under Mustard.
- Panel around the console (reported: wider on the right): the panel's
  layout kept its 4 px spacing after the console, before an invisible end
  spacer. With the tray behind the console's button the spacing is now 0;
  measured 3 px of panel frame on both sides. General › Panel › "Frame
  behind the console" hides the panel's own background (its panel-background
  frames, in this panel only); the console then stands by itself, with the
  panel's margin around it transparent. Checked in the VM both ways.
- Icons: 51 drawings became 248, under 652 names. Chosen from what the VM
  asks for: the icons of every installed application with a menu entry, the
  menu's category icons (asked for as "-symbolic", which Breeze has and so
  won over our drawing; now linked), tray and status names (battery levels
  with charging, wireless strength, wired/offline, Bluetooth, notifications,
  brightness, vault), devices, places, document types and the common
  freedesktop action names. Contact sheets at 16/22/32/48 px checked; the
  Applications menu shows our icons for the categories and the applications
  in Multimedia and System. Build fix: the icon folder is emptied first; a
  drawing written through a link of an earlier build had overwritten the
  link's target (folder, edit-find and dialog-cancel showed other pictures).
- A backdrop per workspace (CDE Backdrop › "A backdrop for each workspace",
  off by default; Pebbles, Lattice, RicePaper, Crochet as a start): switching
  workspaces 1-4 in the VM changed the pattern each time. The fallback to the
  packaged tile no longer breaks the binding, so the pattern keeps following.
- Coloured workspace buttons: CDE gives One to Four the palette's colour sets
  3, 5, 6 and 7, measured on a CDE 2.x screenshot with the Default palette
  (#8998aa, #c6b2a8, #4992a7, #b7878d, exactly sets 3, 5, 6, 7). The tool
  writes the four sets to cde-copper/workspaces.json with every palette; the
  console reads it (General › Workspaces, on by default). Copper uses
  #649099, #c4d2d0, #2e7180, #e8874f. Checked in the VM under NorthernSky.

Checks of 2026-10-03 (after 0.4.0: review fixes, pixel icons), same VM:

- A review of everything since cde6f41 found one bug and several risks, all
  fixed: the console emptied the tray's hidden list at every start when its
  option was off (it now records what it hid itself and takes out only
  that); Copper's progress style was lost on reinstall; choosing one
  backdrop in the Style page had no effect with backdrops per workspace
  (it now switches those off); seven-segment digits under 13 px lost their
  horizontal segments (orientation is now explicit, small digits use 1 px
  strokes, at least 9 px high); the layout spacing and the panel frame's
  opacity binding were not restored (spacing is put back, the frame is
  hidden by scale); the workspace colours could stay from an old or a
  non-CDE scheme (read three times after a change, none for other schemes);
  XFile's menu entry carries InitialPreference=1.
- Busy progress bars: the moving block shows the groove's dark edge on its
  left, as the filled part repeats it; it reads as an outlined block.
  Right-to-left layouts not checked.
- Pixel icons: 59 drawings at 16 and 22 px (181 names with aliases), drawn
  on whole pixels and written as SVG rectangles; the theme lists 16/all and
  22/all as fixed sizes. Dolphin's Places panel shows them crisp; Downloads
  showed a plain folder (Dolphin asks for folder-downloads), now an alias.
- Cursors: 28 drawings after the X11 cursor font on the 16-pixel grid,
  written as Xcursor files (24 drawn anew, 32/48/64 enlarged by whole
  numbers), 99 names with the X11, Qt and CSS aliases. Thin strokes keep
  their colour: the white mask is the shape grown by one pixel, as in the
  cursor font. System Settings lists them as "CDE"; applied in the VM with
  plasma-apply-cursortheme. A test reads the Xcursor headers.
- Cursors, revised after a proof sheet of ten variants
  (screenshots/zeiger-varianten.png; chosen: 8 with the shadow of 9): slim
  shapes rasterised anew at every size, black on a coloured rim, soft
  shadow (premultiplied ARGB, computed without an image library, as the
  tool runs on the user's machine). Rim: Style page › Mouse cursors, or
  `manage.py palette --cursor copper|palette|white|#rrggbb`; "palette"
  follows every palette change. Plasma keeps a cursor theme's images by
  name, so the tool switches to Breeze and back. Checked in the VM: palette
  Arizona gave the rim #d3d178. The fleur's heads are narrower, so the four
  arrows no longer run together into a diamond.
- Style page: the backdrop preview stayed white after a palette change
  while the page was open (it looked for the old palette's tiles, which the
  tool replaces). The page now rereads the palette in use and falls back to
  the packaged Copper tile.
- Meta key: the console provides org.kde.plasma.launchermenu, so Plasma
  activates it on the active screen; it opens the Applications menu above
  the Apps tile. Checked in the VM with a real Meta key press (uinput) and
  with PlasmaShell.activateLauncherMenu; a second press closes the menu.
- Start-up screen (KSplash, contents/splash in the global theme): a Motif
  dialog with copper title bar, logo and a meter of six blocks, one lit per
  KSplash stage, on the Lattice backdrop in Copper's teal. Applying the
  theme sets ksplashrc to it. Checked with `ksplashqml org.cde.copper.desktop
  --test --window` in the VM (screenshots/splash-1920.png, also its
  preview in System Settings); a real login not yet.
- Start-up screen, revised: each block shows what starts in that stage
  (display, window manager, Plasma, settings, session, desktop - the order
  of plasma-workspace's ksplashqml under Wayland; KSplash passes only the
  count), and the line below names it. Colours and backdrop tile follow the
  palette: the tool writes splash/Colours.qml and the Lattice tile with
  every palette (and after a reinstall). Checked under Orchid and Copper.
- Lock screen: Plasma 6 loads it from the shell package plasmashell runs
  (plasmashellrc [Shell] ShellPackage, read by kscreenlocker too), not from
  the global theme, so a lockscreen/ in the global theme is ignored. CDE's
  is the shell package org.cde.copper.shell: lockscreen/ only, everything
  else from org.kde.plasma.desktop (libplasma's X-Plasma-FallbackPackage).
  plasmashell names its configuration after the shell, so switching stops
  plasmashell, copies plasma-<shell>-appletsrc to the other name, sets the
  key and starts it again; uninstall switches back first. Checked in the VM:
  kscreenlocker_greet --testing --shell org.cde.copper.shell (a wrong
  password shows the failure line, the field is ready again); a real lock
  with loginctl lock-session showed the dialog in Orchid's colours,
  unlock-session ended it; switching to Plasma's lock screen and back kept
  the console and desktop configuration. A real unlock by password was not
  tried (the VM user's password is not known here); the success path is
  kscreenlocker's own (authenticator.succeeded -> Qt.quit). Texts in English.
- Logout dialog (contents/logout/Logout.qml of the global theme, which
  ksmserver-logout-greeter loads, Breeze as fallback): the signals and
  context properties of Plasma's own (maysd, sdtype, spdMethods, canLogout,
  softwareUpdatePending), the countdown of 30 s, Enter for the default
  action, Escape or a click beside the dialog to cancel. Shown with
  `ksmserver-logout-greeter --windowed` in the VM for 5 s and stopped (the
  windowed mode carries the actions out for real, so no button was
  pressed); hibernate is not offered by the VM, so its button stays hidden.
- GTK theme (gtktheme.py, themes/CDECopper with gtk-3.0 and gtk-4.0): GTK's
  built-in theme (Adwaita for 3, Default for 4) imported, Motif controls on
  top in the palette's colours, plus rules for the more specific states of
  the built-in themes (disabled, checked, backdrop) and GTK 4's full-path
  selectors. gtk-dark.css is the same file: Plasma reported "prefer dark"
  for Orchid and GTK 4 then fell back to its own dark theme. Applying sets
  it through Plasma's gtkconfig (org.kde.GtkConfig.setGtkTheme); a palette
  change rebuilds it and switches GTK to Adwaita and back so running
  programs reload; uninstall restores the previous GTK theme. Checked in the
  VM with gtk3-widget-factory, gtk4-widget-factory and PCManFM under
  Orchid. Not checked: Firefox, libadwaita programs (they ignore themes).
- System parts (system.py as root, manifest /var/lib/cde-copper/system.json;
  VM snapshot vor-system taken first). Plymouth: script theme from small
  PNG pieces, text set by Plymouth; the VM lacked the script module
  (plymouth-plugin-script), now checked before anything changes. Seen in a
  real boot: the dialog on the Lattice backdrop, the meter filling. GRUB:
  backdrop or picture, menu in a nine-piece Motif frame, title bar and
  countdown. Findings in real boots: under Secure Boot (on in the VM) GRUB
  loads no font files (lsfonts at the GRUB prompt showed only Unifont), so
  the theme falls back to "Unifont Regular 16" there; GRUB draws image
  components over everything, a label on the title image included, and
  draws no progress bar without the timeout id, so the title is set into
  the title image at build time (Pillow on the build machine). A JPEG
  background loads under Secure Boot. Picture: wallpapers/images/<name>.jpg
  (--grub-background, default altai-dark; lattice for the backdrop).
  screenshots/grub-1280.png. Not checked: the passphrase prompt, BIOS
  machines, Debian's grub paths.
- Grip edge (0.8): widgets/glowbar of the desktop theme, read by KWin's
  screenedge effect. Console set to auto-hide, pointer held 4 px above the
  bottom edge with uinput: a raised bar (ink, light, active colour, dark)
  along the console's width, fading in with the approach, in Orchid. KWin
  shares corner elements between two edges, so the bar has no end caps.
  Effect reloaded over D-Bus after replacing the file.
- Alt+Tab (0.8): kwin/tabbox/org.cde.copper.switcher. KWin loads a newly
  installed switcher package only after logging in again (reconfigure
  kept the fallback). Seen with Konsole, Dolphin and KWrite: Motif face,
  title bar with the window's caption, sunken selection. OSD (volume) and
  notifications already wear the desktop theme's Motif frames; Plasma 6.7
  loads the OSD from its own QML module, not from the shell package.
- Controls (0.8): QWidget push buttons, combo boxes and line edits were
  28 px; Kvantum ignored min_height for dialog buttons, larger text
  margins (5/4) make them 32 px, measured with kdialog. QML controls
  (System Settings) were 28–30 px already.
- Scaling (0.8): 150 % at 1920x1080 and 200 % at 3840x2160 with
  kscreen-doctor. Seen sharp at both: window frame and title buttons, the
  console with clock, tiles, workspace buttons and the quarter-size session
  buttons, Alt+Tab (centred), logout dialog, lock screen
  (kscreenlocker_greet --testing), Konsole and kdialog. Not checked at
  these scales: start-up screen, Plymouth and GRUB (fixed pixels), the
  subpanels.
- German (0.8): 207 messages in po/de.po (Codex wrapped the strings,
  domain cde-copper, installed as ~/.local/share/locale/de/LC_MESSAGES/
  cde-copper.mo). Full install from the package in the VM (de_DE): tiles,
  workspace heading, subpanels in German. Found: tile labels saved in the
  configuration stayed English when the tile's program differed from the
  preset (Files with XFile); shipped labels are now translated whatever
  the program. "Anwendungen" did not fit a tile: "Programme".
- Subpanels (0.8): open on the Help arrow, pointer moved into the subpanel
  (stays open), then far away (closed about half a second later). Opened
  or used from the keyboard they stay until Escape or a second click.
  Same rule for the calendar and the volume popup (not seen separately).
- Pictures as backdrops (0.8): picture:origami through the CDE Backdrop
  type, set with manage.py; full screen, sharp. Not checked: the dark
  version under a dark palette, the Style page and per-workspace lists in
  use (built, not clicked through).
- Install over hand-copied files: install.sh refused to overwrite the
  switcher copied in by hand during testing ("Refusing to overwrite
  unowned path"), as it should; removed by hand, then installed.
- Window shadow switch and scroll bar (0.8): manage.py palette
  --window-shadow off/on writes windowShadow to the decoration's group in
  auroraerc; off took effect after a new login, on right away (KWin
  reconfigure). The scroll bar slider now has one bevel ring inside the
  ink outline instead of two (the GTK slider had one already); seen in
  Konsole. Errors met on the way: plasma-apply-cursortheme aborted when
  manage.py ran over ssh (no X display) and Plasma reported it as a crash,
  now only called with DISPLAY set; plasmashell hung on logout in Klipper's
  clipboard history (KIO worker thread join), Plasma's own code, and was
  killed by systemd after the stop timeout.
- Switching with NT Legacy, two screens (0.8.4): the VM got a second
  graphics card (Virtual-1 1920x1080, Virtual-2 1280x800). Global themes
  applied with plasma-apply-lookandfeel, with and without --resetLayout,
  as System Settings does; after each step the shell, the panels and their
  widgets per screen, plasmashell's state, coredumps and warnings.
  - Under CDE's shell NT Legacy's layout (org.kde.plasma.desktop only) gave
    Plasma's default panel: the shell now follows the global theme
    (cde-copper-theme.path, manage.py follow-theme). 17 steps through all
    NT variants, CDE day/night and Breeze, with and without layout: shell
    right in every step, each theme its own panel, no coredumps.
  - Quick switches hit systemd's start limit for plasmashell
    (start-limit-hit, desktop without a shell): reset-failed before every
    start, one retry.
  - NT Legacy's layout on two screens left, in about every second switch,
    its panel on no screen (screen -1) and both screens black until
    plasmashell restarted - without CDE involved too (Breeze -> NT). Cause:
    applied in a running Plasma, the second screen has no desktop yet; the
    panel created for it was removed again and took the first along. One
    panel only: 8 of 8 clean. Fix in nt-legacy/build.py (and CDE's
    layout.js): further screens only where desktopForScreen(s) exists.
    The watcher also restarts plasmashell once if a panel stays on no
    screen, whatever the theme.
  - One console for all screens (default) or one per screen (console
    settings, cdecopperrc): switched on and off at runtime, a console was
    added to and removed from the second screen.
- Console on the screen edge (0.8.4): option "floating" (default on). Off,
  the console set p.floating = false, yet 4 px of panel stayed between it
  and the edge. Codex traced it in plasma-desktop's panel containment:
  every applet gets top and bottom layout margins from the panel
  background's fixedMargins, on the screen-edge side too, unless it sets
  Plasmoid.CanFillArea. With that (only when not floating) and the panel
  as thick as the console (116 px) it reaches the edge: measured, the
  console's outline is the last screen row; floating on keeps 12 px.
  Default button of the logout dialog and lock screen: a 1 px ring with a
  pixel of air instead of the 3 px dark Motif frame.
- Leave Session (0.8.3): the System subpanel's D-Bus entries did nothing:
  the D-Bus caller had become a shell expression ($(command -v qdbus6 ...))
  and the entries' check took "$(command" for a program and gave up.
  resolve()/check() now pass such expressions through (Launch.DBUS). New
  entries Restart... and Shut Down... (LogoutPrompt promptReboot /
  promptShutDown); log out is a door, shut down the power sign, restart the
  circular arrow, in the pixel versions too. The direct D-Bus call opened
  the greeter in the VM; the entries themselves not yet clicked (the user
  was working in the VM).
- Session block, load meter, hard contrast, lock icon (0.8.3): the arrow
  strip opens the tray popup with the hidden icons; the meter (ksystemstats
  sensors cpu/all/usage, memory/physical/usedPercent) went to full on four
  busy loops. Hard contrast under Alpine changed little in colour, the
  palette's console text is already black: CDE's palettes pick black or
  white for it. So the option sets the labels semibold too, the thin small
  type being the other half. Found on the way: a second font.weight in
  ConsoleButton.qml made the console fail to load ("Property value set
  multiple times"). The padlock lost its shackle on the console face (a
  pale stroke without outline): now outlined, copper body, dark keyhole.
  Also found: installing the X11 session had upgraded Plasma only partly,
  some of Plasma's own applets (battery, brightness, weather) failed with
  undefined symbols; the VM was then upgraded as a whole.
- System Settings icons (0.8.2): KDE shortens a missing icon name until
  one exists, so 42 page names (preferences-desktop-color, -icons,
  -cursors, ...) fell onto four drawings and the appearance pages showed
  one monitor. Now ten new drawings (global theme, colours, application
  style, Plasma style, window decorations, icons, pointers, splash, task
  switcher, effects, shortcuts) and SETTINGS_ALIASES onto drawings that
  fit (display, sound, network, power, time, users, printers, search, ...).
  Seen in System Settings in the VM; all module icon names of Plasma 6.7
  resolve except symbolic ones and media-optical-audio (CD drawing).
  CDE Night got its own preview (screenshots/desktop-night-1920.png).
- Icons after the palette (0.8.2): icons.recolour maps Copper's eight
  colours to palette roles (manage.py update_icons, run with every palette;
  0.07 s to draw the set). Proof sheet of all palettes on console face and
  text field: screenshots/icons-palettes.png. Seen in the VM: console and
  PCManFM-Qt under NorthernSky, Summer and Cabernet. Trap met: icons looked
  like Breeze in programs started over ssh, because their XDG_CONFIG_DIRS
  lacked ~/.config/kdedefaults, where a global theme keeps the icon theme;
  started from the console (session environment) they are CDE's.
  Tests: contrast floors for all palettes, symbolic icons and links untouched.
- Stability pass (0.8.1), lab VM, Plasma 6.7.4 then 6.7.5, Wayland and
  X11. A check script after every step: global theme, colour scheme,
  shell, panels and consoles (plasma scripting), wallpaper plugin, new
  coredumps, journal warnings from the theme's files.
  - Global theme with layout under CDE's shell left a desktop without any
    panel, both ways: CDE Copper shipped only org.kde.plasma.desktop-layout.js
    (now also org.cde.copper.shell-layout.js), and Breeze and every other
    theme only have that one (the shell package now has a default layout:
    Plasma's panel template). Breeze ↔ CDE with and without layout: panel
    resp. console each time.
  - Day/night: CDE Night applied without layout (as Plasma's automatic
    switch does through KLookAndFeelManager): palette NorthernSky followed
    (Kvantum, Plasma surfaces, manifest), the plain desktop colour too;
    back to day: Copper. Plasma's automatic switch itself did not fire in
    the VM (night light not running), so it is simulated.
  - Lock screen: real unlock with wrong, then right password, on Wayland
    and X11 (an X11 lock failed once with "Could not establish screen
    lock" while the Alt+Tab test still held the keyboard; again without it,
    fine). Flow rebuilt after Plasma's (see README).
  - Shell switch cde → plasma → cde through the palette tool: console kept.
  - Logout dialog: Escape cancels (no logout after the countdown time),
    Enter logs out.
  - Login twice, then a reboot, then X11: no warnings from the theme's
    files at start, no coredumps; plasmashell stopped within 2 s.
  - Uninstall: restored the state before the first install (here NT
    Legacy's global theme and panel); all theme files gone; found and fixed:
    the decoration's auroraerc group and the lock file stayed. Reinstall
    with --apply --panel: console back; found and fixed: one workspace
    after the next login (KWin kept four in memory, kwinrc had one).
  - Fresh user (useradd, autologin switched, reboot): package installed and
    applied in that session, login again: console, frames, controls, German
    labels; then removed again.
  - Eight palette switches in a row: 3–4 s each, no errors; KWin grew by
    100 MB once (caches) and stayed there over eight more.
  - Settings dialog: half the "does not have a property called cfg_..."
    warnings gone (defaults declared); the rest are settings a page does
    not show, left undeclared on purpose (Plasma's saveConfig writes back
    every cfg_ property of the open page).
  Not checked: several screens (QEMU connects a second virtio head only for
  a viewer that asks for it), Plasma's automatic day/night trigger, a
  second PAM prompt (one-time code), an account without a password.
- Boot parts after the palette (0.8): system.py install as tester's sudo
  drew both in Orchid (manifest palette), boots recorded twice a second
  with virsh screenshot. The black box between GRUB and Plymouth was GRUB's
  console (cleared when an entry boots), not the kernel: still there with
  plymouth.use-simpledrm. GRUB grows a smaller console to 80 x 24 Unifont
  characters (640 x 408 px, measured; 1 x 1 and one line fell back to its
  default box), the signed Fedora GRUB has no gfxterm_background
  (background_color) and color_normal does not reach the cleared area. So
  the console now covers exactly the menu window and countdown, framed
  alike: black inside under Secure Boot, the window colour without it
  (not checked: no VM without Secure Boot). Fedora's BLS entries ignore
  GRUB_GFXPAYLOAD_LINUX: /etc/grub.d/09_cde_copper_gfxpayload exports
  gfxpayload=keep (removed by uninstall). The full test run was not possible at
  this commit: the build stops in the picture wallpapers another session
  is adding (wallpapers/images/mrt.jpg not there yet).
  Off by default since; the frame is there for those who want it.
- XFile 1.2.1 built from source in the VM (motif-devel, libXinerama-devel,
  libXft-devel); a palette change wrote `~/XFile` in that palette and the
  menu entry. Not checked: the Files tile switched to XFile (the launcher
  code is the same as for every other program).
- The VM's wallpaper had been changed to a grey-teal gradient in the meantime;
  it was left as found, as were the console at the top edge and its settings.

Auto-hide (reported: the console could not be brought back):

- Plasma reserves the screen edge that reveals a hidden panel when the hiding
  mode is set and does not move it with the panel. The console's settings set
  mode and edge in one script, the mode first. Reproduced: with auto-hide on,
  moved from the top to the bottom, pressing against the bottom edge did
  nothing; setting the mode again at the bottom made it work.
- Now the console is placed while it stays visible and hidden 1.5 s later.
  Pressing against the edge (40 pointer events over two seconds; a single jump
  to the edge only shows KWin's edge glow) revealed it at the top, after moving
  to the bottom, and after moving back to the top.

Checks of 2026-10-03 (version 0.3.0, palettes and backdrops in Plasma), same VM,
upgraded in place:

- `python3 tests/verify.py`: 16 tests pass. New: 38 colour schemes installed,
  the palette tool runs from the profile copy, an upgrade from 0.2 takes over a
  colour scheme 0.2 had generated for an applied palette.
- `plasma-apply-colorscheme CDEBroica` (what System Settings › Colours does):
  within seconds the console's tool switched the Plasma theme to cde-broica,
  Kvantum to CDEBroica and generated Broica's backdrop tiles; a newly started
  Dolphin showed Broica's controls.
- "CDE Backdrop" wallpaper: Pebbles in Broica's colours, pixels unscaled at 4x
  magnification. The plugin first lay under `~/.local/share/wallpapers` and was
  not found (black desktop); it belongs under `~/.local/share/plasma/wallpapers`.
  Plasma remembered the failed load until the wallpaper type was switched away
  and back.
- Style manager page: every palette with its stripes, the palette in use
  marked. Its Apply button was not clicked in the VM (the same command was run
  from a shell).
- Desktop settings › Wallpaper type lists "CDE Backdrop"; its page shows all
  25 patterns in the palette's colours with the current one marked (dialog
  cancelled afterwards). CDE's `SkyLight.pm` declares 1024 rows and holds
  1023, which made a truncated PNG; missing rows are now repeated and a test
  checks every tile's row count. The widened pixel-size field was not looked
  at again after the fix.
- Title bar height by default now the title font + 6 px (about 23 px, before
  29 px), on request.
- Restored afterwards: palette Copper and the wallpaper the VM had (the NT
  Legacy picture "ntlegacy-win98-flaeche").

Checks of 2026-10-03 (title bar height, reported: a lower limit):

- Heights below 16 px were ignored and fell back to the automatic height
  (about 23 px), so a smaller setting gave a taller bar. Now every height from
  8 px is used and the title text shrinks with it. Seen in the VM at 12, 16
  and 21 px (21 being the value set there): text readable and inside the bar.
- The decoration is listed as "CDE" now; it follows any palette.

Switching global themes (reported: back to CDE Copper the panel came apart and
another one was used):

- The global theme carried its layout at `contents/layout.js`; Plasma reads
  only `contents/layouts/org.kde.plasma.desktop-layout.js`. With the layout
  option ticked, Plasma fell back to its default panel (Kickoff, pager, task
  manager, clock) drawn in CDE's surfaces. Now in the right place; round trip
  CDE Copper → NT Legacy Lilac → CDE Copper with `plasma-apply-lookandfeel
  --resetLayout` gave the front console with its tray each time.
- The global theme set the Qt Windows widget style; now Kvantum. It also has a
  preview picture for System Settings now.
- A global theme writes its colour scheme only into the defaults layer
  (`kdedefaults/kdeglobals`); the palette tool read `kdeglobals` alone and so
  missed it, leaving Kvantum on the previous palette (seen: Camouflage controls
  under the Copper scheme). It now falls back to the defaults layer; a test
  covers it. The full round trip with a non-Copper palette could not be
  repeated cleanly: the VM was in use at the time (Delphinium was chosen in
  between; the state was consistent afterwards).

Decoration preview in System Settings (reported: it showed a broken title
bar):

- The preview uses KDE's default buttons, which include a context-help button;
  the preview window offers no help, so the button was hidden but kept its
  room, leaving a gap in the title bar. Hidden buttons now take no room.
- Under the client the frame colour was drawn; the preview (and a window
  being resized) showed copper there. Now the window colour of the scheme.
- Checked in a new `kcmshell6 kcm_kwindecoration` window; a System Settings
  window open before keeps the old preview until the page is opened again.

Checks of 2026-10-03 evening (buttons, live palette switch, show desktop):

- Push buttons: 32 px high before (measured in a `kdialog` and in System
  Settings), 29 px after (text margins 3/2 instead of 3/3, side margins 5
  instead of 8, minimum size +0.1 font instead of +0.3), about 90 % as asked.
  Short labels ("Ja", "Nein") keep Qt's minimum width of dialog buttons.
- Palette switch in open windows: research by Codex (CLI, read-only) on the
  Kvantum, plasma-integration, KWin and Aurorae sources: Kvantum has no reload;
  KDE programs build a new style object only when the style name changes.
  Tested: a Dolphin opened before a switch to Broica kept Neptune's controls;
  after widgetStyle kvantum -> fusion -> kvantum with the KGlobalSettings
  signals it showed Broica's, without restart. Contrary to the research,
  KWin did not recolour the frames of open windows, not even after
  `reconfigure`; switching the decoration away and back did. Both are now part
  of every palette switch (about 3 s, a short flicker). Back to Neptune with
  Dolphin open: controls and frame changed at once.
- Show Desktop: KWin's D-Bus `showDesktop(true)` is accepted and does nothing
  in Plasma 6.7 (`showingDesktop` stays false); the button now invokes KWin's
  "Show Desktop" shortcut through KGlobalAccel, which toggles. The command was
  checked directly; the console in the VM was not restarted, as the VM was in
  use, so the button itself takes the fix after the next login.

Against the specification's test matrix (`IMPLEMENTATION-GUIDE.md`), as of
0.3:

| Check | Status |
|---|---|
| 100 % scaling, crisp edges | checked (all versions) |
| 150 % scaling | checked for 0.1 only; not for the QML frame, console, popups |
| 200 % scaling | as 150 % |
| active/inactive window distinguishable | checked by colour; no structural difference (see README) |
| keyboard focus visible on every widget | not checked systematically |
| panel auto-hide without focus trap or flicker | reveal checked by pointer (0.2.2); keyboard not checked |
| multiple monitors, popups on screen | not checked (VM shows one output) |
| dark terminal keeps the frame readable | checked (Konsole in every screenshot) |
| starts without QML or KWin errors | warnings in the log (settings pages, menu binding loops) |
| no root rights | checked (installer refuses root, tests run as user) |
| Wayland session | checked; X11 not |
| uninstall removes only own files | checked by test (verify.py) and in the VM |
| icon fallback documented | yes (Breeze, hicolor) |

The project VM was restored to the original configuration after the destructive
installation test. The last visual run deliberately leaves CDE Copper applied
in the VM so it can be opened with `vm/vmctl.sh viewer`; remove it with
`./uninstall.sh` inside `/home/tester/cde-copper` when finished viewing.

Known scope: the Motif controls need Kvantum (fallback: Qt Windows style); the
login screen, cursor theme and third-party client-side decorations are not
replaced. The custom front console with the Plasma system tray beside it is
the supported panel experience.

Checks of 2026-10-07 (login screen, plasma-login-manager 6.7.5), VM at 1280×800:

- `system.py install --parts login` with autologin switched off: the greeter
  shows the Lattice backdrop pixel for pixel (rendered at 1280×800, Image.Pad),
  the clock, labels and icons in the palette's light panel text, the password
  field as a dark Motif field with the copper focus frame, IBM Plex.
- Found on the way: the key is `WallpaperPluginId` (Fedora's defaults.conf has
  `WallpaperPlugin`, which the greeter ignores); the image path is read only
  from /etc/plasmalogin.conf, plugin and FillMode also from conf.d; the greeter
  draws its text in the Button colour set; any image is scaled to the screen,
  tiles included. Restarting plasmalogin alone keeps the greeter user's
  systemd manager (and its cached units) running: `systemctl stop user@984`.
- `uninstall --parts login` restored /etc/plasmalogin.conf (with a wallpaper
  group of its own, as Nobara has), the greeter's kdeglobals, and removed
  plasmarc, the Plasma theme, fonts and backdrop.
- `python3 tests/verify.py`: 28 tests pass.

Checks of 2026-10-07 (window display), VM at 1920x1080:

- Default "strip": the console unchanged, task strip as before.
- "tileLeft" set through the console's configuration (mirrored to
  cdecopperrc [Console] windowDisplay): window tile between the left
  launchers and the workspaces, the strip's row gone, the console lower,
  volume as a tile beside the session block.
- A click on the tile opened the list with all four windows and their
  workspace; after a click into Konsole, Konsole was pressed in and its icon
  on the tile although the open list holds the focus. A click on the KWrite
  entry brought KWrite forward and closed the list.
- "tileRight" with the console upright at the left edge: tile below the
  workspaces, the console as tall as its tiles, the list opening to the right.
- Not checked: the mouse wheel over the tile (the VM's test input has no
  wheel), more than twelve windows (scrolling list).

Checks of 2026-10-07 (window icons under the workspaces), VM at 1920x1080:

- "workspaces": buttons 1-4 in one row, each over a well; eight windows on
  workspace 1 in two rows of icons, the active one pressed in. Before the
  icons were sized to two rows the well showed three and "+5".
- KWin's "Window to Desktop 2": the window's icon moved to workspace 2's well.
  A click on it switched to workspace 2 and brought the window forward.
- Volume: `wpctl set-volume … 40%` from outside showed "40%" within 1.5 s
  (pactl subscribe watcher; before, the 5 s poll). The speaker on the volume
  tile is now smaller than a launcher's icon.
- Not checked: overflow beyond ten windows on one workspace, the console
  upright in this mode, a system without pactl (falls back to the 5 s poll).
- Afterwards: label gone, buttons 17 high, icons up to 24 in two rows of
  four (the wells widened to at least 104); seven windows on workspace 1
  all shown without "+".

Checks of 2026-10-07 (pager: workspaces in miniature), VM with two outputs
(1920x1080 and 1280 wide beside it):

- "pager": under each button a map of both screens, their outlines drawn;
  KWrite, Dolphin and Konsole on workspace 1 at their places on the left
  screen, three Konsoles on the right one, the active Konsole in the
  selection colour and over the windows below it.
- A click on Dolphin's rectangle under workspace 2 switched to workspace 2;
  a click on the empty map of workspace 3 switched to workspace 3.
- "Window Maximize" on Dolphin: its rectangle filled the left screen's map at
  once (geometry changes reach the map).
- Not checked: one console per screen with "only this screen's windows" (the
  map then shows that screen), the console upright in this mode, a live drag.
- Screens changed while running: the second output disabled, the map showed
  one screen with the windows KWin moved onto it; enabled again below the
  first, the map showed both stacked; moved back beside it, side by side.

Checks of 2026-10-07 (workspace views on the Workspaces page):

- A console with windowDisplay=pager from 0.8.11 came up with
  workspaceWindows=pager and windowDisplay=strip (migrated on start, mirrored
  to cdecopperrc).
- Workspaces page › Windows: "Icons under each button" chosen in the dialog
  and applied: workspaceWindows=icons, the console switched. General shows
  only strip and the two tiles, with a note pointing to the Workspaces page.
- Panel height on every change of the strip: pager 100, switcher hidden 128
  (the strip back), shown again 100, "none" 128, tileRight 100, strip 128.
  Before, only a change of windowDisplay itself reached the panel, so
  switching on the Workspaces page left the strip squeezed into 100.
- The VM had consoleScale=1.5 left from an earlier test (panel 2031 long);
  reset to 1, the pager console is 1369 long.

Checks of 2026-10-07 (backdrop after palette changes), VM:

- Host report: after several quick palette switches the left desktop showed
  only its colour. Cause: the tool wrote the palette only to desktops showing
  the CDE Backdrop at that moment; this one, switched back to it later, still
  named BeigeRose, whose tiles had been removed; the fallback to the packaged
  tile then failed in a binding loop ("Binding loop detected for property
  source"), so no tile at all.
- Now: Backdrop=Ankh with Palette=BeigeRose (no such tiles): Ankh drawn from
  backdrops/current, no binding loop in the log.
- Desktops on "Plain colour", `manage.py palette --palette Mustard`, then
  back to CDE Backdrop: Palette=Mustard and the palette's colour behind the
  pattern were there, no "Cannot open". `current` follows the palette.
- The backdrop dialog names the palette in use (Mustard) and shows its tiles;
  every preview the same width, long names such as "Akustikschaum (natural
  colour)" shortened, the full name as tooltip.

- Stale desktops are also corrected by `install`: Palette=BeigeRose and
  Color=#b78989 written to both desktops, then `./install.sh` (applied with
  Mustard): both back to Mustard and #4d648d.

Checks of 2026-10-07 (pattern colour on dark palettes), VM:

- Amber, BrickWall: `--pattern-colour cde` white on #1c160a (the host showed
  the same two colours: as in CDE, not a fault); `--pattern-colour palette`
  #ffb340 on #1c160a, the desktop changed at once.
- Before, the desktop kept the white bricks after the second run: same palette,
  same file name, so the image was not read again. The tool now writes a
  Revision with every palette run and the wallpaper adds it to the address.
- Requests from the Style page carried `--pattern-colour palette` (the box
  reads the manifest's pattern_colour).


Checks of 2026-10-07 (window settings moved to the Workspaces page), VM:

- Front Console page: nothing about windows left. Workspaces page › "Open
  windows": "Shown as" with all five views, grouping (only for the strip) and
  "only this screen's windows".
- "Window tile right" chosen and applied: windowDisplay=tileRight,
  workspaceWindows back to its default, console 1141 long. Then "Each
  workspace in miniature": workspaceWindows=pager, windowDisplay kept
  tileRight for a hidden switcher, console 1369 long.

Checks of 2026-10-07 (icons, small buttons), VM:

- Proof sheets of ten proposals each; chosen: faders for the console's
  settings (cde-console-configure, falling back to "configure" under other
  icon themes), the wire basket for the trash (64, 22 and 16 px drawn).
- Small buttons default configure, lock, desktop, load, volume, network: three
  columns beside the arrow strip; network showed the cable plug (VM on
  virtio ethernet). The volume tile is gone; in strip mode the strip's row
  has no volume button while volume is a small button.
- A click on the small speaker opened the volume popup above it, tooltip
  "Volume 40%".
- Not checked: WLAN signal icons (the VM has no WLAN), the settings
  checkboxes in the dialog, the upright console with three pairs.

Checks of 2026-10-07 (WLAN popup), VM with mac80211_hwsim (three virtual
radios; kernel-modules-internal from Koji, the VM has no internet): two
hotspots "CDE-Testnetz" and "Nachbar:WLAN" on wlan1/wlan2, wlan0 the client.

- The popup listed both, the colon in "Nachbar:WLAN" read right, lock and
  signal shown. Right after opening the list came back empty (the scan it
  starts still running): it now says "Searching for WLANs…" and asks again
  every 1.5 s, the list was there after about 8 s.
- A click on a new secured network brought Plasma's own passphrase dialog
  ("Authenticate CDE-Testnetz"); without ifname nmcli had taken the hotspot's
  card, so the join now names the client device.
- A click on the network in use disconnected wlan0 only (by device); a click
  again brought the saved connection up on wlan0.
- In this setup the header can name a hotspot's connection (a card sending a
  network counts as connected); a laptop with one card has no such case.


Checks of 2026-10-08 on Ubuntu 26.04 with Kubuntu's Plasma 6.6.6 (VM
ubuntu-lab from the cloud image, Wayland, German):

- `install.sh` fine. `apply.sh --panel` failed in layout.js: Plasma 6.6's
  ConfigFile has keyList, not keys, so handing the saved console settings
  back threw a TypeError after the old panels were already gone. Now
  keyList, keys or nothing.
- After the fix and a new login: console, clock, workspaces, launchers, the
  wire basket and the small buttons as on Fedora.
- Network showed offline: the cloud image leaves the cable to
  systemd-networkd (nmcli: unmanaged). Without a connection NetworkManager
  knows, the default route now decides (cable plug shown).
- Without Kvantum the controls fell back to the Qt Windows style, as the
  installer said; with `qt6-style-kvantum` and `apply.sh` again, Dolphin had
  the Motif controls and the Motif window frame.
- Not checked: the login screen and splash on Ubuntu (SDDM), XFile.

Checks of 2026-10-09 (X11 smoke test, version 0.9.4 as committed in d9803fd),
Ubuntu 26.04 VM `ubuntu-lab` with Kubuntu's Plasma 6.6.6 on an **X11 session**
(`plasma-session-x11` and `kwin-x11` installed, SDDM autologin `Session=plasmax11`;
the VM has no internet behind the host's Docker FORWARD policy, so the 33 .deb
files were fetched on the host and installed from a local directory), 1280×800,
German. Input through QEMU's QMP `input-send-event` (absolute tablet) and
`sendkey`; screenshots through the hypervisor.

- `install.sh` upgraded the installed 0.9.3 in place; after a reboot into X11:
  `kwin_x11` with the QML Aurorae frame (`kwin4_decoration_qml_cdecopper`),
  CDE's shell (`org.cde.copper.shell`) and the console at the bottom with
  clock, launchers, workspaces, task strip and small buttons. Kvantum controls
  in Dolphin. No `org.cde.*`, QML or Aurorae messages in the user journal, no
  core dumps.
- Clicked and seen: workspace buttons (2, then back to 1, windows follow),
  the clock's calendar popup, the Terminal tile's subpanel (New Terminal,
  Three, Four), a task button (Konsole raised, frame copper), the volume
  popup (slider, Mute, Settings), the console's right-click menu (CDE Front
  Console settings), the Apps tile by click with the cascade opening on hover
  (Internet › Firefox …), and the Apps menu through the Meta-key route
  (`activate application launcher`), Escape closing each.
- Lock screen: `loginctl lock-session 1` showed CDE's Motif dialog on the
  Lattice backdrop; `unlock-session` returned to the desktop.
- Arrange Around Console (KGlobalAccel) placed Konsole left and Dolphin in
  the middle above the console; at 1280 px the left column is only ~110 px
  wide (one line of the prompt), the layout itself is correct.
- Alt+Tab: `Walk Through Windows` through KGlobalAccel switched the window;
  the switcher box itself does not show without a held key, so its look on
  X11 is not verified.
- Found on the way (not X11-specific): the workspace buttons' tooltip
  doubles the name ("Arbeitsfläche 1 Arbeitsfläche 1", "Arbeitsfläche 2 2"),
  since "Workspace %1 %2" gets the number and the name, and the console
  names KWin's desktops 2, 3, 4 with the first left empty (`kwinrc`
  `[Desktops] Name_2=2`), which other Plasma parts show as well.
- Screenshot: `screenshots/x11-ubuntu-1280.png` (Apps cascade on X11).

Not verified on X11: the Alt+Tab switcher's look, auto-hide, drag of the
console, a second output, 150/200 % scaling.

Checks of 2026-10-09 (window menu and drop sites, after the split of
main.qml), Fedora VM `plasma-lab`, Plasma 6.7, Wayland, two outputs
(1920×1080 at 0,0 and 1280×800 at 1920,0). Input through QEMU's QMP
`input-send-event` on the HID tablet: its x axis spans both outputs
(3200 px), so `x_abs = x * 32767 / 3200`; screenshots through the hypervisor.

- Right click on a task button in the strip opens TaskMenu (title, Minimize,
  Maximize, Keep Above Others, the four workspaces with the window's own
  marked, All Workspaces, New Workspace, Start New Instance, Close); Plasma's
  applet menu no longer opens with it (a MouseArea for the right button, a
  TapHandler let the press through). Keep Above Others toggled by a real
  click, Maximize through the menu's trigger; Escape closes.
- Left clicks unchanged: a task button minimizes its active window, the
  Terminal and System tiles start Konsole and System Settings.
- With DropTarget's drag source on (`draggable`), clicks on the launcher
  tiles started nothing; reordering by dragging is therefore off
  (`draggable: false`) until that is solved.
- Drop logic exercised from test code, not by a real drag: a file to the
  trash (`kioclient move … trash:/`), Dolphin's desktop entry read as
  launcher (label Dolphin, icon org.kde.dolphin, `app:org.kde.dolphin`),
  a launcher moved from the first place to the third and back.
- No `org.cde.*` or QML messages in the user journal.

Not verified: a real drag of files or applications onto a tile (no drag
source in the VM), the right click in the window list and the workspace
icons, the menu on an upright console.

Checks of 2026-10-09 (launcher tiles and rearranging by drag), VM
`ubuntu-lab` (Plasma 6.6.6, Wayland, 1280×800), the working tree after the
main.qml split, clicks through QEMU's QMP input events, the result read from
the guest's journal (the tile's `systemd-run` unit) and `pgrep konsole`:

- Terminal tile, three clicks each: without pointer movement, with 4 px and
  with 20 px of movement between press and release.
  - `draggable: false` (DropArea only): 3 of 3 launched.
  - `draggable: true` with the DragHandler of the first draft: 0 of 3
    launched, not even the motionless click. The handler in a child of the
    tile's button takes the press; this is what stopped the launchers on
    the host.
  - `draggable: true` with the drag started by the button's press-and-hold
    (the version now in `DropTarget.qml`): 3 of 3 launched.
- Rearranging: hold the Terminal tile for 1.3 s, drag it onto the Editor
  tile, release: the tile's picture followed the pointer, Editor and
  Terminal changed places (`cdecopperrc` leftLaunchers: Apps, Files,
  Editor, Terminal), no terminal was started; dragged back the same way.
- `python3 build.py`, `tests/verify.py`: 38 tests pass.

Checks of 2026-10-09 (minimized windows in the pager), VM `ubuntu-lab`
(Plasma 6.6.6, Wayland, 1280×800), "Each workspace in miniature" set through
the panel script, windows minimized with a KWin script:

- A minimized Konsole appears as a small icon at the lower left of its
  workspace's map, without a frame, on the sunken surface; Dolphin, still
  open, stays a raised rectangle. With two Konsole windows and Kate
  minimized: three icons in a row.
- A click on an icon (after the pointer rested on it) restored Kate and
  made it active, read back from KWin. A click right after moving onto the
  icon did nothing once; not reproduced.
- No messages from Workspaces.qml in the journal. `build.py` fine;
  `tests/verify.py`: 42 of 43 pass, the failing one
  (`StyleManager.test_console_opens_the_window`) belongs to the style
  manager being built in the other session, not to this change.

Checks of 2026-10-09 (Style Manager as a window of its own), VM
`plasma-lab` (Plasma 6.7.5, Wayland), the working tree, clicks through
QEMU's QMP tablet, results read from the manifest and `kreadconfig6`:

- `plasmawindowed org.cde.copper.stylemanager`: one decorated window titled
  "Style Manager" ("Stilverwaltung" under German), in the console's window
  strip, sized to its row of six buttons; the close button ends the
  process. A second start is ignored by plasmawindowed; the console's
  `open.sh` then brings the open window forward (tested with KWrite in
  front).
- System subpanel › Style Manager… opens it (after a shell restart for the
  new SectionPopup.qml). Palette › Broica › Apply: colour scheme
  `CDEBroica`, console, frames and KDE programs recoloured; the window
  reported "The open programs have taken the new style". Palette › Indigo
  › OK with a KWrite started under `QT_QPA_PLATFORMTHEME=generic`: the
  window named KWrite as keeping the old style until restarted (its frame
  and controls had stayed as they were).
- Controls › Floating › Apply and back to Outlined; Window › shadow off ›
  Apply (auroraerc `windowShadow=false`), on again; Backdrop shows the
  installed material tile (Filz) selected and previewed, Pointer and Lock
  Screen open with the state in use. The VM was left as before: Indigo,
  Filz, outlined, copper cursors, CDE's lock screen, shadow on.
- `tests/verify.py`: StyleManager (package, domains, tool options, the
  console's opener, stale.py on a made-up /proc) and the installer round
  trip with the new package pass.

Not verified: the KDE Store edition's fallback to System Settings ›
Colours (no store installation in the VM), GTK 4, Flatpak and Electron
programs in the restart list (only the classification test).

Checks of 2026-10-09 (the system tray's popup, "Status und
Benachrichtigungen"), VM `ubuntu-lab` (Plasma 6.6.6, Wayland, 1280×800),
opened by a QMP click on the console's arrow button:

- Heading: a bar in the selection colour with Motif's shadows of that
  colour, the title in the selection's text colour, as on the console's
  subpanels. Two things were needed: the colour scheme's "Header" group on
  selection colour and text (Plasma's PlasmoidHeading draws in that group),
  and `widgets/plasmoidheading.svg` with the colour fixed in the file: drawn
  through the ColorScheme-Background class the bar stayed in the window
  colour, with the colour scheme re-applied and the SVG caches cleared.
  Every palette generates its own SVG, so the fixed colour follows the
  palette. The colour scheme must be re-applied once after upgrading
  (`apply.sh --palette <name>` does), or the heading keeps the old text
  colour.
- Entries: with "Status icons only behind the console's button" the tray's
  weather, input methods, keyboard layout, screen layout and vault entries
  and, with the network button chosen, the network entry are switched off
  (`extraItems`), recorded in the tray's `cdeDisabledItems`; seven entries
  remained in the VM (the kded crash notifier among them). Not yet checked:
  switching the option off puts them back (written, not clicked).
- System Settings (Colours page) after the change: no header turned copper,
  Kirigami keeps its toolbars on the window colour.
- `tests/verify.py`: 43 pass.
- Icons: `battery`, `battery-full`, `battery-charging`, `battery-low`,
  `battery-caution`, `battery-missing` and `battery-empty` are now aliases
  of the drawn battery levels (the tray's power entry asked for the plain
  name and fell back to Breeze). OneDrive and Solaar keep their own icons.

## Battery, Applications menu, two screens (2026-10-09)

Fedora VM `plasma-lab`, Plasma 6.7.5, Wayland, two outputs (1920×1080 at
0,0 and 1280×800 at 1920,0), real clicks through QMP.

- Battery in the load meter: the VM has no battery, so the installed
  `main.qml` was patched for the test to report 57 % and not plugged in.
  The reading "B" appears in all four small-button styles (LED digits,
  bars in "family", "instruments" and "panel"). Patched to plugged in:
  "auto" hides it, "always" shows it. Without the patch (no battery)
  nothing shows, and the journal has no errors. The settings page shows
  the default "In the load meter while on battery".
- Mouse wheel on the settings pages: it used to change any combo box or
  spin box it passed over while scrolling the page (Qt's default), and
  "Apply" then saved the change. Now `wheelEnabled: false` on all of them:
  twelve wheel steps over the Tiles page scroll it past the launcher lists
  and the Battery box, nothing changes, "Apply" stays disabled. A click
  still opens the Battery box with its three choices.
- Applications menu: a click into the transparent rest of the dialog
  (Wayland keeps both levels' size) was swallowed and the menu stayed
  open. It now closes the menu; clicks on the heading and the categories
  work as before.
- "A console on every screen": the second console was added on screen 2,
  but the layout script stopped at `saved.keys` (Plasma's ConfigFile calls
  it `keyList`). The new console then had none of the settings: another
  clock, no LED field, and the windows of all screens. Fixed: the second
  console is now set up like the first, and its strip shows only the
  windows on its screen. A Konsole window moved there with Meta+Shift+Right
  went from one strip to the other. The Applications menu of the second
  console opens on its screen. Switched off, the second console goes away.
- `tests/verify.py`: 44 pass.

## Store console in German on first start (2026-10-09)

Fedora VM `plasma-lab`, Plasma 6.7.5, the session switched to German
(`LANGUAGE=de`) for the test. With the user's copy of `cde-copper.mo`
removed, the console from the full build stayed English ("WORKSPACES",
"Files"): the store edition only copies that file on its first load, too
late for the strings already shown. The console from `store.py`, put in
place of the installed widget, came up in German right away
("ARBEITSFLÄCHEN", "Dateien", "Papierkorb"), also with only
`plasma_applet_org.cde.copper.frontpanel.mo` in its package and no copy in
the user's locale folder: Plasma reads that catalogue from the package.

## Second console keeps its own settings (2026-10-09)

Fedora VM `plasma-lab`, two outputs. Both consoles mirrored every change
into the same `cdecopperrc [Console]`, so a second console set up
differently overwrote the first one's settings there, and the next
rebuild of the panels (applying the global theme, `apply.sh --panel`)
handed them to the first console. The host showed it: the second
console, created by the version before `keyList`, had no settings at all,
and its dialog had written its defaults into `[Console]`.

Now the console on screen 0 writes `[Console]`, the others
`[Console-<screen>]`, read over `[Console]`, and each console writes its
whole configuration at start, which mended the polluted `[Console]` in the
VM on the first restart. Test: the second console set to the label
"ZWEITE", "instruments" and no names under the tiles. Then the panels
were rebuilt with `layout.js` (without its wallpaper part). The first console
came back unchanged ("CDE / COPPER", LED field, names), the second with
its own settings. The rebuilt consoles also get `everyScreen` from
`AllScreens` again; before, they offered the choice switched off while
two consoles stood.

## Meta, type, Return (2026-10-09)

Fedora VM `plasma-lab`, Wayland, keys through `virsh send-key`. Meta opens
the Applications menu (Plasma's launcher-menu shortcut, the console
provides `org.kde.plasma.launchermenu`). Typing "k" there closed the menu
and opened Find Application with "k" in the search field, keyboard focus
in it; "on" followed. Find Application showed nothing for "kon": its
Kicker `AppsModel { flat: true }` lists only the categories in Plasma 6
(with an empty field: Development, Games, … Utilities). It now uses
Kicker's `RunnerModel` with the `krunner_services` runner: "kon" lists
Konqueror, Kontact, Konsole, …; "kons" puts Konsole first, and Return
started it (`pgrep konsole`: none before, one after).
