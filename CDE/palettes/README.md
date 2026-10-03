# CDE palettes

`cde/*.dp` are the 41 colour palettes of the Common Desktop Environment,
copied unchanged from the CDE source tree:

- Project: <https://sourceforge.net/projects/cdesktopenv/>
- Path: `cde/programs/palettes/`
- Commit: `c5727a7798af9a3424f090428120132e73315a60` (2026-09-26)
- Licence: GNU LGPL 2.0 or later (see `cde/COPYING` in that tree)

Each file holds eight background colours. `palettes.py` derives the
foreground, select and shadow colours with the algorithm of Motif's
`lib/Xm/Color.c` (LGPL-2.1-or-later) and maps the eight sets to the theme's
surfaces. The files themselves are not modified. `Black`, `White`,
`BlackWhite` and `WhiteBlack` belong to CDE's monochrome mode and hold
colour names instead of eight sets; the theme does not offer them.
