# CDE backdrops

`cde/*.pm` (XPM) and `cde/*.bm` (XBM) are the desktop backdrops of the
Common Desktop Environment, copied unchanged from the CDE source tree:

- Project: <https://sourceforge.net/projects/cdesktopenv/>
- Path: `cde/programs/backdrops/`
- Commit: `c5727a7798af9a3424f090428120132e73315a60` (2026-09-26)
- Licence: as media files of CDE, Creative Commons Attribution-ShareAlike 3.0
  (<https://creativecommons.org/licenses/by-sa/3.0/>), attribution
  "The Open Group" (see `cde/COPYING` in that tree)

`NoBackdrop` is left out. `Background` and `Foreground` are kept as copied
but not offered; they are plain fills.

`backdrops.py` colours the pixmaps with the workspace colour set of the
applied palette, as dtwm does, and writes PNG files. Those PNG files are
derived works under the same licence (CC BY-SA 3.0, "The Open Group").
