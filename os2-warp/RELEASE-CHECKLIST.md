# Warp Legacy release checklist

Before every new version number. Whatever was not checked is said in the
commit as "not checked", never left out silently; TESTING.md is the log.

## Every version

- [ ] `python3 package.py` (a full build, no `WARP_SKIP_ICONS`) without errors
- [ ] Both archives (`warp-legacy-…`, `warp-legacy-neon-…`) install with
      `kpackagetool6 -t Plasma/LookAndFeel -i` (the store's "Get New…")
- [ ] `msgfmt --check --statistics -o /dev/null po/de.po`: 0 fuzzy, 0 untranslated
- [ ] Installed from the archive in the VM `plasma-lab` (Fedora, Plasma 6.7),
      `journalctl --user` without new QML errors from `org.warplegacy.*`
- [ ] The changed parts triggered by hand and looked at on a screenshot
- [ ] Version raised in `build.py` and the plasmoids' `metadata.json`, tag
      `warp-legacy-<version>`

## Install and uninstall (a release, or changes to install.sh/uninstall.sh)

From a clean snapshot, on Fedora (`plasma-lab`) and Ubuntu
(`LAB_ENV=ubuntu.env`, Kubuntu 26.04):

- [ ] Unpack the Neon archive, `./install.sh --apply neon --layout`, log out and in
- [ ] The classic archive the same way (`--apply --layout`); with both,
      the Warp menu switches classic ↔ Neon, with Neon alone Neon ↔ Neon Blue
- [ ] Neon in place: panels, frame, Kvantum WarpNeon, icons, cursors,
      Konsole profile, wallpaper, lock screen
- [ ] Global Theme switched in System Settings, logged in again:
      warp-legacy-sync follows (Kvantum, Konsole, LibreOffice)
- [ ] `./uninstall.sh`, log out and in: settings as before (compare
      `kreadconfig6` values and a screenshot with the ones before), no files
      left under `~/.local/share` / `~/.config` that name Warp Legacy
- [ ] Without Kvantum and without LibreOffice installed: install.sh only
      notes it, nothing fails

## Panels and plasmoids

- [ ] Each panel at its edge, in classic and Neon
- [ ] Meta opens the Warp menu; `kon` + Return starts Konsole; arrows with
      and without text
- [ ] Tab Launcher's drawer slides in and out, clicks reach it afterwards
