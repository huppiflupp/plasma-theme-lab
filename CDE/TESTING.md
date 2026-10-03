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
- Lit segments and colon carry a black edge one pixel wide, at every size;
  it lies in the one-pixel gap between segments and covers no neighbour.
  Checked at 75, 100, 125 and 150 %, and at 125 % with seconds.
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
