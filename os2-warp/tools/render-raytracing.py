#!/usr/bin/env python3
"""The shared parts of Warp Legacy's ray-traced backdrops (POV-Ray).

The first series (five scenes, 26.10.2026) was replaced by the drafts the
user chose from: tools/raytracing-entwuerfe.py renders those and puts them
into wallpapers/. What stays here, used by it: the materials (HEAD), the
render settings, and the statue's mesh: the Georgia Tech horse read from
its PLY and posed into a Lipizzaner's levade.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT.parent / "wallpaper" / "warp-legacy" / "raytracing"
W, H = 3840, 2160
AA = "+A0.02 +AM2 +R5 +J0.8"

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
    # It stands on its hind hooves: their lowest points over the origin,
    # so that on a plinth they meet its top (not beside it in the air).
    hooves = P[P[:, 1] < 0.02]
    P[:, 0] -= hooves[:, 0].mean()
    P[:, 2] -= hooves[:, 2].mean()
    return P


def horse_inc(pose="stand"):
    """The horse as an include, 1 unit high, hooves on y = 0, head towards
    -x (to the left of the camera); cached beside the PLY."""
    import numpy as np
    inc = MODELS / "gatech-horse" / f"horse-{pose}-v2.inc"
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


if __name__ == "__main__":
    print("The backdrops are rendered by tools/raytracing-entwuerfe.py (--build).")
