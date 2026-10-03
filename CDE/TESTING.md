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
in System Settings, keyboard navigation of the Applications menu, the console
at the top edge.

The project VM was restored to the original configuration after the destructive
installation test. The last visual run deliberately leaves CDE Copper applied
in the VM so it can be opened with `vm/vmctl.sh viewer`; remove it with
`./uninstall.sh` inside `/home/tester/cde-copper` when finished viewing.

Known scope: the Motif controls need Kvantum (fallback: Qt Windows style); the
login screen, cursor theme and third-party client-side decorations are not
replaced. The custom front console with the Plasma system tray beside it is
the supported panel experience.
