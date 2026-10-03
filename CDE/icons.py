"""Original scalable workstation pictograms. No embedded bitmap data."""
from pathlib import Path

INK = "#10262b"
LIGHT = "#c9dedb"
TEAL = "#2e7180"
COPPER = "#e8874f"


def rect(x, y, w, h, fill, stroke=INK, sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def path(d, fill="none", stroke=INK, sw=2):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="miter"/>'


def circle(x, y, r, fill, stroke=INK, sw=2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def folder(mark=""):
    return (path("M5 16V10H24L30 16H57V54H5Z", TEAL) +
            path("M6 16H26L31 21H57", "none", LIGHT) +
            path("M7 11H23L28 16H7Z", COPPER, "none") +
            path("M7 24H54V51", "none", LIGHT) + mark)


def document(mark=""):
    return path("M14 5H39L51 17V58H14Z", "#c4d2d0") + path("M39 5V18H51", COPPER) + mark


def monitor(terminal=False):
    return (rect(5, 8, 54, 39, "#86a4aa") + rect(10, 13, 44, 29, "#061c22" if terminal else TEAL) +
            path("M7 45V10H57", "none", LIGHT) + rect(27, 48, 10, 6, COPPER) +
            path("M17 58L21 54H43L47 58Z", "#86a4aa") +
            (path("M16 21L22 26L16 31M28 32H39", "none", COPPER, 2.5) if terminal else path("M15 35L25 23L35 32L44 20L50 35Z", "#86a4aa", "none")))


def build_icons(out: Path):
    text = path("M21 27H44M21 33H44M21 39H44M21 45H38", "none", INK, 2.5)
    down = path("M28 23H38V37H46L33 50L20 37H28Z", COPPER)
    picture = rect(18, 27, 30, 21, COPPER) + path("M20 45L28 34L36 41L41 36L47 46Z", TEAL) + circle(40, 32, 2, LIGHT, "none")
    home = path("M6 29L31 7L58 29H51V57H13V29Z", "#afc2c2") + path("M5 29L31 7L58 29", "none", COPPER, 5) + rect(27, 36, 11, 21, TEAL) + rect(27, 21, 10, 9, TEAL) + path("M16 31V54", "none", LIGHT)
    globe = circle(32, 32, 25, TEAL) + path("M10 22L20 11L29 12L26 23L18 30L21 38L16 42L9 32Z M36 9L47 14L49 23L42 29L47 39L38 53L32 49L33 34L27 29L33 21Z", COPPER, INK, 1.5) + path("M10 20Q30 5 50 19", "none", LIGHT)
    mail = rect(6, 15, 52, 37, "#afc2c2") + path("M7 16L32 35L57 16", COPPER) + path("M7 51L24 33M57 51L40 33")
    trash = path("M13 18H51L46 57H18Z", "#86a4aa") + rect(10, 12, 44, 7, TEAL) + rect(25, 6, 15, 6, COPPER) + path("M22 25L24 50M32 25V50M42 25L40 50", "none", LIGHT, 3)
    network = rect(23, 6, 18, 15, TEAL) + path("M32 21V33M12 33H52M12 33V43M32 33V43M52 33V43") + "".join(rect(x, 43, 14, 13, COPPER) for x in (5, 25, 45))
    audio = path("M8 25H19L33 12V52L19 39H8Z", "#86a4aa") + path("M39 22Q51 32 39 42M45 14Q63 32 45 50", "none", COPPER, 4)
    gear = path("M26 5H38L40 14L47 17L55 14L61 25L54 31V37L61 43L55 54L46 51L40 55L38 62H26L24 54L17 51L9 54L3 43L10 37V30L3 24L9 14L18 17L24 13Z", "#86a4aa") + circle(32, 33, 12, TEAL) + path("M24 22Q36 14 44 27", "none", LIGHT)
    workspaces = "".join(rect(x, y, 22, 20, COPPER if i == 0 else TEAL) + path(f"M{x+3} {y+16}V{y+3}H{x+18}", "none", LIGHT) for i, (x, y) in enumerate(((7, 9), (35, 9), (7, 35), (35, 35))))
    edit = document(text) + path("M30 43L48 13L56 19L38 48L28 53Z", COPPER) + path("M30 43L38 48M48 13L56 19")
    clock = rect(8, 7, 48, 50, "#86a4aa") + circle(32, 31, 19, "#c4d2d0") + path("M32 17V31L43 37", "none", INK, 3) + rect(29, 51, 6, 3, COPPER, "none")
    cabinet = rect(10, 6, 44, 52, "#86a4aa") + rect(15, 12, 34, 18, TEAL) + rect(15, 35, 34, 18, TEAL) + rect(26, 19, 12, 4, COPPER) + rect(26, 42, 12, 4, COPPER)
    lock = path("M20 28V18C20 2 44 2 44 18V28", "none", "#afc2c2", 7) + rect(12, 26, 40, 32, TEAL) + circle(32, 39, 4, COPPER) + rect(30, 41, 4, 7, COPPER, "none")
    power = path("M23 13A22 22 0 1 0 42 13", "none", TEAL, 7) + path("M32 5V31", "none", COPPER, 7)
    logo = rect(7, 7, 50, 50, TEAL) + "".join(rect(15 if y not in (15, 45) else 22, y, 31 if y in (15, 45) else 12, 4, COPPER, "none") for y in (15, 21, 27, 33, 39, 45))
    defs = {
        "cde-menu": logo, "user-home": home, "folder": folder(),
        "folder-documents": folder(document(text).replace('stroke-width="2"', 'stroke-width="2"')),
        "folder-download": folder(down), "folder-pictures": folder(picture),
        "folder-music": folder(path("M29 44V25L44 21V39", "none", COPPER, 4) + circle(24, 44, 5, COPPER) + circle(39, 39, 5, COPPER)),
        "folder-videos": folder(rect(20, 25, 28, 25, INK) + path("M31 30L41 37L31 45Z", COPPER)),
        "folder-publicshare": folder(circle(28, 31, 5, COPPER) + circle(41, 33, 4, LIGHT) + path("M18 49Q18 36 28 37Q36 36 37 49Z", "#afc2c2") + path("M36 49V41Q46 37 49 49Z", COPPER)),
        "folder-templates": folder(rect(21, 25, 24, 25, "#c4d2d0") + path("M26 31H40M26 37H40M26 43H37")),
        "folder-development": folder(path("M20 43L31 25L44 43Z", COPPER) + path("M26 40L32 30L38 40Z", TEAL)),
        "folder-desktop": folder(rect(18, 24, 30, 21, "#afc2c2") + rect(22, 28, 22, 13, TEAL) + path("M27 49H40", "none", INK, 3)),
        "utilities-terminal": monitor(True), "computer": monitor(), "internet-web-browser": globe,
        "internet-mail": mail, "accessories-text-editor": edit, "user-trash": trash,
        "network-workgroup": network, "audio-volume-high": audio, "preferences-system": gear,
        "preferences-desktop-virtual": workspaces, "text-x-generic": document(text),
        "application-x-executable": cabinet, "drive-harddisk": cabinet, "chronometer": clock,
        "system-lock-screen": lock, "system-log-out": power,
        "help-browser": circle(32, 32, 25, "#afc2c2") + path("M23 24C23 10 47 12 42 26L32 35V40M32 47V51", "none", TEAL, 5),
        "printer": rect(17, 5, 31, 26, "#c4d2d0") + rect(7, 23, 50, 27, "#86a4aa") + rect(18, 39, 29, 20, "#c4d2d0") + rect(44, 29, 5, 4, COPPER),
        "image-x-generic": document(picture), "application-pdf": document(path("M20 43L39 23L32 46L20 43L43 39", "none", "#a32626", 3)),
        "media-playback-start": path("M18 9L53 32L18 55Z", COPPER),
        "media-playback-pause": rect(15, 11, 12, 42, TEAL) + rect(37, 11, 12, 42, TEAL),
        "dialog-ok": path("M10 31L25 47L55 14", "none", TEAL, 7),
        "dialog-cancel": path("M15 15L49 49M49 15L15 49", "none", INK, 6),
        "list-add": path("M32 10V54M10 32H54", "none", INK, 6),
        "list-remove": path("M10 32H54", "none", INK, 6),
        "edit-find": circle(27, 26, 17, "#afc2c2") + path("M40 39L56 56", "none", COPPER, 8),
        "view-refresh": path("M49 19A21 21 0 1 0 51 42M49 7V22H34", "none", TEAL, 5),
        "document-save": rect(9, 6, 46, 52, TEAL) + rect(19, 7, 26, 19, "#afc2c2") + rect(17, 35, 30, 23, "#c4d2d0") + rect(35, 10, 5, 12, INK),
        "edit-copy": document(text) + rect(7, 17, 5, 39, COPPER),
        "edit-paste": rect(10, 10, 44, 48, TEAL) + rect(17, 17, 30, 35, "#c4d2d0") + rect(24, 6, 17, 13, COPPER),
        "edit-cut": circle(18, 46, 8, TEAL) + circle(45, 46, 8, TEAL) + path("M22 40L46 8M41 40L17 8", "none", INK, 4),
        "view-list-details": "".join(rect(8, y, 8, 7, COPPER) + path(f"M23 {y+3}H56", "none", INK, 3) for y in (12, 28, 44)),
        "view-list-icons": "".join(rect(x, y, 16, 16, TEAL) for x in (10, 38) for y in (10, 38)),
    }
    # Folder document badge is scaled independently, so the folder silhouette survives.
    defs["folder-documents"] = folder('<g transform="translate(15 22) scale(.52)">' + document(text) + '</g>')
    for name, transform in (("go-previous", ""), ("go-next", "rotate(180 32 32)"), ("go-up", "rotate(90 32 32)"), ("go-down", "rotate(-90 32 32)")):
        defs[name] = f'<g transform="{transform}">' + path("M9 32L29 12V24H55V40H29V52Z", COPPER) + '</g>'
    aliases = {
        "org.kde.dolphin": "folder", "system-file-manager": "folder", "inode-directory": "folder",
        "org.kde.konsole": "utilities-terminal", "terminal": "utilities-terminal",
        "org.kde.kate": "accessories-text-editor", "org.kde.kwrite": "accessories-text-editor",
        "firefox": "internet-web-browser", "firefox-esr": "internet-web-browser", "web-browser": "internet-web-browser",
        "org.kde.falkon": "internet-web-browser", "org.kde.kmail2": "internet-mail", "mail-message-new": "internet-mail",
        "systemsettings": "preferences-system", "org.kde.systemsettings": "preferences-system",
        "folder-open": "folder", "folder-remote": "network-workgroup", "network-wired": "network-workgroup",
        "network-wireless": "network-workgroup", "network-connect": "network-workgroup",
        "network-wireless-signal-excellent": "network-workgroup", "network-wireless-connected-100": "network-workgroup",
        "audio-volume-medium": "audio-volume-high", "audio-volume-low": "audio-volume-high",
        "user-trash-full": "user-trash", "edit-delete": "user-trash", "user-desktop": "computer",
        "preferences-desktop": "computer", "video-display": "computer", "preferences-desktop-display": "computer",
        "applications-system": "preferences-system", "applications-utilities": "preferences-system",
        "applications-development": "folder-development", "applications-internet": "internet-web-browser",
        "applications-office": "text-x-generic", "applications-graphics": "image-x-generic",
        "applications-multimedia": "media-playback-start", "application-menu": "cde-menu", "start-here-kde": "cde-menu",
        "system-search": "edit-find", "document-open": "folder", "document-new": "text-x-generic",
        "document-edit": "accessories-text-editor", "application-octet-stream": "application-x-executable",
        "unknown": "text-x-generic", "text-plain": "text-x-generic", "text-x-python": "folder-development",
        "text-html": "text-x-generic", "application-x-shellscript": "utilities-terminal",
        "application-x-compressed-tar": "application-x-executable", "package-x-generic": "application-x-executable",
        "window-close": "dialog-cancel", "window-minimize": "list-remove", "window-maximize": "view-list-icons",
        "go-home": "user-home", "go-parent-folder": "go-up", "go-jump": "go-next",
        "view-hidden": "edit-find", "show-menu": "view-list-details", "overflow-menu": "view-list-details",
        "configure": "preferences-system", "configure-toolbars": "preferences-system",
        "system-reboot": "view-refresh", "system-shutdown": "system-log-out",
        "dialog-information": "help-browser", "dialog-warning": "help-browser", "dialog-error": "dialog-cancel",
        "dialog-question": "help-browser", "help-contents": "help-browser", "appointment-new": "chronometer",
        "org.kde.gwenview": "image-x-generic", "org.kde.okular": "application-pdf", "org.kde.ark": "application-x-executable",
        "preferences-desktop-wallpaper": "image-x-generic", "edit-undo": "go-previous", "edit-redo": "go-next",
    }
    defs["audio-volume-muted"] = audio + path("M8 55L55 8", "none", COPPER, 5)
    defs.update(more_icons(text, picture, home, globe, mail, trash, gear, lock, document, folder, monitor))
    defs["document-print-preview"] = defs["printer"] + badge(lens(), 26, 26, 0.6)
    for target, names in MORE_ALIASES.items():
        for name in names:
            aliases[name] = target
    # A drawing beats an older alias of the same name.
    aliases = {name: target for name, target in aliases.items() if name not in defs}
    for name in SYMBOLIC:
        base = name
        while base not in defs and base not in aliases and "-" in base:
            base = base.rsplit("-", 1)[0]
        if base in defs or base in aliases:
            aliases[name + "-symbolic"] = base
    missing = [f"{name} -> {target}" for name, target in aliases.items() if target not in defs and target not in aliases]
    if missing:
        raise RuntimeError("Icon aliases without a drawing: " + ", ".join(missing))
    theme = out / "icons/CDECopper"
    dest = theme / "scalable/all"
    # Start empty: writing a drawing through a link left by an earlier build
    # would overwrite the link's target instead.
    if dest.exists():
        import shutil
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name, body in defs.items():
        (dest / f"{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{body}</svg>\n')
    for name, original in aliases.items():
        p = dest / f"{name}.svg"
        if p.is_symlink() or p.exists():
            p.unlink()
        p.symlink_to(original + ".svg")
    (theme / "index.theme").write_text("[Icon Theme]\nName=CDE Copper\nComment=Original scalable workstation pictograms\nInherits=breeze,hicolor\nDirectories=scalable/all\n\n[scalable/all]\nSize=48\nType=Scalable\nMinSize=16\nMaxSize=512\nContext=Applications\n")


# ---- the rest of the set ---------------------------------------------------
# Same grid, outline and colours as above. Composite icons put a smaller
# pictogram on a base as a badge, as Breeze does with its emblems.
GREY, PALE, PAPER, DARK, RED = "#86a4aa", "#afc2c2", "#c4d2d0", "#061c22", "#a32626"


def badge(small, x=30, y=30, s=0.5):
    return f'<g transform="translate({x} {y}) scale({s})">{small}</g>'


def star_path(cx, cy, r1, r2, n=5):
    import math
    pts = []
    for i in range(2 * n):
        r = r1 if i % 2 == 0 else r2
        a = math.pi / n * i - math.pi / 2
        pts.append(f"{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}")
    return "M" + "L".join(pts) + "Z"


def window(body="", title=COPPER):
    return rect(5, 8, 54, 48, PAPER) + rect(5, 8, 54, 11, title) + path("M7 54V21H57", "none", "#ffffff") + body


def lens():
    return circle(26, 26, 16, PALE) + path("M16 22Q20 14 30 14", "none", "#ffffff", 3) + path("M38 38L57 57", "none", COPPER, 8) + path("M38 38L57 57", "none", INK, 1)


def more_icons(text, picture, home, globe, mail, trash, gear, lock, document, folder, monitor):
    d = {}
    # Document kinds.
    sheet_grid = rect(20, 26, 26, 24, "#ffffff", INK, 1.5) + path("M20 34H46M20 42H46M29 26V50M37 26V50", "none", INK, 1.5)
    d["x-office-spreadsheet"] = document(sheet_grid + rect(20, 26, 9, 8, COPPER, INK, 1.5))
    d["x-office-presentation"] = document(rect(19, 25, 28, 20, TEAL) + rect(23, 34, 5, 8, COPPER, "none") + rect(30, 29, 5, 13, COPPER, "none") + rect(37, 32, 5, 10, COPPER, "none") + path("M33 45V52M28 52H38"))
    d["x-office-document"] = document(text + rect(20, 23, 12, 2, COPPER, "none"))
    d["x-office-drawing"] = document(circle(27, 33, 7, COPPER) + rect(30, 38, 14, 12, TEAL))
    d["x-office-calendar"] = (rect(8, 10, 48, 46, PAPER) + rect(8, 10, 48, 12, COPPER) + "".join(rect(x, 6, 4, 9, GREY) for x in (18, 42))
                              + "".join(rect(13 + 9 * c, 27 + 8 * r, 6, 5, TEAL if (r, c) == (1, 2) else PALE, "none") for r in range(3) for c in range(5)))
    d["x-office-address-book"] = rect(12, 6, 42, 52, TEAL) + rect(8, 6, 8, 52, COPPER) + circle(35, 25, 7, PAPER) + path("M23 46Q23 33 35 33Q47 33 47 46Z", PAPER) + path("M14 12V54", "none", "#ffffff")
    d["audio-x-generic"] = document(circle(26, 45, 5, COPPER) + path("M31 45V27L41 25", "none", INK, 3))
    d["video-x-generic"] = document(rect(19, 27, 26, 22, INK) + path("M28 32L38 38L28 44Z", COPPER, "none") + "".join(rect(21, y, 3, 3, PAPER, "none") for y in (29, 36, 43)))
    d["text-x-script"] = document(path("M20 30L27 35L20 40M30 42H42", "none", COPPER, 3) + path("M20 48H40", "none", INK, 2))
    d["text-x-source"] = document(path("M24 30L18 37L24 44M38 30L44 37L38 44M34 27L29 47", "none", TEAL, 3))
    d["font-x-generic"] = document(path("M20 50L31 24H34L45 50M24 41H41", "none", INK, 4))
    d["package-x-generic"] = (path("M8 22L32 12L56 22V48L32 58L8 48Z", PALE) + path("M8 22L32 32L56 22M32 32V58", "none") + path("M20 17L44 27V36", "none", COPPER, 5)
                              + path("M10 46V25", "none", "#ffffff"))
    d["application-x-cd-image"] = (circle(32, 32, 26, PAPER) + circle(32, 32, 26, "none", INK) + path("M14 22Q20 12 32 10", "none", "#ffffff", 3)
                                   + path("M44 46Q40 52 32 54", "none", COPPER, 3) + circle(32, 32, 8, GREY) + circle(32, 32, 3, "#ffffff"))
    # Applications.
    d["accessories-calculator"] = (rect(12, 4, 40, 56, GREY) + rect(17, 9, 30, 12, DARK) + path("M37 15H43", "none", COPPER, 3)
                                   + "".join(rect(17 + 8 * c, 26 + 8 * r, 6, 6, COPPER if c == 3 else PAPER, INK, 1.5) for r in range(4) for c in range(4)) + path("M14 58V6H50", "none", "#ffffff"))
    d["accessories-character-map"] = (rect(6, 6, 52, 52, PAPER) + path("M6 23H58M6 40H58M23 6V58M40 6V58", "none", GREY, 2) + rect(23, 23, 17, 17, COPPER)
                                      + path("M26 37L31 26H33L38 37M28 33H36", "none", INK, 2.5) + path("M10 19L14 9L18 19M45 10V19M45 10H52M45 14H50", "none", INK, 2))
    d["camera-photo"] = (path("M6 20H18L23 12H41L46 20H58V54H6Z", GREY) + circle(32, 36, 13, DARK) + circle(32, 36, 8, TEAL) + path("M27 32Q29 29 33 29", "none", "#ffffff", 2)
                         + rect(48, 24, 6, 4, COPPER) + path("M8 52V22H56", "none", "#ffffff"))
    d["camera-web"] = circle(32, 26, 20, GREY) + circle(32, 26, 10, DARK) + circle(32, 26, 5, TEAL) + path("M22 54H42L38 45H26Z", PALE) + circle(46, 13, 2, COPPER, "none")
    d["applets-screenshooter"] = (path("M6 18V8H18M46 8H58V18M58 46V56H46M18 56H6V46", "none", COPPER, 5) + badge(d["camera-photo"], 14, 14, 0.56))
    d["document-viewer"] = document(text) + badge(lens(), 28, 28, 0.55)
    d["image-viewer"] = rect(5, 9, 54, 46, COPPER) + rect(11, 15, 42, 34, TEAL) + path("M13 47L25 31L35 41L42 34L51 47Z", PALE) + circle(43, 24, 4, PAPER) + path("M7 53V11H57", "none", "#ffffff")
    d["system-search"] = lens()
    d["edit-find"] = lens()
    d["filelight"] = (circle(32, 32, 26, PALE) + path("M32 32V6A26 26 0 0 1 56 41Z", COPPER) + path("M32 32L56 41A26 26 0 0 1 20 55Z", TEAL)
                      + circle(32, 32, 10, PAPER))
    d["drive-harddisk"] = (rect(5, 20, 54, 26, GREY) + path("M7 44V22H57", "none", "#ffffff") + rect(11, 36, 30, 3, DARK, "none") + rect(48, 34, 6, 5, COPPER))
    d["partitionmanager"] = d["drive-harddisk"] + badge(d["filelight"], 30, 2, 0.5)
    d["system-software-install"] = (path("M10 22H54L50 58H14Z", TEAL) + path("M22 22V16C22 4 42 4 42 16V22", "none", INK, 4) + path("M28 30H36V40H42L32 51L22 40H28Z", COPPER)
                                    + path("M12 24H52", "none", "#ffffff"))
    d["system-software-update"] = d["package-x-generic"] + badge(path("M32 6A26 26 0 1 1 8 40", "none", COPPER, 9) + path("M2 30L10 46L22 34Z", COPPER), 30, 30, 0.5)
    d["utilities-system-monitor"] = (rect(5, 8, 54, 39, GREY) + rect(10, 13, 44, 29, DARK) + path("M12 34H20L24 22L30 38L35 26L39 32H52", "none", COPPER, 2.5)
                                     + path("M7 45V10H57", "none", "#ffffff") + rect(27, 48, 10, 6, COPPER) + path("M17 58L21 54H43L47 58Z", GREY))
    d["utilities-log-viewer"] = document("".join(path(f"M20 {y}H{44 if i % 2 else 38}", "none", INK, 2) + rect(17, y - 1, 2, 2, COPPER if i == 2 else INK, "none") for i, y in enumerate((28, 33, 38, 43, 48))))
    d["wallet-open"] = rect(6, 16, 52, 38, TEAL) + path("M6 16L46 6L50 16", PALE) + rect(38, 28, 20, 14, COPPER) + circle(45, 35, 3, PAPER) + path("M8 52V18H56", "none", "#ffffff")
    key = circle(18, 32, 11, COPPER) + circle(15, 32, 3.5, PAPER) + path("M29 29H58V35H53V42H47V35H29Z", COPPER)
    d["dialog-password"] = key
    d["document-encrypt"] = document(text) + badge(lock, 30, 28, 0.55)
    d["document-decrypt"] = document(text) + badge(path("M20 28V18C20 2 44 2 44 12", "none", "#afc2c2", 7) + rect(12, 26, 40, 32, TEAL) + circle(32, 39, 4, COPPER), 30, 28, 0.55)
    d["application-rss+xml"] = (rect(7, 7, 50, 50, COPPER) + circle(19, 45, 5, PAPER, "none") + path("M15 30Q34 30 34 49M15 17Q47 17 47 49", "none", PAPER, 6))
    d["view-filter"] = path("M6 8H58L38 32V54L26 58V32Z", TEAL) + path("M10 10H54", "none", "#ffffff")
    dice = (rect(6, 22, 30, 30, PAPER) + "".join(circle(x, y, 2.6, INK, "none") for x, y in ((13, 29), (21, 37), (29, 45)))
            + rect(30, 10, 26, 26, COPPER) + "".join(circle(x, y, 2.4, PAPER, "none") for x, y in ((36, 16), (50, 16), (36, 30), (50, 30))))
    d["applications-games"] = dice
    d["kpat"] = (path("M8 14L30 8L40 46L18 52Z", PAPER) + path("M26 12H50V54H26Z", "#ffffff") + path("M38 22L44 31L38 40L32 31Z", RED, "none")
                 + path("M30 18V22M46 44V48", "none", RED, 2))
    d["kmines"] = (path("M32 4V60M4 32H60M12 12L52 52M52 12L12 52", "none", INK, 4) + circle(32, 32, 17, DARK) + circle(26, 26, 4, PAPER, "none") + circle(32, 32, 3, COPPER, "none"))
    d["kmahjongg"] = (rect(14, 6, 38, 50, "#ffffff") + rect(18, 10, 38, 50, PAPER) + circle(37, 23, 5, RED) + path("M27 38H47M37 33V50", "none", TEAL, 4))
    disc = d["application-x-cd-image"]
    d["media-optical"] = disc
    d["multimedia-audio-player"] = disc + badge(circle(18, 46, 9, COPPER) + path("M27 46V12L48 8V38", "none", INK, 5) + circle(39, 40, 9, COPPER), 30, 26, 0.55)
    d["multimedia-video-player"] = (rect(6, 12, 52, 40, DARK) + "".join(rect(x, y, 4, 4, PAPER, "none") for x in (9, 51) for y in (16, 25, 34, 43))
                                    + rect(16, 15, 32, 34, TEAL) + path("M26 22L42 32L26 42Z", COPPER))
    d["applications-multimedia"] = d["multimedia-video-player"]
    d["k3b"] = disc + badge(path("M30 43L48 13L56 19L38 48L28 53Z", COPPER) + path("M30 43L38 48M48 13L56 19"), 28, 28, 0.55)
    d["kolourpaint"] = (path("M30 6C48 6 60 18 58 32C56 42 46 38 42 44C38 50 44 58 32 58C16 58 6 46 6 32C6 18 16 6 30 6Z", PAPER)
                        + circle(20, 22, 5, COPPER) + circle(34, 16, 5, TEAL) + circle(16, 38, 5, RED) + circle(28, 46, 4, DARK)
                        + path("M58 6L38 34", "none", INK, 5) + path("M40 31L34 40L31 36Z", COPPER))
    d["scanner"] = (rect(5, 28, 54, 22, GREY) + path("M5 28L13 14H57L59 28Z", PALE) + rect(10, 38, 44, 4, COPPER, "none") + path("M7 48V30H57", "none", "#ffffff"))
    d["preferences-desktop-remote-desktop"] = (rect(4, 6, 34, 26, GREY) + rect(8, 10, 26, 18, TEAL) + rect(26, 30, 34, 26, GREY) + rect(30, 34, 26, 18, TEAL)
                                               + path("M40 14H50V24M46 18L50 14L54 18", "none", COPPER, 3) + path("M24 50H14V40M18 46L14 50L10 46", "none", COPPER, 3))
    d["krfb"] = monitor() + badge(circle(16, 32, 8, COPPER) + circle(48, 14, 8, COPPER) + circle(48, 50, 8, COPPER) + path("M16 32L48 14M16 32L48 50", "none", INK, 4), 30, 26, 0.55)
    d["ktorrent"] = (path("M8 42V56H56V42", "none", INK, 5) + path("M16 6H28V24H36L22 38L8 24H16Z", COPPER) + path("M36 6H48V24H56L42 38L28 24H36Z", TEAL))
    d["phone"] = rect(18, 4, 28, 56, DARK) + rect(21, 11, 22, 38, TEAL) + rect(28, 53, 8, 3, PAPER, "none") + path("M23 47V13H41", "none", "#ffffff")
    d["kdeconnect"] = d["phone"] + badge(monitor(), 30, 30, 0.5)
    bubble = path("M6 10H50V40H24L12 52V40H6Z", PAPER) + path("M14 20H42M14 28H34", "none", TEAL, 3)
    d["dialog-messages"] = bubble + path("M30 44H44L54 54V44H58V22H54", COPPER)
    d["firewall-config"] = (rect(4, 12, 56, 40, COPPER) + path("M4 22H60M4 32H60M4 42H60M18 12V22M38 12V22M28 22V32M48 22V32M18 32V42M38 32V42M28 42V52M48 42V52", "none", INK, 2))
    bug = (path("M22 12L28 20M42 12L36 20M12 28L20 30M52 28L44 30M12 42H20M52 42H44M14 56L22 48M50 56L42 48", "none", INK, 3)
           + circle(32, 22, 7, DARK) + path("M20 30Q20 22 32 22Q44 22 44 30V44Q44 58 32 58Q20 58 20 44Z", COPPER) + path("M32 26V56", "none", INK, 2))
    d["tools-report-bug"] = bug
    d["cpu"] = (path("".join(f"M{x} 4V12M{x} 52V60M4 {x}H12M52 {x}H60" for x in (20, 28, 36, 44)), "none", INK, 3) + rect(12, 12, 40, 40, DARK)
                + rect(20, 20, 24, 24, TEAL) + rect(26, 26, 12, 12, COPPER, "none"))
    d["input-keyboard"] = (rect(3, 16, 58, 34, GREY) + "".join(rect(8 + 7 * c, 21 + 7 * r, 5, 5, PAPER, INK, 1) for r in range(3) for c in range(7))
                           + rect(16, 42, 32, 4, PAPER, INK, 1) + rect(52, 21, 5, 12, COPPER, INK, 1) + path("M5 48V18H59", "none", "#ffffff"))
    d["input-mouse"] = (path("M16 22C16 8 48 8 48 22V44C48 60 16 60 16 44Z", GREY) + path("M16 26H48M32 10V26", "none", INK, 2) + rect(30, 14, 4, 8, COPPER)
                        + path("M18 44V22Q19 12 30 11", "none", "#ffffff"))
    d["preferences-desktop-locale"] = globe + badge(path("M10 4V60", "none", INK, 5) + path("M12 6H54L46 18L54 30H12Z", COPPER), 32, 30, 0.5)
    d["preferences-desktop-emoticons"] = circle(32, 32, 26, COPPER) + circle(23, 25, 4, INK, "none") + circle(41, 25, 4, INK, "none") + path("M19 38Q32 52 45 38", "none", INK, 4)
    qr = "".join(rect(x, y, 4, 4, INK, "none") for x, y in ((28, 8), (36, 8), (28, 16), (32, 28), (40, 28), (48, 32), (28, 40), (36, 44), (44, 44), (52, 52), (40, 52), (28, 52), (8, 32), (16, 28), (20, 32)))
    d["view-barcode-qr"] = rect(4, 4, 56, 56, "#ffffff") + "".join(rect(x, y, 16, 16, "none", INK, 4) + rect(x + 5, y + 5, 6, 6, COPPER, "none") for x, y in ((8, 8), (40, 8), (8, 40))) + qr
    d["kvantum"] = rect(10, 10, 44, 44, GREY) + path("M12 52V12H52", "none", "#ffffff", 4) + path("M14 52H52V14", "none", DARK, 4) + rect(22, 22, 20, 20, COPPER)
    d["kmenuedit"] = rect(7, 7, 50, 50, TEAL) + "".join(rect(15, y, 18, 4, COPPER, "none") for y in (15, 23, 31, 39)) + badge(path("M30 43L48 13L56 19L38 48L28 53Z", COPPER) + path("M30 43L38 48M48 13L56 19"), 26, 26, 0.6)
    # Categories.
    d["applications-accessories"] = (path("M10 54L46 18L54 26L18 62Z", PAPER) + path("M16 52L20 56M22 46L28 52M28 40L32 44M34 34L40 40", "none", INK, 2)
                                     + path("M44 4L56 16L28 44L16 48L20 36Z", COPPER) + path("M20 36L28 44"))
    d["applications-education"] = (path("M2 24L32 12L62 24L32 36Z", DARK) + path("M14 30V44Q32 54 50 44V30L32 37Z", TEAL) + path("M56 26V44", "none", COPPER, 3) + circle(56, 46, 3, COPPER))
    d["applications-science"] = (path("M24 6H40M27 6V24L10 52C8 56 10 58 14 58H50C54 58 56 56 54 52L37 24V6", PAPER) + path("M17 40H47L53 52C54 55 52 56 50 56H14C12 56 10 55 11 52Z", COPPER, "none")
                                 + circle(28, 47, 2.5, PAPER, "none") + circle(37, 51, 2, PAPER, "none"))
    d["applications-other"] = path("M32 6L56 18V46L32 58L8 46V18Z", PALE) + path("M8 18L32 30L56 18M32 30V58", "none") + path("M32 30L56 18V46L32 58Z", TEAL)
    d["preferences-desktop-accessibility"] = circle(32, 32, 26, TEAL) + circle(32, 16, 5, PAPER, "none") + path("M16 24L32 28L48 24M32 28V40L24 52M32 40L40 52", "none", PAPER, 5)
    d["help-about"] = circle(32, 32, 26, TEAL) + circle(32, 18, 4, PAPER, "none") + path("M26 28H34V48M26 48H40", "none", PAPER, 5)
    # Status: dialogs and security.
    d["dialog-information"] = d["help-about"]
    d["dialog-warning"] = path("M32 5L60 55H4Z", COPPER) + path("M32 22V40M32 46V50", "none", INK, 6)
    d["dialog-error"] = circle(32, 32, 26, RED) + path("M21 21L43 43M43 21L21 43", "none", "#ffffff", 7)
    shield = "M32 4L56 12V30C56 44 46 54 32 60C18 54 8 44 8 30V12Z"
    d["security-high"] = path(shield, TEAL) + path("M20 32L28 40L44 22", "none", PAPER, 6)
    d["security-medium"] = path(shield, COPPER) + path("M32 18V36M32 42V46", "none", INK, 6)
    d["security-low"] = path(shield, RED) + path("M22 22L42 42M42 22L22 42", "none", "#ffffff", 6)
    # Status: battery levels, charging; wireless strength; wired, offline.
    for level in range(0, 101, 10):
        fill = RED if level <= 10 else COPPER if level <= 30 else TEAL
        body = rect(6, 18, 48, 28, PAPER) + rect(54, 26, 5, 12, GREY) + (rect(10, 22, max(1, round(40 * level / 100)), 20, fill, "none") if level else "")
        name = f"battery-{level:03d}"
        d[name] = body
        d[name + "-charging"] = body + path("M34 12L22 34H32L28 52L42 28H32Z", "#ffe08a")
    for strength, arcs in ((0, 0), (20, 1), (40, 2), (60, 3), (80, 3), (100, 4)):
        # Quarter arcs round the dot at (32, 54), the largest within the grid.
        waves = "".join(path(f"M{32 - r} {54 - r}A{r * 1.414:.1f} {r * 1.414:.1f} 0 0 1 {32 + r} {54 - r}", "none", COPPER if i < arcs else PALE, 5) for i, r in enumerate((9, 18, 27, 34)))
        d[f"network-wireless-{strength}"] = waves + circle(32, 54, 4, INK, "none")
    d["network-wired"] = (rect(20, 6, 24, 18, GREY) + path("M26 6V14M32 6V14M38 6V14", "none", COPPER, 2) + rect(16, 24, 32, 18, PALE) + path("M32 42V60", "none", INK, 5))
    d["network-offline"] = d["network-wired"] + path("M8 56L56 8", "none", RED, 5)
    d["preferences-system-bluetooth"] = rect(14, 4, 36, 56, TEAL) + path("M22 20L42 40L32 50V14L42 24L22 44", "none", PAPER, 4)
    d["bluetooth-disabled"] = d["preferences-system-bluetooth"] + path("M8 56L56 8", "none", RED, 5)
    bell = path("M14 46H50L46 40V28C46 16 40 10 32 10C24 10 18 16 18 28V40Z", COPPER) + circle(32, 50, 5, INK, "none") + circle(32, 8, 3, INK, "none") + path("M22 38V28Q22 18 30 15", "none", "#ffe0c0")
    d["preferences-desktop-notification-bell"] = bell
    d["notifications-disabled"] = bell + path("M8 56L56 8", "none", RED, 5)
    sun = circle(32, 32, 12, "#ffe08a") + path("".join(f"M{32 + 18 * c:.1f} {32 + 18 * s:.1f}L{32 + 26 * c:.1f} {32 + 26 * s:.1f}" for c, s in
                                                     ((1, 0), (-1, 0), (0, 1), (0, -1), (.707, .707), (-.707, .707), (.707, -.707), (-.707, -.707))), "none", COPPER, 4)
    d["brightness-high"] = sun
    d["plasmavault"] = rect(6, 6, 52, 52, GREY) + rect(12, 12, 40, 40, PALE) + circle(32, 32, 12, TEAL) + path("M32 22V42M22 32H42", "none", COPPER, 3) + rect(54, 18, 6, 8, INK, "none") + rect(54, 38, 6, 8, INK, "none")
    d["audio-input-microphone"] = rect(24, 4, 16, 32, GREY) + path("M26 10H38M26 16H38M26 22H38", "none", INK, 1.5) + path("M16 28Q16 46 32 46Q48 46 48 28M32 46V58M22 58H42", "none", COPPER, 4)
    d["audio-headphones"] = path("M10 40V30Q10 8 32 8Q54 8 54 30V40", "none", INK, 5) + rect(6, 36, 12, 22, COPPER) + rect(46, 36, 12, 22, COPPER)
    # Devices and places.
    d["drive-removable-media"] = rect(14, 24, 36, 34, GREY) + rect(20, 8, 24, 16, PAPER) + rect(25, 12, 5, 6, INK, "none") + rect(34, 12, 5, 6, INK, "none") + rect(26, 36, 12, 4, COPPER) + path("M16 56V26H48", "none", "#ffffff")
    d["media-flash"] = path("M14 6H42L50 14V58H14Z", DARK) + "".join(rect(x, 8, 4, 10, COPPER, "none") for x in (20, 27, 34, 41)) + rect(18, 30, 28, 22, PALE)
    d["computer-laptop"] = rect(12, 10, 40, 30, GREY) + rect(16, 14, 32, 22, TEAL) + path("M4 48L10 40H54L60 48Z", PALE) + rect(28, 43, 8, 3, COPPER, "none")
    d["network-server"] = rect(16, 4, 32, 56, GREY) + "".join(rect(20, y, 24, 8, PALE) + circle(40, y + 4, 2, COPPER, "none") for y in (9, 21, 33)) + path("M18 58V6H46", "none", "#ffffff")
    d["user-trash-full"] = trash + path("M18 12L28 4L40 10L50 4", "none", INK, 2) + path("M20 14L28 6L38 12L48 6V14H20Z", PAPER)
    d["folder-open"] = (path("M5 16V10H24L30 16H57V54H5Z", TEAL) + path("M5 54L12 26H62L55 54Z", PALE) + path("M13 28H60", "none", "#ffffff"))
    d["document-open"] = d["folder-open"]
    d["folder-root"] = folder(path("M38 24L26 50", "none", COPPER, 5))
    d["folder-network"] = folder(badge(rect(23, 6, 18, 15, PALE) + path("M32 21V33M12 33H52M12 33V43M32 33V43M52 33V43") + "".join(rect(x, 43, 14, 13, COPPER) for x in (5, 25, 45)), 18, 22, 0.5))
    star = path(star_path(32, 33, 26, 11), COPPER)
    d["starred"] = star
    d["folder-favorites"] = folder(badge(star, 18, 22, 0.5))
    d["folder-locked"] = folder(badge(lock, 20, 22, 0.48))
    clock = circle(32, 32, 26, PAPER) + path("M32 14V32L44 40", "none", INK, 5)
    d["document-open-recent"] = document(text) + badge(clock, 28, 28, 0.55)
    d["bookmarks"] = path("M16 4H48V60L32 46L16 60Z", COPPER) + path("M18 56V6H46", "none", "#ffe0c0")
    d["bookmark-new"] = d["bookmarks"] + badge(path("M32 10V54M10 32H54", "none", INK, 10), 30, 30, 0.5)
    # Actions: documents.
    plus = circle(32, 32, 26, TEAL) + path("M32 18V46M18 32H46", "none", PAPER, 7)
    cross = circle(32, 32, 26, RED) + path("M22 22L42 42M42 22L22 42", "none", "#ffffff", 7)
    floppy = rect(9, 6, 46, 52, TEAL) + rect(19, 7, 26, 19, "#afc2c2") + rect(17, 35, 30, 23, "#c4d2d0") + rect(35, 10, 5, 12, INK)
    d["document-save-as"] = floppy + badge(path("M30 43L48 13L56 19L38 48L28 53Z", COPPER) + path("M30 43L38 48M48 13L56 19"), 28, 28, 0.6)
    d["document-save-all"] = badge(floppy, 2, 2, 0.7) + badge(floppy, 20, 20, 0.7)
    d["document-properties"] = document(text) + badge(d["help-about"], 30, 30, 0.5)
    d["document-close"] = document(text) + badge(cross, 30, 30, 0.5)
    d["document-revert"] = document(text) + badge(path("M49 19A21 21 0 1 0 51 42M49 7V22H34", "none", COPPER, 7), 28, 28, 0.55)
    arrow_r = path("M9 24H35V12L55 32L35 52V40H9Z", COPPER)
    d["document-export"] = document(text) + badge(arrow_r, 30, 28, 0.55)
    d["document-import"] = document(text) + badge(f'<g transform="rotate(180 32 32)">{arrow_r}</g>', 30, 28, 0.55)
    d["document-send"] = path("M4 30L60 6L44 58L32 38Z", PAPER) + path("M32 38L60 6M32 38L30 56L38 46", "none") + path("M30 56L32 38L38 46Z", COPPER)
    share = circle(16, 32, 8, COPPER) + circle(48, 14, 8, COPPER) + circle(48, 50, 8, COPPER) + path("M16 32L48 14M16 32L48 50", "none", INK, 4)
    d["document-share"] = share
    d["emblem-shared"] = share
    d["document-new"] = document(text) + badge(plus, 30, 30, 0.5)
    # Actions: editing.
    d["edit-select-all"] = rect(8, 8, 48, 48, PAPER, INK, 0) + path("M8 8H56V56H8Z", "none", INK, 3).replace('stroke-linejoin="miter"', 'stroke-dasharray="6 4"') + rect(18, 18, 28, 28, COPPER)
    d["edit-clear"] = path("M8 44L32 20L52 40L36 56H18Z", PAPER) + path("M32 20L44 8L60 24L52 40Z", COPPER) + path("M18 56H58", "none", INK, 2)
    d["edit-rename"] = rect(4, 18, 56, 28, "#ffffff") + path("M10 26H30M10 34H24", "none", GREY, 3) + path("M38 12V52M33 12H43M33 52H43", "none", INK, 3) + rect(4, 18, 56, 28, "none", COPPER, 2)
    d["edit-find-replace"] = lens() + badge(path("M49 19A21 21 0 1 0 51 42M49 7V22H34", "none", COPPER, 8), 34, 2, 0.45)
    d["zoom-in"] = lens() + path("M26 18V34M18 26H34", "none", INK, 4)
    d["zoom-out"] = lens() + path("M18 26H34", "none", INK, 4)
    d["zoom-original"] = lens() + path("M20 21L23 19V33M29 24V25M29 30V31M33 21L36 19V33", "none", INK, 2.5)
    d["zoom-fit-best"] = lens() + path("M4 14V4H14M50 4H60V14M60 50V60M4 50V60H14", "none", TEAL, 4)
    bars = lambda widths: "".join(rect(6, 10 + 13 * i, w, 8, TEAL) for i, w in enumerate(widths))
    d["view-sort-ascending"] = bars((14, 24, 34, 44)) + path("M54 50V10M46 18L54 10L62 18", "none", COPPER, 4)
    d["view-sort-descending"] = bars((44, 34, 24, 14)) + path("M54 10V50M46 42L54 50L62 42", "none", COPPER, 4)
    eye = path("M4 32Q32 6 60 32Q32 58 4 32Z", PAPER) + circle(32, 32, 10, TEAL) + circle(32, 32, 4, INK, "none") + circle(29, 29, 2, "#ffffff", "none")
    d["view-visible"] = eye
    d["view-hidden"] = eye + path("M10 54L54 10", "none", COPPER, 5)
    d["view-preview"] = document(picture.replace("18, 27", "18, 27")) + badge(eye, 28, 30, 0.55)
    d["view-split-left-right"] = window(path("M32 21V54", "none", INK, 3) + rect(9, 23, 20, 29, PALE, "none") + rect(35, 23, 20, 29, PALE, "none"))
    d["view-split-top-bottom"] = window(path("M7 37H57", "none", INK, 3) + rect(9, 23, 46, 11, PALE, "none") + rect(9, 40, 46, 12, PALE, "none"))
    d["view-fullscreen"] = path("M6 22V6H22M42 6H58V22M58 42V58H42M22 58H6V42", "none", TEAL, 6) + path("M6 6L22 22M58 6L42 22M58 58L42 42M6 58L22 42", "none", COPPER, 4)
    d["view-restore"] = path("M22 6V22H6M42 6V22H58M42 58V42H58M22 58V42H6", "none", TEAL, 6)
    d["window"] = window()
    d["window-new"] = window() + badge(plus, 30, 30, 0.5)
    d["window-close"] = window(path("M22 28L42 48M42 28L22 48", "none", INK, 5))
    d["window-minimize"] = window(rect(28, 40, 8, 8, GREY))
    d["window-maximize"] = window(rect(12, 24, 40, 28, GREY))
    d["window-restore"] = badge(window(), 18, 2, 0.7) + badge(window(), 2, 18, 0.7)
    tab = path("M4 56V20H10L16 10H34L40 20H60V56Z", PAPER) + path("M16 10H34L40 20H10Z", COPPER)
    d["tab-new"] = tab + badge(plus, 30, 30, 0.5)
    d["tab-close"] = tab + badge(cross, 30, 30, 0.5)
    d["application-exit"] = rect(10, 4, 30, 56, GREY) + rect(14, 8, 22, 48, DARK) + path("M30 32H58M48 22L58 32L48 42", "none", COPPER, 5)
    d["process-stop"] = path("M22 4H42L60 22V42L42 60H22L4 42V22Z", RED) + path("M16 32H48", "none", "#ffffff", 7)
    d["system-run"] = gear + badge(path("M18 9L53 32L18 55Z", COPPER), 26, 26, 0.6)
    d["run-build"] = path("M8 52L34 26L40 32L14 58Z", COPPER) + path("M30 14L44 4L60 20L52 30L44 26L36 34L28 26L34 20Z", GREY)
    # Actions: navigation and media.
    for name, rot in (("go-first", 0), ("go-last", 180), ("go-top", 90), ("go-bottom", -90)):
        d[name] = f'<g transform="rotate({rot} 32 32)">' + path("M14 32L34 12V24H56V40H34V52Z", COPPER) + rect(6, 12, 6, 40, TEAL) + '</g>'
    d["media-playback-stop"] = rect(12, 12, 40, 40, TEAL)
    d["media-skip-forward"] = path("M8 12L32 32L8 52Z", COPPER) + path("M30 12L54 32L30 52Z", COPPER) + rect(54, 12, 6, 40, TEAL)
    d["media-skip-backward"] = f'<g transform="rotate(180 32 32)">{d["media-skip-forward"]}</g>'
    d["media-seek-forward"] = path("M6 12L32 32L6 52Z", COPPER) + path("M32 12L58 32L32 52Z", COPPER)
    d["media-seek-backward"] = f'<g transform="rotate(180 32 32)">{d["media-seek-forward"]}</g>'
    d["media-record"] = circle(32, 32, 22, RED)
    # Actions: mail.
    d["mail-reply-sender"] = mail + badge(path("M8 30L26 12V22C46 22 56 34 56 52C50 40 42 38 26 38V48Z", COPPER), 28, 28, 0.55)
    d["mail-reply-all"] = mail + badge(path("M2 30L18 14V22M18 46L2 30M14 30L32 12V22C50 22 60 34 60 52C54 40 46 38 32 38V48Z", COPPER), 28, 28, 0.55)
    d["mail-forward"] = mail + badge(f'<g transform="scale(-1 1) translate(-64 0)">{path("M8 30L26 12V22C46 22 56 34 56 52C50 40 42 38 26 38V48Z", COPPER)}</g>', 28, 28, 0.55)
    d["mail-send"] = d["document-send"]
    d["mail-receive"] = mail + badge(path("M28 6H38V30H48L33 46L18 30H28Z", COPPER), 30, 26, 0.55)
    d["mail-mark-read"] = path("M6 30L32 10L58 30V56H6Z", PAPER) + path("M6 30L32 46L58 30", "none") + path("M18 30L28 38L46 20", "none", TEAL, 4)
    d["mail-mark-unread"] = mail + circle(52, 14, 8, COPPER)
    d["mail-attachment"] = path("M40 14V44C40 56 22 56 22 44V12C22 4 34 4 34 12V42C34 46 28 46 28 42V18", "none", INK, 4)
    # Actions: formatting.
    d["format-text-bold"] = path("M18 10V54H36C48 54 48 32 36 32H18M18 32H34C44 32 44 10 34 10H18", "none", INK, 7)
    d["format-text-italic"] = path("M30 10H48M16 54H34M39 10L25 54", "none", INK, 6)
    d["format-text-underline"] = path("M18 8V34C18 52 46 52 46 34V8", "none", INK, 6) + path("M12 58H52", "none", COPPER, 5)
    d["format-text-strikethrough"] = path("M44 16C38 8 20 9 20 20C20 32 44 30 44 43C44 55 24 56 18 47", "none", INK, 6) + path("M8 32H56", "none", COPPER, 5)
    for name, spans in (("format-justify-left", (6, 6, 6, 6)), ("format-justify-center", (6, 14, 6, 14)), ("format-justify-right", (6, 22, 6, 22)), ("format-justify-fill", (6, 6, 6, 6))):
        widths = (52, 36, 52, 36) if name != "format-justify-fill" else (52, 52, 52, 52)
        x0 = {"format-justify-left": lambda w: 6, "format-justify-center": lambda w: 32 - w / 2, "format-justify-right": lambda w: 58 - w, "format-justify-fill": lambda w: 6}[name]
        d[name] = "".join(path(f"M{x0(w):.0f} {12 + 13 * i}H{x0(w) + w:.0f}", "none", INK, 5) for i, w in enumerate(widths))
    d["format-indent-more"] = "".join(path(f"M{26 if 0 < i < 3 else 6} {12 + 13 * i}H58", "none", INK, 5) for i in range(4)) + path("M6 22L16 31L6 40Z", COPPER)
    d["format-indent-less"] = "".join(path(f"M{26 if 0 < i < 3 else 6} {12 + 13 * i}H58", "none", INK, 5) for i in range(4)) + path("M16 22L6 31L16 40Z", COPPER)
    d["insert-image"] = d["image-x-generic"] if "image-x-generic" in d else document(picture)
    d["insert-link"] = (path("M28 22L36 14C42 8 52 8 56 14C60 20 58 26 52 30L44 38", "none", TEAL, 6) + path("M36 42L28 50C22 56 12 56 8 50C4 44 6 38 12 34L20 26", "none", TEAL, 6)
                        + path("M24 40L40 24", "none", COPPER, 6))
    d["insert-table"] = rect(6, 10, 52, 44, "#ffffff") + rect(6, 10, 52, 11, COPPER) + path("M6 32H58M6 43H58M23 10V54M40 10V54", "none", INK, 2)
    d["object-rotate-left"] = rect(22, 22, 32, 32, PALE) + path("M10 40V22A16 16 0 0 1 40 14", "none", COPPER, 5) + path("M2 28L10 40L18 28Z", COPPER)
    d["object-rotate-right"] = f'<g transform="scale(-1 1) translate(-64 0)">{d["object-rotate-left"]}</g>'
    d["object-flip-horizontal"] = path("M28 10V54L6 54Z", TEAL) + path("M36 10V54L58 54Z", PALE) + path("M32 4V60", "none", COPPER, 3).replace('stroke-linejoin="miter"', 'stroke-dasharray="4 3"')
    d["object-flip-vertical"] = f'<g transform="rotate(90 32 32)">{d["object-flip-horizontal"]}</g>'
    d["transform-crop"] = path("M16 4V48H60M4 16H48V60", "none", INK, 6) + rect(22, 22, 20, 20, COPPER, "none")
    # Emblems: drawn whole, for Dolphin's overlays at small sizes.
    d["emblem-favorite"] = star
    d["emblem-locked"] = lock
    d["emblem-symbolic-link"] = rect(4, 4, 56, 56, "#ffffff") + path("M16 48V36C16 24 26 20 40 20M32 10L44 20L32 30", "none", INK, 6)
    d["emblem-mounted"] = circle(32, 32, 26, TEAL) + path("M18 32L28 42L46 22", "none", "#ffffff", 7)
    d["emblem-important"] = circle(32, 32, 26, COPPER) + path("M32 14V36M32 44V48", "none", INK, 7)
    d["emblem-unreadable"] = cross
    d["sidebar-expand-left"] = window(path("M7 21H22V54H7Z", PALE) + path("M44 30L34 38L44 46", "none", COPPER, 4))
    d["sidebar-collapse-left"] = window(path("M7 21H22V54H7Z", PALE) + path("M34 30L44 38L34 46", "none", COPPER, 4))
    for side in ("expand", "collapse"):
        d[f"sidebar-{side}-right"] = f'<g transform="scale(-1 1) translate(-64 0)">{d[f"sidebar-{side}-left"]}</g>'
    return {k: v for k, v in d.items() if v}


# Names that share a drawing. "-symbolic" variants are listed where Plasma
# asks for them (the Applications menu's categories) - otherwise Breeze's
# monochrome version would win over the drawing.
MORE_ALIASES = {
    "x-office-spreadsheet": ["libreoffice-calc", "application-vnd.oasis.opendocument.spreadsheet", "text-csv", "application-vnd.ms-excel"],
    "x-office-presentation": ["libreoffice-impress", "application-vnd.oasis.opendocument.presentation", "application-vnd.ms-powerpoint"],
    "x-office-document": ["libreoffice-writer", "application-vnd.oasis.opendocument.text", "application-msword", "applications-office"],
    "x-office-drawing": ["libreoffice-draw", "application-vnd.oasis.opendocument.graphics", "image-svg+xml"],
    "x-office-calendar": ["office-calendar", "korganizer", "org.kde.korganizer", "org.kde.merkuro.calendar", "view-calendar", "appointment-new", "text-calendar"],
    "x-office-address-book": ["kaddressbook", "org.kde.kaddressbook", "text-vcard", "contact-new", "view-pim-contacts"],
    "audio-x-generic": ["audio-mpeg", "audio-x-wav", "audio-flac", "audio-ogg", "audio-x-vorbis+ogg"],
    "video-x-generic": ["video-mp4", "video-x-matroska", "video-webm"],
    "text-x-script": ["application-x-shellscript", "text-x-python", "application-x-executable-script", "text-x-perl"],
    "text-x-source": ["text-x-csrc", "text-x-c++src", "text-x-chdr", "application-json", "application-xml", "text-html", "text-x-makefile", "text-x-cmake"],
    "package-x-generic": ["application-zip", "application-x-compressed-tar", "application-x-tar", "application-x-7z-compressed", "application-x-rpm",
                          "application-vnd.debian.binary-package", "application-x-xz-compressed-tar", "ark", "org.kde.ark", "xfa", "xfp", "application-x-archive"],
    "application-x-cd-image": ["application-x-iso9660-image", "application-x-raw-disk-image"],
    "accessories-calculator": ["org.kde.kcalc", "kcalc", "org.kde.kalk"],
    "accessories-character-map": ["kcharselect", "org.kde.kcharselect"],
    "applets-screenshooter": ["spectacle", "org.kde.spectacle", "screenshot"],
    "document-viewer": ["okular", "org.kde.okular", "xfi"],
    "image-viewer": ["gwenview", "org.kde.gwenview", "showfoto", "digikam", "image-x-generic-viewer"],
    "system-search": ["kfind", "org.kde.kfind"],
    "filelight": ["org.kde.filelight"],
    "partitionmanager": ["org.kde.partitionmanager", "org.gnome.DiskUtility", "gnome-disks"],
    "system-software-install": ["plasmadiscover", "org.kde.discover", "applications-other-install"],
    "system-software-update": ["update-low", "update-medium", "update-high", "update-none", "system-software-update-available"],
    "utilities-system-monitor": ["org.kde.plasma-systemmonitor", "ksysguard", "hwinfo", "org.kde.kinfocenter", "kinfocenter"],
    "utilities-log-viewer": ["org.kde.kjournaldbrowser", "text-x-log"],
    "wallet-open": ["kwalletmanager", "org.kde.kwalletmanager", "wallet-closed", "kwalletmanager2"],
    "dialog-password": ["kleopatra", "org.kde.kleopatra", "org.kde.kwatchgnupg", "password-copy", "kgpg", "application-pgp-encrypted"],
    "internet-mail": ["kmail", "kontact", "org.kde.kontact", "ktnef", "kontact-import-wizard", "sieveeditor", "mail-client", "evolution", "thunderbird"],
    "application-rss+xml": ["akregator", "org.kde.akregator", "feed-subscribe"],
    "applications-games": ["applications-toys", "package_games"],
    "multimedia-audio-player": ["elisa", "org.kde.elisa", "juk", "rhythmbox"],
    "multimedia-video-player": ["dragonplayer", "org.kde.dragonplayer", "vlc", "mpv", "haruna", "org.kde.haruna"],
    "media-optical": ["media-optical-cd", "media-optical-dvd", "drive-optical", "gcdmaster"],
    "k3b": ["org.kde.k3b", "brasero"],
    "camera-web": ["kamoso", "org.kde.kamoso", "camera-on"],
    "camera-photo": ["camera", "digikam-camera"],
    "kolourpaint": ["org.kde.kolourpaint", "applications-graphics", "kolourpaint4"],
    "scanner": ["skanpage", "org.kde.skanpage", "skanlite"],
    "preferences-desktop-remote-desktop": ["krdc", "org.kde.krdc", "krfb-connect"],
    "krfb": ["org.kde.krfb", "desktop-sharing"],
    "ktorrent": ["org.kde.ktorrent", "transmission"],
    "kdeconnect": ["org.kde.kdeconnect.app", "kdeconnect-tray", "kdeconnectindicator", "smartphone"],
    "dialog-messages": ["org.kde.neochat", "neochat", "kmouth", "org.kde.kmouth", "konversation", "irc-channel-active"],
    "firewall-config": ["firewall", "security-firewall"],
    "tools-report-bug": ["setroubleshoot_icon", "org.freedesktop.GnomeAbrt", "debug-run", "kbugbuster", "drkonqi"],
    "cpu": ["hwinfo-cpu", "computer-chip"],
    "input-keyboard": ["preferences-desktop-keyboard", "im-chooser", "input-keyboard-virtual", "fcitx", "kmouth-phrasebook"],
    "input-mouse": ["preferences-desktop-mouse", "preferences-desktop-peripherals"],
    "preferences-desktop-locale": ["preferences-desktop-locale-symbolic", "languages"],
    "preferences-desktop-emoticons": ["face-smile", "emoji"],
    "view-barcode-qr": ["qrca", "org.kde.qrca"],
    "kvantum": ["kvantummanager", "preferences-desktop-theme"],
    "kmenuedit": ["org.kde.kmenuedit", "menu-editor"],
    "applications-accessories": ["applications-utilities"],
    "applications-education": ["package_edutainment", "applications-education-language", "applications-education-mathematics", "applications-education-miscellaneous"],
    "applications-science": ["applications-education-science"],
    "applications-other": ["applications-engineering"],
    "help-about": ["documentinfo", "help-hint"],
    "dialog-warning": ["data-warning", "emblem-warning"],
    "dialog-error": ["data-error", "emblem-error"],
    "network-wireless-100": ["network-wireless", "network-wireless-signal-excellent", "network-wireless-connected-100", "network-wireless-connected-80"],
    "network-wireless-80": ["network-wireless-signal-good", "network-wireless-connected-75"],
    "network-wireless-60": ["network-wireless-connected-60", "network-wireless-connected-50"],
    "network-wireless-40": ["network-wireless-signal-ok", "network-wireless-connected-40"],
    "network-wireless-20": ["network-wireless-signal-weak", "network-wireless-connected-25", "network-wireless-connected-20"],
    "network-wireless-0": ["network-wireless-signal-none", "network-wireless-connected-00", "network-wireless-disconnected"],
    "network-wired": ["network-wired-activated", "network-connect", "network-wired-symbolic"],
    "network-offline": ["network-disconnect", "network-wired-disconnected", "network-unavailable"],
    "preferences-system-bluetooth": ["bluetooth", "bluetooth-active", "preferences-system-bluetooth-activated", "bluedevil"],
    "bluetooth-disabled": ["preferences-system-bluetooth-inactive", "bluetooth-inactive"],
    "preferences-desktop-notification-bell": ["notifications", "notification-active", "notification-inactive", "preferences-desktop-notification", "knotify"],
    "notifications-disabled": ["notification-disabled", "notifications-disabled-symbolic"],
    "brightness-high": ["video-display-brightness", "brightness-low", "redshift-status-on", "weather-clear"],
    "plasmavault": ["folder-encrypted", "plasmavault_error"],
    "edit-paste": ["klipper", "org.kde.klipper", "edit-paste-in-place"],
    "audio-input-microphone": ["audio-input-microphone-high", "microphone"],
    "drive-removable-media": ["drive-removable-media-usb", "drive-removable-media-usb-pendrive", "media-removable", "device-notifier"],
    "media-flash": ["media-flash-sd-mmc", "media-flash-memory-stick"],
    "drive-harddisk": ["drive-harddisk-root", "drive-harddisk-system", "drive-multidisk", "drive-partition", "partitionmanager-symbolic"],
    "folder-open": ["folder-drag-accept"],
    "folder-locked": ["folder-root-locked"],
    "starred": ["favorite", "rating", "starred-symbolic", "bookmark-star"],
    "bookmarks": ["bookmarks-organize", "bookmark", "folder-bookmark"],
    "folder-favorites": ["folder-star"],
    "document-new": ["document-new-from-template"],
    "edit-clear": ["edit-clear-history", "edit-clear-all", "edit-clear-list", "edit-clear-locationbar-rtl", "edit-clear-locationbar-ltr"],
    "edit-copy": ["edit-copy-path"],
    "view-hidden": ["visibility"],
    "window-close": ["view-close", "tab-close-other"],
    "help-browser": ["help-contextual", "help-contents", "dialog-question"],
    "system-run": ["system-run-symbolic", "run-install", "media-playlist-play"],
    "go-next": ["arrow-right", "arrow-right-symbolic", "go-next-view"],
    "go-previous": ["arrow-left", "arrow-left-symbolic", "go-previous-view"],
    "go-up": ["arrow-up", "arrow-up-symbolic"],
    "go-down": ["arrow-down", "arrow-down-symbolic"],
    "go-top": ["go-top-symbolic"],
    "edit-find": ["search", "edit-find-symbolic"],
    "mail-send": ["mail-send-receive", "document-send-symbolic"],
    "insert-link": ["edit-link", "link"],
    "process-stop": ["dialog-cancel-symbolic"],
    "computer-laptop": ["computer-laptop-symbolic"],
    "network-server": ["network-server-database", "server-database"],
    "printer": ["document-print", "printer-network", "printmanager", "document-print-direct"],
    "view-preview": ["document-preview"],
}
# Category icons as the Applications menu asks for them.
SYMBOLIC = ("applications-accessories", "applications-development", "applications-education", "applications-games", "applications-graphics",
            "applications-internet", "applications-multimedia", "applications-network", "applications-office", "applications-other",
            "applications-science", "applications-system", "applications-toys", "applications-utilities", "office-calendar",
            "help-about", "preferences-system", "preferences-desktop-accessibility", "preferences-desktop-peripherals",
            "system-file-manager", "user-desktop", "utilities-terminal", "accessories-text-editor", "applications-games-arcade",
            "applications-games-board", "applications-games-card", "applications-games-logic", "applications-games-strategy",
            "applications-education-language", "applications-education-mathematics", "applications-education-miscellaneous",
            "applications-development-web", "applications-development-translation")
