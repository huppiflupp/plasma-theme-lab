"""Farbrechnung: aus wenigen Grundfarben (vom LLM) die volle Palette.

Das LLM wählt nur die Farben, die Charakter tragen. Kanten, Hover,
Textvarianten und Signalfarben leitet dieser Code ab — dort macht ein
Sprachmodell Fehler, die man nicht sieht, bis das Theme läuft.
"""
import colorsys


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def mix(a, b, t):
    """t=0 → a, t=1 → b"""
    ra, rb = rgb(a), rgb(b)
    return hexc([x + (y - x) * t for x, y in zip(ra, rb)])


def luminance(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def on(bg):
    """Schwarz oder Weiß — was auf `bg` besser lesbar ist."""
    return "#ffffff" if contrast(bg, "#ffffff") >= contrast(bg, "#000000") else "#000000"


def shift(h, dl):
    """Helligkeit in HLS verschieben (dl in -1..1)."""
    r, g, b = (v / 255 for v in rgb(h))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, l + dl))
    return hexc([v * 255 for v in colorsys.hls_to_rgb(hh, l, s)])


def readable(fg, bg, minimum=4.5):
    """`fg` so lange aufhellen/abdunkeln, bis er auf `bg` lesbar ist."""
    if contrast(fg, bg) >= minimum:
        return fg
    direction = 1 if luminance(bg) < 0.18 else -1
    c = fg
    for _ in range(40):
        c = shift(c, 0.025 * direction)
        if contrast(c, bg) >= minimum:
            return c
    return on(bg)


def derive(c, mode):
    """Grundfarben eines Variants → vollständige Palette (gemeinsame Schlüssel
    der Lab-Generatoren: surface, window, panel, light, dark, border, …)."""
    dark_mode = mode == "dark"
    surface = c["surface"]
    p = {
        "surface": surface,
        "window": c["window"],
        "panel": c["panel"],
        "text": c["text"],
        "desktop": c["desktop"],
        "accent": c["accent"],
        "glow": c["glow"],
        "title_active": c["title_active"],
        "title_inactive": c["title_inactive"],
    }
    # Bevel: im Dunkeln wirkt eine helle Kante schnell wie ein Rahmen —
    # deshalb dort sanfter aufhellen, dafür kräftiger abdunkeln.
    p["light"] = shift(surface, 0.12 if dark_mode else 0.14)
    p["dark"] = shift(surface, -0.16 if dark_mode else -0.24)
    p["border"] = shift(surface, -0.30) if not dark_mode else hexc(
        [v * 0.35 for v in rgb(surface)])
    p["checker"] = shift(surface, 0.06 if dark_mode else 0.10)
    p["text2"] = readable(mix(c["text"], surface, 0.35), surface, 3.0)
    p["selection"] = c["accent"]
    p["selection_text"] = on(c["accent"])
    p["active"] = c["accent"]
    # Hover trägt Text (Listen, Taskleiste): so weit zur Fläche mischen, bis
    # er lesbar ist — beim Pip-Boy-Test war grüner Text auf Petrol unlesbar.
    for t in (0.45, 0.55, 0.65, 0.75, 0.85, 0.92):
        p["hover"] = mix(c["glow"], surface, t)
        if contrast(c["text"], p["hover"]) >= 4.5:
            break
    else:
        # Leuchtfarbe und Text vertragen sich nicht: Hover als leicht
        # veränderte Fläche — weniger farbig, aber lesbar.
        for dl in (0.06, 0.04, 0.02, -0.02, -0.04):
            p["hover"] = shift(surface, dl if dark_mode else -dl)
            if contrast(c["text"], p["hover"]) >= 4.5:
                break
    p["title_active_text"] = on(c["title_active"])
    p["title_inactive_text"] = readable(mix(on(c["title_inactive"]), c["title_inactive"], 0.3),
                                        c["title_inactive"], 3.0)
    p["link"] = readable(c["glow"], c["window"])
    p["visited"] = readable(mix(c["glow"], "#8040c0", 0.5), c["window"])
    # Signalfarben: feste Töne, nur auf Lesbarkeit gezogen
    p["error"] = readable("#d03030" if not dark_mode else "#ff5a4a", c["window"])
    p["warning"] = readable("#b06a00" if not dark_mode else "#f0a020", c["window"])
    p["positive"] = readable("#2a7a3a" if not dark_mode else "#50c060", c["window"])
    return p
