"""Kate's editor colours for CDE Copper, one theme per palette.

The text area of Kate, KWrite and KDevelop is drawn by KTextEditor, which
takes its colours from a KSyntaxHighlighting theme; neither the colour scheme
nor Kvantum reach it. With "Automatic color theme selection" (KTextEditor's
default) it asks Repository::themeForPalette() for a theme whose background
equals QPalette::Base and whose selection equals QPalette::Highlight, and
falls back to Breeze Light or Breeze Dark when there is none.

So every palette gets a theme of its own, with exactly those two colours, in

    org.kde.syntax-highlighting/themes/CDE<palette>.theme

All of them are installed at once and nothing is rewritten when a palette is
applied: a running editor read the theme folder when it started and only looks
again at its next start, but it does follow the palette at once to a theme it
already knows. Nobody's choice is overridden either, as an editor set to a
fixed theme keeps it.

Every colour comes from the View and Selection colours alone (the colours the
editor is matched by), so two palettes that share them, like Broica and
Default, get the same editor whichever of the two themes is found first.
"""
import json
from pathlib import Path

from palettes import contrast, legible, mix

FOLDER = "org.kde.syntax-highlighting/themes"
# Style hues, the usual ones of a code editor. They are only starting points:
# each is moved toward the text colour until it reads on the palette's field.
HUES = dict(
    purple="#7a2fb0", blue="#1457b8", cyan="#0a7d94", green="#1a7a32",
    red="#b81f1f", orange="#b85400", gold="#8f6f00", pink="#b02a86",
)
# Contrast on the field. A mid-tone field leaves hardly any room: black or
# white text only just reaches 4.5:1 there, so holding the hues to that too
# would turn all of them into the text colour. They get a share of what the
# field offers instead, and never less than MARK.
CODE = 4.5
COMMENT = 3.5
MARK = 3.0
SHARE = 0.62


def code_target(field, ink):
    return max(MARK, min(CODE, contrast(field, ink) * SHARE))


def hues(field, ink):
    """The style hues on this field. A palette whose text has a colour of its
    own (Darkroom's red, there to keep night vision) keeps the hues close to it."""
    target = code_target(field, ink)
    channels = [int(ink[i:i+2], 16) for i in (1, 3, 5)]
    pull = 0.7 if max(channels) - min(channels) > 64 else 0
    return {name: legible(mix(value, ink, pull), field, ink, target) for name, value in HUES.items()}


def tint(hue, field, ink):
    """A background for text in ink, as far toward the hue as ink still reads.

    Light text needs a dark background, so the hue is taken down first."""
    target = min(CODE, contrast(field, ink) * 0.8)
    if contrast(ink, "#000000") > contrast(ink, "#ffffff"):
        hue = mix(hue, "#000000", 0.55)
    for step in range(16, -1, -1):
        candidate = mix(field, hue, step / 20)
        if contrast(candidate, ink) >= target:
            return candidate
    return field


def styles(P):
    """Palette onto KSyntaxHighlighting's default styles."""
    field, ink, selected = P["window"], P["window_text"], P["selection_text"]
    hue = hues(field, ink)
    faint = min(COMMENT, code_target(field, ink))
    comment = legible(mix(ink, field, 0.5), field, ink, faint)
    doc = legible(mix(hue["cyan"], field, 0.3), field, ink, faint)

    def style(colour, **extra):
        return {"text-color": colour, "selected-text-color": selected, **extra}
    plain = style(ink)
    return {
        "Normal": {**plain, "bold": False, "italic": False, "underline": False, "strike-through": False},
        "Keyword": style(ink, bold=True),
        "ControlFlow": style(ink, bold=True),
        "Function": style(hue["purple"]),
        "BuiltIn": style(hue["purple"], bold=True),
        "Extension": style(hue["blue"], bold=True),
        "Variable": style(hue["blue"]),
        "Attribute": style(hue["blue"]),
        "DataType": style(hue["cyan"]),
        "Operator": style(hue["pink"]),
        "Annotation": style(hue["pink"]),
        "Preprocessor": style(hue["green"]),
        "Others": style(hue["green"]),
        "Import": style(hue["orange"]),
        "SpecialString": style(hue["orange"]),
        "Constant": style(hue["orange"]),
        "String": style(hue["red"]),
        "VerbatimString": style(hue["red"]),
        "Char": style(hue["pink"]),
        "SpecialChar": style(hue["orange"], bold=True),
        "DecVal": style(hue["gold"]),
        "BaseN": style(hue["gold"]),
        "Float": style(hue["gold"]),
        "Information": style(hue["gold"]),
        "Comment": style(comment, italic=True),
        "Documentation": style(doc, italic=True),
        "CommentVar": style(doc, bold=True, italic=True),
        "RegionMarker": style(ink, **{"background-color": tint("#3f7fff", field, ink)}),
        "Warning": style(hue["orange"], bold=True),
        "Alert": style(ink, bold=True, **{"background-color": tint("#ff3030", field, ink)}),
        "Error": style(hue["red"], underline=True),
    }


def custom_styles(P):
    """CSV colours its columns itself; the first three use default styles."""
    field, ink, selected = P["window"], P["window_text"], P["selection_text"]
    hue = hues(field, ink)
    columns = {}
    for number, name in zip(range(3, 10), ("green", "pink", "orange", "blue", "red", "cyan", "purple")):
        for label in (f"Column {number}", f"Column {number} Separator"):
            columns[label] = {"text-color": hue[name], "selected-text-color": selected}
    return {"CSV": columns}


def editor_colours(P):
    """Palette onto the editor's own colours; the first two select the theme."""
    field, ink, selection = P["window"], P["window_text"], P["selection"]
    border = mix(field, ink, 0.09)

    def mark(colour):
        return legible(colour, border, ink, MARK)
    return {
        "BackgroundColor": field,
        "TextSelection": selection,
        "CurrentLine": mix(field, ink, 0.05),
        "IconBorder": border,
        "LineNumbers": legible(mix(ink, border, 0.5), border, ink, MARK),
        "CurrentLineNumber": ink,
        "Separator": mix(field, ink, 0.3),
        "IndentationLine": mix(field, ink, 0.18),
        "TabMarker": mix(field, ink, 0.25),
        "WordWrapMarker": mix(field, ink, 0.18),
        "CodeFolding": mix(field, selection, 0.4),
        "BracketMatching": tint("#ffd800", field, ink),
        "SearchHighlight": tint("#ffe600", field, ink),
        "ReplaceHighlight": tint("#40e040", field, ink),
        "SpellChecking": legible("#c81414", field, ink, MARK),
        "ModifiedLines": mark("#d08000"),
        "SavedLines": mark("#209048"),
        "MarkBookmark": mark("#2060e0"),
        "MarkBreakpointActive": mark("#d01818"),
        "MarkBreakpointReached": mark("#c8a000"),
        "MarkBreakpointDisabled": mark("#b030b0"),
        "MarkExecution": mark("#707074"),
        "MarkWarning": mark("#d08000"),
        "MarkError": mark("#d01818"),
        "TemplateBackground": mix(field, ink, 0.12),
        "TemplatePlaceholder": tint("#40e080", field, ink),
        "TemplateFocusedPlaceholder": tint("#20c060", field, ink),
        "TemplateReadOnlyPlaceholder": tint("#ff6060", field, ink),
    }


def theme(P, name):
    return {
        "metadata": {"name": name, "revision": 1, "license": "SPDX-License-Identifier: GPL-2.0-or-later"},
        "text-styles": styles(P),
        "custom-styles": custom_styles(P),
        "editor-colors": editor_colours(P),
    }


def write(base: Path, ident, name, P):
    path = Path(base) / FOLDER / f"{ident}.theme"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(theme(P, name), indent=2) + "\n")


def build_kate(out: Path, P):
    """All themes for the release: Copper from build.py's own colours, the rest
    from the palettes, the same pairs of names the colour schemes use."""
    import palettes
    write(out, "CDECopper", "CDE Copper", P)
    for name in palettes.names():
        write(out, "CDE" + name, "CDE " + name, palettes.theme(name))
