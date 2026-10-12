# 6. When things go wrong

Sorted by escalation level. Always start with the lowest one that fits your
situation.

All commands verified on Plasma 6.7.3.

---

## First: what is actually set?

```bash
kreadconfig6 --file plasmarc   --group Theme   --key name              # Plasma Style
kreadconfig6 --file kdeglobals --group General --key ColorScheme
kreadconfig6 --file kdeglobals --group KDE     --key widgetStyle
kreadconfig6 --file kdeglobals --group Icons   --key Theme
kreadconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage
kreadconfig6 --file ksplashrc  --group KSplash  --key Theme
kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library
kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme
```

These eight lines are also what an installer should back up **before** its
first change. See
[chapter 4.5](04-build-and-install.md#45-rollback-is-part-of-the-installation).

---

## Level 1 — the desktop still works

Everything back to Breeze:

```bash
plasma-apply-lookandfeel --apply org.kde.breeze.desktop
plasma-apply-desktoptheme default
plasma-apply-colorscheme BreezeLight
```

Note: Breeze's Plasma Style is called **`default`**, not `breeze`.

## Level 2 — panel gone, session still alive

Symptom: no panel, no desktop background, but windows still work. You can
get a terminal via a keyboard shortcut or from a running program.

```bash
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

Classic variants:
```bash
kquitapp6 plasmashell && kstart plasmashell
plasmashell --replace &
```

**To reassure you:** there is no endless crash loop.
`plasma-plasmashell.service` has `StartLimitBurst=3` within 60 seconds and
`--no-respawn`. After three failed attempts, systemd gives up. KWin keeps
running, your windows stay.

## Level 3 — session unusable, TTY needed

`Ctrl`+`Alt`+`F3` takes you to a text console. Log in, then:

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)

kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file plasmarc   --group Theme   --key name default
kwriteconfig6 --file kdeglobals --group General --key ColorScheme BreezeLight
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle Breeze
kwriteconfig6 --file kdeglobals --group Icons   --key Theme breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme   Breeze

rm -rf ~/.local/share/plasma/desktoptheme/<my-theme>
rm -rf ~/.local/share/plasma/look-and-feel/<my-theme>
rm -f  ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
```

Then log out and log in again.

### Last resort: reset the panel configuration

If a layout script has wrecked the panels:

```bash
mv ~/.config/plasma-org.kde.plasma.desktop-appletsrc{,.bak}
```

**This deletes all widget settings** and gives you the default layout at the
next start. The `.bak` stays; usually nothing can be rescued from it, but you
can always throw it away later.

## Level 4 — the login screen no longer appears

Now only a TTY (if reachable) or a live medium helps.

```bash
# Plasma Login Manager (Fedora 44+, Nobara, KDE Linux)
sudo systemctl restart plasmalogin

# SDDM (older systems)
sudo sed -i 's/^Current=.*/Current=breeze/' /etc/sddm.conf.d/*.conf
sudo systemctl restart sddm
```

**The way out that always works:** turn off graphical login and repair in
text mode:

```bash
sudo systemctl set-default multi-user.target
sudo reboot
# ... repair ...
sudo systemctl set-default graphical.target
```

## Level 5 — the computer no longer boots

If Plymouth or GRUB were touched. Boot a live medium, mount the system,
chroot:

```bash
# reset Plymouth
sudo plymouth-set-default-theme -R bgrt        # Fedora default
sudo dracut -f --regenerate-all                # rebuild the initramfs

# reset GRUB
sudo sed -i '/^GRUB_THEME=/d' /etc/default/grub
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

On Debian/Ubuntu the last two are `update-initramfs -u` and `update-grub`.

**If you end up here, the mistake was not the theme but the decision to
install it on your work machine.** See
[chapter 5.4](05-testing.md#54-stage-4--full-installation-in-the-vm).

---

## The boundary that matters

| Safe — `$HOME` only, repairable via TTY | Dangerous — system-wide, before login |
|---|---|
| `~/.local/share/plasma/desktoptheme/` | `/usr/share/plasma/*` (collides with package updates) |
| `~/.local/share/plasma/look-and-feel/` | `/usr/share/sddm/themes/`, `/etc/sddm.conf.d/` |
| `~/.local/share/color-schemes/` | `/etc/plasmalogin.conf*` |
| `~/.local/share/aurorae/themes/` | `/usr/share/plymouth/`, `dracut -f` |
| `~/.local/share/icons/`, `wallpapers/` | `/boot/grub2/`, `grub2-mkconfig` |
| `~/.config/*rc`, `~/.cache/*` | `/usr/share/fonts/` instead of `~/.local/share/fonts/` |

**Rule of thumb:** if an installation step asks for `sudo`, it belongs in a
separate script with its own warning, not in the run that someone executes
who "just wants to try out the theme".

---

**Back:** [Overview](README.md) · [Reference card](reference.md)
