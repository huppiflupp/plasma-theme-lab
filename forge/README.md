# Theme Forge: a local LLM as the engine for Plasma themes

From a style description ("Red Alert 2", "Fallout Pip-Boy", "Art Nouveau")
comes a complete, installable Plasma 6 theme: colour scheme, Plasma style,
window decoration, look-and-feel with splash screen, wallpapers, Konsole
colours, Plymouth and GRUB, in 2–4 variants when the model has them.
Everything it writes (descriptions, READMEs, store texts) is in English.

```bash
./forge.py all "Red Alert 2 (real-time strategy, Westwood 2000): Soviets and Allies" -o out/ra2
# → out/ra2/package/      installable package
#   out/ra2/preview.jpg   preview (desktop, GRUB, Plymouth per variant)
#   out/ra2/spec.json     what the LLM decided
#   out/ra2/report.json   tools, check result, run time

cd out/ra2/package
./install.sh --apply soviet         # ~/.local only, no sudo; undo: ./uninstall.sh
sudo ./install-system.sh soviet     # Plymouth + GRUB, with a backup; undo: --revert
```

Independent of `nt-legacy/`, `CDE/` and `tools/`: the generators here are
copies of their own (project rule in `../CLAUDE.md`).

## Pipeline

The LLM writes **no** SVG, QML or scripts. It makes design decisions in a
small, checkable specification; deterministic generators do everything
technical; tools paint and render; checks look at the result, and what fails
goes back to the LLM as a concrete repair order. `./forge.py all` runs it
from top to bottom:

```
request ─► 1 lead colour vote        7 short questions, majority per variant     (LLM, ~4 s)
        ─► 2 design brief            colours, material, shapes, motifs           (LLM, thinking mode, ~10 s)
        ─► 3 specification           JSON, bound to the schema by grammar        (LLM, ~4 s)
        ─► 4 check + repair          errors with a path and a concrete value;
                                     only the broken part is made again          (LLM, <1 s each)
        ─► 5 art plan                scenes per variant, icon style sheet        (LLM)
        ─► 6 build, stage by stage:
             colors       colour scheme, Konsole colours                         (generator)
             plasma-style panels, popups; painted metal texture                  (generator + ComfyUI)
             decoration   Aurorae window frame                                   (generator)
             wallpapers   three per variant                                      (ComfyUI)
             icons        120 pictures, each looked at by the LLM; failures
                          rewritten and painted again, up to 2 rounds           (ComfyUI + LLM)
             splash-boot  look-and-feel, splash, Plymouth, GRUB; the emblem      (generator + Blender/Inkscape)
        ─► 7 package check + preview linter, element ids, contrasts, 9-patch rendering
        ─► 8 visual review (--review) the LLM looks at decoration, wallpapers and
                                     the desktop in a lab VM; repairs, builds and
                                     looks again, up to 2 rounds                (LLM with vision)
```

In order, who does what:

| Step | Decides | Checks | Iterates | Tools |
|---|---|---|---|---|
| 1 lead colours | LLM (7 votes) | majority, hue clusters | — | — |
| 2 brief | LLM (thinking) | — | — | — |
| 3–4 specification | LLM | `spec.py`: schema, contrasts, mode, brands, trap words | partial repair, 4 rounds, then a deterministic last stage | — |
| 5 art plan | LLM | trap words, protected names, German, duplicates | per field/per icon, 4 rounds | — |
| 6 build | generators | — | — | ComfyUI (Z-Image locally, Krea-2 on ai395), Blender (metal emblem), Inkscape (flat emblem), QtSvg |
| 6 icons | catalogue + style sheet | faces (OpenCV), duplicates (hash), the LLM describes each picture blind and compares | rewrite + repaint, 2 rounds; the whole style sheet anew from 40 % failures | ComfyUI, LLM with vision |
| 7 package check | — | linter, element ids, scripts, contrasts | — | `tools/lint-plasma-svg.py` |
| 8 visual review | — | LLM with vision, measured title contrast | colours/frame by partial repair, wallpaper by a new prompt, 2 rounds | LLM with vision, lab VM |

POV-Ray is not a tool of the forge yet. A fitting extension (proposal): the
LLM chooses a raytraced scene as JSON — objects (spheres, polyhedra, a
statue), materials (chrome, glass, gold, marble), floor (chessboard, grid),
time of day — and a fixed generator writes the `.pov`, as Warp Legacy's
`os2-warp/tools/raytracing-entwuerfe.py` does by hand; the visual review then
judges the render like any other wallpaper.

### Visual review (`forge/review.py`)

`./forge.py review out/<x> [--review-vm fedora|ubuntu|artix] [--rounds 2]`,
or `all … --review`. The vision model (`FORGE_VISION`, by default the same
server: Qwen3.6 with its mmproj; any OpenAI-compatible endpoint with vision
can be named) gets each picture with the style model, the variant's look
and lead colour, and answers in a fixed JSON schema: ok, a score, and up to
six issues, each with severity, target and a concrete fix.

* **Decoration**: the active and the inactive title bar, rendered as KWin
  draws them (`preview.window`), twice enlarged so the 13 px title is
  readable. The engine measures the title text's contrast on the rendered
  bar and gives the numbers to the model; claims of illegible text against
  a measured 4.5:1 or more are downgraded (the model called a 7:1 inactive
  title "nearly invisible").
* **Wallpapers**: severity by rule, not by the model's taste. Only lettering
  (also watermarks), a deformed main subject, a colour world contradicting
  the variant, and a busy icon zone are major; style and composition are
  minor. The icon zone (the left column where Plasma puts desktop icons) is
  measured: below an edge density of 0.13 a claim of a busy zone is
  overruled. The measurement never raises a fault itself — a good picture
  with a fine chessboard reaches 0.144, confetti 0.16. Calibrated with
  `tests/review_bench.py` (below).
* **Desktop**: the vmtest screenshot after `install.sh --apply`: legibility
  of icons and labels, the panel, rendering faults (garbled glyphs, Breeze
  left over).

Major issues are repaired where the engine can: title colours and text
contrast through the specification's partial repair (rejected if the
specification's own checks then fail), the frame likewise, a wallpaper by a
rewritten prompt (only with ComfyUI; trap words the LLM keeps are replaced
deterministically as a last stage). Then the package is built again — the
icons from the cache, without checking and repainting them anew — and looked
at anew. What has no repair path (icons, installer faults) stays in
`review.json` under `left`.

Calibration (`tests/review_bench.py -n 3`, 26.10.2026): shipped wallpapers
that are plainly good must get no major issue; bad ones made with PIL must
be caught as the right kind. Before the rules nearly every picture got "no
calm area" or "style mismatch"; after them:

| case | pictures | runs | as expected |
|---|---|---|---|
| good | kalkstein, marmor, schiefer-dark, fenland (RISC Legacy), raytracing-chrome, raytracing-singularity (Warp Legacy) | 18 | 18 (no major issue) |
| bad: busy | confetti over the whole picture (edge density 0.16) | 3 | 3 (icon_zone) |
| bad: lettering | large words on a calm gradient | 3 | 3 (lettering) |
| bad: watermark | a good picture under a faint "© STOCKPHOTO" | 3 | 3 (lettering) |
| bad: colours | candy pastels for a dark red variant | 3 | 3 (colours) |

Two fixes it took: the issue schema asks for the target first (in the other
order the model wrote the kind into "what" and chose a wrong target), and an
issue that names lettering, a watermark or a logo counts as lettering.

### Live run for a recording (`forge/live.py`, `forge/events.py`)

`./forge.py all "<style>" -o out/<x> --live-vm fedora --review` (also
`build out/<x> --live-vm …`): the VM is reverted to `clean`, switched to an
English session, a Dolphin window opened, and after every build stage the
package so far is copied in and just that part applied — colours, Plasma
style, frame, wallpaper, icons, then the whole global theme and its splash.
A screenshot per stage goes to `live-<n>-<stage>.png`.

Every step also goes into `<out>/events.jsonl` (`--events` for another
file): one JSON line with time, seconds since the start, stage and data —
lead colours, the brief, the specification's decisions, the art plan,
every ComfyUI prompt, each painted icon, check results, repairs, review
verdicts, durations. `tail -f events.jsonl` or a small overlay script can
show it beside the recording. While ComfyUI paints the icons,
`assets/progress.png` is rewritten after each icon with the latest 32 (an
image viewer that reloads on change shows the painting live); ComfyUI's own
web page (`http://127.0.0.1:8189`) shows the queue and each step's preview
as well, if a browser window beside the VM is wanted.

| File | Purpose |
|---|---|
| `forge.py` | command line: `design`, `build`, `all`, `bench`, `bench-art`, `vmtest`, `review` |
| `forge/llm.py` | OpenAI-compatible client (llama.cpp, Ollama, vLLM), `response_format: json_schema` |
| `forge/designer.py` | lead colour vote, brief, specification, targeted repair |
| `forge/spec.py` | schema and semantic check (contrasts, mode, lead colour, brands, image prompt traps) |
| `forge/palette.py` | 9 base colours → full palette (bevel, hover, signal colours, legibility) |
| `forge/plasmasvg.py` | Plasma style SVGs (a copy of `tools/gen-plasma-svg.py` + bevels, rounding, glow line) |
| `forge/aurorae.py` | window decoration (corner shapes, four button shapes) |
| `forge/build.py` | the build stage by stage: colour scheme, Konsole, Plasma style, frame, wallpapers, icons, look-and-feel + splash |
| `forge/boot.py` | Plymouth (3 layouts, password prompt) and GRUB (2 layouts, own font) |
| `forge/emblem.py` | emblem from a geometry: Inkscape (flat) or Blender (metal, Cycles) |
| `forge/artplan.py` | art plan: scenes per variant, icon style sheet (or `--themed-icons`) |
| `forge/iconset.py` | icon catalogue: 120 pictures for 519 names, each a function + neutral picture + family |
| `forge/icons.py` | painting, image check, repair loop, metal frame, icon theme |
| `forge/imgcheck.py` | visual check (LLM with vision), faces, duplicates |
| `forge/gpu.py` | switches the graphics card between llama-server and ComfyUI |
| `forge/material.py` | metal texture for decoration and panel |
| `forge/comfy.py` | ComfyUI: local (Z-Image Turbo, default) or ai395 (Krea-2 Turbo) |
| `forge/frames.py` | 9-patch rendering with QtSvg, as KSvg does, for GRUB pictures and the preview |
| `forge/check.py` | package check |
| `forge/installers.py` | `install.sh`, `uninstall.sh`, `install-system.sh` |
| `forge/vmtest.py` | install/apply/uninstall in the lab VMs, in an English session |
| `forge/review.py` | visual review of decoration, wallpapers and the VM desktop, with repairs |
| `forge/live.py` | live run: each build stage played into a lab VM, a screenshot each |
| `forge/events.py` | the event log (JSONL) for overlays in a recording |
| `tests/ra2.expect.json` | style expectation for the reliability test |
| `tests/build_many.py` | build and check many specifications (without ComfyUI) |
| `tests/review_bench.py` | calibration of the wallpaper review on good and deliberately bad pictures |

### What the LLM decides

Name, description · corner shape (square/bevel/round) and size · bevel ·
outline · glow edge · title bar, frame, button shape, button layout · font
(from 13 OFL fonts) · emblem shape and tool (Blender/Inkscape) · boot
layouts · per variant: lead colour, 9 base colours, light/dark, image
prompt.

### Why it is reliable

Measured on the RTX 5080 (Qwen3.6-35B-A3B, IQ3, llama.cpp), request
"Red Alert 2 … Soviets and Allies", style check = the Soviets' title bar red
on a dark ground, the Allies' blue:

| Stage | valid | true to style |
|---|---|---|
| first version (whole specification anew on errors) | 7/10 | 4/10 |
| + targeted partial repair, false alarms fixed | 11/12 | 10/12 |
| + lead colour, the title bar carries it | 20/20 | 18/20 |
| confirmation with 30 runs | 27/30 | 23/30 |
| + lead colour vote, solvable suggestions | 29/30 | 29/30 |
| **final** (`out/bench-final`) | **30/30** | **30/30** |

On average 18.7 s per specification, at most 26 s. Other models (Tron,
Mac OS 9, Pip-Boy, Bauhaus, Art Nouveau): 20/20 valid. 83 different
specifications all build without errors (`tests/build_many.py`). A complete
run with two ComfyUI wallpapers takes just under 4 minutes, 3½ of them
image generation.

What brought the reliability, in order of effect:

1. **Partial repair instead of rewriting.** When the model has to repeat
   900 tokens to replace one word, it carries the error along. Given only
   the broken part with a schema of its own, it works.
2. **Concrete values in error messages.** "Choose a darker text" is often
   ignored, "set colors.text to #161616" almost never.
3. **Pin down its own statement.** Have it write `look` (one sentence) and
   `lead` (the lead colour) first, then check that the title bar carries it.
4. **Majority vote against wavering knowledge.** Asked once, the model
   called the Soviets red, black or olive; 7 short questions settle it
   reliably.
5. **A deterministic last stage** only for technical matters without design
   value (required buttons, forbidden words in the image prompt), visible as
   "auto" in the log, 1 of 30 in the final stage.

### Traps the check catches

* Image models paint every word: "room for desktop icons" gave painted
  icons, "warning signs" made-up lettering. Such words are barred from the
  image prompt.
* Brands: a fixed list plus the title of the request itself (`Red Alert 2`,
  `Pip-Boy`); `--avoid` adds more.
* Plasma writes panel text in the normal text colour → `text` must also be
  legible on `panel`.

## Tested in the VM (plasma-lab, Fedora 44, Plasma 6.7.4)

Install → apply (Soviets) → log in again → change variant (Allies) →
`install-system.sh` → reboot with GRUB, Plymouth, splash → `--revert` +
`uninstall.sh` → reboot: the desktop exactly as before. Found and fixed:

* A global theme does not set the button order, title font and Konsole
  profile; `install.sh --apply` writes them explicitly (with a backup).
* Fedora lacks `plymouth-plugin-script`; the installer stopped halfway.
  Now a check first: nothing changes while something is missing.
* Under Secure Boot GRUB loads no font files (also described in
  `CDE/TESTING.md`); detected, then the built-in Unifont.
* Variable fonts (Oxanium, Cinzel …) give the thinnest instance unless told
  otherwise; for GRUB, Plymouth and lettering a fixed instance (600) is made.
* GRUB's selection bar reached into the next entry (the corners lie outside).
* The note "splash missing" was wrong on Fedora (it uses `rhgb` there).
* Over SSH `kreadconfig6` does not show a global theme's values (they are in
  `~/.config/kdedefaults/`); not a fault of the theme.

## VM test (three environments)

`./forge.py vmtest out/<x> [--vm fedora,ubuntu,artix] [--variant <id>] [--lang en|de|keep] [--no-reset]`
reverts each lab VM to its snapshot `clean`, switches the Plasma session to
English (the default; `--lang keep` leaves the VM's own language) and logs
in again by restarting the VM, copies the package, runs `install.sh
--apply`, takes a screenshot, runs `uninstall.sh` and compares the watched
settings before and after (`forge/vmtest.py`, result in `vmtest.json`,
screenshots `vm-<environment>-*.png`):

| Name | VM | What it covers |
|---|---|---|
| fedora | plasma-lab (`vm/lab.env`) | Fedora 44, systemd, Plasma 6.7 |
| ubuntu | ubuntu-lab (`vm/ubuntu.env`) | Ubuntu 26.04 LTS, an older Plasma |
| artix | artix-lab (`vm/artix.env`) | Artix/OpenRC, **no systemd**, Plasma 6.8 |

### An English session for good

`~/.config/plasma-localerc` alone does not switch Plasma's language
(plasma-lab, 26.10.2026): startplasma gets `LANG` from SDDM, SDDM from PID 1,
and PID 1 reads `/etc/locale.conf` only at boot; the systemd user manager
also keeps its environment (`LANG=de_DE…`) as long as SSH sessions keep it
alive, and hands it on to the next Plasma session. `vmtest` therefore sets,
in this order:

1. the system locale: `sudo localectl set-locale LANG=en_US.UTF-8` (on OpenRC
   `/etc/locale.conf`);
2. `plasma-localerc`: `[Formats] LANG=en_US.UTF-8`, `[Translations] LANGUAGE=en_US`;
3. `systemctl --user set-environment LANG=en_US.UTF-8 LANGUAGE=en_US` (systemd only);
4. a reboot of the VM (restarting SDDM is not enough),

and then checks the language plasmashell really runs with
(`tr '\0' '\n' < /proc/$(pgrep -x plasmashell)/environ | grep LANG`); a
session that did not switch is reported as an error. The keyboard layout
stays as it is. The first available of en_US.UTF-8, en_GB.UTF-8, C.UTF-8 is
taken (on Ubuntu `locale-gen en_US.UTF-8` first, which needs no network).

The home folders are switched as well, because the VMs were built German
(Bilder, Schreibtisch, Vorlagen, Öffentlich …): `~/.config/user-dirs.dirs` is
written in English by hand (Artix has no `xdg-user-dirs-update`), contents
move into the English folders, empty German ones go, and Dolphin's places
(`user-places.xbel`, which holds the old paths) are made anew by KDE. This
runs before the restart and once more after it: the German plasmashell still
running recreated "Schreibtisch" the moment it was gone.

If a VM has a snapshot `clean-en` (clean with language and folders switched),
`vmtest` and the live run revert to it and skip the switch and its restart;
otherwise they revert to `clean` and switch (about a minute per VM).

## System layer

`install-system.sh` checks first (Plymouth script plugin, GRUB tools), only
then changes anything, backs up `/etc/default/grub` and the previous
Plymouth theme to `/var/lib/theme-forge/<id>/` and takes everything back
with `--revert`. `GRUB_TERMINAL_OUTPUT=console` (Fedora's default) is
commented out, otherwise the menu stays in text mode. Fedora needs
`plymouth-plugin-script`.

## Limits

* The style check measures fidelity of colour, not taste. Choice of
  pictures, proportions and "does it feel like the model" remain a human
  check; the preview is there for that.
* Mouse cursors and small status/action icons come from Breeze; the engine
  paints the catalogue's 519 names itself.
* The login screen (Plasma Login Manager) has no QML themes; only the lock
  screen gets the wallpaper.
* Without ComfyUI there are procedural wallpapers (`--no-comfy`).
* GRUB's terminal window ("Booting …") has a frame in the theme's style,
  inside it stays black; a theme cannot set that colour.
* The style check is so far only defined for "Red Alert 2"; for other models
  only validity is measured.
* Generated pictures are decoration, not a reproduction of the model; the
  model's names and logos are deliberately left out.

## Icons: catalogue + style sheet

What an icon shows is fixed in the catalogue (`forge/iconset.py`): a
function and a neutral, figurative picture without lettering. Folders share
a container, file types a sheet; only the sign on it changes. Per theme the
LLM writes only a **style sheet** (way of painting, colours, material,
details, light, background, folder, sheet). Checked: it names no objects
(else every icon shows a tank), no frames or tiles (the engine sets the
frame per variant) and no hex codes.

After painting, the LLM describes each picture without knowing what it is
meant to show, then compares: lettering, unwanted people, empty pictures,
wrong motif. Single failures it rewrites; from 40 % failures on it writes
the style sheet anew. For that the llama-server needs `--mmproj` (Qwen3.6:
`mmproj-F16.gguf`, with `--no-mmproj-offload` on the CPU; on the GPU it
pushed model layers out, 176 → 50 tok/s). Without vision the engine checks
only faces (OpenCV) and duplicates.

## Sharing the graphics card

The LLM (~14 GB) and Z-Image do not fit into 16 GB at the same time.
`forge/gpu.py` stops the LLM service (`FORGE_LLM_SERVICE`, default
`llama-qwen36.service`) for image runs, starts a local ComfyUI
(`/data/ComfyUI`, port 8189) and restores the starting state at the end,
also when a run is aborted.

## Environment

`FORGE_LLM` (default `http://127.0.0.1:8090/v1`, the llama-server on 245k),
`FORGE_COMFY` (default local `http://127.0.0.1:8189`; ai395 with
`http://192.168.178.54:8188`, login from `~/.config/comfyui/claude-zugang`),
`FORGE_IMAGE_MODEL` (`zimage`/`krea2`), `FORGE_VISION` (the model that looks at
pictures; default `FORGE_LLM`), `FORGE_LLM_SERVICE`, `FORGE_COMFY_DIR`.
Python ≥ 3.11 with Pillow and PySide6; `inkscape`, `blender`, `grub2-mkfont`.
