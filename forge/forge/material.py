"""Material: eine gemalte Metalloberfläche je Variante.

ComfyUI malt ein Blech; tint() färbt es so ein, dass sein Mittelwert genau
die Palettenfarbe trifft und nur die Maserung übrig bleibt. Damit gelten die
Kontrastprüfungen der Palette weiter, obwohl Flächen jetzt Textur tragen.
Eingebettet wird es als <image> mit data-URI — das kann QtSvg (Plasma,
KWin); Muster (<pattern>) und Masken kann es nicht.
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
    """Rohes Blech (cached). Ohne ComfyUI: gebürstetes Rauschen."""
    if not os.path.exists(dst):
        try:
            comfy.generate(prompt, 1024, 256, zlib.crc32(prompt.encode()) % 10**6, dst, log=log)
        except Exception as e:  # noqa: BLE001
            log(f"  ComfyUI nicht verfügbar ({str(e)[:120]}) — Textur prozedural")
            noise = Image.effect_noise(FALLBACK_SIZE, 40).filter(ImageFilter.BoxBlur(0))
            noise = noise.resize((FALLBACK_SIZE[0] // 8, FALLBACK_SIZE[1])).resize(FALLBACK_SIZE)
            noise.convert("RGB").save(dst)
    return Image.open(dst).convert("RGB")


def tint(tex, color, strength=0.16):
    """Maserung von `tex` auf `color` übertragen; Mittelwert = color.

    Auf die Streuung der Textur normiert: gebürstetes Blech streut nur um
    ±18 Stufen — linear übertragen blieb davon 7 % übrig, die Fläche wirkte
    einfarbig. Jetzt ist eine Standardabweichung `strength` (16 %) Helligkeit."""
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
    """Ausschnitt in passender Richtung: Schleifspuren laufen entlang der
    gestreckten Achse — dann sieht das Strecken durch KSvg nach Metall aus."""
    if vertical:
        img = img.rotate(90, expand=True)
    W, H = img.size
    x = min(offset, max(0, W - w))
    return img.crop((x, 0, x + min(w, W), min(h, H))).resize((max(1, w), max(1, h)), Image.LANCZOS)
