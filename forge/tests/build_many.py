#!/usr/bin/env python3
"""Builds many specifications without ComfyUI and checks every package.

    tests/build_many.py <target folder> spec1.json spec2.json …

Catches generator faults in unusual combinations that a single preview never
shows. Procedural wallpapers, emblems through Inkscape (fast)."""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from forge import build, check  # noqa: E402

out_root = sys.argv[1]
bad = 0
for i, path in enumerate(sys.argv[2:]):
    s = json.load(open(path))
    s["emblem"]["render"] = "inkscape"
    out = os.path.join(out_root, f"{i:02d}-{s['id']}")
    t0 = time.time()
    try:
        build.build(s, out, use_comfy=False, log=lambda m: None)
        variants = [build.Variant(s, v) for v in s["variants"]]
        errors, notes = check.run(f"{out}/package", variants)
    except Exception:  # noqa: BLE001
        errors, notes = [traceback.format_exc(limit=3)], []
    shape = s["shape"]
    desc = (f"{shape['corner']}/{shape['corner_size']} {shape['bevel']}/{shape['bevel_width']} "
            f"deko {s['decoration']['button_shape']} {s['font']} {s['boot']['plymouth']}/{s['boot']['grub']}")
    status = "OK " if not errors else "ERR"
    bad += bool(errors)
    print(f"{status} {os.path.basename(path):14} {desc} ({time.time() - t0:.0f} s)")
    for e in errors:
        print("     ", e[:400])
print(f"\n{len(sys.argv) - 2 - bad}/{len(sys.argv) - 2} packages without errors")
