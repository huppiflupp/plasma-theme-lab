# Target structure for NiceOS9

A proposal, derived from Breeze and [Klassy](https://github.com/paulmcauley/klassy)
(the best-structured third-party project for Plasma 6).

Not implemented yet — first the current state is measured in the VM, then
restructured. Otherwise you restructure without knowing what was broken before.

---

## Current state

```
NiceOS9-theme/
├── install.sh              479 lines, does everything at once, calls sudo
├── install-grub.sh         writes to /boot/grub2/
├── install-plymouth.sh     rebuilds the initramfs
├── install-sddm.sh         writes to /usr/share/sddm/
├── uninstall.sh            deletes files, does not reset configuration
├── desktoptheme/           3 variants × 1 SVG   (Breeze: 43)
├── plasma/                 2 folders, purpose unclear — duplicate of desktoptheme?
├── look-and-feel/          3 variants, with layouts/ and dead lockscreen/
├── aurorae/                3 decorations
├── color-schemes/          4 colour schemes
├── icons/                  1543 PNG
├── fonts/, wallpapers/, grub/, plymouth/, sddm/, previews/, screenshots/
└── autostart/              panel-nofloat with hard-wired /home/seeas
```

### The eight findings

| # | Finding | Effect |
|---|---|---|
| 1 | `look-and-feel/*/contents/layouts/*.js` | can replace the user's panels — **not reversible**, but only after explicit consent (see below) |
| 2 | One installer for `$HOME` **and** GRUB/Plymouth/SDDM | a single run can stop the machine from booting |
| 3 | 1 instead of 43 widget SVGs | the look is 97 % Breeze |
| 4 | `look-and-feel/*/contents/lockscreen/` | dead code — Plasma 6 loads the lock screen from the shell package |
| 5 | `uninstall.sh` only deletes files | **demonstrated in the VM**, see below |
| 6 | `sed HOME_PLACEHOLDER`, hard-wired `/home/seeas` | breaks with different paths |
| 7 | `defaults` sets `cursorTheme=XCursor-Pro-Red` | the installer does not ship the cursor, even though it is in the repo |
| 8 | Metadata incomplete | fixed — `Version`, `License`, `Website`, `Authors` added |

### Finding 5, demonstrated rather than claimed

Test run `tests/runs/niceos9-20260807-195105`, sequence: install →
apply → reboot → uninstall → reboot.

After `uninstall.sh` **and** a reboot:

```
Global Theme   : [niceos9-bright]     ← points to a deleted directory
Plasma Style   : []
Colour scheme  : []
Icons          : []
Style          : []
Decoration     : []

$ ls ~/.local/share/plasma/look-and-feel/niceos9-bright
ls: cannot access: No such file or directory
```

Visible: a light panel without a matching theme, **empty system tray** —
volume, network and clipboard are missing. No crash, but a
desktop you have to put back together by hand.

Screenshots in the test run directory.

### Side finding on applying

A Global Theme only takes full effect **after the session has been
restarted**. Right after `plasma-apply-lookandfeel --apply`
only parts take hold (icons yes, Plasma Style and colour scheme no), and
nothing is in the configuration files yet — Plasma keeps the values in memory
until the session ends.

For tests this means: without a restart you measure an intermediate state.
For the README it means: the hint "log out and back in" belongs
in it.

On top of that, two things that are **right** and should stay that way: the group
`org.kde.kdecoration2` (still correct under KDecoration3) and the structure of
the existing `panel-background.svg` — 9-patch complete, colour scheme
bound.

---

## Target structure

```
niceos9/
├── Makefile                    one version number, .svgz at build time
├── install.sh                  $HOME only, no sudo — only calls make
├── uninstall.sh                from the manifest, with configuration rollback
├── README.md  LICENSE  LICENSES/  REUSE.toml
│
├── desktoptheme/
│   └── niceos9/                ONE variant with SVGs
│       ├── metadata.json.in
│       ├── plasmarc
│       ├── colors
│       ├── widgets/*.svg       goal: the 14 from priority 1+2
│       └── dialogs/background.svg
│
├── color-schemes/              this is where the variants come from
│   ├── NiceOS9Bright.colors
│   ├── NiceOS9Dark.colors
│   └── NiceOS8Charcoal.colors
│
├── aurorae/ChicagoNine{,Dark,Eight}/
│
├── look-and-feel/              three bundles, all on the same Plasma Style
│   └── com.github.huppiflupp.niceos9-{bright,dark,charcoal}/
│       ├── metadata.json.in
│       └── contents/
│           ├── defaults
│           └── previews/
│                               ← NO layouts/, NO lockscreen/
│
├── layout-templates/           the panel as an offer instead of a must
│   └── org.huppiflupp.niceos9.panel/
│
├── icons/nineicons-redux/
├── fonts/  wallpapers/
│
├── tools/
│   ├── lint-plasma-svg.py      → already done in plasma-theme-lab/tools/
│   └── gen-colors.py           colour schemes from a palette
│
└── risky/                      separate, own warning, default = no
    ├── README.md               "these scripts can stop the machine from booting"
    ├── install-sddm.sh         + detection: plasmalogin has no QML themes
    ├── install-plymouth.sh
    └── install-grub.sh
```

## The seven changes

**1 — `layouts/` stays, but with a safety net.**

First assessment revised. The panel is part of the Mac OS 9 look; a
theme without the bar at the top is incomplete. And KDE already protects in
three places: [Source: `kcms/lookandfeel/kcm.cpp`, `SimpleOptions.qml`]

```cpp
// But do not select layout contents by default if there appaerance settings
if (m_themeContents & KLookAndFeelManager::AppearanceSettings) {
    resetContents &= ~KLookAndFeelManager::LayoutSettings;
}
```

- the "Desktop and window layout" checkbox is **not ticked
  by default** as soon as the theme also provides appearance settings
- below it is a red warning, visible as soon as you tick it
- `plasma-apply-lookandfeel --apply` does not touch the layout without
  `--resetLayout`

What is missing is the **way back**. Before installing, the installer should
back up the panel configuration:

```bash
BACKUP="$HOME/.local/share/niceos9/panel-backup-$(date +%F-%H%M).rc"
mkdir -p "$(dirname "$BACKUP")"
cp -a "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "$BACKUP" 2>/dev/null
echo "Panel configuration backed up: $BACKUP"
```

That turns "irreversible" into "copy one file back and log in
again". That is the real flaw — not the layout itself.

In addition, a `Plasma/LayoutTemplate` for people who want to keep their
configured panel and only try the NiceOS9 arrangement alongside it.
An addition, not a replacement.

The `HOME_PLACEHOLDER` `sed` hack in the layout script therefore remains
and should be solved separately — the wallpaper can be set in the script
via relative resolution instead of an absolute path.

**2 — Risky scripts into `risky/`.**
`install.sh` no longer asks for sudo and touches nothing outside
`$HOME`. Anyone who wants GRUB calls `risky/install-grub.sh` deliberately.
In addition, `install-sddm.sh` gets a check whether SDDM is running at all —
on Fedora 44 and Nobara it is `plasmalogin`, which knows no QML themes.

**3 — One variant with SVGs.**
`desktoptheme/niceos9` is the only one with graphics. `dark` and `charcoal`
disappear as Plasma Styles; the colour schemes take over their effect.
Prerequisite: the SVGs use `class="ColorScheme-*"` + `fill="currentColor"`.
The existing `panel-background.svg` already does.

This reduces three trees to maintain to one — the condition for
14 new SVGs being worth it at all.

**4 — Delete `lockscreen/`.** Dead code since Plasma 6.

**5 — `uninstall.sh` with rollback.**
Before the first change, the installer saves the old values from
`plasmarc`, `kdeglobals` and `kwinrc` into a `restore.sh`. The
uninstaller calls it. This one file is the difference between
"let me try this out" and "I don't dare".

**6 — Makefile instead of `cp -r`.**
One version number for all packages, `.svgz` at build time, installation via
`kpackagetool6` (checks the metadata), uninstallation from the manifest.

**7 — Clarify `plasma/`.**
The folder `plasma/niceos9-{bright,dark}/` contains `colors`, `metadata.json`
and `plasmarc` — the same shape as `desktoptheme/`, but the installer
copies it nowhere. Probably a duplicate from an earlier
version. **Clarify before deleting** — if it has a purpose, that should be
documented.

## The SVG work

The linter says what is missing:

```
Priority 1:  dialogs/background.svg, widgets/background.svg
Priority 2:  tooltip, listitem, viewitem, button, lineedit, checkmarks,
             radiobutton, switch, scrollbar, slider, frame, toolbar
```

14 files. After that it is a theme in its own right and no longer Breeze
with a retro panel. The remaining 39 are polish.

That is design work, not structural work — it belongs after the
restructuring, not before.

## Order

1. Measure the current state in the VM (test run against the current repo)
2. Restructure — points 1, 2, 4, 5, 7 (mechanical, no design)
3. Test again: same look, but safe to try out?
4. Point 3 (one variant) — needs a decision about the colour schemes
5. Point 6 (Makefile)
6. Only then the 14 SVGs
