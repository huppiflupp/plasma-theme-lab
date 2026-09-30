"""Kvantum widget style for CDE Copper, generated from the palette.

Kvantum draws every widget part from an SVG object whose id encodes
element, state and nine-patch position (see reference: Kvantum's
Theme-Making.pdf). Each object is drawn here at exactly the pixel size that
the .kvconfig frame widths request, so no scaling blurs the Motif bevels.

Motif rules used throughout: raised = light top/left, dark bottom/right;
sunken = the reverse; a 1 px ink outline around controls; copper marks the
focused control, the default button and the selection.
"""
from pathlib import Path

CELL = 8           # interior sample size of every nine-patch
GAP = 6            # spacing between objects on the sheet
STATES = ("normal", "focused", "pressed", "toggled")
SIDES = ("top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright")


class Sheet:
    """Lays SVG objects out on a grid and emits the document."""

    def __init__(self):
        self.objects = []
        self.x = GAP
        self.y = GAP
        self.row_height = 0

    def place(self, w, h):
        if self.x + w + GAP > 1600:
            self.x = GAP
            self.y += self.row_height + GAP
            self.row_height = 0
        x, y = self.x, self.y
        self.x += w + GAP
        self.row_height = max(self.row_height, h)
        return x, y

    def add(self, name, w, h, rects):
        """rects: iterable of (u, v, w, h, color) in local coordinates; color None = transparent."""
        x, y = self.place(w, h)
        body = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>']
        for u, v, rw, rh, color in rects:
            if color is None:
                continue
            body.append(f'<rect x="{x+u}" y="{y+v}" width="{rw}" height="{rh}" fill="{color}"/>')
        self.objects.append(f'<g id="{name}">' + "".join(body) + "</g>")

    def add_path(self, name, w, h, paths):
        x, y = self.place(w, h)
        body = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>']
        for d, color, extra in paths:
            body.append(f'<path transform="translate({x},{y})" d="{d}" fill="{color}" {extra}/>')
        self.objects.append(f'<g id="{name}">' + "".join(body) + "</g>")

    def svg(self):
        height = self.y + self.row_height + GAP
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="%d" viewBox="0 0 1600 %d" '
                'shape-rendering="crispEdges">' % (height, height) + "".join(self.objects) + "</svg>")


def runs(pixels, w, h):
    """Merge same-coloured horizontal pixel runs into rects."""
    for v in range(h):
        u = 0
        while u < w:
            color = pixels(u, v)
            end = u + 1
            while end < w and pixels(end, v) == color:
                end += 1
            yield (u, v, end - u, 1, color)
            u = end


def box_pixels(rings, interior, w, h):
    """Colour function of a w×h box: rings from outside in, each (topleft, bottomright).

    Within each 1 px ring the top row and left column carry the top-left
    colour, except for the corner pixels shared with the bottom/right sides:
    those go to the bottom-right colour, which gives the Motif diagonal."""
    n = len(rings)

    def color(u, v):
        d = min(u, v, w - 1 - u, h - 1 - v)
        if d >= n:
            return interior
        tl, br = rings[d]
        a, b, ring_w, ring_h = u - d, v - d, w - 2 * d, h - 2 * d
        if (b == 0 and a < ring_w - 1) or (a == 0 and b < ring_h - 1):
            return tl
        return br
    return color


def nine_patch(sheet, name, rings, interior, frame=None):
    """Emit interior plus eight frame parts for one element-state."""
    n = frame if frame is not None else len(rings)
    size = 2 * n + CELL
    color = box_pixels(rings, interior, size, size)
    parts = {"topleft": (0, 0, n, n), "top": (n, 0, CELL, n), "topright": (n + CELL, 0, n, n),
             "left": (0, n, n, CELL), "right": (n + CELL, n, n, CELL),
             "bottomleft": (0, n + CELL, n, n), "bottom": (n, n + CELL, CELL, n),
             "bottomright": (n + CELL, n + CELL, n, n)}
    if interior is not None:
        sheet.add(name, CELL, CELL, [(0, 0, CELL, CELL, interior)])
    if n == 0:
        return
    for side, (ox, oy, w, h) in parts.items():
        sheet.add(f"{name}-{side}", w, h, runs(lambda u, v: color(ox + u, oy + v), w, h))


def build_kvantum(out, P):
    ink, light, dark = P["rahmen"], P["hell"], P["dunkel"]
    face, base, copper = P["flaeche"], P["fenster"], P["kopf_aktiv"]
    hover_face, pressed_face, groove = "#95b1b6", "#78969c", "#6f8f96"
    disabled = "#6f8588"
    raised = [(ink, ink), (light, dark), (light, dark)]
    sunken = [(ink, ink), (dark, light), (dark, light)]
    etched = [(dark, light), (light, dark)]
    s = Sheet()

    # Push/tool buttons, combo boxes, headers, scrollbar sliders.
    nine_patch(s, "button-normal", raised, face)
    nine_patch(s, "button-focused", raised, hover_face)
    nine_patch(s, "button-pressed", sunken, pressed_face)
    nine_patch(s, "button-toggled", sunken, pressed_face)
    nine_patch(s, "button-default", [(copper, copper), (light, dark), (light, dark)], None)
    s.add("button-default-indicator", 9, 9, [])
    for st, rings, fill in (("normal", raised, face), ("focused", raised, hover_face), ("pressed", sunken, pressed_face)):
        nine_patch(s, f"scrollbarslider-{st}", rings, fill)
    for st in ("normal", "focused", "pressed"):
        s.add(f"grip-{st}", 8, 8, [])
    # Text fields and spin boxes.
    nine_patch(s, "lineedit-normal", sunken, base)
    nine_patch(s, "lineedit-focused", [(ink, ink), (dark, light), (copper, copper)], base)
    # Generic and group frames: double etched line, no interior.
    nine_patch(s, "common-normal", etched, None)
    nine_patch(s, "group-normal", etched, None)
    # Tabs: the active tab shares the page colour and attaches to the frame.
    nine_patch(s, "tabframe-normal", raised, None)
    nine_patch(s, "tab-normal", raised, groove)
    nine_patch(s, "tab-focused", raised, pressed_face)
    nine_patch(s, "tab-toggled", raised, face)
    # Item views: hover is a light wash, selection is copper.
    nine_patch(s, "itemview-normal", [(None, None), (None, None)], None)
    nine_patch(s, "itemview-focused", [(hover_face, hover_face), (hover_face, hover_face)], hover_face)
    nine_patch(s, "itemview-pressed", [(copper, copper), (copper, copper)], copper)
    nine_patch(s, "itemview-toggled", [(copper, copper), (copper, copper)], copper)
    # Menus and menu bars.
    nine_patch(s, "menu-normal", raised, face)
    s.add("menuitem-pressed", CELL, CELL, [(0, 0, CELL, CELL, copper)])
    s.add("menuitem-toggled", CELL, CELL, [(0, 0, CELL, CELL, copper)])
    s.add("menuitem-separator", 16, 8, [(0, 3, 16, 1, dark), (0, 4, 16, 1, light)])
    for st in ("normal", "focused"):
        s.add(f"menuitem-tearoff-{st}", 20, 8, [(u, 3, 4, 1, dark) for u in (0, 8, 16)] + [(u, 4, 4, 1, light) for u in (0, 8, 16)])
    for st in ("focused", "pressed", "toggled"):
        nine_patch(s, f"menubaritem-{st}", [(light, dark), (light, dark)], face)
    # Toolbars.
    s.add("toolbar-normal", CELL, CELL, [(0, 0, CELL, CELL, face)])
    s.add("toolbar-handle", 8, 24, [(2, 2, 1, 20, light), (3, 2, 1, 20, dark), (5, 2, 1, 20, light), (6, 2, 1, 20, dark)])
    s.add("toolbar-separator", 4, 24, [(1, 2, 1, 20, dark), (2, 2, 1, 20, light)])
    s.add("header-separator", 2, 16, [(0, 0, 1, 16, dark), (1, 0, 1, 16, light)])
    # Grooves: scrollbars, sliders, progress bars.
    nine_patch(s, "slider-normal", [(dark, light), (dark, light)], groove)
    nine_patch(s, "slider-toggled", [(dark, light), (dark, light)], P["panel"])
    s.add("slider-tick-normal", 5, 1, [(0, 0, 5, 1, dark)])
    nine_patch(s, "progress-normal", [(dark, light), (dark, light)], P["karo"])
    s.add("progress-pattern-normal", CELL, CELL, [(0, 0, CELL, CELL, copper)])
    s.add("progress-pattern-disabled", CELL, CELL, [(0, 0, CELL, CELL, P["kopf_inaktiv"])])
    for st, rings, fill in (("normal", raised, face), ("focused", raised, hover_face),
                            ("pressed", sunken, pressed_face), ("disabled", raised, face)):
        color = box_pixels(rings, fill, 16, 16)
        s.add(f"slidercursor-{st}", 16, 16, list(runs(color, 16, 16)) + [(4, 7, 8, 1, dark), (4, 8, 8, 1, light)])
    # Splitters, size grip, docks, MDI title bars.
    for st, fill in (("normal", face), ("focused", hover_face), ("pressed", pressed_face)):
        s.add(f"splitter-{st}", CELL, CELL, [(0, 0, CELL, CELL, fill)])
        s.add(f"splitter-grip-{st}", 6, 16, [(2, v, 2, 2, dark) for v in (2, 7, 12)] + [(3, v + 1, 1, 1, light) for v in (2, 7, 12)])
    for st in ("normal", "focused"):
        s.add(f"sizegrip-{st}", 13, 13, [(12 - i, i, 1, 1, dark) for i in range(13)] + [(12 - i, i + 4, 1, 1, dark) for i in range(9)] + [(12 - i, i + 8, 1, 1, dark) for i in range(5)])
    s.add("dock-normal", CELL, CELL, [(0, 0, CELL, CELL, face)])
    s.add("dock-focused", CELL, CELL, [(0, 0, CELL, CELL, hover_face)])
    s.add("titlebar-normal", CELL, CELL, [(0, 0, CELL, CELL, P["kopf_inaktiv"])])
    s.add("titlebar-focused", CELL, CELL, [(0, 0, CELL, CELL, copper)])
    glyphs = {"close": [(2, 2, 8, 8)], "minimize": [(3, 6, 6, 3)], "maximize": [(1, 1, 10, 10)],
              "restore": [(1, 4, 7, 7), (4, 1, 7, 7)], "shade": [(1, 2, 10, 2)], "menu": [(1, 4, 10, 4)]}
    for glyph, rects in glyphs.items():
        for st in ("normal", "focused", "pressed", "disabled"):
            if glyph == "menu" and st != "normal":
                continue
            color = disabled if st == "disabled" else ink
            body = []
            for (u, v, w, h) in rects:
                body += [(u, v, w, 1, color), (u, v + h - 1, w, 1, color), (u, v, 1, h, color), (u + w - 1, v, 1, h, color)]
            if glyph == "close":
                body = [(2 + i, 2 + i, 1, 1, color) for i in range(8)] + [(9 - i, 2 + i, 1, 1, color) for i in range(8)] + \
                       [(3 + i, 2 + i, 1, 1, color) for i in range(7)] + [(8 - i, 2 + i, 1, 1, color) for i in range(7)]
            s.add(f"mdi-{glyph}-{st}", 12, 12, body)
    # Tool tips and the keyboard focus frame.
    nine_patch(s, "tooltip-normal", [(ink, ink), (base, base), (dark, dark)], base)
    nine_patch(s, "focus", [(copper, copper), (ink, ink)], None)
    # Arrows for scrollbars, combo boxes, spin boxes, tool buttons, sub-menus.
    arrow = {"up": "M4.5 1 L8 6 H1 Z", "down": "M4.5 8 L1 3 H8 Z", "left": "M1 4.5 L6 1 V8 Z", "right": "M8 4.5 L3 1 V8 Z"}
    for direction, d in arrow.items():
        for st in ("normal", "focused", "pressed", "disabled"):
            s.add_path(f"arrow-{direction}-{st}", 9, 9, [(d, disabled if st == "disabled" else ink, "")])
    for sign in ("plus", "minus"):
        for st in ("normal", "focused", "pressed", "disabled"):
            color = disabled if st == "disabled" else ink
            body = [(0, 0, 9, 1, color), (0, 8, 9, 1, color), (0, 0, 1, 9, color), (8, 0, 1, 9, color), (1, 1, 7, 7, base), (2, 4, 5, 1, color)]
            if sign == "plus":
                body.append((4, 2, 1, 5, color))
            s.add(f"arrow-{sign}-{st}", 9, 9, body)
    # Tab close and tear indicators.
    for st in ("normal", "focused", "pressed", "disabled"):
        color = disabled if st == "disabled" else (copper if st == "focused" else ink)
        s.add(f"tab-close-{st}", 9, 9, [(1 + i, 1 + i, 1, 1, color) for i in range(7)] + [(7 - i, 1 + i, 1, 1, color) for i in range(7)])
    s.add("tab-tear", 2, 16, [(0, 0, 1, 16, dark), (1, 0, 1, 16, light)])
    # Check boxes (sunken square) and Motif diamond radio buttons.
    check = "M3 8 L6 11 L13 4 L13 6 L6 13 L3 10 Z"
    tri = [(4, 7, 8, 2, ink)]
    for st in ("normal", "focused"):
        rings = [(dark, light), (copper, copper) if st == "focused" else (dark, light)]
        body = list(runs(box_pixels(rings, base, 16, 16), 16, 16))
        s.add(f"checkbox-{st}", 16, 16, body)
        s.add_path(f"checkbox-checked-{st}", 16, 16, [(f"M{x} {y} h{w} v{h} h-{w} Z", c, "") for (x, y, w, h, c) in body if c] + [(check, ink, "")])
        s.add(f"checkbox-tristate-{st}", 16, 16, body + tri)
        diamond_ring = copper if st == "focused" else None
        s.add_path(f"radio-{st}", 16, 16, radio(light, dark, face, diamond_ring))
        s.add_path(f"radio-checked-{st}", 16, 16, radio(dark, light, pressed_face, diamond_ring) + [("M8 5 L11 8 L8 11 L5 8 Z", copper, "")])

    kv = out / "Kvantum/CDECopper"
    kv.mkdir(parents=True, exist_ok=True)
    (kv / "CDECopper.svg").write_text(s.svg())
    (kv / "CDECopper.kvconfig").write_text(kvconfig(P, disabled))


def radio(tl, br, fill, ring):
    """A 16 px Motif diamond: two-pixel bevel, optional copper focus ring."""
    paths = [("M8 0 L16 8 L8 16 L0 8 Z", br, ""), ("M8 0 L16 8 L14 8 L8 2 L2 8 L0 8 Z", tl, ""),
             ("M8 2 L14 8 L8 14 L2 8 Z", fill, "")]
    if ring:
        paths.append(("M8 2 L14 8 L8 14 L2 8 Z M8 3 L13 8 L8 13 L3 8 Z", ring, 'fill-rule="evenodd"'))
    return paths


def kvconfig(P, disabled):
    ink, face, base, copper = P["rahmen"], P["flaeche"], P["fenster"], P["kopf_aktiv"]
    text = f"text.normal.color={ink}\ntext.focus.color={ink}\ntext.press.color={ink}\ntext.toggle.color={ink}\ntext.shadow=false\n"
    return f"""[%General]
author=CDE Copper contributors
comment=Motif workstation controls in teal and copper
respect_DE=true
x11drag=false
alt_mnemonic=true
left_tabs=true
attach_active_tab=true
joined_inactive_tabs=false
mirror_doc_tabs=false
group_toolbar_buttons=false
toolbar_interior_spacing=1
toolbar_separator_thickness=4
spread_progressbar=true
progressbar_thickness=16
composite=false
menu_shadow_depth=0
tooltip_shadow_depth=0
translucent_windows=false
blurring=false
popup_blurring=false
animate_states=false
splitter_width=6
scroll_width=16
scroll_min_extent=36
scroll_arrows=true
scrollbar_in_view=false
transient_scrollbar=false
slider_width=8
slider_handle_width=16
slider_handle_length=16
check_size=16
menu_separator_height=6
submenu_overlap=0
combo_as_lineedit=false
square_combo_button=true
combo_menu=false
inline_spin_indicators=false
vertical_spin_indicators=false
spin_button_width=16
small_icon_size=16
large_icon_size=32
button_icon_size=16
toolbar_icon_size=22
no_window_pattern=true
remove_extra_frames=false
tree_branch_line=true
groupbox_top_label=false
click_behavior=0

[GeneralColors]
window.color={face}
base.color={base}
alt.base.color=#b9cac9
button.color={face}
light.color={P['hell']}
mid.light.color={P['karo']}
dark.color={ink}
mid.color={P['dunkel']}
highlight.color={copper}
inactive.highlight.color={P['hover']}
tooltip.base.color={base}
text.color={ink}
window.text.color={ink}
button.text.color={ink}
disabled.text.color={disabled}
tooltip.text.color={ink}
highlight.text.color={ink}
link.color={P['desktop']}
link.visited.color={P['dunkel']}

[Hacks]
respect_darkness=false
transparent_dolphin_view=false
transparent_ktitle_label=true
transparent_menutitle=true
force_size_grip=true
iconless_menu=false
iconless_pushbutton=false
normal_default_pushbutton=true
tint_on_mouseover=0
no_selection_tint=true

[PanelButtonCommand]
frame=true
frame.element=button
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
interior=true
interior.element=button
indicator.element=arrow
indicator.size=9
{text}text.margin.top=3
text.margin.bottom=3
text.margin.left=8
text.margin.right=8
text.iconspacing=4
min_width=+0.3font
min_height=+0.3font

[PanelButtonTool]
inherits=PanelButtonCommand
text.margin.top=3
text.margin.bottom=3
text.margin.left=4
text.margin.right=4

[Dock]
inherits=PanelButtonCommand
frame=false
interior=false

[DockTitle]
inherits=PanelButtonCommand
frame=false
interior=true
interior.element=dock
text.bold=true
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4

[IndicatorSpinBox]
inherits=PanelButtonCommand
frame.element=lineedit
interior.element=lineedit
indicator.element=arrow
indicator.size=9

[RadioButton]
inherits=PanelButtonCommand
frame=false
interior.element=radio
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4

[CheckBox]
inherits=PanelButtonCommand
frame=false
interior.element=checkbox
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4

[Focus]
inherits=PanelButtonCommand
interior=false
frame=true
frame.element=focus
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2

[GenericFrame]
inherits=PanelButtonCommand
frame=true
interior=false
frame.element=common
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2

[LineEdit]
inherits=PanelButtonCommand
frame.element=lineedit
interior.element=lineedit
text.margin.top=3
text.margin.bottom=3
text.margin.left=4
text.margin.right=4

[DropDownButton]
inherits=PanelButtonCommand
indicator.element=arrow-down

[IndicatorArrow]
indicator.element=arrow
indicator.size=9

[ToolboxTab]
inherits=PanelButtonCommand

[Tab]
inherits=PanelButtonCommand
frame.element=tab
interior.element=tab
indicator.element=tab
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
text.margin.top=3
text.margin.bottom=3
text.margin.left=8
text.margin.right=8

[TabFrame]
inherits=PanelButtonCommand
frame.element=tabframe
interior=false
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3

[TabBarFrame]
inherits=GenericFrame
frame=false
interior=false

[TreeExpander]
inherits=PanelButtonCommand
frame=false
interior=false
indicator.element=arrow
indicator.size=9

[HeaderSection]
inherits=PanelButtonCommand
text.margin.top=3
text.margin.bottom=3
text.margin.left=6
text.margin.right=6

[SizeGrip]
indicator.element=sizegrip

[Toolbar]
inherits=PanelButtonCommand
frame=false
interior=true
interior.element=toolbar
indicator.element=toolbar
indicator.size=8

[Slider]
inherits=PanelButtonCommand
frame.element=slider
interior.element=slider
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2

[SliderCursor]
inherits=PanelButtonCommand
frame=false
interior.element=slidercursor

[Progressbar]
inherits=PanelButtonCommand
frame.element=progress
interior.element=progress
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
text.bold=false

[ProgressbarContents]
inherits=PanelButtonCommand
frame=false
interior.element=progress-pattern

[ItemView]
inherits=PanelButtonCommand
frame.element=itemview
interior.element=itemview
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
text.margin=0
text.margin.top=2
text.margin.bottom=2
text.margin.left=3
text.margin.right=3

[Splitter]
inherits=PanelButtonCommand
frame=false
interior.element=splitter
indicator.element=splitter-grip
indicator.size=16

[Scrollbar]
inherits=PanelButtonCommand
indicator.element=arrow
indicator.size=9

[ScrollbarSlider]
inherits=PanelButtonCommand
frame.element=scrollbarslider
interior.element=scrollbarslider
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
indicator.element=grip
indicator.size=8

[ScrollbarGroove]
inherits=PanelButtonCommand
frame.element=slider
interior.element=slider
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2

[MenuItem]
inherits=PanelButtonCommand
frame=false
interior.element=menuitem
indicator.element=menuitem
min_height=+0.2font
text.margin.top=2
text.margin.bottom=2
text.margin.left=5
text.margin.right=5

[MenuBarItem]
inherits=PanelButtonCommand
frame.element=menubaritem
interior.element=menubaritem
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
text.margin.top=3
text.margin.bottom=3
text.margin.left=6
text.margin.right=6

[MenuBar]
inherits=PanelButtonCommand
frame=false
interior=false

[TitleBar]
inherits=PanelButtonCommand
frame=false
interior.element=titlebar
indicator.element=mdi
indicator.size=12
text.bold=true
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4

[ComboBox]
inherits=PanelButtonCommand
text.margin.left=6
text.margin.right=6

[Menu]
inherits=PanelButtonCommand
frame.element=menu
interior.element=menu
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3

[GroupBox]
inherits=GenericFrame
frame=true
frame.element=group
interior=false
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
text.bold=true

[ToolTip]
inherits=GenericFrame
frame=true
frame.element=tooltip
interior=true
interior.element=tooltip
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
text.margin=0

[Window]
interior=false
frame=false
"""
