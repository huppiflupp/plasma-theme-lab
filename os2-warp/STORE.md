# KDE Store

Two entries on store.kde.org, one per package that `package.py` makes;
each is complete (panels, all wallpapers, fonts, LibreOffice and
Firefox colours, install.sh). Since 25.10.2026, replacing the split
edition below (the user's choice: two entries, not fifteen).

| Entry | File | Category |
|---|---|---|
| **Warp Legacy** | `warp-legacy-<version>.tar.xz` (27 MB) | Global Themes (Plasma 6) |
| **Warp Legacy Neon** | `warp-legacy-neon-<version>.tar.xz` (56 MB) | Global Themes (Plasma 6) |

Licence GPL-2.0-or-later; the Source field links
https://github.com/huppiflupp/warp-legacy. Pictures: the GIFs in
`screenshots/store/classic/` and `screenshots/store/neon/`
(`tools/store-gifs.py`), the PNGs `screenshots/warp-*-2026-10.png`.
Each entry carries only its own archive: no other file, so "Get New…"
cannot pick a wrong one (UPLOAD.md in the repository's root, NT Legacy).

## How the archive works in "Get New…"

The Global Themes category hands the file to kpackagetool6, which wants
one package: a single folder with a `metadata.json`. `package.py` puts
the family's main global theme (`metadata.json`, `contents/`) into the
archive's folder, beside install.sh and build/:

- "Get New…" installs it as the global theme Warp Legacy or Warp Legacy
  Neon, with its name and preview, into
  `~/.local/share/plasma/look-and-feel/org.warplegacy[.neon].desktop/`.
  The rest (panels, icons, frame, Plasma style, wallpapers) comes from
  `install.sh` in that folder; the description says so.
- Unpacked by hand, it is the ordinary release archive.
- The archive is GNU tar: kpackagetool6 could not open the Neon archive
  in Python's default PAX format ("cannot open the package file"),
  the classic one it could (Fedora VM, 25.10.2026).
- `uninstall.sh` removes the folder "Get New…" made: without its
  metadata.json, which uninstall removes with the theme's files, the
  folder would turn every global theme in System Settings into "Breeze".

## Pictures

`tools/store-gifs.py` joins the screenshots into each entry's GIFs,
1920×1080 with a label on each frame. `screenshots/store/classic/`:
`1-warp-legacy.gif` (the variant, the taskbar with the compact box or the
full Control Strip, other pictures and buttons). `screenshots/store/neon/`:
`1-neon-and-neon-blue.gif` (both, and their panels), `2-neon-dark.gif`
and `3-neon-blue-dark.gif` (on dark pictures with the other button
looks). The screenshots come from the Fedora VM in an English session at
1920×1080 (`tools/demo-scene.sh --panels screenshots`, `concept` or
`bottom`; the button look is `buttonStyle` in `auroraerc`, group
`kwin4_decoration_qml_warplegacy…`). The VM has no internet: Firefox and
the weather went through a CONNECT proxy on the host that let only
Wikipedia and wttr.in through, reached by an SSH reverse tunnel.

## Description, Warp Legacy

> OS/2 Warp 4 for Plasma 6: Warp 4's grey and blue, the OS/2 window
> frame with six button looks, the Warp Taskbar, the Warp Bar after the
> WarpCenter, the LaunchPad, the Control Strip (as a compact box with the
> weather or the full strip) and the Tab Launcher, Warp 4's icons, OS/2
> controls in programs (Kvantum), Konsole, LibreOffice and Firefox
> colours, and 43 wallpapers. The night variants are the entry Warp
> Legacy Neon; both can be installed side by side, the Warp menu then
> switches between them.
>
> Install: "Get New…" puts the global theme in place. For everything
> else run, once:
>
> `~/.local/share/plasma/look-and-feel/org.warplegacy.desktop/install.sh --apply --layout`
>
> then log out and in. Or download the archive, unpack it and run
> `./install.sh --apply --layout` inside. `uninstall.sh` beside it puts
> back the settings from before.
>
> Requirements: Plasma 6 (tested on Fedora 44 / Plasma 6.7 and Kubuntu
> 26.04 / Plasma 6.6); Kvantum for the program style (package `kvantum`).
> Not affiliated with IBM, Arca Noae or Stardock; everything is drawn
> anew.

## Description, Warp Legacy Neon

> OS/2 at night for Plasma 6, in two colours: Neon, navy with cyan and
> violet glowing edges, and Neon Blue, the same night in electric blue
> with pink accents. The OS/2 window frame with a slow light running
> round it and six button looks, the Warp Taskbar, the Warp Bar, the
> LaunchPad, the Control Strip (compact box with the weather, or the full
> strip) and the Tab Launcher, glowing icons, neon mouse cursors, Kvantum,
> Konsole, LibreOffice and Firefox colours, and 43 wallpapers. The Warp
> menu switches between Neon and Neon Blue without logging out. The
> classic grey is the entry Warp Legacy.
>
> Install: "Get New…" puts the global theme in place. For everything
> else run, once:
>
> `~/.local/share/plasma/look-and-feel/org.warplegacy.neon.desktop/install.sh --apply --layout`
>
> (`--apply neon-blue` for Neon Blue), then log out and in. Or download
> the archive, unpack it and run `./install.sh --apply --layout` inside.
> `uninstall.sh` beside it puts back the settings from before.
>
> Requirements: Plasma 6 (tested on Fedora 44 / Plasma 6.7 and Kubuntu
> 26.04 / Plasma 6.6); Kvantum for the program style (package `kvantum`).
> Not affiliated with IBM, Arca Noae or Stardock; everything is drawn
> anew.

## The split edition (store.py, not published)

`store.py` (copied from CDE Copper's, see its head) splits the built theme
into one archive per KDE Store entry, so that System Settings › Global
Theme › "Get New…" can install Warp Legacy without `install.sh`: the two
global themes name the other entries as dependencies
(`X-KPackage-Dependencies`, `kns://<knsrc>/api.kde-look.org/<id>`), and
KPackage fetches them along.

```bash
python3 build.py                          # a full build, no WARP_SKIP_ICONS
python3 store.py                          # dist/store/<version>/, no dependencies yet
# upload the parts, write their ids into store-ids.json, then
python3 store.py --ids store-ids.json     # the global themes with dependencies
```

`store.py` reads `build/` and never builds; it stops and names what is
missing when `build/` is half-built or a quick one without the first Neon
icon set. `dist/store/<version>/UPLOAD.md` lists every entry with file,
category, title and description; upload the global themes last.

Warp Legacy Neon Blue (the third variant, 21.10.2026) is not in the store
edition yet: it would need a frame of its own from gen-warp-aurorae.py, its
Plasma style and the blue cursors as further entries. The release archive
has it.

### The entries

| Part | Archive | Category (knsrc) | Dependency of |
|---|---|---|---|
| Warp Bar, LaunchPad, Control Strip, Tab Launcher, Warp Taskbar | `warp-legacy-<panel>-<v>.tar.gz`, one each | Plasma 6 Extensions | both |
| Plasma style, classic / Neon | `warp-legacy[-neon]-plasma-style-<v>.tar.gz` | Plasma Theme | classic / Neon |
| Window frame (SVG Aurorae, both variants) | `warp-legacy-window-frame-<v>.tar.gz` | Plasma 6 Window Decorations | both |
| Colour schemes (both) | `warp-legacy-colors-<v>.tar.gz` | KDE Color Scheme KDE4 | both |
| Icons, classic | `warp-legacy-icons-<v>.tar.gz` (about 3 MB) | KDE Icon Theme | classic |
| Icons, Neon (three sets, the violet one inherits the other two) | `warp-legacy-neon-icons-<v>.tar.gz` (about 31 MB) | KDE Icon Theme | Neon |
| Mouse cursors, Neon | `WarpLegacyNeonCursors.tar.gz` (keep the name) | X11 Mouse Theme | Neon |
| Pictures (39 and two plain desktops) | `warp-legacy-wallpapers-<v>.tar.gz` (about 22 MB) | KDE Wallpaper (other) | both |
| Kvantum (optional) | `warp-legacy-kvantum-<v>.tar.gz` | Kvantum | — |
| Konsole (optional) | `warp-legacy-konsole-<v>.tar.gz` | — | — |

Classic uses Breeze's cursors, which every Plasma has. The store
documents no size limit; the Neon icons are the largest archive. Should
the store refuse one, the release archive on GitHub and the store's
external link are the way out (as CDE/STORE.md describes).

### What the store edition changes

- **Global themes:** `widgetStyle=Breeze` instead of Kvantum; the SVG frame
  (`__aurorae__svg__WarpLegacy`, `…WarpLegacyNeon`) instead of the QML
  one; no font keys (IBM Plex is not in the store edition, so the user's
  fonts stay). Icons, cursors, Plasma style, colours and wallpaper name
  only parts that are dependencies.
- **Window frame:** an approximation drawn by `tools/gen-warp-aurorae.py`
  for the store's "Window Decorations" category, which installs SVG
  Aurorae themes only: Warp 4's buttons, the title bar between them,
  OS/2's edges, Neon's pink corners and glow rings. Missing: the other
  five button looks and the settings page, the gradients of Neon's frame
  line, the glow of the glyphs, the window icon's own look.
- **Plasmoids:** each carries its German translation as
  `plasma_applet_<id>` in `contents/locale` (install.sh puts the shared
  `warp-legacy` catalogue into `~/.local/share/locale`, which the store
  cannot). The Warp menu's "Switch to Warp Legacy Neon" runs
  `warp-legacy-switch` when install.sh brought it, otherwise only
  `plasma-apply-lookandfeel` (the global theme alone; Kvantum, Konsole,
  LibreOffice do not follow).

### What it cannot do

Everything `install.sh` does beyond copying packages:

- `warp-legacy-sync` at login, which keeps Kvantum, the widget style and
  icons in kdeglobals, Konsole, LibreOffice, the System Monitor's colours
  and the wallpaper in step with the chosen variant;
- the button order (close left of hide and maximize): Plasma does not take
  it from a global theme; set it by hand in System Settings › Window
  Decorations › Titlebar Buttons;
- Kvantum: an optional archive for Kvantum Manager (install the folders
  `Warp` and `WarpNeon`, choose one, then Application Style "kvantum");
- Konsole: KDE has no "Get New…" for Konsole schemes; the optional archive
  is unpacked into `~/.local/share/konsole` (profiles without IBM Plex Mono);
- LibreOffice's application colours and the Firefox/Chrome themes;
- the IBM Plex fonts, the neon lock screen picture, four workspaces;
- `uninstall.sh`'s restoring of the settings before: store packages are
  removed in "Get New…", the settings stay as the last theme left them.
