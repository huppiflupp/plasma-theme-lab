"""GTK 3 and GTK 4 theme for CDE Copper, generated from a palette.

GTK programs (Firefox, PCManFM, GIMP...) do not use Qt's Kvantum style. This
theme imports GTK's own built-in theme (Adwaita for GTK 3, Default for
GTK 4) for everything it does not mention and gives the visible controls
Motif's look on top: a one-pixel ink outline, light top and left, dark
bottom and right, square corners, the palette's colours, the selection in
the active-title colour. The same palette keys as the Kvantum theme (see
kvantum.py and palettes.theme). Libadwaita programs ignore themes; they
only take colours from ~/.config/gtk-4.0/gtk.css, which Plasma maintains.
"""
from pathlib import Path


def bevel(P, sunken=False):
    light, dark = (P["dunkel"], P["hell"]) if sunken else (P["hell"], P["dunkel"])
    return f"inset 1px 1px {light}, inset -1px -1px {dark}"


def css(P, gtk4=False):
    ink, face, field = P["rahmen"], P["flaeche"], P["fenster"]
    text, field_text = P["text"], P["fenster_text"]
    accent, accent_text = P["auswahl"], P["auswahl_text"]
    hover, pressed, groove = P["knopf_hover"], P["knopf_gedrueckt"], P["rille"]
    disabled = P["inaktiv_text"]
    title, title_text = P["kopf_aktiv"], P["kopf_aktiv_text"]
    raised, sunken = bevel(P), bevel(P, sunken=True)
    base = ('@import url("resource:///org/gtk/libgtk/theme/Default/Default-light.css");' if gtk4
            else '@import url("resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained.css");')
    menu_item = "popover.menu modelbutton:hover, popover.menu row:hover" if gtk4 else "menuitem:hover, menu menuitem:hover, .menu menuitem:hover, popover modelbutton:hover"
    menu_box = "popover.menu > contents, popover > contents" if gtk4 else "menu, .menu, .context-menu, popover.background"
    check = "checkbutton check, check" if gtk4 else "check"
    radio = "checkbutton radio, radio" if gtk4 else "radio"
    return f"""/* CDE Copper: Motif controls in the palette's colours (generated). */
{base}

@define-color theme_bg_color {face};
@define-color theme_fg_color {text};
@define-color theme_base_color {field};
@define-color theme_text_color {field_text};
@define-color theme_selected_bg_color {accent};
@define-color theme_selected_fg_color {accent_text};
@define-color insensitive_fg_color {disabled};
@define-color borders {ink};

window, .background, dialog, messagedialog .dialog-action-area {{
  background-color: {face};
  color: {text};
}}
*:disabled, label:disabled {{ color: {disabled}; }}

/* Title bars drawn by GTK itself (client-side decorations). */
headerbar, .titlebar, window.csd > .titlebar {{
  background-image: none;
  background-color: {face};
  color: {text};
  border-radius: 0;
  border-bottom: 1px solid {ink};
  box-shadow: {raised};
  min-height: 30px;
}}
headerbar .title {{ font-weight: 600; }}
window.csd, window.csd decoration, decoration {{ border-radius: 0; }}

/* Push buttons. */
button {{
  background-image: none;
  background-color: {face};
  color: {text};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {raised};
  text-shadow: none;
  -gtk-icon-shadow: none;
  padding: 4px 10px;
  min-height: 22px;
}}
button:hover {{ background-color: {hover}; }}
button:active, button:checked {{ background-color: {pressed}; box-shadow: {sunken}; }}
button:disabled {{ color: {disabled}; box-shadow: none; }}
button.flat, button.image-button.flat, headerbar button.flat {{
  border-color: transparent;
  background-color: transparent;
  box-shadow: none;
}}
button.flat:hover {{ border-color: {ink}; background-color: {hover}; box-shadow: {raised}; }}
button.suggested-action, button.default {{
  border: 1px solid {ink};
  box-shadow: 0 0 0 2px {P["dunkel"]}, {raised};
}}
button.destructive-action {{ background-color: {P["fehler"]}; color: #ffffff; }}

/* Text fields, spin boxes, combo entries: sunken. */
entry, spinbutton, spinbutton:not(.vertical), textview, .view text {{
  background-image: none;
  background-color: {field};
  color: {field_text};
  border-radius: 0;
}}
entry, spinbutton {{
  border: 1px solid {ink};
  box-shadow: {sunken};
  min-height: 24px;
}}
entry:focus, spinbutton:focus-within, entry:focus-within {{
  border-color: {accent};
  {"outline: none;" if gtk4 else ""}
}}
spinbutton button {{ border-radius: 0; }}

/* Lists, trees, icon views. */
.view, treeview, iconview, list, listview, columnview, gridview, textview text, row {{
  background-color: {field};
  color: {field_text};
}}
treeview header button, columnview > header > button {{ border-radius: 0; box-shadow: {raised}; }}
selection, *:selected, row:selected, treeview:selected, .view:selected, iconview:selected,
listview > row:selected, gridview > child:selected, entry selection, textview selection {{
  background-color: {accent};
  color: {accent_text};
}}

/* Menus: raised, the item under the pointer in the selection colour. */
menubar {{ background-color: {face}; box-shadow: {raised}; border-bottom: 1px solid {ink}; }}
menubar > menuitem:hover, menubar > item:hover {{ background-color: {accent}; color: {accent_text}; box-shadow: none; }}
{menu_box} {{
  background-color: {face};
  color: {text};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {raised};
  padding: 2px;
}}
{menu_item} {{ background-color: {accent}; color: {accent_text}; border-radius: 0; }}
menu separator, popover separator {{ background-color: {P["dunkel"]}; min-height: 1px; }}

/* Tabs. */
notebook > header {{ background-color: {groove}; border-color: {ink}; }}
notebook > header tab {{
  background-color: {face};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {raised};
  margin: 2px 1px 0 1px;
  padding: 4px 10px;
}}
notebook > header tab:checked {{ background-color: {face}; box-shadow: inset 0 2px {accent}, {raised}; }}
notebook > header tab:hover {{ background-color: {hover}; }}
notebook > stack:not(:only-child) {{ background-color: {face}; }}

/* Scroll bars: a sunken groove, raised slider. */
scrollbar {{ background-color: {groove}; border: none; }}
scrollbar slider {{
  background-color: {face};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {raised};
  min-width: 10px;
  min-height: 10px;
}}
scrollbar slider:hover {{ background-color: {hover}; }}

/* Check boxes and radio buttons. */
{check}, {radio} {{
  background-image: none;
  background-color: {field};
  border: 1px solid {ink};
  box-shadow: {sunken};
  color: {accent};
  min-width: 14px;
  min-height: 14px;
}}
{check} {{ border-radius: 0; }}
{check}:checked, {radio}:checked {{ background-color: {accent}; color: {accent_text}; }}

/* Progress bars and sliders. */
progressbar trough, scale trough, levelbar trough {{
  background-image: none;
  background-color: {P["karo"]};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {sunken};
  min-height: 10px;
}}
progressbar progress, scale highlight, levelbar block.filled {{
  background-image: none;
  background-color: {title};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {bevel({**P, "hell": "rgba(255, 255, 255, 0.3)", "dunkel": "rgba(0, 0, 0, 0.3)"})};
}}
scale slider {{
  background-image: none;
  background-color: {face};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: {raised};
  min-width: 12px;
  min-height: 18px;
}}

/* Switches drawn as Motif toggles. */
switch {{ background-color: {groove}; border: 1px solid {ink}; border-radius: 0; box-shadow: {sunken}; }}
switch:checked {{ background-color: {accent}; }}
switch slider {{ background-color: {face}; border: 1px solid {ink}; border-radius: 0; box-shadow: {raised}; }}

/* Frames, separators, tooltips. */
frame > border, .frame {{ border: 1px solid {P["dunkel"]}; border-radius: 0; box-shadow: inset 1px 1px {P["hell"]}; }}
separator {{ background-color: {P["dunkel"]}; }}
tooltip, tooltip.background {{
  background-color: {field};
  color: {field_text};
  border: 1px solid {ink};
  border-radius: 0;
  box-shadow: none;
}}
tooltip * {{ color: {field_text}; }}

/* States. GTK's built-in theme has more specific rules for disabled,
   pressed and unfocused (backdrop) controls; these repeat ours for them. */
button:backdrop, button:backdrop:hover {{ background-image: none; background-color: {face}; color: {text}; border-color: {ink}; box-shadow: {raised}; }}
button:checked:backdrop, button:active:backdrop {{ background-image: none; background-color: {pressed}; box-shadow: {sunken}; }}
button:disabled, button:disabled:backdrop, button:checked:disabled, button.flat:disabled {{
  background-image: none;
  background-color: {face};
  color: {disabled};
  border-color: {P["dunkel"]};
  box-shadow: none;
}}
button.flat:backdrop, headerbar button.flat:backdrop {{ background-color: transparent; border-color: transparent; box-shadow: none; }}
entry:backdrop, spinbutton:backdrop {{ background-image: none; background-color: {field}; color: {field_text}; border-color: {ink}; box-shadow: {sunken}; }}
entry:disabled, entry:disabled:backdrop, spinbutton:disabled, spinbutton:disabled:backdrop {{
  background-image: none;
  background-color: {face};
  color: {disabled};
  border-color: {P["dunkel"]};
  box-shadow: none;
}}
{check}:backdrop, {radio}:backdrop, {check}:hover, {radio}:hover {{ background-image: none; background-color: {field}; border-color: {ink}; box-shadow: {sunken}; }}
{check}:checked, {check}:indeterminate, {radio}:checked, {radio}:indeterminate,
{check}:checked:backdrop, {check}:indeterminate:backdrop, {radio}:checked:backdrop, {radio}:indeterminate:backdrop,
{check}:checked:hover, {radio}:checked:hover {{
  background-image: none;
  background-color: {accent};
  color: {accent_text};
  border-color: {ink};
}}
{check}:disabled, {radio}:disabled, {check}:checked:disabled, {radio}:checked:disabled, {check}:indeterminate:disabled, {radio}:indeterminate:disabled {{
  background-image: none;
  background-color: {face};
  color: {disabled};
  border-color: {P["dunkel"]};
  box-shadow: none;
}}
scale slider:backdrop, scale slider:hover {{ background-image: none; background-color: {face}; border-color: {ink}; box-shadow: {raised}; }}
scale slider:disabled, scale trough:disabled, progressbar trough:disabled {{ background-image: none; background-color: {face}; border-color: {P["dunkel"]}; box-shadow: none; }}
scale highlight:disabled {{ background-image: none; background-color: {P["kopf_inaktiv"]}; }}
headerbar:backdrop, .titlebar:backdrop {{ background-image: none; background-color: {face}; color: {disabled}; }}
notebook > header tab:backdrop {{ background-color: {face}; }}
notebook > header > tabs > tab:checked, notebook > header.top > tabs > tab:checked, notebook > header.bottom > tabs > tab:checked,
notebook > header.left > tabs > tab:checked, notebook > header.right > tabs > tab:checked {{
  box-shadow: inset 0 2px {accent}, {raised};
}}
notebook > header.top > tabs > tab:hover, notebook > header.bottom > tabs > tab:hover,
notebook > header.left > tabs > tab:hover, notebook > header.right > tabs > tab:hover {{ box-shadow: {raised}; }}
spinbutton:not(.vertical):disabled, spinbutton.vertical:disabled {{ background-image: none; background-color: {face}; color: {disabled}; }}
switch, switch:backdrop {{ background-image: none; background-color: {groove}; border-color: {ink}; }}
switch:checked, switch:checked:backdrop {{ background-image: none; background-color: {accent}; }}
switch slider, switch slider:backdrop, switch:checked slider {{ background-image: none; background-color: {face}; border-color: {ink}; }}
/* GTK 4's own theme names these by their full path. */
progressbar > trough > progress, scale > trough > highlight, levelbar > trough > block.filled {{
  background-image: none;
  background-color: {title};
  border: 1px solid {ink};
  border-radius: 0;
}}
progressbar > trough, scale > trough, levelbar > trough {{ background-image: none; background-color: {P["karo"]}; border-radius: 0; }}
scale > trough > slider {{ background-image: none; background-color: {face}; border: 1px solid {ink}; border-radius: 0; box-shadow: {raised}; }}
checkbutton > check, checkbutton > radio {{ background-image: none; background-color: {field}; border: 1px solid {ink}; box-shadow: {sunken}; }}
checkbutton > check:checked, checkbutton > check:indeterminate, checkbutton > radio:checked, checkbutton > radio:indeterminate {{
  background-image: none; background-color: {accent}; color: {accent_text};
}}
checkbutton > check:disabled, checkbutton > radio:disabled {{ background-color: {face}; color: {disabled}; box-shadow: none; }}
"""


def build_gtk(out: Path, P, name="CDECopper"):
    theme = out / "themes" / name
    for version, gtk4 in (("gtk-3.0", False), ("gtk-4.0", True)):
        (theme / version).mkdir(parents=True, exist_ok=True)
        (theme / version / "gtk.css").write_text(css(P, gtk4))
        # Asked for when Plasma reports a dark scheme; without it GTK falls
        # back to its own dark theme. The palette decides, not the variant.
        (theme / version / "gtk-dark.css").write_text(css(P, gtk4))
    (theme / "index.theme").write_text(f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={name}\nComment=Motif controls in the CDE palette\n\n"
                                       f"[X-GNOME-Metatheme]\nGtkTheme={name}\n")
