# RISC Legacy icon kit

Every icon Breeze has (2 577 meanings, `names.py`), drawn anew in RISC OS's
manner as SVG, in two colour worlds: `ro4` (RISC OS 4: pale green folders,
grey, black outline, flat colour) and `ro5` (RISC OS 5: blue folders,
saturated colours, soft gradients). The user's rules (25.10.2026): **every
icon, correctly scaled, no picture twice.**

## Files

| file | what |
|---|---|
| `names.py` | the meanings per category and Breeze's synonyms (symlinks) |
| `kit.py` | `Canvas`: 48 × 48 grid, primitives, gradients, the two worlds |
| `glyphs.py` | ~380 symbols on a 24 grid: `glyph(c, name, x, y, size, color)` |
| `base.py` | bodies: `folder`, `page`, `case`, `tile`, `disc`, `plaque`, `action`, `overlay` |
| `places.py` | places (done, the model for the rest) |
| `fam_*.py` | one family module per category or part of one |
| `build_icons.py` | builds both themes, reports coverage and duplicates, renders sheets |

## A family module

```python
"""fam_status.py: status icons."""
from base import action, disc, overlay, page, tile
from glyphs import glyph, reg, S, F, O, D    # reg(): add glyphs of your own

def draw(name, c):          # c: kit.Canvas
    if name == "battery-100":
        ...                  # draw with c.path/rect/circle/text, glyph(), base helpers
        return True          # drawn
    return None              # not mine
```

`draw` must return a true value only for names it drew, and must never
raise. Use `c.small` to leave out detail at 16/22 px (the same function
draws the large and the small version). Colours come from the world:
`c["ink"]`, `c["blue"]`, `c["red"]`, `c["green"]`, `c["yellow"]`,
`c["orange"]`, `c["cyan"]`, `c["violet"]`, `c["brown"]`, `c["grey"]`,
`c["folder"]` (pair), `c["page"]`, `c["case"]`, `c["metal"]`, `c["screen"]`;
`c.grad(top, bottom)` for a top-lit gradient (flattened in ro4),
`c.lighten(col, t)`, `c.darken(col, t)`. Never hard-code a colour that
differs between the worlds; a fixed white or black is fine.

New glyphs go into your own module with `@reg("my-name")` (prefix the name
with your family, e.g. `status-battery-cell`, so modules never collide).
Do not edit `glyphs.py`, `base.py`, `kit.py` or another agent's module.

## Style (RISC OS)

- **Folders** blue/green with an emblem (`folder(c, "glyph")`); **files**
  a page with the corner folded at the top right; the type as a coloured
  band with the type's name (`page(c, "PDF", c["red"])`) or an emblem on
  the page. RISC OS names file types in capitals: JPEG, PDF, TEXT, BASIC.
- **Applications** are objects on their own, not on a tile (RISC OS's
  !Edit is a pen and a page, !Paint a palette and brush, !Configure cogs).
- **Actions** (toolbar icons): `action(c, glyph, accent, badge)` — the
  glyph large in the outline colour, a badge (plus, minus, cross, check …)
  in a round plaque at the lower right. Related actions share the glyph and
  differ by badge or arrow; one accent colour per family.
- **Status** small and clear: levels as filled segments (battery, signal,
  volume), states as a plaque (`overlay`).
- Outline in `c["ink"]`; one light source from the top; no text smaller
  than 7 on the 48 grid; at 16/22 px drop text and fine detail.
- No logos or trademarks of others (Firefox, Android, Docker …): draw what
  the thing is or does; a short word on the body is the last resort.
- QtSvg only: paths, rect, circle, ellipse, linear gradients, text. No
  filters, masks, patterns, clip paths.

## No duplicates

Two meanings must not give the same picture. Different meanings that
look alike (e.g. `go-up` and `go-top`) must differ visibly (a bar, a
second arrow, another badge). `build_icons.py` prints `DUPLICATE: a = b`
for identical drawings; fix every one in your category.

## Checks

```bash
cd riscos/iconkit
python3 build_icons.py /tmp/x --only status          # coverage + duplicates
QT_QPA_PLATFORM=offscreen python3 build_icons.py --sheet /tmp/s.png ro5 status battery 0 100
```

The sheet shows each icon at 22 px (small), 48 and 96 px. Look at it
(both worlds) before calling a part done: the meaning must be readable at
22 px.
