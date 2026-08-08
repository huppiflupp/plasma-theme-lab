# plasma-theme-lab

Werkstatt für Plasma-6-Themes: eine Wegwerf-VM zum Testen, ein Linter für
Plasma-SVGs, ein Leitfaden — und die Referenzquellen von KDE zum Nachschlagen.

Entstanden aus der Arbeit an [NiceOS9](https://github.com/huppiflupp/NiceOS9-theme),
aber nicht darauf beschränkt.

---

## Was hier liegt

```
plasma-theme-lab/
├── guide/          Leitfaden: konforme Plasma-6-Themes bauen
├── tools/          lint-plasma-svg.py — prüft, was Plasma stillschweigend verschluckt
├── vm/             Test-VM (Fedora 44 KDE), unbeaufsichtigt aufgesetzt
├── tests/          Testläufe und Screenshots
├── reference/      geklonte KDE-Quellen (breeze, libplasma, plasma-workspace)
└── niceos9/        das zu überarbeitende Theme
```

## Schnellstart

**Ein Theme prüfen — dauert Sekunden, braucht keine VM:**

```bash
tools/lint-plasma-svg.py niceos9/desktoptheme/niceos9-dark \
    --vergleich reference/libplasma/src/desktoptheme/breeze
```

**Ein Theme in der VM ausprobieren:**

```bash
vm/build-vm.sh                      # einmalig, ~30 min
vm/provision.sh                     # Werkzeuge, Autologin
vm/vmctl.sh snap create clean       # der Ausgangszustand

vm/vmctl.sh reset                   # zurück auf clean, Sekunden
vm/vmctl.sh push niceos9 /home/tester/theme
vm/vmctl.sh ssh 'cd theme && ./install.sh'
vm/vmctl.sh shot befund.png
```

## Die VM

Fedora 44 KDE (Plasma 6), 6 GB RAM, 4 vCPU, 40 GB. Unbeaufsichtigt per
Kickstart installiert, Autologin in die Plasma-Wayland-Session, SSH mit
eigenem Schlüssel.

Sie läuft unter `qemu:///system` — der libvirt-Dienst ist socket-aktiviert
und die Gruppenmitgliedschaft `libvirt` reicht. **Kein sudo nötig.**

```bash
vm/vmctl.sh status            # Zustand, IP, Snapshots
vm/vmctl.sh ssh [befehl]      # Kommando im Gast
vm/vmctl.sh push <von> <nach> # Dateien hinein
vm/vmctl.sh shot [datei]      # Screenshot
vm/vmctl.sh snap create|list|revert|rm
vm/vmctl.sh reset             # zurück auf 'clean'
vm/vmctl.sh viewer            # grafische Konsole (interaktiv)
vm/vmctl.sh viewer-bg         # dito, abgeloest im Hintergrund
```

**Screenshots kommen vom Hypervisor**, nicht aus dem Gast (`virsh
screenshot`). Das funktioniert auch dann noch, wenn Plasma abgestürzt ist
oder keine Session mehr läuft — genau der Fall, der bei Theme-Tests
interessant ist. Ein Werkzeug im Gast kann dann per Definition nichts mehr
liefern.

**Der Snapshot ist der eigentliche Trick.** Ohne ihn testet man beim zweiten
Durchlauf auf den Resten des ersten.

### Grafisch reinschauen

```bash
vm/vmctl.sh viewer
# entspricht: virt-viewer --attach -c qemu:///system plasma-lab
```

`--attach` ist nötig, weil die VM mit `spice,listen=none` läuft — SPICE
lauscht auf keinem Netzwerk-Port. Ohne `--attach` meldet virt-viewer
"Verbindung fehlgeschlagen".

`vmctl.sh viewer` läuft im Vordergrund und blockiert das Terminal. Wer den
Betrachter aus einem Skript oder Werkzeug heraus starten will, nimmt
`vmctl.sh viewer-bg`: Das legt eine eigene systemd-User-Unit an, die die
Prozessgruppe des Aufrufers überlebt. `nohup` und `setsid` reichen dafür
nicht — Werkzeuge, die ihre Prozessgruppe nach dem Befehl abräumen,
erwischen den Prozess trotzdem.

## Der Linter

Plasma meldet fehlende SVG-Element-IDs **nicht** — ein fehlendes
`hover-center` äußert sich nur darin, dass der Hover-Effekt ausbleibt. Es
gibt dafür kein offizielles Werkzeug; auch KDEs CI prüft SVG-Struktur nicht.

`tools/lint-plasma-svg.py` schließt diese Lücke. Er prüft 9-Patch-Sätze je
Zustandspräfix, Farbschema-Anbindung, `currentColor`, Insets und die
Pflichtfelder in `metadata.json`.

**Kalibriert gegen Breeze:** Die Referenzimplementierung läuft mit null
Fehlern durch. Ein Linter, der das Original anmeckert, meckert falsch.

## Der Gerüst-Generator

Eine Plasma-SVG ist kein Bild, sondern ein Atlas: Alle Zustände eines
Widgets liegen nebeneinander im selben Koordinatenraum, Plasma schneidet
sie über Element-IDs heraus. Ein `button.svg` braucht so 40+ exakt
benannte Objekte — und ein Tippfehler in einer ID wird stillschweigend
ignoriert.

`tools/gen-plasma-svg.py` erzeugt diese Struktur aus Parametern:

```bash
tools/gen-plasma-svg.py --liste                     # was es gibt
tools/gen-plasma-svg.py button                      # nach stdout
tools/gen-plasma-svg.py --alle -o desktoptheme/meintheme/
tools/gen-plasma-svg.py button --palette platinum-dark --stil flach --rahmen 2
```

Kennt zwölf Widget-Typen mit ihren Zustandssätzen (aus dem Breeze-Quellbaum
abgeleitet), setzt `hint-*`-Marker, Masken und das
`current-color-scheme`-Stylesheet. Zustände werden sinnvoll unterschieden —
`pressed` dreht den 3D-Rahmen um, aus herausstehend wird eingedrückt.

Das Ergebnis ist bearbeitbares SVG: In Inkscape öffnen und die Flächen
gestalten, ohne die IDs anzufassen. Oder die Palette in `PALETTEN`
anpassen und neu erzeugen.

**Gegenprobe:** Alle zwölf erzeugten Dateien laufen fehlerfrei durch
`lint-plasma-svg.py`.

## Der Leitfaden

[`guide/`](guide/README.md) — sechs Kapitel. Er wiederholt nicht die
KDE-Doku, sondern behandelt, woran Projekte scheitern:

1. [Die sieben Ebenen und ihr Risiko](guide/01-ebenen-und-risiko.md)
2. [Plasma Style](guide/02-plasma-style.md) — SVGs, 9-Patch, hints, Farbschemata
3. [Look-and-Feel-Paket](guide/03-look-and-feel.md) — und die Panel-Falle
4. [Bauen und Installieren](guide/04-bauen-und-installieren.md) — Varianten ohne Duplikate
5. [Testen](guide/05-testen.md) — vier Stufen
6. [Wenn es schiefgeht](guide/06-recovery.md) — Rettung nach Eskalationsstufe

Dazu die [Referenzkarte](guide/referenz.md).

Aussagen sind als *geprüft*, *Quelle* oder *unsicher* markiert. Wo die
offizielle Doku etwas anderes sagt als der Quellcode, steht das dabei.

## Referenzquellen

`reference/` enthält flache Klone:

| Verzeichnis | Was drin ist |
|---|---|
| `libplasma/src/desktoptheme/breeze/` | **der Breeze Plasma Style** — 43 Widget-SVGs |
| `libplasma/src/desktoptheme/breeze-light/` | eine Variante *ohne* SVGs — das Vorbild für Varianten |
| `breeze/` | Qt-Style (`kstyle/`) und Fensterdekoration (`kdecoration/`) |
| `plasma-workspace/` | Look-and-Feel-Pakete, SDDM-Theme |

**Häufigster Irrtum:** Das Repo `plasma/breeze` enthält keinen Plasma Style.
Der liegt in `libplasma`.

## Grundregeln

1. Ein Theme, das man nicht gefahrlos ausprobieren kann, ist kein fertiges Theme.
2. Was in `$HOME` lebt, und was ins System greift, gehören in getrennte Skripte.
3. Wenn du ein Panel-Layout ausliefern willst, sichere vorher das des Nutzers.
4. Baue Varianten aus einer Quelle, nicht per Copy-Paste.
5. Zähle `KPlugin.Version` bei jedem Release hoch — sie ist der Cache-Schlüssel.
