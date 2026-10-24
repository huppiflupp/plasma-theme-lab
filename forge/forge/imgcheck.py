"""Prüfung der gemalten Cameos — was das Bildmodell aus dem Motiv gemacht hat.

Zwei Stufen:
* ohne LLM: Gesicht im Bild, obwohl das Motiv keine Person nennt (OpenCV),
  und fast gleiche Bilder (Differenz-Hash). Leere oder beschriftete Bilder
  lassen sich mit Pixelstatistik nicht verlässlich erkennen (kalibriert am
  24.10.2026: ein leeres rotes Feld lag zwischen guten Bildern mit ruhigem
  Hintergrund; tesseract übersah Fantasieschrift und las „hee“ in Metall).
* mit LLM, wenn der Server Bilder versteht (/props → modalities.vision):
  das Modell beschreibt, was zu sehen ist, und meldet Schrift oder ein
  leeres Bild.

Liefert {icon: [Fehler]} — die Fehler gehen als Reparaturauftrag ans LLM.
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
SHOWS = {}          # icon → was die Sichtprüfung zuletzt gesehen hat


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

# Ohne das gewünschte Motiv gefragt: wer es kennt, sieht es auch in einem
# leeren roten Feld („a large red switch, appearing off“, Test 24.10.2026).
VISION_Q = ("Describe this small painted picture.\n"
            "shows: what it shows, in at most 15 English words; say \"nothing clear\" if there is no "
            "recognisable object.\n"
            "text: true if any letters, words or numbers are visible (also fake or garbled lettering).\n"
            "person: true if a human, a face or hands are visible.\n"
            "clear: true if one main object is clearly recognisable at a glance.")

# Erst die Art benennen, dann urteilen — direkt gefragt, hielt das Modell einen
# Plastik- und einen Metall-Mülleimer für verschiedene Dinge.
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
    """pictures {icon: Pfad}, motifs {icon: {source, motif}} → {icon: [Fehler]}."""
    bad = {}
    for name, path in pictures.items():
        motif = motifs[name]["motif"]
        if not artplan.wants_person(motif) and _faces(path):
            bad.setdefault(name, []).append(
                "das gemalte Bild zeigt eine Person/ein Gesicht, obwohl das Motiv keine nennt — das Bildmodell "
                "ergänzt bei diesem Gegenstand einen Menschen; wähle einen Gegenstand, ein Fahrzeug oder Gebäude, "
                "das allein für sich steht (keine Tische, Pulte oder Plätze, an die man jemanden setzen würde)")
    hashes = {n: dhash(p) for n, p in pictures.items()}
    names = list(pictures)
    for i, a in enumerate(names):
        for b in names[:i]:
            same_family = iconset.FAMILY[a] == iconset.FAMILY[b] != "object"   # Ordner/Blatt gleichen sich gewollt
            if bin(hashes[a] ^ hashes[b]).count("1") <= 6 and not same_family:
                bad.setdefault(a, []).append(f"das gemalte Bild sieht fast genauso aus wie „{b}“ — wähle ein "
                                             "deutlich anderes Motiv")
                break
    if vision is None:
        # Erst die Grafikkarte zurück ans LLM: nach dem Malen ist es angehalten,
        # und /props wäre dann „kein Bildverständnis“ (Lauf 24.10.2026: Sichtprüfung fiel aus).
        from . import gpu
        try:
            gpu.need("llm", log)
        except RuntimeError as e:
            log(f"  Sichtprüfung nicht möglich: {e}")
        vision = vision_available()
    global LAST_VISION
    LAST_VISION = vision
    if not vision:
        log("  Sichtprüfung: LLM versteht keine Bilder — nur Gesichter und Doppelte geprüft")
    if vision:
        for name, path in pictures.items():
            try:
                v = _vision(path, motifs[name]["motif"])
                SHOWS[name] = v["shows"]
            except llm.LLMError as e:
                log(f"  Sichtprüfung {name}: {e}")
                continue
            errs = []
            if not v["clear"]:
                errs.append(f"das gemalte Bild zeigt nichts Klares (zu sehen: {v['shows']}) — wähle einen Gegenstand "
                            "mit klarer, markanter Form")
            if v["text"]:
                errs.append(f"im gemalten Bild steht Schrift (zu sehen: {v['shows']}) — wähle einen Gegenstand, der "
                            "nie beschriftet ist (keine Bücher, Schilder, Automaten, Verpackungen, Karten)")
            if v["person"] and not artplan.wants_person(motifs[name]["motif"]) and name not in bad:
                errs.append(f"das gemalte Bild zeigt einen Menschen (zu sehen: {v['shows']}), obwohl das Motiv "
                            "keinen nennt — wähle einen Gegenstand, der allein für sich steht")
            if not v["matches"] and v["clear"]:
                errs.append(f"das gemalte Bild zeigt etwas anderes (zu sehen: {v['shows']}) — wähle ein Motiv, "
                            "das ein Bildmodell eindeutig malen kann, und beschreibe sein Aussehen genauer")
            if errs:
                bad.setdefault(name, []).extend(errs)
    return bad
