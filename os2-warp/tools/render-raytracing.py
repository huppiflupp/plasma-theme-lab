#!/usr/bin/env python3
"""Ray-traced backdrops in the 1990s manner, rendered with POV-Ray.

The "Chrome Spheres" picture used to come from the image model, with the
image model's mistakes (reflections that do not match, a horizon that
bends). These are traced for real: chrome, glass and a chessboard, the
scenes below at several times of day. Each scene gives a day picture
(wallpapers/<stem>.jpg) and a night picture (<stem>-dark.jpg), which
build.py puts into the package as images/ and images_dark/: Plasma shows
the night one under a dark colour scheme.

    render-raytracing.py [--preview] [stem[:time] ...]   default: all missing

Needs povray (3.7). The .pov sources and the full PNGs go to
../wallpaper/warp-legacy/raytracing/ (outside the repository); the record
of every picture (scene, time, renderer, settings, seconds) to the JSON
beside the JPEG.
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "wallpapers"
RAW = ROOT.parent / "wallpaper" / "warp-legacy" / "raytracing"
W, H = 3840, 2160

# ---- times of day ------------------------------------------------------
# sun: elevation and azimuth in degrees (azimuth 0 = from behind the camera,
# positive = from the right), colour and strength; sky: colour at the
# horizon and at the zenith; fog: the haze that swallows the far squares.
TIMES = {
    "morgen": dict(sun=(14, -55), sun_rgb=(1.0, 0.84, 0.68), sun_k=1.25, amb=0.10,
                   horizon=(0.98, 0.84, 0.72), zenith=(0.36, 0.56, 0.86), stars=False),
    "mittag": dict(sun=(52, -30), sun_rgb=(1.0, 0.98, 0.94), sun_k=1.35, amb=0.12,
                   horizon=(0.70, 0.83, 0.98), zenith=(0.05, 0.20, 0.78), stars=False),
    "abend": dict(sun=(7, 60), sun_rgb=(1.0, 0.62, 0.34), sun_k=1.3, amb=0.08,
                  horizon=(1.0, 0.56, 0.30), zenith=(0.16, 0.14, 0.42), stars=False),
    "nacht": dict(sun=(34, 35), sun_rgb=(0.55, 0.64, 0.86), sun_k=0.55, amb=0.05,
                  horizon=(0.07, 0.11, 0.24), zenith=(0.0, 0.01, 0.05), stars=True),
}

# ---- materials -----------------------------------------------------------
HEAD = """#version 3.7;
global_settings { assumed_gamma 1.0 max_trace_level 24 adc_bailout 0.003 }
#declare Chrome = texture { pigment { rgb <0.80, 0.82, 0.86> }
  finish { ambient 0 diffuse 0.03 reflection { 0.88 metallic } specular 0.9 roughness 0.0015 metallic } }
#declare Gold = texture { pigment { rgb <0.86, 0.62, 0.22> }
  finish { ambient 0 diffuse 0.08 reflection { 0.75 metallic } specular 0.8 roughness 0.003 metallic } }
#declare Glass = material {
  texture { pigment { rgbf <0.97, 0.99, 1.0, 0.96> }
    finish { ambient 0 diffuse 0 specular 0.9 roughness 0.0008 reflection { 0.04, 1 fresnel on } conserve_energy } }
  interior { ior 1.5 fade_distance 4 fade_power 1001 fade_color <0.75, 0.9, 1.0> } }
#declare Blue = texture { pigment { rgb <0.04, 0.12, 0.55> }
  finish { ambient 0 diffuse 0.6 specular 0.8 roughness 0.003 reflection { 0.04, 0.30 fresnel on } } }
#declare Lacquer = texture { pigment { rgb <0.72, 0.05, 0.04> }
  finish { ambient 0 diffuse 0.65 specular 0.7 roughness 0.004 reflection { 0.02, 0.25 fresnel on } } }
#declare Marble = texture {
  pigment { marble turbulence 1.6 omega 0.62 lambda 2.2 scale <0.9, 2.4, 0.9> rotate <12, 0, 25>
    color_map { [0.00 rgb <0.94, 0.93, 0.90>] [0.80 rgb <0.90, 0.89, 0.86>]
                [0.90 rgb <0.62, 0.62, 0.64>] [0.95 rgb <0.40, 0.41, 0.44>] [1.00 rgb <0.92, 0.91, 0.88>] } }
  finish { ambient 0 diffuse 0.78 specular 0.35 roughness 0.02 reflection { 0.02, 0.10 fresnel on } } }
#declare Board = texture {
  pigment { checker rgb <0.86, 0.86, 0.84>, rgb <0.025, 0.025, 0.03> scale 2 translate <0, 1, 0> }
  finish { ambient 0 diffuse 0.72 specular 0.5 roughness 0.006 reflection { 0.04, 0.30 fresnel on } } }
#declare BoardIOR = interior { ior 1.5 }
// A square pyramid, apex up, as a closed mesh (glass needs a closed solid).
#macro Pyramid(B, Ht)
  mesh { triangle { <-B, 0, -B>, <B, 0, -B>, <0, Ht, 0> } triangle { <B, 0, -B>, <B, 0, B>, <0, Ht, 0> }
         triangle { <B, 0, B>, <-B, 0, B>, <0, Ht, 0> } triangle { <-B, 0, B>, <-B, 0, -B>, <0, Ht, 0> }
         triangle { <-B, 0, -B>, <B, 0, -B>, <B, 0, B> } triangle { <-B, 0, -B>, <B, 0, B>, <-B, 0, B> }
         inside_vector y }
#end
"""


def vec(t):
    return "<" + ", ".join(f"{x:.4f}" for x in t) + ">"


def sky(t):
    """Sky, sun and haze for a time of day."""
    T = TIMES[t]
    el, az = map(math.radians, T["sun"])
    d = 10000
    sun = (d * math.cos(el) * math.sin(az), d * math.sin(el), -d * math.cos(el) * math.cos(az))
    k = T["sun_k"]
    stars = ""
    if T["stars"]:
        # Stars: a fine granite pattern cut down to its brightest specks.
        stars = """
  pigment { granite scale 0.006
    color_map { [0.00 rgbt <0, 0, 0, 1>] [0.83 rgbt <0, 0, 0, 1>] [0.86 rgbt <0.9, 0.92, 1.0, 0.0>] [1.0 rgbt <1, 1, 1, 0>] } }"""
    return f"""
sky_sphere {{
  pigment {{ gradient y color_map {{ [0.0 rgb {vec(T['horizon'])}] [0.10 rgb {vec(tuple((a + b) / 2 for a, b in zip(T['horizon'], T['zenith'])))}] [0.42 rgb {vec(T['zenith'])}] [1.0 rgb {vec(T['zenith'])}] }} }}{stars}
}}
light_source {{ {vec(sun)} rgb {vec(tuple(c * k for c in T['sun_rgb']))} parallel point_at <0, 0, 0>
  area_light <260, 0, 0>, <0, 0, 260>, 5, 5 adaptive 1 jitter circular orient }}
// The sky's light from above, without shadows: what radiosity would give.
light_source {{ <0, 5000, 0> rgb {vec(tuple(c * T['amb'] * 2.2 for c in T['zenith']))} shadowless }}
light_source {{ <0, 900, -3000> rgb {vec(tuple(c * T['amb'] * 1.6 for c in T['horizon']))} shadowless }}
fog {{ fog_type 2 distance 200 color rgb {vec(T['horizon'])} fog_offset 0 fog_alt 3 }}
"""


CAMERA = """
camera { location <0, 2.35, -11.5> look_at <1.2, 1.35, 0> angle 52 right x * image_width / image_height }
"""


def floor():
    return "plane { y, 0 texture { Board } interior { BoardIOR } }\n"


# ---- scenes ----------------------------------------------------------------
def chrom(t):
    """The old picture, traced: chrome spheres and glass pyramids."""
    return CAMERA + floor() + """
sphere { <2.4, 1.9, 2.2>, 1.9 texture { Chrome } }
sphere { <-0.6, 0.85, 0.6>, 0.85 texture { Chrome } }
sphere { <5.0, 0.95, 0.4>, 0.95 texture { Chrome } }
sphere { <0.9, 0.45, -1.8>, 0.45 texture { Chrome } }
object { Pyramid(0.62, 3.0) rotate y * 30 material { Glass } translate <0.55, 0, 0.6> }
object { Pyramid(0.55, 2.3) rotate y * 12 material { Glass } translate <5.6, 0, 3.6> }
"""


def koerper(t):
    """Geometric bodies: a chrome cube, a glass sphere, a red cone, a torus."""
    return CAMERA + floor() + """
box { <-1, 0, -1>, <1, 2, 1> rotate y * 28 texture { Blue } translate <-0.6, 0, 1.6> }
sphere { <2.3, 1.25, 0.2>, 1.25 material { Glass } }
cone { <0, 0, 0>, 0.9, <0, 2.6, 0>, 0 texture { Lacquer } translate <4.9, 0, 2.8> }
torus { 1.0, 0.32 rotate x * 90 rotate y * -25 texture { Gold } translate <5.2, 1.32, -0.6> }
cylinder { <0, 0, 0>, <0, 3.2, 0>, 0.45 material { Glass } translate <1.6, 0, 3.8> }
sphere { <0.6, 0.38, -2.1>, 0.38 texture { Chrome } }
sphere { <3.8, 0.3, -2.4>, 0.3 texture { Lacquer } }
"""


def statue(t):
    """A marble bust on a column, after the chessboards of the 1990s demos.
    Modelled from blob components (POV-Ray's metaballs), no outside model."""
    return CAMERA + floor() + """
#declare Plinth = union {
  box { <-0.85, 0, -0.85>, <0.85, 0.22, 0.85> }
  cylinder { <0, 0.22, 0>, <0, 1.35, 0>, 0.58 }
  box { <-0.75, 1.35, -0.75>, <0.75, 1.55, 0.75> }
  texture { Marble } }
// A torso in the manner of the antique fragments: no head, no arms, the
// legs broken off at the thighs, a slight contrapposto. Blob components
// (POV-Ray's metaballs), cut flat where the stone broke.
#declare Torso = intersection {
  // The visible size of a component is about half its radius (threshold
  // 0.5, strength 1): the radii are chosen so that the fields overlap and
  // the forms run into each other as in stone.
  blob { threshold 0.5
    sphere { <0, 0, 0>, 1.0, 1 scale <0.78, 0.55, 0.55> translate <0, 0.62, 0> }
    cylinder { <-0.24, 0.55, 0>, <-0.30, -0.2, -0.05>, 0.40, 1 }
    cylinder { < 0.24, 0.55, 0>, < 0.33, -0.2, 0.07>, 0.40, 1 }
    sphere { <0, 0, 0>, 1.0, 1 scale <0.58, 0.62, 0.46> translate <0, 1.08, 0> }
    sphere { <0, 0, 0>, 1.0, 1 scale <0.86, 0.66, 0.56> translate <0, 1.56, 0> }
    sphere { <-0.21, 1.55, -0.20>, 0.45, 0.6 }
    sphere { < 0.21, 1.55, -0.20>, 0.45, 0.6 }
    cylinder { <-0.42, 1.78, 0.02>, <-0.80, 1.42, 0.04>, 0.33, 1 }
    cylinder { < 0.42, 1.78, 0.02>, < 0.80, 1.42, 0.04>, 0.33, 1 }
    cylinder { <0, 1.75, 0.02>, <0, 2.35, 0.0>, 0.30, 1 }
  }
  box { <-1.5, 0.12, -1.5>, <1.5, 2.10, 1.5> }
  plane { <-1, 0, 0>, 0.80 } plane { <1, 0, 0>, 0.80 }
  rotate z * 4
  texture { Marble } }
union { object { Plinth } object { Torso translate y * 1.43 } rotate y * -28 translate <2.2, 0, 1.4> }
sphere { <-0.4, 0.7, 0.4>, 0.7 texture { Chrome } }
sphere { <4.6, 0.55, -0.4>, 0.55 texture { Chrome } }
object { cone { <0, 0, 0>, 0.5, <0, 2.4, 0>, 0 } material { Glass } translate <5.4, 0, 2.6> }
"""


SINK_CAMERA = """
camera { location <-0.5, 4.4, -8.6> look_at <1.2, -0.2, 3.2> angle 56 right x * image_width / image_height }
"""


def sinkhole(t):
    """The chessboard caves in: a round hole with earth walls, tiles slipping
    in, a chrome sphere at the edge."""
    return SINK_CAMERA + """
// The board as a slab with the hole cut out; the pattern is solid, so the
// cut faces show it as well.
difference {
  box { <-400, -0.3, -60>, <400, 0, 600> }
  cylinder { <1.0, -1, 3.0>, <1.0, 1, 3.0>, 3.1 }
  texture { Board } interior { BoardIOR } }
// Earth below the slab, the shaft, and darkness at its bottom (without
// it the sky would show through below the horizon).
difference {
  cylinder { <1.0, -0.3, 3.0>, <1.0, -30, 3.0>, 3.8 }
  cylinder { <1.0, 0, 3.0>, <1.0, -31, 3.0>, 3.1 }
  // Earth at the top, going black with depth.
  texture { pigment { gradient y pigment_map {
      [0.0 rgb 0] [0.55 rgb 0]
      [0.85 granite scale 0.08 color_map { [0 rgb <0.10, 0.07, 0.05>] [1 rgb <0.17, 0.12, 0.08>] }]
      [1.0 granite scale 0.08 color_map { [0 rgb <0.22, 0.16, 0.10>] [0.5 rgb <0.30, 0.22, 0.14>] [1 rgb <0.36, 0.27, 0.18>] }] }
      scale 6 translate y * -6 }
            normal { granite 1.4 scale 0.25 } finish { ambient 0 diffuse 0.75 } } }
disc { <1.0, -12, 3.0>, y, 3.2 pigment { rgb 0 } finish { ambient 0 diffuse 0 } }
// Tiles slipping over the edge into the hole.
#macro Tile(C, P, R) box { <-1, -0.15, -1>, <1, 0.15, 1> rotate R translate P
  texture { pigment { rgb C } finish { ambient 0 diffuse 0.72 specular 0.5 roughness 0.006 reflection { 0.04, 0.3 fresnel on } } } interior { BoardIOR } } #end
Tile(<0.86, 0.86, 0.84>, <-1.55, -0.55, 2.4>, <6, 24, -34>)
Tile(<0.025, 0.025, 0.03>, <3.45, -0.75, 1.9>, <-12, -14, 40>)
Tile(<0.025, 0.025, 0.03>, <0.4, -2.2, 2.6>, <-55, 10, 25>)
Tile(<0.86, 0.86, 0.84>, <1.6, -3.4, 3.4>, <70, 40, 10>)
sphere { <-2.25, 0.78, 0.9>, 0.78 texture { Chrome } }
sphere { <5.6, 1.15, 4.2>, 1.15 texture { Chrome } }
sphere { <3.6, 0.45, -1.6>, 0.45 texture { Chrome } }
object { cone { <0, 0, 0>, 0.55, <0, 2.6, 0>, 0 } material { Glass } translate <-3.6, 0, 5.6> }
"""


SCENES = {"chrom": chrom, "koerper": koerper, "statue": statue, "sinkhole": sinkhole}
# stem: (scene, day time, night time). The day picture names the time of day.
PICTURES = {
    "raytracing-chrom": ("chrom", "mittag", "nacht"),
    "raytracing-chrom-abend": ("chrom", "abend", "nacht"),
    "raytracing-koerper": ("koerper", "morgen", "nacht"),
    "raytracing-statue": ("statue", "abend", "nacht"),
    "raytracing-sinkhole": ("sinkhole", "mittag", "nacht"),
}
AA = "+A0.02 +AM2 +R5 +J0.8"

# ---- the statue's mesh -------------------------------------------------------
# The horse from the Georgia Tech Large Geometric Models Archive
# (sites.cc.gatech.edu/projects/large_models/horse.html, originally a
# Cyberware scan), downloaded once into ../wallpaper/warp-legacy/models/;
# read here as geometry only (binary PLY), never shipped as a mesh.
MODELS = ROOT.parent / "wallpaper" / "warp-legacy" / "models"
HORSE_PLY = MODELS / "gatech-horse" / "horse.ply"


def read_ply(path):
    """Vertices and triangles of a binary big-endian PLY (x, y, z first)."""
    import numpy as np
    data = path.read_bytes()
    end = data.index(b"end_header\n") + len(b"end_header\n")
    head = data[:end].decode("ascii").splitlines()
    nv = int(next(l for l in head if l.startswith("element vertex")).split()[-1])
    nf = int(next(l for l in head if l.startswith("element face")).split()[-1])
    props = [l.split()[1:] for l in head if l.startswith("property") and "list" not in l]
    size = {"float32": "f4", "float": "f4", "uint8": "u1", "uchar": "u1", "int32": "i4"}
    vt = np.dtype([(p[1], ">" + size[p[0]]) for p in props[:sum(1 for _ in props)]])
    v = np.frombuffer(data, vt, nv, end)
    ft = np.dtype([("n", "u1"), ("i", ">i4", 3)])
    f = np.frombuffer(data, ft, nf, end + nv * vt.itemsize)
    assert (f["n"] == 3).all()
    return np.stack([v["x"], v["y"], v["z"]], 1).astype(float), f["i"].astype(int)


def mesh2(P, F, name):
    """A POV-Ray mesh2 with smooth vertex normals."""
    import numpy as np
    N = np.zeros_like(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    vec = lambda a: ",\n".join(f"<{x:.5f},{y:.5f},{z:.5f}>" for x, y, z in a)  # noqa: E731
    faces = ",\n".join(f"<{a},{b},{c}>" for a, b, c in F)
    return (f"#declare {name} = mesh2 {{\n vertex_vectors {{ {len(P)},\n{vec(P)} }}\n"
            f" normal_vectors {{ {len(N)},\n{vec(N)} }}\n face_indices {{ {len(F)},\n{faces} }}\n}}\n")


def levade(P):
    """The scan stands; a Lipizzaner's levade rears: the front legs folded
    (knee, then elbow), the body raised about the hind hooves, which bends
    the hindquarters down over the hocks. Rotations in the side plane with
    soft bands, so the skin stretches instead of tearing."""
    import numpy as np

    def smooth(a, b, t):          # 0 at a, 1 at b
        u = np.clip((t - a) / (b - a), 0, 1)
        return u * u * (3 - 2 * u)

    def rot(Q, cx, cy, deg, w):
        a = math.radians(deg)
        x, y = Q[:, 0] - cx, Q[:, 1] - cy
        R = Q.copy()
        R[:, 0] = cx + x * math.cos(a) - y * math.sin(a)
        R[:, 1] = cy + x * math.sin(a) + y * math.cos(a)
        return Q + w[:, None] * (R - Q)

    P = P.copy()
    front = smooth(0.06, -0.02, P[:, 0]) * smooth(0.50, 0.42, P[:, 1])
    O = P.copy()
    # The two front legs, left and right of the body, each about its own
    # knee and elbow (read from the scan: the leg's middle at that height).
    for side, knee_deg, elbow_deg in ((1, 112, -60), (-1, 96, -48)):
        leg = front * smooth(-0.02 * side, 0.02 * side, O[:, 2]) if side > 0 else \
            front * smooth(0.02, -0.02, O[:, 2])
        at = lambda h: O[(leg > 0.9) & (abs(O[:, 1] - h) < 0.02), 0].mean()  # noqa: E731
        kx, ex = at(0.24), at(0.44)
        P = rot(P, kx, 0.24, knee_deg, leg * smooth(0.28, 0.20, O[:, 1]))   # the cannon folded back under
        P = rot(P, ex, 0.46, elbow_deg, leg)                                # the forearm raised forward
    P = rot(P, 0.46, 0.0, -34, np.ones(len(P)))                 # the whole horse up on its hind legs
    P[:, 1] -= P[:, 1].min()
    P /= P[:, 1].max()
    return P


def horse_inc(pose="stand"):
    """The horse as an include, 1 unit high, hooves on y = 0, head towards
    -x (to the left of the camera); cached beside the PLY."""
    import numpy as np
    inc = MODELS / "gatech-horse" / f"horse-{pose}.inc"
    if inc.exists():
        return inc
    P, F = read_ply(HORSE_PLY)
    P = np.stack([-P[:, 1], P[:, 2], P[:, 0]], 1)        # PLY z up, y along the body
    P -= [(P[:, 0].min() + P[:, 0].max()) / 2, P[:, 1].min(), (P[:, 2].min() + P[:, 2].max()) / 2]
    P /= P[:, 1].max()
    if pose == "levade":
        P = levade(P)
    inc.write_text(mesh2(P, F, "Horse"))
    return inc


def render(scene, t, png, preview=False):
    src = RAW / f"{scene}-{t}.pov"
    src.write_text(HEAD + sky(t) + SCENES[scene](t))
    w, h = (960, 540) if preview else (W, H)
    cmd = ["povray", f"+I{src}", f"+O{png}", f"+W{w}", f"+H{h}", "+FN", "-D", "-V", "+WT14"] + AA.split()
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not png.exists():
        raise RuntimeError(f"povray {src.name}: {r.stderr[-1500:]}")
    return time.time() - t0, " ".join(cmd[1:])


def main(args):
    preview = "--preview" in args
    names = [a for a in args if not a.startswith("--")]
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    done = {}
    for stem, (scene, day, night) in PICTURES.items():
        for suffix, t in (("", day), ("-dark", night)):
            name = stem + suffix
            wanted = (not names and not (OUT / f"{name}.jpg").exists() or name in names
                      or f"{scene}:{t}" in names or preview and not names)
            if not wanted:
                continue
            key = (scene, t)
            png = RAW / f"{scene}-{t}{'-preview' if preview else ''}.png"
            if key not in done:
                seconds, cmd = render(scene, t, png, preview)
                done[key] = seconds
                print(f"  {scene}-{t}: {seconds:.0f} s")
            if preview:
                continue
            Image.open(png).convert("RGB").save(OUT / f"{name}.jpg", quality=92, optimize=True, progressive=True)
            (OUT / f"{name}.json").write_text(json.dumps({
                "renderer": next(line for line in subprocess.run(["povray", "--version"], capture_output=True,
                                 text=True).stderr.splitlines() if line.startswith("POV-Ray")),
                "script": "os2-warp/tools/render-raytracing.py", "scene": scene, "time_of_day": t,
                "source": f"wallpaper/warp-legacy/raytracing/{scene}-{t}.pov", "size": [W, H],
                "antialias": AA, "seed": None, "seconds": round(done[key], 1),
                "host": "245k (Intel Core Ultra 5 245K, 14 threads, CPU)"}, indent=2, ensure_ascii=False) + "\n")
            print(f"  {name}.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
