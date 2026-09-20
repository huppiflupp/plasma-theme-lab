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
    theme = out / "icons/CDECopper"
    dest = theme / "scalable/all"
    dest.mkdir(parents=True, exist_ok=True)
    for name, body in defs.items():
        (dest / f"{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{body}</svg>\n')
    for name, original in aliases.items():
        p = dest / f"{name}.svg"
        if p.is_symlink() or p.exists():
            p.unlink()
        p.symlink_to(original + ".svg")
    (theme / "index.theme").write_text("[Icon Theme]\nName=CDE Copper\nComment=Original scalable workstation pictograms\nInherits=breeze,hicolor\nDirectories=scalable/all\n\n[scalable/all]\nSize=48\nType=Scalable\nMinSize=16\nMaxSize=512\nContext=Applications\n")
