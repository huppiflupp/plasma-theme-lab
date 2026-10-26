"""Rasterise 9-patch frames from Plasma SVGs — the way KSvg does it.

Plasma cuts elements out of the SVG by id and stretches the edges. The same
here with QtSvg (the renderer Plasma uses as well), so that GRUB pictures,
Plymouth boxes and the preview carry exactly the Plasma style's shapes.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QByteArray, QRectF  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

_app = QGuiApplication.instance() or QGuiApplication([])
PARTS = ["topleft", "top", "topright", "left", "center", "right",
         "bottomleft", "bottom", "bottomright"]


def _to_pil(img):
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    return Image.frombuffer("RGBA", (img.width(), img.height()),
                            bytes(img.constBits()), "raw", "RGBA", img.bytesPerLine(), 1)


def renderer(svg_text):
    r = QSvgRenderer(QByteArray(svg_text.encode()))
    if not r.isValid():
        raise ValueError("invalid SVG")
    return r


def element(r, eid, w, h, scale=1):
    img = QImage(max(1, round(w * scale)), max(1, round(h * scale)), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r.render(p, eid, QRectF(0, 0, img.width(), img.height()))
    p.end()
    return _to_pil(img)


def parts(r, prefix, scale=1):
    """The nine elements at natural size (times scale)."""
    out = {}
    for part in PARTS:
        eid = f"{prefix}-{part}" if prefix else part
        if not r.elementExists(eid):
            raise KeyError(f"element missing: {eid}")
        b = r.boundsOnElement(eid)
        out[part] = element(r, eid, b.width(), b.height(), scale)
    return out


def compose(p, w, h):
    """Put a 9-patch together at w×h (edges and middle stretched)."""
    lw, th = p["topleft"].size
    rw, bh = p["bottomright"].size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mw, mh = max(1, w - lw - rw), max(1, h - th - bh)

    def put(part, x, y, ww, hh):
        im.alpha_composite(p[part].resize((ww, hh), Image.NEAREST) if p[part].size != (ww, hh)
                           else p[part], (x, y))
    put("top", lw, 0, mw, th)
    put("bottom", lw, h - bh, mw, bh)
    put("left", 0, th, lw, mh)
    put("right", w - rw, th, rw, mh)
    put("center", lw, th, mw, mh)
    put("topleft", 0, 0, lw, th)
    put("topright", w - rw, 0, rw, th)
    put("bottomleft", 0, h - bh, lw, bh)
    put("bottomright", w - rw, h - bh, rw, bh)
    return im


def frame(svg_text, prefix, w, h, scale=1):
    return compose(parts(renderer(svg_text), prefix, scale), w, h)
