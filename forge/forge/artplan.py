"""Art plan: what gets painted — wallpapers, material, the icons' cameo motifs.

An LLM step of its own after the specification, in small requests (scenes +
material per variant, once all icon motifs), each with a schema and a check
of its own. The engine itself puts the image prompts together from the
motifs (a fixed style formula), so that the icons become one consistent set.

Private mode (--private): names of units, characters and places of the
model are allowed. The image model does not know many of them, though (test
24.10.2026: "Kirov airship" gave a grey steel ship instead of the red
zeppelin); hence the plan asks for the name AND the look.
"""
import json
import re

from . import events, iconset, llm, spec as specmod

TRAPS = {"icon", "icons", "text", "letters", "letter", "words", "logo", "logos", "label", "labels",
         "caption", "sign", "signs", "poster", "screen", "screens", "desktop", "interface", "ui",
         "monitor", "display", "document", "file", "files", "page", "pages", "symbol", "writing"}

SCENES_SYSTEM = """You plan the imagery of a desktop theme. An image model (Krea) then paints
your prompts. It paints every word literally and does NOT reliably know many names from games
and films. Write everything in English."""

SCENES_USER = """Style model: {request}
Design brief:
{brief}

Variant: {vname} ({mode}), lead colour {lead}, base tone {surface}.
{names_rule}

Deliver:
0. elements: first 4–8 iconic elements of EXACTLY THIS variant/faction in the model
   (units, characters, buildings, locations — none of the other side). name: as in the
   model; look: in English, what it looks like (shape, colours, features), 8–30 words.
   Colours as in the model — in strategy games units and buildings carry the
   faction/team colour; here that is the lead colour {lead}, not camouflage green by default.
{voted}
1. wallpapers: exactly three wallpapers for this variant; each shows at least one
   element from elements as its main subject, in an iconic scene of its own.
   prompt: English, 50–130 words, one continuous paragraph, ONLY the scene — the engine
   puts the medium and style in front itself, do not name them. For every unit or character
   describe its LOOK (shape, colours, features), not just the name. Light and colour world
   fitting the lead colour, one calm area of the picture (sky, fog, ground).
   Never: symbols, screens, signs, lettering, frames. End with "no text, no logos".
   title: a short English title for the picture.
2. texture: an English prompt for a metal surface as the material for window frames
   and panels: top view of a flat sheet in the base tone/lead colour of this
   variant, horizontal grinding marks, slight signs of wear, even light,
   without rivets, seams, objects and lettering. Colour: mainly the lead colour, dark."""

ICONS_SYSTEM = """You design a set of program icons in the style of the "cameos" of a
strategy game: each icon is a small painted picture of a motif from the imagery of the
model that still tells its function. Write everything in English."""

ICONS_USER = """Style model: {request}
Design brief (excerpt):
{brief}
{names_rule}

Iconic elements of the model (a selection, you may take others):
{elements}

For every icon write source first — the NAME of an element of the model (a unit, a
building, a character, an object of its imagery; not the icon's function) —, then
motif: English, 6–25 words, an object, a unit, a character or a building from the
model, large and clear in the picture, whose connection with the function one sees at
once (terminal → radio operator at a console, trash → scrap heap …). Rules:
- All folders (folder, folder-*, user-home, user-desktop) show THE SAME container
  as "folder"; the variants only add one clear feature.
- Every motif different; no lettering, no letters, no screens, no documents.
- File types and abstract functions as a tangible object of the imagery: e.g. a
  sealed dossier, a film reel in an ammunition box, a field telephone, a lever,
  a radio antenna, a safe — never "file", "symbol", "icon" or a screen.
- For named units/characters also give their look.

Icons:
{icons}"""


def _names_rule(private):
    if private:
        return ("Names of units, characters and places of the model are allowed (private theme) — "
                "name them, and describe in addition what they look like.")
    return ("No names of brands, units or characters of the model — describe them only "
            "in your own words by their look.")


def _words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def _banned(spec, private):
    if private:
        return []
    request = spec.get("_meta", {}).get("request", "")
    return specmod.TRADEMARKS + specmod.names_from_request(request)


def _mark_errors(field, text, banned):
    low = text.lower()
    return [f"{field} contains the protected name \"{t}\"" for t in banned
            if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low)]


SCENE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["elements", "wallpapers", "texture"],
    "properties": {
        "elements": {"type": "array", "minItems": 4, "maxItems": 8, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "look"],
            "properties": {"name": {"type": "string", "minLength": 2, "maxLength": 40},
                           "look": {"type": "string", "minLength": 30, "maxLength": 260}}}},
        "wallpapers": {"type": "array", "minItems": 3, "maxItems": 3, "items": {
            "type": "object", "additionalProperties": False, "required": ["title", "prompt"],
            "properties": {"title": {"type": "string", "minLength": 3, "maxLength": 40},
                           "prompt": {"type": "string", "minLength": 250, "maxLength": 1400}}}},
        "texture": {"type": "string", "minLength": 80, "maxLength": 600},
    },
}


def _body(p):
    """The prompt without the closing formula "no text, no logos"."""
    return re.split(r"(?i)no text", p)[0]


def _traps(text):
    """Trap words, without harmless phrases ("signs of wear", "no text")."""
    low = re.sub(r"\bsigns? of\b", "", text.lower())
    low = re.sub(r"\b(no|without)\s+\w+", "", low)
    return sorted(_words(low) & TRAPS)


def check_scenes(obj, banned, private=False, voted=(), others=()):
    errors = []
    names = [e["name"] for e in obj["elements"]]
    for e in obj["elements"]:
        if _words(e["look"]) & GERMAN or re.search(r"[äöüß]", e["look"].lower()):
            errors.append(f"elements \"{e['name']}\": look is not in English — write it in English")
    if voted:
        missing = [n for n in voted[:4] if not any(_name_in(n, e) for e in names)]
        if missing:
            errors.append(f"elements: the agreed elements {', '.join(missing)} are missing — add them")
    for i, w in enumerate(obj["wallpapers"]):
        for o in others:
            if re.search(r"\b" + re.escape(o.lower()), w["prompt"].lower()):
                errors.append(f"wallpapers[{i}].prompt names \"{o}\" — that is the other variant; "
                              "show only elements of this variant")
    for i, w in enumerate(obj["wallpapers"]):
        p = w["prompt"]
        traps = _traps(_body(p))
        if private and not any(_name_in(n, p) for n in names):
            errors.append(f"wallpapers[{i}].prompt shows none of the elements ({', '.join(names)}) — "
                          "take one of them as the main subject and describe its look")
        if traps:
            sents = [s for s in specmod._sentences(_body(p)) if _traps(s)]
            errors.append(f"wallpapers[{i}].prompt contains {', '.join(traps)} — the image model paints that "
                          f"literally. Rewrite these sentences without these words: " + " / ".join(f"\"{s}\"" for s in sents))
        if "no text" not in p.lower():
            errors.append(f"wallpapers[{i}].prompt must end with \"no text, no logos\"")
        if len(p.split()) < 40:
            errors.append(f"wallpapers[{i}].prompt is too short ({len(p.split())} words, at least 50)")
        errors += _mark_errors(f"wallpapers[{i}]", p + " " + w["title"], banned)
    t = obj["texture"].lower()
    for w in sorted(_words(t) & {"rivet", "rivets", "text", "logo", "logos", "letters", "seam", "seams"}):
        if not re.search(r"\b(no|without)\b[^.]*\b" + w, t):
            errors.append(f"texture names \"{w}\" — the surface must be empty (or write \"no {w}\")")
    return errors


def _name_in(name, text):
    """Is the element's name in the text? One distinctive word is enough ("Kirov" for "Kirov Airship")."""
    low = text.lower()
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) > 3]
    return name.lower() in low or any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words)


# Replacement words for traps — as a suggestion in the error message and as
# the last stage without the LLM. Figurative, without lettering.
REPLACE = {"text": "markings", "letters": "markings", "letter": "dispatch", "words": "markings",
           "writing": "markings", "screen": "radar scope", "screens": "radar scopes",
           "monitor": "radar scope", "display": "gauge", "document": "dossier", "file": "dossier",
           "files": "dossiers", "page": "sheet", "pages": "sheets", "icon": "emblem", "icons": "emblems",
           "logo": "emblem", "logos": "emblems", "symbol": "emblem", "label": "tag", "labels": "tags",
           "sign": "metal plate", "signs": "metal plates", "poster": "placard", "caption": "marking",
           "desktop": "tabletop", "interface": "control panel", "ui": "control panel", "screen-": "scope"}


def replace_traps(text):
    def sub(m):
        w = m.group(0)
        r = REPLACE.get(w.lower())
        return r if r else w
    return re.sub(r"[A-Za-z]+", lambda m: sub(m) if m.group(0).lower() in TRAPS and not
                  re.search(r"(?i)\b(no|without)\s+$", text[:m.start()]) else m.group(0), text)


# German function words: an answer containing them was not written in English.
GERMAN = {"der", "die", "das", "ein", "eine", "einen", "mit", "und", "auf", "im", "zum", "des", "dem"}
GENERIC = {"symbol", "icon", "stilisiert", "stylized", "generic", "abstract", "abstrakt", "file", "document"}


def icon_schema():
    item = {"type": "object", "additionalProperties": False, "required": ["source", "motif"],
            "properties": {"source": {"type": "string", "minLength": 3, "maxLength": 60},
                           "motif": {"type": "string", "minLength": 20, "maxLength": 220}}}
    return {"type": "object", "additionalProperties": False, "required": ["motifs"],
            "properties": {"motifs": {
                "type": "object", "additionalProperties": False, "required": iconset.PAINTED,
                "properties": {k: item for k in iconset.PAINTED}}}}


def check_icon(name, entry, banned):
    errors = []
    motif = entry["motif"]
    if _words(motif) & GERMAN or re.search(r"[äöüß]", motif.lower()):
        errors.append(f"{name}: motif is not in English — write it in English")
    if _words(entry["source"]) & GENERIC:
        errors.append(f"{name}: source \"{entry['source']}\" is not an element of the model — take a "
                      "unit, a building, a character or an object from the model")
    if re.search(r"(?<![A-Za-z])[\"„“'][^\"„“”']{2,}[\"“”'](?![A-Za-z])", motif):
        errors.append(f"{name}: motif contains a quotation — it gets painted as lettering; leave out the quotation marks")
    traps = _traps(motif)
    if traps:
        alt = ", ".join(f"\"{t}\" → \"{REPLACE.get(t, '?')}\"" for t in traps)
        errors.append(f"{name}: motif contains {', '.join(traps)} — the image model paints that literally; "
                      f"replace: {alt}")
    errors += _mark_errors(f"{name}", motif, banned)
    return errors


def check_icons(obj, banned):
    """{icon: [errors]} — empty when everything fits."""
    out = {}
    seen = {}
    for name, entry in obj.items():
        errs = check_icon(name, entry, banned)
        key = entry["motif"].lower().strip(" .")
        if key in seen:
            errs.append(f"{name}: motif is identical to {seen[key]} — every motif different")
        seen.setdefault(key, name)
        if errs:
            out[name] = errs
    return out


ICON_FIX = """Style model: {request}
{names_rule}
Icon "{name}" ({meaning}). So far: {entry}
Errors:
- {errors}
Return source and motif anew (motif in English, 6–25 words, a tangible object, a unit,
a building or a character from the model that tells the function)."""


def _ask(system, user, schema, check, log, what, rounds=4, seed=None):
    """A request with a check; errors go back together with the answer so far."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text, info = llm.chat(msgs, schema=schema, max_tokens=8000, temperature=0.6, seed=seed)
    log(f"{what}: {info['tokens']} tokens in {info['seconds']} s")
    obj = json.loads(text)
    for r in range(rounds):
        errs = check(obj)
        if not errs:
            return obj, r + 1
        for e in errs:
            log(f"  error: {e}")
        text, info = llm.chat(msgs + [{"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)},
                                      {"role": "user", "content": "Fix exactly these errors and return "
                                       "everything in full:\n- " + "\n- ".join(errs)}],
                              schema=schema, max_tokens=8000, temperature=0.3, seed=seed)
        obj = json.loads(text)
    errs = check(obj)
    if errs:
        raise llm.LLMError(f"{what}: still errors after {rounds} rounds: {errs}")
    return obj, rounds + 1


VOTE_Q = ("Style source: {request}\nFaction/variant: {variant}\nList up to 8 of the most iconic units, "
          "structures and hero characters that belong ONLY to this faction, with their exact names in the "
          "source. Answer with one comma-separated line of names, nothing else.")


def _norm(name):
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in ("the", "a", "an")]
    return " ".join(words)


def vote_elements(request, variant, samples=6, log=print):
    """Iconic elements by majority vote, in thinking mode.

    Without thinking mode the model invented names and mixed up the factions
    (Tanya with the Soviets, "MiG2…MiG8"); with it the right ones come, but
    every answer with one or two outliers — those drop out in the majority.
    Forms of a name are grouped ("Kirov" ⊂ "Kirov Airship")."""
    answers = []
    for i in range(samples):
        try:
            text, _ = llm.chat([{"role": "user", "content": VOTE_Q.format(request=request, variant=variant)}],
                               temperature=0.6, max_tokens=16000, seed=9000 + i, think=True)
        except llm.LLMError:
            continue
        names = [n.strip(" .*-") for n in text.strip().splitlines()[-1].split(",")]
        answers.append({_norm(n): n for n in names if 2 <= len(n) <= 40 and _norm(n)})
    groups = []          # [{keys}, votes, {spelling: count}]
    for ans in answers:
        hit_groups = set()
        for key, shown in ans.items():
            for gi, g in enumerate(groups):
                if any(key == k or f" {key} " in f" {k} " or f" {k} " in f" {key} " for k in g[0]):
                    if gi not in hit_groups:
                        g[1] += 1
                        hit_groups.add(gi)
                    g[0].add(key)
                    g[2][shown] = g[2].get(shown, 0) + 1
                    break
            else:
                groups.append([{key}, 1, {shown: 1}])
                hit_groups.add(len(groups) - 1)
    need = max(2, (len(answers) + 1) // 2)
    picked = sorted((g for g in groups if g[1] >= need), key=lambda g: -g[1])[:8]
    names = [max(g[2], key=lambda n: (g[2][n], len(n))) for g in picked]
    log(f"elements {variant}: " + (", ".join(f"{n} ({g[1]}/{len(answers)})" for n, g in zip(names, picked))
                                   or "no agreement"))
    return names


STYLE_SYSTEM = """You design the picture style of an icon set for a desktop theme. An image model
then paints every icon; what it shows is fixed — you decide only HOW it looks. Write everything
in English."""

STYLE_USER = """Style model: {request}
Design brief (excerpt):
{brief}
{names_rule}
Colours of the theme: {colors}

Write a style sheet, in ENGLISH, one short sentence per field, so that all icons look like a set
from the model (for a game: like its own pictures — build menu, loading screen, box —, NOT like
modern app icons). First consider how the model's pictures are really painted/rendered, and
describe exactly that.
- medium: the model's way of painting and kind of picture.
- palette: 3–5 colours in words (no hex codes). The pictures serve ALL variants, hence
  neutral, muted base tones of the imagery (metal, earth, light) — a variant's colour comes
  later through the frame; do not mix the lead colours of several variants.
- materials: surfaces and materials the objects carry.
- elements: 2–4 recurring design details (e.g. rivets, edges, glowing parts).
- lighting: light and shadow.
- background: what lies behind each object — plain, dark, soft, of one colour
  (no blocks of colour, no tiles), so the object stands free.
No frames, borders, tiles, buttons or drop shadows — the engine itself puts the frame
round every picture.
- folder: what ALL folders look like — a container of the imagery (e.g. an ammunition box,
  a file cassette, a wooden chest) with a smooth, empty front.
- sheet: what ALL files look like — a sheet/card/tablet of the imagery with a
  folded corner and a smooth, empty surface.
Each field describes only what one SEES (shape, material, colour, light) — no sentences about
purpose, effect or what gets added later. Never: lettering, letters, numbers, logos,
emblems, stencilled lettering, screens with content, people."""

STYLE_FIX = """Icon style sheet for the style model: {request}
Field "{field}": {what}
So far: {value}
Errors:
- {errors}
Return only this field anew: in English, one sentence, only what one sees (shape, material,
colour, light) — no sentences about purpose or what gets added later."""

STYLE_WHAT = {"medium": "way of painting and kind of picture", "palette": "3–5 colours in words",
              "materials": "surfaces and materials", "elements": "2–4 recurring design details",
              "lighting": "light and shadow", "background": "what lies behind each object",
              "folder": "what all folders look like: a container with a smooth, empty front",
              "sheet": "what all files look like: a sheet/card with a folded corner and an empty surface"}

STYLE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["medium", "palette", "materials", "elements", "lighting", "background", "folder", "sheet"],
    "properties": {k: {"type": "string", "minLength": 10, "maxLength": 220}
                   for k in ("medium", "palette", "materials", "elements", "lighting", "background", "folder",
                             "sheet")}}

STYLE_TRAPS = TRAPS | {"stencil", "stencilled", "stenciled", "lettering", "numbers", "number", "digits",
                       "people", "soldier", "soldiers", "face", "faces", "person", "portrait", "portraits",
                       "character", "characters", "labeling", "labelling", "labelled", "labeled"}


TILE_WORDS = {"border", "borders", "frame", "frames", "framed", "tile", "tiles", "tiled", "button", "buttons",
              "app", "badge", "badges", "outline", "outlines", "outlined"}


# Objects in the style end up in EVERY icon: "Low-polygon models of the Grizzly
# tank …" under medium gave 108 tank icons (run of 24.10.2026).
SUBJECTS = {"tank", "tanks", "aircraft", "airship", "airships", "airplane", "jet", "jets", "ship", "ships",
            "submarine", "helicopter", "generator", "generators", "silo", "silos", "soldier", "soldiers", "unit",
            "units", "vehicle", "vehicles", "robot", "robots", "car", "cars", "truck", "trucks", "building",
            "buildings", "tower", "towers", "weapon", "weapons", "gun", "guns", "cannon", "missile", "missiles",
            "reactor", "coil"}


def check_style(obj, banned, subjects=()):
    obj = {k: v for k, v in obj.items() if k in STYLE_SCHEMA["properties"]}
    errors = []
    for k in ("medium", "palette", "materials", "elements", "lighting", "background"):
        named = sorted({n for n in subjects if _name_in(n, obj[k])} | (_words(obj[k]) & SUBJECTS))
        if named:
            errors.append(f"{k} names objects ({', '.join(named)}) — the image model paints them into EVERY icon; "
                          "describe only the way of painting, colour, surface, light, without objects")
    if re.search(r"#[0-9a-fA-F]{3,6}\b", obj["palette"]):
        errors.append("palette contains hex codes — name the colours in words")
    for k in ("medium", "elements", "background", "materials", "lighting"):
        low = re.sub(r"\b(no|without|never)\s+(any\s+|a\s+|an\s+)?[\w-]+(\s*(,|or|and)\s*[\w-]+)*", "",
                     obj[k].lower())
        hit = sorted(_words(low) & TILE_WORDS) + (["drop shadow"] if "drop shadow" in low else [])
        if hit:
            errors.append(f"{k} names {', '.join(hit)} — that gives app tiles; the engine sets the frame, "
                          "describe only the object itself")
    for k in ("folder", "sheet"):
        hit = sorted(_words(obj[k]) & {"emblem", "emblems", "stamp", "stamped", "insignia", "badge", "seal",
                                       "star", "marking", "markings", "tag", "tags"})
        if hit:
            errors.append(f"{k} names {', '.join(hit)} — folder/sheet stay without a sign of their own, the engine "
                          "puts one on per icon; describe only shape and material")
    for k, v in obj.items():
        if _words(v) & GERMAN or re.search(r"[äöüß]", v.lower()):
            errors.append(f"{k} is not in English — write it in English")
        if re.search(r"(?i)\b(motor|engine|the system|added later|ready for|left blank for|placeholder)\b", v):
            errors.append(f"{k} talks about the process (\"ready for …\", \"engine\") — describe only what one sees")
        low = re.sub(r"\b(no|without|never)\s+(any\s+|a\s+|an\s+)?[\w-]+(\s*(,|or|and)\s*[\w-]+)*", "", v.lower())
        low = re.sub(r"\bsigns? of\b", "", low)
        bad = sorted(_words(low) & STYLE_TRAPS)
        if bad:
            errors.append(f"{k} names {', '.join(bad)} — the image model paints that on every icon; leave these "
                          "words out without replacement")
        errors += _mark_errors(k, v, banned)
    return errors


def style_sheet(spec, private=False, log=print, seed=None, subjects=(), feedback=""):
    meta = spec.get("_meta", {})
    colors = "; ".join(f"{v['name']}: lead colour {v['lead']}, surface {v['colors']['surface']}" for v in spec["variants"])
    user = STYLE_USER.format(request=meta.get("request", ""), brief=meta.get("brief", "")[:1500],
                             names_rule=_names_rule(private), colors=colors)
    if feedback:
        user += "\n\n" + feedback
    banned = _banned(spec, private)
    msgs = [{"role": "system", "content": STYLE_SYSTEM}, {"role": "user", "content": user}]
    # Thinking mode: one request decides the look of all icons — without it
    # Red Alert 2 got "glossy 3D, thick borders", i.e. app icons (test 24.10.2026).
    text, info = llm.chat(msgs, schema=STYLE_SCHEMA, max_tokens=12000, temperature=0.6, seed=seed, think=True)
    log(f"icon style sheet: {info['tokens']} tokens in {info['seconds']} s")
    obj = json.loads(text)
    part = {"type": "object", "additionalProperties": False, "required": ["value"],
            "properties": {"value": {"type": "string", "minLength": 10, "maxLength": 220}}}
    # Partial repair per field — the model returned the whole sheet unchanged four times.
    for r in range(1, 5):
        errs = check_style(obj, banned, subjects)
        if not errs:
            return obj, r
        for k in obj:
            mine = [e for e in errs if e.startswith(k + " ")]
            if not mine:
                continue
            log(f"  style sheet {k}: \"{obj[k][:110]}\" — {'; '.join(mine)[:120]}")
            fix = STYLE_FIX.format(request=meta.get("request", ""), field=k, what=STYLE_WHAT[k], value=obj[k],
                                   errors="\n- ".join(mine))
            t, _ = llm.chat([{"role": "user", "content": fix}], schema=part, max_tokens=400, temperature=0.4,
                            seed=(seed or 0) + r)
            obj[k] = json.loads(t)["value"]
    # Last stage without the LLM: strike clauses with trap words.
    def bad_field(k, text):
        return any(e.startswith(k + " ") for e in check_style(dict(obj, **{k: text}), banned, subjects))
    for k in [k for k in STYLE_SCHEMA["properties"] if bad_field(k, obj[k])]:
        parts = re.split(r"(,\s+|\s+and\s+|;\s+|\.\s+)", obj[k])
        keep = [p for p in parts[::2] if p.strip() and not bad_field(k, p)]
        if keep:
            log(f"  auto: style sheet {k} shortened")
            obj[k] = ", ".join(x.strip(" .") for x in keep) + "."
            obj.setdefault("_auto", []).append(k)
    errs = check_style({k: v for k, v in obj.items() if k != "_auto"}, banned, subjects)
    if errs:
        raise llm.LLMError(f"icon style sheet: still errors: {errs}")
    return obj, 5


def compose(name, pic, style):
    """Motif from sign + family: folders and files share the basic shape."""
    fam = iconset.FAMILY[name]
    if fam == "folder":
        return style["folder"].rstrip(". ") + (f", with {pic} mounted large on its front" if pic else "")
    if fam == "document":
        return style["sheet"].rstrip(". ") + f", with {pic} painted large in its centre"
    return pic


def catalog_motifs(style):
    return {name: {"source": "catalog", "picture": iconset.PICTURE[name],
                   "motif": compose(name, iconset.PICTURE[name], style)} for name in iconset.PAINTED}


def icon_prompt(motif, style):
    """The prompt for a catalogue icon: motif + style sheet, in a fixed order."""
    nobody = "" if wants_person(motif) else "A single object only, no people, no faces, no hands. "
    return (f"{style['medium'].rstrip('. ')}, square icon picture, the subject fills the frame edge to edge: "
            f"{motif}. {nobody}Colours: {style['palette'].rstrip('. ')}. Materials: "
            f"{style['materials'].rstrip('. ')}. Details: {style['elements'].rstrip('. ')}. "
            f"{style['lighting'].rstrip('. ')}. Background: {style['background'].rstrip('. ')}. "
            "No frame, no border, no text, no letters, no numbers, no logos.")


def plan(spec, private=False, log=print, seed=None, themed_icons=False):
    events.begin("art-plan", private=private, themed_icons=themed_icons)
    result = _plan_themed(spec, private, log, seed) if themed_icons else _plan_catalog(spec, private, log, seed)
    events.end("art-plan", rounds=result["rounds"], style=result.get("style"),
               scenes={k: {"elements": [e["name"] for e in v["elements"]],
                           "wallpapers": [w["title"] for w in v["wallpapers"]]}
                       for k, v in result["variants"].items()})
    return result


def scene_subjects(result):
    """The names of all variants' elements — barred from the style sheet."""
    return sorted({e["name"] for v in result["variants"].values() for e in v["elements"]})


def _plan_catalog(spec, private, log, seed):
    """The default: scenes per variant as before, icons from catalogue + style sheet."""
    result = _scenes(spec, private, log, seed)
    style, r = style_sheet(spec, private, log, seed, subjects=scene_subjects(result))
    result["style"] = style
    result["icons"] = catalog_motifs(style)
    result["rounds"]["style"] = r
    return result


def _scenes(spec, private, log, seed):
    meta = spec.get("_meta", {})
    request, brief = meta.get("request", ""), meta.get("brief", "")
    banned = _banned(spec, private)
    rule = _names_rule(private)
    result = {"private": private, "variants": {}, "icons": None, "rounds": {}}
    others_all = {v["id"]: [o["id"] for o in spec["variants"] if o["id"] != v["id"]] for v in spec["variants"]}
    for v in spec["variants"]:
        anchor = next((a["name"] for a in meta.get("anchors", []) if a.get("lead") == v["lead"]), v["id"])
        voted = vote_elements(request, anchor, log=log) if private else []
        vtext = ("   Agreed elements (from several questions, take these): " + ", ".join(voted)
                 if voted else "")
        user = SCENES_USER.format(request=request, brief=brief, vname=v["name"], mode=v["mode"],
                                  lead=v["lead"], surface=v["colors"]["surface"], names_rule=rule, voted=vtext)
        others = others_all[v["id"]]
        obj, r = _ask(SCENES_SYSTEM, user, SCENE_SCHEMA,
                      lambda o, voted=voted, others=others: check_scenes(o, banned, private, voted, others),
                      log, f"scenes {v['id']}", seed=seed)
        result["variants"][v["id"]] = obj
        result["rounds"][f"scenes-{v['id']}"] = r
    return result


def _plan_themed(spec, private, log, seed):
    """The alternative (--themed-icons): the LLM invents a motif per icon from the model's imagery."""
    meta = spec.get("_meta", {})
    request, brief = meta.get("request", ""), meta.get("brief", "")
    banned = _banned(spec, private)
    rule = _names_rule(private)
    result = _scenes(spec, private, log, seed)
    elements = "\n".join(f"- {e['name']}: {e['look']}" for v in result["variants"].values()
                          for e in v["elements"])
    user = ICONS_USER.format(request=request, brief=brief[:1500], names_rule=rule, icons=iconset.describe(),
                             elements=elements)
    msgs = [{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": user}]
    text, info = llm.chat(msgs, schema=icon_schema(), max_tokens=10000, temperature=0.6, seed=seed)
    log(f"icon motifs: {info['tokens']} tokens in {info['seconds']} s")
    motifs = json.loads(text)["motifs"]
    # One small request per faulty icon — 35 errors in an object of 70 at
    # once the model never fixed (test 24.10.2026).
    item = icon_schema()["properties"]["motifs"]["properties"][iconset.PAINTED[0]]
    rounds = 0
    for rounds in range(1, 5):
        bad = check_icons(motifs, banned)
        if not bad:
            break
        log(f"  round {rounds}: {len(bad)} icon(s) to repair")
        for name, errs in bad.items():
            fix = ICON_FIX.format(request=request, names_rule=rule, name=name,
                                  meaning=iconset.ICONS[name][1],
                                  entry=json.dumps(motifs[name], ensure_ascii=False),
                                  errors="\n- ".join(errs))
            t, _ = llm.chat([{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": fix}],
                            schema=item, max_tokens=400, temperature=0.4, seed=(seed or 0) + rounds)
            motifs[name] = json.loads(t)
    bad = check_icons(motifs, banned)
    auto = []
    for name in list(bad):
        fixed = dict(motifs[name], motif=replace_traps(motifs[name]["motif"]))
        if not check_icon(name, fixed, banned):
            motifs[name] = fixed
            auto.append(name)
    if auto:
        log(f"  auto: trap words replaced in {', '.join(auto)}")
        result["auto"] = auto
    bad = check_icons(motifs, banned)
    if bad:
        raise llm.LLMError(f"icon motifs: still errors: {bad}")
    result["icons"] = motifs
    result["rounds"]["icons"] = rounds
    return result


CATALOG_FIX = """Icon "{name}" for the function: {meaning}.
So far it was meant to show: {entry}
The image model made something unusable of it:
- {errors}
Choose a DIFFERENT, everyday, figurative picture for this function that everyone recognises
at once and that an image model can paint unambiguously: a single object, in English,
3–12 words, without lettering and without people. No reference to the style model needed —
the engine sets the style. source: "catalog"."""


def repair_icon(name, entry, errors, spec, private, seed=None, log=print, catalog=False):
    """Have a motif rewritten — after an image check that showed what the image
    model made of it. The new answer must pass check_icon."""
    request = spec.get("_meta", {}).get("request", "")
    banned = _banned(spec, private)
    item = icon_schema()["properties"]["motifs"]["properties"][iconset.PAINTED[0]]
    errs = list(errors)
    for i in range(3):
        if catalog:
            msgs = [{"role": "user", "content": CATALOG_FIX.format(name=name, meaning=iconset.ICONS[name][1],
                                                                  entry=entry["motif"], errors="\n- ".join(errs))}]
        else:
            msgs = [{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": ICON_FIX.format(
                request=request, names_rule=_names_rule(private), name=name, meaning=iconset.ICONS[name][1],
                entry=json.dumps(entry, ensure_ascii=False), errors="\n- ".join(errs))}]
        t, _ = llm.chat(msgs, schema=item, max_tokens=400, temperature=0.5, seed=(seed or 0) + i)
        new = json.loads(t)
        left = check_icon(name, new, banned)
        if catalog and re.search(r"(?i)\b(background|backdrop|transparent)\b", new["motif"]):
            left.append(f"{name}: motif names a background — only the object, the style sheet sets the background")
        if new["motif"].strip().lower() == entry["motif"].strip().lower():
            left.append(f"{name}: motif unchanged — it must be a different motif")
        if not left:
            log(f"  {name}: {entry['motif'][:50]}… → {new['motif'][:70]}")
            return new
        entry, errs = new, left
    fixed = dict(entry, motif=replace_traps(entry["motif"]))
    return fixed if not check_icon(name, fixed, banned) else None


# Words by which the engine recognises that a motif is meant to show a person.
PEOPLE = {"officer", "soldier", "soldiers", "commander", "man", "woman", "engineer", "conscript", "conscripts",
          "portrait", "face", "pilot", "general", "agent", "spy", "scientist", "operator", "figure", "trooper",
          "troopers", "girl", "boy", "person", "crew", "sniper", "commando", "technician", "radioman", "operative",
          "worker", "mechanic", "guard", "medic", "g", "gi", "hero", "heroine", "infantry", "infantryman"}


def wants_person(motif):
    return bool(_words(motif) & PEOPLE)


def strip_purpose(motif):
    """"…, representing the reboot function" describes the function, not the picture."""
    return re.split(r"(?i)(,?\s+(representing|symbolizing|symbolising|to represent)|,\s+for)\b", motif)[0].strip(" .")


def cameo_prompt(motif, request, private):
    """A fixed style formula for all icons — that makes the set consistent.
    It cuts off explanations ("…, representing PDF documents"): they describe
    the function, not the picture. "Portrait" used to be in the formula;
    Z-Image then painted a face even onto the map table and the switch panel
    (24 of 69, test 24.10.2026) — without a person in the motif it now says
    explicitly: no people."""
    motif = strip_purpose(motif)
    style = re.split(r"[(:]", request)[0].strip() if private else "a late-1990s real-time strategy game"
    nobody = "" if wants_person(motif) else "A single object only, no people, no faces, no hands. "
    return ("Extreme close-up painted game cameo artwork, the subject fills the entire square image edge to "
            f"edge with no empty margin: {motif}. {nobody}Painted in the style of {style} build-menu cameo "
            "pictures: rich saturated colours, dramatic rim lighting, crisp silhouette, slightly grainy painted "
            "texture. No frame, no border, no text, no letters, no logos.")


def wallpaper_prompt(scene, request, private):
    """The style formula in front, the closing formula behind — the set stays
    consistent even when the LLM writes "military photography" in a scene."""
    scene = re.sub(r"(?i)^\s*(a\s+)?digital painting( in the style of [^,.:]*)?[,.:]?\s*", "", scene)
    scene = _body(scene).strip(" ,.")
    style = (re.split(r"[(:]", request)[0].strip() + " loading screens and box art") if private \
        else "late-1990s real-time strategy game loading screens"
    return f"Digital painting in the style of {style}, painterly, dramatic lighting: {scene}. No text, no logos."
