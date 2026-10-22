"""FreeCAD theme for CDE Copper, generated from a palette.

FreeCAD (1.x) draws its widgets with its own Qt style sheet and keeps the
colours of the 3D view, the sketcher and the tree in its parameters, so
neither the colour scheme nor Kvantum reach it (the Flatpak has no Kvantum
at all). This writes, into FreeCAD's per-user folders (native and Flatpak):

    Gui/Stylesheets/CDE Copper.qss          Motif controls in the palette
    Gui/Stylesheets/images_cde/*.svg        their arrows and check marks
    Gui/Stylesheets/parameters/CDE Copper.yaml   FreeCAD's style tokens
    SavedPreferencePacks/CDE Copper/        the theme FreeCAD lists under
                                            Preferences > General > Theme
    Mod/CDECopper/                          re-applies the pack's colours at
                                            start-up after a palette change

The pack sets the style sheet and the colours of the 3D view (backdrop in
the workspace colour, selection in the active-title colour), sketcher and
tree. FreeCAD copies a pack's values into user.cfg only when it is chosen;
the small module notices a newer pack (its stamp) while the CDE Copper
theme is chosen and copies the colours again, so FreeCAD follows the
palette from its next start. Nothing changes while the theme is not chosen.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

from palettes import legible, mix, readable

NAME = "CDE Copper"
QSS = f"{NAME}.qss"
ICONS = "images_cde"


def bevel(P, sunken=False):
    """Motif's two-pixel shadow: light top and left, dark bottom and right."""
    light, dark = (P["dark"], P["light"]) if sunken else (P["light"], P["dark"])
    return f"border: 2px solid; border-color: {light} {dark} {dark} {light}; border-radius: 0px;"


def colours(P):
    """The palette mapped onto FreeCAD's colour parameters (#rrggbb)."""
    desk = P["desktop"]
    top, bottom = mix(desk, "#ffffff", 0.12), mix(desk, "#000000", 0.15)
    # Sketch geometry and dimensions in FreeCAD's own hues, moved toward
    # black or white until they read on the workspace colour.
    ink = readable(desk)

    def on_desk(colour, target=3.0):
        return legible(colour, desk, ink, target)
    construction = on_desk("#4f8fdc")
    return dict(
        top=top, bottom=bottom, shape=P["surface"],
        selection=P["selection"], preselection=P["hover"],
        edge=on_desk(P["light"] if ink == "#ffffff" else P["border"], 4.5),
        construction=construction, external=on_desk("#cc3f8f"),
        constrained=on_desk("#33cc33"), internal=mix(construction, ink, 0.45),
        dimension=on_desk(P["hover"]), expression=on_desk("#ff9c38"),
        invalid=on_desk("#ff4a4a"), grid=mix(desk, ink, 0.25),
        text=ink,
    )


def rgba(colour, alpha=255):
    """FreeCAD's unsigned colour: 0xRRGGBBAA."""
    return str(int(colour[1:], 16) << 8 | alpha)


def pack_cfg(P):
    """The preference pack: FCParameters with only the keys the theme sets."""
    C = colours(P)
    view = {
        "Simple": False, "Gradient": True, "RadialGradient": False, "UseBackgroundColorMid": False,
        "BackgroundColor2": C["top"], "BackgroundColor3": C["bottom"], "BackgroundColor": C["bottom"],
        "DefaultShapeColor": C["shape"], "DefaultShapeLineColor": P["border"], "DefaultShapeVertexColor": P["border"],
        "SelectionColor": C["selection"], "HighlightColor": C["preselection"],
        "BoundingBoxColor": C["text"], "AnnotationTextColor": C["text"], "CbLabelColor": C["text"],
        "AxisLetterColor": C["text"], "CursorTextColor": C["text"], "CursorCrosshairColor": C["text"],
        "SketchEdgeColor": C["edge"], "SketchVertexColor": C["edge"], "CreateLineColor": C["edge"],
        "EditedEdgeColor": C["edge"], "EditedVertexColor": C["dimension"],
        "ConstructionColor": C["construction"], "ExternalColor": C["external"],
        "FullyConstrainedColor": C["constrained"], "FullyConstraintElementColor": C["constrained"],
        "FullyConstraintConstructionElementColor": C["internal"], "FullyConstraintConstructionPointColor": C["constrained"],
        "FullyConstraintInternalAlignmentColor": C["internal"], "InternalAlignedGeoColor": C["internal"],
        "ConstrainedDimColor": C["dimension"], "ConstrainedIcoColor": C["dimension"],
        "NonDrivingConstrDimColor": C["construction"], "DeactivatedConstrDimColor": mix(C["dimension"], C["bottom"], 0.5),
        "ExprBasedConstrDimColor": C["expression"], "InvalidSketchColor": C["invalid"],
    }
    groups = {
        "MainWindow": {"StyleSheet": QSS, "Theme": NAME, "QtStyle": "Fusion",
                       "OverlayActiveStyleSheet": "Freecad Overlay.qss"},
        "View": view,
        "NaviCube": {"Color": P["surface"]},
        "TreeView": {"TreeActiveColor": P["selection"], "TreeEditColor": P["hover"]},
        "Themes": {"ThemeAccentColor1": P["selection"], "ThemeAccentColor2": P["hover"], "ThemeAccentColor3": P["link"]},
        "OutputWindow": {"colorText": P["window_text"], "colorLogging": P["link"],
                         "colorWarning": P["warning"], "colorError": P["error"]},
        "Mod/Sketcher/General": {"GridLineColor": C["grid"], "GridDivLineColor": C["grid"]},
        "Mod/Draft": {"gridColor": C["grid"], "snapcolor": C["preselection"], "constructioncolor": C["construction"]},
    }
    root = ET.Element("FCParameters")
    prefs = ET.SubElement(ET.SubElement(ET.SubElement(root, "FCParamGroup", Name="Root"), "FCParamGroup", Name="BaseApp"),
                          "FCParamGroup", Name="Preferences")
    for path, values in groups.items():
        group = prefs
        for part in path.split("/"):
            group = next((g for g in group if g.get("Name") == part), None) or ET.SubElement(group, "FCParamGroup", Name=part)
        for key, value in values.items():
            if isinstance(value, bool):
                ET.SubElement(group, "FCBool", Name=key, Value=str(int(value)))
            elif path == "MainWindow":
                ET.SubElement(group, "FCText", Name=key).text = value
            else:
                ET.SubElement(group, "FCUInt", Name=key, Value=rgba(value))
    ET.indent(root, "  ")
    return '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n' + ET.tostring(root, encoding="unicode") + "\n"


PACKAGE = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<package format="1">
  <name>CDE Copper</name>
  <description>FreeCAD in the colours of the CDE Copper palette</description>
  <version>1.0.0</version>
  <maintainer>CDE Copper</maintainer>
  <license>GPL-3.0-or-later</license>
  <content>
    <preferencepack>
      <name>{NAME}</name>
      <type>Theme</type>
      <description>Motif controls and the CDE palette, following the palette chosen in the Style Manager.</description>
      <version>1.0.0</version>
      <tag>cde</tag>
    </preferencepack>
  </content>
</package>
"""


def icons(P):
    """Arrow and check-mark SVGs in the text colour, plus disabled ones."""
    arrows = {"up": "2,11 8,4 14,11", "down": "2,5 8,12 14,5", "left": "11,2 4,8 11,14", "right": "5,2 12,8 5,14"}
    out = {}
    for name, colour in (("", P["text"]), ("-disabled", P["inactive_text"]), ("-field", P["window_text"])):
        for direction, points in arrows.items():
            out[f"arrow-{direction}{name}.svg"] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                f'<polygon points="{points}" fill="{colour}"/></svg>\n')
    for name, colour in (("", P["selection_text"]), ("-disabled", P["inactive_text"])):
        out[f"check{name}.svg"] = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
            f'<path d="M3 8.5 6.5 12 13 4" fill="none" stroke="{colour}" stroke-width="2.4" stroke-linecap="square"/></svg>\n')
    # Motif's radio button is a diamond; checked, it is sunken and filled.
    out["radio.svg"] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                        f'<polygon points="8,1 15,8 8,15 1,8" fill="{P["window"]}"/>'
                        f'<polyline points="1,8 8,1 15,8" fill="none" stroke="{P["dark"]}" stroke-width="2"/>'
                        f'<polyline points="15,8 8,15 1,8" fill="none" stroke="{P["light"]}" stroke-width="2"/></svg>\n')
    out["radio-checked.svg"] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                                f'<polygon points="8,1 15,8 8,15 1,8" fill="{P["selection"]}"/>'
                                f'<polyline points="1,8 8,1 15,8" fill="none" stroke="{P["dark"]}" stroke-width="2"/>'
                                f'<polyline points="15,8 8,15 1,8" fill="none" stroke="{P["light"]}" stroke-width="2"/></svg>\n')
    return out


def qss(P):
    face, field, text, field_text = P["surface"], P["window"], P["text"], P["window_text"]
    accent, accent_text, hover, pressed = P["selection"], P["selection_text"], P["button_hover"], P["button_pressed"]
    ink, light, dark, groove, disabled = P["border"], P["light"], P["dark"], P["groove"], P["inactive_text"]
    menu, menu_text = P.get("menue", face), P.get("menue_text", text)
    raised, sunken = bevel(P), bevel(P, sunken=True)
    C = colours(P)
    img = f"qss:{ICONS}"
    return f"""/* CDE Copper for FreeCAD: Motif controls in the palette's colours (generated). */

QWidget {{ background-color: {face}; color: {text}; selection-background-color: {accent}; selection-color: {accent_text}; }}
QWidget:disabled {{ color: {disabled}; }}
QMainWindow::separator {{ background-color: {face}; width: 4px; height: 4px; }}
QMainWindow::separator:hover, QSplitter::handle:hover {{ background-color: {hover}; }}
QToolTip {{ background-color: {field}; color: {field_text}; border: 1px solid {ink}; padding: 2px; }}
QLabel, QCheckBox, QRadioButton {{ background-color: transparent; }}

/* Menus: a raised bar, items raised when chosen, as Motif draws them. */
QMenuBar {{ background-color: {menu}; color: {menu_text}; {raised} }}
QMenuBar::item {{ background-color: transparent; padding: 3px 8px; border: 2px solid transparent; }}
QMenuBar::item:selected, QMenuBar::item:pressed {{ {raised} background-color: {menu}; }}
QMenu {{ background-color: {menu}; color: {menu_text}; {raised} padding: 2px; }}
QMenu::item {{ padding: 3px 24px 3px 24px; border: 2px solid transparent; }}
QMenu::item:selected {{ background-color: {accent}; color: {accent_text}; }}
QMenu::item:disabled {{ color: {disabled}; background-color: transparent; }}
QMenu::separator {{ height: 2px; margin: 3px 4px; border-top: 1px solid {dark}; border-bottom: 1px solid {light}; }}
QMenu::indicator {{ width: 12px; height: 12px; left: 4px; }}
QMenu::indicator:non-exclusive:checked {{ image: url({img}/check-field.svg); }}
QMenu::right-arrow {{ image: url({img}/arrow-right.svg); width: 10px; height: 10px; }}

/* Toolbars and the status bar. */
QToolBar {{ background-color: {face}; {raised} spacing: 2px; padding: 1px; }}
QToolBar::separator {{ width: 2px; height: 2px; margin: 3px; background-color: {dark}; }}
QToolBar::handle {{ width: 6px; height: 6px; margin: 2px; border-left: 2px solid {light}; border-right: 2px solid {dark}; }}
QStatusBar {{ background-color: {face}; {raised} }}
QStatusBar::item {{ border: none; }}

/* Buttons: raised, sunken when pressed; copper marks focus and default. */
QPushButton {{ background-color: {face}; color: {text}; {raised} padding: 3px 12px; min-height: 18px; }}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:pressed, QPushButton:checked {{ background-color: {pressed}; {sunken} }}
QPushButton:default {{ border-color: {accent} {dark} {dark} {accent}; }}
QPushButton:focus {{ outline: none; border-color: {accent}; }}
QPushButton:disabled {{ color: {disabled}; background-color: {face}; }}
QPushButton::menu-indicator {{ image: url({img}/arrow-down.svg); subcontrol-position: right center; width: 10px; right: 4px; }}
QToolButton {{ background-color: transparent; border: 2px solid transparent; padding: 2px; }}
QToolButton:hover {{ background-color: {hover}; {raised} }}
QToolButton:pressed, QToolButton:checked {{ background-color: {pressed}; {sunken} }}
QToolButton:disabled {{ background-color: transparent; }}
QToolButton[popupMode="1"] {{ padding-right: 14px; }}
QToolButton::menu-button {{ border: none; width: 12px; }}
QToolButton::menu-arrow, QToolButton::menu-indicator {{ image: url({img}/arrow-down.svg); width: 8px; height: 8px; }}
QToolButton#qt_toolbar_ext_button {{ qproperty-icon: url({img}/arrow-right.svg); }}
Gui--SplitButton {{ background-color: transparent; }}

/* Fields: sunken, in the text-area colour. */
QLineEdit, QAbstractSpinBox, QTextEdit, QPlainTextEdit, QTextBrowser {{
  background-color: {field}; color: {field_text}; {sunken} padding: 1px 3px;
  selection-background-color: {accent}; selection-color: {accent_text};
}}
QLineEdit:focus, QAbstractSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {accent}; }}
QLineEdit:disabled, QAbstractSpinBox:disabled {{ background-color: {face}; color: {disabled}; }}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{ background-color: {face}; {raised} width: 14px; subcontrol-origin: border; }}
QAbstractSpinBox::up-button {{ subcontrol-position: top right; }}
QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; }}
QAbstractSpinBox::up-button:pressed, QAbstractSpinBox::down-button:pressed {{ {sunken} }}
QAbstractSpinBox::up-arrow {{ image: url({img}/arrow-up.svg); width: 8px; height: 8px; }}
QAbstractSpinBox::down-arrow {{ image: url({img}/arrow-down.svg); width: 8px; height: 8px; }}
QAbstractSpinBox::up-arrow:disabled {{ image: url({img}/arrow-up-disabled.svg); }}
QAbstractSpinBox::down-arrow:disabled {{ image: url({img}/arrow-down-disabled.svg); }}

/* Option menus (combo boxes): raised, with Motif's arrow button. */
QComboBox {{ background-color: {face}; color: {text}; {raised} padding: 2px 6px; min-height: 18px; }}
QComboBox:editable {{ background-color: {field}; color: {field_text}; {sunken} }}
QComboBox:focus {{ border-color: {accent}; }}
QComboBox:on {{ background-color: {pressed}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{ image: url({img}/arrow-down.svg); width: 10px; height: 10px; }}
QComboBox::down-arrow:disabled {{ image: url({img}/arrow-down-disabled.svg); }}
QComboBox QAbstractItemView {{ background-color: {menu}; color: {menu_text}; border: 1px solid {ink};
  selection-background-color: {accent}; selection-color: {accent_text}; }}

/* Check boxes square, radio buttons Motif's diamonds. */
QCheckBox::indicator, QGroupBox::indicator, QAbstractItemView::indicator {{ width: 13px; height: 13px; background-color: {field}; {sunken} }}
QCheckBox::indicator:checked, QGroupBox::indicator:checked, QAbstractItemView::indicator:checked {{ background-color: {accent}; image: url({img}/check.svg); }}
QCheckBox::indicator:indeterminate {{ background-color: {mix(field, accent, 0.5)}; }}
QCheckBox::indicator:disabled {{ background-color: {face}; }}
QCheckBox::indicator:checked:disabled {{ image: url({img}/check-disabled.svg); }}
QRadioButton::indicator {{ width: 16px; height: 16px; image: url({img}/radio.svg); }}
QRadioButton::indicator:checked {{ image: url({img}/radio-checked.svg); }}

QGroupBox {{ border: 2px groove {dark}; border-color: {dark} {light} {light} {dark}; margin-top: 12px; padding-top: 4px; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 3px; }}

/* Lists, trees and tables. */
QAbstractItemView {{ background-color: {field}; color: {field_text}; alternate-background-color: {P["alt_window"]};
  {sunken} selection-background-color: {accent}; selection-color: {accent_text}; outline: none; }}
QAbstractItemView::item:hover {{ background-color: {mix(field, accent, 0.25)}; color: {field_text}; }}
QAbstractItemView::item:selected {{ background-color: {accent}; color: {accent_text}; }}
/* FreeCAD greys hidden objects with the disabled text colour: readable on the field. */
QAbstractItemView:disabled {{ color: {legible(mix(field_text, field, 0.55), field, field_text, 2.5)}; }}
QTreeView::branch:has-children:closed {{ image: url({img}/arrow-right-field.svg); }}
QTreeView::branch:has-children:open {{ image: url({img}/arrow-down-field.svg); }}
QTreeView::branch:selected {{ background-color: {accent}; }}
QHeaderView {{ background-color: {face}; border: none; }}
QHeaderView::section {{ background-color: {face}; color: {text}; {raised} padding: 2px 4px; }}
QHeaderView::section:pressed {{ {sunken} }}
QHeaderView::down-arrow {{ image: url({img}/arrow-down.svg); width: 8px; height: 8px; }}
QHeaderView::up-arrow {{ image: url({img}/arrow-up.svg); width: 8px; height: 8px; }}
QTableView {{ gridline-color: {groove}; }}
QTableCornerButton::section {{ background-color: {face}; {raised} }}
Gui--PropertyEditor--PropertyEditor {{ qproperty-groupTextColor: {text}; qproperty-groupBackground: {face}; }}
Gui--PropertyEditor--PropertyEditor > QWidget > QWidget > QLabel {{ background-color: {field}; }}

/* Scroll bars: a sunken trough, raised slider and arrow buttons. */
QScrollBar {{ background-color: {groove}; {sunken} }}
QScrollBar:vertical {{ width: 16px; margin: 16px 0; }}
QScrollBar:horizontal {{ height: 16px; margin: 0 16px; }}
QScrollBar::handle {{ background-color: {face}; {raised} }}
QScrollBar::handle:hover {{ background-color: {hover}; }}
QScrollBar::handle:vertical {{ min-height: 20px; }}
QScrollBar::handle:horizontal {{ min-width: 20px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ background-color: {face}; {raised} subcontrol-origin: margin; }}
QScrollBar::add-line:pressed, QScrollBar::sub-line:pressed {{ {sunken} }}
QScrollBar::add-line:vertical {{ height: 12px; subcontrol-position: bottom; }}
QScrollBar::sub-line:vertical {{ height: 12px; subcontrol-position: top; }}
QScrollBar::add-line:horizontal {{ width: 12px; subcontrol-position: right; }}
QScrollBar::sub-line:horizontal {{ width: 12px; subcontrol-position: left; }}
QScrollBar::up-arrow {{ image: url({img}/arrow-up.svg); width: 8px; height: 8px; }}
QScrollBar::down-arrow {{ image: url({img}/arrow-down.svg); width: 8px; height: 8px; }}
QScrollBar::left-arrow {{ image: url({img}/arrow-left.svg); width: 8px; height: 8px; }}
QScrollBar::right-arrow {{ image: url({img}/arrow-right.svg); width: 8px; height: 8px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QAbstractScrollArea::corner {{ background-color: {face}; }}

QSlider::groove {{ background-color: {groove}; {sunken} }}
QSlider::groove:horizontal {{ height: 6px; }}
QSlider::groove:vertical {{ width: 6px; }}
QSlider::handle {{ background-color: {face}; {raised} }}
QSlider::handle:horizontal {{ width: 22px; margin: -6px 0; }}
QSlider::handle:vertical {{ height: 22px; margin: 0 -6px; }}
QProgressBar {{ background-color: {P["checker"]}; color: {text}; {sunken} text-align: center; }}
QProgressBar::chunk {{ background-color: {P["title_active"]}; }}

/* Tabs: attached, the current one raised and joined to its page. */
QTabWidget::pane {{ {raised} top: -2px; }}
QTabBar {{ background-color: transparent; }}
QTabBar::tab {{ background-color: {face}; color: {text}; {raised} padding: 3px 10px; margin-right: 1px; }}
QTabBar::tab:!selected {{ background-color: {pressed}; margin-top: 3px; }}
QTabBar::tab:selected {{ border-top-color: {accent}; }}
QTabBar::tab:bottom {{ border-color: {light} {dark} {dark} {light}; }}
QTabBar::tab:bottom:!selected {{ margin-top: 0; margin-bottom: 3px; }}
QTabBar::tab:bottom:selected {{ border-bottom-color: {accent}; }}
QTabBar::scroller {{ width: 16px; }}
QTabBar QToolButton {{ background-color: {face}; {raised} }}
QTabBar::tear {{ width: 0; border: none; }}
QTabBar::close-button {{ subcontrol-position: right; }}

/* Docks: a title in the inactive frame colour, as mwm frames. */
QDockWidget {{ titlebar-close-icon: none; titlebar-normal-icon: none; }}
QDockWidget::title {{ background-color: {P["title_inactive"]}; color: {P["title_inactive_text"]}; {raised} padding: 3px; text-align: left; }}
QDockWidget::close-button, QDockWidget::float-button {{ background-color: {face}; {raised} width: 10px; height: 10px; }}

/* The task panel's boxes. */
QSint--ActionGroup QFrame[class="header"] {{ background-color: {P["title_inactive"]}; {raised} }}
QSint--ActionGroup QToolButton[class="header"] {{ background-color: transparent; color: {P["title_inactive_text"]}; font-weight: bold; text-align: left; border: none; }}
QSint--ActionGroup QFrame[class="header"] QLabel {{ background-color: transparent; }}
QSint--ActionGroup QFrame[class="header"] QLabel[fold="false"] {{ image: url({img}/arrow-down.svg); padding: 3px; }}
QSint--ActionGroup QFrame[class="header"] QLabel[fold="true"] {{ image: url({img}/arrow-up.svg); padding: 3px; }}
QSint--ActionGroup QFrame[class="content"] {{ background-color: {face}; border: 2px solid; border-color: {face} {dark} {dark} {light}; }}
QSint--ActionGroup QToolButton[class="action"] {{ background-color: transparent; text-align: left; border: 2px solid transparent; }}
QSint--ActionGroup QToolButton[class="action"]:hover {{ {raised} background-color: {hover}; }}

/* The 3D view's tabs and MDI windows. */
QTabBar#mdiAreaTabBar::tab:selected {{ background-color: {C["top"]}; color: {readable(C["top"])}; }}
QMdiArea {{ background-color: {P["desktop"]}; }}
QMdiSubWindow {{ background-color: {face}; }}

/* The sketcher's solver messages: semantic colours, readable on the panel. */
Gui--StatefulLabel[state="empty"], Gui--StatefulLabel[state="under_constrained"] {{ color: {text}; }}
Gui--StatefulLabel[state="conflicting_constraints"], Gui--StatefulLabel[state="malformed_constraints"],
Gui--StatefulLabel[state="solver_failed"] {{ color: {legible(P["error"], face, text)}; font-weight: bold; }}
Gui--StatefulLabel[state="redundant_constraints"] {{ color: {legible(P["warning"], face, text)}; }}
Gui--StatefulLabel[state="partially_redundant_constraints"] {{ color: {legible(P["link"], face, text)}; }}
Gui--StatefulLabel[state="fully_constrained"] {{ color: {legible(P["positive"], face, text)}; font-weight: bold; }}
Gui--UrlLabel {{ color: {legible(P["link"], face, text)}; text-decoration: underline; }}
"""


def tokens(P):
    """FreeCAD 1.1's style parameters for this theme (Stylesheets/parameters/
    <theme>.yaml). Our style sheet holds its colours itself; the stock
    overlay style sheet and FreeCAD's own code read these."""
    C = colours(P)
    icons = "white" if readable(P["surface"]) == "#ffffff" else "black"
    values = {
        "3DViewBackgroundRefColor": C["top"], "AccentColor": P["selection"], "AccentBackgroundColor": P["selection"],
        "GeneralBackgroundColor": P["surface"], "GeneralBorderColor": P["border"], "GeneralGridLinesColor": P["groove"],
        "IconsLocationFolderName": "images_classic", "PrimaryColor": P["surface"], "StylesheetIconsColor": icons,
        "TextDisabledColor": P["inactive_text"], "TextEditFieldBackgroundColor": P["window"],
        "TextForegroundColor": P["text"], "TextUrlColor": legible(P["link"], P["surface"], P["text"]),
        "SketcherFullyConstrainedColor": legible(P["positive"], P["surface"], P["text"]),
        "SketcherUnderConstrainedColor": P["text"], "SketcherEmptySketchColor": P["text"],
        "SketcherConflictingConstraintsColor": legible(P["error"], P["surface"], P["text"]),
        "SketcherMalformedConstraintsColor": legible(P["error"], P["surface"], P["text"]),
        "SketcherSolverFailedColor": legible(P["error"], P["surface"], P["text"]),
        "SketcherRedundantConstraintsColor": legible(P["warning"], P["surface"], P["text"]),
        "SketcherPartiallyRedundantConstraintsColor": legible(P["link"], P["surface"], P["text"]),
    }
    return "".join(f'{key}: "{value}"\n' for key, value in values.items())


MODULE = '''"""CDE Copper: re-applies the theme's colours after a palette change.

FreeCAD copies a preference pack's values only when the pack is chosen. CDE
Copper rewrites its pack whenever the palette changes; while the CDE Copper
theme is chosen, this copies the newer colours at start-up (and stores the
pack's stamp, so it does so once). Written by CDE Copper; it removes it again.
"""
import FreeCAD


# FreeCAD runs this file with separate globals and locals: names defined at
# the top would be invisible inside a function, so everything stays in it.
def _apply():
    import os
    import xml.etree.ElementTree as ET
    NAME = "CDE Copper"
    folder = os.path.join(FreeCAD.getUserAppDataDir(), "SavedPreferencePacks", NAME)
    path = os.path.join(folder, NAME + ".cfg")
    main = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    if main.GetString("Theme") != NAME or not os.path.isfile(path):
        return
    stamp = str(os.path.getmtime(path))
    own = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/CDECopper")
    if own.GetString("Applied") == stamp:
        return

    pending = [(ET.parse(path).getroot().find("FCParamGroup"), "")]
    while pending:
        element, prefix = pending.pop()
        for child in element:
            name = child.get("Name")
            if child.tag == "FCParamGroup":
                pending.append((child, prefix + "/" + name if prefix else name))
                continue
            group = FreeCAD.ParamGet("User parameter:" + prefix)
            if child.tag == "FCUInt":
                group.SetUnsigned(name, int(child.get("Value")))
            elif child.tag == "FCBool":
                group.SetBool(name, child.get("Value") == "1")
            elif child.tag == "FCText":
                group.SetString(name, child.text or "")
    own.SetString("Applied", stamp)


try:
    _apply()
except Exception as error:
    FreeCAD.Console.PrintWarning("CDE Copper: " + str(error) + "\\n")
'''


def files(P):
    """Every file of the theme, by its path in FreeCAD's user folder."""
    out = {f"Gui/Stylesheets/{QSS}": qss(P),
           f"Gui/Stylesheets/parameters/{NAME}.yaml": tokens(P),
           f"SavedPreferencePacks/{NAME}/{NAME}.cfg": pack_cfg(P),
           "Mod/CDECopper/InitGui.py": MODULE}
    out.update({f"Gui/Stylesheets/{ICONS}/{name}": svg for name, svg in icons(P).items()})
    return out


# What CDE Copper owns in a FreeCAD user folder, removed on uninstall.
OWNED = (f"Gui/Stylesheets/{QSS}", f"Gui/Stylesheets/{ICONS}", f"Gui/Stylesheets/parameters/{NAME}.yaml",
         f"SavedPreferencePacks/{NAME}", "Mod/CDECopper")


def write(folder: Path, P):
    for rel, content in files(P).items():
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
    package = folder / "SavedPreferencePacks" / "package.xml"
    add_to_package(package)


def add_to_package(package: Path):
    """List the pack in SavedPreferencePacks/package.xml beside the user's own."""
    if not package.exists():
        package.parent.mkdir(parents=True, exist_ok=True)
        package.write_text(PACKAGE)
        return
    tree = ET.parse(package)
    content = tree.getroot().find("content")
    if content is None:
        content = ET.SubElement(tree.getroot(), "content")
    if any(p.findtext("name") == NAME for p in content.findall("preferencepack")):
        return
    content.append(ET.fromstring(PACKAGE).find("content/preferencepack"))
    ET.indent(tree, "  ")
    tree.write(package, encoding="UTF-8", xml_declaration=True)


def remove_from_package(package: Path):
    if not package.exists():
        return
    tree = ET.parse(package)
    content = tree.getroot().find("content")
    packs = content.findall("preferencepack") if content is not None else []
    ours = [p for p in packs if p.findtext("name") == NAME]
    if len(ours) == len(packs):
        package.unlink()
        return
    for pack in ours:
        content.remove(pack)
    tree.write(package, encoding="UTF-8", xml_declaration=True)


# The Flatpak keeps its own XDG folders, apart from ~/.local/share.
FLATPAK_DATA = Path(".var/app/org.freecad.FreeCAD/data")


def user_folders(data: Path, home: Path = None):
    """FreeCAD's per-user folders, of a native FreeCAD (under data) and of
    the Flatpak (under home): one per version since 1.1 (v1-1), or the
    folder itself for 1.0. Only folders FreeCAD already made are used."""
    folders = []
    for base in [data / "FreeCAD"] + ([home / FLATPAK_DATA / "FreeCAD"] if home else []):
        if base.is_dir():
            versions = sorted(p for p in base.glob("v[0-9]*-[0-9]*") if p.is_dir())
            folders += versions or [base]
    return folders


def build_freecad(out: Path, P):
    """The theme for the release archive, laid out as FreeCAD's user folder."""
    for rel, content in files(P).items():
        path = out / "freecad" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    (out / "freecad" / "SavedPreferencePacks" / "package.xml").write_text(PACKAGE)
