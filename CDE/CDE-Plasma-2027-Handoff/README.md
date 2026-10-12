# CDE Plasma 2027 — design and prototyping package

This package describes a modern KDE Plasma interface whose origins in CDE and Motif remain instantly recognisable. It is intended as a handover to a coding LLM or a theme developer.

## Target picture

The binding visual reference is `references/05-target-teal-copper-panel.png`:

- petrol/teal as the desktop and panel base
- copper orange for active title bars, selection and important states
- hard, multi-step Motif bevels instead of smooth Breeze/plastic surfaces
- distinct, drawn workstation icons instead of stock Freedesktop icons
- floating, two-row CDE front panel with small subpanel triggers
- modern usability: HiDPI, clear typography, usable spacing, Plasma 6/Wayland

## Contents

| File/folder | Purpose |
|---|---|
| `references/` | All five design screenshots in chronological order |
| `DESIGN-SPEC.md` | Binding design rules, dimensions, states and exclusions |
| `KDE-PLASMA-MAPPING.md` | Mapping of the design to Plasma components |
| `IMPLEMENTATION-GUIDE.md` | Implementation order, test and acceptance criteria |
| `LLM-PROMPT.md` | Ready-to-use brief for a coding LLM |
| `design-tokens.json` | Machine-readable colours, geometry and effects |
| `MANIFEST.md` | Meaning and priority of the reference images |

## Recommended use

1. Unpack the ZIP completely.
2. Give the LLM the complete folder.
3. Use `LLM-PROMPT.md` as the first brief.
4. Implement only phase 1 at first (colour scheme, window decoration, panel prototype) and compare screenshots against `05-target-teal-copper-panel.png`.
5. Only then expand icons, subpanels and the install script.

## Technical target frame

- KDE Plasma 6
- Qt 6
- Wayland as the primary target, X11 without deliberate dependency
- preferably SVG/QML/KDecoration3; no raster scaling for frames or icons
- reproducible installation and complete uninstallation in the user profile

The screenshots are concept images. Individual texts, app names and placements are not pixel-exact implementation requirements; the rules in `DESIGN-SPEC.md` take precedence.
