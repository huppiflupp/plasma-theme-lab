# 5. Testing

Four stages, from seconds to minutes. The first three run safely on your
work machine. The fourth belongs in a throwaway VM.

| Stage | What | Duration | Where |
|---|---|---|---|
| 1 | Static checks | seconds | anywhere, CI |
| 2 | Render a single widget | seconds | work machine |
| 3 | Reload the session | ~30 s | work machine |
| 4 | Full installation | minutes | **VM only** |

---

## 5.1 Stage 1 — static checks

### The SVG linter

Plasma does **not** report missing element IDs. A missing `hover-center`
shows only in that the hover effect is simply not there. There is no
official tool against this, neither from KDE nor from third parties.

This project ships one:

```bash
tools/lint-plasma-svg.py desktoptheme/mytheme
tools/lint-plasma-svg.py desktoptheme/mytheme \
    --compare /usr/share/plasma/desktoptheme/default
```

It checks:

- well-formed XML
- completeness of the 9-patch sets for each state prefix (it also knows the
  legitimate 3-patch forms that Breeze itself uses)
- a `current-color-scheme` stylesheet is present when `ColorScheme-*`
  classes are used
- `fill="currentColor"` is set; without it the fixed colors stay
- unknown color classes (typos in `ColorScheme-…`)
- `hint-*-inset` on panel backgrounds
- required fields in `metadata.json`

The comparison mode shows which SVGs are missing compared with Breeze,
sorted by urgency, with the deprecated `icons/` left out.

**Calibration:** the linter runs against Breeze itself with zero errors.
That is the cross-check every linter needs: a tool that complains about the
reference implementation complains wrongly.

### Icon names your own set intercepts

An incomplete icon set is worse than none. It overrides the fallback to
Breeze without providing a replacement, and it does so in two ways, both
measured with `kiconfinder6`:

```
audio-volume-high  →  audio-volume  →  audio  →  audio-x-generic
```

The lookup shortens at the hyphens and finally falls back to the class icon
`<class>-x-generic`. If you ship `audio-x-generic` but not
`audio-volume-high`, the volume control shows a sheet of paper with a musical
note; exactly this was reported by the community for 0.2.2. And because the
hit comes from your own set, Breeze is never asked.

```bash
tools/check-symbolic-trap.py nt-legacy/icons-nt/NTLegacyIcons
tools/check-symbolic-trap.py <dir> --all     # also the harmless cases
```

The tool turns the question around: for every class icon in your own set,
it looks up all names of the same class in Breeze that you do **not** ship
yourself. It leaves out file-type names; that `text-css` falls back to
`text-x-generic` is the whole point. What remains is what shows a wrong
picture in practice: `application-exit` as a sheet of paper, `audio-card` as
sheet music.

Either draw the missing names as well or leave out the class icon. Both are
defensible; only the in-between state is not.

### Metadata against KDE's own schema

KDE ships a JSON schema for `KPluginMetaData` and uses it in its own CI:

```bash
curl -sO https://invent.kde.org/sysadmin/ci-utilities/-/raw/master/resources/jsonschemas/kpluginmetadata.schema.json
check-jsonschema --schemafile kpluginmetadata.schema.json $(find . -name metadata.json)
```

It catches typos in person objects and wrong types. It does **not** catch
missing required fields (`additionalProperties: true`, no top-level
`required`); the linter above takes care of that.

### The rest

```bash
xmllint --noout $(find . -name '*.svg')          # XML well-formedness
desktop-file-validate aurorae/*/metadata.desktop  # Aurorae metadata
reuse lint                                        # license compliance
appstreamcli validate <file>                      # AppStream, if generated
```

`reuse` is the same tool KDE uses in its CI (`fsfe/reuse:5` as a container).

## 5.2 Stage 2 — render a single widget

The most underrated tool:

```bash
plasmawindowed org.kde.plasma.digitalclock
plasmawindowed org.kde.plasma.kickoff
```

It renders a single plasmoid in its own window, with the active Plasma
Style. No `plasmashell --replace`, no waiting, no risk to the running
session.

For SVG work this is the fastest feedback there is: save the file, clear the
cache, restart `plasmawindowed`.

## 5.3 Stage 3 — reload the session

```bash
plasma-apply-desktoptheme mytheme
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

**Clearing the cache is not optional.** Without it you do not see your
change and look for the bug in the wrong place. See
[chapter 2.6](02-plasma-style.md#26-the-cache).

More useful commands:

```bash
plasma-apply-desktoptheme --list-themes
plasma-apply-colorscheme MyScheme
plasma-apply-lookandfeel --list
plasma-apply-lookandfeel --apply com.example.mytheme   # without --resetLayout!
/usr/libexec/plasma-apply-aurorae MyTheme
```

### Empty keys after switching themes — almost always a measurement error

Until 9 August 2026 this section said the opposite: that switching via
*System Settings → Global Theme* left a half-set state behind, because
`plasmarc/Theme`, `Icons/Theme` and `kwinrc` stayed empty. That measurement
was wrong, and it justified an entire script that was not needed in that
form.

**What really happens:** Plasma writes a global theme's values not as user
values but as *defaults* to `~/.config/kdedefaults/`, and deletes the user
value in the process (`libklookandfeel/klookandfeelmanager.cpp`,
`writeNewDefaults`):

```cpp
defaultGroup.writeEntry(key, value, writeFlags);   // write the default
if (m_mode == Mode::Apply) {
    group.revertToDefault(key, writeFlags);        // delete the user value
}
```

So that the defaults are read, Plasma prepends them to the cascade at
session start:

```console
$ echo $XDG_CONFIG_DIRS
/home/you/.config/kdedefaults:/etc/xdg:/usr/share/kde-settings/…
```

**Over SSH this variable is missing.** `kreadconfig6` then reads only
`~/.config`, finds nothing and reports empty, even though everything is set
correctly. If you measure in a test VM via `ssh`, you measure exactly the
wrong thing.

Measuring correctly means: adopt the cascade of the real session.

```console
$ export XDG_CONFIG_DIRS="$HOME/.config/kdedefaults:/etc/xdg:/usr/share/kde-settings/kde-profile/default/xdg"
$ kreadconfig6 --file plasmarc --group Theme --key name
nt-legacy-win98
```

Or straight from the running process:

```console
$ tr '\0' '\n' < /proc/$(pgrep plasmashell)/environ | grep XDG_CONFIG_DIRS
```

**Consequence for your own scripts:** `kwriteconfig6` writes *nothing* if
the value equals the cascaded default; KConfig does not store an entry that
equals the default value. Demonstrated in the test VM: after
`kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Windows` the
key was still only in `kdedefaults`. A script that wants to "make sure" with
`kwriteconfig6` is therefore often an elaborate no-op.

### The application style is the exception — it does not take effect as a default

Everything else takes effect from `kdedefaults`: color scheme, Plasma Style,
icons, cursors, window decoration, splash screen. The application style
does not.

Measured in the test VM on a clean snapshot, after login:

```console
$ kreadconfig6 --file kdeglobals --group KDE --key widgetStyle
Windows                       # set correctly - as a default
```

and yet every Qt application started with Breeze. Only an entry in
`~/.config/kdeglobals` itself works, and `kwriteconfig6` cannot write it as
long as it equals the default value. If you want to ship the style, you have
to write it into the user file bypassing KConfig.

### Someone else's panel breaks any theme

`plasma-apply-lookandfeel --apply X` only applies the *appearance*, not the
desktop layout. So the user's panel stays, and most distributions ship a
**floating** panel.

Plasma draws floating panels with the rounded variants from `translucent/`.
A theme built for an edge-to-edge panel looks out of place in it; with the
NT recreation, dark instead of light gray, with rounded corners instead of
edges. The same installation, once without and once with `--resetLayout`,
produces two completely different pictures.

**For preview images this means:** if you produce them in a VM where the
layout was applied at some point, you photograph a state that a fresh
installation does not produce. The images then promise more than the
package delivers. Therefore: always produce preview images after a
`vmctl.sh reset`, never on accumulated state.

Also note: in the theme selection, every tile has a remove button next to
it. An accidental click deletes the installed style, and the shell silently
falls back to Breeze, with no message.

### `plasma-apply-colorscheme` does not reload a *changed* scheme

A pitfall that causes a lot of confusion: if you edit the `.colors` file and
then run

```bash
plasma-apply-colorscheme MyScheme
```

you see **no change**: the scheme is already active, so the command does
nothing. The old colors stay in `kdeglobals`.

Especially treacherous when resetting after a test: the `.colors` file looks
right again, but the system keeps showing the test colors.

Detouring through another scheme forces the reload:

```bash
plasma-apply-colorscheme BreezeLight
plasma-apply-colorscheme MyScheme
```

The actual state can only be checked in `kdeglobals`, not in the scheme
file:

```bash
kreadconfig6 --file kdeglobals --group "Colors:Selection" --key BackgroundNormal
```

**The same pattern applies to the window decoration:** `BorderSize` takes
effect neither via `plasma-apply-*` nor via `qdbus org.kde.KWin /KWin reconfigure`;
KWin only picks up the border size at session start. A test run over all
eight sizes without logging in again measures the same state eight times.

## 5.4 Stage 4 — full installation in the VM

**Everything that needs `sudo` belongs here.** The login manager, Plymouth
and GRUB run before you can log in; a mistake there may cost you a live
medium and an evening.

Even if your installer only writes to `$HOME`, the VM is the better place:
only there can you check how the theme behaves on a **fresh** user account.
On your own computer you have long had settings that hide gaps in the theme.

The procedure that has proven itself:

1. Set up the VM once, install the tools
2. Create a **snapshot `clean`**
3. Reset to `clean` before every test run
4. Copy the theme in, install, take a screenshot, record the findings
5. Back to 3

The snapshot is the real trick. Without it, the second run tests on the
leftovers of the first.

This project ships the VM:

```bash
vm/build-vm.sh              # once, unattended installation
vm/provision.sh             # tools, autologin
vm/vmctl.sh snap create clean

vm/vmctl.sh reset           # back to clean, takes seconds
vm/vmctl.sh push ../niceos9 /home/tester/theme
vm/vmctl.sh ssh 'cd theme && ./install.sh'
vm/vmctl.sh shot findings.png
```

**Screenshots via the hypervisor, not via the guest.** `vmctl.sh shot` uses
`virsh screenshot`, which still works when Plasma has crashed or no session
is running at all. That is exactly the interesting case in theme tests. A
`spectacle` inside the guest by definition cannot deliver anything once the
session is gone.

### What to check in the VM

- Does the theme install on a fresh account without errors?
- Does it look as intended on a fresh account?
- Does the session still start after applying it?
- Does it survive a **reboot**? (The most common case in which a theme
  stands out: at the next login.)
- Does `uninstall.sh` really return the system to its initial state?
- What changed in the system? (`rpm -Va`, comparison with the baseline)

The "survives a reboot" point is the most important one and the one most
often skipped.

## 5.5 Headless

KWin ships a virtual backend; Xvfb is not needed:

```bash
kwin_wayland --virtual --width 1920 --height 1080 \
             --no-lockscreen --no-global-shortcuts \
             --exit-with-session ./tools/smoke.sh
```

`smoke.sh` starts `plasmashell`, waits, takes a screenshot and compares it
with a reference image:

```bash
compare -metric AE reference.png current.png diff.png
```

For a retro theme that aims at pixel accuracy, screenshot comparison makes
sense. KDE itself deliberately avoids it and instead uses
[selenium-webdriver-at-spi](https://invent.kde.org/sdk/selenium-webdriver-at-spi)
via AT-SPI2, which is oversized for a theme project.

## 5.6 How others do it — researched, not guessed

The sobering finding first: **Plasma themes are not visually tested
anywhere, not even by KDE.**

Since April 2026, KDE has run its own openQA instance for KDE Linux
([os-autoinst-distri-kdelinux](https://invent.kde.org/kde-linux/os-autoinst-distri-kdelinux)).
Its 168 needles serve only to control the flow: UEFI screen, Plymouth,
login, "Kickoff icon visible". Not a single test checks a theme's
appearance. Same with openSUSE: a search of `os-autoinst-distri-opensuse`
for `breeze|lookandfeel|desktoptheme|colorscheme` gives zero hits.

`plasma-workspace/appiumtests/kcms/` is misleading too. Files like
`kcm_desktoptheme_test.py` sound relevant but test the settings module, not
the theme; at its core the desktop theme test consists of two lines that
check whether "All themes" and "Breeze Light" are in the list.

**What follows from this:** if you install a theme in a VM, log in again
and look, you already do more than the reference implementation. The bar is
lower than expected. That is no reason to get comfortable, but it puts the
question "is this enough?" into perspective.

### The one pixel comparison KDE runs

`breeze-icons/optimize-svg.sh` renders every icon **before and after** SVGO
optimization and discards the result if `compare -metric MAE > 100`.

This is notable because it is not a checked-in reference image but a
before/after comparison in the same run. That removes the dependency on
fonts, anti-aliasing and screen resolution, exactly the reasons golden-image
tests of user interfaces are so reliably annoying. For a theme project this
is the better pattern.

### A warning about SVG optimizers

SVGO's `cleanupIds` runs as part of `preset-default` and removes IDs that are
not referenced internally. In a Plasma theme, `center`, `hint-tile-center`
and the like are **never** referenced internally; Plasma looks them up from
outside. **A careless `svgo` run over the theme folder destroys the theme
completely.** This project uses neither `svgo` nor `scour`; if you do, you
must explicitly turn off `cleanupIds`.

### Two tools worth having

`plasmathemeexplorer` from `plasma-sdk` shows all theme elements as a grid
and marks for each element whether it comes from your own theme or from the
Breeze fallback. For the question "what is still missing?" there is nothing
better.

And a Qt cross-check: Qt SVG does **not** support `<clipPath>`
([doc.qt.io](https://doc.qt.io/qt-6/svgextensions.html)), the classic case
of "pretty in Inkscape, broken in Plasma". Rendering the same file once
normally and once with `QtSvg::Option::Tiny12FeaturesOnly` and logging the
parser warnings catches a class of errors that neither `xmllint` nor a
linter of your own can see.

---

## 5.7 What KDE itself does

For context: the CI configuration is centralized in `sysadmin/ci-utilities`;
the repos only include templates. `plasma/breeze` uses `linux-qt6`,
`freebsd-qt6`, `windows-qt6`, `xml-lint`, `yaml-lint`. `libplasma` also uses
`qml-lint`.

Available and copyable for your own projects: `clang-format`, `cppcheck`,
`json-validation`, `reuse-lint`, `qml-lint`, `xml-lint`, `yaml-lint`,
`pre-commit`, `flatpak`.

**There is no theme linter in this collection.** Nobody checks the SVG
structure; that is the gap `tools/lint-plasma-svg.py` fills.

---

**Next:** [Chapter 6 — When things go wrong](06-recovery.md)
