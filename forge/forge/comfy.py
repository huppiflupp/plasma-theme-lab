"""ComfyUI-Client.

Standard ist das lokale ComfyUI auf 245k (RTX 5080, 127.0.0.1:8189) mit
Z-Image Turbo. Mit FORGE_COMFY=http://192.168.178.54:8188 geht es an ai395
(Krea-2 Turbo, Basic Auth; Zugang aus ~/.config/comfyui/claude-zugang oder
Umgebung). FORGE_IMAGE_MODEL=zimage|krea2 überschreibt die Wahl.
Die API blockiert, solange ein großes Modell lädt — Timeouts beim
Pollen sind normal und brechen den Lauf nicht ab.
"""
import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("FORGE_COMFY", "http://127.0.0.1:8189")
LOCAL = urllib.parse.urlparse(BASE).hostname in ("127.0.0.1", "localhost")
MODEL = os.environ.get("FORGE_IMAGE_MODEL", "zimage" if LOCAL else "krea2")


def _credentials():
    user, pw = os.environ.get("COMFYUI_USER"), os.environ.get("COMFYUI_PASS")
    path = os.path.expanduser("~/.config/comfyui/claude-zugang")
    if not (user and pw) and os.path.exists(path):
        vals = dict(re.findall(r'^\s*(?:export\s+)?(\w+)=["\']?([^"\'\n]*)', open(path).read(), re.M))
        user, pw = vals.get("COMFYUI_USER"), vals.get("COMFYUI_PASS")
    return user, pw


def _req(path, payload=None, timeout=60):
    headers = {"Content-Type": "application/json"}
    user, pw = (None, None) if LOCAL else _credentials()
    if user:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
    data = json.dumps(payload).encode() if payload is not None else None
    return urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers),
                                  timeout=timeout).read()


def krea2(prompt, width, height, seed, prefix, steps=8):
    """Krea-2 Turbo: fotorealistisch/gemalt, kein Text, kein negatives Prompt."""
    return {
        "10": {"class_type": "UNETLoader",
               "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader",
               "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": steps, "cfg": 1, "sampler_name": "euler",
                         "scheduler": "simple", "denoise": 1, "model": ["10", 0],
                         "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }


def zimage(prompt, width, height, seed, prefix, steps=8):
    """Z-Image Turbo (lokal, 16 GB): wie Krea-2 ohne negatives Prompt, cfg 1."""
    return {
        "10": {"class_type": "UNETLoader",
               "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "14": {"class_type": "ModelSamplingAuraFlow", "inputs": {"shift": 3, "model": ["10", 0]}},
        "11": {"class_type": "CLIPLoader",
               "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": steps, "cfg": 1, "sampler_name": "res_multistep",
                         "scheduler": "simple", "denoise": 1, "model": ["14", 0],
                         "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }


def generate(prompt, width, height, seed, dst, timeout=1800, log=print):
    """Erzeugt ein Bild und schreibt es nach `dst` (PNG). Kantenlängen auf 16 runden."""
    from . import gpu
    gpu.need("images", log)
    width, height = width // 16 * 16, height // 16 * 16
    prefix = "forge_" + re.sub(r"\W+", "_", os.path.splitext(os.path.basename(dst))[0])
    wf = (zimage if MODEL == "zimage" else krea2)(prompt, width, height, seed, prefix)
    pid = None
    t0 = time.time()
    while pid is None:
        try:
            pid = json.loads(_req("/prompt", {"prompt": wf}, timeout=300))["prompt_id"]
        except Exception as e:  # noqa: BLE001 - Kaltstart per Socket-Aktivierung
            if time.time() - t0 > 300:
                raise RuntimeError(f"ComfyUI nimmt keinen Auftrag an: {e}") from e
            time.sleep(10)
    while time.time() - t0 < timeout:
        try:
            h = json.loads(_req(f"/history/{pid}", timeout=30))
        except Exception:  # noqa: BLE001 - Server lädt noch
            time.sleep(10)
            continue
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") == "error":
                raise RuntimeError(json.dumps(st.get("messages"))[:1500])
            for out in h[pid]["outputs"].values():
                for im in out.get("images", []):
                    data = _req("/view?" + urllib.parse.urlencode(im), timeout=120)
                    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                    with open(dst, "wb") as f:
                        f.write(data)
                    log(f"  Bild {os.path.basename(dst)} {width}x{height} in {time.time() - t0:.0f} s")
                    return dst
            raise RuntimeError("Auftrag fertig, aber ohne Bild")
        time.sleep(3)
    raise TimeoutError("ComfyUI: Zeitüberschreitung")
