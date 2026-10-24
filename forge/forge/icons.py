"""Icon-Theme aus gemalten Cameos.

Je Symbol ein Bild (ComfyUI, einmal für alle Varianten, zwischengespeichert),
je Variante ein Rahmen in deren Metallfarbe: dunkle Außenkante, Bevel,
Nieten, vertieftes Bildfeld. Bitmaps in allen Größen, die Dolphin und das
Panel anfragen (Type=Fixed); was der Katalog nicht abdeckt, erbt das Theme
von Breeze.
"""
import json
import os
import zlib

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from . import artplan, comfy, iconset, imgcheck
from .palette import mix, rgb, shift

CONTEXT_DIR = {"places": "places", "devices": "devices", "apps": "apps", "categories": "categories",
               "mimetypes": "mimetypes", "actions": "actions"}
CONTEXT_NAME = {"places": "Places", "devices": "Devices", "apps": "Applications",
                "categories": "Categories", "mimetypes": "MimeTypes", "actions": "Actions"}


def paint_all(plan, request, assets, private, log=print):
    """Alle Cameo-Bilder malen (fehlende nachholen). Liefert {icon: Pfad}.

    Neben jedem Bild liegt sein Prompt; ändert sich der (neues Motiv, neue
    Stilformel), wird neu gemalt — sonst blieben alte Fehlbilder im Cache."""
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
        log(f"Cameos: {len(jobs)} von {len(iconset.PAINTED)} zu malen")
    for i, (name, prompt) in enumerate(jobs.items()):
        retry = plan["icons"][name].get("retry")
        key = name + (f"#{retry}" if retry else "")
        dst = out[name]
        comfy.generate(prompt, 512, 512, zlib.crc32(key.encode()) % 10**6, dst,
                       log=lambda m, i=i, name=name: log(f"  [{i + 1}/{len(jobs)}] {name}:{m.split(':', 1)[-1]}"))
        with open(dst[:-4] + ".prompt", "w") as f:
            f.write(prompt)
    return out


def paint_checked(plan, spec, assets, private, log=print, rounds=2):
    """Malen, prüfen, misslungene Motive vom LLM neu formulieren lassen, neu malen.

    Gesammelt je Runde: erst alle Bilder, dann alle Prüfungen und Reparaturen
    (LLM), dann alle Neumalungen — so wechselt die Grafikkarte nur zweimal pro
    Runde zwischen LLM und Bildmodell (gpu.py)."""
    request = spec.get("_meta", {}).get("request", "")
    pictures = paint_all(plan, request, assets, private, log)
    history = plan.setdefault("image_fixes", [])
    restyled = False
    for r in range(1, rounds + 1):
        bad = imgcheck.check(pictures, plan["icons"], log)
        if not bad:
            break
        if plan.get("style") and not restyled and len(bad) >= 0.4 * len(pictures):
            # Systematisch: dann liegt es am gemeinsamen Stil, nicht an den Motiven.
            restyled = True
            seen = [imgcheck.SHOWS[n] for n in bad if n in imgcheck.SHOWS][:12]
            log(f"Bildprüfung: {len(bad)} von {len(pictures)} auffällig — Stilblatt wird neu geschrieben")
            feedback = ("ACHTUNG: Mit dem letzten Stilblatt zeigten fast alle Icons dasselbe statt ihres Gegenstands, "
                        "z. B.: " + " / ".join(seen) + "\nVorheriges Stilblatt: " + json.dumps(plan["style"])
                        + "\nSchreibe ein Stilblatt, das nur Malweise, Farben, Oberflächen und Licht beschreibt.")
            style, _ = artplan.style_sheet(spec, private, log, seed=8000,
                                           subjects=artplan.scene_subjects(plan), feedback=feedback)
            history.append({"round": r, "restyle": True, "old": plan["style"], "new": style, "seen": seen})
            plan["style"] = style
            plan["icons"] = artplan.catalog_motifs(style)
            pictures = paint_all(plan, request, assets, private, log)
            continue
        log(f"Bildprüfung Runde {r}: {len(bad)} Cameo(s) neu: {', '.join(bad)}")
        for name, errs in bad.items():
            entry = plan["icons"][name]
            style = plan.get("style")
            if style and iconset.FAMILY[name] != "object":
                # Katalog: nur das Zeichen auf Ordner/Blatt wird neu gefasst, die Grundform bleibt.
                ask = {"source": "catalog", "motif": entry.get("picture") or iconset.PICTURE[name]}
                errs = errs + ["beschreibe nur das Zeichen, das groß auf dem Ordner/Blatt sitzt (einen einzelnen "
                               "Gegenstand, 3–12 Wörter), nicht den Ordner/das Blatt selbst"]
            else:
                ask = {"source": entry["source"], "motif": entry["motif"]}
            new = artplan.repair_icon(name, ask, errs, spec, private, seed=7000 + r, log=log, catalog=bool(style))
            if new is None:
                log(f"  {name}: keine gültige Neufassung — Bild bleibt")
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
            log(f"Bildprüfung: nach {rounds} Runden noch auffällig: {', '.join(bad)}")
    plan["image_check"] = {"left": sorted(bad) if bad else [], "vision": imgcheck.LAST_VISION}
    return pictures


def _metal(P):
    """Rahmenfarben aus der Palette: Metall in der Titelfarbe, abgedunkelt."""
    base = mix(P["title_active"], P["surface"], 0.35)
    return {"base": base, "light": shift(base, 0.16), "dark": shift(base, -0.18),
            "edge": mix(P["border"], "#000000", 0.4), "rivet": shift(base, 0.25), "glow": P["glow"]}


def frame(picture, P, size):
    """Ein Cameo in Rahmen, size×size Pixel. Bis 32 px schlicht, darüber mit Nieten."""
    m = _metal(P)
    S = size * 4 if size < 64 else size        # Überabtastung für saubere Kanten
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    small = size <= 32
    edge = max(1, round(S * (0.03 if small else 0.02)))
    bevel = round(S * (0.07 if small else 0.085))
    d.rectangle([0, 0, S - 1, S - 1], fill=rgb(m["edge"]) + (255,))
    # Metallplatte mit Licht oben links
    inner = [edge, edge, S - 1 - edge, S - 1 - edge]
    d.rectangle(inner, fill=rgb(m["base"]) + (255,))
    d.polygon([(edge, edge), (S - 1 - edge, edge), (S - 1 - edge - bevel, edge + bevel),
               (edge + bevel, edge + bevel), (edge + bevel, S - 1 - edge - bevel), (edge, S - 1 - edge)],
              fill=rgb(m["light"]) + (255,))
    d.polygon([(S - 1 - edge, S - 1 - edge), (edge, S - 1 - edge), (edge + bevel, S - 1 - edge - bevel),
               (S - 1 - edge - bevel, S - 1 - edge - bevel), (S - 1 - edge - bevel, edge + bevel),
               (S - 1 - edge, edge)], fill=rgb(m["dark"]) + (255,))
    # Bildfeld, vertieft (dunkle Linie oben/links, helle unten/rechts)
    o = edge + bevel
    w = S - 2 * o
    pic = Image.open(picture).convert("RGB")
    if small:   # klein zählt nur das Motiv in der Mitte, nicht die Szene drumherum
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
    """Icon-Theme für eine Variante nach out/icons/<Name>Icons."""
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
    lines = ["[Icon Theme]", f"Name={var.name}", f"Comment=Cameo-Symbole, generiert von Theme Forge",
             f"Inherits={inherit},hicolor", "Example=folder",
             "Directories=" + ",".join(sorted(d for d, _, _ in dirs)), ""]
    for d, size, ctx in sorted(dirs):
        lines += [f"[{d}]", f"Size={size}", f"Context={CONTEXT_NAME[ctx]}", "Type=Fixed", ""]
    with open(f"{base}/index.theme", "w") as f:
        f.write("\n".join(lines))
    return name
