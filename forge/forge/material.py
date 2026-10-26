"""Material: a painted metal surface per variant.

ComfyUI paints a sheet of metal; tint() tints it so that its mean hits the
palette colour exactly and only the grain remains. So the palette's contrast
checks still hold although surfaces now carry texture. It is embedded as
<image> with a data URI — QtSvg can do that (Plasma, KWin); patterns
(<pattern>) and masks it cannot.
"""
import base64
import io
import os
import zlib

from PIL import Image, ImageFilter, ImageOps

from . import comfy
from .palette import rgb

FALLBACK_SIZE = (1024, 256)


def texture(prompt, dst, log=print):
    """Raw sheet metal (cached). Without ComfyUI: brushed noise."""
    if not os.path.exists(dst):
        try:
            comfy.generate(prompt, 1024, 256, zlib.crc32(prompt.encode()) % 10**6, dst, log=log)
        except Exception as e:  # noqa: BLE001
            log(f"  ComfyUI not available ({str(e)[:120]}) — procedural texture")
            noise = Image.effect_noise(FALLBACK_SIZE, 40).filter(ImageFilter.BoxBlur(0))
            noise = noise.resize((FALLBACK_SIZE[0] // 8, FALLBACK_SIZE[1])).resize(FALLBACK_SIZE)
            noise.convert("RGB").save(dst)
    return Image.open(dst).convert("RGB")


def tint(tex, color, strength=0.16):
    """Carry the grain of `tex` over to `color`; mean = color.

    Normalised to the texture's spread: brushed metal spreads only by ±18
    steps — carried over linearly, 7 % of it remained and the area looked
    plain. Now one standard deviation is `strength` (16 %) of lightness."""
    lum = ImageOps.grayscale(tex)
    hist = lum.histogram()
    n = max(1, sum(hist))
    mean = sum(i * c for i, c in enumerate(hist)) / n
    std = max(4.0, (sum(c * (i - mean) ** 2 for i, c in enumerate(hist)) / n) ** 0.5)
    r, g, b = rgb(color)

    def lut(base):
        return [max(0, min(255, round(base * (1 + max(-2.5, min(2.5, (i - mean) / std)) * strength))))
                for i in range(256)]
    return Image.merge("RGB", (lum.point(lut(r)), lum.point(lut(g)), lum.point(lut(b))))


def data_uri(img, size=None, quality=None):
    if size:
        img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def strip(img, w, h, vertical=False, offset=0):
    """A crop in the fitting direction: grinding marks run along the
    stretched axis — then KSvg's stretching looks like metal."""
    if vertical:
        img = img.rotate(90, expand=True)
    W, H = img.size
    x = min(offset, max(0, W - w))
    return img.crop((x, 0, x + min(w, W), min(h, H))).resize((max(1, w), max(1, h)), Image.LANCZOS)
