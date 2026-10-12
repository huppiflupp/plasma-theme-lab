# CDE Copper release checklist

Work through this before every new version number. Whatever was not checked is
stated in the commit as "not checked" – never silently left out. TESTING.md stays
the log; this list is the test plan.

## Always (every version)

- [ ] `python3 build.py` without errors, `python3 tests/verify.py` green
- [ ] `msgfmt --check --statistics -o /dev/null po/de.po`: 0 fuzzy, 0 untranslated
- [ ] `python3 manage.py check` on the test system: output plausible
- [ ] Installed in the VM `plasma-lab` (Fedora, Plasma 6.7), Plasma restarted:
      `journalctl --user -u plasma-plasmashell` without new QML errors/warnings
      from `org.cde.copper.*`
- [ ] Looked at a screenshot of the console (`vm/vmctl.sh shot`): all tiles present,
      nothing cut off, no empty space
- [ ] Triggered the changed function by hand (click, keyboard, popup closes with Esc)
- [ ] No private names/addresses in the product (test `test_no_private_hosts_in_product`)
- [ ] Version bumped in `build.py`/`po/README.md`, README and TESTING.md updated

## For changes to the console (frontpanel/)

- [ ] Looked at the console at the bottom, top, left, right (vertical!)
- [ ] Console size 1.0 and 1.5; contrast "hard" on/off
- [ ] One light and one dark palette (e.g. Copper and Graphite/Black)
- [ ] Open the settings dialog, change an option, OK – the value arrives

## For changes to palettes, icons, style (palettes/, icons.py, kvantum.py)

- [ ] `screenshots/icon-sheet-*.png` regenerated and looked at
- [ ] Icons at 16, 22 and scalable recognisable on light and dark backgrounds
- [ ] Looked at a Qt dialog (Dolphin "Open") and a GTK program

## Additionally before a store release

- [ ] Ubuntu VM `ubuntu-lab` (Plasma 6.6): install, apply, uninstall
- [ ] Uninstalling restores the configuration (test + visual check)
- [ ] README screenshots match the current defaults (e.g. the "Layouts" launcher)
- [ ] Open items from REVIEW-*.md reviewed

## Known unchecked (until someone does it)

- X11 session
- Two physical screens ("one console per screen")
- Screen reader; keyboard operation of the application menu and auto-hide
