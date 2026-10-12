# Wallpapers

40 pictures at 3840×2160, each light (`<key>.jpg`) and dark (`<key>-dark.jpg`).
`build.py` packages every motif as the Plasma wallpaper `org.cde.copper.<key>` with
`images/` and `images_dark/`. Plasma picks the dark version automatically while
a dark colour scheme is active. The list with names is in `build.py`
(`PICTURES`); `manage.py` takes it over for installation and uninstallation.

Except for CDE Flow the pictures are AI-generated and pure decoration: no
real photographs, no measurement data. Logos, lettering and trademarks are deliberately
kept out.

## The sets

| Set | Motifs | Colours |
|---|---|---|
| Copper | Altai, Canopée, Cluster, River, Cascade | Copper, in the style of the Plasma 5 wallpapers |
| CDE palettes | Monolith, Aurora, Mesa, Reef, Origami, Bauhaus, Vineyard, Orbit | one CDE palette each (see `build.py`) |
| Workstation work | Chip City, CAD, Molecule, Sequence, Prepress, Editing Suite, MRI, Mixing Desk, VLSI, Flow | what CDE workstations ran for in the 90s |
| Abstract | Crystal, Marble, Dune | after the patterns of the most popular KDE Store wallpapers |
| 90s illustration | Watercolour, Panorama | late-90s software cover illustration, without figures or logos of the originals |
| Two screens | Dune Left/Right, Space Left/Right | one panorama each, split across 32 and 27 inches |
| Landscapes | Alps, Dolomites, Elbe Sandstone, Fjord, Iceland, Black Forest, Tuscany, Wadden Sea | photographs, by day and by night |

## How they were made

Generated with ComfyUI on ai395, model Krea-2 Turbo fp8 (8 steps, cfg 1).
The scripts are under `gen/`:

- `gen.py` sends a job list (JSON) to ComfyUI and fetches the pictures. It
  knows text-to-image, img2img (`init_file`, `denoise`), pure upscaling
  (`upscale_only`) and queue priority (`front`). If a job gets lost because
  the server restarts, it resubmits it. It reads the credentials
  from `~/.config/comfyui/claude-zugang`; they do not belong in the repo.
- `prompts.py` (Copper set), `prompts2.py` (all others) and
  `prompts_acro.py` (90s illustration) contain the prompts. `prompts2.py`
  also contains Rost (rust) and Seismik (seismics), which were not adopted.
- `selection.json` records which seed was taken per motif and which
  colours the dark version was made with.

Process per motif:

1. Light: text-to-image at 1920×1088 (Aquarell and Panorama at 1024×576),
   several seeds, one selected.
2. Dark: `dark.py` darkens the light picture keeping the same composition: neutral
   areas are mapped onto two night colours of the palette, saturated accents
   stay bright (`warm`, `sat` or `none`). Then follows img2img with the
   dark prompt and the same seed, usually denoise 0.45–0.5. Only this gets
   light and gloss right.
3. Both versions go through 4x-UltraSharp; `finish.py` turns them into
   3840×2160 JPEG q90.

CDE Flow is computed rather than generated: `cfd.py` calculates the
potential flow around a Joukowski airfoil with circulation (Kutta condition).
The lines are streamlines, the background is the pressure coefficient. Light and
dark come from the same calculation, directly in 4K.

## One picture across two screens

`panorama/duene.jpg` and `panorama/weltraum.jpg` (each with `-dark`) are wide pictures
(10752×3200, Krea-2 at 2688×800, prompts in `gen/dune_wide_prompt.json` and
`gen/space_wide_prompt.json`,
then 4x-UltraSharp). `gen/span.py` splits it by millimetres across two
screens, top-aligned, leaving out the strip behind the bezels. That way
the lines run straight across the bezel even though the pixel densities differ.
The left and right halves are cut for a 32-inch screen
(698×393 mm) to the left of a 27-inch screen (597×336 mm) with a 20 mm
gap. For other screens:

    python3 gen/span.py panorama/duene-dark.jpg left.jpg right.jpg \
        --left 698x393 --right 597x336 --gap 20

`kscreen-doctor -j` gives the dimensions in millimetres (`sizeMM`). Plasma does not
stretch one picture across several screens; each gets its half separately.

## Tiles

`tiles/` contains 20 seamless material tiles at 1024×1024, in natural colour:
flokati, moss, felt, cork, terrazzo, linen, handmade paper, sand (raked),
slate, travertine, rattan, velour, knit, lava stone, gravel, water,
frost flowers, perforated metal, acoustic foam and leather. They are meant to be
tiled pixel for pixel, like the CDE backdrops, just contemporary.

- Krea-2 generates each material as a top view (prompts in
  `gen/prompts_tiles.py`, seed 1301).
- `gen/tile.py seamless` turns it into a tile. First it removes the
  large-scale brightness gradient (otherwise the vignette repeats as a
  checkerboard), then it blends the picture with its half-shifted copy
  through an irregular mask. This works for irregular materials, not
  for grids.
- Perforated metal is therefore computed (`gen/tile.py lochblech`): brushed
  aluminium with a staggered hole grid that divides the tile exactly.
- `gen/tile.py tint --palette <name>` recolours a tile into a CDE palette.
  To do so it maps the brightness onto three colours of the workspace set
  (shadow at the bottom, background, light at the top), just as CDE draws its backdrops in the
  colours of the workspace.

## Landscapes

Eight photographic landscapes, each light and as a night shot: Alps,
Dolomites, Elbe Sandstone Mountains, fjord, Iceland, Black Forest, Tuscany and the Wadden Sea.
Prompts in `gen/prompts_land.py`, selection and night colours in
`gen/picks_land.json`. The night is made as above, with denoise 0.55, so that
the day photo becomes a real night shot.
