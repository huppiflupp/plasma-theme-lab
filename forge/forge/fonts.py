"""A curated font catalogue (SIL OFL / Apache, from github.com/google/fonts).

The LLM chooses from this catalogue by enum; the engine downloads the file
into a cache and ships it with the theme (GRUB needs .pf2, Plymouth/SDDM the TTF).
"""
import os
import urllib.request

RAW = "https://github.com/google/fonts/raw/main/"
CACHE = os.path.expanduser("~/.cache/theme-forge/fonts")

# key: (family name, path in the google/fonts repo, character)
CATALOG = {
    "russo-one": ("Russo One", "ofl/russoone/RussoOne-Regular.ttf",
                  "heavy, angular, military-technical, 90s strategy game"),
    "black-ops-one": ("Black Ops One", "ofl/blackopsone/BlackOpsOne-Regular.ttf",
                      "stencil lettering, military, crate markings"),
    "rajdhani": ("Rajdhani", "ofl/rajdhani/Rajdhani-SemiBold.ttf",
                 "narrow, technical, cockpit display, very legible"),
    "oxanium": ("Oxanium", "ofl/oxanium/Oxanium%5Bwght%5D.ttf",
                "science fiction, angular, spaceship console"),
    "orbitron": ("Orbitron", "ofl/orbitron/Orbitron%5Bwght%5D.ttf",
                 "science fiction, wide, futuristic, retro future"),
    "exo-2": ("Exo 2", "ofl/exo2/Exo2%5Bwght%5D.ttf",
              "modern technical, neutral futuristic"),
    "share-tech-mono": ("Share Tech Mono", "ofl/sharetechmono/ShareTechMono-Regular.ttf",
                        "monospace, terminal, hacker"),
    "vt323": ("VT323", "ofl/vt323/VT323-Regular.ttf",
              "pixel terminal, 1980s computer"),
    "press-start-2p": ("Press Start 2P", "ofl/pressstart2p/PressStart2P-Regular.ttf",
                       "8-bit pixels, arcade"),
    "cinzel": ("Cinzel", "ofl/cinzel/Cinzel%5Bwght%5D.ttf",
               "Roman capitals, fantasy, noble"),
    "fredoka": ("Fredoka", "ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf",
                "round, friendly, playful, children"),
    "special-elite": ("Special Elite", "apache/specialelite/SpecialElite-Regular.ttf",
                      "typewriter, dossier, noir"),
    "ibm-plex-sans": ("IBM Plex Sans", "ofl/ibmplexsans/IBMPlexSans%5Bwdth,wght%5D.ttf",
                      "sober, office, corporate"),
}


def describe():
    return "\n".join(f"- {k}: {v[2]}" for k, v in CATALOG.items())


def fetch(key):
    """Downloads the font (once) and returns (family name, local path)."""
    family, path, _ = CATALOG[key]
    os.makedirs(CACHE, exist_ok=True)
    dst = os.path.join(CACHE, key + ".ttf")
    if not os.path.exists(dst):
        data = urllib.request.urlopen(RAW + path, timeout=60).read()
        if not data.startswith((b"\x00\x01\x00\x00", b"true", b"OTTO")):
            raise RuntimeError(f"{key}: no font file at {path}")
        with open(dst + ".part", "wb") as f:
            f.write(data)
        os.replace(dst + ".part", dst)
    return family, dst


def static(key, weight=600):
    """A fixed instance of a variable font (else every tool takes the
    default instance — for Oxanium "ExtraLight", hardly legible in GRUB and
    Plymouth). For static fonts the file unchanged."""
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
                loc[tag] = None        # pin the axis to its default
        inst = instancer.instantiateVariableFont(font, {k: v for k, v in loc.items() if v is not None},
                                                 updateFontNames=False)
        if any(v is None for v in loc.values()):
            inst = instancer.instantiateVariableFont(inst, {k: None for k, v in loc.items() if v is None})
        inst.save(dst + ".part")
        os.replace(dst + ".part", dst)
    return family, dst
