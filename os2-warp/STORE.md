# KDE Store edition

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

## The entries

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

## What the store edition changes

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

## What it cannot do

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

## Pictures

`tools/store-gifs.py` joins the screenshots into the entry's GIFs in
`screenshots/store/`, 1920×1080 with a label on each frame:
`1-three-variants.gif` (the three variants, classic on other pictures),
`2-panels.gif` (the taskbar with the compact box or the full Control Strip
in each variant), `3-neon-dark.gif` and `4-neon-blue-dark.gif` (the Neons
on dark pictures with the other button styles). The screenshots come from
the VM in an English session (`tools/demo-scene.sh --panels concept` or
`bottom`).
