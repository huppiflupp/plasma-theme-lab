"""Prüfung in den Test-VMs: installieren, anwenden, Foto, deinstallieren.

Drei Umgebungen, alle über ../vm/vmctl.sh (LAB_ENV wählt die Maschine):

    fedora  plasma-lab  (lab.env)     Fedora 44, systemd, Plasma 6.7
    ubuntu  ubuntu-lab  (ubuntu.env)  Ubuntu 26.04 LTS, ältere Plasma-Fassung
    artix   artix-lab   (artix.env)   Artix, OpenRC — kein systemd-User-Manager;
                                      prüft die setsid-/kquitapp6-Zweige der
                                      Installer, die sonst nie laufen

Ablauf je VM: Snapshot `clean` zurück (abschaltbar), Paket nach
~/forge-test/<id> übertragen, `install.sh --apply <variante>`, Foto,
`uninstall.sh`, Foto. Geprüft wird, dass beide Skripte ohne Fehler enden
und die gemerkten Einstellungen danach wieder genau wie vorher sind.
Ergebnis in <out>/vmtest.json, Fotos in <out>/vm-<umgebung>-*.png.
"""
import json
import os
import subprocess
import time

VM_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vm"))
ENVS = {"fedora": "lab.env", "ubuntu": "ubuntu.env", "artix": "artix.env"}
# Was ein Theme anfasst und uninstall.sh zurückstellen muss: Datei, Gruppe, Schlüssel.
WATCH = [("kdeglobals", "KDE", "LookAndFeelPackage"), ("kdeglobals", "General", "ColorScheme"),
         ("kdeglobals", "Icons", "Theme"), ("kdeglobals", "KDE", "widgetStyle"),
         ("kwinrc", "org.kde.kdecoration2", "theme"), ("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft"),
         ("plasmarc", "Theme", "name")]


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


def run_one(env, pkg, variant, out, reset=True, log=print):
    rep = {"env": env, "variant": variant, "errors": []}
    if reset:
        log(f"[{env}] Snapshot clean …")
        vmctl(env, "reset", check=True)
    else:
        vmctl(env, "start", check=True)
    time.sleep(10)                       # Plasma nach dem Autologin
    theme = os.path.basename(os.path.dirname(os.path.abspath(pkg))) or "theme"
    target = f"forge-test/{theme}/"
    before = settings(env)
    vmctl(env, "ssh", f"mkdir -p {target}", check=True)
    vmctl(env, "push", os.path.abspath(pkg) + "/", target, check=True)
    log(f"[{env}] install.sh --apply {variant}")
    r = vmctl(env, "ssh", f"cd {target} && ./install.sh --apply {variant}")
    rep["install"] = {"rc": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-6:]}
    if r.returncode:
        rep["errors"].append(f"install.sh endete mit {r.returncode}")
    time.sleep(8)
    rep["applied_shot"] = vmctl(env, "shot", os.path.abspath(f"{out}/vm-{env}-applied.png")).stdout.strip()
    rep["applied"] = settings(env)
    if rep["applied"] == before:
        rep["errors"].append("--apply hat keine der beobachteten Einstellungen geändert")
    log(f"[{env}] uninstall.sh")
    r = vmctl(env, "ssh", f"cd {target} && ./uninstall.sh")
    rep["uninstall"] = {"rc": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-6:]}
    if r.returncode:
        rep["errors"].append(f"uninstall.sh endete mit {r.returncode}")
    time.sleep(8)
    rep["after_shot"] = vmctl(env, "shot", os.path.abspath(f"{out}/vm-{env}-after.png")).stdout.strip()
    after = settings(env)
    rep["not_restored"] = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if rep["not_restored"]:
        rep["errors"].append("nach uninstall.sh nicht wie vorher: " + ", ".join(rep["not_restored"]))
    return rep


def run(out, envs=("fedora", "ubuntu", "artix"), variant=None, reset=True, log=print):
    pkg = f"{out}/package"
    spec = json.load(open(f"{out}/spec.json"))
    variant = variant or spec["variants"][0]["id"]
    reports = []
    for env in envs:
        if env not in ENVS:
            raise ValueError(f"unbekannte VM {env} (vorhanden: {', '.join(ENVS)})")
        try:
            rep = run_one(env, pkg, variant, out, reset=reset, log=log)
        except Exception as e:  # noqa: BLE001 - eine kaputte VM soll die anderen nicht aufhalten
            rep = {"env": env, "variant": variant, "errors": [f"Lauf abgebrochen: {e}"]}
        for e in rep["errors"]:
            log(f"[{env}] FEHLER: {e}")
        if not rep["errors"]:
            log(f"[{env}] OK")
        reports.append(rep)
    with open(f"{out}/vmtest.json", "w") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    return reports
