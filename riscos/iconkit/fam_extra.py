"""fam_extra.py: names that turned out meanings of their own once names.py
took Breeze's largest size as the measure (25.10.2026): before, they had
counted as synonyms and no family module drew them. Its category "extra"
matches none, so build_icons asks it only when no module of the name's own
category draws the name."""
from base import action, disc, page
from glyphs import glyph

ACTIONS = {
    "align-vertical-bottom-to-anchor": ("arrow-bottom", "blue", "target", "red"),
    "amarok_change_language": ("language", "violet", "refresh", "blue"),
    "choice-round": ("circle", "blue", "dot", "blue"),
    "edit-table-delete-row": ("table", "ink", "minus", "red"),
    "format-list-unordered": ("list-bullet", None, None, None),
    "gnumeric-cells-merge": ("grid", "green", "equals", "green"),
    "gnumeric-column-size": ("columns", "green", "measure", "blue"),
    "gnumeric-row-size": ("list", "green", "measure", "blue"),
    "love": ("heart", "red", None, None),
    "mail-deleted": ("envelope", None, "trash", "red"),
    "mail-encrypted-full": ("envelope", None, "lock", "orange"),
    "mail-flag": ("envelope", None, "flag", "red"),
    "mail-forwarded": ("envelope", None, "forward", "blue"),
    "mail-replied": ("envelope", None, "reply", "green"),
    "mail-thread-watch": ("envelope", None, "eye", "violet"),
    "path-clip-edit": ("path", "blue", "scissors", "orange"),
    "qa": ("help", "blue", "check", "green"),
    "show-offline": ("user", None, "eye-off", "grey"),
    "system-lock-screen": ("monitor", None, "lock", "orange"),
    "system-save-session": ("windows", None, "save", "blue"),
    "system-search": ("monitor", None, "magnifier", "blue"),
    "system-users": ("users", None, None, None),
    "tag-recents": ("tag", "orange", "clock", "blue"),
    "text_subscript": ("abc", None, "arrow-down", "blue"),
    "text_superscript": ("abc", None, "arrow-up", "blue"),
    "tool-measure": ("ruler", "orange", None, None),
    "view-time-schedule-baselined-add": ("calendar", "blue", "plus", "green"),
    "xml-node-duplicate": ("node", "violet", "copy", "blue"),
}


def dialog(c, color, mark):
    """The error box's symbol: a disc with a white inner ring, so it is not
    the plain state disc (state-error, state-ok …)."""
    disc(c, color, mark)
    c.circle(24, 24, 15.5, "none", "#ffffff", 1.6)
    return True


def draw(name, c):
    if name in ACTIONS:
        g, accent, badge, badge_color = ACTIONS[name]
        return action(c, g, accent, badge, badge_color)
    if name == "dialog-error":
        return dialog(c, c["red"], "cross")
    if name == "dialog-information":
        return dialog(c, c["blue"], "info")
    if name == "dialog-positive":
        return dialog(c, c["green"], "check")
    if name == "dialog-question":
        c.circle(24, 24, 19, c.grad(c["page"]))
        glyph(c, "question", 12, 12, 24, c["blue"])
        return True
    if name == "dialog-warning":
        c.path("M24 5 L44 41 H4 Z", c.grad(c.lighten(c["yellow"], 0.3), c["yellow"]))
        glyph(c, "exclamation", 14, 16, 20, c["ink"])
        return True
    if name == "network-wired":
        glyph(c, "ethernet", 6, 6, 36, c["ink"])
        c.path("M18 40 v4 M30 40 v4", "none", c["blue"], 3)
        return True
    if name == "face-smile":
        c.circle(24, 24, 19, c.grad(c.lighten(c["yellow"], 0.35), c["yellow"]))
        c.circle(18, 20, 2.2, c["ink"], None)
        c.circle(30, 20, 2.2, c["ink"], None)
        c.path("M15 28 Q24 35 33 28", "none", "ink", 2.4)
        return True
    if name == "start-here-kde":
        # RISC OS's start of everything, the Apps on the iconbar: three
        # coloured blocks (no one's logo).
        c.rect(8, 22, 16, 16, c.grad(c.lighten(c["red"], 0.3), c["red"]), 2)
        c.rect(24, 22, 16, 16, c.grad(c.lighten(c["blue"], 0.3), c["blue"]), 2)
        c.rect(16, 7, 16, 16, c.grad(c.lighten(c["green"], 0.3), c["green"]), 2)
        return True
    if name == "multimedia-player":
        c.rect(14, 4, 20, 40, c.grad(c["metal"]), 4)
        c.rect(17, 8, 14, 14, c.grad(c["screen"]), 1.5, width=1)
        c.circle(24, 33, 6.5, c.lighten(c["metal"][1], 0.4), width=1.2)
        c.circle(24, 33, 2.2, c["ink"], None)
        return True
    if name == "accessories-text-editor":
        page(c, lines=True)
        c.path("M18 40 L38 14 L43 18 L23 44 L17 45 Z", c.grad(c.lighten(c["yellow"], 0.2), c["orange"]), width=1.2)
        c.path("M38 14 L43 18", "none", c["red"], 3)
        return True
    return None
