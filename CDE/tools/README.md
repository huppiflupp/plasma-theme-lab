# CDE Copper's own generator copies

These three scripts are CDE Copper's private copies of the lab's SVG
generators, taken from plasma-theme-lab commit 9930435 (the last state that
reproduces `../build/` byte for byte):

- `gen-plasma-svg.py` — Plasma style widget SVGs
- `gen-aurorae.py` — Aurorae window decoration
- `lint-plasma-svg.py` — structural check for the generated Plasma SVGs

`gen-motif-aurorae.py` is CDE Copper's own: the Motif frame as an SVG Aurorae
theme for the KDE Store edition (`../store.py`).

They are deliberately **not** shared with NT Legacy or any other theme in the
repository. Changes to the lab-wide `../../tools/` do not reach CDE Copper,
and changes made here do not reach the other themes. If a fix from the
lab-wide tools is wanted here, copy it over on purpose, rebuild, and check the
resulting diff in `../build/`. `tests/verify.py` fails when a build needs
anything outside the `CDE/` directory.
