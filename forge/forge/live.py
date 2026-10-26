"""The live run: the theme grows in a lab VM, stage by stage, for a recording.

`forge.py all "<style>" -o out/x --live-vm fedora` (or ubuntu, artix): the VM
is reverted to its snapshot `clean` (unless --no-reset), switched to an English
session, and after each build stage (build.STAGES) the package so far is
copied in and just that part is applied, so the screen shows the theme grow:

    colors        the colour scheme            plasma-apply-colorscheme
    plasma-style  panels and popups            plasma-apply-desktoptheme
    decoration    window frames                kwinrc + KWin reconfigure
    wallpapers    the first wallpaper          plasma-apply-wallpaperimage
    icons         the icon theme               kdeglobals [Icons] + iconChanged
    splash-boot   the whole global theme       install.sh --apply, then the splash shown

A screenshot after each stage goes to <out>/live-<n>-<stage>.png, and each step
into the event log (<out>/events.jsonl) for an overlay. While ComfyUI paints
the icons, <out>/assets/progress.png shows the latest ones (forge/icons.py).
"""
import os
import time

from . import events, vmtest


class Live:
    def __init__(self, env, out, reset=True, lang="en", variant=None, log=print):
        self.env, self.out, self.log = env, os.path.abspath(out), log
        self.variant = variant
        self.n = 0
        self.target = None
        events.begin("live-vm", vm=env, lang=lang)
        ready = vmtest.revert(env, lang, log) if reset else False
        if not reset:
            vmtest.vmctl(env, "start", check=True)
        if not ready:
            vmtest.set_language(env, lang, log)
        # A window on screen, so colours, frame and icons can be seen to change
        # (without one only the wallpaper did, test 26.10.2026).
        time.sleep(8)
        self._ssh('(setsid -f dolphin --new-window "$HOME" >/dev/null 2>&1 </dev/null); sleep 5')
        events.end("live-vm")

    def _ssh(self, cmd):
        r = vmtest.vmctl(self.env, "ssh", cmd)
        if r.returncode:
            self.log(f"[{self.env}] {cmd[:60]}…: {(r.stderr or r.stdout).strip()[-200:]}")
        return r

    def __call__(self, stage, pkg, variants):
        var = next((v for v in variants if v.v["id"] == self.variant), variants[0])
        theme = os.path.basename(self.out.rstrip("/")) or "theme"
        self.target = f"forge-live/{theme}/"
        t0 = time.time()
        self._ssh(f"mkdir -p {self.target}")
        vmtest.vmctl(self.env, "push", os.path.abspath(pkg) + "/", self.target, check=True)
        self._ssh(f"cd {self.target} && ./install.sh >/dev/null")      # copy only
        cmd = {
            "colors": f"plasma-apply-colorscheme {var.camel}",
            "plasma-style": f"plasma-apply-desktoptheme {var.id}",
            "decoration": ("kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library "
                           "org.kde.kwin.aurorae && kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 "
                           f"--key theme __aurorae__svg__{var.camel} && dbus-send --session --type=method_call "
                           "--dest=org.kde.KWin /KWin org.kde.KWin.reconfigure"),
            "wallpapers": f"plasma-apply-wallpaperimage \"$HOME/.local/share/wallpapers/{var.id}\"",
            "icons": (f"kwriteconfig6 --file kdeglobals --group Icons --key Theme {var.camel}Icons && "
                      "dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0"),
            # The whole global theme, then its splash for a few seconds (ksplashqml --test).
            "splash-boot": (f"cd {self.target} && ./install.sh --apply {var.v['id']} >/dev/null; "
                            f"(timeout 8 ksplashqml {var.lnf} --test >/dev/null 2>&1 &) ; sleep 3"),
        }[stage]
        self._ssh(cmd)
        time.sleep(4)                     # let Plasma redraw before the screenshot
        self.n += 1
        shot = f"{self.out}/live-{self.n}-{stage}.png"
        vmtest.vmctl(self.env, "shot", shot)
        events.emit("live-vm", "applied", build_stage=stage, variant=var.v["id"], command=cmd,
                    screenshot=os.path.basename(shot), seconds=round(time.time() - t0, 1))
        self.log(f"[{self.env}] live: {stage} applied ({shot})")
