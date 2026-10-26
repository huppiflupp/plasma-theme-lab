"""The LLM part: style analysis (free) → specification (bound by grammar)."""
import json

from . import events, fonts, llm, spec

BRIEF_SYSTEM = """You are an art director for desktop themes (KDE Plasma).
You describe the visual language of a model so that a theme can be made
from it. Concrete and brief, no introduction. Write in English."""

BRIEF_USER = """Style model: {request}

Describe in at most 250 words:
1. The colour world with hex values; if the model has factions/variants, per variant.
   Begin each variant with "Lead colour: #……" — the one colour by which one recognises
   it at once (not a warning or effect colour). Then base tone and accents.
   State whether the variants are rather dark or light.
2. Materials and surfaces (e.g. brushed metal, paper, glass).
3. Shapes: corners (square, chamfered, round), edges, frame thickness, 3D effect.
4. Typography (its character, not a brand name).
5. Motifs and imagery for wallpapers (scenes, light, mood).
6. A simple symbol/emblem that fits the style.
Keep close to the model: its real colours, its factions, its imagery.
You may name the model's names here (the brief is internal); the finished theme
is built later without brand names."""

SPEC_SYSTEM = """You turn a design brief into a theme specification (JSON).
The generators build colour scheme, Plasma style, window decoration,
wallpapers, Plymouth and GRUB theme from it. You write only the JSON, in English.

Fields:
- id: short, lower case, with hyphens (e.g. "iron-front"). name: display name, your own
  invention, NOT a brand name of the model. description: one short English sentence (at most 140 characters).
- shape.corner: square | chamfer (bevelled corner, technical/military) | round.
  shape.corner_size: 0 for square, else 2–8 px. shape.bevel: flat | raised (3D edge).
  shape.bevel_width: 0 for flat, else 1–3. shape.outer_border: dark outer line 0–2 px.
  shape.edge_glow: true = a thin glowing line in the glow colour inside frames.
- decoration: window frame. title_height 18–40, border 1–8, button_size at least
  2 smaller than title_height, button_shape square|round|chamfer|diamond,
  title_align left|center|right. Buttons as letters: M menu, S on all desktops,
  H help, F keep above, B keep below, L shade, I minimize,
  A maximize, X close, _ spacer. I, A and X must be present, no button twice.
- font: the font for titles, splash screen and GRUB. Choice:
{fonts}
- emblem.shape: one of {emblems}. emblem.render: blender (3D metal, sculpted)
  or inkscape (flat, graphic). emblem.label: a short word for the splash screen
  (your own invention, no brand name).
- boot.plymouth: emblem-bar (emblem + progress bar) | emblem-pulse (pulsing
  emblem) | text-bar (name + bar). boot.grub: centered | left-panel.
- variants: 1–3 colour variants (e.g. factions of the model). Per variant:
  id (lower case, no hyphen), name, look, lead, mode (dark|light), colors, wallpaper_prompt.
  look: one sentence on which colours of the model this variant carries (lead colour, base tone,
  material) — write it first and then choose the colours exactly so.
  lead: the variant's lead colour as hex — take the "Lead colour" from the brief
  (not an accent or warning colour); title_active carries exactly this lead colour.
  The lead colour belongs in title_active (and may also go in accent); surface, window and panel are a fitting base tone
  (dark metal, paper, …), not just any neutral.
  colors (hex, lower case):
{colors}
  Rules: text must have a contrast of at least 4.5:1 on surface, window AND panel.
  mode dark means: surface and window dark (luminance ≤ 0.18), text light.
  mode light means: surface and window light, text dark.
  accent is strong, so that white or black text on it is legible.
  wallpaper_prompt: English, one continuous paragraph (40–120 words) for an
  image model: first the medium ("Digital painting …"), then a motif from the model's
  imagery, light, a colour world fitting colors, a composition with a calm, empty
  area (sky, ground, fog). The image model paints every word literally: name no
  symbols, icons, screens, interfaces, signs, posters, maps, lettering.
  No brand or character names. Always end with "no text, no logos, no brand names"."""


ANCHOR_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["variants"],
    "properties": {"variants": {"type": "array", "minItems": 1, "maxItems": 3, "items": {
        "type": "object", "additionalProperties": False, "required": ["name", "lead"],
        "properties": {"name": {"type": "string", "maxLength": 30}, "lead": spec.HEX}}}}}
ANCHOR_Q = ("Style model: {request}\nWhich variants or factions does the model have? For each, give "
            "its characteristic identifying colour — the vivid colour one connects with it at once "
            "(faction colour, glow colour, brand colour), not the black, white or grey "
            "background. Only if the model really is colourless, give a grey.")


def anchors(request, samples=7, log=print):
    """Lead colours by majority vote.

    Single answers of the model scatter (for "Red Alert 2" the Soviets came
    out red, but also black, grey, blue or — in the long brief — olive). The
    majority is almost always right. Hence: several short questions, the hues
    bundled per variant, the largest bundle wins."""
    import colorsys
    import re
    from .palette import rgb
    votes = {}
    for i in range(samples):
        try:
            text, _ = llm.chat([{"role": "user", "content": ANCHOR_Q.format(request=request)}],
                               schema=ANCHOR_SCHEMA, temperature=0.8, max_tokens=300, seed=7000 + i)
        except llm.LLMError:
            continue
        for v in json.loads(text)["variants"]:
            key = re.sub(r"[^a-zäöüß]", "", v["name"].lower())[:5]
            if key:
                votes.setdefault(key, {"names": [], "leads": []})
                votes[key]["names"].append(v["name"])
                votes[key]["leads"].append(v["lead"])
    result = []
    for key, d in votes.items():
        if len(d["names"]) < (samples + 1) // 2:
            continue                    # a minority variant (e.g. an expansion)
        cols = []
        for c in d["leads"]:
            h, l, sat = colorsys.rgb_to_hls(*(x / 255 for x in rgb(c)))
            if sat >= 0.25 and 0.08 <= l <= 0.85:
                cols.append((h * 360, l, c))
        if not cols:
            continue

        def near(a, b):
            dd = abs(a - b) % 360
            return min(dd, 360 - dd) <= 25
        best = max(cols, key=lambda x: sum(near(x[0], y[0]) for y in cols))
        cluster = sorted((y for y in cols if near(best[0], y[0])), key=lambda y: y[1])
        if len(cluster) < max(2, round(samples * 0.4)):
            continue                    # too little agreement: the brief decides
        name = max(set(d["names"]), key=d["names"].count)
        result.append({"name": name, "lead": cluster[len(cluster) // 2][2],
                       "support": f"{len(cluster)}/{samples}"})
    log("lead colours: " + (", ".join(f"{a['name']} {a['lead']} ({a['support']})" for a in result) or "no agreement"))
    return result


def brief(request, log=print, lead_colors=()):
    user = BRIEF_USER.format(request=request)
    if lead_colors:
        user += ("\n\nAgreed lead colours (from several questions, binding): " +
                 ", ".join(f"{a['name']}: {a['lead']}" for a in lead_colors) +
                 ". Take them as the variants' lead colours.")
    text, info = llm.chat([{"role": "system", "content": BRIEF_SYSTEM},
                           {"role": "user", "content": user}],
                          think=True, max_tokens=8000, temperature=0.3)
    log(f"brief: {info['tokens']} tokens in {info['seconds']} s")
    return text.strip()


def _sub_schema(path):
    node = spec.SCHEMA
    for key in path:
        node = node["items"] if isinstance(key, int) else node["properties"][key]
    return node


def _get(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def _set(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def repair_part(system, request, design_brief, current, path, errors, log=print, seed=None):
    """Have only the faulty part made again.

    When a small model has to repeat the whole specification to replace one
    word, it often carries the error along. With a partial schema and only
    this excerpt the task is small enough."""
    name = ".".join(str(k) for k in path)
    part = _get(current, path)
    user = (f"Style model: {request}\n\nDesign brief:\n{design_brief}\n\n"
            f"Current specification:\n{json.dumps(current, ensure_ascii=False)}\n\n"
            f"The part \"{name}\" is faulty:\n- " + "\n- ".join(errors) +
            f"\n\nReturn only this part, corrected, as {{\"value\": …}}. "
            "Take suggested values exactly. Otherwise change as little as possible.\n"
            f"So far: {json.dumps(part, ensure_ascii=False)}")
    schema = {"type": "object", "additionalProperties": False, "required": ["value"],
              "properties": {"value": _sub_schema(path)}}
    text, info = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                          schema=schema, max_tokens=3000, temperature=0.3, seed=seed)
    log(f"  repair {name}: {info['tokens']} tokens in {info['seconds']} s")
    return json.loads(text)["value"]


def design(request, design_brief, avoid=(), log=print, retries=4, seed=None):
    system = SPEC_SYSTEM.format(
        fonts=fonts.describe(),
        emblems=", ".join(spec.EMBLEMS),
        colors="\n".join(f"    {k}: {v}" for k, v in spec.COLOR_KEYS.items()))
    user = (f"Style model: {request}\n\nDesign brief:\n{design_brief}\n\n"
            "Create the specification.")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text, info = llm.chat(messages, schema=spec.SCHEMA, max_tokens=6000, temperature=0.5, seed=seed)
    log(f"specification: {info['tokens']} tokens in {info['seconds']} s")
    current = json.loads(text)
    current["_meta"] = {"request": request}
    rounds = 0
    for rounds in range(1, retries + 1):
        errs = spec.validate_paths(current, avoid)
        if not errs:
            return current, rounds
        groups = {}
        for path, msg in errs:
            groups.setdefault(path, []).append(msg)
            log(f"  error: {msg}")
        for path, msgs in groups.items():
            if path == ():
                # Cross references (e.g. duplicate ids): the whole specification
                current, _ = llm.chat_json(
                    messages + [{"role": "assistant", "content": json.dumps(current, ensure_ascii=False)},
                                {"role": "user", "content": "Errors:\n- " + "\n- ".join(msgs) +
                                 "\nReturn the complete, corrected specification."}],
                    spec.SCHEMA, retries=0, max_tokens=6000, temperature=0.3, seed=seed)
                current["_meta"] = {"request": request}
            else:
                _set(current, path, repair_part(system, request, design_brief, current, path, msgs,
                                                log=log, seed=seed))
    # Last stage without the LLM, only for trap words in the image prompt.
    auto = []
    for i, v in enumerate(current["variants"]):
        if spec.trap_sentences(v["wallpaper_prompt"]):
            v["wallpaper_prompt"] = spec.strip_traps(v["wallpaper_prompt"])
            auto.append(f"variants.{i}.wallpaper_prompt: sentences with trap words struck")
    d = current["decoration"]
    used = d["buttons_left"] + d["buttons_right"]
    if any(ch not in used for ch in "IAX") or any(used.count(ch) > 1 for ch in used if ch != "_"):
        d.update(spec.fixed_buttons(d))
        auto.append("decoration: required buttons I, A, X added")
    if auto:
        log("  auto: " + "; ".join(auto))
        current.setdefault("_auto", []).extend(auto)
    errs = spec.validate(current, avoid)
    if errs:
        raise llm.LLMError(f"still errors after {retries} repair rounds: {errs}")
    return current, rounds + 1


def run(request, avoid=(), log=print, seed=None):
    events.begin("design", request=request)
    leads = anchors(request, log=log)
    events.emit("design", "lead-colours", anchors=leads)
    b = brief(request, log=log, lead_colors=leads)
    events.emit("design", "brief", brief=b)
    s, attempts = design(request, b, avoid=avoid, log=log, seed=seed)
    s["_meta"].update({"anchors": leads, "brief": b, "attempts": attempts})
    events.end("design", attempts=attempts, auto=s.get("_auto"), name=s["name"], description=s["description"],
               shape=s["shape"], decoration=s["decoration"], font=s["font"], emblem=s["emblem"],
               variants=[{"id": v["id"], "name": v["name"], "lead": v["lead"], "mode": v["mode"], "look": v["look"]}
                         for v in s["variants"]])
    return s
