"""Icon theme from painted cameos.

One picture per icon (ComfyUI, once for all variants, cached), a frame per
variant in its metal colour: dark outer edge, bevel, rivets, sunken picture
field. Bitmaps in all the sizes Dolphin and the panel ask for (Type=Fixed);
what the catalogue does not cover the theme inherits from Breeze.
"""
import json
import os
import zlib

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from . import artplan, comfy, events, iconset, imgcheck
from .palette import mix, rgb, shift

CONTEXT_DIR = {"places": "places", "devices": "devices", "apps": "apps", "categories": "categories",
               "mimetypes": "mimetypes", "actions": "actions"}
CONTEXT_NAME = {"places": "Places", "devices": "Devices", "apps": "Applications",
                "categories": "Categories", "mimetypes": "MimeTypes", "actions": "Actions"}


def paint_all(plan, request, assets, private, log=print):
    """Paint all cameo pictures (the missing ones). Returns {icon: path}.

    Beside each picture lies its prompt; when that changes (a new motif, a new
    style formula) it is painted again — else old failures stayed in the cache."""
    out = {}
    os.makedirs(f"{assets}/cameos", exist_ok=True)
    jobs = {}
    for name in iconset.PAINTED:
        dst = f"{assets}/cameos/{name}.png"
        prompt = (artplan.icon_prompt(plan["icons"][name]["motif"], plan["style"]) if plan.get("style")
                  else artplan.cameo_prompt(plan["icons"][name]["motif"], request, private))
        stamp = dst[:-4] + ".prompt"
        if os.path.exists(dst) and (not os.path.exists(stamp) or open(stamp).read() != prompt):
            os.remove(dst)
        if not os.path.exists(dst):
            jobs[name] = prompt
        out[name] = dst
    if jobs:
        log(f"cameos: {len(jobs)} of {len(iconset.PAINTED)} to paint")
    for i, (name, prompt) in enumerate(jobs.items()):
        retry = plan["icons"][name].get("retry")
        key = name + (f"#{retry}" if retry else "")
        dst = out[name]
        comfy.generate(prompt, 512, 512, zlib.crc32(key.encode()) % 10**6, dst,
                       log=lambda m, i=i, name=name: log(f"  [{i + 1}/{len(jobs)}] {name}:{m.split(':', 1)[-1]}"))
        with open(dst[:-4] + ".prompt", "w") as f:
            f.write(prompt)
        events.emit("icons", "painted", icon=name, prompt=prompt, n=i + 1, of=len(jobs))
        progress_sheet([out[n] for n in list(jobs)[:i + 1]], f"{assets}/progress.png")
    return out


def progress_sheet(paths, dst, cols=8, rows=4, cell=128):
    """The latest painted icons as one picture (newest top left), for showing
    beside a screen recording while ComfyUI paints; rewritten after each icon."""
    sheet = Image.new("RGB", (cols * cell, rows * cell), (24, 24, 24))
    for k, path in enumerate(reversed(paths[-cols * rows:])):
        try:
            im = Image.open(path).convert("RGB").resize((cell - 8, cell - 8))
        except OSError:
            continue
        sheet.paste(im, ((k % cols) * cell + 4, (k // cols) * cell + 4))
    tmp = dst + ".tmp.png"
    sheet.save(tmp)
    os.replace(tmp, dst)          # a viewer never sees a half-written file


def paint_checked(plan, spec, assets, private, log=print, rounds=2):
    """Paint, check, have failed motifs rewritten by the LLM, paint again.

    Collected per round: first all pictures, then all checks and repairs
    (LLM), then all repaintings — so the graphics card switches between LLM
    and image model only twice per round (gpu.py)."""
    request = spec.get("_meta", {}).get("request", "")
    pictures = paint_all(plan, request, assets, private, log)
    history = plan.setdefault("image_fixes", [])
    restyled = False
    for r in range(1, rounds + 1):
        bad = imgcheck.check(pictures, plan["icons"], log)
        if not bad:
            break
        if plan.get("style") and not restyled and len(bad) >= 0.4 * len(pictures):
            # Systematic: then the shared style is to blame, not the motifs.
            restyled = True
            seen = [imgcheck.SHOWS[n] for n in bad if n in imgcheck.SHOWS][:12]
            log(f"image check: {len(bad)} of {len(pictures)} flawed — rewriting the style sheet")
            feedback = ("CAUTION: with the last style sheet almost all icons showed the same thing instead of their object, "
                        "e.g.: " + " / ".join(seen) + "\nPrevious style sheet: " + json.dumps(plan["style"])
                        + "\nWrite a style sheet that describes only the way of painting, colours, surfaces and light.")
            style, _ = artplan.style_sheet(spec, private, log, seed=8000,
                                           subjects=artplan.scene_subjects(plan), feedback=feedback)
            history.append({"round": r, "restyle": True, "old": plan["style"], "new": style, "seen": seen})
            plan["style"] = style
            plan["icons"] = artplan.catalog_motifs(style)
            pictures = paint_all(plan, request, assets, private, log)
            continue
        log(f"image check round {r}: {len(bad)} cameo(s) anew: {', '.join(bad)}")
        for name, errs in bad.items():
            entry = plan["icons"][name]
            style = plan.get("style")
            if style and iconset.FAMILY[name] != "object":
                # Catalogue: only the sign on the folder/sheet is rewritten, the basic shape stays.
                ask = {"source": "catalog", "motif": entry.get("picture") or iconset.PICTURE[name]}
                errs = errs + ["describe only the sign that sits large on the folder/sheet (a single "
                               "object, 3–12 words), not the folder/sheet itself"]
            else:
                ask = {"source": entry["source"], "motif": entry["motif"]}
            new = artplan.repair_icon(name, ask, errs, spec, private, seed=7000 + r, log=log, catalog=bool(style))
            if new is None:
                log(f"  {name}: no valid rewrite — the picture stays")
                continue
            if style and iconset.FAMILY[name] != "object":
                new = dict(new, picture=new["motif"], motif=artplan.compose(name, new["motif"], style))
            history.append({"round": r, "icon": name, "errors": errs, "old": entry["motif"], "new": new["motif"]})
            plan["icons"][name] = dict(new, retry=r)
            os.remove(pictures[name])
        pictures = paint_all(plan, request, assets, private, log)
    else:
        bad = imgcheck.check(pictures, plan["icons"], log)
        if bad:
            log(f"image check: still flawed after {rounds} rounds: {', '.join(bad)}")
    plan["image_check"] = {"left": sorted(bad) if bad else [], "vision": imgcheck.LAST_VISION}
    return pictures


def _metal(P):
    """Frame colours from the palette: metal in the title colour, darkened."""
    base = mix(P["title_active"], P["surface"], 0.35)
    return {"base": base, "light": shift(base, 0.16), "dark": shift(base, -0.18),
            "edge": mix(P["border"], "#000000", 0.4), "rivet": shift(base, 0.25), "glow": P["glow"]}


def frame(picture, P, size):
    """A cameo in a frame, size×size pixels. Plain up to 32 px, with rivets above."""
    m = _metal(P)
    S = size * 4 if size < 64 else size        # supersampling for clean edges
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    small = size <= 32
    edge = max(1, round(S * (0.03 if small else 0.02)))
    bevel = round(S * (0.07 if small else 0.085))
    d.rectangle([0, 0, S - 1, S - 1], fill=rgb(m["edge"]) + (255,))
    # metal plate lit from the top left
    inner = [edge, edge, S - 1 - edge, S - 1 - edge]
    d.rectangle(inner, fill=rgb(m["base"]) + (255,))
    d.polygon([(edge, edge), (S - 1 - edge, edge), (S - 1 - edge - bevel, edge + bevel),
               (edge + bevel, edge + bevel), (edge + bevel, S - 1 - edge - bevel), (edge, S - 1 - edge)],
              fill=rgb(m["light"]) + (255,))
    d.polygon([(S - 1 - edge, S - 1 - edge), (edge, S - 1 - edge), (edge + bevel, S - 1 - edge - bevel),
               (S - 1 - edge - bevel, S - 1 - edge - bevel), (S - 1 - edge - bevel, edge + bevel),
               (S - 1 - edge, edge)], fill=rgb(m["dark"]) + (255,))
    # picture field, sunken (a dark line top/left, a light one bottom/right)
    o = edge + bevel
    w = S - 2 * o
    pic = Image.open(picture).convert("RGB")
    if small:   # small, only the motif in the centre counts, not the scene round it
        W, H = pic.size
        pic = pic.crop((W // 8, H // 8, W - W // 8, H - H // 8))
    pic =ImageEnhance.Contrast(pic).enhance(1.08).resize((w, w), Image.LANCZOS)
    im.paste(pic, (o, o))
    line = max(1, round(S * 0.012))
    d.rectangle([o, o, o + w - 1, o + line - 1], fill=rgb(shift(m["dark"], -0.12)) + (255,))
    d.rectangle([o, o, o + line - 1, o + w - 1], fill=rgb(shift(m["dark"], -0.12)) + (255,))
    if not small:
        r = max(2, round(S * 0.022))
        for cx, cy in ((edge + bevel / 2, edge + bevel / 2), (S - edge - bevel / 2, edge + bevel / 2),
                       (edge + bevel / 2, S - edge - bevel / 2), (S - edge - bevel / 2, S - edge - bevel / 2)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb(m["dark"]) + (255,))
            d.ellipse([cx - r + 1, cy - r + 1, cx + r - 2, cy + r - 2], fill=rgb(m["rivet"]) + (255,))
    if S != size:
        im = im.resize((size, size), Image.LANCZOS)
        if size <= 24:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=1))
    return im


def build_theme(var, pictures, emblem_png, out, inherit):
    """The icon theme of a variant into out/icons/<Name>Icons."""
    name = f"{var.camel}Icons"
    base = f"{out}/icons/{name}"
    dirs = set()
    for icon, (ctx, _, aliases) in iconset.ICONS.items():
        src = emblem_png if icon == "start-here" else pictures[icon]
        for size in iconset.SIZES:
            img = frame(src, var.P, size)
            d = f"{size}x{size}/{CONTEXT_DIR[ctx]}"
            dirs.add((d, size, ctx))
            os.makedirs(f"{base}/{d}", exist_ok=True)
            for n in [icon] + aliases:
                img.save(f"{base}/{d}/{n}.png", optimize=True)
    lines = ["[Icon Theme]", f"Name={var.name}", f"Comment=Cameo icons, generated by Theme Forge",
             f"Inherits={inherit},hicolor", "Example=folder",
             "Directories=" + ",".join(sorted(d for d, _, _ in dirs)), ""]
    for d, size, ctx in sorted(dirs):
        lines += [f"[{d}]", f"Size={size}", f"Context={CONTEXT_NAME[ctx]}", "Type=Fixed", ""]
    with open(f"{base}/index.theme", "w") as f:
        f.write("\n".join(lines))
    return name
