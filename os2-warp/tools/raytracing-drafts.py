#!/usr/bin/env python3
"""Thirty drafts of ray-traced backdrops (POV-Ray), for the user to choose by number.

The second round after tools/render-raytracing.py: clearer (no ground fog,
the haze only swallows the far horizon), smaller objects with more floor
and sky, in the manner of the old "Chrome Spheres" picture and varied from
there: polyhedra lying about or floating, a marble Lipizzaner in a levade on
a plinth (the Georgia Tech horse scan, posed: render-raytracing.py), a
singularity in the floor that the chessboard runs into, a green wireframe
grid as the other floor, four times of day and a night with the moon.

    raytracing-drafts.py                 all drafts, 1280x720, contact sheet, LISTE.md
    raytracing-drafts.py 4 17            only these
    raytracing-drafts.py --final 17      draft 17 at 3840x2160 with its day/night partner

Everything goes to ../wallpaper/warp-legacy/raytracing/entwuerfe/ (outside
the repository); nothing here touches the theme until a draft is chosen.
"""
import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("rt", HERE / "render-raytracing.py")
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)

OUT = rt.RAW / "entwuerfe"
CACHE = rt.RAW / "cache"
FONT = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"

# ---- times of day ------------------------------------------------------------
# sun/moon: (elevation, azimuth) in degrees, positive azimuth = from the
# right; the sun shines from behind the camera, the moon from ahead; light colour and strength;
# fill: the sky's shadowless light, kept low for contrast; sky at the horizon
# and the zenith.
TIMES = {
    "morning": dict(light=(16, -70), rgb=(1.0, 0.86, 0.70), k=1.35, fill=0.05,
                   horizon=(0.97, 0.82, 0.68), zenith=(0.22, 0.42, 0.80)),
    "noon": dict(light=(55, -40), rgb=(1.0, 0.98, 0.95), k=1.4, fill=0.06,
                   horizon=(0.62, 0.78, 0.98), zenith=(0.02, 0.14, 0.62)),
    "evening": dict(light=(8, 62), rgb=(1.0, 0.60, 0.32), k=1.35, fill=0.04,
                  horizon=(1.0, 0.52, 0.26), zenith=(0.12, 0.10, 0.36)),
    "night": dict(light=(6, -9), rgb=(0.62, 0.70, 0.92), k=0.55, fill=0.025,
                  horizon=(0.05, 0.08, 0.18), zenith=(0.0, 0.005, 0.03)),
}


def sky(t, moon=False, stars=None, black=False, moon_vec=None, cam=None):
    T = TIMES[t]
    el, az = map(math.radians, T["light"])
    d = 10000
    # By day the light comes from behind the camera, to one side; at night
    # from the moon, which stands in view ahead (moon_vec: its direction).
    ahead = 1 if t == "night" else -1
    pos = (d * math.cos(el) * math.sin(az), d * math.sin(el), ahead * d * math.cos(el) * math.cos(az))
    if moon_vec is not None and t == "night":
        pos = tuple(d * c for c in moon_vec)
    stars = t == "night" if stars is None else stars
    hz, zn = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) if black else (T["horizon"], T["zenith"])
    mid = tuple((a + b) / 2 for a, b in zip(hz, zn))
    s = f"""
sky_sphere {{
  pigment {{ gradient y color_map {{ [0.0 rgb {rt.vec(hz)}] [0.08 rgb {rt.vec(mid)}] [0.40 rgb {rt.vec(zn)}] [1.0 rgb {rt.vec(zn)}] }} }}"""
    if stars:
        s += """
  pigment { granite scale 0.005
    color_map { [0.00 rgbt <0, 0, 0, 1>] [0.84 rgbt <0, 0, 0, 1>] [0.87 rgbt <0.9, 0.93, 1.0, 0.0>] [1.0 rgbt <1, 1, 1, 0>] } }"""
    s += "\n}\n"
    light = tuple(c * T["k"] for c in T["rgb"])
    # Soft shadows from the sun; the moon a point, so that its path on the
    # board stays a narrow glitter, not a broad smear.
    soft = "" if t == "night" else "\n  area_light <200, 0, 0>, <0, 0, 200>, 5, 5 adaptive 1 jitter circular orient"
    s += f"light_source {{ {rt.vec(pos)} rgb {rt.vec(light)} parallel point_at <0, 0, 0>{soft} }}\n"
    if moon:
        s += moon_object(tuple(c / d for c in pos), cam)
    if t == "night":
        # The night sky's glow from behind the camera: without it everything
        # in front of the moon would be a silhouette.
        s += "light_source { <-2000, 2500, -6000> rgb <0.16, 0.19, 0.28> shadowless }\n"
    f = T["fill"]
    s += f"light_source {{ <0, 5000, 0> rgb {rt.vec(tuple(c * f * 2.4 for c in (zn if not black else (0.1, 0.2, 0.15))))} shadowless }}\n"
    # Only the far floor fades: a ground haze 0.3 high, thin; the sky and
    # everything standing up stays clear.
    s += f"fog {{ fog_type 2 distance 260 fog_offset 0 fog_alt 0.25 color rgb {rt.vec(hz)} }}\n"
    return s


def moon_object(direction, cam, D=6000.0, radius_deg=0.36):
    """The moon where its light comes from: about 0.7 degrees across (a
    little more than the real 0.5, so that it reads at desktop size),
    highlands and maria from two patterns, craters, darker towards the
    limb (a cylindrical pattern whose axis points at the camera), warm
    white, a faint halo that the floor does not mirror. The floor's own
    gloss makes its reflection, a narrow path (floor(night=True))."""
    loc = cam["loc"] if cam else (0, 2.4, -15)
    P = tuple(l + D * c for l, c in zip(loc, direction))
    r = D * math.tan(math.radians(radius_deg))
    v = tuple(-c for c in direction)              # from the moon towards the camera
    high = ("granite scale 0.35 color_map { [0 rgb <0.80, 0.78, 0.72>] [0.5 rgb <0.95, 0.93, 0.86>] "
            "[1 rgb <1.0, 0.98, 0.92>] }")
    mare = "granite scale 0.6 color_map { [0 rgb <0.50, 0.50, 0.50>] [1 rgb <0.64, 0.63, 0.60>] }"
    craters = ("crackle form <1, 0, 0> scale 0.12 color_map { [0 rgb <0.70, 0.68, 0.64>] [0.06 rgb <0.98, 0.96, 0.90>] "
               "[1 rgb <0.98, 0.96, 0.90>] }")
    surface = (f"bozo turbulence 0.6 omega 0.55 scale 0.55 pigment_map {{ [0.00 {mare}] [0.42 {mare}] "
               f"[0.50 {high}] [0.80 average pigment_map {{ [1 {high}] [1 {craters}] }}] [1.00 {high}] }}")

    def dim(k):
        return f"average pigment_map {{ [{k:.2f} {surface}] [{1 - k:.2f} rgb 0] }}"
    return f"""#include "transforms.inc"
sphere {{ 0, 1
  texture {{ pigment {{ cylindrical pigment_map {{ [0 {dim(0.62)}] [0.35 {dim(0.88)}] [1 {dim(1.0)}] }} }}
            finish {{ emission 1.25 diffuse 0 ambient 0 }} }}
  transform {{ Point_At_Trans({rt.vec(v)}) }}
  scale {r:.2f} translate {rt.vec(P)} no_shadow }}
disc {{ 0, {rt.vec(v)}, 1
  texture {{ pigment {{ spherical color_map {{ [0 rgbt <1, 1, 1, 1>] [1 rgbt <0.9, 0.92, 1.0, 0.82>] }} }}
            finish {{ emission 0.35 diffuse 0 ambient 0 }} }}
  scale {4.5 * r:.2f} translate {rt.vec(tuple(p + 2.5 * r * c for p, c in zip(P, direction)))} no_shadow no_reflection }}
"""


def moon_direction(cam, sx, el):
    """The direction to put the moon at screen x (0 left .. 1 right) and
    elevation el (degrees): right of the desktop's icons, left of a widget
    at the top right."""
    loc, at, angle = cam["loc"], cam["at"], cam["angle"]
    dx, dz = at[0] - loc[0], at[2] - loc[2]
    yaw = math.atan2(dx, dz)
    az = yaw + math.atan((2 * sx - 1) * math.tan(math.radians(angle) / 2))
    e = math.radians(el)
    return (math.cos(e) * math.sin(az), math.sin(e), math.cos(e) * math.cos(az))


def moon_screen_y(cam, el):
    """Where (0 top .. 1 bottom) the moon's height lands on the screen."""
    loc, at, angle = cam["loc"], cam["at"], cam["angle"]
    pitch = math.atan2(at[1] - loc[1], math.hypot(at[0] - loc[0], at[2] - loc[2]))
    half_v = math.atan(math.tan(math.radians(angle) / 2) * 9 / 16)
    return 0.5 - 0.5 * math.tan(math.radians(el) - pitch) / math.tan(half_v)


# ---- floors --------------------------------------------------------------------
BOARD_FINISH = "finish { ambient 0 diffuse 0.72 specular 0.55 roughness 0.005 reflection { 0.05, 0.38 fresnel on } }"
# At night no highlight of the light source (it floated as a blur over
# the horizon): the moon's path is its reflection, spread by fine bumps.
NIGHT_FINISH = ("finish { ambient 0 diffuse 0.72 specular 0 reflection { 0.05, 0.42 fresnel on } } "
                "normal { bumps 0.035 scale 0.008 }")
GREEN = (0.15, 1.0, 0.35)
WIDTH_4K = 3840


def fade_distance(cell, cam, angle):
    """Where a square of the floor shrinks to about two pixels high at
    3840 px: beyond it the pattern can only alias (the moire at the
    horizon), so it fades into its average there, a mipmap by distance.
    A square at distance d on the floor is f * cell * h / d^2 high."""
    f = (WIDTH_4K / 2) / math.tan(math.radians(angle) / 2)
    return math.sqrt(f * cell * max(0.5, cam[1]) / 2)


def faded(near, far, fade, uv):
    """near up to fade[2], far beyond fade[3], measured from the camera's
    foot (fade[0], fade[1]) in pattern space."""
    if not fade:
        return near
    cx, cz, d0, d1 = fade
    a, b = ("x", "y") if uv else ("x", "z")
    fn = f"min(1, max(0, (sqrt(({a}-({cx:.3f}))*({a}-({cx:.3f}))+({b}-({cz:.3f}))*({b}-({cz:.3f}))) - {d0:.3f}) / {d1 - d0:.3f}))"
    return f"function {{ {fn} }} pigment_map {{ [0 {near}] [1 {far}] }}"


def board_tex(a=(0.88, 0.88, 0.86), b=(0.02, 0.02, 0.025), uv=False, cell=2.0, fade=None, night=False):
    m = "uv_mapping " if uv else ""
    sc = f"scale {cell}" if uv else f"scale {cell} translate <0, {cell / 2}, 0>"
    avg = tuple((x + y) / 2 for x, y in zip(a, b))
    near = f"checker rgb {rt.vec(a)}, rgb {rt.vec(b)} {sc}"
    return (f"texture {{ {m}pigment {{ {faded(near, f'rgb {rt.vec(avg)}', fade, uv)} }} "
            f"{NIGHT_FINISH if night else BOARD_FINISH} }}")


def grid_tex(uv=False, cell=2.0, width=0.04, fade=None, night=False):
    """Glowing green lines on black: the 1980s wireframe floor. One texture
    (POV-Ray layers nothing over a uv-mapped one): the lines from two
    gradients in a pigment map, emission makes only them glow, black times
    emission stays black, and the black floor still mirrors. Far away the
    lines fade into the green they average to."""
    m = "uv_mapping " if uv else ""
    w = width / cell
    g, k = f"rgb {rt.vec(GREEN)}", "rgb <0.004, 0.008, 0.005>"
    second = "y" if uv else "z"
    lines = f"gradient {second} color_map {{ [0 {g}] [{w:.4f} {k}] [{1 - w:.4f} {k}] [1 {g}] }}"
    near = f"gradient x pigment_map {{ [0 {g}] [{w:.4f} {lines}] [{1 - w:.4f} {lines}] [1 {g}] }} scale {cell}"
    cov = 1 - (1 - 2 * w) ** 2
    avg = tuple(c * cov for c in GREEN)
    return (f"texture {{ {m}pigment {{ {faded(near, f'rgb {rt.vec(avg)}', fade, uv)} }}"
            f" finish {{ emission 1 diffuse 0.2 specular {0 if night else 0.6} roughness 0.004"
            f" reflection {{ 0.06, {0.38 if night else 0.30} fresnel on }} }}"
            + (" normal { bumps 0.035 scale 0.008 }" if night else "") + " }")


def funnel_inc(depth=1.3, twist=0.0, r0=0.22, R=400.0, nr=420, nt=480):
    """The singularity: a surface of revolution y = -depth * (1/r - 1/R),
    from r0 out to R, then a throat going down into black. uv coordinates
    follow the floor's x and z, turned by twist / r, so the chessboard (or
    the grid) runs into the funnel and winds round it."""
    name = f"funnel-{depth:.2f}-{twist:.2f}.inc"
    inc = CACHE / name
    if inc.exists():
        return inc
    CACHE.mkdir(parents=True, exist_ok=True)
    r = np.geomspace(r0, R, nr)
    th = np.linspace(0, 2 * math.pi, nt, endpoint=False)
    rr, tt = np.meshgrid(r, th, indexing="ij")
    y = -depth * (1 / rr - 1 / R)
    P = np.stack([rr * np.cos(tt), y, rr * np.sin(tt)], -1).reshape(-1, 3)
    ang = tt + twist / rr
    UV = np.stack([rr * np.cos(ang), rr * np.sin(ang)], -1).reshape(-1, 2)
    # The throat: rings at r0 going down.
    ys = y[0, 0] - np.geomspace(0.05, 40, 24)
    tr = np.stack([np.full((24, nt), r0) * np.cos(th), np.repeat(ys[:, None], nt, 1), np.full((24, nt), r0) * np.sin(th)], -1)
    P = np.vstack([tr[::-1].reshape(-1, 3), P])
    UV = np.vstack([np.zeros((24 * nt, 2)), UV])
    rows = 24 + nr
    F = []
    for i in range(rows - 1):
        a = i * nt + np.arange(nt)
        b = i * nt + (np.arange(nt) + 1) % nt
        F += [np.stack([a, b, a + nt], 1), np.stack([b, b + nt, a + nt], 1)]
    F = np.vstack(F)
    vec = lambda A: ",".join(f"<{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}>" for p in A)  # noqa: E731
    uvs = ",".join(f"<{u:.4f},{v:.4f}>" for u, v in UV)
    faces = ",".join(f"<{a},{b},{c}>" for a, b, c in F)
    inc.write_text(f"#declare Funnel = mesh2 {{ vertex_vectors {{ {len(P)}, {vec(P)} }}\n uv_vectors {{ {len(UV)}, {uvs} }}\n"
                   f" face_indices {{ {len(F)}, {faces} }} }}\n")
    return inc


def floor(kind, cam=None, night=False, **kw):
    """The floor; cam = the camera's dict, for the fade into the distance."""
    cell = kw.get("cell", 2.0)
    loc, angle = (cam["loc"], cam["angle"]) if cam else ((0, 2.4, -15), 46)
    d = fade_distance(cell, loc, angle)
    if kind in ("board", "grid"):
        fade = (loc[0], loc[2], 0.7 * d, 1.5 * d)
        if kind == "board":
            tex = board_tex(kw.get("a", (0.88, 0.88, 0.86)), kw.get("b", (0.02, 0.02, 0.025)), cell=cell, fade=fade,
                            night=night)
        else:
            tex = grid_tex(cell=cell, width=0.02 * cell, fade=fade, night=night)
        # At night with an ior, so that fresnel gives the lacquered board its
        # strong grazing reflection, the moon's path (the day pictures were
        # made without, they stay as chosen).
        ior = " interior { ior 1.5 }" if night else ""
        return f"plane {{ y, 0 {tex}{ior} }}\n"
    if kind in ("funnel", "funnel-grid"):
        inc = funnel_inc(kw.get("depth", 1.3), kw.get("twist", 0.0))
        sc = kw.get("scale", 1.6)
        x, z = kw.get("at", (0, 6))
        # uv lives in the mesh's own units, before the object's scale.
        c = cell / sc
        fade = ((loc[0] - x) / sc, (loc[2] - z) / sc, 0.7 * d / sc, 1.5 * d / sc)
        tex = (board_tex(uv=True, cell=c, fade=fade, night=night) if kind == "funnel"
               else grid_tex(uv=True, cell=c, width=0.02 * c, fade=fade, night=night))
        ior = " interior { ior 1.5 }" if night else ""
        return (f'#include "{inc}"\nobject {{ Funnel {tex}{ior} scale {sc} translate <{x}, 0, {z}> }}\n'
                f"sphere {{ <{x}, -30, {z}>, 6 pigment {{ rgb 0 }} finish {{ ambient 0 diffuse 0 }} }}\n")
    raise ValueError(kind)


# ---- objects ---------------------------------------------------------------------
MATS = {"chrom": "texture { Chrome }", "gold": "texture { Gold }", "glas": "material { Glass }",
        "rot": "texture { Lacquer }", "blau": "texture { Blue }", "marmor": "texture { Marble scale 0.3 }"}
PHI = (1 + 5 ** 0.5) / 2


def _hull_mesh(V, name):
    from scipy.spatial import ConvexHull
    V = np.asarray(V, float)
    V /= np.linalg.norm(V, axis=1).max()
    h = ConvexHull(V)
    tris = []
    for s in h.simplices:
        a, b, c = V[s]
        n = np.cross(b - a, c - a)
        if np.dot(n, a) < 0:
            b, c = c, b
        tris.append(f"triangle {{ {rt.vec(a)}, {rt.vec(b)}, {rt.vec(c)} }}")
    return f"#declare {name} = mesh {{ {' '.join(tris)} inside_vector <0, 1, 0.1> }}\n"


def polyhedra():
    cyc = lambda p: [p, (p[1], p[2], p[0]), (p[2], p[0], p[1])]  # noqa: E731
    ico = [q for s1 in (1, -1) for s2 in (1, -1) for q in cyc((0, s1, s2 * PHI))]
    dod = [(a, b, c) for a in (1, -1) for b in (1, -1) for c in (1, -1)] + \
          [q for s1 in (1, -1) for s2 in (1, -1) for q in cyc((0, s1 / PHI, s2 * PHI))]
    octa = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    src = _hull_mesh(ico, "Ico") + _hull_mesh(dod, "Dod") + _hull_mesh(octa, "Octa")
    # The small stellated dodecahedron: a pentagonal pyramid on each face of
    # a dodecahedron, the points where an icosahedron's corners would be.
    from scipy.spatial import ConvexHull
    D = np.asarray(dod, float)
    D /= np.linalg.norm(D, axis=1).max()
    h = ConvexHull(D)
    faces = {}
    for s, eq in zip(h.simplices, h.equations):
        faces.setdefault(tuple(np.round(eq, 5)), set()).update(s)
    tris = []
    for eq, idx in faces.items():
        pts = D[list(idx)]
        c = pts.mean(0)
        n = np.array(eq[:3])
        apex = c + n * 1.15
        u = pts - c
        e1 = u[0] / np.linalg.norm(u[0])
        e2 = np.cross(n, e1)
        order = np.argsort(np.arctan2(u @ e2, u @ e1))
        ring = pts[order]
        for i in range(len(ring)):
            tris.append(f"triangle {{ {rt.vec(ring[i])}, {rt.vec(ring[(i + 1) % len(ring)])}, {rt.vec(apex)} }}")
    src += f"#declare Star = union {{ mesh {{ {' '.join(tris)} }} object {{ Dod }} }}\n"
    return src


def sph(x, z, r, mat="chrom", y=None):
    return f"sphere {{ <{x}, {r if y is None else y}, {z}>, {r} {MATS[mat]} }}\n"


def pyr(x, z, b, h, mat="glas", rot=0):
    return f"object {{ Pyramid({b}, {h}) rotate y * {rot} {MATS[mat]} translate <{x}, 0, {z}> }}\n"


def poly(kind, x, z, size, mat="chrom", y=None, rot=(0, 0, 0)):
    """A polyhedron (Ico, Dod, Octa, Star) of radius size; lying (y None:
    resting on the floor, approximately) or floating at y."""
    yy = size * (0.80 if kind != "Star" else 0.75) if y is None else y
    return f"object {{ {kind} scale {size} rotate {rt.vec(rot)} {MATS[mat]} translate <{x}, {yy}, {z}> }}\n"


def box(x, z, s, mat="blau", rot=0, y=0):
    return f"box {{ <-{s}, 0, -{s}>, <{s}, {2 * s}, {s}> rotate y * {rot} {MATS[mat]} translate <{x}, {y}, {z}> }}\n"


def cone(x, z, r, h, mat="rot"):
    return f"cone {{ <{x}, 0, {z}>, {r}, <{x}, {h}, {z}>, 0 {MATS[mat]} }}\n"


def torus(x, y, z, R, r, mat="gold", rot=(90, -25, 0)):
    return f"torus {{ {R}, {r} rotate {rt.vec(rot)} {MATS[mat]} translate <{x}, {y}, {z}> }}\n"


def statue(x, z, size=2.4, rot=-15):
    """The Lipizzaner in a levade, marble, on a slender plinth with a
    moulded foot and top."""
    inc = rt.horse_inc("levade")
    return f"""#include "{inc}"
union {{
  box {{ <-0.80, 0, -0.50>, <0.80, 0.14, 0.50> }}
  box {{ <-0.70, 0.14, -0.42>, <0.70, 0.22, 0.42> }}
  box {{ <-0.60, 0.22, -0.35>, <0.60, 1.30, 0.35> }}
  box {{ <-0.70, 1.30, -0.42>, <0.70, 1.38, 0.42> }}
  box {{ <-0.78, 1.38, -0.48>, <0.78, 1.48, 0.48> }}
  // the hooves pressed 1.5 % into the top, so they stand on it, not above
  object {{ Horse scale {size} translate <0, {1.48 - 0.015 * size:.4f}, 0> }}
  texture {{ Marble scale 0.22 }}
  rotate y * {rot} translate <{x}, 0, {z}> }}
"""


SERIF = "/usr/share/fonts/google-noto/NotoSerif-Bold.ttf"
DIGITS_FONT = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"


def phi(x, z, size=1.6, mat="chrom", y=0.0, rot=-15):
    """The letter phi as a solid, standing (y 0) or floating."""
    return (f'text {{ ttf "{SERIF}" "Φ" 0.35, 0 translate <-0.38, 0, -0.175> scale {size} rotate y * {rot} '
            f"{MATS[mat]} translate <{x}, {y}, {z}> }}\n")


def digits(x, z, chars="1618", size=0.7, mat="gold", rot=-10, gap=0.62):
    """Digits lying flat on the floor, extruded."""
    out = []
    for i, ch in enumerate(chars):
        out.append(f'text {{ ttf "{DIGITS_FONT}" "{ch}" 0.18, 0 rotate x * 90 translate <{i * gap}, 0.18, 0> '
                   f"scale {size} rotate y * {rot} {MATS[mat]} translate <{x}, 0, {z}> }}\n")
    return "".join(out)


def digit_mesh(chars, x0, z0, size, rot, surface, height=0.16, gap=0.66):
    """Digits lying on the floor as a mesh that follows the surface: the
    glyphs' outlines (matplotlib's TextPath), cut on a fine grid and
    triangulated (shapely), extruded, every point set onto the surface
    (surface(x, z) -> y), so that on the funnel's rim they bend with it."""
    import shapely
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    from shapely.geometry import Polygon, box as sbox
    prop = FontProperties(fname=DIGITS_FONT)
    tris, sides = [], []
    for i, ch in enumerate(chars):
        rings = [r for r in TextPath((0, 0), ch, size=1, prop=prop).to_polygons() if len(r) > 2]
        geom = Polygon()
        for r in rings:                          # even-odd: holes of 0, 6, 8, 9
            geom = geom.symmetric_difference(Polygon(r).buffer(0))
        geom = shapely.affinity.translate(geom, i * gap)
        cell = 0.05
        x1, y1, x2, y2 = geom.bounds
        pieces = []
        for gx in np.arange(x1, x2, cell):
            for gy in np.arange(y1, y2, cell):
                part = geom.intersection(sbox(gx, gy, gx + cell, gy + cell))
                if not part.is_empty:
                    pieces.append(part)
        for part in pieces:
            for t in shapely.constrained_delaunay_triangles(part).geoms:
                tris.append(np.asarray(t.exterior.coords)[:3])
        polys = geom.geoms if hasattr(geom, "geoms") else [geom]
        for pg in polys:
            for ring in [pg.exterior, *pg.interiors]:
                c = np.asarray(shapely.segmentize(ring, 0.03).coords)
                sides += [(c[k], c[k + 1]) for k in range(len(c) - 1)]
    a = math.radians(rot)

    def place(u, v, h):
        x = x0 + size * (u * math.cos(a) + v * math.sin(a))
        z = z0 + size * (-u * math.sin(a) + v * math.cos(a))
        return (x, surface(x, z) + h * size, z)
    out = []
    for t in tris:
        top = [place(u, v, height) for u, v in t]
        bot = [place(u, v, 0) for u, v in t]
        out.append(f"triangle {{ {rt.vec(top[0])}, {rt.vec(top[1])}, {rt.vec(top[2])} }}")
        out.append(f"triangle {{ {rt.vec(bot[0])}, {rt.vec(bot[2])}, {rt.vec(bot[1])} }}")
    for (u1, v1), (u2, v2) in sides:
        p1, p2 = place(u1, v1, 0), place(u2, v2, 0)
        q1, q2 = place(u1, v1, height), place(u2, v2, height)
        out.append(f"triangle {{ {rt.vec(p1)}, {rt.vec(p2)}, {rt.vec(q2)} }}")
        out.append(f"triangle {{ {rt.vec(p1)}, {rt.vec(q2)}, {rt.vec(q1)} }}")
    return out


def bent_digits(x, z, chars="1618", size=0.9, mat="gold", rot=-8, depth=1.4, at=None):
    """Digits lying on the floor, bent with the funnel where they reach it."""
    if at is None:
        surface = lambda X, Z: 0.0  # noqa: E731
    else:
        surface = lambda X, Z: funnel_y(max(0.3, math.hypot(X - at[0], Z - at[1])), depth)  # noqa: E731
    tris = digit_mesh(chars, x, z, size, rot, surface)
    return f"mesh {{ {' '.join(tris)} inside_vector <0, 1, 0.01> {MATS[mat]} }}\n"


def funnel_y(r, depth, scale=1.6, R=400.0):
    """The height of the funnel's surface at distance r from its centre."""
    return -depth * scale * (scale / r - 1 / R)


def camera(loc=(0, 2.4, -15), at=(1.4, 1.5, 0), angle=46):
    return f"camera {{ location {rt.vec(loc)} look_at {rt.vec(at)} angle {angle} right x * image_width / image_height }}\n"


# ---- the thirty drafts -------------------------------------------------------------
# number: (description, time, night partner time or None, floor, floor args,
#          moon, camera args, objects)
C = dict(loc=(0, 2.4, -15), at=(1.4, 1.5, 0), angle=46)
CLASSIC = [sph(3.2, 3.0, 1.6), sph(0.4, 1.2, 0.75), sph(5.6, 1.4, 0.85), sph(1.9, -0.8, 0.42),
           pyr(1.5, 2.0, 0.55, 2.6), pyr(6.4, 4.4, 0.5, 2.0, rot=15)]
DRAFTS = {
    1: ("Chrome spheres, classic, noon (the original's style, smaller)", "noon", "night", "board", {}, False, C, CLASSIC),
    2: ("Chrome spheres, morning", "morning", "night", "board", {}, False, C, CLASSIC),
    3: ("Chrome spheres, evening", "evening", "night", "board", {}, False, C, CLASSIC),
    4: ("Chrome spheres, night with the moon (partner for chrome spheres in the evening)", "night", None, "board", {}, True, C, CLASSIC),
    5: ("Chrome spheres, one floating over the board, noon", "noon", "night", "board", {}, False, C,
        [sph(3.0, 3.0, 1.3), sph(0.6, 1.0, 0.7), sph(5.4, 1.6, 0.8), sph(2.4, 1.5, 0.9, y=4.2), pyr(1.4, 2.2, 0.5, 2.2)]),
    6: ("A row of spheres towards the horizon, growing smaller, evening", "evening", "night", "board", {}, False,
        dict(loc=(-1, 1.9, -14), at=(2, 1.2, 4), angle=44),
        [sph(-1.5 + i * 2.1, -2 + i * 2.6, 1.1 * 0.82 ** i) for i in range(8)]),
    7: ("Chrome and glass on a red and white board, noon", "noon", "night", "board",
        dict(a=(0.92, 0.90, 0.88), b=(0.62, 0.03, 0.03)), False, C,
        [sph(2.6, 2.4, 1.4), sph(5.2, 1.0, 0.9, "glas"), sph(0.2, 0.8, 0.7, "glas"), sph(3.8, -0.8, 0.45)]),
    8: ("A large glass sphere, small chrome spheres, morning", "morning", "night", "board", {}, False, C,
        [sph(2.6, 2.4, 1.7, "glas"), sph(5.4, 1.2, 0.6), sph(0.4, 0.4, 0.5), sph(4.4, -0.8, 0.35, "gold")]),
    9: ("Polyhedra lying about: icosahedron, dodecahedron, octahedron, noon", "noon", "night", "board", {}, False, C,
        [poly("Ico", 0.6, 1.2, 0.9, "chrom", rot=(10, 20, 0)), poly("Dod", 3.2, 3.2, 1.3, "gold", rot=(0, 30, 20)),
         poly("Octa", 5.6, 1.0, 0.9, "glas", y=0.9, rot=(0, 25, 0)), sph(2.0, -0.6, 0.45)]),
    10: ("A star polyhedron floating over the board, evening", "evening", "night", "board", {}, False, C,
         [poly("Star", 2.8, 2.6, 1.2, "chrom", y=3.4, rot=(20, 35, 10)), sph(1.0, 1.0, 0.6), sph(5.0, 1.8, 0.7)]),
    11: ("Solids: cube, cone, torus, glass cylinder (smaller), morning", "morning", "night", "board", {}, False, C,
         [box(0.4, 2.0, 0.7, rot=28), cone(5.2, 3.2, 0.7, 2.2), torus(3.0, 1.05, 1.4, 0.8, 0.26),
          f"cylinder {{ <1.8, 0, 4.2>, <1.8, 2.6, 4.2>, 0.4 {MATS['glas']} }}\n", sph(2.2, -0.8, 0.4)]),
    12: ("A golden dodecahedron floating, night with the moon", "night", None, "board", {}, True, C,
         [poly("Dod", 2.8, 2.6, 1.3, "gold", y=3.0, rot=(15, 30, 10)), sph(0.6, 1.2, 0.6), sph(5.4, 2.0, 0.8)]),
    13: ("A field of glass pyramids, evening", "evening", "night", "board", {}, False, C,
         [pyr(x, z, 0.4 + 0.15 * ((i * 7) % 3), 1.4 + 0.5 * ((i * 5) % 4), rot=i * 17)
          for i, (x, z) in enumerate([(0, 1), (1.6, 3), (3.2, 0.5), (4.2, 3.8), (5.6, 1.6), (2.4, 6), (6.8, 5)])]
         + [sph(2.2, -0.9, 0.45)]),
    14: ("Linked chrome rings floating, noon", "noon", "night", "board", {}, False, C,
         [torus(2.8, 3.0, 2.4, 1.1, 0.18, "chrom", (90, 20, 0)), torus(3.6, 3.0, 2.4, 1.1, 0.18, "gold", (0, 20, 0)),
          sph(0.6, 1.0, 0.6), sph(5.6, 1.6, 0.7)]),
    15: ("A gold icosahedron on the green grid, night with the moon", "night", None, "grid", {}, False, C,
         [poly("Ico", 2.8, 2.4, 1.3, "gold", rot=(10, 20, 0)), sph(0.4, 1.2, 0.6), sph(5.6, 1.6, 0.7)]),
    16: ("A marble Lipizzaner in a levade on a plinth, noon", "noon", "night", "board", {}, False,
         dict(loc=(0, 2.4, -9.5), at=(1.6, 2.2, 2.4), angle=42), [statue(2.0, 2.4)]),
    17: ("Lipizzaner levade, evening", "evening", "night", "board", {}, False,
         dict(loc=(0, 2.4, -9.5), at=(1.6, 2.2, 2.4), angle=42), [statue(2.0, 2.4, rot=-25)]),
    18: ("Lipizzaner levade, night with the moon", "night", None, "board", {}, True,
         dict(loc=(0, 2.4, -9.5), at=(1.6, 2.2, 2.4), angle=42), [statue(2.0, 2.4, rot=-25)]),
    19: ("The Lipizzaner with two chrome spheres by the plinth, morning", "morning", "night", "board", {}, False,
         dict(loc=(0, 2.4, -11), at=(1.8, 2.0, 2.4), angle=44),
         [statue(2.2, 2.6, rot=-10), sph(-0.4, 1.4, 0.6), sph(4.6, 1.2, 0.7)]),
    20: ("The Lipizzaner on the green grid, night", "night", None, "grid", {}, False,
         dict(loc=(0, 2.4, -9.5), at=(1.6, 2.2, 2.4), angle=42), [statue(2.0, 2.4, rot=-25)]),
    21: ("Singularity: the chessboard runs into the funnel, noon", "noon", "night", "funnel", dict(depth=2.2), False,
         dict(loc=(0, 6.5, -6.5), at=(0.2, -1.2, 6), angle=50), []),
    22: ("Twisted singularity, the board winds into it, evening", "evening", "night", "funnel",
         dict(depth=2.2, twist=1.4), False, dict(loc=(0, 6.5, -6.5), at=(0.2, -1.2, 6), angle=50), []),
    23: ("Singularity, a chrome sphere floating above it, night with the moon", "night", None, "funnel",
         dict(depth=2.2, twist=0.8), True, dict(loc=(0, 6.5, -6.5), at=(0.2, -0.4, 6), angle=50),
         [sph(0, 6, 0.7, y=1.9)]),
    24: ("Singularity in the green grid, night", "night", None, "funnel-grid", dict(depth=2.2), False,
         dict(loc=(0, 6.5, -6.5), at=(0.2, -1.2, 6), angle=50), []),
    25: ("Grid funnel, a star polyhedron floating, black sky", "night", None, "funnel-grid",
         dict(depth=2.4, twist=1.0), False, dict(loc=(0, 6.5, -6.5), at=(0.2, 0.5, 6), angle=50),
         [poly("Star", 0, 6, 0.8, "chrom", y=2.0, rot=(20, 30, 0))]),
    26: ("Singularity, spheres at its rim, morning", "morning", "night", "funnel", dict(depth=2.2, twist=0.6), False,
         dict(loc=(0, 6.5, -6.5), at=(0.2, -1.2, 6), angle=50),
         [sph(-3.4, 4.2, 0.6, y=0.6 - 2.2 * 1.6 * (1 / (3.6 / 1.6) - 1 / 400)), sph(3.2, 8.4, 0.7, y=0.55)]),
    27: ("The flat green grid, chrome spheres, night", "night", None, "grid", {}, False, C, CLASSIC[:4]),
    28: ("The green grid, evening sky, glass pyramids", "evening", "night", "grid", {}, False, C,
         [pyr(1.4, 2.0, 0.6, 2.6), pyr(4.4, 3.6, 0.5, 2.0, rot=20), sph(3.0, 0.6, 0.6)]),
    29: ("Grid, a star polyhedron floating, a glass pyramid, night with the moon", "night", None, "grid", {}, True, C,
         [poly("Star", 3.0, 3.0, 1.1, "chrom", y=3.2, rot=(10, 20, 30)), pyr(1.0, 1.6, 0.55, 2.2), sph(5.4, 1.2, 0.6)]),
    30: ("All together: the Lipizzaner, polyhedra, a floating sphere, noon", "noon", "night", "board", {}, False,
         dict(loc=(0, 2.6, -12), at=(1.8, 1.9, 2), angle=48),
         [statue(1.8, 3.4, size=2.0, rot=-20), poly("Dod", 5.4, 1.6, 0.8, "gold", rot=(0, 30, 20)),
          poly("Ico", -1.0, 1.2, 0.6, "glas", rot=(10, 0, 0)), sph(4.2, 4.6, 0.7, y=4.0), sph(2.6, -1.0, 0.4)]),
}
# Round 2 (the user, 26.10.2026): singularities with the horizon in view,
# a finer board, the Lipizzaner small at the edge, a phi, digits lying about.
# The camera tilted down about 5 degrees at a 50 degree view: the horizon
# lies a third from the top, the funnel in the middle ground.
FC = dict(loc=(0, 2.4, -9), at=(0, 0.8, 12), angle=50)
AT = (0, 9)
F1 = dict(depth=1.4, cell=0.6, at=AT)


def ball(x, z, r, mat="chrom", depth=1.4, at=AT):
    """A sphere resting on the funnel's slope (approximately)."""
    d = math.hypot(x - at[0], z - at[1])
    return sph(x, z, r, mat, y=funnel_y(d, depth) + r * 1.05)


# Depth: something small right in front (z 0-2), the middle ground
# (z 5-9, the funnel at z 9), something far behind (z 13-20).
DRAFTS.update({
    31: ("Singularity with the horizon, a golden phi floating above it, a small chrome sphere in front, the Lipizzaner and a glass pyramid far behind, noon",
         "noon", "night", "funnel", F1, False, FC,
         [phi(0, 9, 1.5, "gold", y=1.2, rot=-10), sph(-1.3, -1.5, 0.18), statue(-7.0, 16, size=1.5, rot=20),
          pyr(6.5, 19, 0.6, 2.2)]),
    32: ("Singularity, gold digits 1 6 1 8 lying on the far slope and bending with it, a marble phi behind, evening",
         "evening", "night", "funnel", F1, False, FC,
         [bent_digits(-1.75, 10.4, "1618", 1.3, "gold", rot=0, at=AT), sph(1.4, -1.6, 0.18),
          phi(5.0, 15, 1.5, "marmor", rot=-25), statue(-6.5, 14, size=1.5, rot=20)]),
    33: ("Singularity at night with the moon, a marble phi in the middle ground, the Lipizzaner far behind on the right", "night", None,
         "funnel", F1, True, FC,
         [phi(-3.6, 8, 1.4, "marmor", rot=15), statue(6.6, 17, size=1.5, rot=-30), sph(1.2, -1.5, 0.18),
          ball(1.9, 7.6, 0.32)]),
    34: ("Twisted singularity, chrome digits 3 1 4 1 5 bending on the far slope, morning", "morning", "night",
         "funnel", dict(F1, twist=1.2), False, FC,
         [bent_digits(-2.05, 10.4, "31415", 1.25, "chrom", rot=0, at=AT), statue(-6.4, 12, size=1.5, rot=25),
          phi(5.5, 17, 1.4, "gold", y=1.0, rot=-20), sph(1.3, -1.5, 0.18, "gold")]),
    35: ("Singularity in the green grid, a golden phi floating, night with the moon", "night", None, "funnel-grid",
         dict(F1, cell=0.8), True, FC,
         [phi(0, 9, 1.5, "gold", y=1.3), statue(-6.8, 15, size=1.5, rot=20), sph(1.4, -1.5, 0.18),
          poly("Ico", 6.0, 18, 0.7, "chrom", rot=(10, 20, 0))]),
    36: ("Grid singularity in the evening, gold digits 0-9 lying bent on the far slope", "evening", "night",
         "funnel-grid", dict(F1, cell=0.8), False, FC,
         [bent_digits(-3.3, 10.3, "0123456789", 1.0, "gold", rot=0, at=AT), statue(6.8, 16, size=1.5, rot=-30),
          sph(-1.3, -1.5, 0.18)]),
    37: ("Deep singularity, spheres at different depths rolling in, a golden phi far behind, noon", "noon",
         "night", "funnel", dict(F1, depth=2.0), False, FC,
         [sph(-0.9, -1.5, 0.18), ball(-1.9, 7.2, 0.34, depth=2.0), ball(1.5, 6.6, 0.28, depth=2.0),
          ball(2.6, 11.0, 0.45, depth=2.0), phi(-5.2, 16, 1.5, "gold", rot=10), statue(6.8, 18, size=1.5, rot=-30)]),
    38: ("Twisted grid, gold digits 1 6 1 8 bent on the slope, the Lipizzaner in the middle ground, night with the moon",
         "night", None, "funnel-grid", dict(F1, cell=0.8, twist=1.2), True, FC,
         [bent_digits(-1.75, 10.4, "1618", 1.3, "gold", rot=0, at=AT), statue(5.2, 9.5, size=1.4, rot=-30),
          sph(-1.3, -1.5, 0.18)]),
    39: ("Only the singularity, a large chrome phi behind on the right, a small sphere in front, a very fine board, noon (calm)",
         "noon", "night", "funnel", dict(F1, cell=0.4), False, FC,
         [phi(5.0, 15, 2.2, "chrom", rot=-25), sph(-1.2, -1.5, 0.18)]),
    40: ("All together: singularity, phi, the Lipizzaner, bent digits, spheres, icosahedron, pyramid, evening", "evening",
         "night", "funnel", F1, False, FC,
         [phi(0, 9, 1.4, "gold", y=1.3, rot=-10), statue(-6.8, 15, size=1.5, rot=25),
          bent_digits(-1.5, 10.5, "1618", 1.1, "chrom", rot=0, at=AT), ball(2.7, 9.8, 0.4),
          poly("Ico", 1.4, -1.2, 0.22, "glas"), pyr(6.8, 19, 0.6, 2.2), sph(-2.4, 2.0, 0.25, "gold")]),
})
# The horse drafts again, the Lipizzaner standing on the plinth (26.10.2026).
for _n in (16, 17, 18, 19, 20, 30):
    DRAFTS[f"{_n}b"] = (DRAFTS[_n][0] + " (the horse standing on the plinth)",) + DRAFTS[_n][1:]
BLACK_SKY = {25}


def label(n):
    return f"{n:02d}" if isinstance(n, int) else n


def order(n):
    return (int(str(n).rstrip("b")), str(n))


def scene(n, t=None, moon_dir=None):
    """moon_dir: (screen x, elevation) of the moon at night."""
    desc, day, night, fl, fargs, moon, cam, objs = DRAFTS[n]
    t = t or day
    vec = moon_direction(cam, *moon_dir) if moon_dir else moon_direction(cam, 0.72, 5)
    return (rt.HEAD + "global_settings { charset utf8 }\n#declare Blue = texture { pigment { rgb <0.04, 0.12, 0.55> } finish { ambient 0 diffuse 0.6 "
            "specular 0.8 roughness 0.003 reflection { 0.04, 0.30 fresnel on } } }\n" + polyhedra()
            + sky(t, moon=moon or t == "night", black=n in BLACK_SKY, moon_vec=vec, cam=cam) + camera(**cam)
            + floor(fl, cam=cam, night=t == "night", **fargs) + "".join(objs))


def render(n, t, png, w, h, moon_dir=None):
    src = png.with_suffix(".pov")
    src.write_text(scene(n, t, moon_dir))
    cmd = ["povray", f"+I{src}", f"+O{png}", f"+W{w}", f"+H{h}", "+FN", "-D", "-V", "+WT14"] + rt.AA.split()
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not png.exists():
        raise RuntimeError(f"povray {src.name}: {r.stderr[-2000:]}")
    return time.time() - t0


def contact_sheet(nums, name="kontaktbogen.png"):
    W, H, cols = 640, 360, 6
    rows = math.ceil(len(nums) / cols)
    sheet = Image.new("RGB", (cols * W, rows * H), "black")
    font = ImageFont.truetype(FONT, 64)
    for i, n in enumerate(nums):
        im = Image.open(OUT / f"{label(n)}.png").convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 40 + 40 * len(label(n)), 80), fill=(0, 0, 0))
        d.text((10, 4), label(n), font=font, fill=(255, 220, 0))
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    sheet.save(OUT / name)


# ---- the chosen ones (the user, 26.10.2026) -----------------------------------------
# draft: (package stem, name, German name, description, day time, night
# time, the moon's (elevation, azimuth) at night: each night its own sky).
FINALS = {
    1: ("raytracing-chrome", "Chrome Spheres", "Chromkugeln", "Chrome spheres and glass pyramids on a chessboard", "noon", "night", (0.865, 5.5)),
    2: ("raytracing-chrome-morning", "Chrome Spheres, Morning", "Chromkugeln am Morgen", "The chrome spheres in the morning sun", "morning", "night", (0.3, 2.8)),
    3: ("raytracing-chrome-evening", "Chrome Spheres, Evening", "Chromkugeln am Abend", "The chrome spheres at sunset, and by moonlight", "evening", "night", (0.865, 3.8)),
    6: ("raytracing-sphere-row", "Row of Spheres", "Kugelreihe", "Chrome spheres growing smaller towards the horizon", "evening", "night", (0.85, 6)),
    10: ("raytracing-star-polyhedron", "Stellated Dodecahedron", "Sternpolyeder", "A chrome star polyhedron floating over the board", "evening", "night", (0.84, 3.5)),
    11: ("raytracing-solids", "Ray-Traced Solids", "Raytracing-Körper", "Cube, cone, torus and a glass cylinder", "morning", "night", (0.82, 5)),
    13: ("raytracing-glass-pyramids", "Glass Pyramids", "Glaspyramiden", "A field of glass pyramids", "evening", "night", (0.82, 6)),
    14: ("raytracing-rings", "Linked Rings", "Verschränkte Ringe", "Two linked rings floating, chrome and gold", "noon", "night", (0.86, 5)),
    "16b": ("raytracing-lipizzaner-noon", "Lipizzaner, Noon", "Lipizzaner am Mittag", "A marble Lipizzaner in a levade on its plinth", "noon", "night", (0.86, 5)),
    "17b": ("raytracing-lipizzaner-evening", "Lipizzaner, Evening", "Lipizzaner am Abend", "The marble Lipizzaner at sunset", "evening", "night", (0.74, 6)),
    "18b": ("raytracing-lipizzaner-moonlight", "Lipizzaner by Moonlight", "Lipizzaner im Mondlicht", "The marble Lipizzaner by moonlight, in the morning by day", "morning", "night", (0.8, 3.5)),
    "19b": ("raytracing-lipizzaner-spheres", "Lipizzaner with Spheres", "Lipizzaner mit Kugeln", "The Lipizzaner between two chrome spheres", "morning", "night", (0.65, 6.5)),
    27: ("raytracing-grid", "Green Grid", "Grünes Gitternetz", "Chrome spheres on a green wireframe grid", "morning", "night", (0.84, 5)),
    28: ("raytracing-grid-evening", "Green Grid, Evening", "Gitternetz am Abend", "Glass pyramids on the green grid at sunset", "evening", "night", (0.76, 4)),
    "30b": ("raytracing-ensemble", "Ensemble", "Ensemble", "The Lipizzaner, polyhedra and a floating sphere", "noon", "night", (0.79, 3)),
    31: ("raytracing-singularity-phi", "Singularity with Phi", "Singularität mit Phi", "The board runs into a singularity, a golden phi above it", "noon", "night", (0.68, 4.5)),
    37: ("raytracing-singularity-spheres", "Singularity with Spheres", "Singularität mit Kugeln", "Spheres rolling into a deep singularity", "noon", "night", (0.63, 5.5)),
    39: ("raytracing-singularity", "Singularity", "Singularität", "Only the singularity and a chrome phi, a fine board", "noon", "night", (0.66, 3.5)),
}
HORSE_DRAFTS = {"16b", "17b", "18b", "19b", "30b"}


THEME = HERE.parent / "wallpapers"
JPEG_QUALITY = 88       # about 0.7 MB a picture, a pair 1.2-1.6 MB


def record(n, t, suffix, seconds):
    """The JSON beside a finished picture."""
    import hashlib
    stem, name, name_de, description, day, night, moon = FINALS[n]
    rec = {
        "renderer": "POV-Ray 3.7.0.10.unofficial", "script": "os2-warp/tools/raytracing-drafts.py",
        "draft": label(n), "scene": DRAFTS[n][0], "time_of_day": t, "moon": list(moon) if t == "night" else None,
        "floor": DRAFTS[n][3], "floor_args": {k: v for k, v in DRAFTS[n][4].items()},
        "camera": DRAFTS[n][6], "size": [rt.W, rt.H], "antialias": rt.AA, "jpeg_quality": JPEG_QUALITY,
        "seed": None, "seconds": round(seconds, 1), "host": "245k (Intel Core Ultra 5 245K, 14 threads, CPU)",
        "source": f"wallpaper/warp-legacy/raytracing/final/{stem}{suffix}.pov"}
    if "Horse" in "".join(DRAFTS[n][7]) or "horse-levade" in "".join(DRAFTS[n][7]):
        rec["model"] = {
            "name": "horse", "source": "Georgia Tech Large Geometric Models Archive",
            "url": "https://sites.cc.gatech.edu/projects/large_models/horse.html",
            "file": "https://sites.cc.gatech.edu/data_files/large_models/horse.ply.gz",
            "sha256_ply_gz": hashlib.sha256(rt.HORSE_PLY.with_suffix(".ply.gz").read_bytes()).hexdigest(),
            "origin": "originally a Cyberware scan (not stated on the page)",
            "license": "no terms stated on the archive's pages",
            "changes": "posed into a levade (render-raytracing.py: levade()), marble, on a plinth"}
    return rec


def build_final(n, nights_only=False):
    stem, name, name_de, description, day, night, moon = FINALS[n]
    for suffix, t in (("", day), ("-dark", night)):
        if nights_only and suffix == "":
            continue
        png = rt.RAW / "final" / f"{stem}{suffix}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        seconds = render(n, t, png, rt.W, rt.H, moon)
        Image.open(png).convert("RGB").save(THEME / f"{stem}{suffix}.jpg", quality=JPEG_QUALITY, optimize=True,
                                           progressive=True)
        (THEME / f"{stem}{suffix}.json").write_text(json.dumps(record(n, t, suffix, seconds), indent=2,
                                                               ensure_ascii=False) + "\n")
        print(f"  {stem}{suffix}: {seconds:.0f} s, {(THEME / f'{stem}{suffix}.jpg').stat().st_size // 1024} KB")


def final_sheet():
    """Day | night for every chosen draft."""
    W, H = 480, 270
    font = ImageFont.truetype(FONT, 24)
    items = [v[0] for v in FINALS.values() if (THEME / f"{v[0]}.jpg").exists()]
    cols = 2
    sheet = Image.new("RGB", (cols * (2 * W + 16), math.ceil(len(items) / cols) * (H + 8)), "black")
    for i, stem in enumerate(items):
        x, y = (i % cols) * (2 * W + 16), (i // cols) * (H + 8)
        for j, suffix in enumerate(("", "-dark")):
            im = Image.open(THEME / f"{stem}{suffix}.jpg").resize((W, H), Image.LANCZOS)
            sheet.paste(im, (x + j * W, y))
        d = ImageDraw.Draw(sheet)
        d.rectangle((x, y, x + 16 + 16 * len(stem), y + 30), fill=(0, 0, 0))
        d.text((x + 6, y + 2), stem, font=font, fill=(255, 220, 0))
    sheet.save(rt.RAW / "final-kontaktbogen.png")


def main(args):
    OUT.mkdir(parents=True, exist_ok=True)
    if "--build" in args:
        # The chosen drafts at 3840x2160, day and night, into the theme.
        picks = [int(a) if a.isdigit() else a for a in args if not a.startswith("--")] or list(FINALS)
        for n in picks:
            build_final(n, nights_only="--nights" in args)
        final_sheet()
        return 0
    if "--check" in args:
        # Previews of what the finals add: every night with its moon, the
        # day pictures of the night drafts.
        for n, (stem, *_x, day, night, moon) in FINALS.items():
            for t in (day, night):
                if t != "night":
                    continue
                png = OUT / "check" / f"{label(n)}-{t}.png"
                png.parent.mkdir(exist_ok=True)
                render(n, t, png, 1280, 720, moon)
        return 0
    if "--final" in args:
        n = args[args.index("--final") + 1]
        n = int(n) if n.isdigit() else n
        desc, day, night, *_ = DRAFTS[n]
        for t in [day] + ([night] if night else []):
            png = OUT / f"final-{label(n)}-{t}.png"
            s = render(n, t, png, rt.W, rt.H)
            print(f"  {png.name}: {s:.0f} s")
        return 0
    nums = [int(a) if a.isdigit() else a for a in args] or sorted(DRAFTS, key=order)
    for n in nums:
        s = render(n, None, OUT / f"{label(n)}.png", 1280, 720)
        print(f"  {label(n)}: {s:.0f} s  {DRAFTS[n][0]}")
    have = sorted((n for n in DRAFTS if (OUT / f"{label(n)}.png").exists()), key=order)
    if any(isinstance(n, int) and n <= 30 for n in nums):
        contact_sheet([n for n in have if isinstance(n, int) and n <= 30])
    if any(not (isinstance(n, int) and n <= 30) for n in nums):
        contact_sheet([n for n in have if not (isinstance(n, int) and n <= 30)], "kontaktbogen-2.png")
    lines = ["# Ray-traced drafts (Warp Legacy)", "",
             "POV-Ray 3.7, 1280x720. Chosen by number; a chosen draft is rendered at 3840x2160 with its",
             "day/night partner by `os2-warp/tools/raytracing-drafts.py --final N`.", "",
             "| No. | Draft | Time of day | Night partner |", "|---|---|---|---|"]
    for n in sorted(DRAFTS, key=order):
        desc, day, night, *_r = DRAFTS[n]
        lines.append(f"| {label(n)} | {desc} | {day} | {night or '-'} |")
    lines += ["", "Statue: the horse from the Georgia Tech Large Geometric Models Archive",
              "(sites.cc.gatech.edu/projects/large_models/horse.html, originally a Cyberware scan),",
              "posed into a levade in render-raytracing.py."]
    (OUT / "LISTE.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
