"""Die Theme-Spezifikation: JSON-Schema für das LLM und semantische Prüfung.

Das Schema wird dem Server als Grammatik mitgegeben (response_format), damit
kommen nur syntaktisch gültige Antworten zurück. Was eine Grammatik nicht
ausdrücken kann — Kontraste, Helligkeit passend zum Modus, Markennamen in
Bild-Prompts — prüft validate() und meldet es in Sätzen, die das Modell
direkt umsetzen kann.
"""
import re

from . import fonts
from .palette import contrast, luminance, mix, on, readable, shift

HEX = {"type": "string", "pattern": "^#[0-9a-f]{6}$"}
COLOR_KEYS = {
    "surface": "Fläche von Fenstern, Knöpfen, Panels-Inhalt (Hauptfarbe)",
    "window": "Hintergrund von Listen, Textfeldern, Dokumenten",
    "panel": "Taskleiste/Panel",
    "text": "Normaler Text auf surface und window",
    "accent": "Auswahl (markierte Einträge), muss mit Text darauf lesbar sein",
    "glow": "Zweite Akzentfarbe für Hover, Links, leuchtende Kanten",
    "title_active": "Titelleiste des aktiven Fensters",
    "title_inactive": "Titelleiste inaktiver Fenster (gedämpft)",
    "desktop": "Ersatz-Hintergrundfarbe hinter dem Hintergrundbild",
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

# Begriffe, die nicht in Bild-Prompts oder Namen landen dürfen: Marken der
# Vorlage (Bildmodelle malen sonst Logos nach), dazu was der Nutzer per
# --avoid ergänzt.
# Nur eindeutige Namen: „windows“ oder „apple“ sind im Bild-Prompt meist
# Fenster und Äpfel (erster Serienlauf: Fehlalarm bei „command tent windows“).
TRADEMARKS = ["red alert", "command & conquer", "command and conquer", "c&c",
              "westwood", "electronic arts", "microsoft", "macos", "star wars",
              "warhammer", "fallout", "nintendo", "playstation"]


# Wörter, die das Bildmodell wörtlich nimmt: „icons“ malt Symbole ins Bild,
# „sign“/„poster“/„map“ erzeugen Fantasieschrift. Gefunden im ersten RA2-Lauf.
PROMPT_TRAPS = ["icon", "icons", "desktop", "interface", "ui", "screen", "screens", "monitor",
                "sign", "signs", "signage", "poster", "posters", "label", "labels", "map", "maps",
                "letter", "letters", "word", "words", "writing", "banner", "banners", "logo"]


def _text_for(text, bgs):
    """Ein Textton, der auf allen Hintergründen 4.5:1 schafft — als Vorschlag."""
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
    """Geschützte Namen aus der Anfrage selbst: der Titel (vor „(“ oder „:“)
    als Ganzes und Kunstwörter darin (Bindestrich, Binnenmajuskel, z. B.
    „Pip-Boy“, „StarCraft“). Gewöhnliche Wörter wie „Red“ allein bleiben
    erlaubt — nur die ganze Wendung „Red Alert 2“ ist gesperrt."""
    title = re.split(r"[(:]", request)[0].strip()
    out = [title.lower()] if len(title) >= 3 else []
    for word in title.split():
        if len(word) > 2 and ("-" in word or any(ch.isupper() for ch in word[1:])):
            out.append(word.lower())
    return out


def fixed_buttons(d):
    """Pflichtknöpfe ergänzen: I, A, X rechts, ohne Doppelte."""
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
    """Letzte Stufe: Sätze mit Fallenwörtern streichen. Ein Satz weniger
    schadet einem Bild-Prompt nicht; ein gemaltes Icon im Hintergrund schon."""
    keep = [s for s in _sentences(prompt) if s not in trap_sentences(prompt)]
    out = " ".join(keep)
    if "no text" not in out.lower():
        out = out.rstrip(". ") + ". No text, no logos, no brand names."
    return out


def validate(spec, avoid=()):
    """Liefert eine Liste verständlicher Fehlermeldungen (leer = in Ordnung)."""
    return [msg for _, msg in validate_paths(spec, avoid)]


class _Errors(list):
    """Fehlerliste, die zu jeder Meldung festhält, welcher Teil betroffen ist."""
    path = ()

    def append(self, msg):
        super().append((self.path, msg))


def validate_paths(spec, avoid=()):
    """Wie validate(), aber als (Pfad, Meldung). Pfad z. B. ("variants", 1, "colors")
    — damit lässt sich gezielt nur dieser Teil vom LLM reparieren."""
    errors = _Errors()
    request = spec.get("_meta", {}).get("request", "")
    banned = [t.lower() for t in list(TRADEMARKS) + list(avoid) + names_from_request(request)]

    def no_marks(field, text):
        low = text.lower()
        for t in banned:
            if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low):
                errors.append(f"{field} enthält den geschützten Namen „{t}“ — "
                              "beschreibe den Stil stattdessen mit eigenen Worten")

    errors.path = ()
    no_marks("name", spec["name"])
    no_marks("description", spec["description"])
    no_marks("emblem.label", spec["emblem"]["label"])

    sh = spec["shape"]
    errors.path = ("shape",)
    if sh["corner"] == "square" and sh["corner_size"] != 0:
        errors.append("shape.corner ist square, dann muss shape.corner_size 0 sein")
    if sh["corner"] != "square" and sh["corner_size"] < 2:
        errors.append(f"shape.corner ist {sh['corner']}, dann muss corner_size mindestens 2 sein")
    if sh["bevel"] == "flat" and sh["bevel_width"] != 0:
        errors.append("shape.bevel ist flat, dann muss bevel_width 0 sein")
    if sh["bevel"] == "raised" and sh["bevel_width"] == 0:
        errors.append("shape.bevel ist raised, dann muss bevel_width mindestens 1 sein")

    d = spec["decoration"]
    errors.path = ("decoration",)
    if d["button_size"] > d["title_height"] - 2:
        errors.append(f"decoration.button_size ({d['button_size']}) muss mindestens 2 kleiner "
                      f"sein als title_height ({d['title_height']})")
    used = d["buttons_left"] + d["buttons_right"]
    missing = [ch for ch in "IAX" if ch not in used]
    if missing:
        right = fixed_buttons(d)["buttons_right"]
        errors.append(f"Knöpfe fehlen: {', '.join(missing)} (I Minimieren, A Maximieren, X Schließen "
                      f"sind Pflicht) — setze buttons_right auf \"{right}\"")
    dup = {ch for ch in used if ch != "_" and used.count(ch) > 1}
    if dup:
        errors.append(f"Knöpfe doppelt: {''.join(sorted(dup))}")

    errors.path = ()
    ids = [v["id"] for v in spec["variants"]]
    if len(set(ids)) != len(ids):
        errors.append("variants: die id-Werte müssen verschieden sein")

    for i, v in enumerate(spec["variants"]):
        tag = f"Variante „{v['id']}“"
        c = v["colors"]
        errors.path = ("variants", i)
        no_marks(f"{tag}: name", v["name"])
        errors.path = ("variants", i, "wallpaper_prompt")
        no_marks(f"{tag}: wallpaper_prompt", v["wallpaper_prompt"])
        wp = v["wallpaper_prompt"].lower()
        body = wp.split("no text")[0]
        traps = sorted({w for w in re.findall(r"[a-z]+", body) if w in PROMPT_TRAPS})
        if traps:
            quoted = " / ".join(f"„{t}“" for t in trap_sentences(v["wallpaper_prompt"]))
            errors.append(f"{tag}: wallpaper_prompt enthält {', '.join(traps)} — das Bildmodell malt "
                          f"das wörtlich (Symbole, Schrift). Schreibe diese Sätze ohne diese Wörter neu: "
                          f"{quoted}. Statt Platz für Symbole: „ruhige, leere Fläche“.")
        if "no text" not in wp:
            errors.append(f"{tag}: wallpaper_prompt muss mit „no text, no logos“ enden")
        if len(wp.split()) < 25:
            errors.append(f"{tag}: wallpaper_prompt ist zu kurz — ein ganzer Absatz mit "
                          "Medium, Motiv, Licht, Farben und Bildaufbau")
        dark = v["mode"] == "dark"
        errors.path = ("variants", i, "colors")
        # Fehlermeldungen mit konkretem Ersatzwert: kleine Modelle setzen
        # „nimm #1c1c1c“ zuverlässig um, „wähle text dunkler“ oft nicht.
        luma_ok = True
        for key in ("surface", "window"):
            lum = luminance(c[key])
            if (dark and lum > 0.18) or (not dark and lum < 0.35):
                luma_ok = False
                errors.append(f"{tag}: mode ist {v['mode']}, aber colors.{key} {c[key]} ist zu "
                              f"{'hell' if dark else 'dunkel'} (Luminanz {lum:.2f}) — "
                              f"setze colors.{key} auf {_lum_fix(c[key], dark)}")
        bad = [bg for bg in ("surface", "window", "panel") if contrast(c["text"], c[bg]) < 4.5]
        if bad and luma_ok:
            fix = _text_for(c["text"], [c[b] for b in ("surface", "window", "panel")])
            worst = ", ".join(f"{b} {c[b]} {contrast(c['text'], c[b]):.1f}:1" for b in bad)
            if fix:
                errors.append(f"{tag}: colors.text {c['text']} ist nicht lesbar auf {worst} "
                              f"(nötig 4.5:1) — setze colors.text auf {fix}")
            else:
                # Kein Text passt auf alle drei Flächen. Dann einen klaren
                # Textton passend zum Modus vorschlagen und jede Fläche, die
                # damit nicht reicht, konkret nachziehen — immer lösbar.
                fix_text = "#ececec" if dark else "#161616"
                fixes = [f"colors.text auf {fix_text}"]
                for b_ in ("surface", "window", "panel"):
                    col = c[b_]
                    for _ in range(40):
                        if contrast(fix_text, col) >= 4.5:
                            break
                        col = shift(col, -0.02 if dark else 0.02)
                    if col != c[b_]:
                        fixes.append(f"colors.{b_} auf {col}")
                errors.append(f"{tag}: colors.text {c['text']} ist nicht lesbar auf {worst} "
                              f"(nötig 4.5:1) — setze " + ", ".join(fixes))
        # Die Leitfarbe, die das Modell selbst genannt hat, muss die Titelleiste
        # tragen — das sichtbarste Element jedes Fensters (wie Petrol bei NT
        # Legacy, Kupfer bei CDE). Ohne diese Regel erfüllte das Modell „lead
        # kommt vor“ mit dem Akzent allein und ließ die Titel grau.
        lead_h, lead_s = _hs(v["lead"])
        th, ts = _hs(c["title_active"])
        if lead_s >= 0.25 and (_hue_dist(th, lead_h) > 22 or ts < 0.2):
            errors.append(f"{tag}: title_active {c['title_active']} trägt die Leitfarbe lead {v['lead']} "
                          f"nicht — setze title_active auf {readable(v['lead'], on(v['lead']))}")
        k = contrast(c["accent"], on(c["accent"]))
        if k < 4.5:
            errors.append(f"{tag}: colors.accent {c['accent']} trägt weder schwarzen noch weißen "
                          f"Text lesbar ({k:.1f}:1) — setze colors.accent z. B. auf "
                          f"{readable(c['accent'], on(c['accent']))}")
        k = contrast(c["title_active"], on(c["title_active"]))
        if k < 4.5:
            errors.append(f"{tag}: colors.title_active {c['title_active']} trägt keinen lesbaren "
                          f"Titeltext ({k:.1f}:1) — setze title_active z. B. auf "
                          f"{readable(c['title_active'], on(c['title_active']))}")
        if contrast(c["accent"], c["window"]) < 1.4:
            fix = c["accent"]
            step = -0.025 if luminance(c["window"]) > 0.18 else 0.025
            for _ in range(30):
                fix = shift(fix, step)
                if contrast(fix, c["window"]) >= 1.6 and contrast(fix, on(fix)) >= 4.5:
                    break
            errors.append(f"{tag}: colors.accent hebt sich kaum von colors.window ab "
                          f"({contrast(c['accent'], c['window']):.2f}:1, nötig 1.4:1) — "
                          f"setze colors.accent auf {fix}")
        if contrast(c["title_active"], c["title_inactive"]) < 1.25 and \
                c["title_active"] == c["title_inactive"]:
            errors.append(f"{tag}: title_active und title_inactive müssen sich unterscheiden")
    return errors
