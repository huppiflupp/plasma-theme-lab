"""Visual review by the LLM: does the built theme look right?

The icon check (imgcheck.py) looks at single painted icons. This looks at
what the user sees of the whole theme, with a vision model (llm.VISION,
FORGE_VISION; by default the same server, Qwen3.6 with its mmproj):

1. the window decoration, rendered as KWin draws it (preview.window, active
   above inactive, on the desktop colour);
2. each wallpaper;
3. the whole desktop in a lab VM after `install.sh --apply` (the vmtest
   screenshot): legibility, contrast of icons and labels to the wallpaper,
   whether frame and colours fit the style, obvious rendering faults
   (garbled glyphs, Breeze left over).

Every answer is bound to REVIEW_SCHEMA: ok, a score, and concrete issues,
each with a target. Major issues are repaired where the engine can: colours
and frame through the specification's partial repair (designer.repair_part),
a wallpaper through a rewritten prompt; then the package is built again and
looked at anew, up to `rounds` times. Issues without a repair path (icons,
rendering faults in the installer) are reported, not hidden.
"""
import base64
import io
import json
import os

from PIL import Image

from . import designer, events, llm, spec as specmod

TARGETS = {
    "decoration": ["title_colours", "title_text", "frame", "buttons", "other"],
    "wallpaper": ["picture", "other"],
    "desktop": ["wallpaper", "panel", "text_contrast", "icons", "decoration", "rendering", "other"],
}


def schema(kind):
    return {"type": "object", "additionalProperties": False, "required": ["ok", "score", "summary", "issues"],
            "properties": {
                "ok": {"type": "boolean"},
                "score": {"type": "integer", "minimum": 1, "maximum": 10},
                "summary": {"type": "string", "maxLength": 300},
                "issues": {"type": "array", "maxItems": 6, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["what", "severity", "target", "fix"],
                    "properties": {"what": {"type": "string", "maxLength": 220},
                                   "severity": {"enum": ["minor", "major"]},
                                   "target": {"enum": TARGETS[kind]},
                                   "fix": {"type": "string", "maxLength": 220}}}}}}


CONTEXT = """Style model: {request}
Theme: {name} — {description}
Variant: {variant} ({mode}), lead colour {lead}; its look: {look}"""

QUESTIONS = {
    "decoration": """These are two window title bars with a strip of frame of a desktop theme, shown twice
enlarged as the window manager draws them: above the ACTIVE window, below an INACTIVE one, on the
desktop colour. The inactive one is meant to be quieter, but its title must stay legible.
Judge as a demanding UI designer:
- Is the title text legible on both (contrast)? Do active and inactive differ clearly?
- Do the colours and the frame fit the style model and the variant's look and lead colour?
- Are the buttons (menu left; minimize, maximize, close right) recognisable and tidy?
- Anything broken: cut-off shapes, misaligned parts, stray lines, artefacts?
ok: true only if there is no major issue. Each issue: what is wrong, severity, target
(title_colours, title_text, frame, buttons, other) and a concrete fix (e.g. "make the
inactive title bar clearly darker than the active one").""",
    "wallpaper": """This is a desktop wallpaper of the theme. Judge:
- Does it fit the style model and the variant (colours, mood, motif)?
- Is there lettering, fake writing, logos, watermarks, distorted figures or other AI faults?
- Is there a calm area where desktop icons stay legible (usually the top left)?
ok: true only if there is no major issue. target: picture or other; fix: a concrete change to
the picture (motif, composition, light, colours).""",
    "desktop": """This is a screenshot of the whole desktop right after the theme was installed and applied.
Judge as a demanding UI designer:
- Are the desktop icons and their labels legible against the wallpaper (contrast)?
- Is the panel (taskbar) legible and does it fit the theme?
- Do colours, panel and wallpaper go together and fit the style model?
- Obvious rendering faults: garbled or missing glyphs, the default Breeze look left over where
  the theme should be, black or white boxes, cut-off elements?
ok: true only if there is no major issue. target: wallpaper, panel, text_contrast, icons,
decoration, rendering or other; fix: a concrete change.""",
}


def _image_url(path_or_image, size=1024):
    im = path_or_image if isinstance(path_or_image, Image.Image) else Image.open(path_or_image)
    im = im.convert("RGB")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def look(kind, picture, spec, v, log=print, size=1024, measured=None):
    """One structured verdict on one picture."""
    meta = spec.get("_meta", {})
    ctx = CONTEXT.format(request=meta.get("request", ""), name=spec["name"], description=spec["description"],
                         variant=v["name"], mode=v["mode"], lead=v["lead"], look=v["look"])
    if measured:
        ctx += ("\nMeasured contrast of the title text to its title bar: "
                + ", ".join(f"{k} {c}:1" for k, c in measured.items())
                + " (4.5:1 and above is legible; trust these numbers over your impression).")
    msg = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": _image_url(picture, size)}},
                                        {"type": "text", "text": ctx + "\n\n" + QUESTIONS[kind]}]}]
    text, info = llm.chat(msg, schema=schema(kind), max_tokens=1200, temperature=0.2, base=llm.VISION)
    verdict = json.loads(text)
    if measured:
        verdict = filter_measured(verdict, measured)
    log(f"  review {kind} {v['id']}: score {verdict['score']}/10, "
        f"{'ok' if verdict['ok'] else 'issues'} ({info['seconds']} s) — {verdict['summary'][:120]}")
    events.emit("review", kind, variant=v["id"], score=verdict["score"], ok=verdict["ok"],
                summary=verdict["summary"], issues=verdict["issues"])
    return verdict


def decoration_picture(pkg, var, spec):
    """Active above inactive, on the desktop colour — what KWin will draw.
    The title bars twice enlarged, so the vision model can read the 13 px
    title text (at natural size it called legible text "nearly invisible")."""
    from . import preview
    from .palette import rgb
    font = f"{pkg}/fonts/{spec['font']}.ttf"
    a, th, _ = preview.window(pkg, var, 760, 160, f"{spec['name']} — active window", font, active=True)
    i, _, _ = preview.window(pkg, var, 760, 160, f"{spec['name']} — inactive window", font, active=False)
    strip = th + 24                                 # title bar plus a little of the frame
    canvas = Image.new("RGBA", (800, 2 * strip + 60), rgb(var.P["desktop"]) + (255,))
    canvas.alpha_composite(a.crop((0, 0, 760, strip)), (20, 20))
    canvas.alpha_composite(i.crop((0, 0, 760, strip)), (20, 40 + strip))
    return canvas.resize((canvas.width * 2, canvas.height * 2), Image.LANCZOS)


def title_contrast(pkg, var, spec):
    """Measured contrast of the title text to its title bar (median of the bar
    between menu button and window buttons), active and inactive. The vision
    model judged an inactive title of 6:1 "nearly invisible" — a measurement
    overrules such claims (see filter_measured)."""
    from . import preview
    from .palette import contrast
    import statistics
    font = f"{pkg}/fonts/{spec['font']}.ttf"
    rc = preview._rc(f"{pkg}/aurorae/themes/{var.camel}/{var.camel}rc")
    out = {}
    for state, active in (("active", True), ("inactive", False)):
        im, th, border = preview.window(pkg, var, 760, 160, "", font, active=active)
        bar = im.convert("RGB").crop((border + 60, 3, 760 - 160, max(4, th - 3)))
        px = list(bar.getdata())
        med = tuple(int(statistics.median(c[i] for c in px)) for i in range(3))
        text = tuple(int(x) for x in rc["ActiveTextColor" if active else "InactiveTextColor"].split(","))
        out[state] = round(contrast("#%02x%02x%02x" % text, "#%02x%02x%02x" % med), 1)
    return out


def filter_measured(verdict, measured):
    """Claims that the title text is illegible, against a measured ≥ 4.5:1, become minor."""
    for i in verdict["issues"]:
        low = (i["what"] + " " + i["fix"]).lower()
        if i["severity"] == "major" and i["target"] in ("title_text", "title_colours") and \
                any(w in low for w in ("legib", "invisible", "contrast", "read", "visible")):
            state = "inactive" if "inactive" in low else "active"
            if measured.get(state, 0) >= 4.5:
                i["severity"] = "minor"
                i["what"] += f" [overruled: measured {measured[state]}:1]"
    verdict["ok"] = not any(i["severity"] == "major" for i in verdict["issues"])
    return verdict


def wallpapers_of(pkg, var):
    base = f"{pkg}/wallpapers"
    return sorted(f"{base}/{d}/contents/images/1920x1080.jpg" for d in os.listdir(base)
                  if (d == var.id or d.startswith(var.id + "-")) and
                  os.path.exists(f"{base}/{d}/contents/images/1920x1080.jpg"))


def _issue_lines(issues):
    return [f"visual review: {i['what']} — suggested: {i['fix']}" for i in issues]


def repair_colours(spec, vi, issues, log=print, seed=None):
    """Colours (title, text, panel) through the specification's partial repair."""
    v = spec["variants"][vi]
    meta = spec.get("_meta", {})
    system = designer.SPEC_SYSTEM.format(
        fonts="(unchanged)", emblems=", ".join(specmod.EMBLEMS),
        colors="\n".join(f"    {k}: {d}" for k, d in specmod.COLOR_KEYS.items()))
    path = ("variants", vi, "colors")
    old = json.loads(json.dumps(v["colors"]))
    new = designer.repair_part(system, meta.get("request", ""), meta.get("brief", ""), spec, path,
                               _issue_lines(issues), log=log, seed=seed)
    if new == old:
        log(f"  colour repair for {v['id']} changed nothing")
        return False
    v["colors"] = new
    errs = [m for p, m in specmod.validate_paths(spec) if p[:2] == ("variants", vi)]
    if errs:                     # the repair must not break the checks that held before
        log(f"  colour repair rejected ({errs[0][:100]}) — keeping the old colours")
        v["colors"] = old
        return False
    events.emit("review", "repair", target="colors", variant=v["id"], old=old, new=new)
    return True


def repair_frame(spec, issues, log=print, seed=None):
    meta = spec.get("_meta", {})
    system = designer.SPEC_SYSTEM.format(
        fonts="(unchanged)", emblems=", ".join(specmod.EMBLEMS),
        colors="\n".join(f"    {k}: {d}" for k, d in specmod.COLOR_KEYS.items()))
    old = json.loads(json.dumps(spec["decoration"]))
    spec["decoration"] = designer.repair_part(system, meta.get("request", ""), meta.get("brief", ""), spec,
                                              ("decoration",), _issue_lines(issues), log=log, seed=seed)
    if [m for p, m in specmod.validate_paths(spec) if p[:1] == ("decoration",)]:
        spec["decoration"] = old
        log("  frame repair rejected — keeping the old decoration")
        return False
    events.emit("review", "repair", target="decoration", old=old, new=spec["decoration"])
    return True


PROMPT_FIX = """A desktop wallpaper was painted from this prompt:
{prompt}
A visual review found:
- {issues}
Write the prompt anew so that these faults go away: English, one continuous paragraph,
50–130 words, only the scene (no medium or style words), describe looks instead of names,
one calm area for desktop icons, never symbols, screens, signs, lettering or frames.
End with "no text, no logos"."""


def repair_wallpaper(spec, plan, vi, index, issues, log=print, seed=None):
    """A new prompt for one wallpaper; the cache paints it anew on the next build."""
    from . import artplan
    v = spec["variants"][vi]
    vplan = (plan or {}).get("variants", {}).get(v["id"])
    old = vplan["wallpapers"][index]["prompt"] if vplan else v["wallpaper_prompt"]
    part = {"type": "object", "additionalProperties": False, "required": ["prompt"],
            "properties": {"prompt": {"type": "string", "minLength": 200, "maxLength": 1300}}}
    for attempt in range(3):
        text, _ = llm.chat([{"role": "user", "content": PROMPT_FIX.format(
            prompt=old, issues="\n- ".join(f"{i['what']} ({i['fix']})" for i in issues))}],
            schema=part, max_tokens=900, temperature=0.5, seed=(seed or 0) + attempt)
        new = json.loads(text)["prompt"]
        if not artplan._traps(artplan._body(new)) and "no text" in new.lower():
            break
    else:
        log(f"  wallpaper prompt for {v['id']} not repaired (trap words remain)")
        return False
    if vplan:
        vplan["wallpapers"][index]["prompt"] = new
    else:
        v["wallpaper_prompt"] = new
    events.emit("review", "repair", target="wallpaper", variant=v["id"], index=index, old=old, new=new)
    return True


def review(out, spec, plan=None, rounds=2, vm=None, lang="en", use_comfy=True, log=print, seed=None):
    """Look, repair, build again, look again — at most `rounds` repair rounds.
    Writes <out>/review.json; returns it."""
    from . import build, check, vmtest
    history = []
    for r in range(rounds + 1):
        pkg = f"{out}/package"
        variants = [build.Variant(spec, v) for v in spec["variants"]]
        events.begin("review", round=r)
        found = {"round": r, "variants": {}}
        todo = []                                  # (repair, args)
        for vi, var in enumerate(variants):
            v = spec["variants"][vi]
            res = {"decoration": look("decoration", decoration_picture(pkg, var, spec), spec, v, log, size=1600,
                                      measured=title_contrast(pkg, var, spec))}
            res["wallpapers"] = [look("wallpaper", w, spec, v, log) for w in wallpapers_of(pkg, var)]
            found["variants"][v["id"]] = res
            major = [i for i in res["decoration"]["issues"] if i["severity"] == "major"]
            colour = [i for i in major if i["target"] in ("title_colours", "title_text")]
            frame = [i for i in major if i["target"] in ("frame", "buttons")]
            if colour:
                todo.append((repair_colours, (spec, vi, colour)))
            if frame:
                todo.append((repair_frame, (spec, frame)))
            for wi, w in enumerate(res["wallpapers"]):
                bad = [i for i in w["issues"] if i["severity"] == "major" and i["target"] == "picture"]
                if bad and use_comfy:      # without an image model a repaint would be a procedural picture
                    todo.append((repair_wallpaper, (spec, plan, vi, wi, bad)))
        if vm:
            vt = vmtest.run(out, envs=[vm], lang=lang, log=log)[0]
            shot = f"{out}/vm-{vm}-applied.png"
            if os.path.exists(shot):
                v0 = spec["variants"][0]
                d = look("desktop", shot, spec, v0, log)
                found["desktop"] = d
                for i in d["issues"]:
                    if i["severity"] != "major":
                        continue
                    if i["target"] in ("text_contrast", "panel", "decoration"):
                        todo.append((repair_colours, (spec, 0, [i])))
                    elif i["target"] == "wallpaper" and use_comfy:
                        todo.append((repair_wallpaper, (spec, plan, 0, 0, [i])))
            found["vmtest_errors"] = vt["errors"]
        history.append(found)
        events.end("review", round=r, repairs=len(todo))
        if not todo or r == rounds:
            break
        log(f"review round {r}: {len(todo)} repair(s)")
        done = 0
        for fn, args in todo:
            done += bool(fn(*args, log=log, seed=seed))
        if not done:
            break
        build.build(spec, out, use_comfy=use_comfy, log=log, plan=plan)
        errors, _ = check.run(pkg, [build.Variant(spec, v) for v in spec["variants"]])
        if errors:
            log(f"  package check after the repair: {errors[:3]}")
    left = [f"{vid} {kind}: {i['what']}" for h in history[-1:] for vid, res in h["variants"].items()
            for kind, verdicts in (("decoration", [res["decoration"]]), ("wallpaper", res["wallpapers"]))
            for vd in verdicts for i in vd["issues"] if i["severity"] == "major"]
    if history and history[-1].get("desktop"):
        left += [f"desktop: {i['what']}" for i in history[-1]["desktop"]["issues"] if i["severity"] == "major"]
    result = {"rounds": history, "left": left, "vision": llm.VISION}
    with open(f"{out}/review.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(f"{out}/spec.json", "w") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    if plan is not None:
        with open(f"{out}/artplan.json", "w") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
    return result
