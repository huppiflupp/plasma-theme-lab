"""Testing in the lab VMs: install, apply, screenshot, uninstall.

Three environments, all through ../vm/vmctl.sh (LAB_ENV picks the machine):

    fedora  plasma-lab  (lab.env)     Fedora 44, systemd, Plasma 6.7
    ubuntu  ubuntu-lab  (ubuntu.env)  Ubuntu 26.04 LTS, an older Plasma
    artix   artix-lab   (artix.env)   Artix, OpenRC, no systemd user manager;
                                      exercises the installers' setsid and
                                      kquitapp6 branches that never run
                                      elsewhere

Per VM: revert to the snapshot `clean` (can be skipped), switch the Plasma
session to the language asked for (English by default: screenshots and
store pictures are taken in English) and log in again, copy the package to
~/forge-test/<id>, `install.sh --apply <variant>`, screenshot,
`uninstall.sh`, screenshot. Checked: both scripts end without an error and
the watched settings are exactly as before afterwards.
Result in <out>/vmtest.json, screenshots in <out>/vm-<environment>-*.png.
"""
import json
import os
import subprocess
import time

VM_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vm"))
ENVS = {"fedora": "lab.env", "ubuntu": "ubuntu.env", "artix": "artix.env"}
# What a theme touches and uninstall.sh must put back: file, group, key.
WATCH = [("kdeglobals", "KDE", "LookAndFeelPackage"), ("kdeglobals", "General", "ColorScheme"),
         ("kdeglobals", "Icons", "Theme"), ("kdeglobals", "KDE", "widgetStyle"),
         ("kwinrc", "org.kde.kdecoration2", "theme"), ("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft"),
         ("plasmarc", "Theme", "name")]
# The session's language: LANGUAGE for the translations; LANG is the first
# of these locales the guest has (Fedora's lab VM brings en_GB, not en_US).
LOCALES = {"en": ("en_US.UTF-8", "en_GB.UTF-8", "C.UTF-8"), "de": ("de_DE.UTF-8",)}


def vmctl(env, *args, timeout=900, check=False):
    r = subprocess.run([os.path.join(VM_DIR, "vmctl.sh"), *args], cwd=VM_DIR, capture_output=True, text=True,
                       timeout=timeout, env={**os.environ, "LAB_ENV": ENVS[env]})
    if check and r.returncode:
        raise RuntimeError(f"vmctl {' '.join(args)} ({env}): {r.stderr.strip() or r.stdout.strip()}")
    return r


def settings(env):
    script = "; ".join(f"echo \"$(kreadconfig6 --file {f} --group {g} --key {k})\"" for f, g, k in WATCH)
    out = vmctl(env, "ssh", script, check=True).stdout.splitlines()
    return {f"{f}[{g}]{k}": (out[i] if i < len(out) else "") for i, (f, g, k) in enumerate(WATCH)}


# The XDG folders in English (the VMs were built German: Bilder, Schreibtisch,
# Vorlagen, Öffentlich …). Written by hand: Artix has no xdg-user-dirs-update.
# Contents move along, a German folder left empty is removed, and Dolphin's
# places (user-places.xbel, which holds the old paths) are made anew by KDE.
# It runs before the restart and once more after it: the German plasmashell
# still running recreated "Schreibtisch" the moment it was gone.
ENGLISH_DIRS = r"""
f="$HOME/.config/user-dirs.dirs"; tmp="$f.new"; : > "$tmp"
for triple in DESKTOP:Desktop:Schreibtisch DOWNLOAD:Downloads:Downloads TEMPLATES:Templates:Vorlagen \
              PUBLICSHARE:Public:Öffentlich DOCUMENTS:Documents:Dokumente MUSIC:Music:Musik \
              PICTURES:Pictures:Bilder VIDEOS:Videos:Videos PROJECTS:Projects:Projekte; do
    key=${triple%%:*}; rest=${triple#*:}; name=${rest%%:*}; de=${rest#*:}; new="$HOME/$name"
    old=$(sed -n "s/^XDG_${key}_DIR=\"\(.*\)\"$/\1/p" "$f" 2>/dev/null | sed "s|\$HOME|$HOME|")
    mkdir -p "$new"
    for src in "$old" "$HOME/$de"; do
        if [ -n "$src" ] && [ "$src" != "$new" ] && [ "$src" != "$HOME" ] && [ -d "$src" ]; then
            find "$src" -mindepth 1 -maxdepth 1 -exec mv -n {} "$new"/ \;
            rm -f "$src/.directory"
            rmdir "$src" 2>/dev/null || echo "kept $src (name clash inside)"
        fi
    done
    printf 'XDG_%s_DIR="$HOME/%s"\n' "$key" "$name" >> "$tmp"
done
mv "$tmp" "$f"
echo en_US > "$HOME/.config/user-dirs.locale"
rm -f "$HOME/.local/share/user-places.xbel" "$HOME/.local/share/user-places.xbel.bak" \
      "$HOME/.local/share/user-places.xbel.tbcache"
"""


def set_language(env, lang, log=print):
    """Switch the Plasma session to `lang` for good; None keeps the VM's own.

    plasma-localerc alone is not enough (plasma-lab, 26.10.2026):
    startplasma gets LANG from SDDM, SDDM from PID 1, and PID 1 reads
    /etc/locale.conf only at boot; the systemd user manager also keeps its
    environment (LANG=de_DE…) while SSH sessions keep it alive and hands it
    on to the next Plasma session. Hence: the system locale (localectl, or
    /etc/locale.conf on OpenRC), plasma-localerc, the user manager's
    environment, then a reboot (restarting SDDM is not enough). The keyboard
    layout stays as it is. Returns the LANG plasmashell runs with."""
    if not lang:
        return None
    candidates = " ".join(LOCALES.get(lang, (f"{lang}.UTF-8",)))
    language = {"en": "en_US"}.get(lang, lang)
    gen = ("locale -a 2>/dev/null | grep -qi '^en_US.utf-\\?8$' || { command -v locale-gen >/dev/null 2>&1 && "
           "sudo -n locale-gen en_US.UTF-8 >/dev/null 2>&1; }; ") if lang == "en" else ""
    script = (gen + f"have=$(locale -a 2>/dev/null | sed 's/utf8/UTF-8/'); for l in {candidates}; do "
              "printf '%s\\n' \"$have\" | grep -qix \"$l\" && break; done; "
              "if [ -d /run/systemd/system ] && command -v localectl >/dev/null 2>&1; then "
              "sudo -n localectl set-locale LANG=\"$l\"; "
              "else printf 'LANG=%s\\n' \"$l\" | sudo -n tee /etc/locale.conf >/dev/null; fi; "
              "kwriteconfig6 --file plasma-localerc --group Formats --key LANG \"$l\"; "
              f"kwriteconfig6 --file plasma-localerc --group Translations --key LANGUAGE {language}; "
              f"systemctl --user set-environment LANG=\"$l\" LANGUAGE={language} 2>/dev/null; echo \"$l\"")
    chosen = (vmctl(env, "ssh", script, check=True).stdout.strip().splitlines() or ["?"])[-1]
    if lang == "en":
        r = vmctl(env, "ssh", ENGLISH_DIRS, check=True)
        for line in r.stdout.strip().splitlines():
            log(f"[{env}] {line}")
    log(f"[{env}] session language {lang} ({chosen}), restarting the VM")
    vmctl(env, "stop", check=True)
    vmctl(env, "start", check=True)
    running = ""
    for _ in range(12):                 # until the autologin's plasmashell is up
        time.sleep(5)
        r = vmctl(env, "ssh", "p=$(pgrep -xo plasmashell) && tr '\\0' '\\n' < /proc/$p/environ | sed -n 's/^LANG=//p'")
        running = r.stdout.strip()
        if running:
            break
    if lang == "en":                     # what the old session recreated before the restart
        for line in vmctl(env, "ssh", ENGLISH_DIRS).stdout.strip().splitlines():
            log(f"[{env}] {line}")
    log(f"[{env}] plasmashell runs with LANG={running or '?'}")
    return running


def session_lang(env):
    """The LANG the running plasmashell has, "" if none runs (yet)."""
    for _ in range(12):
        r = vmctl(env, "ssh", "p=$(pgrep -xo plasmashell) && tr '\\0' '\\n' < /proc/$p/environ | sed -n 's/^LANG=//p'")
        if r.stdout.strip():
            return r.stdout.strip()
        time.sleep(5)
    return ""


def revert(env, lang, log=print):
    """Back to the starting state: the snapshot clean-en when English is asked
    for and the VM has one (language and folders switched already, saves the
    restart), else clean. Returns True when the language is ready."""
    import re
    snaps = vmctl(env, "snap", "list").stdout
    if lang == "en" and re.search(r"^\s*clean-en\s", snaps, re.M):
        log(f"[{env}] snapshot clean-en …")
        vmctl(env, "snap", "revert", "clean-en", check=True)
        return True
    log(f"[{env}] snapshot clean …")
    vmctl(env, "reset", check=True)
    return False


def make_clean_en(env, log=print):
    """The snapshot clean-en: clean with the session and the XDG folders in
    English, so runs need not switch and restart every time. vmctl's snapshot
    is taken with the VM shut down (offline)."""
    vmctl(env, "snap", "revert", "clean", check=True, timeout=600)
    lang = set_language(env, "en", log)
    if not lang.lower().startswith("en"):
        raise RuntimeError(f"{env}: the session did not switch (LANG={lang or '?'}); no snapshot taken")
    r = vmctl(env, "ssh", "ls ~; cat ~/.config/user-dirs.dirs")
    log(r.stdout.strip())
    vmctl(env, "snap", "create", "clean-en", check=True, timeout=600)
    log(f"[{env}] snapshot clean-en created")


def run_one(env, pkg, variant, out, reset=True, lang="en", log=print):
    rep = {"env": env, "variant": variant, "lang": lang, "errors": []}
    if reset:
        ready = revert(env, lang, log)
    else:
        vmctl(env, "start", check=True)
        ready = False
    session = session_lang(env) if ready else set_language(env, lang, log)
    rep["session_lang"] = session
    if lang and session is not None and not session.lower().startswith(lang.lower()):
        rep["errors"].append(f"the session did not switch to {lang} (plasmashell has LANG={session or '?'})")
    time.sleep(10)                       # Plasma after the autologin
    theme = os.path.basename(os.path.dirname(os.path.abspath(pkg))) or "theme"
    target = f"forge-test/{theme}/"
    before = settings(env)
    vmctl(env, "ssh", f"mkdir -p {target}", check=True)
    vmctl(env, "push", os.path.abspath(pkg) + "/", target, check=True)
    log(f"[{env}] install.sh --apply {variant}")
    r = vmctl(env, "ssh", f"cd {target} && ./install.sh --apply {variant}")
    rep["install"] = {"rc": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-6:]}
    if r.returncode:
        rep["errors"].append(f"install.sh ended with {r.returncode}")
    time.sleep(8)
    rep["applied_shot"] = vmctl(env, "shot", os.path.abspath(f"{out}/vm-{env}-applied.png")).stdout.strip()
    rep["applied"] = settings(env)
    if rep["applied"] == before:
        rep["errors"].append("--apply changed none of the watched settings")
    log(f"[{env}] uninstall.sh")
    r = vmctl(env, "ssh", f"cd {target} && ./uninstall.sh")
    rep["uninstall"] = {"rc": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-6:]}
    if r.returncode:
        rep["errors"].append(f"uninstall.sh ended with {r.returncode}")
    time.sleep(8)
    rep["after_shot"] = vmctl(env, "shot", os.path.abspath(f"{out}/vm-{env}-after.png")).stdout.strip()
    after = settings(env)
    rep["not_restored"] = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if rep["not_restored"]:
        rep["errors"].append("not as before after uninstall.sh: " + ", ".join(rep["not_restored"]))
    return rep


def run(out, envs=("fedora", "ubuntu", "artix"), variant=None, reset=True, lang="en", log=print):
    pkg = f"{out}/package"
    spec = json.load(open(f"{out}/spec.json"))
    variant = variant or spec["variants"][0]["id"]
    reports = []
    for env in envs:
        if env not in ENVS:
            raise ValueError(f"unknown VM {env} (there are: {', '.join(ENVS)})")
        try:
            rep = run_one(env, pkg, variant, out, reset=reset, lang=lang, log=log)
        except Exception as e:  # noqa: BLE001 - one broken VM must not hold up the others
            rep = {"env": env, "variant": variant, "lang": lang, "errors": [f"run aborted: {e}"]}
        for e in rep["errors"]:
            log(f"[{env}] ERROR: {e}")
        if not rep["errors"]:
            log(f"[{env}] OK")
        reports.append(rep)
    with open(f"{out}/vmtest.json", "w") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    return reports
