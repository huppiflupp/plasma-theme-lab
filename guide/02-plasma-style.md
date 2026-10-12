# 2. Plasma Style

The Plasma Style colors the shell: panel, plasmoids, tooltips, notifications,
OSD. It consists almost entirely of SVG files plus a handful of metadata.

---

## 2.1 Directory layout

```
<name>/
├── metadata.json          # required — without it the theme is not found
├── plasmarc               # optional: default wallpaper, transparency
├── colors                 # optional: own palette for the shell
├── widgets/*.svg          # the main part (Breeze: 43 files)
├── dialogs/background.svg # background of all Plasma popups
├── opaque/{widgets,dialogs}/       # variant without transparency
├── translucent/{widgets,dialogs}/  # variant with transparency
├── solid/{widgets,dialogs}/        # variant for blur-free environments
└── icons/*.svg            # DEPRECATED in Plasma 6 — do not create any more
```

The three variant folders are optional. Depending on the environment
(compositing on/off, blur available), Plasma picks the matching set and
otherwise falls back to `widgets/`.

`icons/` used to be responsible for tray icons. In Plasma 6 they come from
the icon theme. Breeze still ships the files; new themes do not need them.

## 2.2 metadata.json

```json
{
    "KPlugin": {
        "Id": "niceos9",
        "Name": "NiceOS9",
        "Description": "Mac OS 9 Platinum style for the Plasma shell",
        "Authors": [{ "Name": "First Last", "Email": "mail@example.org" }],
        "License": "GPL-3.0-or-later",
        "Version": "2.1.0",
        "Website": "https://github.com/…",
        "Category": "",
        "EnabledByDefault": true
    },
    "X-Plasma-API": "5.0"
}
```

Four things you need to know:

**The theme's identity is the folder name, not `Id`.** [source: `kcms/desktoptheme/themesmodel.cpp`, verified]
The KCM scans directories under `plasma/desktoptheme` and uses the directory
name. Proof: the installed `breeze-light` has `"Id": "default"` in its
`metadata.json` and is still called `breeze-light` everywhere. The
documentation recommends keeping both the same; that is good advice, but not
a requirement.

**`Version` is the cache key.** See [2.6](#26-the-cache). Bump it with every
release.

**`metadata.desktop` still works but is deprecated.**
[source: `ksvg/src/ksvg/private/imageset_p.cpp`] The code checks
`metadata.json` first, then `metadata.desktop`, and prints a warning for the
latter. New themes: JSON only.

**`X-Plasma-API`** is still `"5.0"` in Breeze in 2026. Whether the value is
evaluated at all could not be shown in the code **[uncertain]**. Use `"5.0"`
to follow Breeze.

## 2.3 The 9-patch system

Every frame-like element consists of nine named SVG elements:

```
topleft      top       topright
   left    center    right
bottomleft  bottom  bottomright
```

The scaling rules:

| Part | Behavior | Switch with |
|---|---|---|
| Corners | are **never** scaled | — |
| Edges | are **tiled** | `hint-stretch-borders` → stretch |
| `center` | is **stretched** | `hint-tile-center` → tile |

For a retro look with 1-pixel borders, this is the central mechanism:
corners stay pixel-exact, edges tile cleanly.

### Prefixes turn a 9-patch into a state

IDs are made up of several hyphen-separated parts. A prefix in front defines
a state. From Breeze's `widgets/button.svg`:

```
normal-topleft, normal-top, normal-center, …
hover-topleft,  hover-top,  hover-center,  …
pressed-…, focus-…, shadow-…
toolbutton-hover-…, toolbutton-pressed-…
mask-normal-…
```

Plasma checks whether a prefix exists by looking for `<prefix>-center`,
nothing more. [source: `ksvg` `FrameSvg::hasElementPrefix()`]

```cpp
// for now it simply checks if a center element exists,
// because it could make sense for certain themes to not have all the elements
```

If `hover-center` is missing, there is no hover state, **with no error
message**. That is the reason for [stage 1 of testing](05-testing.md).

### A useful tool

KDE ships an Inkscape extension meant for exactly this:
`ksvg/src/tools/inkscape extensions/plasmarename.{inx,py}`. "Plasma →
PlasmaRename" puts a prefix on all selected elements. With it you build a
`hover-*` set from a `normal-*` set in seconds instead of twenty clicks.

## 2.4 All hint IDs

A `hint-*` element is an invisible rectangle whose geometry carries a
setting. You draw it in Inkscape, give it the ID and set its opacity to 0.

| ID | Effect |
|---|---|
| `hint-tile-center` | tile `center` instead of stretching |
| `hint-stretch-borders` | stretch edges instead of tiling |
| `hint-compose-over-border` | draw `center` **under** the borders — prevents alpha overlap at semi-transparent borders |
| `hint-{top,right,bottom,left}-margin` | set the content's inner padding |
| `hint-{top,right,bottom,left}-inset` | shift the frame inward — for shadows and floating panels |
| `hint-apply-color-scheme` | tint the whole SVG monochrome (only without a `colors` file) |
| `hint-focus-over-base` | put the focus frame over the base (`lineedit.svg`) |
| `hint-size`, `hint-bar-size`, `hint-scrollbar-size`, `hint-handle-size` | size settings |
| `hint-preferred-icon-size` | preferred icon size |
| `hint-rotation-angle` | clock/busy widget |
| `hint-glow-radius`, `hint-use-shadow`, `hint-show-separator` | effects |

Hints can be combined with prefixes: `shadow-hint-top-margin`,
`floating-hint-bottom-margin`, `normal-hint-compose-over-border`. All three
actually occur in Breeze. [verified]

**`hint-*-inset` is the Plasma 6 newcomer.** It separates the drawn area
from the space claimed, which floating panels and drop shadows need. A theme
without insets looks wrong on a floating panel.

## 2.5 Color scheme support

There are two mechanisms. The second one is the right one.

**(a) `hint-apply-color-scheme`** — insert an element with this ID and ship
**no** `colors` file. The whole SVG is then tinted monochrome in the window
background color. A blunt tool, rarely useful.

**(b) The `current-color-scheme` stylesheet** — the standard way:

```xml
<defs>
  <style id="current-color-scheme" type="text/css">
    .ColorScheme-Text             { color:#31363b; }
    .ColorScheme-Background       { color:#eff0f1; }
    .ColorScheme-Highlight        { color:#3daee9; }
    .ColorScheme-ViewText         { color:#31363b; }
    .ColorScheme-ViewBackground   { color:#fcfcfc; }
    .ColorScheme-ViewHover        { color:#93cee9; }
    .ColorScheme-ViewFocus        { color:#3daee9; }
    .ColorScheme-ButtonText       { color:#31363b; }
    .ColorScheme-ButtonBackground { color:#eff0f1; }
    .ColorScheme-ButtonHover      { color:#93cee9; }
    .ColorScheme-ButtonFocus      { color:#3daee9; }
  </style>
</defs>

<path class="ColorScheme-Background" fill="currentColor" d="…"/>
```

Before rendering, Plasma replaces the `color:` values with the system colors.

**Two things are mandatory:** the class **and** `fill="currentColor"` or
`stroke="currentColor"`. Without `currentColor` the fixed color stays.

Gradients do not accept classes; wrap the gradient element in a group
instead: `<g class="ColorScheme-Background">…</g>`.

`ColorScheme-Highlight` is a special case: it follows the **accent color**
set by the user.

**Why this matters:** only if you use these classes consistently can you
build color variants without duplicating SVGs. See
[chapter 4](04-build-and-install.md#44-variants-without-duplicates).

### Helper scripts

In `frameworks/ksvg/src/tools/`:

- `apply-stylesheet.sh` — replaces fixed colors with `ColorScheme-*` classes
- `currentColorFillFix.sh` — repairs `fill` attributes for `currentColor`
- `split-plasma-svgs` — splits a Plasma SVG into individual elements (debugging)

## 2.6 The cache

**The most common cause of "my change has no effect".**

Plasma caches rendered pixmaps in
`~/.cache/plasma_theme_<name>_v<version>.kcache` plus `~/.cache/ksvg-elements`.
The cache name contains the version from `metadata.json`:

```cpp
QString cacheFile = QLatin1String("plasma_theme_") + imageSetName;
if (!themeVersion.isEmpty()) { cacheFile += QLatin1String("_v") + themeVersion; }
```
[source: `ksvg`]

Two things follow from this:

**While developing**, after every SVG change:
```bash
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

**When publishing**, bump the version. Otherwise your users see the old
theme after the update and report bugs that were fixed long ago.

## 2.7 Which SVGs do you really need?

Formally none; everything falls back to Breeze. In practice, by visibility:

| Priority | File | What you see |
|---|---|---|
| **1** | `widgets/panel-background.svg` | Panel / taskbar |
| **1** | `dialogs/background.svg` | all Plasma popups |
| **1** | `widgets/background.svg` | plasmoid backgrounds |
| 2 | `widgets/tooltip.svg` | tooltips |
| 2 | `widgets/listitem.svg`, `viewitem.svg` | lists (application launcher!) |
| 2 | `widgets/button.svg`, `lineedit.svg` | controls in plasmoids |
| 2 | `widgets/checkmarks.svg`, `radiobutton.svg`, `switch.svg` | selection controls |
| 2 | `widgets/scrollbar.svg`, `slider.svg` | sliders |
| **1** | `widgets/tasks.svg` | window buttons in the taskbar — requested by `taskmanager.so`, verified with `strings` |
| 3 | `widgets/plasmoidheading.svg`, `toolbar.svg`, `frame.svg` | frames, headers |
| 3 | `widgets/clock.svg`, `analog_meter.svg`, `pager.svg` | special widgets |
| — | `icons/*.svg` | **deprecated** — leave out |

**The sentence that matters:** a theme with only `panel-background.svg` is
not a look of its own; it is Breeze with a different panel. Priorities 1
and 2 are the threshold from which a theme is perceived as standing on its
own. That is about 12 files, not 43.

## 2.8 .svg in the repo, .svgz when shipped

At build time, Breeze compresses every `.svg` to `.svgz` with `gzip -9 -n`.
[source: `libplasma/src/desktoptheme/CMakeLists.txt`, verified against
`/usr/share/plasma/desktoptheme/default/widgets/`, which holds 43 `.svgz`]

The `-n` suppresses the timestamp so builds stay reproducible.

This division of labor is right and worth adopting: the repository holds
plain-text SVGs that you can diff and open in Inkscape. The compressed
version is what ships. Plasma reads both.

How to do this without CMake is described in
[chapter 4](04-build-and-install.md).

## 2.9 The `colors` file in the Plasma Style — better left out

A Plasma Style may contain a file named `colors`. It looks like a color
scheme and sets the shell's colors. The temptation is great: you then have
the panel color firmly under control.

**The price is high.** If there is a `colors` file, it wins over the user's
color scheme. Measured in the test VM on the application launcher, color
scheme *Desert* with Plasma Style *Teal*:

| | Surface color |
|---|---|
| with `colors` file | `#D8D8D0` — the theme color, Teal |
| without `colors` file | `#D8D0C0` — the color scheme, Desert |

The user can switch color schemes as much as they like: the shell stays on
the theme colors. **Breeze ships no `colors` file for exactly this reason**
(checked in `/usr/share/plasma/desktoptheme/default/`).

The colors are not lost without it. They belong in the color scheme
(`color-schemes/<Name>.colors`), and the installation script sets both
together.

### As for the accent color

A related but different point: the user's accent color does not reach a
theme either if the **color scheme** explicitly sets `Colors:Selection`,
which every scheme with its own color palette does. Verified:
`AccentColor=200,40,40` set, the selection stayed petrol.

This is not a bug but the result of a deliberate decision. If you want to
pass the accent color through, you must not fix `Colors:Selection`, and
thereby give up your own selection color. For a theme that recreates a
specific color palette, that is the wrong trade.

### Individual elements may keep fixed colors

In this project, `panel-background.svg` deliberately keeps fixed colors.
Reason: Plasma tints shell elements from `Colors:Window`, not from
`Colors:Complementary`. A panel that is meant to stand out from the plasmoid
surfaces cannot be controlled separately that way; with the class it became
`#d8d8d0` instead of `#b8c4c4`. This is the exception, not the rule:
25 of the 37 SVGs follow the color scheme.

---

**Next:** [Chapter 3 — Look-and-Feel package](03-look-and-feel.md)
