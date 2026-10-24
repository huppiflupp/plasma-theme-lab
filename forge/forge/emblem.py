"""Embleme: eine Geometrie, zwei Renderer.

Jede Form ist eine Liste einfacher Polygone ohne Löcher (Ringe werden aus
Vierecken zusammengesetzt). Daraus entsteht entweder ein flaches SVG, das
Inkscape rastert, oder ein extrudiertes Metallobjekt, das Blender rendert.
"""
import json
import math
import os
import shutil
import subprocess
import tempfile

from .palette import mix, shift


def _ring(r1, r2, n=48, a0=0, a1=360):
    polys = []
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * i / n)
        t1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        polys.append([(r2 * math.cos(t0), r2 * math.sin(t0)), (r2 * math.cos(t1), r2 * math.sin(t1)),
                      (r1 * math.cos(t1), r1 * math.sin(t1)), (r1 * math.cos(t0), r1 * math.sin(t0))])
    return polys


def _regular(n, r, rot=-90):
    return [(r * math.cos(math.radians(rot + 360 * i / n)), r * math.sin(math.radians(rot + 360 * i / n)))
            for i in range(n)]


def shapes(kind):
    """Polygone im Bereich -1..1, y nach unten."""
    if kind == "star":
        pts = []
        for i in range(10):
            r = 1.0 if i % 2 == 0 else 0.42
            a = math.radians(-90 + 36 * i)
            pts.append((r * math.cos(a), r * math.sin(a) + 0.05))
        return [pts]
    if kind == "gear":
        pts = []
        teeth = 10
        for i in range(teeth * 4):
            a = math.radians(360 * i / (teeth * 4))
            r = 1.0 if i % 4 in (1, 2) else 0.8
            pts.append((r * math.cos(a), r * math.sin(a)))
        return [pts]
    if kind == "shield":
        return [[(-0.85, -0.9), (0.85, -0.9), (0.85, 0.05), (0.55, 0.6), (0, 1.0),
                 (-0.55, 0.6), (-0.85, 0.05)]]
    if kind == "hexagon":
        return [_regular(6, 1.0, -90)]
    if kind == "chevron":
        return [[(-1, -0.55), (0, 0.15), (1, -0.55), (1, -0.05), (0, 0.65), (-1, -0.05)],
                [(-1, 0.25), (0, 0.95), (1, 0.25), (1, 0.55), (0, 1.0), (-1, 0.55)]]
    if kind == "diamond":
        return [[(0, -1), (0.7, 0), (0, 1), (-0.7, 0)]]
    if kind == "lightning":
        return [[(0.15, -1), (-0.6, 0.15), (-0.05, 0.15), (-0.25, 1), (0.6, -0.2), (0.05, -0.2),
                 (0.35, -1)]]
    if kind == "crosshair":
        return _ring(0.62, 0.8) + [[(-0.07, -1), (0.07, -1), (0.07, -0.3), (-0.07, -0.3)],
                                   [(-0.07, 0.3), (0.07, 0.3), (0.07, 1), (-0.07, 1)],
                                   [(-1, -0.07), (-0.3, -0.07), (-0.3, 0.07), (-1, 0.07)],
                                   [(0.3, -0.07), (1, -0.07), (1, 0.07), (0.3, 0.07)],
                                   _regular(4, 0.12, 45)]
    if kind == "wing":
        polys = []
        for side in (-1, 1):
            for k in range(4):
                y0 = -0.45 + k * 0.28
                polys.append([(side * 0.18, y0), (side * (1.0 - k * 0.18), y0 - 0.12),
                              (side * (0.95 - k * 0.18), y0 + 0.1), (side * 0.18, y0 + 0.2)])
        polys.append(_regular(6, 0.24, 0))
        return polys
    return _ring(0.0001, 1.0, n=64)   # circle


def svg(kind, palette, size=512):
    """Flaches Emblem: Metallverlauf in Akzentfarbe, dunkle Kontur."""
    base = palette["accent"]
    hi, lo = shift(base, 0.22), shift(base, -0.22)
    edge = mix(palette["border"], "#000000", 0.3)
    s = size * 0.44
    c = size / 2

    def pts(poly):
        return " ".join(f"{c + x * s:.2f},{c + y * s:.2f}" for x, y in poly)
    body = "\n".join(f'  <polygon points="{pts(p)}"/>' for p in shapes(kind))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
 <defs>
  <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="{hi}"/><stop offset="0.48" stop-color="{base}"/>
   <stop offset="0.52" stop-color="{lo}"/><stop offset="1" stop-color="{base}"/>
  </linearGradient>
 </defs>
 <g fill="url(#metal)" stroke="{edge}" stroke-width="{size * 0.012:.1f}" stroke-linejoin="round">
{body}
 </g>
</svg>
'''


def render_inkscape(kind, palette, dst, size=512):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "emblem.svg")
        with open(src, "w") as f:
            f.write(svg(kind, palette, size))
        subprocess.run(["inkscape", src, "--export-type=png", f"--export-filename={dst}",
                        f"--export-width={size}"], check=True, capture_output=True, timeout=120)
    return dst


BLENDER_SCRIPT = r'''
import bpy, json, sys, math
args = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
verts, faces = [], []
for poly in args["polys"]:
    i0 = len(verts)
    verts += [(x, -y, 0.0) for x, y in poly]
    faces.append(list(range(i0, len(verts))))
mesh = bpy.data.meshes.new("emblem"); mesh.from_pydata(verts, [], faces); mesh.update()
ob = bpy.data.objects.new("emblem", mesh); sc.collection.objects.link(ob)
sol = ob.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.22; sol.offset = 1
bev = ob.modifiers.new("bevel", "BEVEL"); bev.width = 0.035; bev.segments = 3
bev.limit_method = "ANGLE"
mat = bpy.data.materials.new("metal"); mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (*args["color"], 1)
bsdf.inputs["Metallic"].default_value = 0.85
bsdf.inputs["Roughness"].default_value = 0.32
ob.data.materials.append(mat)
ob.rotation_euler = (math.radians(14), math.radians(-10), 0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.55; cam.location = (0, 0, 6)
sc.camera = cam
for name, loc, energy, col in [("key", (-3, 3, 5), 900, (1, 0.97, 0.92)),
                               ("rim", (3, -2, 2.5), 500, tuple(args["glow"])),
                               ("fill", (2, 3, 4), 250, (0.8, 0.85, 1))]:
    L = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
    L.data.energy = energy; L.data.size = 3; L.data.color = col; L.location = loc
    L.rotation_euler = (0, 0, 0)
    c = L.constraints.new("TRACK_TO"); c.target = ob
    sc.collection.objects.link(L)
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
sc.render.engine = "CYCLES"; sc.cycles.samples = args["samples"]; sc.cycles.device = "CPU"
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = args["size"]
sc.render.filepath = args["dst"]; sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
bpy.ops.render.render(write_still=True)
'''


def render_blender(kind, palette, dst, size=512, samples=48):
    if not shutil.which("blender"):
        raise RuntimeError("blender nicht gefunden")

    def lin(h):
        from .palette import rgb
        return [((v / 255) ** 2.2) for v in rgb(h)]
    args = {"polys": shapes(kind), "color": lin(palette["accent"]), "glow": lin(palette["glow"]),
            "size": size, "samples": samples, "dst": os.path.abspath(dst)}
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "emblem.py")
        with open(script, "w") as f:
            f.write(BLENDER_SCRIPT)
        r = subprocess.run(["blender", "-b", "--factory-startup", "-P", script, "--", json.dumps(args)],
                           capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not os.path.exists(dst):
        raise RuntimeError("Blender-Render fehlgeschlagen: " + (r.stderr or r.stdout)[-800:])
    return dst


def render(kind, how, palette, dst, log=print):
    """Rendert mit dem gewünschten Werkzeug; fällt Blender aus, nimmt Inkscape."""
    if how == "blender":
        try:
            return render_blender(kind, palette, dst), "blender"
        except Exception as e:  # noqa: BLE001
            log(f"  Blender ging nicht ({str(e)[:200]}), nehme Inkscape")
    return render_inkscape(kind, palette, dst), "inkscape"
