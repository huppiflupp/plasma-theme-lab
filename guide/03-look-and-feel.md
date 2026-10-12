# 3. Look-and-Feel package

The Look-and-Feel package is what appears in System Settings as a
**"Global Theme"**. It contains hardly any graphics itself; it is a clamp
that wires the other layers together.

That is exactly why it is the riskiest layer that still lives in `$HOME`:
it writes to the user's configuration.

---

## 3.1 Package structure

Authoritative, from the source code
[`plasma-workspace/shell/packageplugins/lookandfeel/lookandfeel.cpp`]:

```
<id>/
├── metadata.json
└── contents/
    ├── defaults                    ← the core piece
    ├── colors
    ├── layouts/
    │   ├── org.kde.plasma.desktop-layout.js   ← replaces panels (3.4)
    │   └── defaults
    ├── previews/
    │   ├── preview.png             (400×250)
    │   ├── fullscreenpreview.jpg
    │   ├── lockscreen.png
    │   ├── splash.png
    │   └── windowswitcher.png
    ├── splash/Splash.qml
    ├── logout/Logout.qml
    └── windowswitcher/WindowSwitcher.qml
```

The code calls `setRequired()` for none of these parts: **everything is
optional**. Missing parts come from `org.kde.breeze.desktop` via
`setFallbackPackage()`.

**There is no `lockscreen/` folder any more**, and no `loginmanager/`.
See [chapter 1.4](01-layers-and-risk.md#important-the-lock-screen-no-longer-belongs-in-the-look-and-feel-package):
if you maintain QML there, you maintain dead code.

## 3.2 metadata.json

```json
{
    "KPackageStructure": "Plasma/LookAndFeel",
    "KPlugin": {
        "Id": "com.github.huppiflupp.niceos9-dark",
        "Name": "NiceOS9 Dark",
        "Description": "Mac OS 9 Platinum look for Plasma 6",
        "Authors": [{ "Name": "First Last", "Email": "mail@example.org" }],
        "License": "GPL-3.0-or-later",
        "Version": "2.1.0",
        "Website": "https://github.com/…"
    },
    "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
    "X-Plasma-APIVersion": "2"
}
```

Two fields are not optional here:

**`KPackageStructure` at the top level.** Without this key the package does
not appear under "Global Themes". It does *not* belong in `KPlugin`.

**`X-Plasma-APIVersion: "2"`** is not cosmetic. `kscreenlocker` checks the
value and refuses to use the package if it is `< 2`.
[source: `kscreenlocker/greeter/greeterapp.cpp`]

**About `Id`:** reverse domain notation is the convention
(`org.kde.breeze.desktop`, `com.github.<user>.<theme>`). Avoid spaces in the
Id; it becomes the directory name.

**License strings:** `KAboutLicense::byKeyword()` normalizes and recognizes
`"GPL-3.0-or-later"`. `"LGPL-2.1-only"` is **not** recognized and is shown
as "Custom". Not an error, just an ugly display.

## 3.3 contents/defaults — the core piece

Format: `[file][Group]` followed by `Key=Value`. The Breeze reference:
[verified]

```ini
[kdeglobals][KDE]
widgetStyle=Breeze

[kdeglobals][General]
ColorScheme=BreezeLight

[kdeglobals][Icons]
Theme=breeze

[plasmarc][Theme]
name=default

[Wallpaper]
Image=Next

[kcminputrc][Mouse]
cursorTheme=breeze_cursors

[kwinrc][org.kde.kdecoration2]
library=org.kde.breeze
theme=Breeze

[ksplashrc][KSplash]
Theme=org.kde.breeze.desktop
```

**Remember:** the decoration group is called `org.kde.kdecoration2`, even
under KDecoration3. See [chapter 1.6](01-layers-and-risk.md#16-window-decoration-kdecoration3-but-config-key-kdecoration2).

For an Aurorae theme:
```ini
[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__MyTheme
```

### What does not belong here

Every key in `defaults` overrides a user setting. Limit yourself to what is
part of the appearance. Fonts, double-click behavior, power settings and
keyboard shortcuts do not belong in a theme, even though you could
technically set them there.

## 3.4 The panel trap

**The point at which a theme can cost user data.**

A `contents/layouts/org.kde.plasma.desktop-layout.js` is a script that
rebuilds the desktop configuration:

```javascript
var panel = new Panel;
panel.location = "top";
panel.addWidget("org.kde.plasma.kickoff");
…
```

When it runs, **all of the user's panels, widgets and their settings are
gone**. This cannot be undone. Someone who set up their panel over years
loses that work by trying out a theme.

### The all-clear

KDE protects in three places. If you want to ship a layout, you should know
them; they change the trade-off.

**The checkbox is not pre-checked.**
[source: `kcms/lookandfeel/kcm.cpp`, `resetSelectedContents()`]

```cpp
// But do not select layout contents by default if there appaerance settings
if (m_themeContents & KLookAndFeelManager::AppearanceSettings) {
    resetContents &= ~KLookAndFeelManager::LayoutSettings;
}
```

As soon as a theme also brings appearance settings (which every serious
theme does), "Desktop and window layout" is unchecked when the dialog opens.

**There is a warning.** `SimpleOptions.qml` shows a red `InlineMessage`
below the checkbox as soon as you check it, saying that applying a desktop
layout deletes the current desktops, panels, docks and widgets.

**The command line does not touch the layout.**
[source: `kcms/lookandfeel/tool/lnftool.cpp`, verified]

```cpp
// By default do not modify the layout, unless explicitly specified
KLookAndFeelManager::Contents selection =
    KLookAndFeelManager::AppearanceSettings | KLookAndFeelManager::BlendChanges;
if (parser.isSet(_resetLayout)) { selection |= KLookAndFeelManager::LayoutSettings; }
```

```console
$ plasma-apply-lookandfeel --help
  -a, --apply <packagename>  Apply a global theme package.
      --resetLayout          Reset the Plasma Desktop layout
```

So `plasma-apply-lookandfeel --apply <name>` does not touch the layout.
Only `--resetLayout` does.

**But:** these three nets catch the user who clicks by accident. They do not
catch the one who checks the box on purpose, and that is what anyone does
who wants to see the theme the way it is meant. For them, the loss of their
panel configuration is final.

### What follows from this

Shipping a layout is legitimate. For a theme whose structure is part of the
look (menu bar at the top, no floating panel), it would even be incomplete
without one. What is missing is the way back.

**Back up the panel configuration in the installer before you change
anything:**

```bash
BACKUP="$HOME/.local/share/<theme>/panel-backup-$(date +%F-%H%M).rc"
mkdir -p "$(dirname "$BACKUP")"
cp -a "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "$BACKUP" 2>/dev/null
echo "Panel configuration backed up: $BACKUP"
```

Four lines, and "irreversible" becomes "copy the file back, log in again".
That is the difference between a theme you can try out and one you have to
think about first.

### Panel preset instead of a forced layout

There is a package format for exactly this purpose: **`Plasma/LayoutTemplate`**.

```
layout-templates/org.example.mytheme.panel/
├── metadata.json          ← "KPackageStructure": "Plasma/LayoutTemplate"
└── contents/
    └── layout.js
```

```bash
kpackagetool6 -t Plasma/LayoutTemplate -i ./layout-templates/org.example.mytheme.panel
```

A layout template appears on right-click under **"Add Panel"** and creates
an *additional* panel. It overwrites nothing. The user decides.

**Recommendation:** offer both. The `layouts/` in the Look-and-Feel package
for everyone who wants the full theme, protected by the backup above. In
addition, a layout template for everyone who wants to keep their own panel
and only try the layout next to it. One sentence about it in the README:
"The matching panel is also available on its own: right-click the desktop →
Add Panel → NiceOS9."

Side effect: layout scripts often contain absolute paths (wallpaper) that
the installer has to fill in with `sed`. Without a layout script, this hack
goes away.

## 3.5 Preview images

`contents/previews/preview.png` is what the user sees in the selection
dialog. If it is missing, a gray rectangle appears there, the most common
reason a good theme gets overlooked in the store.

| File | Where it shows |
|---|---|
| `preview.png` | Tile in the theme selection (400×250) |
| `fullscreenpreview.jpg` | Large view |
| `lockscreen.png` | Lock screen preview |
| `splash.png` | Splash screen preview |
| `windowswitcher.png` | Window switcher preview |

## 3.6 Splash screen (KSplash)

`contents/splash/Splash.qml` is a QML file shown at login. It gets a
`stage` property that counts up from 1 to 6.

Two things you need to know: the splash screen runs in a very early session
state, so use only `QtQuick`, no Plasma components. And it can be tested on
its own:

```bash
ksplashqml --test <package-id>
```

---

**Next:** [Chapter 4 — Building and installing](04-build-and-install.md)
