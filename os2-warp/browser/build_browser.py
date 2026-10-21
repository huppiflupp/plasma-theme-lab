#!/usr/bin/env python3
"""Browser themes for Warp Legacy: Firefox and Chrome/Chromium.

    build_browser(out, variants, version)

writes, per variant (classic and Neon), from the palettes in ../build.py:

    out/firefox/<id>/            WebExtension theme (manifest.json, images/)
    out/firefox/<id>.xpi         the same zipped: load it temporarily via
                                 about:debugging, or have it signed on AMO
    out/chrome/<id>/             Chrome theme, "Load unpacked" in developer mode
    out/chrome/<id>.zip          the same zipped (Chrome Web Store upload)
    out/userchrome/<key>/        userChrome.css + userContent.css: Firefox's
                                 own look without a signed add-on
    out/firefox-apply.sh         applies/removes those per profile (on request)

<id> is warp-legacy or warp-legacy-neon, <key> classic or neon. Run alone
(python3 browser/build_browser.py) it builds into build/warp-legacy/browser,
which install.sh copies to ~/.local/share/warp-legacy/browser.

All colours come from one table, roles(), so the three outputs agree.
"""
import importlib.util
import json
import shutil
import stat
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def roles(P, neon):
    """Browser colour roles (Firefox theme keys) from a build.py palette."""
    if neon:
        cyan, violet, pink = P["light"], P["dark"], P["selection_glow"][2]
        return dict(
            frame=P["title_active"], frame_inactive=P["title_inactive"],
            tab_background_text=P["text2"], tab_text="#ffffff",
            tab_selected=P["hover"], tab_line=cyan, tab_loading=pink,
            tab_background_separator="#2b3f8f",
            toolbar=P["surface"], toolbar_text=P["text"],
            toolbar_top_separator=cyan, toolbar_bottom_separator=violet,
            toolbar_vertical_separator="#2b3f8f",
            toolbar_field=P["window"], toolbar_field_text=P["text"],
            toolbar_field_border="#2b3f8f",
            toolbar_field_focus=P["window"], toolbar_field_text_focus="#ffffff",
            toolbar_field_border_focus=cyan,
            toolbar_field_highlight=P["selection"], toolbar_field_highlight_text="#ffffff",
            icons=P["link"], icons_attention=pink,
            button_background_hover=P["hover"], button_background_active="#1d3480",
            popup=P["surface"], popup_text=P["text"], popup_border=cyan,
            popup_highlight=P["selection"], popup_highlight_text="#ffffff",
            sidebar=P["window"], sidebar_text=P["text"], sidebar_border=violet,
            sidebar_highlight=P["selection"], sidebar_highlight_text="#ffffff",
            ntp_background=P["desktop"], ntp_text=P["text"], ntp_card_background=P["surface"],
            link=P["link"], focus=cyan,
            tabstrip_icons=P["link"], tabstrip_hover=P["hover"], glyph="#ffffff",
            close_hover=pink,
            # decoration, not Firefox keys
            accent1=cyan, accent2=violet, accent3=pink, scheme="dark")
    return dict(
        # Warp 4: tabs on the blue title bar, the selected one grey like the
        # window body below it.
        frame=P["title_active"], frame_inactive=P["title_inactive"],
        tab_background_text=P["title_active_text"], tab_text=P["text"],
        tab_selected=P["surface"], tab_line=P["light"], tab_loading=P["desktop"],
        tab_background_separator=P["dark"],
        toolbar=P["surface"], toolbar_text=P["text"],
        toolbar_top_separator=P["light"], toolbar_bottom_separator=P["dark"],
        toolbar_vertical_separator=P["dark"],
        toolbar_field=P["window"], toolbar_field_text=P["text"],
        toolbar_field_border=P["dark"],
        toolbar_field_focus=P["window"], toolbar_field_text_focus=P["text"],
        toolbar_field_border_focus=P["selection"],
        toolbar_field_highlight=P["selection"], toolbar_field_highlight_text=P["selection_text"],
        icons=P["text"], icons_attention=P["selection"],
        button_background_hover=P["hover"], button_background_active=P["groove"],
        popup=P["surface"], popup_text=P["text"], popup_border=P["border"],
        popup_highlight=P["selection"], popup_highlight_text=P["selection_text"],
        # Warp 4's lists select in grey, menus in blue (DESIGN.md §2)
        sidebar=P["window"], sidebar_text=P["text"], sidebar_border=P["dark"],
        sidebar_highlight=P["dark"], sidebar_highlight_text="#ffffff",
        # New tab: Warp 3's teal desktop, black labels as on it
        ntp_background=P["desktop"], ntp_text="#000000", ntp_card_background=P["window"],
        link=P["link"], focus=P["selection"],
        # icons on the blue title bar: white, as the title text
        tabstrip_icons=P["title_active_text"], tabstrip_hover="rgba(255, 255, 255, 0.25)",
        glyph=P["title_active_text"], close_hover=P["error"],
        accent1=P["light"], accent2=P["dark"], accent3=P["border"], scheme="light")


def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


FIREFOX_KEYS = [
    "frame", "frame_inactive", "tab_background_text", "tab_text", "tab_selected", "tab_line",
    "tab_loading", "tab_background_separator", "toolbar", "toolbar_text", "toolbar_top_separator",
    "toolbar_bottom_separator", "toolbar_vertical_separator", "toolbar_field", "toolbar_field_text",
    "toolbar_field_border", "toolbar_field_focus", "toolbar_field_text_focus",
    "toolbar_field_border_focus", "toolbar_field_highlight", "toolbar_field_highlight_text",
    "icons", "icons_attention", "button_background_hover", "button_background_active",
    "popup", "popup_text", "popup_border", "popup_highlight", "popup_highlight_text",
    "sidebar", "sidebar_text", "sidebar_border", "sidebar_highlight", "sidebar_highlight_text",
    "ntp_background", "ntp_text", "ntp_card_background"]

# The lit top edge of a Neon frame: cyan -> pink -> violet, fading out
STREAK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2" viewBox="0 0 3840 2">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="{a1}"/><stop offset="0.25" stop-color="{a3}"/>
    <stop offset="0.5" stop-color="{a2}"/><stop offset="0.75" stop-color="{a2}" stop-opacity="0"/>
  </linearGradient></defs>
  <rect width="3840" height="2" fill="url(#g)"/>
</svg>
"""


def firefox_manifest(name, id_, version, R, neon):
    theme = {"colors": {k: R[k] for k in FIREFOX_KEYS}}
    if neon:
        theme["images"] = {"additional_backgrounds": ["images/streak.svg"]}
        theme["properties"] = {"additional_backgrounds_alignment": ["left top"],
                               "additional_backgrounds_tiling": ["no-repeat"],
                               "color_scheme": "dark", "content_color_scheme": "auto"}
    else:
        theme["properties"] = {"color_scheme": "light", "content_color_scheme": "auto"}
    return {"manifest_version": 2, "name": name, "version": version,
            "description": ("OS/2 Warp at night: navy, cyan and violet edges" if neon else
                            "Warp 4 classic: grey toolbars, blue title bar") +
            ". Companion to the Warp Legacy Plasma theme.",
            "browser_specific_settings": {"gecko": {"id": f"{id_}@warplegacy.theme",
                                                    "strict_min_version": "128.0"}},
            "theme": theme}


def chrome_manifest(name, version, R, neon):
    c = {"frame": R["frame"], "frame_inactive": R["frame_inactive"],
         "frame_incognito": R["frame"], "frame_incognito_inactive": R["frame_inactive"],
         "toolbar": R["toolbar"], "toolbar_text": R["toolbar_text"],
         "toolbar_button_icon": R["icons"],
         "tab_text": R["tab_text"], "tab_background_text": R["tab_background_text"],
         "tab_background_text_inactive": R["tab_background_text"],
         "tab_background_text_incognito": R["tab_background_text"],
         "bookmark_text": R["toolbar_text"],
         "omnibox_background": R["toolbar_field"], "omnibox_text": R["toolbar_field_text"],
         "ntp_background": R["ntp_background"], "ntp_text": R["ntp_text"],
         "ntp_link": R["link"], "ntp_header": R["toolbar_bottom_separator"]}
    return {"manifest_version": 3, "name": name, "version": version,
            "description": "Companion to the Warp Legacy Plasma theme.",
            "theme": {"colors": {k: rgb(v) for k, v in c.items()},
                      # HSL shifts, -1 = keep. Buttons: Chrome derives icon
                      # colours from these where toolbar_button_icon is unknown.
                      "tints": {"buttons": [0.55, 0.9, 0.7] if neon else [-1, 0, 0],
                                "frame": [-1, -1, -1], "frame_inactive": [-1, -1, -1],
                                "frame_incognito": [-1, -1, -1],
                                "frame_incognito_inactive": [-1, -1, -1]},
                      "properties": {"ntp_background_alignment": "bottom"}}}


def glyph(path, colour):
    """A 16 px window-button glyph as a data: URI (stroke only)."""
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' "
           f"fill='none' stroke='{colour}' stroke-width='1.5'><path d='{path}'/></svg>")
    return 'url("data:image/svg+xml,' + svg.replace("#", "%23").replace('"', "'") + '")'


# OS/2's own window-button glyphs instead of the icon theme's symbolic
# icons, which may be invisible on the title bar colour.
GLYPHS = {"close": "M3.5 3.5l9 9M12.5 3.5l-9 9", "min": "M4 11.5h8",
          "max": "M3.5 3.5h9v9h-9z", "restore": "M5.5 5.5h5v5h-5z"}


def userchrome_css(name, R, neon):
    """userChrome.css: Firefox's chrome variables (as of Firefox 153).

    Firefox's own theme engine sets the same variables from a theme's
    manifest; here they are set from a user sheet with !important, which wins
    over the default theme and over any add-on theme still installed.
    """
    v = {
        "--toolbox-background-color": R["frame"],
        "--toolbox-background-color-inactive": R["frame_inactive"],
        "--toolbox-text-color": R["tab_background_text"],
        "--toolbox-text-color-inactive": R["tab_background_text"],
        "--lwt-accent-color": R["frame"],
        "--lwt-accent-color-inactive": R["frame_inactive"],
        "--lwt-text-color": R["tab_background_text"],
        "--tab-background-color-selected": R["tab_selected"],
        "--tab-selected-textcolor": R["tab_text"],
        "--lwt-tab-line-color": R["tab_line"],
        "--tab-loading-fill": R["tab_loading"],
        "--lwt-background-tab-separator-color": R["tab_background_separator"],
        "--toolbar-background-color": R["toolbar"],
        "--toolbar-text-color": R["toolbar_text"],
        "--tabs-navbar-separator-color": R["toolbar_top_separator"],
        "--toolbarseparator-color": R["toolbar_vertical_separator"],
        "--chrome-content-separator-color": R["toolbar_bottom_separator"],
        "--toolbar-field-background-color": R["toolbar_field"],
        "--toolbar-field-text-color": R["toolbar_field_text"],
        "--toolbar-field-border-color": R["toolbar_field_border"],
        "--toolbar-field-background-color-focus": R["toolbar_field_focus"],
        "--toolbar-field-text-color-focus": R["toolbar_field_text_focus"],
        "--toolbar-field-border-color-focus": R["toolbar_field_border_focus"],
        "--lwt-toolbar-field-highlight": R["toolbar_field_highlight"],
        "--lwt-toolbar-field-highlight-text": R["toolbar_field_highlight_text"],
        "--toolbarbutton-icon-fill": R["icons"],
        "--toolbarbutton-icon-fill-attention": R["icons_attention"],
        "--toolbarbutton-background-color-hover": R["button_background_hover"],
        "--toolbarbutton-background-color-active": R["button_background_active"],
        "--panel-background-color": R["popup"],
        "--panel-text-color": R["popup_text"],
        "--panel-border-color": R["popup_border"],
        "--panel-separator-color": R["toolbar_vertical_separator"],
        "--urlbarview-background-color-selected": R["popup_highlight"],
        "--urlbarview-text-color-selected": R["popup_highlight_text"],
        "--urlbarview-background-color-hover": R["button_background_hover"],
        "--sidebar-background-color": R["sidebar"],
        "--sidebar-text-color": R["sidebar_text"],
        "--sidebar-border-color": R["sidebar_border"],
        "--tabpanel-background-color": R["ntp_background"],
        "--newtab-background-color": R["ntp_background"],
        "--newtab-text-primary-color": R["ntp_text"],
        "--focus-outline-color": R["focus"],
    }
    decl = "\n".join(f"  {k}: {c} !important;" for k, c in v.items())
    a1, a2, a3 = R["accent1"], R["accent2"], R["accent3"]
    if neon:
        extra = f"""
/* Neon: the lit frame edge on top (cyan -> pink -> violet, fading out),
   the selected tab outlined in cyan with a faint glow. */
#TabsToolbar {{
  background-image: linear-gradient(to right, {a1}, {a3} 25%, {a2} 50%, transparent 75%) !important;
  background-size: 100% 2px !important;
  background-repeat: no-repeat !important;
  background-position: top !important;
}}
.tab-background:is([selected], [multiselected]) {{
  outline: 1px solid {a1} !important;
  outline-offset: -1px !important;
  box-shadow: 0 0 6px {a1}66 !important;
}}
#nav-bar {{
  border-top: 1px solid {a1}55 !important;
  box-shadow: inset 0 -1px 0 {a2} !important;
}}
#urlbar[focused] > .urlbar-background, #urlbar[focused] > #urlbar-background,
#searchbar:focus-within {{
  box-shadow: 0 0 0 1px {a1}, 0 0 8px {a1}88 !important;
}}
menupopup, panel {{ --panel-border-radius: 0px !important; }}
"""
    else:
        extra = f"""
/* Warp 4: square corners, raised selected tab (white top/left, grey
   bottom/right), sunken address field (grey top/left, white bottom/right). */
.tab-background {{ border-radius: 0 !important; }}
.tab-background:is([selected], [multiselected]) {{
  outline: none !important;
  box-shadow: inset 1px 1px 0 {a1}, inset -1px -1px 0 {a2} !important;
}}
#urlbar-background, .urlbar-background, #searchbar {{
  border-radius: 0 !important;
  border: 1px solid !important;
  border-color: {a2} {a1} {a1} {a2} !important;
  box-shadow: inset 1px 1px 0 #000000 !important;
}}
#urlbar[focused] > .urlbar-background, #urlbar[focused] > #urlbar-background {{
  outline: 1px solid {R["focus"]} !important;
  outline-offset: 0 !important;
}}
#nav-bar {{
  border-top: 1px solid {a1} !important;
  box-shadow: inset 0 -1px 0 {a2} !important;
}}
toolbarbutton .toolbarbutton-icon, toolbarbutton .toolbarbutton-badge-stack,
toolbarbutton .toolbarbutton-text {{ border-radius: 0 !important; }}
menupopup, panel {{ --panel-border-radius: 0px !important; }}
"""
    buttons = "\n".join(
        f".titlebar-{k} > .toolbarbutton-icon {{ background-image: {glyph(d, R['glyph'])} !important; }}"
        for k, d in GLYPHS.items()) + f"""
.titlebar-button:hover > .toolbarbutton-icon {{
  background-color: {R["tabstrip_hover"]} !important;
}}
.titlebar-close:hover > .toolbarbutton-icon {{ background-color: {R["close_hover"]} !important; }}"""
    return f"""/* {name} for Firefox (userChrome.css), generated by build_browser.py.
   Installed by firefox-apply.sh; remove with: firefox-apply.sh remove */

:root, #navigator-toolbox, toolbar, menupopup, panel, #urlbar, .urlbarView,
#sidebar-box, #sidebar-main, sidebar-main, #tabbrowser-tabpanels {{
{decl}
}}

:root {{ color-scheme: {R["scheme"]} !important; }}

/* The tab strip sits on the title bar colour. */
#TabsToolbar, .titlebar-buttonbox-container {{
  --toolbarbutton-icon-fill: {R["tabstrip_icons"]} !important;
  --toolbarbutton-background-color-hover: {R["tabstrip_hover"]} !important;
}}
{buttons}

/* Context and main menus draw with the system's Menu colours; take the
   theme's instead. */
menupopup {{ color: {R["popup_text"]} !important; }}
menupopup > :is(menu, menuitem)[_moz-menuactive]:not([disabled]) {{
  background-color: {R["popup_highlight"]} !important;
  color: {R["popup_highlight_text"]} !important;
}}
{extra}"""


def usercontent_css(name, R):
    """userContent.css: the new tab and home page in the theme's colours."""
    return f"""/* {name} for Firefox (userContent.css), generated by build_browser.py. */

@-moz-document url("about:newtab"), url("about:home"), url("about:privatebrowsing") {{
  :root {{ color-scheme: {R["scheme"]} !important; }}
  :root, body {{
    --newtab-background-color: {R["ntp_background"]} !important;
    --newtab-background-color-secondary: {R["ntp_card_background"]} !important;
    --newtab-text-primary-color: {R["ntp_text"]} !important;
    background-color: {R["ntp_background"]} !important;
    color: {R["ntp_text"]} !important;
  }}
}}
"""


def write_zip(src, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(src).as_posix())


def build_browser(out, variants, version="0.1.0"):
    """Build all browser themes into out (a directory, recreated).

    variants: build.py's VARIANTS, i.e. dicts with key ("" or "neon"),
    name and the palette P.
    """
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    for v in variants:
        neon = v["key"] == "neon"
        id_ = "warp-legacy" + ("-neon" if neon else "")
        R = roles(v["P"], neon)

        ff = out / "firefox" / id_
        ff.mkdir(parents=True)
        (ff / "manifest.json").write_text(
            json.dumps(firefox_manifest(v["name"], id_, version, R, neon), indent=2) + "\n")
        if neon:
            (ff / "images").mkdir()
            (ff / "images/streak.svg").write_text(
                STREAK_SVG.format(a1=R["accent1"], a2=R["accent2"], a3=R["accent3"]))
        write_zip(ff, out / "firefox" / f"{id_}.xpi")

        ch = out / "chrome" / id_
        ch.mkdir(parents=True)
        (ch / "manifest.json").write_text(
            json.dumps(chrome_manifest(v["name"], version, R, neon), indent=2) + "\n")
        write_zip(ch, out / "chrome" / f"{id_}.zip")

        uc = out / "userchrome" / ("neon" if neon else "classic")
        uc.mkdir(parents=True)
        (uc / "userChrome.css").write_text(userchrome_css(v["name"], R, neon))
        (uc / "userContent.css").write_text(usercontent_css(v["name"], R))

    script = out / "firefox-apply.sh"
    shutil.copy2(HERE / "firefox-apply.sh", script)
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def main():
    spec = importlib.util.spec_from_file_location("warp_build", HERE.parent / "build.py")
    build = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE.parent))
    spec.loader.exec_module(build)
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else build.OUT / "warp-legacy/browser"
    build_browser(out, build.VARIANTS, build.VERSION)
    print(f"Browser themes built in {out}")


if __name__ == "__main__":
    main()
