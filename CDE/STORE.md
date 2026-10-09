# KDE Store: the one entry

CDE Copper goes to https://store.kde.org as a single product carrying the
release archive of `package.py` (`dist/cde-copper-<version>.tar.xz`), which
installs with `install.sh` like a download from the project page. The
store's own "Install" button cannot run a script, so the entry says so in
its first lines. (`store.py` still builds the split edition of KPackage
archives, one per store category, should that ever be wanted.)

## Entry

| Field | Value |
|---|---|
| Category | Global Themes (Plasma 6) |
| Title | CDE Copper |
| License | GPLv2+ (fonts: SIL OFL 1.1; CDE backdrops: CC BY-SA 3.0, The Open Group) |
| Source | https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE |
| Homepage | the same |
| Download file | `cde-copper-<version>.tar.xz` from `dist/`; if the store refuses the size, a GitHub release and the store's external link instead |
| Logo | `screenshots/kde-look/logo-512.png` |
| Pictures | `screenshots/kde-look/overview.png` first, then the five GIFs in the order of their names |
| Tags | cde, motif, retro, unix, workstation, plasma6 |

## Description

```
CDE Copper is a complete Common Desktop Environment for Plasma 6: the front
console with launchers, subpanels, a workspace switch and the window list,
the Motif window frame, Motif controls in Qt programs (Kvantum), CDE's 37
palettes with matching icons and backdrops, CDE's lock screen, saved window
layouts, mouse cursors after the X11 cursor font, IBM Plex as the interface
font, and a day/night pair of global themes.

INSTALL: this is not a package the store can install with "Install" or "Get
New…". Download the archive, unpack it and run from the unpacked folder:

    bash install.sh
    bash apply.sh --panel

then log out and back in. "install.sh --dry-run" lists what would be
installed; "python3 manage.py check" names the optional parts missing on
your system (Kvantum for the Motif controls, nmcli, wpctl, Spectacle…).
Everything goes into your home folder; "bash uninstall.sh" removes it again
and restores your previous configuration. Palettes, backdrops and pictures
are switched in the console's Style Manager (System tile) or with
"bash apply.sh --palette NorthernSky --backdrop picture:polarlicht".

Requirements: Plasma 6.6 or newer (tested on Fedora 44 / Plasma 6.7 and
Kubuntu 26.04 / Plasma 6.6, Wayland and X11), Python 3, the Plasma 5
Support data engine (plasma5support), and Kvantum for the Motif controls
(qt6-style-kvantum on Ubuntu, kvantum on Fedora); without it the theme
falls back to the Qt Windows style and says so.

Source, issues and the full documentation (README, TESTING):
https://github.com/huppiflupp/plasma-theme-lab/tree/main/CDE
```

## Before uploading

- Version in `build.py` and `po/README.md` raised, `python3 build.py`,
  `python3 tests/verify.py`, `python3 package.py` (RELEASE-CHECKLIST.md).
- The archive unpacked somewhere else and `bash install.sh --dry-run` run
  from there once.
- Changelog on the store: the version's lines from the commit log, short.
