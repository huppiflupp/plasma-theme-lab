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

The project VM was restored to the original configuration after the destructive
installation test. The last visual run deliberately leaves CDE Copper applied
in the VM so it can be opened with `vm/vmctl.sh viewer`; remove it with
`./uninstall.sh` inside `/home/tester/cde-copper` when finished viewing.

Known scope: this release uses the native Qt Windows widget style, relies on
Aurorae for the KWin frame, and does not replace the general system tray,
login screen, cursor theme, or third-party client-side decorations. The custom
front console is the supported panel experience.
