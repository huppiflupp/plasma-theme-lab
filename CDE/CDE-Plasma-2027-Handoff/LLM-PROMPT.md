# Brief for the coding LLM

You are receiving a complete design handoff for a KDE Plasma 6 theme called **CDE Plasma 2027**. First read `README.md`, `MANIFEST.md`, `DESIGN-SPEC.md`, `KDE-PLASMA-MAPPING.md`, `IMPLEMENTATION-GUIDE.md` and `design-tokens.json`. Then analyse all images in `references/`.

## Goal

Build an installable, reversible prototype for KDE Plasma 6 that looks like a modern evolution of CDE/Motif. The binding image reference is `references/05-target-teal-copper-panel.png`. The other images document design stages and must not be mixed without scrutiny.

## Non-negotiable requirements

1. Petrol/teal and copper orange according to the design tokens.
2. Hard, multi-step Motif bevels; practically no rounded corners.
3. No recognisable Breeze, Oxygen, Material or "KDE plastic" aesthetic.
4. Distinct workstation icons; no stock icons in the visible core area.
5. Floating, two-row front panel with mechanical-looking segments and small subpanel triggers.
6. Panel modes: visible, auto-hide, hotspot/grip edge.
7. Plasma 6, Qt 6, HiDPI and Wayland; no root requirement.
8. Installing and uninstalling must not overwrite or delete anyone else's files.

## Approach

Work in verifiable phases. Start exclusively with phase 1 from `IMPLEMENTATION-GUIDE.md`. Before writing, present a short component and file structure. Then implement complete files, not isolated fragments. Run syntax/QML checks, start an isolated Plasma test where possible and document remaining limitations.

After phase 1, produce:

- an installable colour scheme
- a window decoration prototype
- a static two-row front panel
- twelve core icons
- `install.sh`, `uninstall.sh` and an own installation manifest
- a README with prerequisites and test steps
- screenshots at 1920×1080 and, if available, 2560×1440

## Decision duties

If Plasma APIs or distribution details are missing, stop at the smallest necessary point and ask specifically for the Plasma version and distribution. Do not invent any API. If two ordinary Plasma panels are used for the first prototype, mark this explicitly as a phase 1 approximation and plan the shared QML containment as the target architecture.

## Self-check before handover

Compare the prototype with the target reference and answer:

- Is CDE/Motif recognisable without explanation?
- Is the panel a distinct front panel or just a tinted taskbar?
- Are copper areas used sparingly and functionally?
- Are there visible stock icons or modern rounded corners?
- Are active, inactive, hover, focus and pressed states unambiguous?
- Do installation, uninstallation, keyboard operation and HiDPI work?

Fix any P0/P1 deviations found before handover.
