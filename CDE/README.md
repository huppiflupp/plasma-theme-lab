# CDE Copper

A contemporary CDE/Motif workstation theme for KDE Plasma 6.

![CDE Copper in the Fedora lab VM](screenshots/desktop-kvantum-1920.png)

The handoff's teal and copper palette meets a more traditional CDE silhouette:
a compact bottom front console, centered window titles, square Motif controls,
hard bevels and original vector workstation icons. Copper identifies the active
window, selected workspace and focused controls. The desktop stays quiet teal.

## Included

- KDE color scheme and 38 Plasma surface SVGs.
- Kvantum widget style with Motif controls: bevelled buttons, sunken fields,
  diamond radio buttons, copper focus frame, default button and selection,
  bevelled scrollbars with arrows, attached tabs and hard-edged menus.
- IBM Plex Sans Condensed for the interface and titles (semibold), IBM Plex
  Mono for Konsole and fixed-width text; both ship with the theme (SIL OFL).
- Aurorae decoration with active/inactive frames, Motif menu and minimize symbols,
  square maximize/restore controls, and a separate close button.
- One front-console plasmoid: clock, launchers, four-workspace switcher, window
  task strip, Places and System subpanels, searchable installed applications,
  audio level, network status, screen locking and session controls.
- Original SVG icon artwork and semantic aliases, with no embedded raster images.
- Konsole profile and color scheme, global-theme bundle, and teal wallpaper.
- User-only installer, ownership manifest and configuration rollback.

## Install

Requires Plasma 6 / Qt 6, Aurorae, Python 3, `kbuildsycoca6`, Plasma apply
utilities, `qdbus-qt6` or `qdbus6`, and the Plasma 5 Support executable data
engine. The Motif controls need the Kvantum style engine (package `kvantum`);
without it the installer falls back to the built-in Qt Windows style and says
so. The fonts are installed per user and need `fc-cache`. Network/audio status uses NetworkManager's
`nmcli` and WirePlumber's `wpctl`. Launchers use Dolphin, Konsole, Kate and the
configured default web/mail applications. A mail client must be configured.

The release archive contains ready-built assets. From its extracted directory:

```sh
bash install.sh --dry-run
bash install.sh
bash apply.sh --panel
```

Log out and back in after applying. `--panel` explicitly replaces the current
panel layout; the installer backs up the previous layout first. Without that
flag, your current panels stay in place. The front console can also be added
as a widget through Plasma's normal widget picker.

Right-click the console and open its settings for top/bottom position and
Always Visible, Auto-hide / Edge Reveal, or Dodge Windows. Popups accept Tab,
Enter, Space and Escape. The task strip scrolls when many windows are open.

## Restore

```sh
bash uninstall.sh
```

This stops/restarts Plasma, restores the configuration saved before the first
installation, then removes only manifest-owned assets. Log out and back in to
fully reload the original decoration and application style. Backups remain in
`~/.local/share/cde-copper-install/`; later install cycles archive them beside it.
Rollback restores whole saved config files, including changes made since the
installation. Inspect that backup before uninstalling a long-lived installation.

An existing unowned `CDECopper` theme is never overwritten. Installation refuses
that collision. No root privileges are used for installation or removal.

## Develop

All project-specific work lives here. The supplied handoff remains unchanged.

```sh
python3 build.py
```

The SVG generators are CDE Copper's own copies under `tools/`; the build never
reaches outside this directory, and the release archive carries the same copies.
The theme shares a repository with NT Legacy, but the two are kept apart on
purpose: a change to one must not alter the other (see `tools/README.md`).
Palette and decoration generation live in `build.py`; original icon geometry
and aliases in `icons.py`; the Kvantum SVG and its configuration in
`kvantum.py`; the console lives in `frontpanel/`; the fonts in `fonts/`.
Generated assets are under `build/`.

All testing was performed in the project's `plasma-lab` VM. See [TESTING.md](TESTING.md).

## Scope

This is version 0.1.0. The application style is a Kvantum theme generated from
the palette in `kvantum.py`, not a compiled Qt style, so it needs Kvantum at
run time. Third-party applications can supply their own controls or
client-side decorations. Less common icon names fall back to
Breeze and then hicolor; the console's core icons and common file-manager icons
are custom SVGs. The console exposes audio/network/session controls, but does
not embed the general-purpose Plasma system tray. Other tray widgets can be
added through Plasma's panel editor. Login/lock-screen replacement and a custom
cursor theme are outside this release. Native Plasma manages panel hiding and
screen-edge reveal; this release does not implement a separate retractable handle.

The console uses a horizontal layout. Very narrow logical screens below 800 px
and multiple physical monitors have not been validated.

## Credits

Source and original artwork: GPL-2.0-or-later. IBM Plex Sans Condensed and IBM
Plex Mono are copyright IBM Corp. under the SIL Open Font License 1.1
(`fonts/IBMPlex/LICENSE-OFL.txt`). Plasma SVG and Aurorae generation
reuse the lab's tools by huppiflupp. CDE/Motif is the design inspiration; no CDE
or Microsoft icon files are copied. The supplied reference images are not
installed or included in the release.

Implementation follows KDE's [panel scripting API](https://develop.kde.org/docs/plasma/scripting/api/)
and the QML API metadata installed in the test VM.
