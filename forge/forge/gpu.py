"""One graphics card, two users: the LLM and the image model take turns.

On 245k (RTX 5080, 16 GB) the llama-server takes ~14 GB; Z-Image needs the
card to itself. need("images") therefore stops the LLM service and starts a
local ComfyUI, need("llm") does the reverse. It switches only when needed —
the course design → paint → check → repair → paint so costs few switches of
~20 s each. At the end of the program restore() brings back the starting
state (the LLM service running, our own ComfyUI ended).

Active only when ComfyUI is local (comfy.LOCAL). Somebody else's ComfyUI on
the same port is shared, but never ended.

Environment: FORGE_LLM_SERVICE (systemd user service, default llama-qwen36.service,
empty = do not manage), FORGE_COMFY_DIR (default /data/ComfyUI).
"""
import atexit
import os
import signal
import subprocess
import time
import urllib.request

from . import comfy

SERVICE = os.environ.get("FORGE_LLM_SERVICE", "llama-qwen36.service")
COMFY_DIR = os.environ.get("FORGE_COMFY_DIR", "/data/ComfyUI")
UNIT = "comfy-forge"            # a systemd scope of its own, so that only ours is ended

_state = {"mode": None, "stopped_llm": False, "started_comfy": False}


def _up(url, timeout=2):
    try:
        urllib.request.urlopen(url, timeout=timeout).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def _llm_url():
    from . import llm
    return llm.BASE.rsplit("/v1", 1)[0] + "/health"


def _systemctl(*args):
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True)


def _wait(url, seconds, what):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if _up(url):
            return
        time.sleep(2)
    raise RuntimeError(f"{what} not ready after {seconds} s")


def managed():
    return comfy.LOCAL and bool(SERVICE)


def need(mode, log=print):
    """mode = "llm" or "images"; makes sure that service runs."""
    if not managed() or _state["mode"] == mode:
        return
    if mode == "images":
        if not _up(comfy.BASE + "/system_stats"):
            if _systemctl("is-active", SERVICE).stdout.strip() == "active":
                log(f"GPU: stopping {SERVICE}, starting a local ComfyUI")
                _systemctl("stop", SERVICE)
                _state["stopped_llm"] = True
            _start_comfy()
            _wait(comfy.BASE + "/system_stats", 120, "ComfyUI")
    else:
        if not _up(_llm_url()):
            if _state["started_comfy"]:
                log("GPU: ending ComfyUI, starting the LLM service")
                _stop_comfy()
            _systemctl("start", SERVICE)
            _wait(_llm_url(), 300, SERVICE)
            _state["stopped_llm"] = False
    _state["mode"] = mode


def _start_comfy():
    port = comfy.BASE.rsplit(":", 1)[-1].strip("/")
    cmd = ["systemd-run", "--user", "--scope", f"--unit={UNIT}", "-p", "MemoryHigh=16G", "-p", "MemoryMax=20G",
           "-p", "MemorySwapMax=2G", "venv/bin/python", "main.py", "--listen", "127.0.0.1", "--port", port,
           "--disable-auto-launch", "--disable-pinned-memory", "--fast-disk"]
    cache = os.path.expanduser("~/.cache/theme-forge")
    os.makedirs(cache, exist_ok=True)
    logf = open(f"{cache}/comfy.log", "ab")
    subprocess.Popen(cmd, cwd=COMFY_DIR, stdout=logf, stderr=logf, stdin=subprocess.DEVNULL,
                     start_new_session=True)
    _state["started_comfy"] = True


def _stop_comfy():
    _systemctl("stop", f"{UNIT}.scope")
    for _ in range(30):
        if not _up(comfy.BASE + "/system_stats", 1):
            break
        time.sleep(1)
    _state["started_comfy"] = False


def restore(log=print):
    """The starting state: our own ComfyUI off, the LLM service on (if we stopped it)."""
    if _state["started_comfy"]:
        _stop_comfy()
    if _state["stopped_llm"]:
        log(f"GPU: starting {SERVICE} again")
        _systemctl("start", SERVICE)
        _state["stopped_llm"] = False
    _state["mode"] = None


def _term(*_):
    raise SystemExit(143)


atexit.register(restore)
# SIGTERM (kill, systemd) is to clean up as well, not only Ctrl+C.
signal.signal(signal.SIGTERM, _term)
