# Building Well-Behaved Plasma 6 Themes

A guide that starts from the official KDE documentation and picks up where
it stops: how to build a theme so that people can **try it out safely** and
so that it stays **maintainable**.

Status: August 2026 · Reference system: Plasma 6.7.3, KF6, Qt 6, Fedora/Nobara 44

---

## Who should read this

Anyone who writes a Plasma theme and has seen a theme break more than it
beautified. The guide assumes you can read SVG and INI files. You do not
need C++.

## The chapters

| # | Chapter | What it covers |
|---|---|---|
| 1 | [The seven layers and their risk](01-layers-and-risk.md) | What a theme actually is, and which parts of it can make a computer unusable |
| 2 | [Plasma Style](02-plasma-style.md) | SVGs, 9-patch, `hint-*` IDs, color scheme stylesheets |
| 3 | [Look-and-Feel package](03-look-and-feel.md) | The bundle package, `contents/defaults`, and the panel trap |
| 4 | [Building and installing](04-build-and-install.md) | CMake, `kpackagetool6`, variants without duplicates |
| 5 | [Testing](05-testing.md) | Four stages: linter, single widget, session, VM |
| 6 | [When things go wrong](06-recovery.md) | Recovery commands, sorted by escalation level |

Plus the [reference card](reference.md): everything you need to look up, on one page.

---

## The five rules

If you read only one page, read this one.

**1. A theme that cannot be tried out safely is not a finished theme.**
The bar is not "looks good" but "the user can apply it, dislike it and be
back in ten seconds". Anything else is a prototype.

**2. Strictly separate what lives in `$HOME` from what reaches into the system.**
Everything under `~/.local/share/` can be repaired from a TTY in under a
minute. The login manager, Plymouth and GRUB run *before* login; if something
goes wrong there, you may need a live medium. These two classes never belong
in the same installation run.

**3. If you want to ship a panel layout, back up the user's first.**
A `contents/layouts/org.kde.plasma.desktop-layout.js` replaces all panels and
widgets when applied, and that cannot be undone. KDE asks first and does not
pre-check the option, but anyone who wants to see the full theme checks it.
A backup copy of `plasma-org.kde.plasma.desktop-appletsrc` turns this into a
way back. See [chapter 3.4](03-look-and-feel.md#34-the-panel-trap).

**4. Build variants from one source, not by copy-paste.**
Three color variants do not mean three SVG trees. Breeze solves this with
*one* SVG set and three color schemes. Copy, and you maintain every fix three
times, and forget it the third time.

**5. Bump `KPlugin.Version` with every release.**
This number is the key of the render cache
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). Without a bump, your
users see the old theme after the update and report bugs that do not exist.

---

## Why this guide exists

The official documentation at [develop.kde.org/docs/plasma/theme](https://develop.kde.org/docs/plasma/theme/)
is good, but it treats Plasma themes as a graphics task. The questions
projects actually fail on are different:

- Which part of my theme can make my user's computer unusable?
- Why does my SVG change have no effect? (Answer: [the cache](02-plasma-style.md#26-the-cache))
- How do I test this without sacrificing my own system? ([Chapter 5](05-testing.md))
- How do I maintain three variants without doing the work three times? ([Chapter 4](04-build-and-install.md))

In several places the official documentation is also out of date; the guide
names these places and says what applies instead.

## Verification levels

Statements are marked:

- **[verified]** — reproduced locally on Plasma 6.7.3
- **[source]** — read in the current KDE source code, with the path given
- **[uncertain]** — plausible but not verified; treat it as a guess

Where the official documentation says something different from the source
code, this is stated explicitly.
