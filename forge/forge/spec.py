"""The theme specification: JSON schema for the LLM and the semantic check.

The schema goes to the server as a grammar (response_format), so only
syntactically valid answers come back. What a grammar cannot express —
contrasts, brightness fitting the mode, brand names in image prompts —
validate() checks and reports in sentences the model can act on directly.
"""
import re

from . import fonts
from .palette import contrast, luminance, mix, on, readable, shift

HEX = {"type": "string", "pattern": "^#[0-9a-f]{6}$"}
COLOR_KEYS = {
    "surface": "surface of windows, buttons, panel contents (the main colour)",
    "window": "background of lists, text fields, documents",
    "panel": "taskbar/panel",
    "text": "normal text on surface and window",
    "accent": "selection (highlighted entries), text on it must be legible",
    "glow": "second accent colour for hover, links, glowing edges",
    "title_active": "title bar of the active window",
    "title_inactive": "title bar of inactive windows (muted)",
    "desktop": "fallback background colour behind the wallpaper",
}
EMBLEMS = ["star", "gear", "shield", "hexagon", "chevron", "diamond", "lightning",
           "crosshair", "wing", "circle"]
BUTTONS_RE = "^[MSHFBLIAX_]{0,6}$"

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "name", "description", "shape", "decoration", "font",
                 "emblem", "boot", "variants"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z][a-z0-9-]{2,24}$"},
        "name": {"type": "string", "minLength": 3, "maxLength": 32},
        "description": {"type": "string", "minLength": 10, "maxLength": 300},
        "shape": {
            "type": "object", "additionalProperties": False,
            "required": ["corner", "corner_size", "bevel", "bevel_width",
                         "outer_border", "edge_glow"],
            "properties": {
                "corner": {"enum": ["square", "chamfer", "round"]},
                "corner_size": {"type": "integer", "minimum": 0, "maximum": 8},
                "bevel": {"enum": ["flat", "raised"]},
                "bevel_width": {"type": "integer", "minimum": 0, "maximum": 3},
                "outer_border": {"type": "integer", "minimum": 0, "maximum": 2},
                "edge_glow": {"type": "boolean"},
            },
        },
        "decoration": {
            "type": "object", "additionalProperties": False,
            "required": ["title_height", "border", "button_shape", "button_size",
                         "title_align", "buttons_left", "buttons_right"],
            "properties": {
                "title_height": {"type": "integer", "minimum": 18, "maximum": 40},
                "border": {"type": "integer", "minimum": 1, "maximum": 8},
                "button_shape": {"enum": ["square", "round", "chamfer", "diamond"]},
                "button_size": {"type": "integer", "minimum": 12, "maximum": 30},
                "title_align": {"enum": ["left", "center", "right"]},
                "buttons_left": {"type": "string", "pattern": BUTTONS_RE},
                "buttons_right": {"type": "string", "pattern": BUTTONS_RE},
            },
        },
        "font": {"enum": list(fonts.CATALOG)},
        "emblem": {
            "type": "object", "additionalProperties": False,
            "required": ["shape", "render", "label"],
            "properties": {
                "shape": {"enum": EMBLEMS},
                "render": {"enum": ["blender", "inkscape"]},
                "label": {"type": "string", "minLength": 2, "maxLength": 14},
            },
        },
        "boot": {
            "type": "object", "additionalProperties": False,
            "required": ["plymouth", "grub"],
            "properties": {
                "plymouth": {"enum": ["emblem-bar", "emblem-pulse", "text-bar"]},
                "grub": {"enum": ["centered", "left-panel"]},
            },
        },
        "variants": {
            "type": "array", "minItems": 1, "maxItems": 3,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["id", "name", "look", "lead", "mode", "colors", "wallpaper_prompt"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z][a-z0-9]{1,15}$"},
                    "look": {"type": "string", "minLength": 20, "maxLength": 300},
                    "lead": HEX,
                    "name": {"type": "string", "minLength": 2, "maxLength": 24},
                    "mode": {"enum": ["dark", "light"]},
                    "colors": {
                        "type": "object", "additionalProperties": False,
                        "required": list(COLOR_KEYS),
                        "properties": {k: HEX for k in COLOR_KEYS},
                    },
                    "wallpaper_prompt": {"type": "string", "minLength": 120, "maxLength": 1100},
                },
            },
        },
    },
}

# Terms that must not end up in image prompts or names: brands of the model
# (image models paint logos otherwise), plus what the user adds with --avoid.
# Unambiguous names only: "windows" or "apple" in an image prompt are mostly
# windows and apples (first series run: a false alarm on "command tent windows").
TRADEMARKS = ["red alert", "command & conquer", "command and conquer", "c&c",
              "westwood", "electronic arts", "microsoft", "macos", "star wars",
              "warhammer", "fallout", "nintendo", "playstation"]


# Words the image model takes literally: "icons" paints symbols into the
# picture, "sign"/"poster"/"map" make up lettering. Found in the first RA2 run.
PROMPT_TRAPS = ["icon", "icons", "desktop", "interface", "ui", "screen", "screens", "monitor",
                "sign", "signs", "signage", "poster", "posters", "label", "labels", "map", "maps",
                "letter", "letters", "word", "words", "writing", "banner", "banners", "logo"]


def _text_for(text, bgs):
    """A text tone that reaches 4.5:1 on all backgrounds — as a suggestion."""
    for goal in (7.0, 4.5):
        c = text
        for _ in range(3):
            for bg in bgs:
                c = readable(c, bg, goal)
        if all(contrast(c, bg) >= goal for bg in bgs):
            return c
    for cand in ("#f2f2f2", "#141414", "#ffffff", "#000000"):
        if all(contrast(cand, bg) >= 4.5 for bg in bgs):
            return cand
    return None


def _hs(col):
    import colorsys
    from .palette import rgb
    h, _, sat = colorsys.rgb_to_hls(*(x / 255 for x in rgb(col)))
    return h * 360, sat


def _hue_dist(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _lum_fix(col, dark):
    c = col
    for _ in range(40):
        if (dark and luminance(c) <= 0.16) or (not dark and luminance(c) >= 0.40):
            return c
        c = shift(c, -0.025 if dark else 0.025)
    return c


def names_from_request(request):
    """Protected names from the request itself: the title (before "(" or ":")
    as a whole and coined words in it (hyphen, inner capital, e.g. "Pip-Boy",
    "StarCraft"). Ordinary words like "Red" alone stay allowed — only the
    whole phrase "Red Alert 2" is barred."""
    title = re.split(r"[(:]", request)[0].strip()
    out = [title.lower()] if len(title) >= 3 else []
    for word in title.split():
        if len(word) > 2 and ("-" in word or any(ch.isupper() for ch in word[1:])):
            out.append(word.lower())
    return out


def fixed_buttons(d):
    """Add the required buttons: I, A, X on the right, without duplicates."""
    left = "".join(ch for ch in d["buttons_left"] if ch not in "IAX")
    right = "".join(ch for ch in d["buttons_right"].replace("_", "") if ch not in "IAX" and ch not in left)
    return {"buttons_left": left, "buttons_right": right[:3] + "IAX"}


def _sentences(text):
    return re.split(r"(?<=[.!?])\s+", text.strip())


def trap_sentences(prompt):
    out = []
    for sent in _sentences(prompt.split("no text")[0] if "no text" in prompt.lower() else prompt):
        if {w for w in re.findall(r"[a-z]+", sent.lower())} & set(PROMPT_TRAPS):
            out.append(sent)
    return out


def strip_traps(prompt):
    """The last stage: strike sentences with trap words. One sentence fewer
    does an image prompt no harm; a painted icon in the background does."""
    keep = [s for s in _sentences(prompt) if s not in trap_sentences(prompt)]
    out = " ".join(keep)
    if "no text" not in out.lower():
        out = out.rstrip(". ") + ". No text, no logos, no brand names."
    return out


def validate(spec, avoid=()):
    """Returns a list of understandable error messages (empty = fine)."""
    return [msg for _, msg in validate_paths(spec, avoid)]


class _Errors(list):
    """An error list that records for each message which part it concerns."""
    path = ()

    def append(self, msg):
        super().append((self.path, msg))


def validate_paths(spec, avoid=()):
    """Like validate(), but as (path, message). A path is e.g. ("variants", 1, "colors"),
    so that the LLM can repair just this part."""
    errors = _Errors()
    request = spec.get("_meta", {}).get("request", "")
    banned = [t.lower() for t in list(TRADEMARKS) + list(avoid) + names_from_request(request)]

    def no_marks(field, text):
        low = text.lower()
        for t in banned:
            if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low):
                errors.append(f"{field} contains the protected name \"{t}\" — "
                              "describe the style in your own words instead")

    errors.path = ()
    no_marks("name", spec["name"])
    no_marks("description", spec["description"])
    no_marks("emblem.label", spec["emblem"]["label"])

    sh = spec["shape"]
    errors.path = ("shape",)
    if sh["corner"] == "square" and sh["corner_size"] != 0:
        errors.append("shape.corner is square, so shape.corner_size must be 0")
    if sh["corner"] != "square" and sh["corner_size"] < 2:
        errors.append(f"shape.corner is {sh['corner']}, so corner_size must be at least 2")
    if sh["bevel"] == "flat" and sh["bevel_width"] != 0:
        errors.append("shape.bevel is flat, so bevel_width must be 0")
    if sh["bevel"] == "raised" and sh["bevel_width"] == 0:
        errors.append("shape.bevel is raised, so bevel_width must be at least 1")

    d = spec["decoration"]
    errors.path = ("decoration",)
    if d["button_size"] > d["title_height"] - 2:
        errors.append(f"decoration.button_size ({d['button_size']}) must be at least 2 smaller "
                      f"than title_height ({d['title_height']})")
    used = d["buttons_left"] + d["buttons_right"]
    missing = [ch for ch in "IAX" if ch not in used]
    if missing:
        right = fixed_buttons(d)["buttons_right"]
        errors.append(f"buttons missing: {', '.join(missing)} (I minimize, A maximize, X close "
                      f"are required) — set buttons_right to \"{right}\"")
    dup = {ch for ch in used if ch != "_" and used.count(ch) > 1}
    if dup:
        errors.append(f"buttons twice: {''.join(sorted(dup))}")

    errors.path = ()
    ids = [v["id"] for v in spec["variants"]]
    if len(set(ids)) != len(ids):
        errors.append("variants: the id values must differ")

    for i, v in enumerate(spec["variants"]):
        tag = f"variant \"{v['id']}\""
        c = v["colors"]
        errors.path = ("variants", i)
        no_marks(f"{tag}: name", v["name"])
        errors.path = ("variants", i, "wallpaper_prompt")
        no_marks(f"{tag}: wallpaper_prompt", v["wallpaper_prompt"])
        wp = v["wallpaper_prompt"].lower()
        body = wp.split("no text")[0]
        traps = sorted({w for w in re.findall(r"[a-z]+", body) if w in PROMPT_TRAPS})
        if traps:
            quoted = " / ".join(f"\"{t}\"" for t in trap_sentences(v["wallpaper_prompt"]))
            errors.append(f"{tag}: wallpaper_prompt contains {', '.join(traps)} — the image model paints "
                          f"that literally (symbols, lettering). Rewrite these sentences without these words: "
                          f"{quoted}. Instead of room for symbols: \"calm, empty area\".")
        if "no text" not in wp:
            errors.append(f"{tag}: wallpaper_prompt must end with \"no text, no logos\"")
        if len(wp.split()) < 25:
            errors.append(f"{tag}: wallpaper_prompt is too short — a whole paragraph with "
                          "medium, motif, light, colours and composition")
        dark = v["mode"] == "dark"
        errors.path = ("variants", i, "colors")
        # Error messages with a concrete value: small models act on
        # "take #1c1c1c" reliably, on "choose a darker text" often not.
        luma_ok = True
        for key in ("surface", "window"):
            lum = luminance(c[key])
            if (dark and lum > 0.18) or (not dark and lum < 0.35):
                luma_ok = False
                errors.append(f"{tag}: mode is {v['mode']}, but colors.{key} {c[key]} is too "
                              f"{'light' if dark else 'dark'} (luminance {lum:.2f}) — "
                              f"set colors.{key} to {_lum_fix(c[key], dark)}")
        bad = [bg for bg in ("surface", "window", "panel") if contrast(c["text"], c[bg]) < 4.5]
        if bad and luma_ok:
            fix = _text_for(c["text"], [c[b] for b in ("surface", "window", "panel")])
            worst = ", ".join(f"{b} {c[b]} {contrast(c['text'], c[b]):.1f}:1" for b in bad)
            if fix:
                errors.append(f"{tag}: colors.text {c['text']} is not legible on {worst} "
                              f"(4.5:1 needed) — set colors.text to {fix}")
            else:
                # No text fits all three surfaces. Then suggest a clear text
                # tone fitting the mode and adjust each surface that is not
                # enough with it, concretely — always solvable.
                fix_text = "#ececec" if dark else "#161616"
                fixes = [f"colors.text to {fix_text}"]
                for b_ in ("surface", "window", "panel"):
                    col = c[b_]
                    for _ in range(40):
                        if contrast(fix_text, col) >= 4.5:
                            break
                        col = shift(col, -0.02 if dark else 0.02)
                    if col != c[b_]:
                        fixes.append(f"colors.{b_} to {col}")
                errors.append(f"{tag}: colors.text {c['text']} is not legible on {worst} "
                              f"(4.5:1 needed) — set " + ", ".join(fixes))
        # The lead colour the model named itself must be carried by the title
        # bar — the most visible element of every window (like petrol in NT
        # Legacy, copper in CDE). Without this rule the model met "lead
        # appears" with the accent alone and left the titles grey.
        lead_h, lead_s = _hs(v["lead"])
        th, ts = _hs(c["title_active"])
        if lead_s >= 0.25 and (_hue_dist(th, lead_h) > 22 or ts < 0.2):
            errors.append(f"{tag}: title_active {c['title_active']} does not carry the lead colour lead {v['lead']} "
                          f"— set title_active to {readable(v['lead'], on(v['lead']))}")
        k = contrast(c["accent"], on(c["accent"]))
        if k < 4.5:
            errors.append(f"{tag}: colors.accent {c['accent']} carries neither black nor white "
                          f"text legibly ({k:.1f}:1) — set colors.accent e.g. to "
                          f"{readable(c['accent'], on(c['accent']))}")
        k = contrast(c["title_active"], on(c["title_active"]))
        if k < 4.5:
            errors.append(f"{tag}: colors.title_active {c['title_active']} carries no legible "
                          f"title text ({k:.1f}:1) — set title_active e.g. to "
                          f"{readable(c['title_active'], on(c['title_active']))}")
        if contrast(c["accent"], c["window"]) < 1.4:
            fix = c["accent"]
            step = -0.025 if luminance(c["window"]) > 0.18 else 0.025
            for _ in range(30):
                fix = shift(fix, step)
                if contrast(fix, c["window"]) >= 1.6 and contrast(fix, on(fix)) >= 4.5:
                    break
            errors.append(f"{tag}: colors.accent hardly stands out from colors.window "
                          f"({contrast(c['accent'], c['window']):.2f}:1, 1.4:1 needed) — "
                          f"set colors.accent to {fix}")
        if contrast(c["title_active"], c["title_inactive"]) < 1.25 and \
                c["title_active"] == c["title_inactive"]:
            errors.append(f"{tag}: title_active and title_inactive must differ")
    return errors
