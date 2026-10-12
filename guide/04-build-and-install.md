# 4. Building and installing

Most theme projects install with `cp -r` from an `install.sh`. That works
until you want to undo it or maintain a second variant. This chapter shows
what to do instead.

---

## 4.1 Why not `cp -r`

A typical installer looks like this:

```bash
rm -rf "$HOME/.local/share/plasma/desktoptheme/mytheme"
cp -r desktoptheme/mytheme "$HOME/.local/share/plasma/desktoptheme/"
```

Four problems:

**No validation.** A typo in `metadata.json` only shows up when the user
cannot find the theme in the list.

**No clean uninstall.** The `uninstall.sh` has to maintain the list of paths
a second time. Forget one and junk is left behind. Worse: if you delete files
without resetting the configuration, the user is left with a half-broken
system, because `plasmarc` points to a theme that no longer exists.

**No `.svgz`.** Whatever is in the repo is what ships.

**Versions are maintained by hand.** With three variants, the version number
lives in three places. At release time you change two of them.

## 4.2 The middle ground without CMake

If you do not want CMake, a `Makefile` and `kpackagetool6` get you far:

```makefile
VERSION  := 2.1.0
BUILD    := build
PREFIX   ?= $(HOME)/.local

VARIANTS := niceos9 niceos9-dark niceos9-charcoal

.PHONY: all clean install uninstall check

all: $(BUILD)/.stamp

# generate metadata.json from a template - the version is set only here
$(BUILD)/.stamp: $(shell find desktoptheme -type f)
	@rm -rf $(BUILD); mkdir -p $(BUILD)
	@for v in $(VARIANTS); do \
	    cp -r desktoptheme/$$v $(BUILD)/$$v; \
	    sed "s/@VERSION@/$(VERSION)/" desktoptheme/$$v/metadata.json.in \
	        > $(BUILD)/$$v/metadata.json; \
	    rm -f $(BUILD)/$$v/metadata.json.in; \
	    find $(BUILD)/$$v -name '*.svg' -exec sh -c \
	        'gzip -9 -n -c "$$1" > "$${1}z" && rm "$$1"' _ {} \; ; \
	done
	@touch $@

install: all
	@for v in $(VARIANTS); do \
	    kpackagetool6 -t Plasma/Theme -u $(BUILD)/$$v 2>/dev/null || \
	    kpackagetool6 -t Plasma/Theme -i $(BUILD)/$$v; \
	done

uninstall:
	@for v in $(VARIANTS); do kpackagetool6 -t Plasma/Theme -r $$v || true; done

clean:
	rm -rf $(BUILD)
```

This takes care of the three most important points: one version number,
`.svgz` compression, validated installation.

## 4.3 kpackagetool6

The official way to install KDE packages. [verified, Plasma 6.7.3]

```bash
kpackagetool6 -t Plasma/Theme       -i ./mytheme       # install
kpackagetool6 -t Plasma/Theme       -u ./mytheme       # upgrade
kpackagetool6 -t Plasma/Theme       -r mytheme         # remove
kpackagetool6 -t Plasma/Theme       -l                 # list
kpackagetool6 -t Plasma/Theme       -s mytheme         # show metadata
kpackagetool6 -t Plasma/LookAndFeel -i ./com.example.mytheme
kpackagetool6 -t Plasma/LayoutTemplate -i ./org.example.mytheme.panel
sudo kpackagetool6 -g -t Plasma/Theme -i ./mytheme     # system-wide
```

`-i` and `-u` accept a directory **or** an archive (`.tar.gz`, `.zip`).

The types that matter for themes:

| Type | Target directory |
|---|---|
| `Plasma/Theme` | `plasma/desktoptheme/` |
| `Plasma/LookAndFeel` | `plasma/look-and-feel/` |
| `Plasma/LayoutTemplate` | `plasma/layout-templates/` |
| `KWin/Aurorae` | `aurorae/themes/` |
| `Plasma/Applet` | `plasma/plasmoids/` |

**What does not exist:** `kpackagetool6 --validate`. Older guides mention it;
it does not appear in the help text of 6.7.3. [verified]
For checking metadata, see [chapter 5](05-testing.md).

Color schemes and Aurorae themes are still simply copied:
```bash
install -Dm644 color-schemes/*.colors -t "$HOME/.local/share/color-schemes/"
cp -r aurorae/MyTheme "$HOME/.local/share/aurorae/themes/"
```

## 4.4 Variants without duplicates

The most common maintenance problem: three color variants, three SVG trees,
every fix three times.

### How Breeze solves it

Breeze ships **one** SVG set, under the name `default`. The variants
`breeze-light` and `breeze-dark` contain: [verified]

```console
$ ls /usr/share/plasma/desktoptheme/breeze-light/
colors  metadata.json  plasmarc
```

**Not a single SVG file.** This works because

1. missing files fall back to `default`, and
2. the Breeze SVGs take their colors, via `current-color-scheme`
   stylesheets, from the `colors` file of the respective variant.

### The catch for your own themes

The fallback **always** goes to `default`, i.e. to Breeze, not to your base
theme. So `mytheme-dark` without SVGs shows Breeze graphics in your colors,
not your graphics.

That leaves two workable paths:

**Path A — one variant as the Plasma Style, variants via the color scheme.**
You ship exactly *one* Plasma Style. The variants come from different color
schemes and different Look-and-Feel packages, each of which sets the same
Plasma Style:

```ini
# look-and-feel/…niceos9-dark/contents/defaults
[plasmarc][Theme]
name=niceos9                 ← the same style for all variants
[kdeglobals][General]
ColorScheme=NiceOS9Dark      ← this is where the difference comes from
```

**This is the lowest-maintenance path** and exactly the reason Breeze is
built this way: one SVG set, several global themes.

Prerequisite: your SVGs use `class="ColorScheme-*"` and `fill="currentColor"`
consistently. Without that, they cannot be recolored.

**Path B — copy the SVGs into each variant at build time.** For when variants
should differ in *shape*, not only in color. The repo holds one set, and the
build script copies it into all variants. It costs disk space, but no
duplicate maintenance.

What you should **not** do: put three SVG trees into the repository.

### Generating color schemes

With several variants, generating them from a palette pays off.
[Catppuccin for KDE](https://github.com/catppuccin/kde) does this
exemplarily: more than 60 `.colors` files come out of one palette file.

For three variants, a short Python script is enough:

```python
# tools/gen-colors.py
PALETTES = {
    "NiceOS9Bright":   {"bg": "221,221,221", "fg": "0,0,0",       "hl": "0,0,128"},
    "NiceOS9Dark":     {"bg": "44,42,40",    "fg": "230,226,220", "hl": "180,200,255"},
    "NiceOS8Charcoal": {"bg": "60,60,60",    "fg": "220,220,220", "hl": "128,128,160"},
}
TEMPLATE = open("templates/colorscheme.in").read()
for name, colors in PALETTES.items():
    text = TEMPLATE
    for key, value in {**colors, "name": name}.items():
        text = text.replace(f"@{key}@", value)
    open(f"color-schemes/{name}.colors", "w").write(text)
```

Important: generated files belong in the repository too (the user should not
need Python), but the template is the source of truth. A CI job that checks
whether the generated files are up to date prevents drift.

## 4.5 Rollback is part of the installation

An `uninstall.sh` that only deletes files is not enough. If your installer
changes `plasmarc` and `kdeglobals`, it must back up the old values:

```bash
# In the installer, BEFORE any change:
RESTORE="$HOME/.local/share/mytheme/restore.sh"
mkdir -p "$(dirname "$RESTORE")"
{
    echo '#!/usr/bin/env bash'
    echo '# Generated automatically - restores the state from before the installation.'
    echo "kwriteconfig6 --file plasmarc --group Theme --key name \
'$(kreadconfig6 --file plasmarc --group Theme --key name)'"
    echo "kwriteconfig6 --file kdeglobals --group General --key ColorScheme \
'$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)'"
    echo "kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle \
'$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)'"
    echo "kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library \
'$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library)'"
} > "$RESTORE"
chmod +x "$RESTORE"
echo "Way back saved: $RESTORE"
```

This one file is the difference between "let me try this out" and "I don't
dare".

## 4.6 Publishing

The format for the KDE Store is a plain **`.tar.gz`**. There is no `.plasma`
format.

Two stumbling blocks: [verified against `/usr/share/knsrcfiles/`]

**Plasma Styles need a tag.** `plasma-themes.knsrc` filters with
`TagFilter=ghns_excluded!=1,plasma##version==5`. A Plasma Style without the
tag `plasma##version==5` does **not** appear under "Get New Plasma Styles",
not even in 2026.

**Global themes are flagged as executable.** `lookandfeel.knsrc` sets
`ContentWarning=Executables` because Look-and-Feel packages can contain
layout scripts. The user gets a warning. Another argument for
[not shipping `layouts/`](03-look-and-feel.md#panel-preset-instead-of-a-forced-layout).

### Licenses

For a project outside KDE none of this is mandatory, but it is cheap to have
and makes the project packageable (Fedora and Debian ask exactly for this):

- SPDX header in every text file:
  ```
  SPDX-FileCopyrightText: 2026 Name <mail@example.org>
  SPDX-License-Identifier: GPL-3.0-or-later
  ```
- `LICENSES/<SPDX-Id>.txt` for each license used (`reuse download <ID>`)
- Binary files via a `.license` sidecar or `REUSE.toml`
- For graphics, `CC-BY-SA-4.0` is the usual choice

For a retro recreation, the **origin of the assets** is the trickier question
than the file format. Fonts and graphics from a commercial operating system
are not automatically free, and neither are recreations. The license of every
font you adopt must be documented explicitly.

---

**Next:** [Chapter 5 — Testing](05-testing.md)
