"""Colour arithmetic: the full palette from a few base colours (by the LLM).

The LLM chooses only the colours that carry character. Edges, hover, text
variants and signal colours this code derives — there a language model makes
mistakes one does not see until the theme runs.
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
    """Black or white — whichever is more legible on `bg`."""
    return "#ffffff" if contrast(bg, "#ffffff") >= contrast(bg, "#000000") else "#000000"


def shift(h, dl):
    """Shift the lightness in HLS (dl in -1..1)."""
    r, g, b = (v / 255 for v in rgb(h))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, l + dl))
    return hexc([v * 255 for v in colorsys.hls_to_rgb(hh, l, s)])


def readable(fg, bg, minimum=4.5):
    """Lighten/darken `fg` until it is legible on `bg`."""
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
    """A variant's base colours → the complete palette (the lab generators'
    shared keys: surface, window, panel, light, dark, border, …)."""
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
    # Bevel: in the dark a light edge soon looks like a frame —
    # hence lighten more gently there, and darken more strongly.
    p["light"] = shift(surface, 0.12 if dark_mode else 0.14)
    p["dark"] = shift(surface, -0.16 if dark_mode else -0.24)
    p["border"] = shift(surface, -0.30) if not dark_mode else hexc(
        [v * 0.35 for v in rgb(surface)])
    p["checker"] = shift(surface, 0.06 if dark_mode else 0.10)
    p["text2"] = readable(mix(c["text"], surface, 0.35), surface, 3.0)
    p["selection"] = c["accent"]
    p["selection_text"] = on(c["accent"])
    p["active"] = c["accent"]
    # Hover carries text (lists, taskbar): mix towards the surface until it
    # is legible — in the Pip-Boy test green text on petrol was illegible.
    for t in (0.45, 0.55, 0.65, 0.75, 0.85, 0.92):
        p["hover"] = mix(c["glow"], surface, t)
        if contrast(c["text"], p["hover"]) >= 4.5:
            break
    else:
        # Glow colour and text do not go together: hover as a slightly
        # changed surface — less colourful, but legible.
        for dl in (0.06, 0.04, 0.02, -0.02, -0.04):
            p["hover"] = shift(surface, dl if dark_mode else -dl)
            if contrast(c["text"], p["hover"]) >= 4.5:
                break
    p["title_active_text"] = on(c["title_active"])
    # 4.5:1 like all other text: at 3:1 the inactive title was illegible on
    # the textured title bars (visual review, 26.10.2026).
    p["title_inactive_text"] = readable(mix(on(c["title_inactive"]), c["title_inactive"], 0.3),
                                        c["title_inactive"], 4.5)
    p["link"] = readable(c["glow"], c["window"])
    p["visited"] = readable(mix(c["glow"], "#8040c0", 0.5), c["window"])
    # Signal colours: fixed tones, only pulled to legibility
    p["error"] = readable("#d03030" if not dark_mode else "#ff5a4a", c["window"])
    p["warning"] = readable("#b06a00" if not dark_mode else "#f0a020", c["window"])
    p["positive"] = readable("#2a7a3a" if not dark_mode else "#50c060", c["window"])
    return p
