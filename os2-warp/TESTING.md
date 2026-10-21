# Warp Legacy test log

Newest first. What was tested where, and what was not.

## After 0.4.1 — 21.10.2026, open points

**Kubuntu 26.04** (`ubuntu-lab`), archive 0.4.1:

- Without LibreOffice (purged offline): `install.sh --apply neon --layout`,
  `warp-legacy-switch classic`, `uninstall.sh` all exit 0, no tracebacks;
  warp-legacy-sync runs clean at login.
- Firefox 157 (Snap): `firefox-apply.sh` finds the Snap profile, refuses
  while Firefox runs; Neon and classic look right, `remove` cleans up.
  Chrome/Chromium: not in the VM, not installable offline: not tested.
- Lock screen locked for real: Neon readable. Classic was not: the greeter
  takes its clock colour from the Plasma style's button text (black in
  classic), on the black tubes. Classic now locks on the tubes on OS/2
  grey (`neon-roehren-hell`); checked on Fedora 44 (plasma-lab): readable.
- Found: uninstall.sh's Firefox note pointed at the script it deleted next;
  it now stops while Firefox wears the theme (`--keep-firefox` to go on).
  A build disturbed by a parallel one packed without an icon set:
  package.py now refuses an incomplete build/.

**Fedora 44** (`plasma-lab`): the Warp menu's switch, Neon → classic →
Neon three times, no crash (a first version without restarting
plasmashell crashed it in Kirigami's PlasmaTheme::syncColors). Neon's
violet selection in System Settings.

## 0.4.1 — 21.10.2026, release archive

**Kubuntu 26.04.1** (`ubuntu-lab`, Plasma 6.6.6, Qt 6.10.2, Wayland, no
Kvantum, no numpy, LibreOffice without a profile), from snapshot `clean`:

- Archive unpacked, `./install.sh --apply neon --layout`, then `--apply`,
  then `--apply neon` again: all exit 0; `kvantum.none` recorded once.
- After a reboot: taskbar, Control Strip, Tab Launcher (slid in), Neon
  frame, icons, cursors, Konsole profile (transparent), wallpaper, lock
  screen picture; no QML errors from `org.warplegacy.*`.
- Meta, `kon`, Return: Konsole starts.
- `./uninstall.sh`: the 19 recorded settings, cursor theme, Konsole profile
  and workspaces as before; appletsrc and plasmashellrc byte for byte. No
  `~/.config/Kvantum`, no `~/.local/share/warp-legacy`, no
  `plasma-systemmonitor`, no style cache. `~/.config/libreoffice` stays
  (made by unopkg, without Warp Legacy's files).
- Left by Plasma's own global theme switch, not Warp Legacy's: in
  `kdedefaults/kwinrc` `[TabBox] LayoutName`, `BorderSize`; `kdeglobals`
  `[KDE] contrast`; `kwinrc` `[Tiling]` of the added workspaces.
- First run of 0.4.0 found: the taskbar and the Warp menu did not load on
  Qt 6.10 (`short`, a reserved word, in common/DesktopMenu.qml); a second
  install recorded Warp Legacy's own Kvantum file as "before"; an empty
  `plasma-systemmonitor` folder and the style cache were left. Fixed.

**Fedora 44** (`plasma-lab`, Plasma 6.7.4, snapshot `clean`, Kvantum
installed from local RPMs), archive 0.4.0:

- `./install.sh --apply neon --layout`, reboot: every part of Neon in
  place, Kvantum WarpNeon, LibreOffice "Warp Legacy Neon"; no QML errors.
- Meta, `kon`, Return: Konsole starts.
- `plasma-apply-lookandfeel -a org.warplegacy.desktop`, reboot:
  warp-legacy-sync took Kvantum, Konsole, LibreOffice, icons, wallpaper
  along to classic.
- `./uninstall.sh`, reboot: all recorded settings as before.
- Without Kvantum: install.sh notes it, exit 0.
- Found: the Warp menu's history, an empty kvantum.kvconfig and LibreOffice
  extension copies (one per login) left behind; the open drawer over new
  windows' title bars. Fixed in 0.4.1 (checked singly, not in a full run).

Not tested: without LibreOffice; Firefox and Chrome; the lock screen
actually locked; the arrow keys in the menu and the drawer on Ubuntu;
Kvantum's look on Ubuntu (not installed there).
