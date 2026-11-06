"""Terminal colours for CDE Copper, generated from a palette.

Terminals keep sixteen colours and a background of their own, out of reach of
the colour scheme. There are two sets, chosen in the Style Manager:

    dark    the default: a background darkened from the workspace colour, so
            programs that assume a dark terminal stay legible
    field   the palette's text field, like the editors; programs that paint
            their own surfaces suffer (Midnight Commander's blue panels)

The set is written for each terminal in its own format at every palette
change: Konsole's colour scheme (its theme profile names it; Yakuake takes
Konsole's default profile), xterm's and uxterm's app-defaults in the home
folder, and for Alacritty, kitty, foot and WezTerm a fragment beside their
configuration. A configuration that does not exist yet is created to load the
fragment. One that does exist is the user's: it is left alone and the user is
told the one line to add.
"""
from pathlib import Path
import shutil

from palettes import contrast, legible, luminance, mix

KINDS = ("dark", "field")
DEFAULT = "dark"
MARK = "Written by CDE Copper; delete this line to keep your own settings."
FONT = "IBM Plex Mono"
FONT_SIZE = 11
WHITE, BLACK = "#ffffff", "#000000"
# Red, green, yellow, blue, magenta, cyan.
ON_DARK = ("#e0605a", "#6cbf72", "#d8b24a", "#3f78cc", "#b98adf", "#3fb8c6")
ON_LIGHT = ("#b81f1f", "#1a7a32", "#8f6f00", "#1457b8", "#7a2fb0", "#0a7d94")
BLUE = 3


def tinted(ink, hues):
    """A text colour of its own (Darkroom's red, there to keep night vision)
    draws the hues toward it."""
    channels = [int(ink[i:i+2], 16) for i in (1, 3, 5)]
    pull = 0.7 if max(channels) - min(channels) > 64 else 0
    return [mix(hue, ink, pull) for hue in hues]


def dark(P):
    background = P["desktop"]
    for step in range(21):
        background = mix(P["desktop"], BLACK, step / 20)
        if luminance(background) <= 0.016:
            break
    ink = P["window_text"]
    if contrast(ink, background) >= 4.5:    # a dark field's text, also a coloured one
        foreground = ink
    else:
        foreground = legible(mix(P["window"], WHITE, 0.2), background, WHITE, 10)
    hues = tinted(foreground, ON_DARK)
    base = [legible(hue, background, WHITE, 5.5) for hue in hues]
    # Blue is also a surface: Midnight Commander puts white text on it, so it
    # cannot rise like the others; it only has to read as text at all.
    base[BLUE] = legible(hues[BLUE], background, WHITE, 3)
    bright = [legible(mix(hue, WHITE, 0.3), background, WHITE, 7) for hue in hues]
    # Bright colours must also read on that blue surface.
    bright = [legible(colour, base[BLUE], WHITE, 3) for colour in bright]
    return dict(background=background, foreground=foreground,
                ansi=[mix(background, WHITE, 0.14), *base, foreground,
                      legible(mix(background, WHITE, 0.42), background, WHITE, 3.5), *bright, WHITE])


def field(P):
    background, ink = P["window"], P["window_text"]
    target = min(4.5, max(3, contrast(background, ink) * 0.62))
    hues = tinted(ink, ON_LIGHT)
    base = [legible(hue, background, ink, target) for hue in hues]
    bright = [legible(mix(hue, ink, 0.2), background, ink, target) for hue in hues]
    # On a dark field black stays the darkest colour, on a light one it is the
    # text. "White" must not vanish on a light field, so it follows the text.
    black = mix(background, BLACK, 0.4) if luminance(background) < luminance(ink) else ink
    return dict(background=background, foreground=ink,
                ansi=[black, *base, legible(mix(background, ink, 0.55), background, ink, 3),
                      legible(mix(ink, background, 0.45), background, ink, min(3.5, target)), *bright, ink])


def colours(P, kind=DEFAULT):
    """Background, foreground, the sixteen colours and the palette's selection."""
    return {**(field(P) if kind == "field" else dark(P)),
            "selection": P["selection"], "selection_text": P["selection_text"]}


def _rgb(colour):
    return ",".join(str(int(colour[i:i+2], 16)) for i in (1, 3, 5))


def konsole(C, name="CDE Copper"):
    lines = ["[General]", f"Description={name}", "Opacity=1", "Blur=false", "Wallpaper="]
    for role, value in (("Background", C["background"]), ("Foreground", C["foreground"])):
        lines += ["", f"[{role}]", f"Color={_rgb(value)}", "", f"[{role}Intense]", f"Color={_rgb(value)}"]
        faint = value if role == "Background" else mix(value, C["background"], 0.3)
        lines += ["", f"[{role}Faint]", f"Color={_rgb(faint)}"]
    for i in range(8):
        lines += ["", f"[Color{i}]", f"Color={_rgb(C['ansi'][i])}",
                  "", f"[Color{i}Intense]", f"Color={_rgb(C['ansi'][i + 8])}",
                  "", f"[Color{i}Faint]", f"Color={_rgb(mix(C['ansi'][i], C['background'], 0.3))}"]
    return "\n".join(lines) + "\n"


def xterm(C, widget="XTerm"):
    lines = [f"! {MARK}", f"{widget}*VT100*background: {C['background']}", f"{widget}*VT100*foreground: {C['foreground']}",
             f"{widget}*VT100*cursorColor: {C['foreground']}", f"{widget}*VT100*highlightColor: {C['selection']}",
             f"{widget}*VT100*highlightTextColor: {C['selection_text']}", f"{widget}*VT100*highlightColorMode: true",
             f"{widget}*VT100*faceName: {FONT}", f"{widget}*VT100*faceSize: {FONT_SIZE}"]
    lines += [f"{widget}*VT100*color{i}: {value}" for i, value in enumerate(C["ansi"])]
    return "\n".join(lines) + "\n"


NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")


def alacritty(C):
    def group(title, part):
        return [f"[colors.{title}]", *(f'{name} = "{value}"' for name, value in zip(NAMES, part)), ""]
    return "\n".join([
        f"# {MARK}", "[colors.primary]", f'background = "{C["background"]}"', f'foreground = "{C["foreground"]}"', "",
        "[colors.selection]", f'background = "{C["selection"]}"', f'text = "{C["selection_text"]}"', "",
        *group("normal", C["ansi"][:8]), *group("bright", C["ansi"][8:]),
        "[font]", f"size = {FONT_SIZE}", "", "[font.normal]", f'family = "{FONT}"', ""])


def kitty(C):
    return "\n".join([
        f"# {MARK}", f"font_family {FONT}", f"font_size {FONT_SIZE}", f"background {C['background']}", f"foreground {C['foreground']}",
        f"cursor {C['foreground']}", f"selection_background {C['selection']}", f"selection_foreground {C['selection_text']}",
        *(f"color{i} {value}" for i, value in enumerate(C["ansi"])), ""])


def foot(C):
    bare = {key: C[key][1:] for key in ("background", "foreground", "selection", "selection_text")}
    return "\n".join([
        f"# {MARK}", "[main]", f"font={FONT}:size={FONT_SIZE}", "", "[colors-dark]", f"background={bare['background']}", f"foreground={bare['foreground']}",
        f"selection-background={bare['selection']}", f"selection-foreground={bare['selection_text']}",
        *(f"regular{i}={value[1:]}" for i, value in enumerate(C["ansi"][:8])),
        *(f"bright{i}={value[1:]}" for i, value in enumerate(C["ansi"][8:])), ""])


def wezterm(C):
    def row(part):
        return "[" + ", ".join(f'"{value}"' for value in part) + "]"
    return "\n".join([
        f"# {MARK}", "[colors]", f'background = "{C["background"]}"', f'foreground = "{C["foreground"]}"',
        f'cursor_bg = "{C["foreground"]}"', f'cursor_border = "{C["foreground"]}"', f'cursor_fg = "{C["background"]}"',
        f'selection_bg = "{C["selection"]}"', f'selection_fg = "{C["selection_text"]}"',
        f"ansi = {row(C['ansi'][:8])}", f"brights = {row(C['ansi'][8:])}", "", "[metadata]", 'name = "CDE Copper"', ""])


def targets(config: Path):
    """Per terminal: its program, folder, fragment and writer, its main
    configuration, what that needs to load the fragment, and the text to find."""
    return (
        dict(program="alacritty", folder=config / "alacritty", fragment="cde-copper.toml", write=alacritty, main="alacritty.toml",
             line='[general]\nimport = ["cde-copper.toml"]', needle="cde-copper.toml", comment="#"),
        dict(program="kitty", folder=config / "kitty", fragment="cde-copper.conf", write=kitty, main="kitty.conf",
             line="include cde-copper.conf", needle="cde-copper.conf", comment="#"),
        dict(program="foot", folder=config / "foot", fragment="cde-copper.ini", write=foot, main="foot.ini",
             line=f"include={config}/foot/cde-copper.ini", needle="cde-copper.ini", comment="#"),
        dict(program="wezterm", folder=config / "wezterm", fragment="colors/CDECopper.toml", write=wezterm, main="wezterm.lua",
             line='return { color_scheme = "CDE Copper", font_size = %d, font = require("wezterm").font("%s") }' % (FONT_SIZE, FONT),
             needle="CDE Copper", comment="--"),
    )


def ours(path: Path):
    return path.is_file() and MARK in path.read_text(errors="replace")


def _write_ours(path: Path, content):
    """Only over nothing or over our own file."""
    if path.exists() and not ours(path):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def write_all(P, kind, data: Path, config: Path, home: Path):
    """Write the set for every terminal present. Returns what the user has to
    do by hand, one line per terminal whose configuration is their own."""
    C = colours(P, kind)
    (data / "konsole").mkdir(parents=True, exist_ok=True)
    (data / "konsole/CDECopper.colorscheme").write_text(konsole(C))
    notes = []
    for widget, program in (("XTerm", "xterm"), ("UXTerm", "uxterm")):
        path = home / widget
        if shutil.which(program) or ours(path):
            if not _write_ours(path, xterm(C, widget)):
                notes.append(f"{path} is your own; {program} keeps its colours")
    for term in targets(config):
        if not (shutil.which(term["program"]) or term["folder"].is_dir()):
            continue
        fragment = term["folder"] / term["fragment"]
        if not _write_ours(fragment, term["write"](C)):
            notes.append(f"{fragment} is your own; {term['program']} keeps its colours")
            continue
        main = term["folder"] / term["main"]
        if not main.exists():
            _write_ours(main, f"{term['comment']} {MARK}\n{term['line']}\n")
        elif term["needle"] not in main.read_text(errors="replace"):
            notes.append(f"{main} is your own; to follow the palette add: {term['line']}")
    return notes


def remove_all(config: Path, home: Path):
    """Our files only."""
    for path in (home / "XTerm", home / "UXTerm"):
        if ours(path):
            path.unlink()
    for term in targets(config):
        for path in (term["folder"] / term["main"], term["folder"] / term["fragment"]):
            if ours(path):
                path.unlink()
