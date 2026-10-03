#!/usr/bin/env python3
"""Krea-2 turbo jobs on ai395 -> local PNGs. jobs.json: [{name,prompt,seed,w,h,upscale}]"""
import json, os, sys, time, random, requests
from pathlib import Path
env = dict(l.strip().replace("export ", "").split("=", 1) for l in open(os.path.expanduser("~/.config/comfyui/claude-zugang")) if "=" in l)
AUTH = (env["COMFYUI_USER"].strip('"\''), env["COMFYUI_PASS"].strip('"\''))
B = "http://192.168.178.54:8188"
out = Path(sys.argv[2] if len(sys.argv) > 2 else "out"); out.mkdir(exist_ok=True)

def graph(j):
    g = {
      "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
      "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
      "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"text": j["prompt"], "clip": ["11", 0]}},
      "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
      "5": {"class_type": "EmptyLatentImage", "inputs": {"width": j.get("w", 1920), "height": j.get("h", 1088), "batch_size": 1}},
      "3": {"class_type": "KSampler", "inputs": {"seed": j["seed"], "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1,
             "model": ["10", 0], "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
      "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
    }
    if j.get("upscale_only"):
        return {"20": {"class_type": "LoadImage", "inputs": {"image": j["init"]}},
                "40": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
                "41": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["40", 0], "image": ["20", 0]}},
                "29": {"class_type": "SaveImage", "inputs": {"filename_prefix": "cdewp_" + j["name"], "images": ["41", 0]}}}
    if j.get("init"):  # img2img from uploaded image
        g["20"] = {"class_type": "LoadImage", "inputs": {"image": j["init"]}}
        g["21"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["20", 0], "vae": ["12", 0]}}
        g["3"]["inputs"]["latent_image"] = ["21", 0]; g["3"]["inputs"]["denoise"] = j["denoise"]
        del g["5"]
    img = ["8", 0]
    if j.get("upscale"):
        g["40"] = {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}}
        g["41"] = {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["40", 0], "image": img}}
        img = ["41", 0]
    g["29"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "cdewp_" + j["name"], "images": img}}
    return g

for j in json.load(open(sys.argv[1])):
    dst = out / f"{j['name']}.png"
    if dst.exists(): continue
    if j.get("init_file"):
        r = requests.post(f"{B}/upload/image", auth=AUTH, files={"image": (j["name"] + "_in.png", open(j["init_file"], "rb"))}, data={"overwrite": "true"})
        j["init"] = r.json()["name"]
    t = time.time()

    def submit():
        r = requests.post(f"{B}/prompt", auth=AUTH, json={"prompt": graph(j), "front": bool(j.get("front"))}, timeout=600).json()
        if "prompt_id" not in r: raise RuntimeError(f"{j['name']}: {r}")
        return r["prompt_id"]

    pid, lost = submit(), 0
    while True:
        time.sleep(5)
        try:
            h = requests.get(f"{B}/history/{pid}", auth=AUTH, timeout=30).json()
            if pid in h: break
            q = requests.get(f"{B}/queue", auth=AUTH, timeout=30).json()
        except Exception:
            time.sleep(10); continue  # server busy loading or restarting
        queued = any(item[1] == pid for item in q["queue_running"] + q["queue_pending"])
        lost = 0 if queued else lost + 1
        if lost >= 3:  # neither queued nor in history: server restarted, job lost
            print(f"{j['name']}: Job verloren, neu eingereicht", flush=True)
            pid, lost = submit(), 0
    h = h[pid]
    if h["status"]["status_str"] == "error": print(j["name"], "FEHLER", h["status"]["messages"][-1]); continue
    for o in h["outputs"].values():
        for im in o.get("images", []):
            dst.write_bytes(requests.get(f"{B}/view", auth=AUTH, params={**im, "type": "output"}).content)
    print(f"{j['name']}: {time.time()-t:.0f}s", flush=True)
