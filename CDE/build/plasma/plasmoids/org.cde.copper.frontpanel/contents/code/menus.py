#!/usr/bin/env python3
"""Subpanel contents for the CDE front console: a browser's bookmarks and an
application's recently opened files.

    menus.py bookmarks <slot command>
    menus.py recent <slot command>
    menus.py tray

The slot command is what the tile starts: "@browser", "@editor", "app:<id>"
or a shell command. It is resolved to the application the desktop would
actually start (System Settings › Default Applications for the "@" tokens).
Output is a JSON list of {label, icon, args, tip}; args are passed to the
slot's command when an entry is chosen.

"tray" prints the ids of the applications' status icons (StatusNotifierItem)
now registered, as a JSON list, so the console can hide them in the tray.

Standard library only; it runs inside the user's session on demand.
"""
import configparser
import json
import os
import re
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET

HOME = Path.home()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
LIMIT = 15

QUERIES = {"@browser": ["xdg-settings", "get", "default-web-browser"],
           "@editor": ["xdg-mime", "query", "default", "text/plain"],
           "@mail": ["xdg-mime", "query", "default", "x-scheme-handler/mailto"],
           "@files": ["xdg-mime", "query", "default", "inode/directory"]}


def data_dirs():
    dirs = [DATA_HOME] + [Path(d) for d in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if d]
    return dirs + [HOME / ".local/share/flatpak/exports/share", Path("/var/lib/flatpak/exports/share")]


def desktop_entry(app_id):
    """Name, Exec binary and Icon of an installed application, or None."""
    name = app_id if app_id.endswith(".desktop") else app_id + ".desktop"
    for d in data_dirs():
        path = d / "applications" / name
        if path.is_file():
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
                entry = parser["Desktop Entry"]
            except (configparser.Error, KeyError, UnicodeDecodeError):
                return None
            exec_line = entry.get("Exec", "").split()
            binary = os.path.basename(exec_line[0]) if exec_line else ""
            if binary == "flatpak":   # flatpak run ... <app id>
                binary = next((w for w in exec_line if "." in w and not w.startswith("-")), binary)
            return {"id": name[:-8], "name": entry.get("Name", ""), "binary": binary, "icon": entry.get("Icon", "")}
    return None


def resolve(command):
    """The application behind a slot command: {id, name, binary, icon}."""
    token = command.strip().split()[0] if command.strip() else ""
    if token in QUERIES:
        try:
            app_id = subprocess.run(QUERIES[token], capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            app_id = ""
        entry = desktop_entry(app_id) if app_id else None
        if entry:
            return entry
        return {"id": "", "name": "", "binary": {"@browser": "firefox", "@editor": "kate"}.get(token, ""), "icon": ""}
    if token.startswith("app:"):
        return desktop_entry(token[4:]) or {"id": token[4:], "name": "", "binary": token[4:], "icon": ""}
    return {"id": "", "name": "", "binary": os.path.basename(token), "icon": ""}


def keys(app):
    """Lower-case names an application may be recorded under."""
    found = {app["id"].lower(), app["name"].lower(), app["binary"].lower()}
    if app["id"]:
        found.add(app["id"].lower().split(".")[-1])
    # LibreOffice: every module records itself as LibreOffice / soffice.
    if any(k.startswith(("libreoffice", "soffice")) for k in found if k):
        found |= {"libreoffice", "soffice"}
    return {k for k in found if k}


# ---- bookmarks ----------------------------------------------------------

def firefox_profiles(kind):
    roots = {"firefox": [CONFIG_HOME / "mozilla/firefox", HOME / ".mozilla/firefox",
                         HOME / ".var/app/org.mozilla.firefox/.mozilla/firefox",
                         HOME / ".var/app/org.mozilla.firefox/config/mozilla/firefox"],
             "librewolf": [HOME / ".librewolf", CONFIG_HOME / "librewolf/librewolf",
                           HOME / ".var/app/io.gitlab.librewolf-community/.librewolf"]}[kind]
    for root in roots:
        ini = root / "profiles.ini"
        if not ini.is_file():
            continue
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.read(ini)
        chosen = []
        for section in parser.sections():
            if section.startswith("Install") and parser[section].get("Default"):
                chosen.append(parser[section]["Default"])
        for section in parser.sections():
            if section.startswith("Profile") and parser[section].get("Default") == "1":
                chosen.append(parser[section].get("Path", ""))
        chosen += [parser[s].get("Path", "") for s in parser.sections() if s.startswith("Profile")]
        for rel in chosen:
            path = Path(rel) if Path(rel).is_absolute() else root / rel
            if (path / "places.sqlite").is_file():
                yield path


def firefox_bookmarks(kind):
    for profile in firefox_profiles(kind):
        # The browser holds a lock: read a copy, with its write-ahead log.
        with tempfile.TemporaryDirectory(prefix="cde-places-") as temp:
            for name in ("places.sqlite", "places.sqlite-wal"):
                if (profile / name).is_file():
                    shutil.copy2(profile / name, Path(temp) / name)
            try:
                db = sqlite3.connect(Path(temp) / "places.sqlite")
                rows = db.execute("""
                    SELECT b.title, p.url, parent.guid = 'toolbar_____' AS toolbar
                    FROM moz_bookmarks b
                    JOIN moz_places p ON p.id = b.fk
                    JOIN moz_bookmarks parent ON parent.id = b.parent
                    WHERE b.type = 1 AND p.url NOT LIKE 'place:%'
                    ORDER BY toolbar DESC, CASE WHEN toolbar THEN b.position END, b.dateAdded DESC
                    LIMIT ?""", (LIMIT,)).fetchall()
                db.close()
            except sqlite3.Error:
                continue
        return [(title or url, url) for title, url, _ in rows]
    return []


def chromium_bookmarks(paths):
    def walk(node):
        if node.get("type") == "url":
            yield node.get("name") or node.get("url"), node.get("url")
        for child in node.get("children", []):
            yield from walk(child)
    for path in paths:
        if path.is_file():
            try:
                roots = json.loads(path.read_text(encoding="utf-8")).get("roots", {})
            except (OSError, ValueError):
                continue
            found = []
            for root in ("bookmark_bar", "other", "synced"):
                if isinstance(roots.get(root), dict):
                    found += list(walk(roots[root]))
            return found[:LIMIT]
    return []


def xbel_bookmarks(path):
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return []
    found = []
    for mark in tree.iter("bookmark"):
        title = mark.findtext("title") or mark.get("href")
        if mark.get("href"):
            found.append((title, mark.get("href")))
    return found[:LIMIT]


CHROMIUM = {"chromium": "chromium", "chromium-browser": "chromium", "google-chrome": "google-chrome",
            "google-chrome-stable": "google-chrome", "brave": "BraveSoftware/Brave-Browser",
            "brave-browser": "BraveSoftware/Brave-Browser", "vivaldi": "vivaldi", "vivaldi-stable": "vivaldi",
            "microsoft-edge": "microsoft-edge", "opera": "opera"}


def bookmarks(app):
    k = keys(app)
    if k & {"firefox", "org.mozilla.firefox", "firefox-esr"}:
        found = firefox_bookmarks("firefox")
    elif k & {"librewolf", "io.gitlab.librewolf-community"}:
        found = firefox_bookmarks("librewolf")
    elif k & set(CHROMIUM):
        folder = CHROMIUM[next(iter(k & set(CHROMIUM)))]
        found = chromium_bookmarks([CONFIG_HOME / folder / "Default/Bookmarks"])
    elif k & {"falkon", "org.kde.falkon"}:
        found = chromium_bookmarks([CONFIG_HOME / "falkon/profiles/default/bookmarks.json"])
    elif k & {"konqueror", "org.kde.konqueror"}:
        found = xbel_bookmarks(DATA_HOME / "konqueror/bookmarks.xml")
    else:
        found = []
    seen, result = set(), []
    for title, url in found:
        if url not in seen:
            seen.add(url)
            result.append({"label": title, "icon": "internet-web-browser", "args": [url], "tip": url})
    return result


# ---- recent files -------------------------------------------------------
#
# Three places record what an application opened, and no application uses
# all of them: KDE programs report to Plasma's activity database (the source
# of the task manager's jump lists), GTK programs and downloads write
# recently-used.xbel, and LibreOffice keeps its own pick list.

NS = {"bookmark": "http://www.freedesktop.org/standards/desktop-bookmarks",
      "mime": "http://www.freedesktop.org/standards/shared-mime-info"}

# LibreOffice modules and the files they open, for the shared pick list.
OFFICE = {"writer": {"odt", "ott", "fodt", "doc", "docx", "dot", "dotx", "rtf", "txt"},
          "calc": {"ods", "ots", "fods", "xls", "xlsx", "xlsm", "csv"},
          "impress": {"odp", "otp", "fodp", "ppt", "pptx"},
          "draw": {"odg", "otg", "fodg", "vsd", "vsdx"},
          "math": {"odf", "mml"}}


def activity_files(wanted):
    """(time, path) from kactivitymanagerd, newest first."""
    folder = DATA_HOME / "kactivitymanagerd/resources"
    if not (folder / "database").is_file():
        return []
    with tempfile.TemporaryDirectory(prefix="cde-activities-") as temp:
        for name in ("database", "database-wal"):
            if (folder / name).is_file():
                shutil.copy2(folder / name, Path(temp) / name)
        try:
            db = sqlite3.connect(Path(temp) / "database")
            rows = db.execute("SELECT initiatingAgent, targettedResource, lastUpdate FROM ResourceScoreCache "
                              "WHERE targettedResource LIKE '/%' OR targettedResource LIKE 'file:%' "
                              "ORDER BY lastUpdate DESC LIMIT 400").fetchall()
            db.close()
        except sqlite3.Error:
            return []
    found = []
    for agent, resource, when in rows:
        agent = agent.lower()
        if agent in wanted or agent.split(".")[-1] in wanted:
            path = urllib.parse.unquote(urllib.parse.urlparse(resource).path) if resource.startswith("file:") else resource
            found.append((int(when or 0), path))
    return found


def xbel_files(wanted):
    """(time, path) from recently-used.xbel; ISO times compare as text."""
    try:
        tree = ET.parse(DATA_HOME / "recently-used.xbel")
    except (OSError, ET.ParseError):
        return []
    found = []
    for mark in tree.getroot().iter("bookmark"):
        href = mark.get("href", "")
        if not href.startswith("file://"):
            continue
        best = None
        for used in mark.iter("{%s}application" % NS["bookmark"]):
            exec_words = used.get("exec", "").strip("'\"").split()
            names = {used.get("name", "").lower()}
            if exec_words:
                names.add(os.path.basename(exec_words[0]).lower())
            if names & wanted:
                best = max(best or "", used.get("modified", ""))
        if best is not None:
            found.append((best, urllib.parse.unquote(urllib.parse.urlparse(href).path)))
    # ISO 8601 to seconds, so the sources can be merged.
    from datetime import datetime
    result = []
    for stamp, path in found:
        try:
            result.append((int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()), path))
        except ValueError:
            result.append((0, path))
    return result


def office_files(app):
    """LibreOffice's pick list, newest first, for the module of app."""
    if not keys(app) & {"libreoffice", "soffice"}:
        return []
    module = next((m for m in OFFICE if m in app["id"].lower() or m in app["name"].lower()), None)
    path = CONFIG_HOME / "libreoffice/4/user/registrymodifications.xcu"
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return []
    oor = "{http://openoffice.org/2001/registry}"
    order = {}
    for item in root.iter("item"):
        if "PickList']/OrderList" not in item.get(oor + "path", ""):
            continue
        for node in item.iter("node"):
            value = node.find(".//value")
            if value is not None and value.text and node.get(oor + "name", "").isdigit():
                order[int(node.get(oor + "name"))] = value.text
    found = []
    for rank in sorted(order):
        url = order[rank]
        if not url.startswith("file://"):
            continue
        file = urllib.parse.unquote(urllib.parse.urlparse(url).path)
        if module and Path(file).suffix.lower().lstrip(".") not in OFFICE[module]:
            continue
        # Newer than anything else, in pick-list order.
        found.append((2 ** 40 - rank, file))
    return found


def mime_icon(file):
    import mimetypes
    kind = mimetypes.guess_type(file)[0]
    return kind.replace("/", "-") if kind else "text-x-generic"


def recent(app):
    wanted = keys(app)
    found = office_files(app) + activity_files(wanted) + xbel_files(wanted)
    found.sort(key=lambda item: item[0], reverse=True)
    seen, result = set(), []
    for _, file in found:
        if file in seen or not os.path.isfile(file):
            continue
        seen.add(file)
        result.append({"label": os.path.basename(file), "icon": mime_icon(file), "args": [file], "tip": file})
    return result[:LIMIT]


def tray_ids():
    """Ids of the registered status icons, read over D-Bus with gdbus."""
    def get(service, path, interface, prop):
        result = subprocess.run(["gdbus", "call", "--session", "-d", service, "-o", path,
                                 "-m", "org.freedesktop.DBus.Properties.Get", interface, prop],
                                capture_output=True, text=True, timeout=3)
        return result.stdout if result.returncode == 0 else ""
    try:
        listing = get("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher",
                      "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems")
        ids = []
        for entry in re.findall(r"'([^']+)'", listing):
            service, _, path = entry.partition("/")
            found = re.search(r"'([^']*)'", get(service, "/" + path, "org.kde.StatusNotifierItem", "Id"))
            if found and found.group(1) and found.group(1) not in ids:
                ids.append(found.group(1))
        return ids
    except (OSError, subprocess.SubprocessError):
        return []


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "tray":
        print(json.dumps(tray_ids()))
        return 0
    if len(sys.argv) < 3 or sys.argv[1] not in ("bookmarks", "recent"):
        print(__doc__, file=sys.stderr)
        return 2
    app = resolve(sys.argv[2])
    items = bookmarks(app) if sys.argv[1] == "bookmarks" else recent(app)
    print(json.dumps({"app": app.get("name") or app.get("binary"), "items": items}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
