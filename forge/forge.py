#!/usr/bin/env python3
"""Theme Forge — ein lokales LLM entwirft aus einer Stilbeschreibung ein Plasma-Theme.

    ./forge.py all "Red Alert 2" -o out/ra2          # Entwurf, Bau, Prüfung, Vorschau
    ./forge.py design "Stil" -o out/x                 # nur spec.json (LLM)
    ./forge.py build out/x                            # Paket aus spec.json bauen
    ./forge.py bench "Stil" -n 5 -o out/bench         # Zuverlässigkeit messen (nur LLM-Teil)
    ./forge.py vmtest out/x [--vm fedora,ubuntu,artix] # in den Test-VMs installieren/anwenden/entfernen

Umgebung: FORGE_LLM (Standard http://127.0.0.1:8090/v1), FORGE_COMFY (Standard lokales
ComfyUI 127.0.0.1:8189), FORGE_LLM_SERVICE (wird für Bildläufe angehalten, siehe forge/gpu.py).
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forge import artplan, build, check, designer, llm, preview, spec as specmod, vmtest  # noqa: E402


def log(msg):
    print(msg, flush=True)


def cmd_design(a):
    os.makedirs(a.out, exist_ok=True)
    s = designer.run(a.request, avoid=a.avoid, log=log, seed=a.seed)
    with open(f"{a.out}/spec.json", "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    log(f"spec.json geschrieben ({s['_meta']['attempts']} LLM-Versuch(e))")
    if a.art:
        p = artplan.plan(s, private=a.private, log=log, seed=a.seed, themed_icons=a.themed_icons)
        with open(f"{a.out}/artplan.json", "w") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)
        log("artplan.json geschrieben")
    return s


def cmd_build(a, s=None):
    if s is None:
        s = json.load(open(f"{a.out}/spec.json"))
    errs = specmod.validate(s, a.avoid)
    if errs:
        log("spec.json ungültig:\n- " + "\n- ".join(errs))
        return 1
    t0 = time.time()
    plan = None
    if os.path.exists(f"{a.out}/artplan.json") and not a.no_art:
        plan = json.load(open(f"{a.out}/artplan.json"))
    report = build.build(s, a.out, use_comfy=not a.no_comfy, log=log, plan=plan)
    if plan:      # die Bildprüfung kann Motive neu gefasst haben
        with open(f"{a.out}/artplan.json", "w") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
    variants = [build.Variant(s, v) for v in s["variants"]]
    pkg = f"{a.out}/package"
    errors, notes = check.run(pkg, variants)
    for n in notes:
        log(f"Hinweis: {n}")
    for e in errors:
        log(f"FEHLER: {e}")
    sheet = preview.sheet(pkg, variants, s, f"{a.out}/preview.jpg")
    report.update({"errors": errors, "notes": notes, "seconds": round(time.time() - t0, 1)})
    for v in report["variants"].values():
        v.pop("palette", None)
    with open(f"{a.out}/report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log(f"Paket: {pkg}\nVorschau: {sheet}\n{'OK' if not errors else f'{len(errors)} Fehler'} "
        f"in {report['seconds']} s")
    return 1 if errors else 0


def cmd_bench(a):
    """Nur die LLM-Kette, n-mal: wie oft entsteht eine gültige Spezifikation,
    nach wie vielen Versuchen, und erfüllt sie die Stilprüfung der Vorlage?"""
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for i in range(a.n):
        t0 = time.time()
        try:
            s = designer.run(a.request, avoid=a.avoid, log=lambda m: None, seed=1000 + i)
            ok, attempts = True, s["_meta"]["attempts"]
            with open(f"{a.out}/spec-{i}.json", "w") as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
        except llm.LLMError as e:
            s, ok, attempts, err = None, False, None, str(e)
            log(f"  Lauf {i}: {e}")
        else:
            err = None
        style = style_check(s, a.expect) if s and a.expect else []
        rows.append({"run": i, "valid": ok, "attempts": attempts, "style_errors": style, "error": err,
                     "auto": bool(s and s.get("_auto")),
                     "seconds": round(time.time() - t0, 1)})
        log(f"Lauf {i}: gültig={ok} Versuche={attempts} Stil={'ok' if not style else style} "
            f"({rows[-1]['seconds']} s)")
    valid = sum(r["valid"] for r in rows)
    styled = sum(r["valid"] and not r["style_errors"] for r in rows)
    first = sum(r["attempts"] == 1 for r in rows)
    auto = sum(r["auto"] for r in rows)
    summary = {"runs": a.n, "valid": valid, "first_try": first, "style_ok": styled, "auto_fixed": auto,
               "rows": rows}
    with open(f"{a.out}/bench.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"\ngültig {valid}/{a.n}, beim ersten Versuch {first}/{a.n}, Stilprüfung bestanden {styled}/{a.n}, "
        f"davon mit Automatik-Korrektur {auto}")
    return 0 if styled == a.n else 1


def cmd_bench_art(a):
    """Den Bildplan n-mal auf einer festen spec.json erzeugen (aus -o): wie oft
    gelingt er, wie viele Runden, wie oft greift die Automatik, und nennen die
    Szenen die abgestimmten Elemente?"""
    s = json.load(open(f"{a.out}/spec.json"))
    rows = []
    for i in range(a.n):
        t0 = time.time()
        try:
            p = artplan.plan(s, private=a.private, log=lambda m: None, seed=2000 + i, themed_icons=a.themed_icons)
            row = {"ok": True, "rounds": p["rounds"], "auto": p.get("auto"),
                   "elements": {k: [e["name"] for e in v["elements"]] for k, v in p["variants"].items()}}
            with open(f"{a.out}/artplan-bench-{i}.json", "w") as f:
                json.dump(p, f, indent=2, ensure_ascii=False)
        except llm.LLMError as e:
            row = {"ok": False, "error": str(e)[:400]}
        row["seconds"] = round(time.time() - t0, 1)
        rows.append(row)
        log(f"Lauf {i}: {json.dumps(row, ensure_ascii=False)[:300]}")
    ok = sum(r["ok"] for r in rows)
    auto = sum(bool(r.get("auto")) for r in rows)
    with open(f"{a.out}/bench-art.json", "w") as f:
        json.dump({"runs": a.n, "ok": ok, "auto": auto, "rows": rows}, f, indent=2, ensure_ascii=False)
    log(f"\nBildplan gelungen {ok}/{a.n}, mit Automatik {auto}")
    return 0 if ok == a.n else 1


def style_check(s, expect_path):
    """Erwartungen an eine Vorlage (JSON): je Variante Farbton-Bereiche, Modus,
    erlaubte Eckformen. Hier wird geprüft, ob das LLM die Vorlage getroffen hat."""
    import colorsys
    from forge.palette import rgb
    exp = json.load(open(expect_path))
    errs = []
    if "corner" in exp and s["shape"]["corner"] not in exp["corner"]:
        errs.append(f"Ecke {s['shape']['corner']} nicht in {exp['corner']}")
    if "variants" in exp and len(s["variants"]) < exp["variants"]["min"]:
        errs.append(f"nur {len(s['variants'])} Variante(n)")
    for want in exp.get("palettes", []):
        found = False
        for v in s["variants"]:
            hits = 0
            for key in want["keys"]:
                h, l, sat = colorsys.rgb_to_hls(*(c / 255 for c in rgb(v["colors"][key])))
                hue = h * 360
                lo, hi = want["hue"]
                inside = (lo <= hue <= hi) if lo <= hi else (hue >= lo or hue <= hi)
                if inside and sat >= want.get("min_sat", 0.25):
                    hits += 1
            if hits >= want.get("min_hits", 1) and (want.get("mode") in (None, v["mode"])):
                found = True
        if not found:
            errs.append(f"keine Variante passt zu „{want['name']}“")
    return errs


def cmd_vmtest(a):
    """Das gebaute Paket in den Test-VMs (forge/vmtest.py): Fedora, Ubuntu, Artix/OpenRC."""
    reports = vmtest.run(a.out, envs=a.vm.split(","), variant=a.variant, reset=a.reset, log=log)
    bad = [r["env"] for r in reports if r["errors"]]
    log(f"VM-Test: {len(reports) - len(bad)} von {len(reports)} ohne Fehler" + (f" (Fehler: {', '.join(bad)})" if bad else ""))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["design", "build", "all", "bench", "bench-art", "vmtest"])
    ap.add_argument("request", nargs="?", help="Stilbeschreibung (design/all/bench) oder Ausgabeordner (build)")
    ap.add_argument("-o", "--out")
    ap.add_argument("--avoid", action="append", default=[], help="zusätzliche verbotene Begriffe")
    ap.add_argument("--no-comfy", action="store_true", help="prozedurale Hintergründe statt ComfyUI")
    ap.add_argument("--seed", type=int)
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--expect", help="Stil-Erwartungen (JSON) für bench")
    ap.add_argument("--private", action="store_true",
                    help="Namen von Figuren/Einheiten der Vorlage erlauben (nur für private Themes!)")
    ap.add_argument("--themed-icons", action="store_true",
                    help="Icons als Motive aus der Bildwelt der Vorlage (LLM je Icon) statt Katalog + Stilblatt")
    ap.add_argument("--no-art", dest="art", action="store_false",
                    help="ohne Bildplan (keine Icons, Texturen, Szenen)")
    ap.add_argument("--vm", default="fedora,ubuntu,artix", help="vmtest: Test-VMs, kommagetrennt")
    ap.add_argument("--variant", help="vmtest: anzuwendende Variante (Standard: die erste)")
    ap.add_argument("--no-reset", dest="reset", action="store_false",
                    help="vmtest: Snapshot clean nicht zurücksetzen")
    a = ap.parse_args()
    a.no_art = not a.art
    if a.command == "vmtest":
        a.out = a.out or a.request
        return cmd_vmtest(a)
    if a.command in ("build", "bench-art"):
        a.out = a.out or a.request
        return cmd_build(a) if a.command == "build" else cmd_bench_art(a)
    if not a.request or not a.out:
        ap.error("Stilbeschreibung und -o nötig")
    if a.command == "design":
        cmd_design(a)
        return 0
    if a.command == "bench":
        return cmd_bench(a)
    if a.command == "bench-art":
        return cmd_bench_art(a)
    s = cmd_design(a)
    return cmd_build(a, s)


if __name__ == "__main__":
    sys.exit(main())
