"""Checking the painted cameos — what the image model made of the motif.

Two stages:
* without the LLM: a face in the picture although the motif names no person
  (OpenCV), and nearly identical pictures (difference hash). Empty or
  lettered pictures cannot be recognised reliably by pixel statistics
  (calibrated on 24.10.2026: an empty red field lay between good pictures
  with a calm background; tesseract missed made-up lettering and read "hee"
  in metal).
* with the LLM, if the server understands images (/props → modalities.vision):
  the model describes what is to be seen and reports lettering or an empty
  picture.

Returns {icon: [errors]} — the errors go to the LLM as a repair order.
"""
import base64
import io
import json
import os
import urllib.request

from PIL import Image

from . import artplan, iconset, llm

_cascade = None
LAST_VISION = None
SHOWS = {}          # icon → what the visual check saw last


def _faces(path):
    global _cascade
    try:
        import cv2
    except ImportError:
        return 0
    if _cascade is None:
        _cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    g = cv2.imread(path, 0)
    if g is None:
        return 0
    return len(_cascade.detectMultiScale(g, 1.1, 6, minSize=(g.shape[0] // 6, g.shape[0] // 6)))


def dhash(path, n=8):
    im = Image.open(path).convert("L").resize((n + 1, n), Image.LANCZOS)
    px = list(im.getdata())
    return sum(1 << i for i, (a, b) in enumerate((px[r * (n + 1) + c], px[r * (n + 1) + c + 1])
                                               for r in range(n) for c in range(n)) if a > b)


def vision_available():
    try:
        props = json.loads(urllib.request.urlopen(llm.BASE.rsplit("/v1", 1)[0] + "/props", timeout=5).read())
        return bool(props.get("modalities", {}).get("vision"))
    except Exception:  # noqa: BLE001
        return False


VISION_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["shows", "text", "person", "clear"],
    "properties": {"shows": {"type": "string", "maxLength": 160}, "text": {"type": "boolean"},
                   "person": {"type": "boolean"}, "clear": {"type": "boolean"}}}

# Asked without the intended motif: whoever knows it sees it even in an
# empty red field ("a large red switch, appearing off", test 24.10.2026).
VISION_Q = ("Describe this small painted picture.\n"
            "shows: what it shows, in at most 15 English words; say \"nothing clear\" if there is no "
            "recognisable object.\n"
            "text: true if any letters, words or numbers are visible (also fake or garbled lettering).\n"
            "person: true if a human, a face or hands are visible.\n"
            "clear: true if one main object is clearly recognisable at a glance.")

# Name the kind first, then judge — asked directly, the model took a plastic
# and a metal waste bin for different things.
MATCH_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["meant_kind", "result_kind", "matches"],
                "properties": {"meant_kind": {"type": "string", "maxLength": 40},
                               "result_kind": {"type": "string", "maxLength": 40},
                               "matches": {"type": "boolean"}}}
MATCH_Q = ("An icon was meant to show: {motif}\nAn observer describes the painted result as: {shows}\n"
           "meant_kind: the kind of main object that was meant, 1-3 words (e.g. \"waste bin\", \"push button\").\n"
           "result_kind: the kind of main object in the result, 1-3 words.\n"
           "matches: true if both are the same kind of thing — material, colour, angle and details do not matter.")


def _vision(path, motif):
    motif = artplan.strip_purpose(motif)
    buf = io.BytesIO()
    Image.open(path).convert("RGB").resize((384, 384)).save(buf, "PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    msg = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}},
                                        {"type": "text", "text": VISION_Q}]}]
    v = json.loads(llm.chat(msg, schema=VISION_SCHEMA, max_tokens=300, temperature=0.1)[0])
    m = llm.chat([{"role": "user", "content": MATCH_Q.format(motif=motif, shows=v["shows"])}],
                 schema=MATCH_SCHEMA, max_tokens=120, temperature=0.1)[0]
    m = json.loads(m)
    v["matches"], v["kinds"] = m["matches"], (m["meant_kind"], m["result_kind"])
    return v


def check(pictures, motifs, log=print, vision=None):
    """pictures {icon: path}, motifs {icon: {source, motif}} → {icon: [errors]}."""
    bad = {}
    for name, path in pictures.items():
        motif = motifs[name]["motif"]
        if not artplan.wants_person(motif) and _faces(path):
            bad.setdefault(name, []).append(
                "the painted picture shows a person/a face although the motif names none — the image model "
                "adds a human to this object; choose an object, a vehicle or a building "
                "that stands on its own (no tables, desks or seats where one would put somebody)")
    hashes = {n: dhash(p) for n, p in pictures.items()}
    names = list(pictures)
    for i, a in enumerate(names):
        for b in names[:i]:
            same_family = iconset.FAMILY[a] == iconset.FAMILY[b] != "object"   # folders/sheets are meant to look alike
            if bin(hashes[a] ^ hashes[b]).count("1") <= 6 and not same_family:
                bad.setdefault(a, []).append(f"the painted picture looks almost exactly like \"{b}\" — choose a "
                                             "clearly different motif")
                break
    if vision is None:
        # First the graphics card back to the LLM: after painting it is stopped,
        # and /props would then say "no vision" (run of 24.10.2026: the visual check was skipped).
        from . import gpu
        try:
            gpu.need("llm", log)
        except RuntimeError as e:
            log(f"  visual check not possible: {e}")
        vision = vision_available()
    global LAST_VISION
    LAST_VISION = vision
    if not vision:
        log("  visual check: the LLM does not understand images — only faces and duplicates checked")
    if vision:
        for name, path in pictures.items():
            try:
                v = _vision(path, motifs[name]["motif"])
                SHOWS[name] = v["shows"]
            except llm.LLMError as e:
                log(f"  visual check {name}: {e}")
                continue
            errs = []
            if not v["clear"]:
                errs.append(f"the painted picture shows nothing clear (seen: {v['shows']}) — choose an object "
                            "with a clear, distinctive shape")
            if v["text"]:
                errs.append(f"the painted picture has lettering (seen: {v['shows']}) — choose an object that "
                            "never carries lettering (no books, signs, machines, packaging, maps)")
            if v["person"] and not artplan.wants_person(motifs[name]["motif"]) and name not in bad:
                errs.append(f"the painted picture shows a human (seen: {v['shows']}) although the motif "
                            "names none — choose an object that stands on its own")
            if not v["matches"] and v["clear"]:
                errs.append(f"the painted picture shows something else (seen: {v['shows']}) — choose a motif "
                            "an image model can paint unambiguously, and describe its look more precisely")
            if errs:
                bad.setdefault(name, []).extend(errs)
    return bad
