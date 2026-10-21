"""Warp Legacy Neon's mouse cursors: Plasma's Breeze cursors (breeze_cursors,
dark with a white rim) with the rim in Neon's light: cyan at the top left,
violet, pink towards the bottom right, as the window frames (NeonFrame.qml).

Made at build time from the Breeze cursors installed with Plasma, so the
repository carries none of their files: the Xcursor images (X11 programs,
older toolkits) are recoloured pixel by pixel, the SVG ones (Plasma 6 on
Wayland, cursors_scalable) get a gradient for their white fill. Breeze is
GPL-2.0-or-later, as Warp Legacy.
"""
import re
import shutil
import struct
from pathlib import Path

import numpy as np

SOURCE = Path("/usr/share/icons/breeze_cursors")
STOPS = [(0.0, (0x48, 0xcf, 0xfe)), (0.55, (0x7a, 0x4d, 0xff)), (1.0, (0xff, 0x4f, 0xd8))]
IMAGE = 0xfffd0002


def ramp(t):
    """The colour at t (0..1) along the stops, per pixel."""
    out = np.zeros(t.shape + (3,))
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        f = np.clip((t - t0) / (t1 - t0), 0, 1)[..., None]
        part = (t >= t0) & (t <= t1)
        out[part] = (np.array(c0) + (np.array(c1) - np.array(c0)) * f)[part]
    return out


def recolour(argb, w, h):
    """One image: premultiplied ARGB words. The light of a grey pixel is how
    much white it holds; that part takes the gradient, running over the
    cursor's own extent from top left to bottom right."""
    px = np.frombuffer(argb, dtype="<u4").reshape(h, w).astype(np.uint32)
    a = (px >> 24).astype(float)
    rgb = np.stack([(px >> 16) & 255, (px >> 8) & 255, px & 255], axis=-1).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        plain = np.where(a[..., None] > 0, rgb * 255 / a[..., None], 0)
    light = plain.mean(axis=-1) / 255
    ys, xs = np.nonzero(a > 128)
    if not len(xs):
        return argb
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    yy, xx = np.mgrid[0:h, 0:w]
    t = ((xx - x0) / max(1, x1 - x0) + (yy - y0) / max(1, y1 - y0)) / 2
    neon = ramp(np.clip(t, 0, 1))
    # only light and clearly coloured-free pixels: Breeze's coloured details
    # (the busy wheel, the help badge) keep their colours
    grey = (plain.max(axis=-1) - plain.min(axis=-1)) < 40
    w_ = np.where(grey, light, 0)[..., None]
    mixed = plain * (1 - w_) + neon * w_
    out = np.clip(mixed * a[..., None] / 255, 0, 255).astype(np.uint32)
    word = (a.astype(np.uint32) << 24) | (out[..., 0] << 16) | (out[..., 1] << 8) | out[..., 2]
    return word.astype("<u4").tobytes()


def xcursor(data):
    """An Xcursor file with every image recoloured; layout unchanged."""
    buf = bytearray(data)
    magic, header, version, ntoc = struct.unpack_from("<4sIII", buf, 0)
    assert magic == b"Xcur"
    for k in range(ntoc):
        kind, subtype, pos = struct.unpack_from("<3I", buf, 16 + 12 * k)
        if kind != IMAGE:
            continue
        hlen, _, _, _, w, h = struct.unpack_from("<6I", buf, pos)
        start = pos + hlen
        buf[start:start + 4 * w * h] = recolour(bytes(buf[start:start + 4 * w * h]), w, h)
    return bytes(buf)


GRADIENT = ('<linearGradient id="warpNeon" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#48cffe"/><stop offset=".55" stop-color="#7a4dff"/>'
            '<stop offset="1" stop-color="#ff4fd8"/></linearGradient>')


def svg(text):
    """White fills become the gradient, across each shape's box: the rim,
    and white faces (the busy wheel, the forbidden sign) as in the Xcursor
    images."""
    if not re.search(r'fill="#(fff|ffffff|fcfcfc)"', text, re.I):
        return text
    text = re.sub(r'fill="#(fff|ffffff|fcfcfc)"', 'fill="url(#warpNeon)"', text, flags=re.I)
    return re.sub(r"(<svg[^>]*>)", r"\1" + GRADIENT, text, count=1)


def build_cursors(out: Path, name="WarpLegacyNeonCursors", stops=None):
    """stops: three colours top left to bottom right, Neon's by default
    (Neon Blue: cyan, blue, pink)."""
    global STOPS, GRADIENT
    if stops:
        rgb = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in stops]
        STOPS = [(0.0, rgb[0]), (0.55, rgb[1]), (1.0, rgb[2])]
        GRADIENT = ('<linearGradient id="warpNeon" x1="0" y1="0" x2="1" y2="1">'
                    f'<stop offset="0" stop-color="{stops[0]}"/><stop offset=".55" stop-color="{stops[1]}"/>'
                    f'<stop offset="1" stop-color="{stops[2]}"/></linearGradient>')
    if not (SOURCE / "cursors").is_dir():
        print("Note: no Breeze cursors found, Neon keeps the system's cursors")
        return False
    theme = out / "icons" / name
    if theme.exists():
        shutil.rmtree(theme)
    for sub in ("cursors", "cursors_scalable"):
        src = SOURCE / sub
        if not src.is_dir():
            continue
        shutil.copytree(src, theme / sub, symlinks=True)
    for f in (theme / "cursors").iterdir():
        if f.is_file() and not f.is_symlink():
            f.write_bytes(xcursor(f.read_bytes()))
    if (theme / "cursors_scalable").is_dir():
        for f in (theme / "cursors_scalable").rglob("*.svg"):
            if not f.is_symlink():
                f.write_text(svg(f.read_text()))
    (theme / "index.theme").write_text(
        f"[Icon Theme]\nName={'Warp Legacy Neon Blue' if stops else 'Warp Legacy Neon'}\n"
        f"Comment=Breeze's cursors with Warp Legacy Neon's light: {'cyan, blue, pink' if stops else 'cyan, violet, pink'}\n"
        "Inherits=breeze_cursors\n")
    return True


if __name__ == "__main__":
    import sys
    build_cursors(Path(sys.argv[1]))
