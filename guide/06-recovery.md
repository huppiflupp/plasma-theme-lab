# 6. Wenn es schiefgeht

Nach Eskalationsstufe sortiert. Fang immer bei der niedrigsten an, die auf
deine Lage passt.

Alle Kommandos auf Plasma 6.7.3 geprüft.

---

## Zuerst: Was ist überhaupt gesetzt?

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

Diese acht Zeilen sind auch das, was ein Installer **vor** seiner ersten
Änderung sichern sollte. Siehe
[Kapitel 4.5](04-bauen-und-installieren.md#45-rollback-ist-teil-der-installation).

---

## Stufe 1 — Die Oberfläche funktioniert noch

Alles zurück auf Breeze:

```bash
plasma-apply-lookandfeel --apply org.kde.breeze.desktop
plasma-apply-desktoptheme default
plasma-apply-colorscheme BreezeLight
```

Beachte: Der Plasma Style von Breeze heißt **`default`**, nicht `breeze`.

## Stufe 2 — Panel weg, Session lebt noch

Symptom: Kein Panel, kein Desktop-Hintergrund, aber Fenster funktionieren
noch. Ein Terminal bekommst du über ein Tastenkürzel oder aus einem
laufenden Programm heraus.

```bash
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
systemctl --user restart plasma-plasmashell.service
```

Klassische Varianten:
```bash
kquitapp6 plasmashell && kstart plasmashell
plasmashell --replace &
```

**Zur Beruhigung:** Es gibt keine endlose Absturzschleife.
`plasma-plasmashell.service` hat `StartLimitBurst=3` in 60 Sekunden und
`--no-respawn`. Nach drei Fehlversuchen gibt systemd auf. KWin läuft
weiter, deine Fenster bleiben.

## Stufe 3 — Session unbrauchbar, TTY nötig

`Strg`+`Alt`+`F3` bringt dich auf eine Textkonsole. Anmelden, dann:

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)

kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file plasmarc   --group Theme   --key name default
kwriteconfig6 --file kdeglobals --group General --key ColorScheme BreezeLight
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle Breeze
kwriteconfig6 --file kdeglobals --group Icons   --key Theme breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme   Breeze

rm -rf ~/.local/share/plasma/desktoptheme/<mein-theme>
rm -rf ~/.local/share/plasma/look-and-feel/<mein-theme>
rm -f  ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
```

Dann abmelden und neu anmelden.

### Notnagel: Panel-Konfiguration zurücksetzen

Wenn ein Layout-Skript die Panels zerlegt hat:

```bash
mv ~/.config/plasma-org.kde.plasma.desktop-appletsrc{,.bak}
```

**Das löscht alle Widget-Einstellungen** und gibt dir beim nächsten Start
das Standardlayout. Die `.bak` bleibt liegen — meist ist daraus nichts mehr
zu retten, aber wegwerfen kann man sie später immer noch.

## Stufe 4 — Es kommt keine Anmeldemaske mehr

Jetzt hilft nur noch ein TTY (falls erreichbar) oder ein Live-Medium.

```bash
# Plasma Login Manager (Fedora 44+, Nobara, KDE Linux)
sudo systemctl restart plasmalogin

# SDDM (ältere Systeme)
sudo sed -i 's/^Current=.*/Current=breeze/' /etc/sddm.conf.d/*.conf
sudo systemctl restart sddm
```

**Der Ausweg, der immer funktioniert** — grafische Anmeldung abschalten und
im Textmodus reparieren:

```bash
sudo systemctl set-default multi-user.target
sudo reboot
# ... reparieren ...
sudo systemctl set-default graphical.target
```

## Stufe 5 — Der Rechner startet nicht mehr

Wenn Plymouth oder GRUB angefasst wurden. Live-Medium booten, System
einhängen, chrooten:

```bash
# Plymouth zurücksetzen
sudo plymouth-set-default-theme -R bgrt        # Fedora-Standard
sudo dracut -f --regenerate-all                # initramfs neu bauen

# GRUB zurücksetzen
sudo sed -i '/^GRUB_THEME=/d' /etc/default/grub
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

Auf Debian/Ubuntu heißen die letzten beiden `update-initramfs -u` und
`update-grub`.

**Wenn du hier landest, war der Fehler nicht das Theme, sondern die
Entscheidung, es auf dem Arbeitsrechner zu installieren.** Siehe
[Kapitel 5.4](05-testen.md#54-stufe-4--vollinstallation-in-der-vm).

---

## Die Grenze, um die es geht

| Sicher — nur `$HOME`, per TTY reparierbar | Gefährlich — systemweit, vor dem Login |
|---|---|
| `~/.local/share/plasma/desktoptheme/` | `/usr/share/plasma/*` (kollidiert mit Paketupdates) |
| `~/.local/share/plasma/look-and-feel/` | `/usr/share/sddm/themes/`, `/etc/sddm.conf.d/` |
| `~/.local/share/color-schemes/` | `/etc/plasmalogin.conf*` |
| `~/.local/share/aurorae/themes/` | `/usr/share/plymouth/`, `dracut -f` |
| `~/.local/share/icons/`, `wallpapers/` | `/boot/grub2/`, `grub2-mkconfig` |
| `~/.config/*rc`, `~/.cache/*` | `/usr/share/fonts/` statt `~/.local/share/fonts/` |

**Faustregel:** Wenn ein Installationsschritt nach `sudo` fragt, gehört er
in ein eigenes Skript mit eigener Warnung — und nicht in den Durchlauf, den
jemand ausführt, der „das Theme mal ausprobieren" will.

---

**Zurück:** [Übersicht](README.md) · [Referenzkarte](referenz.md)
