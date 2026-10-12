# 1. The seven layers and their risk

There is no such thing as "a theme" in Plasma. There are seven independent
layers and a bundle package that wires them together. They do **not**
interlock: each one can be broken or incomplete on its own without the
others noticing.

This is the most common beginner mistake: you change the Plasma Style and
wonder why Dolphin looks unchanged. The Plasma Style colors the shell.
Dolphin is a Qt app and listens to a completely different layer.

---

## 1.1 The overview

| # | Layer | Location (per user) | Metadata | Affects |
|---|---|---|---|---|
| 1 | **Plasma Style** | `~/.local/share/plasma/desktoptheme/<name>/` | `metadata.json` | Panel, plasmoids, tooltips, OSD, notifications — **the shell only** |
| 2 | **Color scheme** | `~/.local/share/color-schemes/<Name>.colors` | INI inside the file itself | Qt apps **and** the shell |
| 3 | **Application style** (QStyle) | Plugin `.so` | Plugin JSON | **Qt Widgets apps only** |
| 4 | **Window decoration** | `~/.local/share/aurorae/themes/<name>/` | `metadata.desktop` | Title bars, borders |
| 5 | **Icons** | `~/.local/share/icons/<name>/` | `index.theme` | Icons everywhere |
| 6 | **Cursors** | `~/.local/share/icons/<name>/cursors/` | `index.theme` | Pointer |
| 7 | **Splash screen** (KSplash) | inside the Look-and-Feel package | — | Loading screen |
| ★ | **Look-and-Feel** ("Global Theme") | `~/.local/share/plasma/look-and-feel/<id>/` | `metadata.json` + `KPackageStructure` | bundles 1–7 via `contents/defaults` |

The former name "Desktop Theme" for layer 1 is outdated; the UI now says
**Plasma Style**. The directory name `desktoptheme` stayed.

---

## 1.2 The key question: what colors what?

This confusion costs the most time. Sorted by what you see:

| What you want to color | Responsible layer |
|---|---|
| Panel / taskbar | Plasma Style (`widgets/panel-background.svg`) |
| Application launcher, widgets in the panel | Plasma Style |
| Notifications, tooltips, OSD | Plasma Style |
| A window's title bar | Window decoration (Aurorae) |
| Menu bar and toolbar **inside** Dolphin | Application style + color scheme |
| Buttons and input fields **inside** Dolphin | Application style (QStyle) |
| System Settings, Discover (QML/Kirigami) | Color scheme — **not** the application style |
| Lock screen | Shell package (**no longer** Look-and-Feel, see 1.4) |
| Login screen | Login manager (see 1.5) |

The application style is compiled C++ code (`KStyle`/`QCommonStyle`), not a
data format. You cannot "paint" it. If you want truly custom buttons in Qt
apps, you have three options: accept Breeze/Fusion, use
[Kvantum](#kvantum), or fork a QStyle.

### Kvantum

[Kvantum](https://github.com/tsujan/Kvantum) is a QStyle that takes its
appearance from SVG + INI — the only realistic path to custom Qt widgets
without C++. Actively maintained (as of 2026-08).

**But:** Kvantum colors *only* Qt Widgets apps. Plasma shell, panel,
plasmoids, KRunner and System Settings stay untouched; they come from the
Plasma Style or the color scheme.

Kvantum is an external dependency the user must have installed. If your
`contents/defaults` sets `widgetStyle=kvantum` and Kvantum is missing, the
user ends up with an unstyled fallback. **Useful as an optional add-on, not
as a required part.** WhiteSur and Colloid do exactly that: Kvantum is
included but installed separately.

### Before you reach for Kvantum: measure what really does not fit

A single bad-looking widget tempts you to replace the whole widget style.
Usually that is not worth it, and you trade one annoyance for twenty new
ones, because then *all* widgets have to be redrawn.

`tools/widget-test-window.py` shows all standard Qt widgets in one window
and saves it as an image:

```bash
./widget-test-window.py --style Windows --image /tmp/win.png
./widget-test-window.py --style Breeze  --image /tmp/breeze.png
```

Where the images differ, the widget style decides. Where they look the same,
the application draws by itself, and switching styles will not help either.

For NT Legacy the result was clear: the "MS Windows 9x" style
(`widgetStyle=Windows`) draws **everything** right — square buttons with a
3D edge, square checkboxes, sunken input fields, striped scroll bars.
Progress bars even appear as classic blocks in the selection color, exactly
as they should.

### The outlier: widgets that draw themselves

Dolphin's capacity indicator ("21.0 GiB free") still looks wrong — a silver
capsule with a soft gradient. It is **not** a `QProgressBar` but
`KCapacityBar` from KWidgetsAddons, and it draws its shape itself instead of
going through the style.

The test that proves it: set the selection color to bright red as a trial.
List selections and highlighted icons turn red, the bar stays silver — it
ignores the palette. **No** theme layer reaches such widgets; only a patch
to the library helps.

**Remember:** "looks wrong" has three possible causes, and they need
different tools: Plasma Style (shell), widget style (Qt widgets), or the
application itself. Assign first, then work.

---

## 1.3 Risk classes — the most important table in the whole guide

| Layer | Risk | Why |
|---|---|---|
| Plasma Style | **low** | Fallback to `default` is hard-wired in the code |
| Color scheme | **low** | at worst unreadable, reversible via CLI |
| Application style | low | missing plugin → Fusion |
| Window decoration | **medium** | only with an invalid `library`; a *theme name* that points nowhere leaves windows **with no title bar at all** — see below |
| Icons / cursors | low | Fallback via `Inherits` or `hicolor` |
| Look-and-Feel | **medium** | writes to `kdeglobals`/`kwinrc`; a layout script deletes panels |
| **Login manager** | **high** | system-wide, acts *before* login → black screen with no GUI rescue |
| **Plymouth / GRUB** | **high** | initramfs or bootloader — at worst the computer no longer boots |

**The dividing line runs between rows 6 and 7.** Everything above it lives
in `$HOME` and can be repaired from a TTY in a minute. Everything below it
runs before you can log in.

Practical consequence for your project:

```
theme/
├── install.sh            # $HOME only, no sudo, safe to try at any time
└── risky/                # separate folder, separate warning, default = no
    ├── install-sddm.sh
    ├── install-plymouth.sh
    └── install-grub.sh
```

An `install.sh` that asks for `sudo` and touches GRUB in the same run is a
design flaw, regardless of its code quality.

### Also: a theme does not set the appearance of other programs

Some things you would blame on the theme are a setting of the application.
Dolphin's status bar, for example, has for some time appeared as a floating
box at the bottom left instead of a full-width bar. Next to a square retro
theme this looks like a bug, but it is the default `ShowStatusBar=Small`
from `dolphinrc`. With Breeze it looks identical.

**The test that resolves such mix-ups:** take the same screenshot once with
`widgetStyle=Breeze`. If it looks the same there, the theme is not the
cause.

The temptation then is to simply set the value in `apply.sh` as well. Do not
do exactly that: someone trying out a theme does not expect their Dolphin
configuration to be different afterwards, and will never find the
connection later. Such changes belong in a **separate, explicitly invoked
script with a complete way back** (in this project: `nt-legacy/appearance.sh`).
The backup must distinguish between "was not set" and "was set to the
default value"; otherwise, after resetting, a value is left there that the
user never chose.

---

## 1.4 Plasma is more robust than its reputation — four safety nets

It helps to know what Plasma catches on its own. That saves your nerves and
keeps you from rebuilding protections that already exist.

**Missing SVG file → Breeze.** [source: `ksvg/src/ksvg/private/imageset_p.cpp`]
The fallback chain is hard-wired to `default`:
```cpp
fallbackImageSets = {ImageSetPrivate::defaultImageSet};   // "default"
```
A configurable fallback **no longer** exists. The documentation on
develop.kde.org still mentions `[Settings] FallbackTheme=oxygen` in
`plasmarc`; this key is not read anywhere in the current code.

**Missing element ID → silently skipped.** [source: `ksvg` `FrameSvg::hasElementPrefix()`]
The only check is whether `<prefix>-center` exists. If it is missing, the
prefix is set to empty. No crash, but also **no warning**. That is exactly
why you need a [linter of your own](05-testing.md#51-stage-1--static-checks).

**The plasmashell crash loop is capped.** [verified]
`/usr/lib/systemd/user/plasma-plasmashell.service`:
```ini
StartLimitIntervalSec=60s
StartLimitBurst=3
ExecStart=/usr/bin/plasmashell --no-respawn
```
After three failed starts within 60 seconds, systemd gives up. There is no
endless loop. KWin and the session keep running; only the panel and desktop
are missing. Window keyboard shortcuts still work.

**The lock screen cannot lock anyone out.** [source: `kscreenlocker/greeter/greeterapp.cpp`]
```cpp
// on error, load the fallback lockscreen to not lock the user out of the system
static const QUrl fallbackUrl(QStringLiteral("qrc:/fallbacktheme/LockScreen.qml"));
```
The fallback is compiled into the binary.

### Important: the lock screen no longer belongs in the Look-and-Feel package

This is the Plasma 6 change with the biggest consequences for theme authors.
[source: `greeterapp.cpp`, verified against `/usr/share/plasma/shells/`]

The lock screen is loaded from the **shell** package:
```
/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/
```
The Look-and-Feel package format **no longer** has a `lockscreen` folder,
only `previews/lockscreen.png`, i.e. the preview image.

**A `look-and-feel/<x>/contents/lockscreen/LockScreen.qml` is dead code under
Plasma 6.** It is never loaded. The porting page on develop.kde.org still
mentions it; that is outdated.

---

## 1.5 The login manager changed in 2025/26

On Fedora 44, Nobara 44 and KDE Linux, **SDDM is no longer installed**.
In its place runs the **Plasma Login Manager** (`plasmalogin`), an SDDM fork
that KDE has maintained itself since roughly Plasma 6.6. [verified]

```console
$ readlink -f /etc/systemd/system/display-manager.service
/usr/lib/systemd/system/plasmalogin.service
$ rpm -q sddm
package sddm is not installed
```

Its configuration lives in `/etc/plasmalogin.conf` and has **no `[Theme]`
section**. There is no `themes/` directory under `/usr/share/plasmalogin/`.

**Consequence: the Plasma Login Manager does not support QML themes.**
Essentially only the background image is configurable.

If your project ships an SDDM theme, it therefore needs detection; otherwise
you copy files into a directory nobody reads:

```bash
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    echo "This system uses the Plasma Login Manager."
    echo "It does not support QML themes - the login screen stays unchanged."
    echo "Only the background image is configurable."
elif [ -f /usr/lib/systemd/system/sddm.service ]; then
    # classic SDDM path
    sudo cp -r sddm/my-theme /usr/share/sddm/themes/
fi
```

Whether KDE will eventually support themes for the Plasma Login Manager is
open. **[uncertain]**

---

## 1.6 Window decoration: KDecoration3, but config key `kdecoration2`

A pitfall that costs a lot of time. Plasma 6 uses **KDecoration3**; the
plugin directory is `/usr/lib64/qt6/plugins/org.kde.kdecoration3/`.
[verified]

**The configuration key, however, is still `org.kde.kdecoration2`.**
[source: `kwin/src/decorations/decorationbridge.cpp`]

```cpp
static const QString s_pluginName    = QStringLiteral("org.kde.kdecoration3");
static const QString s_configKeyName = QStringLiteral("org.kde.kdecoration2");
static const QString s_defaultPlugin = QStringLiteral("org.kde.breeze");
```

Confirmed locally:
```console
$ kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library
org.kde.breeze
$ kreadconfig6 --file kwinrc --group org.kde.kdecoration3 --key library
              # empty
```

**If you write `[kwinrc][org.kde.kdecoration3]` in `contents/defaults`, you
achieve nothing.** The group must be called `org.kde.kdecoration2` — even in
2026, even under KDecoration3.

### Which Aurorae engine goes into `defaults`? — `org.kde.kwin.aurorae`, not `.v2`

There are two: the classic one (`org.kde.kwin.aurorae`) and the
KDecoration3-native one (`org.kde.kwin.aurorae.v2`). The obvious choice for
a new theme would be `.v2`. **It is wrong.**

`.v2` only exists from **Plasma 6.6** on. On 6.0 to 6.5, loading fails and
KWin falls back to its fallback chain (`decorations/decorationbridge.cpp`):

```cpp
if (!initPlugin(pluginId)) {
    if (s_defaultPlugin != pluginId) initPlugin(s_defaultPlugin);  // "org.kde.breeze"
```

So the user gets **Breeze window borders, with no error message**. On your
own up-to-date system you never see this.

Conversely, the v1 setting costs nothing on new systems: KWin upgrades the
line itself at session start (`migrateAuroraeTheme`, present from
Plasma 6.6 on). Verified in the test VM, Plasma 6.7:

```console
$ kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
      --key library org.kde.kwin.aurorae
$ # ... restart ...
$ kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library
org.kde.kwin.aurorae.v2
```

**So enter `org.kde.kwin.aurorae` and leave the migration to KWin.** This is
correct on every version: on old ones it works, on new ones it automatically
becomes `.v2`.

Aurorae themes still use `metadata.desktop`. Here this is **not** legacy but
the intended format:

```ini
[Desktop Entry]
Name=My Theme
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__MyTheme
X-KDE-PluginInfo-Version=1.0
```

The prefix `__aurorae__svg__` is mandatory and must be followed by the
folder name.

### The `center` area of `decoration.svg` must not be transparent

The obvious assumption: the middle of the decoration lies entirely under the
window content, so it can stay empty. That holds exactly as long as the user
does not touch the border size.

If they increase it in *System Settings → Window Decorations → Border size*,
KWin reports a wider border than the `left`/`right`/`bottom` elements draw;
these keep their natural width from the SVG. The difference falls into the
`center` area. The Aurorae documentation says so explicitly:

> "the borders may extend into the center element if the border size is
> changed"
> — [develop.kde.org/docs/plasma/aurorae](https://develop.kde.org/docs/plasma/aurorae/)

If `center` was transparent, you see the **desktop shining through** there:
a gap between the border and the window content. Measured at
`BorderSize=Large` and a 4 px border width:

```
x=76      black       outer edge
x=77      white       highlight edge
x=78..79  gray 192    border area    ← only 4 px drawn
x=80..81  teal        GAP            ← KWin reserves 6 px
x=82+     white       window content
```

So: fill `center` with the border area. The price is that with a
translucent window you see this area instead of the desktop, which is the
right trade for an opaque theme.

**For testing:** `BorderSize` does **not** take effect via
`qdbus org.kde.KWin /KWin reconfigure`. KWin only picks up the border size
when loading the decoration, i.e. at session start. If you measure without
logging in again, you check the same state eight times and take the result
for success. `tools/check-frames.py` measures the color sequence across the
window and reports every spot where the desktop color shows up again inside
the window.

---

**Next:** [Chapter 2 — Plasma Style](02-plasma-style.md)
