# Reference card

Everything you need to look up, on one page. Verified on Plasma 6.7.3.

---

## Paths

| What | Per user (`~/.local/share/`) | System-wide (`/usr/share/`) |
|---|---|---|
| Plasma Style | `plasma/desktoptheme/<name>/` | same |
| Look-and-Feel | `plasma/look-and-feel/<id>/` | same |
| Layout template | `plasma/layout-templates/<id>/` | same |
| Color scheme | `color-schemes/<Name>.colors` | same |
| Aurorae | `aurorae/themes/<name>/` | same |
| Icons / cursors | `icons/<name>/` | same |
| Wallpapers | `wallpapers/<name>/` | same |
| Fonts | `fonts/` | `/usr/share/fonts/` |
| Lock screen | — | `plasma/shells/org.kde.plasma.desktop/contents/lockscreen/` |
| SDDM themes | — | `/usr/share/sddm/themes/<name>/` |

Cache: `~/.cache/plasma_theme_<name>_v<version>.kcache`, `~/.cache/ksvg-elements`

## Commands

```bash
# Apply
plasma-apply-desktoptheme <name>          # --list-themes
plasma-apply-colorscheme <Name>
plasma-apply-lookandfeel --apply <id>     # --list, --resetLayout (CAUTION)
plasma-apply-cursortheme <name>
plasma-apply-wallpaperimage <file>
/usr/libexec/plasma-apply-aurorae <name>

# Package management
kpackagetool6 -t Plasma/Theme -i|-u|-r|-l|-s <target>
kpackagetool6 --list-types

# Read/write configuration
kreadconfig6  --file <file> --group <group> --key <key>
kwriteconfig6 --file <file> --group <group> --key <key> <value>

# Reload
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service

# Single test
plasmawindowed org.kde.plasma.digitalclock
ksplashqml --test <id>
kwin_wayland --virtual --width 1920 --height 1080 --exit-with-session <script>
```

**Does not exist:** `kpackagetool6 --validate`, `--generate-index`.

## Configuration keys

| Layer | File | Group | Key | Breeze value |
|---|---|---|---|---|
| Plasma Style | `plasmarc` | `Theme` | `name` | `default` |
| Color scheme | `kdeglobals` | `General` | `ColorScheme` | `BreezeLight` |
| Application style | `kdeglobals` | `KDE` | `widgetStyle` | `Breeze` |
| Icons | `kdeglobals` | `Icons` | `Theme` | `breeze` |
| Global theme | `kdeglobals` | `KDE` | `LookAndFeelPackage` | `org.kde.breeze.desktop` |
| Splash screen | `ksplashrc` | `KSplash` | `Theme` | `org.kde.breeze.desktop` |
| Decoration | `kwinrc` | `org.kde.kdecoration2` | `library` | `org.kde.breeze` |
| Decoration | `kwinrc` | `org.kde.kdecoration2` | `theme` | `Breeze` |
| Cursors | `kcminputrc` | `Mouse` | `cursorTheme` | `breeze_cursors` |

**Remember:** `kdecoration2`, even under KDecoration3. And Breeze's Plasma
Style is called `default`, not `breeze`.

## SVG element IDs

**9-patch:** `topleft` `top` `topright` `left` `center` `right`
`bottomleft` `bottom` `bottomright`

Also valid: only `left`/`center`/`right` (horizontal), only
`top`/`center`/`bottom` (vertical), only `center`.

**State prefixes** (example `button.svg`): `normal-` `hover-` `pressed-`
`focus-` `shadow-` `toolbutton-hover-` `mask-normal-`

A prefix counts as present if `<prefix>-center` exists, and nothing else is
checked.

**hint IDs:**

| ID | Effect |
|---|---|
| `hint-tile-center` | tile center instead of stretching |
| `hint-stretch-borders` | stretch edges instead of tiling |
| `hint-compose-over-border` | draw center under the borders |
| `hint-{top,right,bottom,left}-margin` | inner padding |
| `hint-{top,right,bottom,left}-inset` | frame inward (shadow, floating) |
| `hint-apply-color-scheme` | tint monochrome (only without `colors`) |
| `hint-focus-over-base` | focus over base |
| `hint-size`, `hint-bar-size`, `hint-scrollbar-size` | size settings |

**Color classes** (complete, extracted from Breeze):

```
ColorScheme-Text              ColorScheme-Background
ColorScheme-Highlight         ColorScheme-Frame
ColorScheme-ViewText          ColorScheme-ViewBackground
ColorScheme-ViewHover         ColorScheme-ViewFocus
ColorScheme-ButtonText        ColorScheme-ButtonBackground
ColorScheme-ButtonHover       ColorScheme-ButtonFocus
ColorScheme-NegativeText      ColorScheme-NeutralText
ColorScheme-PositiveText
```

Always together with `fill="currentColor"` or `stroke="currentColor"`.

## Breeze in the source code

| Artifact | Repo |
|---|---|
| **Plasma Style** | `plasma/libplasma` → `src/desktoptheme/{breeze,breeze-light,breeze-dark}/` |
| Qt style + decoration | `plasma/breeze` → `kstyle/`, `kdecoration/` |
| Color schemes | `plasma/breeze` → `colors/` |
| Look-and-Feel packages | `plasma/plasma-workspace` → `lookandfeel/` |
| SDDM theme | `plasma/plasma-desktop` → `sddm-theme/` |
| Icons | `frameworks/breeze-icons` |
| SVG tools | `frameworks/ksvg` → `src/tools/` |

**Most common misconception:** the `plasma/breeze` repo contains **no**
Plasma Style. That lives in `libplasma`.

## Package structure

**Plasma Style** (`metadata.json`):
```json
{ "KPlugin": { "Id": "…", "Name": "…", "Version": "1.0.0",
               "License": "GPL-3.0-or-later", "EnabledByDefault": true },
  "X-Plasma-API": "5.0" }
```

**Look-and-Feel** (`metadata.json`) — `KPackageStructure` is mandatory:
```json
{ "KPackageStructure": "Plasma/LookAndFeel",
  "KPlugin": { … },
  "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
  "X-Plasma-APIVersion": "2" }
```

**Aurorae** (`metadata.desktop` — correct here, not legacy):
```ini
[Desktop Entry]
Name=…
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__<folder-name>
```

## Verification

```bash
tools/lint-plasma-svg.py <theme> --compare /usr/share/plasma/desktoptheme/default
xmllint --noout $(find . -name '*.svg')
check-jsonschema --schemafile kpluginmetadata.schema.json $(find . -name metadata.json)
desktop-file-validate aurorae/*/metadata.desktop
reuse lint
```

Schema: `https://invent.kde.org/sysadmin/ci-utilities/-/raw/master/resources/jsonschemas/kpluginmetadata.schema.json`

## Emergency exit

```bash
plasma-apply-lookandfeel --apply org.kde.breeze.desktop
plasma-apply-desktoptheme default

# from the TTY:
export XDG_RUNTIME_DIR=/run/user/$(id -u)
kwriteconfig6 --file plasmarc --group Theme --key name default
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
rm -f ~/.cache/plasma_theme_*.kcache

# reset panels (deletes all widget settings):
mv ~/.config/plasma-org.kde.plasma.desktop-appletsrc{,.bak}

# turn off graphical login:
sudo systemctl set-default multi-user.target
```

## Pitfalls

| Symptom | Cause |
|---|---|
| Change has no effect | Cache — `rm ~/.cache/plasma_theme_*.kcache` |
| Theme does not appear in the list | `metadata.json` faulty, or folder name ≠ expected |
| Global theme missing from the selection | `KPackageStructure` missing |
| Decoration is not set | group `kdecoration3` used instead of `kdecoration2` |
| Colors are not replaced | `fill="currentColor"` missing |
| Hover effect missing | `hover-center` missing — Plasma does not report this |
| Panel geometry wrong | `hint-*-inset` missing |
| SDDM theme has no effect | system uses `plasmalogin` — no QML themes |
| Lock screen QML has no effect | belongs in the shell package, not in Look-and-Feel |
| User loses their panels | layout script in the Look-and-Feel package |
| User sees old theme after update | `KPlugin.Version` not bumped |
