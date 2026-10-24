"""Kuratierter Schriftkatalog (SIL OFL / Apache, aus github.com/google/fonts).

Das LLM wählt per Enum aus diesem Katalog; der Motor lädt die Datei in einen
Cache und legt sie dem Theme bei (GRUB braucht .pf2, Plymouth/SDDM die TTF).
"""
import os
import urllib.request

RAW = "https://github.com/google/fonts/raw/main/"
CACHE = os.path.expanduser("~/.cache/theme-forge/fonts")

# Schlüssel: (Familienname, Pfad im google/fonts-Repo, Charakter)
CATALOG = {
    "russo-one": ("Russo One", "ofl/russoone/RussoOne-Regular.ttf",
                  "schwer, kantig, militärisch-technisch, Strategiespiel der 90er"),
    "black-ops-one": ("Black Ops One", "ofl/blackopsone/BlackOpsOne-Regular.ttf",
                      "Schablonenschrift, Militär, Kisten-Aufdruck"),
    "rajdhani": ("Rajdhani", "ofl/rajdhani/Rajdhani-SemiBold.ttf",
                 "schmal, technisch, Cockpit-Anzeige, gut lesbar"),
    "oxanium": ("Oxanium", "ofl/oxanium/Oxanium%5Bwght%5D.ttf",
                "Science-Fiction, eckig, Raumschiff-Konsole"),
    "orbitron": ("Orbitron", "ofl/orbitron/Orbitron%5Bwght%5D.ttf",
                 "Science-Fiction, breit, futuristisch, Retro-Zukunft"),
    "exo-2": ("Exo 2", "ofl/exo2/Exo2%5Bwght%5D.ttf",
              "modern-technisch, neutral-futuristisch"),
    "share-tech-mono": ("Share Tech Mono", "ofl/sharetechmono/ShareTechMono-Regular.ttf",
                        "Monospace, Terminal, Hacker"),
    "vt323": ("VT323", "ofl/vt323/VT323-Regular.ttf",
              "Pixel-Terminal, 80er-Jahre-Computer"),
    "press-start-2p": ("Press Start 2P", "ofl/pressstart2p/PressStart2P-Regular.ttf",
                       "8-Bit-Pixel, Arcade"),
    "cinzel": ("Cinzel", "ofl/cinzel/Cinzel%5Bwght%5D.ttf",
               "römische Versalien, Fantasy, edel"),
    "fredoka": ("Fredoka", "ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf",
                "rund, freundlich, verspielt, Kinder"),
    "special-elite": ("Special Elite", "apache/specialelite/SpecialElite-Regular.ttf",
                      "Schreibmaschine, Akte, Noir"),
    "ibm-plex-sans": ("IBM Plex Sans", "ofl/ibmplexsans/IBMPlexSans%5Bwdth,wght%5D.ttf",
                      "nüchtern, Büro, Corporate"),
}


def describe():
    return "\n".join(f"- {k}: {v[2]}" for k, v in CATALOG.items())


def fetch(key):
    """Lädt die Schrift (einmalig) und liefert (Familienname, lokaler Pfad)."""
    family, path, _ = CATALOG[key]
    os.makedirs(CACHE, exist_ok=True)
    dst = os.path.join(CACHE, key + ".ttf")
    if not os.path.exists(dst):
        data = urllib.request.urlopen(RAW + path, timeout=60).read()
        if not data.startswith((b"\x00\x01\x00\x00", b"true", b"OTTO")):
            raise RuntimeError(f"{key}: keine Schriftdatei unter {path}")
        with open(dst + ".part", "wb") as f:
            f.write(data)
        os.replace(dst + ".part", dst)
    return family, dst


def static(key, weight=600):
    """Feste Instanz einer variablen Schrift (sonst nimmt jedes Werkzeug die
    Standardinstanz — bei Oxanium „ExtraLight“, in GRUB und Plymouth kaum
    lesbar). Für statische Schriften die Datei unverändert."""
    family, path = fetch(key)
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    if "fvar" not in font:
        return family, path
    dst = os.path.join(CACHE, f"{key}-{weight}.ttf")
    if not os.path.exists(dst):
        from fontTools.varLib import instancer
        axes = {a.axisTag: (a.minValue, a.maxValue) for a in font["fvar"].axes}
        loc = {}
        for tag, (lo, hi) in axes.items():
            if tag == "wght":
                loc[tag] = max(lo, min(hi, weight))
            else:
                loc[tag] = None        # Achse auf Standardwert festlegen
        inst = instancer.instantiateVariableFont(font, {k: v for k, v in loc.items() if v is not None},
                                                 updateFontNames=False)
        if any(v is None for v in loc.values()):
            inst = instancer.instantiateVariableFont(inst, {k: None for k, v in loc.items() if v is None})
        inst.save(dst + ".part")
        os.replace(dst + ".part", dst)
    return family, dst
