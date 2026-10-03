# Hintergrundbilder

28 Bilder in 3840×2160, jedes hell (`<key>.jpg`) und dunkel (`<key>-dark.jpg`).
`build.py` packt jedes Motiv als Plasma-Hintergrund `org.cde.copper.<key>` mit
`images/` und `images_dark/`. Plasma nimmt die dunkle Fassung automatisch, solange
ein dunkles Farbschema aktiv ist. Die Liste mit Namen steht in `build.py`
(`PICTURES`), `manage.py` übernimmt sie für Installation und Deinstallation.

Bis auf CDE Strömung sind die Bilder KI-generiert und reine Dekoration: keine
echten Aufnahmen, keine Messdaten. Logos, Schrift und Markenzeichen sind bewusst
herausgehalten.

## Die Sätze

| Satz | Motive | Farben |
|---|---|---|
| Copper | Altai, Canopée, Cluster, Fluss, Kaskade | Copper, im Stil der Plasma-5-Hintergründe |
| CDE-Paletten | Monolith, Polarlicht, Mesa, Riff, Origami, Bauhaus, Weinberg, Orbit | je eine CDE-Palette (siehe `build.py`) |
| Workstation-Arbeit | Chipstadt, CAD, Molekül, Sequenz, Druckvorstufe, Schnittplatz, MRT, Mischpult, VLSI, Strömung | wofür CDE-Workstations in den 90ern liefen |
| Abstrakt | Kristall, Marmor, Düne | nach den Mustern der beliebtesten KDE-Store-Hintergründe |
| 90er-Illustration | Aquarell, Panorama | Software-Cover-Illustration der späten 90er, ohne Figuren oder Logos der Vorlagen |

## Wie sie entstanden sind

Erzeugt mit ComfyUI auf ai395, Modell Krea-2 Turbo fp8 (8 Steps, cfg 1).
Die Skripte liegen unter `gen/`:

- `gen.py` schickt eine Jobliste (JSON) an ComfyUI und holt die Bilder. Es
  kennt Text-zu-Bild, img2img (`init_file`, `denoise`), reines Hochskalieren
  (`upscale_only`) und Vorrang in der Warteschlange (`front`). Geht ein Job
  verloren, weil der Server neu startet, reicht es ihn neu ein. Die Zugangsdaten
  liest es aus `~/.config/comfyui/claude-zugang`, sie gehören nicht ins Repo.
- `prompts.py` (Copper-Satz), `prompts2.py` (alle anderen) und
  `prompts_acro.py` (90er-Illustration) enthalten die Prompts. `prompts2.py`
  enthält auch Rost und Seismik, die nicht übernommen wurden.
- `auswahl.json` hält fest, welcher Seed je Motiv genommen wurde und mit welchen
  Farben die Dunkelfassung entstand.

Ablauf je Motiv:

1. Hell: Text-zu-Bild in 1920×1088 (Aquarell und Panorama in 1024×576),
   mehrere Seeds, einer ausgewählt.
2. Dunkel: `dark.py` dunkelt das helle Bild mit gleicher Komposition ab: neutrale
   Flächen werden auf zwei Nachtfarben der Palette abgebildet, gesättigte Akzente
   bleiben leuchtend (`warm`, `sat` oder `none`). Danach folgt img2img mit dem
   Dunkel-Prompt und demselben Seed, meist Denoise 0.45–0.5. Erst dadurch stimmen
   Licht und Glanz.
3. Beide Fassungen gehen durch 4x-UltraSharp, `finish.py` macht daraus
   3840×2160 JPEG q90.

CDE Strömung ist gerechnet statt generiert: `cfd.py` berechnet die
Potentialströmung um ein Joukowski-Profil mit Zirkulation (Kutta-Bedingung).
Die Linien sind Stromlinien, der Hintergrund ist der Druckbeiwert. Hell und
dunkel stammen aus derselben Rechnung, direkt in 4K.
