# Theme Forge — ein lokales LLM als Motor für Plasma-Themes

Aus einer Stilbeschreibung („Red Alert 2“, „Fallout Pip-Boy“, „Jugendstil“)
entsteht ein komplettes, installierbares Plasma-6-Theme: Farbschema, Plasma
Style, Fensterdekoration, Look-and-Feel mit Startbildschirm, Hintergründe,
Konsole-Farben, Plymouth und GRUB — in 2–4 Varianten, wenn die Vorlage welche
hat.

```bash
./forge.py all "Red Alert 2 (Echtzeitstrategie, Westwood 2000): Sowjets und Alliierte" -o out/ra2
# → out/ra2/package/      installierbares Paket
#   out/ra2/preview.jpg   Vorschau (Desktop, GRUB, Plymouth je Variante)
#   out/ra2/spec.json     was das LLM entschieden hat
#   out/ra2/report.json   Werkzeuge, Prüfergebnis, Laufzeit

cd out/ra2/package
./install.sh --apply soviet         # nur ~/.local, kein sudo; rückgängig: ./uninstall.sh
sudo ./install-system.sh soviet     # Plymouth + GRUB, mit Sicherung; rückgängig: --revert
```

Unabhängig von `nt-legacy/`, `CDE/` und `tools/`: Die Generatoren hier sind
eigene Kopien (Projektregel in `../CLAUDE.md`).

## Wie es arbeitet

Das LLM schreibt **keine** SVG, QML oder Skripte. Es trifft Gestaltungs-
entscheidungen in einer kleinen, prüfbaren Spezifikation; alles Technische
erledigen deterministische Generatoren.

```
Anfrage ─► 1 Leitfarben-Abstimmung   7 kurze Befragungen, Mehrheit je Variante   (LLM, ~4 s)
        ─► 2 Design-Brief            Farben, Material, Formen, Motive            (LLM, Denkmodus, ~10 s)
        ─► 3 Spezifikation           JSON, per Grammatik an das Schema gebunden  (LLM, ~4 s)
        ─► 4 Prüfung + Reparatur     Fehler mit Pfad und konkretem Ersatzwert;
                                     nur das kaputte Teilstück wird neu erzeugt  (LLM, je <1 s)
        ─► 5 Bildplan                Szenen je Variante, Icon-Stilblatt          (LLM)
        ─► 6 Malen + Sichtprüfung    ComfyUI lokal; das LLM sieht jedes Icon an,
                                     misslungene werden neu gefasst und gemalt   (LLM + Bildmodell)
        ─► 7 Generatoren             Plasma-SVG, Aurorae, Farben, L&F, Icons, Plymouth, GRUB
        ─► 8 Paketprüfung + Vorschau Linter, Element-IDs, Kontraste, 9-Patch-Rendering
```

| Datei | Aufgabe |
|---|---|
| `forge.py` | Kommandozeile: `design`, `build`, `all`, `bench` |
| `forge/llm.py` | OpenAI-kompatibler Client (llama.cpp, Ollama, vLLM), `response_format: json_schema` |
| `forge/designer.py` | Leitfarben-Abstimmung, Brief, Spezifikation, gezielte Reparatur |
| `forge/spec.py` | Schema und semantische Prüfung (Kontraste, Modus, Leitfarbe, Marken, Bild-Prompt-Fallen) |
| `forge/palette.py` | 9 Grundfarben → volle Palette (Bevel, Hover, Signalfarben, Lesbarkeit) |
| `forge/plasmasvg.py` | Plasma-Style-SVGs (Kopie von `tools/gen-plasma-svg.py` + Fasen, Rundungen, Leuchtlinie) |
| `forge/aurorae.py` | Fensterdekoration (Eckformen, vier Knopfformen) |
| `forge/build.py` | Farbschema, Konsole, Look-and-Feel + Splash, Hintergrund-Paket |
| `forge/boot.py` | Plymouth (3 Layouts, Passwortabfrage) und GRUB (2 Layouts, eigene Schrift) |
| `forge/emblem.py` | Emblem aus einer Geometrie: Inkscape (flach) oder Blender (Metall, Cycles) |
| `forge/artplan.py` | Bildplan: Szenen je Variante, Icon-Stilblatt (oder `--themed-icons`) |
| `forge/iconset.py` | Icon-Katalog: 120 Bilder für 519 Namen, je Funktion + neutrales Bild + Familie |
| `forge/icons.py` | Malen, Bildprüfung, Reparaturschleife, Metallrahmen, Icon-Theme |
| `forge/imgcheck.py` | Sichtprüfung (LLM mit Bildverständnis), Gesichter, Doppelte |
| `forge/gpu.py` | schaltet die Grafikkarte zwischen llama-server und ComfyUI um |
| `forge/material.py` | Metalltextur für Dekoration und Panel |
| `forge/comfy.py` | ComfyUI: lokal (Z-Image Turbo, Standard) oder ai395 (Krea-2 Turbo) |
| `forge/frames.py` | 9-Patch-Rendering mit QtSvg, wie KSvg — für GRUB-Bilder und Vorschau |
| `forge/check.py` | Paketprüfung |
| `forge/installers.py` | `install.sh`, `uninstall.sh`, `install-system.sh` |
| `tests/ra2.expect.json` | Stilerwartung für den Zuverlässigkeitstest |
| `tests/build_many.py` | viele Spezifikationen bauen und prüfen (ohne ComfyUI) |

### Was das LLM entscheidet

Name, Beschreibung · Eckform (eckig/Fase/rund) und -größe · Bevel · Außenlinie ·
Leuchtkante · Titelleiste, Rahmen, Knopfform, Knopfbelegung · Schrift (aus 13
OFL-Schriften) · Emblemform und Werkzeug (Blender/Inkscape) · Boot-Layouts ·
je Variante: Leitfarbe, 9 Grundfarben, hell/dunkel, Bild-Prompt.

### Warum es zuverlässig ist

Gemessen auf der RTX 5080 (Qwen3.6-35B-A3B, IQ3, llama.cpp), Anfrage
„Red Alert 2 … Sowjets und Alliierte“, Stilprüfung = Titelleiste der Sowjets
rot auf dunklem Grund, der Alliierten blau:

| Stand | gültig | stiltreu |
|---|---|---|
| erste Fassung (ganze Spezifikation neu bei Fehlern) | 7/10 | 4/10 |
| + gezielte Teilreparatur, Fehlalarme behoben | 11/12 | 10/12 |
| + Leitfarbe, Titelleiste trägt sie | 20/20 | 18/20 |
| Bestätigung mit 30 Läufen | 27/30 | 23/30 |
| + Leitfarben-Abstimmung, lösbare Vorschläge | 29/30 | 29/30 |
| **Endstand** (`out/bench-final`) | **30/30** | **30/30** |

Ø 18,7 s pro Spezifikation, höchstens 26 s. Andere Vorlagen (Tron, Mac OS 9,
Pip-Boy, Bauhaus, Jugendstil): 20/20 gültig. 83 verschiedene Spezifikationen
bauen alle fehlerfrei (`tests/build_many.py`). Ein kompletter Lauf mit zwei
ComfyUI-Hintergründen dauert knapp 4 Minuten, davon 3½ Bildgenerierung.

Was die Zuverlässigkeit gebracht hat, in der Reihenfolge der Wirkung:

1. **Teilreparatur statt Neuschreiben.** Muss das Modell 900 Token
   wiederholen, um ein Wort zu ersetzen, schleppt es den Fehler mit.
   Bekommt es nur das kaputte Teilstück mit eigenem Teilschema, klappt es.
2. **Konkrete Werte in Fehlermeldungen.** „Text dunkler wählen“ wird oft
   ignoriert, „setze colors.text auf #161616“ fast nie.
3. **Die eigene Aussage festnageln.** Erst `look` (ein Satz) und `lead`
   (Leitfarbe) schreiben lassen, dann prüfen, ob die Titelleiste sie trägt.
4. **Mehrheitsentscheid gegen Wissensschwankung.** Einzeln nannte das Modell
   die Sowjets mal rot, mal schwarz, mal oliv; 7 kurze Befragungen
   bündeln das zuverlässig.
5. **Deterministische letzte Stufe** nur für Technik ohne Gestaltungswert
   (Pflichtknöpfe, verbotene Wörter im Bild-Prompt) — sichtbar als
   „Automatik“ im Protokoll, im Endstand 1 von 30.

### Fallen, die die Prüfung abfängt

* Bildmodelle malen jedes Wort: „Platz für Desktop-Symbole“ ergab gemalte
  Icons, „warning signs“ Fantasieschrift. Solche Wörter sind im Bild-Prompt
  gesperrt.
* Marken: feste Liste plus der Titel der Anfrage selbst (`Red Alert 2`,
  `Pip-Boy`); `--avoid` ergänzt weitere.
* Plasma schreibt Panel-Text in der normalen Textfarbe → `text` muss auch
  auf `panel` lesbar sein.

## In der VM geprüft (plasma-lab, Fedora 44, Plasma 6.7.4)

Installieren → anwenden (Sowjets) → Neuanmeldung → Variante wechseln
(Alliierte) → `install-system.sh` → Neustart mit GRUB, Plymouth, Splash →
`--revert` + `uninstall.sh` → Neustart: Desktop wieder exakt wie vorher.
Gefunden und behoben:

* Knopfreihenfolge, Titelschrift und Konsole-Profil setzt ein Global Theme
  nicht — `install.sh --apply` schreibt sie ausdrücklich (mit Sicherung).
* Fedora fehlt `plymouth-plugin-script`; der Installer brach mittendrin ab.
  Jetzt Vorabprüfung, nichts wird geändert, solange etwas fehlt.
* Unter Secure Boot lädt GRUB keine Schriftdateien (auch in `CDE/TESTING.md`
  beschrieben) — erkannt, dann eingebaute Unifont.
* Variable Schriften (Oxanium, Cinzel …) liefern ohne Angabe die dünnste
  Instanz; für GRUB/Plymouth/Schriftzüge wird eine feste Instanz (600) erzeugt.
* Der GRUB-Auswahlbalken ragte in den nächsten Eintrag (Ecken liegen außen).
* Hinweis „splash fehlt“ war auf Fedora falsch (dort `rhgb`).
* Über SSH zeigt `kreadconfig6` die Werte eines Global Themes nicht (sie liegen
  in `~/.config/kdedefaults/`) — kein Fehler des Themes.

## VM-Test (drei Umgebungen)

`./forge.py vmtest out/<x> [--vm fedora,ubuntu,artix] [--variant <id>] [--no-reset]`
setzt jede Test-VM auf ihren Snapshot `clean` zurück, überträgt das Paket,
ruft `install.sh --apply` auf, macht ein Foto, ruft `uninstall.sh` auf und
vergleicht die beobachteten Einstellungen vorher/nachher (`forge/vmtest.py`,
Ergebnis in `vmtest.json`, Fotos `vm-<umgebung>-*.png`):

| Name | VM | Was sie abdeckt |
|---|---|---|
| fedora | plasma-lab (`vm/lab.env`) | Fedora 44, systemd, Plasma 6.7 |
| ubuntu | ubuntu-lab (`vm/ubuntu.env`) | Ubuntu 26.04 LTS, ältere Plasma-Fassung |
| artix | artix-lab (`vm/artix.env`) | Artix/OpenRC, **kein systemd**, Plasma 6.8 |

## Systemschicht

`install-system.sh` prüft vorab (Plymouth-Script-Plugin, GRUB-Werkzeuge),
ändert erst dann, sichert `/etc/default/grub` und das vorige Plymouth-Theme
nach `/var/lib/theme-forge/<id>/` und nimmt mit `--revert` alles zurück.
`GRUB_TERMINAL_OUTPUT=console` (Fedora-Standard) wird auskommentiert, sonst
bleibt das Menü im Textmodus. Fedora braucht `plymouth-plugin-script`.

## Grenzen

* Die Stilprüfung misst Farbtreue, nicht Geschmack. Bildauswahl, Proportionen
  und „wirkt es wie die Vorlage“ bleiben eine menschliche Prüfung — die
  Vorschau ist dafür da.
* Mauszeiger und kleine Status-/Aktionssymbole kommen aus Breeze; die
  519 Namen des Katalogs malt der Motor selbst.
* Die Login-Oberfläche (Plasma Login Manager) hat keine QML-Themes; nur der
  Sperrbildschirm bekommt den Hintergrund.
* Ohne ComfyUI gibt es prozedurale Hintergründe (`--no-comfy`).
* GRUBs Terminalfenster („Booting …“) hat einen Rahmen im Theme-Stil, innen
  bleibt es schwarz — die Farbe lässt sich per Theme nicht setzen.
* Die Stilprüfung ist bisher nur für „Red Alert 2“ hinterlegt; für andere
  Vorlagen wird nur Gültigkeit gemessen.
* Generierte Bilder sind Dekoration, keine Wiedergabe der Vorlage; Namen
  und Logos der Vorlage kommen bewusst nicht vor.

## Icons: Katalog + Stilblatt

Was ein Icon zeigt, steht fest im Katalog (`forge/iconset.py`): Funktion und
ein neutrales, gegenständliches Bild ohne Schrift. Ordner teilen einen
Behälter, Dateitypen ein Blatt, nur das Zeichen darauf wechselt. Das LLM
schreibt pro Theme nur ein **Stilblatt** (Malweise, Farben, Material,
Details, Licht, Hintergrund, Ordner, Blatt). Geprüft wird, dass es keine
Gegenstände nennt (sonst steht in jedem Icon ein Panzer), keine Rahmen oder
Kacheln (den Rahmen setzt der Motor je Variante) und keine Hex-Codes.

Nach dem Malen beschreibt das LLM jedes Bild, ohne zu wissen, was es zeigen
soll, und vergleicht danach: Schrift, ungewollte Personen, leere Bilder,
falsches Motiv. Einzelne Fehlbilder fasst es neu, ab 40 % Fehlern schreibt
es das Stilblatt neu. Dafür braucht der llama-server `--mmproj` (Qwen3.6:
`mmproj-F16.gguf`, mit `--no-mmproj-offload` auf der CPU — auf der GPU
verdrängte es Modellteile, 176 → 50 tok/s). Ohne Bildverständnis prüft
der Motor nur Gesichter (OpenCV) und Doppelte.

## Grafikkarte teilen

LLM (~14 GB) und Z-Image passen nicht gleichzeitig in 16 GB. `forge/gpu.py`
hält den LLM-Dienst (`FORGE_LLM_SERVICE`, Standard `llama-qwen36.service`)
für Bildläufe an, startet ein lokales ComfyUI (`/data/ComfyUI`, Port 8189)
und stellt am Ende den Ausgangszustand wieder her — auch bei Abbruch.

## Umgebung

`FORGE_LLM` (Standard `http://127.0.0.1:8090/v1`, der llama-server auf 245k),
`FORGE_COMFY` (Standard lokal `http://127.0.0.1:8189`; ai395 mit
`http://192.168.178.54:8188`, Zugang aus `~/.config/comfyui/claude-zugang`),
`FORGE_IMAGE_MODEL` (`zimage`/`krea2`), `FORGE_LLM_SERVICE`, `FORGE_COMFY_DIR`. Python ≥ 3.11 mit Pillow und PySide6;
`inkscape`, `blender`, `grub2-mkfont`.
