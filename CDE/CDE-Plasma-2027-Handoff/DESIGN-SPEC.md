# Design specification

## 1. Guiding idea

"CDE on a high-end UNIX workstation from 2026/27": a robust, technical, calm interface with clear mechanical depth. Modernity comes from precision, HiDPI, legibility and well-considered animation – not from rounded corners, transparency or glass.

## 2. Mandatory palette

| Token | Hex | Use | Example |
|---|---:|---|---|
| Desktop Deep Teal | `#086875` | desktop background, large calm areas | wallpaper base tone |
| Panel Teal | `#2E7180` | panel and menu frames | front panel |
| Surface Blue Gray | `#86A4AA` | window surfaces, fields | file manager |
| Surface Light | `#AFC2C2` | light widget surface | dialogs |
| Copper Active | `#E8874F` | active title bar, active workspace | focus state |
| Copper Light | `#F0B184` | highlight edge and icon details | top/left bevel edge |
| Teal Shadow | `#174C55` | deep shadow edge | bottom/right bevel edge |
| Ink | `#10262B` | standard text and outlines | menu text |
| Terminal | `#061C22` | terminal/dark special surface | console |
| Cyan Signal | `#3DB5C3` | rare status information | network/activity |
| Disabled | `#6F8588` | disabled text | inactive action |

Copper is a focus and action signal, not a blanket secondary colour. At most roughly 10–15 % of any view should be copper.

## 3. Shape language

- Corners: 0–2 px radius as a rule; windows and large panels 0 px.
- Frames: dark outside, then light, medium inside; 2–3 clearly separated steps.
- Raised elements: light edge top/left, shadow edge bottom/right.
- Pressed elements: reverse the bevel direction; shift content 1 px right/down.
- Focus: copper border plus a high-contrast inner line; never just a colour change.
- Shadows: short and firm (e.g. 0 5 px 12 px at low opacity), no diffuse Material Design shadow.
- Transparency/blur: do not use in the core theme. Optionally at most 3–5 % visual see-through in the floating panel.
- Separators: visible, usually 1 px, never replaced by spacing alone.

## 4. Typography

- UI: one narrow, highly legible sans; preferably `IBM Plex Sans Condensed`, fallback `Noto Sans`.
- Terminal/technical labels: `IBM Plex Mono`, fallback `Noto Sans Mono`.
- Standard size: 10–11 pt at 96 dpi; no artificially tiny retro type.
- Title bars: semibold, not heavy black; normal letter spacing.
- No bitmap font as the default. A bitmap look may only appear in small decorative labels.

## 5. Window decoration

| Element | Requirement |
|---|---|
| active title bar | copper `#E8874F`, 28–32 px, fine texture optional |
| inactive title bar | desaturated blue-green/grey, clearly distinguishable from active |
| outer frame | 4 px visually, three hard bevel steps |
| window buttons | square 22–24 px, drawn glyphs, their own bevel |
| order | menu/window on the left; minimise, maximise, close on the right |
| resize zone | invisible, at least 6–8 px, despite the narrow visible frame |

Active focus must be recognisable without colour perception, through contrast and frame structure.

## 6. Controls

- Buttons: rectangular, 28–34 px high, 2 px bevel; default button with an additional copper border.
- Input fields: sunken frame, light inner surface; focus as a copper inner edge.
- Menus: compact, 30–34 px row height, clear submenu triangles, no pills.
- Selection: copper surface with dark text or dark teal with light text – depending on contrast.
- Tabs: tabs that look physically connected; the active tab opens into the content area.
- Scrollbars: 16–20 px, visible arrow buttons optional; no ultra-thin overlay scrollbar.
- Tooltips: light blue-green surface, dark double frame, short fade-in.

## 7. Icon system

- Own icons are mandatory; no visible mix with Breeze/Papirus/Tela.
- Style: technical workstation pictograms, 2–4 main colours, dark outline, hard highlights.
- Geometry: mostly angular, minimal diagonal edges; no circular app-icon look.
- Grid: masters as SVG; optically tuned for 16, 22, 24, 32, 48 and 64 px.
- Folders: teal-grey body with a copper tab/accent.
- Status icons: monochrome/two-colour, clear pixel silhouette, no thin Breeze lines.
- An active launcher gets a pressed-in frame and a copper marker, not merely a dot.

## 8. Front panel

The front panel is the distinguishing feature and must not look like an ordinary taskbar.

### Structure

- floating, 12–24 px from the screen edge; target position at the top first, a bottom variant possible later
- width about 88–94 % of the screen, centred
- two clearly separated rows, together approx. 96–116 px high
- top row: CDE/toolbox, workspaces, large launchers/active tasks, clock, central status modules
- bottom row: applications/places/system/help, context actions and system modules
- segments look like individual mechanical tiles within a shared frame
- small triangle triggers open subpanels above or below the associated segment

### Behaviour

- three modes: always visible, auto-hide, slide in/out via hotspot
- show/hide: 140–180 ms, linear or a subtle ease-out; no springy behaviour
- when hidden, a 3–5 px grip edge or a small copper indicator stays visible
- a subpanel stays open while pointer/focus is in the main segment or the subpanel; Escape closes it
- keyboard operation and screen-reader names for every launcher and every status module
- popup geometry must handle multi-monitor and screen-edge cases

## 9. Desktop and wallpaper

The theme must also work on plain petrol. A wallpaper is optional and must not dominate the interface. No built-in logo, no mandatory text and no UI elements in the wallpaper. With a picture, calm areas should sit behind windows/panel and copper should appear only sparingly as a landscape or light accent.

## 10. Animation

- functional animations only: panel, subpanel, workspace switch, focus change
- 120–200 ms; no long fades, bounce, jelly or zoom effects
- respect reduced motion; every function usable without animation

## 11. Explicit exclusions

- no Breeze/Oxygen/"KDE plastic" impression
- no large rounded corners, pills, glass surfaces or Material Design cards
- no arbitrary stock icons
- no lavender/pink target palette; it remains a development reference only
- no 1:1 museum copy with tiny fonts or poor HiDPI usability
- no modern panel that has merely been tinted teal
