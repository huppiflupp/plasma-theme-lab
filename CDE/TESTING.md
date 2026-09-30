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

The project VM was restored to the original configuration after the destructive
installation test. The last visual run deliberately leaves CDE Copper applied
in the VM so it can be opened with `vm/vmctl.sh viewer`; remove it with
`./uninstall.sh` inside `/home/tester/cde-copper` when finished viewing.

Known scope: this release uses the native Qt Windows widget style, relies on
Aurorae for the KWin frame, and does not replace the general system tray,
login screen, cursor theme, or third-party client-side decorations. The custom
front console is the supported panel experience.
