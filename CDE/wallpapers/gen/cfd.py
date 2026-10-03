#!/usr/bin/env python3
"""Potential flow around a Joukowski airfoil, rendered as a wallpaper.

Streamlines are contours of the stream function, the background is the
pressure coefficient. Computed, not generated: both variants come from the
same field. Usage: cfd.py <light.png> <dark.png> [width height]"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (3840, 2160)
U, ALPHA = 1.0, np.radians(8)          # free stream, angle of attack
MU = complex(-0.09, 0.08)              # circle centre: thickness and camber
R = abs(1 - MU)                        # circle through z=1 -> sharp trailing edge
GAMMA = 4 * np.pi * U * R * np.sin(ALPHA + np.arcsin(MU.imag / R))  # Kutta condition

# Airfoil plane (zeta), placed right of centre; invert Joukowski numerically.
aspect = W / H
x = np.linspace(-7.5, 3.6, W // 3)
span = (x[-1] - x[0]) / aspect
y = np.linspace(-0.55 * span, 0.45 * span, H // 3)
X, Y = np.meshgrid(x, y)
zeta = X + 1j * Y
root = np.sqrt(zeta ** 2 - 4)
z = (zeta + root) / 2
z = np.where(np.abs(z - MU) < R, (zeta - root) / 2, z)   # take the branch outside the circle
inside = np.abs(z - MU) < R * 0.999
zr = (z - MU) * np.exp(-1j * ALPHA)
F = U * (zr + R ** 2 / zr) + 1j * GAMMA / (2 * np.pi) * np.log(zr)
psi = F.imag
dF = U * (1 - R ** 2 / zr ** 2) + 1j * GAMMA / (2 * np.pi * zr)
dzeta = 1 - 1 / z ** 2
vel = np.abs(dF * np.exp(-1j * ALPHA) / np.where(np.abs(dzeta) < 1e-3, 1e-3, dzeta))
cp = np.clip(1 - (vel / U) ** 2, -3, 1)
psi[inside] = np.nan
cp[inside] = np.nan

t = np.linspace(0, 2 * np.pi, 600)
circle = MU + R * np.exp(1j * t)
foil = circle + 1 / circle

THEMES = {
    "light": dict(bg="#f3efe2", field=["#f3efe2", "#cfe6f0", "#85c4ed", "#858cd9"], lines="#5586c3", foil="#3d4f8a", alpha=0.55),
    "dark": dict(bg="#070b1a", field=["#070b1a", "#0f1d3a", "#1d3f6e", "#3a3f8f"], lines="#85c4ed", foil="#c8d6f5", alpha=0.65),
}


def render(path, theme):
    t = THEMES[theme]
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(t["bg"])
    cmap = LinearSegmentedColormap.from_list("cp", t["field"])
    ax.imshow(-cp, extent=(x[0], x[-1], y[0], y[-1]), origin="lower", cmap=cmap,
              vmin=-0.6, vmax=1.4, interpolation="bicubic", aspect="auto")
    levels = np.linspace(np.nanmin(psi), np.nanmax(psi), 110)
    ax.contour(X, Y, psi, levels=levels, colors=t["lines"], linewidths=1.3, alpha=t["alpha"],
               linestyles="solid")
    ax.fill(foil.real, foil.imag, color=t["foil"], zorder=3)
    ax.set_xlim(x[0], x[-1]); ax.set_ylim(y[0], y[-1]); ax.axis("off")
    fig.savefig(path, dpi=100, facecolor=t["bg"])
    plt.close(fig)


render(sys.argv[1], "light")
render(sys.argv[2], "dark")
