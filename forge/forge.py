#!/usr/bin/env python3
"""Theme Forge: a local LLM designs a Plasma theme from a style description.

    ./forge.py all "Red Alert 2" -o out/ra2          # design, build, check, preview
    ./forge.py design "style" -o out/x                # spec.json only (LLM)
    ./forge.py build out/x                            # build the package from spec.json
    ./forge.py bench "style" -n 5 -o out/bench        # measure reliability (LLM part only)
    ./forge.py vmtest out/x [--vm fedora,ubuntu,artix] [--lang en]
                                                      # install/apply/remove in the lab VMs
    ./forge.py review out/x [--review-vm artix] [--rounds 2]
                                                      # the vision model judges and repairs
    ./forge.py all "style" -o out/x --live-vm fedora --review
                                                      # for a recording: the theme grows in the VM

Environment: FORGE_LLM (default http://127.0.0.1:8090/v1), FORGE_COMFY (default the local
ComfyUI 127.0.0.1:8189), FORGE_LLM_SERVICE (stopped for image runs, see forge/gpu.py).
Everything forge writes (descriptions, READMEs, store texts) is in English.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forge import artplan, build, check, designer, events, live, llm, preview, review, spec as specmod, vmtest  # noqa: E402


def log(msg):
    print(msg, flush=True)


def cmd_design(a):
    os.makedirs(a.out, exist_ok=True)
    s = designer.run(a.request, avoid=a.avoid, log=log, seed=a.seed)
    with open(f"{a.out}/spec.json", "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    log(f"spec.json written ({s['_meta']['attempts']} LLM attempt(s))")
    if a.art:
        p = artplan.plan(s, private=a.private, log=log, seed=a.seed, themed_icons=a.themed_icons)
        with open(f"{a.out}/artplan.json", "w") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)
        log("artplan.json written")
    return s


def cmd_build(a, s=None):
    if s is None:
        s = json.load(open(f"{a.out}/spec.json"))
    errs = specmod.validate(s, a.avoid)
    if errs:
        log("spec.json invalid:\n- " + "\n- ".join(errs))
        return 1
    t0 = time.time()
    plan = None
    if os.path.exists(f"{a.out}/artplan.json") and not a.no_art:
        plan = json.load(open(f"{a.out}/artplan.json"))
    on_stage = None
    if getattr(a, "live_vm", None):
        on_stage = live.Live(a.live_vm, a.out, reset=a.reset, lang=None if a.lang == "keep" else a.lang,
                             variant=a.variant, log=log)
    report = build.build(s, a.out, use_comfy=not a.no_comfy, log=log, plan=plan, on_stage=on_stage)
    if plan:      # the image check may have rewritten motifs
        with open(f"{a.out}/artplan.json", "w") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
    variants = [build.Variant(s, v) for v in s["variants"]]
    pkg = f"{a.out}/package"
    errors, notes = check.run(pkg, variants)
    for n in notes:
        log(f"Note: {n}")
    for e in errors:
        log(f"ERROR: {e}")
    sheet = preview.sheet(pkg, variants, s, f"{a.out}/preview.jpg")
    report.update({"errors": errors, "notes": notes, "seconds": round(time.time() - t0, 1)})
    for v in report["variants"].values():
        v.pop("palette", None)
    with open(f"{a.out}/report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log(f"Package: {pkg}\nPreview: {sheet}\n{'OK' if not errors else f'{len(errors)} error(s)'} "
        f"in {report['seconds']} s")
    return 1 if errors else 0


def cmd_bench(a):
    """The LLM chain alone, n times: how often does a valid spec come out,
    after how many attempts, and does it pass the style check of the model?"""
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
            log(f"  run {i}: {e}")
        else:
            err = None
        style = style_check(s, a.expect) if s and a.expect else []
        rows.append({"run": i, "valid": ok, "attempts": attempts, "style_errors": style, "error": err,
                     "auto": bool(s and s.get("_auto")),
                     "seconds": round(time.time() - t0, 1)})
        log(f"run {i}: valid={ok} attempts={attempts} style={'ok' if not style else style} "
            f"({rows[-1]['seconds']} s)")
    valid = sum(r["valid"] for r in rows)
    styled = sum(r["valid"] and not r["style_errors"] for r in rows)
    first = sum(r["attempts"] == 1 for r in rows)
    auto = sum(r["auto"] for r in rows)
    summary = {"runs": a.n, "valid": valid, "first_try": first, "style_ok": styled, "auto_fixed": auto,
               "rows": rows}
    with open(f"{a.out}/bench.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"\nvalid {valid}/{a.n}, at the first attempt {first}/{a.n}, style check passed {styled}/{a.n}, "
        f"of them with automatic fixes {auto}")
    return 0 if styled == a.n else 1


def cmd_bench_art(a):
    """Make the art plan n times from one fixed spec.json (from -o): how often
    does it succeed, in how many rounds, how often do the automatic fixes step
    in, and do the scenes name the agreed elements?"""
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
        log(f"run {i}: {json.dumps(row, ensure_ascii=False)[:300]}")
    ok = sum(r["ok"] for r in rows)
    auto = sum(bool(r.get("auto")) for r in rows)
    with open(f"{a.out}/bench-art.json", "w") as f:
        json.dump({"runs": a.n, "ok": ok, "auto": auto, "rows": rows}, f, indent=2, ensure_ascii=False)
    log(f"\nart plan succeeded {ok}/{a.n}, with automatic fixes {auto}")
    return 0 if ok == a.n else 1


def style_check(s, expect_path):
    """Expectations of a model (JSON): hue ranges per variant, mode, allowed
    corner shapes. Checks whether the LLM hit the model."""
    import colorsys
    from forge.palette import rgb
    exp = json.load(open(expect_path))
    errs = []
    if "corner" in exp and s["shape"]["corner"] not in exp["corner"]:
        errs.append(f"corner {s['shape']['corner']} not in {exp['corner']}")
    if "variants" in exp and len(s["variants"]) < exp["variants"]["min"]:
        errs.append(f"only {len(s['variants'])} variant(s)")
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
            errs.append(f"no variant matches \"{want['name']}\"")
    return errs


def cmd_vmtest(a):
    """The built package in the lab VMs (forge/vmtest.py): Fedora, Ubuntu, Artix/OpenRC,
    in an English session unless --lang says otherwise."""
    reports = vmtest.run(a.out, envs=a.vm.split(","), variant=a.variant, reset=a.reset,
                         lang=None if a.lang == "keep" else a.lang, log=log)
    bad = [r["env"] for r in reports if r["errors"]]
    log(f"VM test: {len(reports) - len(bad)} of {len(reports)} without errors" + (f" (errors: {', '.join(bad)})" if bad else ""))
    return 1 if bad else 0


def cmd_review(a):
    """The vision model looks at decoration, wallpapers and (with --vm) the desktop in a lab VM,
    repairs what it can and builds again (forge/review.py)."""
    s = json.load(open(f"{a.out}/spec.json"))
    plan = json.load(open(f"{a.out}/artplan.json")) if os.path.exists(f"{a.out}/artplan.json") else None
    res = review.review(a.out, s, plan, rounds=a.rounds, vm=a.vm_review, lang=None if a.lang == "keep" else a.lang,
                        use_comfy=not a.no_comfy, log=log, seed=a.seed)
    log("review: " + ("no major issues left" if not res["left"] else f"{len(res['left'])} major issue(s) left: "
                      + "; ".join(res["left"])[:600]))
    return 1 if res["left"] else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["design", "build", "all", "bench", "bench-art", "vmtest", "review"])
    ap.add_argument("request", nargs="?", help="style description (design/all/bench) or output folder (build)")
    ap.add_argument("-o", "--out")
    ap.add_argument("--avoid", action="append", default=[], help="additional forbidden terms")
    ap.add_argument("--no-comfy", action="store_true", help="procedural wallpapers instead of ComfyUI")
    ap.add_argument("--seed", type=int)
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--expect", help="style expectations (JSON) for bench")
    ap.add_argument("--private", action="store_true",
                    help="allow names of characters/units of the model (private themes only!)")
    ap.add_argument("--themed-icons", action="store_true",
                    help="icons as motifs from the model's imagery (LLM per icon) instead of catalogue + style sheet")
    ap.add_argument("--no-art", dest="art", action="store_false",
                    help="without an art plan (no icons, textures, scenes)")
    ap.add_argument("--vm", default="fedora,ubuntu,artix", help="vmtest: lab VMs, comma-separated")
    ap.add_argument("--lang", default="en",
                    help="vmtest: session language for the screenshots (default en; keep: the VM's own)")
    ap.add_argument("--variant", help="vmtest: variant to apply (default: the first)")
    ap.add_argument("--rounds", type=int, default=2, help="review: repair rounds at most (0 = only look)")
    ap.add_argument("--review-vm", dest="vm_review", help="review: also judge the desktop in this lab VM "
                    "(fedora, ubuntu or artix)")
    ap.add_argument("--events", help="event log (JSONL) for overlays; default <out>/events.jsonl")
    ap.add_argument("--live-vm", dest="live_vm", help="build/all: play every build stage into this lab VM "
                    "(fedora, ubuntu or artix) — for a recording (forge/live.py)")
    ap.add_argument("--review", dest="do_review", action="store_true",
                    help="all: after the build, the visual review with repairs (forge/review.py)")
    ap.add_argument("--no-reset", dest="reset", action="store_false",
                    help="vmtest: do not revert to the snapshot clean")
    a = ap.parse_args()
    a.no_art = not a.art
    if a.command in ("vmtest", "review", "build", "bench-art"):
        a.out = a.out or a.request
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        events.open_log(a.events or f"{a.out}/events.jsonl")
    if a.command == "review":
        return cmd_review(a)
    if a.command == "vmtest":
        a.out = a.out or a.request
        return cmd_vmtest(a)
    if a.command in ("build", "bench-art"):
        a.out = a.out or a.request
        return cmd_build(a) if a.command == "build" else cmd_bench_art(a)
    if not a.request or not a.out:
        ap.error("a style description and -o are needed")
    if a.command == "design":
        cmd_design(a)
        return 0
    if a.command == "bench":
        return cmd_bench(a)
    if a.command == "bench-art":
        return cmd_bench_art(a)
    s = cmd_design(a)
    rc = cmd_build(a, s)
    if a.do_review:
        a.vm_review = a.vm_review or a.live_vm
        rc = cmd_review(a) or rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
