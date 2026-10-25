"""fam_mimetypes.py: file types as RISC OS draws them.

Every file is base.page(): the type's short name in capitals on a coloured
band (JPEG, PDF, ZIP, C++ ...) and an emblem on the page that says what is
inside. The colour follows the kind of content (one family per kind):

  text / config   grey        code        blue, cyan, violet, red per language
  images          green       audio       orange       video   red
  archives        brown       packages    brown/green  fonts   violet
  office text     blue        sheets      green        slides  orange
  keys, secrets   ochre       machines    cyan

The generic types (text-x-generic, image-x-generic, x-office-*) carry no
band, only a large emblem. Templates get a dashed stencil frame, a set of
several files a second page behind.
"""
from base import page
from glyphs import D, F, O, S, W, glyph, reg


# ---- glyphs of this family ------------------------------------------------
@reg("mime-braces")
def _(c, k):
    S(c, "M9 4 C6 4 7.5 9 6 11 C5.4 11.8 4 12 4 12 C4 12 5.4 12.2 6 13 C7.5 15 6 20 9 20"
         " M15 4 C18 4 16.5 9 18 11 C18.6 11.8 20 12 20 12 C20 12 18.6 12.2 18 13 C16.5 15 18 20 15 20", k)


@reg("mime-bits")
def _(c, k):
    # 1 0 / 0 1 in heavy strokes: binary data, readable at 22 px
    F(c, "M4 3 H8 V11 H4 Z M16 13 H20 V21 H16 Z", k)
    for cx, cy in ((16, 7), (6, 17)):
        c.parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="3" ry="3.4" fill="none" stroke="{k}" '
                       f'stroke-width="{W(c) * 1.5:g}"/>')


# emblem variants for the small versions of big families
@reg("mime-zipper")
def _(c, k):
    S(c, "M4 4 H20 V20 H4 Z M12 4 V20", k)
    S(c, "M9.5 7 H14.5 M9.5 10.5 H14.5 M9.5 14 H14.5", k)
    F(c, "M10 15.5 H14 V20 H10 Z", k)


@reg("mime-crate")
def _(c, k):
    S(c, "M3 6 H21 V20 H3 Z M3 6 L21 20 M21 6 L3 20", k)


@reg("mime-squeeze")
def _(c, k):
    S(c, "M3 12 H9 M6 9 L9 12 L6 15 M21 12 H15 M18 9 L15 12 L18 15 M12 3 V21", k)


@reg("mime-stack")
def _(c, k):
    S(c, "M5 4 H19 V9 H5 Z M3 11 H21 V16 H3 Z M5 18 H19 V21 H5 Z", k)


@reg("mime-pic-tall")
def _(c, k):
    S(c, "M6 3 H18 V21 H6 Z M6 17 L10 12 L14 16 L18 12", k)
    D(c, 13.5, 7.5, 1.6, k)


@reg("mime-pic-pixel")
def _(c, k):
    S(c, "M3 5 H21 V19 H3 Z", k)
    F(c, "M3 5 H9 V12 H3 Z M9 12 H15 V19 H9 Z M15 5 H21 V12 H15 Z", k)


@reg("mime-film-play")
def _(c, k):
    S(c, "M3 5 H21 V19 H3 Z", k)
    F(c, "M10 8.5 L16 12 L10 15.5 Z", k)


@reg("mime-clapper")
def _(c, k):
    S(c, "M3 10 H21 V20 H3 Z M3 10 L4 5 L20 3 L21 8 M8 4.4 L10 9 M13 3.8 L15 8.5", k)


@reg("mime-keyval")
def _(c, k):
    # [section] and key = value lines: a configuration file
    S(c, "M6 3 H4 V8 H6 M18 3 H20 V8 H18 M8 5.5 H16 M3 13 H8 M13 13 H21 M3 19 H8 M13 19 H18", k)
    D(c, 10.5, 13, 1.2, k)
    D(c, 10.5, 19, 1.2, k)


@reg("mime-flow")
def _(c, k):
    S(c, "M8 3 H16 V8 H8 Z M3 15 H10 V20 H3 Z M14 15 H21 V20 H14 Z M12 8 V11.5 M6.5 15 V11.5 H17.5 V15", k)


@reg("mime-wave")
def _(c, k):
    S(c, "M2.5 12 H5 L7 7 L9 17 L11 4 L13 20 L15 8 L17 15 L19 10 L20 12 H21.5", k)


@reg("mime-cube")
def _(c, k):
    F(c, "M4 7.5 L12 12 V21 L4 16.5 Z", k)
    S(c, "M12 3 L20 7.5 V16.5 L12 21 L4 16.5 V7.5 Z M4 7.5 L12 12 L20 7.5 M12 12 V21", k)


@reg("mime-pixfont")
def _(c, k):
    rows = (".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X")
    d = ""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "X":
                x, y = 4.5 + i * 3, 3 + j * 3
                d += f"M{x:g} {y:g} h2.8 v2.8 h-2.8 z "
    F(c, d, k)


@reg("mime-gantt")
def _(c, k):
    S(c, "M3 3 V21 H21", k)
    F(c, "M5 5 H12 V8.5 H5 Z M9 10.5 H17 V14 H9 Z M14 16 H21 V19.5 H14 Z", k)


@reg("mime-mindmap")
def _(c, k):
    O(c, 12, 12, 3.6, k)
    S(c, "M9 10 L5.5 6.5 M15 10 L18.5 6.5 M9 14 L5.5 17.5 M15 14 L18.5 17.5", k)
    for x, y in ((4.5, 5.5), (19.5, 5.5), (4.5, 18.5), (19.5, 18.5)):
        D(c, x, y, 2.2, k)


@reg("mime-keys")
def _(c, k):
    S(c, "M3 5 H21 V19 H3 Z M7.5 13 V19 M12 13 V19 M16.5 13 V19", k)
    F(c, "M6 5 H9 V13 H6 Z M10.5 5 H13.5 V13 H10.5 Z M15 5 H18 V13 H15 Z", k)


@reg("mime-diff")
def _(c, k):
    S(c, "M7 3 V11 M3 7 H11 M13 17 H21 M14 7 H21 M3 17 H10", k)


@reg("mime-angle")
def _(c, k):
    S(c, "M8 6 L3 12 L8 18 M16 6 L21 12 L16 18 M10 12 H14", k)


@reg("mime-doc")
def _(c, k):
    S(c, "M3 4 H21 M3 8 H10 M3 12 H10 M3 16 H21 M3 20 H15 M13 7 H21 V13 H13 Z", k)


@reg("mime-heading")
def _(c, k):
    S(c, "M4 5 H15", k, W(c) * 2.0)
    S(c, "M4 11 H20 M4 15 H20 M4 19 H15", k)


# ---- the table ------------------------------------------------------------
# name: (band label or None, colour, emblem or None, flags)
# colour: a world colour key, "+" lighter, "-" darker; flags: "tpl"
# (template: dashed stencil frame), "stack" (several files), "lines".
T = {
    # packages and installers
    "android-package-archive": ("APK", "green", "box"),
    "application-vnd.android.app-bundle": ("AAB", "green", "archive"),
    "application-vnd.appimage": ("APPIMG", "cyan", "box"),
    "application-vnd.flatpak.ref": ("FLATPK", "cyan", "download"),
    "application-vnd.snap": ("SNAP", "brown", "box"),
    "application-x-deb": ("DEB", "brown", "box"),
    "application-x-rpm": ("RPM", "brown", "box"),
    "application-x-msdownload": ("MSI", "grey", "box"),
    "package-x-generic": (None, "brown", "box"),
    "text-x-rpm-spec": ("SPEC", "brown", "list"),
    # passes, certificates, secrets
    "application-vnd.apple.pkpass": ("PASS", "grey", "ticket"),
    "application-vnd.apple.pkpasses": ("PASSES", "grey", "ticket"),
    "apple-vnd.apple.pkpasses": ("PASSES", "grey", "ticket", "stack"),
    "application-certificate": ("CERT", "yellow-", "shield"),
    "application-pgp-encrypted": ("PGP", "yellow-", "lock"),
    "application-pgp-signature": ("SIG", "yellow-", "signature"),
    "application-x-pem-key": ("PEM", "yellow-", "key"),
    "application-x-openvpn-profile": ("OVPN", "green-", "vpn"),
    # documents
    "application-pdf": ("PDF", "red", "mime-doc"),
    "application-postscript": ("PS", "red-", "bezier"),
    "application-x-gzpostscript": ("PS.GZ", "red-", "archive"),
    "application-x-bzdvi": ("DVI.BZ", "brown", "lines"),
    "application-epub+zip": ("EPUB", "green-", "book"),
    "application-x-fictionbook+xml": ("FB2", "green-", "graduation"),
    "application-x-chm": ("CHM", "blue", "help"),
    "application-msword": ("DOC", "blue", "lines"),
    "application-msword-template": ("DOT", "blue", "lines", "tpl"),
    "application-msonenote": ("NOTE", "violet", "sticky-note"),
    "application-msoutlook": ("MSG", "blue", "envelope"),
    "application-vnd.ms-access": ("MDB", "red-", "database"),
    "application-vnd.ms-excel.addin.macroenabled.12": ("XLAM", "green", "puzzle"),
    "application-vnd.ms-excel.template.macroenabled.12": ("XLTM", "green", "table", "tpl"),
    "application-vnd.ms-infopath": ("XSN", "violet", "clipboard-check"),
    "application-vnd.ms-powerpoint.addin.macroenabled.12": ("PPAM", "orange", "puzzle"),
    "application-vnd.ms-powerpoint.template.macroenabled.12": ("POTM", "orange", "presentation", "tpl"),
    "application-vnd.ms-publisher": ("PUB", "cyan", "columns"),
    "application-vnd.visio": ("VSD", "blue-", "mime-flow"),
    "application-vnd.oasis.opendocument.chart": ("ODC", "cyan", "chart-bar"),
    "application-vnd.oasis.opendocument.database": ("ODB", "cyan", "database"),
    "application-vnd.oasis.opendocument.formula": ("ODF", "cyan", "sigma"),
    "application-vnd.oasis.opendocument.formula-template": ("OTF", "cyan", "sigma", "tpl"),
    "application-vnd.oasis.opendocument.presentation-template": ("OTP", "orange", "presentation", "tpl"),
    "application-vnd.oasis.opendocument.spreadsheet-template": ("OTS", "green", "table", "tpl"),
    "application-vnd.oasis.opendocument.text-template": ("OTT", "blue", "lines", "tpl"),
    "application-vnd.oasis.opendocument.web-template": ("OTH", "blue", "globe", "tpl"),
    "application-x-lyx": ("LYX", "blue-", "lines"),
    "application-xmind": ("MIND", "orange", "mime-mindmap"),
    "application-x-kplato": ("PLAN", "violet", "mime-gantt"),
    "application-x-kmymoney": ("KMY", "green", "money"),
    "application-x-skg": ("SKG", "green", "bank"),
    "application-x-skgc": ("SKGC", "green", "lock"),
    "application-x-kvtml": ("VOCAB", "green", "language"),
    "application-x-labplot2": ("LML", "cyan", "chart-line"),
    "application-x-root": ("ROOT", "cyan", "histogram"),
    "application-x-marble": ("KML", "green", "map"),
    "x-office-address-book": ("ADDR", "violet", "book"),
    "x-office-contact": ("VCARD", "violet", "user"),
    "x-office-calendar": ("ICS", "red", "calendar"),
    "x-office-document": (None, "blue", "mime-heading"),
    "x-office-spreadsheet": (None, "green", "table"),
    "x-office-presentation": (None, "orange", "presentation"),
    "x-office-drawing": (None, "violet", "shapes"),
    # data, markup, config
    "application-atom+xml": ("ATOM", "orange", "feed"),
    "application-json": ("JSON", "violet", "mime-braces"),
    "application-toml": ("TOML", "grey", "mime-keyval"),
    "application-xhtml+xml": ("XHTML", "blue", "globe"),
    "application-octet-stream": ("DATA", "grey", "mime-bits"),
    "application-x-zerosize": ("EMPTY", "grey", None),
    "application-x-partial-download": ("PART", "grey", "hourglass"),
    "application-x-macbinary": ("MACBIN", "grey", "mime-bits"),
    "application-x-python-bytecode": ("PYC", "blue-", "mime-bits"),
    "application-vnd.iccprofile": ("ICC", "violet", "color"),
    "application-vnd.nokia.xml.qt.resource": ("QRC", "green-", "mime-angle"),
    "application-x-designer": ("UI", "green", "window"),
    "application-x-gettext-translation": ("MO", "green", "language"),
    "application-x-xliff": ("XLIFF", "green", "chat"),
    "text-x-po": ("PO", "green-", "language"),
    "application-x-desktop": ("LAUNCH", "grey", "rocket"),
    "application-x-ms-shortcut": ("LNK", "grey", "link"),
    "application-x-theme": ("THEME", "violet", "palette"),
    "application-x-plasma": ("WIDGET", "blue", "panel"),
    "x-kde-nsplugin-generated": ("PLUGIN", "grey", "plug"),
    "application-x-trash": ("TRASH", "grey", "trash"),
    "application-x-bittorrent": ("TORRNT", "green", "download"),
    "application-x-smb-workgroup": ("SMB", "cyan", "network"),
    "application-x-kexi-connectiondata": ("CONN", "cyan", "link"),
    "application-x-kexiproject-shortcut": ("KEXI", "cyan", "database"),
    "application-dicom": ("DICOM", "cyan", "plus"),
    "application-x-cda": ("CDA", "orange", "disc"),
    "text-xml": ("XML", "green", "mime-angle"),
    "text-csv": ("CSV", "green", "table"),
    "text-html": ("HTML", "blue", "globe"),
    "text-rtf": ("RTF", "blue", "align-left"),
    "text-x-markdown": ("MD", "grey", "hash"),
    "text-wiki": ("WIKI", "grey", "book"),
    "text-vnd.typst": ("TYP", "blue", "text"),
    "text-x-tex": ("TEX", "blue", "sigma"),
    "text-x-texinfo": ("TEXI", "blue", "book"),
    "text-vnd.abc": ("ABC", "orange", "note"),
    "text-x-apport": ("CRASH", "red", "crash"),
    "text-x-authors": ("AUTHRS", "grey", "people"),
    "text-x-changelog": ("CHANGE", "grey", "history"),
    "text-x-install": ("SETUP", "grey", "wrench"),
    "text-x-hex": ("HEX", "grey", "chip"),
    "text-x-patch": ("PATCH", "grey", "mime-diff"),
    "text-x-generic": (None, "grey", None, "lines"),
    "message-news": ("NEWS", "blue-", "chat"),
    "message-partial": ("PART", "blue", "envelope"),
    "message-rfc822": ("EML", "blue", "envelope"),
    "application-x-srt": ("SRT", "grey", "callout"),
    # executables, libraries
    "application-x-executable": ("EXEC", "grey", "gear"),
    "application-x-ms-dos-executable": ("EXE", "grey", "terminal"),
    "application-x-sharedlib": ("SO", "grey", "puzzle"),
    "application-x-shockwave-flash": ("SWF", "red", "lightning"),
    "application-x-java": ("CLASS", "red", "mime-bits"),
    "application-x-java-archive": ("JAR", "red", "archive"),
    # archives
    "application-zip": ("ZIP", "brown", "archive"),
    "application-x-rar": ("RAR", "brown", "archive"),
    "application-x-tar": ("TAR", "brown", "archive"),
    "application-x-compressed-tar": ("TAR.GZ", "brown", "archive"),
    "application-x-bzip-compressed-tar": ("TAR.BZ", "brown", "archive"),
    "application-x-lzma-compressed-tar": ("TAR.XZ", "brown", "archive"),
    "application-x-tarz": ("TAR.Z", "brown", "archive"),
    "application-x-tzo": ("TZO", "brown", "archive"),
    "application-x-gzip": ("GZ", "brown", "archive"),
    "application-x-bzip": ("BZ2", "brown", "archive"),
    "application-x-lzop": ("LZO", "brown", "archive"),
    "application-x-ace": ("ACE", "brown", "archive"),
    "application-x-ar": ("AR", "brown", "archive"),
    "application-x-arc": ("ARC", "brown", "archive"),
    "application-x-arj": ("ARJ", "brown", "archive"),
    # disc images and virtual machines
    "application-x-cd-image": ("ISO", "grey", "disc"),
    "application-x-apple-diskimage": ("DMG", "grey", "harddisk"),
    "virtualbox-hdd": ("HDD", "cyan", "harddisk"),
    "virtualbox-vdi": ("VDI", "cyan", "harddisk"),
    "virtualbox-vmdk": ("VMDK", "cyan", "harddisk"),
    "virtualbox-ova": ("OVA", "cyan", "box"),
    "virtualbox-ovf": ("OVF", "cyan", "mime-angle"),
    "virtualbox-vbox": ("VBOX", "cyan", "monitor"),
    "virtualbox-vbox-extpack": ("EXTPK", "cyan", "puzzle"),
    # fonts
    "application-x-font-afm": ("AFM", "violet", "ruler"),
    "application-x-font-bdf": ("BDF", "violet", "mime-pixfont"),
    "application-x-font-otf": ("OTF", "violet", "font"),
    "application-x-font-ttf": ("TTF", "violet", "font"),
    "application-x-font-type1": ("TYPE1", "violet", "font"),
    # images
    "image-x-generic": (None, "green", "picture"),
    "image-bmp": ("BMP", "green", "picture"),
    "image-gif": ("GIF", "green", "picture"),
    "image-jpeg": ("JPEG", "green", "picture"),
    "image-png": ("PNG", "green", "picture"),
    "image-tiff": ("TIFF", "green", "picture"),
    "image-x-tga": ("TGA", "green", "picture"),
    "image-x-adobe-dng": ("DNG", "green", "camera"),
    "image-x-ico": ("ICO", "green", "star"),
    "image-x-psd": ("PSD", "green", "layers"),
    "image-x-xcf": ("XCF", "green", "brush"),
    "image-svg+xml-compressed": ("SVGZ", "green", "vector"),
    "image-x-vnd.trolltech.qpicture": ("QPIC", "green", "shapes"),
    "application-x-wmf": ("WMF", "green-", "shapes"),
    "application-illustrator": ("AI", "orange", "vector"),
    "image-vnd.djvu": ("DJVU", "green-", "mime-doc"),
    "image-vnd.dwg": ("DWG", "green-", "compass-draw"),
    "image-vnd.dgn": ("DGN", "green-", "ruler"),
    "application-x-krita": ("KRA", "violet", "brush"),
    "application-x-blender": ("BLEND", "orange", "mime-cube"),
    # audio
    "audio-x-generic": (None, "orange", "music"),
    "audio-x-mpeg": ("MP3", "orange", "music"),
    "audio-x-flac": ("FLAC", "orange", "music"),
    "audio-x-wav": ("WAV", "orange", "mime-wave"),
    "audio-midi": ("MIDI", "orange", "mime-keys"),
    "application-ogg": ("OGG", "orange", "note"),
    "application-x-audacity-project": ("AUP", "orange-", "mime-wave"),
    "x-media-podcast": ("CAST", "orange", "podcast"),
    # video
    "video-x-generic": (None, "red", "film"),
    "video-mp4": ("MP4", "red", "film"),
    "video-webm": ("WEBM", "red", "film"),
    "video-x-matroska": ("MKV", "red", "film"),
    "video-x-theora+ogg": ("OGV", "red", "film"),
    "video-x-wmv": ("WMV", "red", "film"),
    "application-x-kdenlive": ("KDEN", "red", "film-reel"),
    "application-x-kdenlivetitle": ("TITLE", "red", "text"),
    # game engine
    "application-x-godot-project": ("GODOT", "cyan", "game"),
    "application-x-godot-resource": ("TRES", "cyan", "box"),
    "application-x-godot-scene": ("TSCN", "cyan", "tree"),
    "application-x-godot-shader": ("SHADER", "cyan", "gradient-tool"),
    "application-x-gdscript": ("GD", "cyan", "code"),
    # source code: the code glyph and the language's short name
    "text-x-csrc": ("C", "blue", "code"),
    "text-x-chdr": ("H", "blue+", "code"),
    "text-x-c++src": ("C++", "blue-", "code"),
    "text-x-c++hdr": ("H++", "blue-", "code"),
    "text-x-csharp": ("C#", "violet", "code"),
    "text-x-python": ("PY", "blue", "code"),
    "application-x-javascript": ("JS", "yellow-", "code"),
    "application-x-perl": ("PL", "blue", "code"),
    "application-x-php": ("PHP", "violet", "code"),
    "application-x-ruby": ("RB", "red", "code"),
    "application-x-m4": ("M4", "grey", "code"),
    "text-rust": ("RS", "brown", "code"),
    "text-x-go": ("GO", "cyan", "code"),
    "text-x-kotlin": ("KT", "violet", "code"),
    "text-x-scala": ("SCALA", "red", "code"),
    "text-x-haskell": ("HS", "violet", "code"),
    "text-x-lua": ("LUA", "blue-", "code"),
    "text-x-nim": ("NIM", "yellow-", "code"),
    "text-x-pascal": ("PAS", "blue", "code"),
    "text-x-adasrc": ("ADA", "green-", "code"),
    "text-fortran": ("F90", "violet", "code"),
    "text-x-r": ("R", "blue+", "chart-line"),
    "text-x-tcl": ("TCL", "orange", "code"),
    "text-x-qml": ("QML", "green", "code"),
    "text-css": ("CSS", "blue", "mime-braces"),
    "text-x-sass": ("SASS", "red", "mime-braces"),
    "text-x-script": ("SH", "grey", "terminal"),
    "text-x-cmake": ("CMAKE", "grey", "hammer"),
    "text-dockerfile": ("DOCKER", "cyan", "container"),
}


def _colour(c, spec):
    if spec.endswith("-"):
        return c.darken(c[spec[:-1]], 0.3)
    if spec.endswith("+"):
        return c.lighten(c[spec[:-1]], 0.3)
    return c[spec]


def _frame(c):
    """A template: a dashed stencil frame round the page's content."""
    w = 1.2 * (1.6 if c.small else 1.0)
    c.parts.append(f'<rect x="11.5" y="8" width="25" height="21" rx="1.5" fill="none" stroke="{c["ink"]}" '
                   f'stroke-width="{w:g}" stroke-dasharray="{3 * w:g} {2 * w:g}"/>')


def _file(c, name, label, col, emblem, flags):
    if "stack" in flags and not c.small:
        c.group("translate(-4 -3)", lambda cv: page(cv))
    ink = c.darken(col, 0.25) if col != c["grey"] else c["ink"]
    if label is None:
        if c.small:
            page(c)
            if emblem:
                glyph(c, emblem, 11.5, 12, 25, ink, width=2.8)
            if "lines" in flags:
                c.line("M13 16 h20 M13 23 h20 M13 30 h20 M13 37 h13", c["ink"], 1.6)
            return True
        page(c, emblem=emblem, emblem_color=ink, lines="lines" in flags)
        return True
    if c.small:
        _small(c, name, emblem)
        return True
    page(c, label, col, emblem=emblem, emblem_color=ink)
    if "tpl" in flags:
        _frame(c)
    return True


# ---- 16/22 px -------------------------------------------------------------
# No word fits at 16/22 px, so the emblem is drawn large and the band
# narrow. Formats that share a kind and an emblem (the archives, the image
# formats, the languages ...) must still differ: within each such group a
# file gets its own band shade and band mark, in this order. Templates
# always carry a dashed band.
SHADES = ("base", "light", "dark")
MARKS = ("plain", "stripe", "block", "dots", "notch")
VARIANTS = [(sh, mk) for mk in MARKS for sh in SHADES]


# Big families also change their emblem at small size, the strongest cue:
SUBFAM = {
    ("brown", "archive"): ("archive", "mime-zipper", "mime-crate", "mime-squeeze", "mime-stack"),
    ("green", "picture"): ("picture", "mime-pic-tall", "mime-pic-pixel"),
    ("red", "film"): ("film", "mime-film-play", "mime-clapper"),
    ("violet", "font"): ("font", "text", "italic"),
    ("cyan", "harddisk"): ("harddisk", "partition", "multidisk"),
}


def _variants():
    groups, out = {}, {}
    for name, (label, col, emblem, *flags) in T.items():
        if label is None:
            continue
        key = (col.rstrip("+-"), emblem)
        i = groups.get(key, 0)
        groups[key] = i + 1
        alts = SUBFAM.get(key, (emblem,))
        n = len(alts)
        shade, mark = SHADES[(i // n) % 3], MARKS[i // (3 * n)]
        out[name] = (key[0], alts[i % n], shade, mark)
    return out


SMALL = _variants()


def _small(c, name, emblem):
    key, emblem, shade, mark = SMALL[name]
    base = c[key]
    col = base if shade == "base" else c.lighten(base, 0.45) if shade == "light" else c.darken(base, 0.4)
    ink = c.darken(base, 0.25) if key != "grey" else c["ink"]
    page(c)
    if emblem:
        glyph(c, emblem, 11.5, 9, 24, ink, width=2.8)
    if mark == "notch":
        # the band's left end cut away in a step
        c.path("M14 35 h26 v7 a2 2 0 0 1 -2 2 h-29 a2 2 0 0 1 -2 -2 v-3 h7 z", col)
    else:
        c.path("M7 35 h33 v7 a2 2 0 0 1 -2 2 h-29 a2 2 0 0 1 -2 -2 z", col)
    w = "#ffffff"
    if "tpl" in T[name][3:]:
        c.parts.append(f'<path d="M10 39.5 h27" stroke="{w}" stroke-width="2.4" stroke-dasharray="3.5 2.5" fill="none"/>')
    elif mark == "stripe":
        c.line("M10 39.5 h27", w, 2.0)
    elif mark == "block":
        c.rect(29, 37, 8, 5, w, 1, None)
    elif mark == "dots":
        c.circle(17, 39.5, 2.6, w, None)
        c.circle(30, 39.5, 2.6, w, None)


def draw(name, c):
    spec = T.get(name)
    if not spec:
        return None
    label, col, emblem, *flags = spec
    return _file(c, name, label, _colour(c, col), emblem, flags)
