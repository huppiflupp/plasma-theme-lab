"""Places: RISC OS's folder with the emblem of what it holds; the coloured
folders recoloured; brand folders (git, deb, …) with a word on the front
instead of somebody's logo."""
from base import folder, page, plaque
from glyphs import glyph

COLOURS = {"black": ("#5a5f69", "#30343b"), "blue": ("#8fd0ff", "#3d97e6"), "brown": ("#d8a878", "#9a6436"),
           "cyan": ("#8ff0f0", "#2ab8c8"), "green": ("#a9e8a0", "#4fae47"), "grey": ("#d6d6d6", "#9a9a9a"),
           "magenta": ("#f5a0e6", "#c43fae"), "orange": ("#ffc880", "#e88a1a"), "red": ("#ff9a90", "#d33a2c"),
           "violet": ("#c8a8ff", "#7a4fd8"), "yellow": ("#fff08a", "#e0c21c")}

EMBLEM = {
    "folder-activities": "activities", "folder-book": "book", "folder-bookmark": "bookmark", "folder-build": "hammer",
    "folder-calculate": "calculator", "folder-chart": "chart-bar", "folder-cloud": "cloud", "folder-comic": "chat",
    "folder-crash": "crash", "folder-database": "database", "folder-decrypted": "eye", "folder-design": "compass-draw",
    "folder-desktop": "desktop", "folder-development": "code", "folder-documents": "page", "folder-download": "download",
    "folder-drawing": "pencil", "folder-encrypted": "lock", "folder-extension": "extension", "folder-favorites": "star",
    "folder-games": "game", "folder-html": "globe", "folder-image-people": "people", "folder-important": "exclamation",
    "folder-language": "language", "folder-library": "bank", "folder-locked": "key", "folder-log": "log",
    "folder-mail": "envelope", "folder-network": "network", "folder-notes": "sticky-note", "folder-paint": "brush",
    "folder-pictures": "picture", "folder-podcast": "podcast", "folder-presentation": "presentation",
    "folder-print": "printer", "folder-publicshare": "share", "folder-remote": "link", "folder-root": "harddisk",
    "folder-script": "terminal", "folder-sign": "signature", "folder-sound": "music", "folder-table": "table",
    "folder-temp": "hourglass", "folder-templates": "pages", "folder-text": "lines", "folder-trash": "trash",
    "folder-unlocked": "unlock", "folder-videos": "film", "user-desktop": "monitor", "user-home": "house",
    "folder_html": "at",
}
WORDS = {"folder-android": "And", "folder-appimage": "AI", "folder-blender": "Bl", "folder-deb": "deb",
         "folder-docker": None, "folder-flatpak": "Fp", "folder-gdrive": "GD", "folder-git": None,
         "folder-godot": "Gd", "folder-java": "Java", "folder-mac": "Mac", "folder-rpm": "rpm", "folder-snap": "Snp",
         "folder-tar": "tar", "folder-windows": "Win"}
SMALL_HUES = ("red", "blue", "orange", "violet", "brown", "cyan", "green", "grey", "yellow",
              "ink", "red", "blue", "orange", "violet", "brown")
WORD_GLYPH = {"folder-docker": "container", "folder-git": "branch"}


def draw(name, c):
    if name == "folder":
        return folder(c)
    if name == "folder-open":
        return folder(c, open_=True)
    if name.startswith("folder-") and name[7:] in COLOURS:
        return folder(c, color=COLOURS[name[7:]])
    if name in EMBLEM:
        return folder(c, EMBLEM[name])
    if name in WORD_GLYPH:
        return folder(c, WORD_GLYPH[name])
    if name in WORDS:
        folder(c)
        if not c.small:
            c.text(24, 36, WORDS[name], 10 if len(WORDS[name]) <= 3 else 8.5, c.darken(c["folder"][1], 0.55))
        else:
            # 16/22 px: the word does not fit; a plaque in the brand's own
            # colour with its first two letters keeps them apart.
            hue = SMALL_HUES[sorted(WORDS).index(name) % len(SMALL_HUES)]
            c.rect(13, 25, 22, 14, c[hue], 2.5, None)
            c.text(24, 36, (WORDS[name] or name[7:9]).upper()[:2], 11, "#ffffff")
        return True
    if name == "document-multiple":
        c.group("translate(-4 -3)", lambda cv: page(cv))
        return page(c, lines=True)
    if name.startswith("mail-folder-"):
        what = {"inbox": "inbox", "outbox": "upload", "sent": "send"}[name[12:]]
        return folder(c, what)
    if name == "mail-message":
        c.rect(5, 11, 38, 26, c.grad(c["page"]), 2)
        c.path("M5 12 L24 27 L43 12", "none")
        return True
    if name == "network-server-database":
        glyph(c, "server", 6, 4, 32, c["ink"]); plaque(c, "database", c["blue"])
        return True
    if name == "network-workgroup":
        glyph(c, "network", 4, 4, 40, c["ink"])
        return True
    if name == "user-identity":
        c.circle(24, 24, 19, c.grad(c["folder"]))
        glyph(c, "user", 10, 10, 28, c["ink"])
        return True
    if name in ("user-trash", "user-trash-full"):
        can = c.grad(c["metal"], horizontal=True)
        c.path("M12 14 h24 l-2 28 a2 2 0 0 1 -2 2 h-16 a2 2 0 0 1 -2 -2 z", can)
        c.rect(9, 10, 30, 5, c.lighten(c["metal"][1], 0.3), 1.5)
        if name.endswith("full"):
            c.path("M13 10 c3 -6 9 -2 11 -6 c3 4 8 1 11 6 z", c.grad(c["page"]))
            c.rect(9, 10, 30, 5, c.lighten(c["metal"][1], 0.3), 1.5)
        if not c.small:
            c.line("M19 20 v18 M24 20 v18 M29 20 v18", c.darken(c["metal"][1], 0.3), 1.4)
        return True
    return None
