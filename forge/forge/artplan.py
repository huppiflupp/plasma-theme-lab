"""Bildplan: was gemalt wird — Hintergründe, Material, Cameo-Motive der Icons.

Ein eigener LLM-Schritt nach der Spezifikation, in kleinen Anfragen (je
Variante Szenen + Material, einmal alle Icon-Motive), jede mit eigenem
Schema und eigener Prüfung. Die Bild-Prompts selbst setzt der Motor aus den
Motiven zusammen (feste Stilformel), damit die Icons ein einheitlicher Satz
werden.

Privatmodus (--private): Namen von Einheiten, Figuren und Orten der
Vorlage sind erlaubt. Das Bildmodell kennt viele davon aber nicht (Test
24.10.2026: „Kirov airship“ ergab ein graues Stahlschiff statt des roten
Zeppelins) — deshalb verlangt der Plan Name UND Aussehen.
"""
import json
import re

from . import iconset, llm, spec as specmod

TRAPS = {"icon", "icons", "text", "letters", "letter", "words", "logo", "logos", "label", "labels",
         "caption", "sign", "signs", "poster", "screen", "screens", "desktop", "interface", "ui",
         "monitor", "display", "document", "file", "files", "page", "pages", "symbol", "writing"}

SCENES_SYSTEM = """Du planst die Bildwelt eines Desktop-Themes. Ein Bildmodell (Krea) malt danach
deine Prompts. Es malt jedes Wort wörtlich und kennt viele Namen aus Spielen und
Filmen NICHT sicher."""

SCENES_USER = """Stilvorlage: {request}
Design-Brief:
{brief}

Variante: {vname} ({mode}), Leitfarbe {lead}, Grundton {surface}.
{names_rule}

Liefere:
0. elements: zuerst 4–8 ikonische Elemente GENAU DIESER Variante/Fraktion in der Vorlage
   (Einheiten, Figuren, Gebäude, Schauplätze — keine der Gegenseite). name: wie in der
   Vorlage; look: ENGLISCH, wie es aussieht (Form, Farben, Merkmale), 8–30 Wörter.
   Farben wie in der Vorlage — in Strategiespielen tragen Einheiten und Gebäude die
   Fraktions-/Teamfarbe; hier ist das die Leitfarbe {lead}, nicht pauschal Tarngrün.
{voted}
1. wallpapers: genau drei Hintergrundbilder für diese Variante; jedes zeigt mindestens
   ein Element aus elements als Hauptmotiv, in einer eigenen, ikonischen Szene.
   prompt: englisch, 50–130 Wörter, ein durchgehender Absatz, NUR die Szene — Medium
   und Stil setzt der Motor selbst davor, nenne sie nicht. Für jede Einheit oder Figur
   ihr AUSSEHEN beschreiben (Form, Farben, Merkmale), nicht nur den Namen. Licht,
   Farbwelt passend zur Leitfarbe, eine ruhige Bildzone (Himmel, Nebel, Boden).
   Nie: Symbole, Bildschirme, Schilder, Schrift, Rahmen. Ende: „no text, no logos“.
   title: kurzer deutscher Bildtitel.
2. texture: englischer Prompt für eine Metalloberfläche als Material für Fensterrahmen
   und Leisten: Draufsicht auf ein flaches Blech im Grundton/der Leitfarbe dieser
   Variante, waagrechte Schleifspuren, leichte Gebrauchsspuren, gleichmäßiges Licht,
   ohne Nieten, Nähte, Objekte und Schrift. Farbe: vor allem die Leitfarbe, dunkel."""

ICONS_SYSTEM = """Du entwirfst einen Satz Programmsymbole im Stil der „Cameos“ eines
Strategiespiels: jedes Symbol ist ein kleines gemaltes Bild eines Motivs aus der
Bildwelt der Vorlage, das trotzdem die Funktion verrät."""

ICONS_USER = """Stilvorlage: {request}
Design-Brief (Auszug):
{brief}
{names_rule}

Ikonische Elemente der Vorlage (Auswahl, du darfst weitere nehmen):
{elements}

Schreibe für jedes Symbol zuerst source — den NAMEN eines Elements der Vorlage (eine
Einheit, ein Gebäude, eine Figur, ein Gegenstand der Bildwelt; nicht die Funktion des
Symbols) —, dann
motif: englisch, 6–25 Wörter, ein Gegenstand, eine
Einheit, eine Figur oder ein Gebäude aus der Vorlage, groß und klar im Bild, dessen
Zusammenhang mit der Funktion man sofort sieht (Terminal → Funker an einer
Konsole, Papierkorb → Schrotthaufen …). Regeln:
- Alle Ordner (folder, folder-*, user-home, user-desktop) zeigen DENSELBEN Behälter
  wie „folder“; die Varianten fügen nur ein deutliches Merkmal hinzu.
- Jedes Motiv anders; keine Schrift, keine Buchstaben, keine Bildschirme, keine Dokumente.
- Dateitypen und abstrakte Funktionen als greifbarer Gegenstand der Bildwelt: z. B. eine
  versiegelte Akte, eine Filmrolle in einer Munitionskiste, ein Feldtelefon, ein Hebel,
  eine Funkantenne, ein Tresor — nie „Datei“, „Symbol“, „Icon“ oder ein Bildschirm.
- Für Einheiten/Figuren mit Namen auch das Aussehen nennen.

Symbole:
{icons}"""


def _names_rule(private):
    if private:
        return ("Namen von Einheiten, Figuren und Orten der Vorlage sind erlaubt (privates Theme) — "
                "nenne sie, und beschreibe zusätzlich, wie sie aussehen.")
    return ("Keine Namen von Marken, Einheiten oder Figuren der Vorlage — beschreibe sie nur "
            "mit eigenen Worten nach ihrem Aussehen.")


def _words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def _banned(spec, private):
    if private:
        return []
    request = spec.get("_meta", {}).get("request", "")
    return specmod.TRADEMARKS + specmod.names_from_request(request)


def _mark_errors(field, text, banned):
    low = text.lower()
    return [f"{field} enthält den geschützten Namen „{t}“" for t in banned
            if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low)]


SCENE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["elements", "wallpapers", "texture"],
    "properties": {
        "elements": {"type": "array", "minItems": 4, "maxItems": 8, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "look"],
            "properties": {"name": {"type": "string", "minLength": 2, "maxLength": 40},
                           "look": {"type": "string", "minLength": 30, "maxLength": 260}}}},
        "wallpapers": {"type": "array", "minItems": 3, "maxItems": 3, "items": {
            "type": "object", "additionalProperties": False, "required": ["title", "prompt"],
            "properties": {"title": {"type": "string", "minLength": 3, "maxLength": 40},
                           "prompt": {"type": "string", "minLength": 250, "maxLength": 1400}}}},
        "texture": {"type": "string", "minLength": 80, "maxLength": 600},
    },
}


def _body(p):
    """Prompt ohne die Schlussformel „no text, no logos“."""
    return re.split(r"(?i)no text", p)[0]


def _traps(text):
    """Fallenwörter, ohne harmlose Wendungen („signs of wear“, „no text“)."""
    low = re.sub(r"\bsigns? of\b", "", text.lower())
    low = re.sub(r"\b(no|without)\s+\w+", "", low)
    return sorted(_words(low) & TRAPS)


def check_scenes(obj, banned, private=False, voted=(), others=()):
    errors = []
    names = [e["name"] for e in obj["elements"]]
    for e in obj["elements"]:
        if _words(e["look"]) & GERMAN or re.search(r"[äöüß]", e["look"].lower()):
            errors.append(f"elements „{e['name']}“: look ist deutsch — schreibe es englisch")
    if voted:
        missing = [n for n in voted[:4] if not any(_name_in(n, e) for e in names)]
        if missing:
            errors.append(f"elements: es fehlen abgestimmte Elemente {', '.join(missing)} — nimm sie auf")
    for i, w in enumerate(obj["wallpapers"]):
        for o in others:
            if re.search(r"\b" + re.escape(o.lower()), w["prompt"].lower()):
                errors.append(f"wallpapers[{i}].prompt nennt „{o}“ — das ist die andere Variante; "
                              "zeige nur Elemente dieser Variante")
    for i, w in enumerate(obj["wallpapers"]):
        p = w["prompt"]
        traps = _traps(_body(p))
        if private and not any(_name_in(n, p) for n in names):
            errors.append(f"wallpapers[{i}].prompt zeigt keines der elements ({', '.join(names)}) — "
                          "nimm eines davon als Hauptmotiv und beschreibe sein Aussehen")
        if traps:
            sents = [s for s in specmod._sentences(_body(p)) if _traps(s)]
            errors.append(f"wallpapers[{i}].prompt enthält {', '.join(traps)} — das Bildmodell malt das "
                          f"wörtlich. Schreibe diese Sätze ohne diese Wörter: " + " / ".join(f"„{s}“" for s in sents))
        if "no text" not in p.lower():
            errors.append(f"wallpapers[{i}].prompt muss mit „no text, no logos“ enden")
        if len(p.split()) < 40:
            errors.append(f"wallpapers[{i}].prompt ist zu kurz ({len(p.split())} Wörter, mindestens 50)")
        errors += _mark_errors(f"wallpapers[{i}]", p + " " + w["title"], banned)
    t = obj["texture"].lower()
    for w in sorted(_words(t) & {"rivet", "rivets", "text", "logo", "logos", "letters", "seam", "seams"}):
        if not re.search(r"\b(no|without)\b[^.]*\b" + w, t):
            errors.append(f"texture nennt „{w}“ — die Fläche muss leer sein (oder „no {w}“ schreiben)")
    return errors


def _name_in(name, text):
    """Element-Name im Text? Ein markantes Wort genügt („Kirov“ für „Kirov Airship“)."""
    low = text.lower()
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) > 3]
    return name.lower() in low or any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words)


# Ersatzwörter für Fallen — als Vorschlag in der Fehlermeldung und als letzte
# Stufe ohne LLM. Gegenständlich, ohne Schrift.
REPLACE = {"text": "markings", "letters": "markings", "letter": "dispatch", "words": "markings",
           "writing": "markings", "screen": "radar scope", "screens": "radar scopes",
           "monitor": "radar scope", "display": "gauge", "document": "dossier", "file": "dossier",
           "files": "dossiers", "page": "sheet", "pages": "sheets", "icon": "emblem", "icons": "emblems",
           "logo": "emblem", "logos": "emblems", "symbol": "emblem", "label": "tag", "labels": "tags",
           "sign": "metal plate", "signs": "metal plates", "poster": "placard", "caption": "marking",
           "desktop": "tabletop", "interface": "control panel", "ui": "control panel", "screen-": "scope"}


def replace_traps(text):
    def sub(m):
        w = m.group(0)
        r = REPLACE.get(w.lower())
        return r if r else w
    return re.sub(r"[A-Za-z]+", lambda m: sub(m) if m.group(0).lower() in TRAPS and not
                  re.search(r"(?i)\b(no|without)\s+$", text[:m.start()]) else m.group(0), text)


GERMAN = {"der", "die", "das", "ein", "eine", "einen", "mit", "und", "auf", "im", "zum", "des", "dem"}
GENERIC = {"symbol", "icon", "stilisiert", "stylized", "generic", "abstract", "abstrakt", "file", "document"}


def icon_schema():
    item = {"type": "object", "additionalProperties": False, "required": ["source", "motif"],
            "properties": {"source": {"type": "string", "minLength": 3, "maxLength": 60},
                           "motif": {"type": "string", "minLength": 20, "maxLength": 220}}}
    return {"type": "object", "additionalProperties": False, "required": ["motifs"],
            "properties": {"motifs": {
                "type": "object", "additionalProperties": False, "required": iconset.PAINTED,
                "properties": {k: item for k in iconset.PAINTED}}}}


def check_icon(name, entry, banned):
    errors = []
    motif = entry["motif"]
    if _words(motif) & GERMAN or re.search(r"[äöüß]", motif.lower()):
        errors.append(f"{name}: motif ist deutsch — schreibe es englisch")
    if _words(entry["source"]) & GENERIC:
        errors.append(f"{name}: source „{entry['source']}“ ist kein Element der Vorlage — nimm eine "
                      "Einheit, ein Gebäude, eine Figur oder einen Gegenstand aus der Vorlage")
    if re.search(r"(?<![A-Za-z])[\"„“'][^\"„“”']{2,}[\"“”'](?![A-Za-z])", motif):
        errors.append(f"{name}: motif enthält ein Zitat — das wird als Schrift gemalt; ohne Anführungszeichen")
    traps = _traps(motif)
    if traps:
        alt = ", ".join(f"„{t}“ → „{REPLACE.get(t, '?')}“" for t in traps)
        errors.append(f"{name}: motif enthält {', '.join(traps)} — das Bildmodell malt das wörtlich; "
                      f"ersetze: {alt}")
    errors += _mark_errors(f"{name}", motif, banned)
    return errors


def check_icons(obj, banned):
    """{icon: [Fehler]} — leer, wenn alles passt."""
    out = {}
    seen = {}
    for name, entry in obj.items():
        errs = check_icon(name, entry, banned)
        key = entry["motif"].lower().strip(" .")
        if key in seen:
            errs.append(f"{name}: motif ist identisch mit {seen[key]} — jedes Motiv anders")
        seen.setdefault(key, name)
        if errs:
            out[name] = errs
    return out


ICON_FIX = """Stilvorlage: {request}
{names_rule}
Symbol „{name}“ ({meaning}). Bisher: {entry}
Fehler:
- {errors}
Gib source und motif neu zurück (motif englisch, 6–25 Wörter, ein greifbarer Gegenstand,
eine Einheit, ein Gebäude oder eine Figur aus der Vorlage, der die Funktion verrät)."""


def _ask(system, user, schema, check, log, what, rounds=4, seed=None):
    """Anfrage mit Prüfung; Fehler gehen mit der bisherigen Antwort zurück."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text, info = llm.chat(msgs, schema=schema, max_tokens=8000, temperature=0.6, seed=seed)
    log(f"{what}: {info['tokens']} Token in {info['seconds']} s")
    obj = json.loads(text)
    for r in range(rounds):
        errs = check(obj)
        if not errs:
            return obj, r + 1
        for e in errs:
            log(f"  Fehler: {e}")
        text, info = llm.chat(msgs + [{"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)},
                                      {"role": "user", "content": "Korrigiere genau diese Fehler und gib "
                                       "alles vollständig zurück:\n- " + "\n- ".join(errs)}],
                              schema=schema, max_tokens=8000, temperature=0.3, seed=seed)
        obj = json.loads(text)
    errs = check(obj)
    if errs:
        raise llm.LLMError(f"{what}: nach {rounds} Runden noch Fehler: {errs}")
    return obj, rounds + 1


VOTE_Q = ("Style source: {request}\nFaction/variant: {variant}\nList up to 8 of the most iconic units, "
          "structures and hero characters that belong ONLY to this faction, with their exact names in the "
          "source. Answer with one comma-separated line of names, nothing else.")


def _norm(name):
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in ("the", "a", "an")]
    return " ".join(words)


def vote_elements(request, variant, samples=6, log=print):
    """Ikonische Elemente per Mehrheitsentscheid, im Denkmodus.

    Ohne Denkmodus erfand das Modell Namen und vermischte die Fraktionen
    (Tanja bei den Sowjets, „MiG2…MiG8“); mit Denkmodus kommen die richtigen,
    aber jede Antwort mit ein, zwei Ausreißern — die fallen bei der Mehrheit
    heraus. Namensformen werden gebündelt („Kirov“ ⊂ „Kirov Airship“)."""
    answers = []
    for i in range(samples):
        try:
            text, _ = llm.chat([{"role": "user", "content": VOTE_Q.format(request=request, variant=variant)}],
                               temperature=0.6, max_tokens=16000, seed=9000 + i, think=True)
        except llm.LLMError:
            continue
        names = [n.strip(" .*-") for n in text.strip().splitlines()[-1].split(",")]
        answers.append({_norm(n): n for n in names if 2 <= len(n) <= 40 and _norm(n)})
    groups = []          # [{keys}, Stimmen, {Schreibweise: Anzahl}]
    for ans in answers:
        hit_groups = set()
        for key, shown in ans.items():
            for gi, g in enumerate(groups):
                if any(key == k or f" {key} " in f" {k} " or f" {k} " in f" {key} " for k in g[0]):
                    if gi not in hit_groups:
                        g[1] += 1
                        hit_groups.add(gi)
                    g[0].add(key)
                    g[2][shown] = g[2].get(shown, 0) + 1
                    break
            else:
                groups.append([{key}, 1, {shown: 1}])
                hit_groups.add(len(groups) - 1)
    need = max(2, (len(answers) + 1) // 2)
    picked = sorted((g for g in groups if g[1] >= need), key=lambda g: -g[1])[:8]
    names = [max(g[2], key=lambda n: (g[2][n], len(n))) for g in picked]
    log(f"Elemente {variant}: " + (", ".join(f"{n} ({g[1]}/{len(answers)})" for n, g in zip(names, picked))
                                   or "keine Einigung"))
    return names


STYLE_SYSTEM = """Du gestaltest den Bildstil eines Icon-Satzes für ein Desktop-Theme. Ein Bildmodell
malt danach jedes Icon; was es zeigt, steht fest — du bestimmst nur, WIE es aussieht."""

STYLE_USER = """Stilvorlage: {request}
Design-Brief (Auszug):
{brief}
{names_rule}
Farben des Themes: {colors}

Schreibe ein Stilblatt, ENGLISCH, je Feld ein kurzer Satz, so dass alle Icons wie ein Satz
aus der Vorlage wirken (bei einem Spiel: wie dessen eigene Bilder — Bau-Menü, Ladebildschirm,
Verpackung —, NICHT wie moderne App-Icons). Überlege zuerst, wie die Bilder der Vorlage
wirklich gemalt/gerendert sind, und beschreibe genau das.
- medium: Malweise und Bildart der Vorlage.
- palette: 3–5 Farben in Worten (keine Hex-Codes). Die Bilder gelten für ALLE Varianten,
  deshalb neutrale, gedämpfte Grundtöne der Bildwelt (Metall, Erde, Licht) — die Farbe einer
  Variante kommt später über den Rahmen, mische nicht die Leitfarben mehrerer Varianten.
- materials: Oberflächen und Werkstoffe, die die Gegenstände tragen.
- elements: 2–4 wiederkehrende Gestaltungsdetails (z. B. Nieten, Kanten, Leuchtteile).
- lighting: Licht und Schatten.
- background: was hinter jedem Gegenstand liegt — schlicht, dunkel, weich, einfarbig
  (keine Farbblöcke, keine Kacheln), damit der Gegenstand freisteht.
Keine Rahmen, Ränder, Kacheln, Knöpfe oder Schlagschatten — den Rahmen setzt der Motor
selbst um jedes Bild.
- folder: wie ALLE Ordner aussehen — ein Behälter der Bildwelt (z. B. Munitionskiste,
  Aktenkassette, Holztruhe) mit glatter, freier Vorderseite.
- sheet: wie ALLE Dateien aussehen — ein Blatt/eine Karte/Tafel der Bildwelt mit
  umgeknickter Ecke und glatter, freier Fläche.
Jedes Feld beschreibt nur, was man SIEHT (Form, Material, Farbe, Licht) — keine Sätze über
Zweck, Wirkung oder darüber, was später dazukommt. Nie: Schrift, Buchstaben, Zahlen,
Logos, Embleme, Schablonenschrift, Bildschirme mit Inhalt, Personen."""

STYLE_FIX = """Stilblatt für Icons zur Stilvorlage: {request}
Feld „{field}“: {what}
Bisher: {value}
Fehler:
- {errors}
Gib nur dieses Feld neu zurück: englisch, ein Satz, nur was man sieht (Form, Material, Farbe,
Licht) — keine Sätze über Zweck oder was später dazukommt."""

STYLE_WHAT = {"medium": "Malweise und Bildart", "palette": "3–5 Farben in Worten",
              "materials": "Oberflächen und Werkstoffe", "elements": "2–4 wiederkehrende Gestaltungsdetails",
              "lighting": "Licht und Schatten", "background": "was hinter jedem Gegenstand liegt",
              "folder": "wie alle Ordner aussehen: ein Behälter mit glatter, freier Vorderseite",
              "sheet": "wie alle Dateien aussehen: ein Blatt/eine Karte mit umgeknickter Ecke und freier Fläche"}

STYLE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["medium", "palette", "materials", "elements", "lighting", "background", "folder", "sheet"],
    "properties": {k: {"type": "string", "minLength": 10, "maxLength": 220}
                   for k in ("medium", "palette", "materials", "elements", "lighting", "background", "folder",
                             "sheet")}}

STYLE_TRAPS = TRAPS | {"stencil", "stencilled", "stenciled", "lettering", "numbers", "number", "digits",
                       "people", "soldier", "soldiers", "face", "faces", "person", "portrait", "portraits",
                       "character", "characters", "labeling", "labelling", "labelled", "labeled"}


TILE_WORDS = {"border", "borders", "frame", "frames", "framed", "tile", "tiles", "tiled", "button", "buttons",
              "app", "badge", "badges", "outline", "outlines", "outlined"}


# Gegenstände im Stil landen in JEDEM Icon: „Low-polygon models of the Grizzly
# tank …“ unter medium ergab 108 Panzer-Icons (Lauf 24.10.2026).
SUBJECTS = {"tank", "tanks", "aircraft", "airship", "airships", "airplane", "jet", "jets", "ship", "ships",
            "submarine", "helicopter", "generator", "generators", "silo", "silos", "soldier", "soldiers", "unit",
            "units", "vehicle", "vehicles", "robot", "robots", "car", "cars", "truck", "trucks", "building",
            "buildings", "tower", "towers", "weapon", "weapons", "gun", "guns", "cannon", "missile", "missiles",
            "reactor", "coil"}


def check_style(obj, banned, subjects=()):
    obj = {k: v for k, v in obj.items() if k in STYLE_SCHEMA["properties"]}
    errors = []
    for k in ("medium", "palette", "materials", "elements", "lighting", "background"):
        named = sorted({n for n in subjects if _name_in(n, obj[k])} | (_words(obj[k]) & SUBJECTS))
        if named:
            errors.append(f"{k} nennt Gegenstände ({', '.join(named)}) — die malt das Bildmodell in JEDES Icon; "
                          "beschreibe nur Malweise, Farbe, Oberfläche, Licht, ohne Gegenstände")
    if re.search(r"#[0-9a-fA-F]{3,6}\b", obj["palette"]):
        errors.append("palette enthält Hex-Codes — nenne die Farben in Worten")
    for k in ("medium", "elements", "background", "materials", "lighting"):
        low = re.sub(r"\b(no|without|never)\s+(any\s+|a\s+|an\s+)?[\w-]+(\s*(,|or|and)\s*[\w-]+)*", "",
                     obj[k].lower())
        hit = sorted(_words(low) & TILE_WORDS) + (["drop shadow"] if "drop shadow" in low else [])
        if hit:
            errors.append(f"{k} nennt {', '.join(hit)} — das ergibt App-Kacheln; den Rahmen setzt der Motor, "
                          "beschreibe nur den Gegenstand selbst")
    for k in ("folder", "sheet"):
        hit = sorted(_words(obj[k]) & {"emblem", "emblems", "stamp", "stamped", "insignia", "badge", "seal",
                                       "star", "marking", "markings", "tag", "tags"})
        if hit:
            errors.append(f"{k} nennt {', '.join(hit)} — Ordner/Blatt bleiben ohne eigenes Zeichen, der Motor "
                          "setzt je Icon eines darauf; beschreibe nur Form und Material")
    for k, v in obj.items():
        if _words(v) & GERMAN or re.search(r"[äöüß]", v.lower()):
            errors.append(f"{k} ist deutsch — schreibe es englisch")
        if re.search(r"(?i)\b(motor|engine|the system|added later|ready for|left blank for|placeholder)\b", v):
            errors.append(f"{k} spricht über den Ablauf („ready for …“, „motor“) — beschreibe nur, was man sieht")
        low = re.sub(r"\b(no|without|never)\s+(any\s+|a\s+|an\s+)?[\w-]+(\s*(,|or|and)\s*[\w-]+)*", "", v.lower())
        low = re.sub(r"\bsigns? of\b", "", low)
        bad = sorted(_words(low) & STYLE_TRAPS)
        if bad:
            errors.append(f"{k} nennt {', '.join(bad)} — das malt das Bildmodell auf jedes Icon; lass diese "
                          "Wörter ersatzlos weg")
        errors += _mark_errors(k, v, banned)
    return errors


def style_sheet(spec, private=False, log=print, seed=None, subjects=(), feedback=""):
    meta = spec.get("_meta", {})
    colors = "; ".join(f"{v['name']}: Leitfarbe {v['lead']}, Fläche {v['colors']['surface']}" for v in spec["variants"])
    user = STYLE_USER.format(request=meta.get("request", ""), brief=meta.get("brief", "")[:1500],
                             names_rule=_names_rule(private), colors=colors)
    if feedback:
        user += "\n\n" + feedback
    banned = _banned(spec, private)
    msgs = [{"role": "system", "content": STYLE_SYSTEM}, {"role": "user", "content": user}]
    # Denkmodus: eine Anfrage bestimmt das Aussehen aller Icons — ohne ihn kam
    # für Red Alert 2 „glossy 3D, thick borders“, also App-Icons (Test 24.10.2026).
    text, info = llm.chat(msgs, schema=STYLE_SCHEMA, max_tokens=12000, temperature=0.6, seed=seed, think=True)
    log(f"Icon-Stilblatt: {info['tokens']} Token in {info['seconds']} s")
    obj = json.loads(text)
    part = {"type": "object", "additionalProperties": False, "required": ["value"],
            "properties": {"value": {"type": "string", "minLength": 10, "maxLength": 220}}}
    # Teilreparatur je Feld — das ganze Blatt gab das Modell viermal unverändert zurück.
    for r in range(1, 5):
        errs = check_style(obj, banned, subjects)
        if not errs:
            return obj, r
        for k in obj:
            mine = [e for e in errs if e.startswith(k + " ")]
            if not mine:
                continue
            log(f"  Stilblatt {k}: „{obj[k][:110]}“ — {'; '.join(mine)[:120]}")
            fix = STYLE_FIX.format(request=meta.get("request", ""), field=k, what=STYLE_WHAT[k], value=obj[k],
                                   errors="\n- ".join(mine))
            t, _ = llm.chat([{"role": "user", "content": fix}], schema=part, max_tokens=400, temperature=0.4,
                            seed=(seed or 0) + r)
            obj[k] = json.loads(t)["value"]
    # Letzte Stufe ohne LLM: Satzteile mit Fallenwörtern streichen.
    def bad_field(k, text):
        return any(e.startswith(k + " ") for e in check_style(dict(obj, **{k: text}), banned, subjects))
    for k in [k for k in STYLE_SCHEMA["properties"] if bad_field(k, obj[k])]:
        parts = re.split(r"(,\s+|\s+and\s+|;\s+|\.\s+)", obj[k])
        keep = [p for p in parts[::2] if p.strip() and not bad_field(k, p)]
        if keep:
            log(f"  Automatik: Stilblatt {k} gekürzt")
            obj[k] = ", ".join(x.strip(" .") for x in keep) + "."
            obj.setdefault("_auto", []).append(k)
    errs = check_style({k: v for k, v in obj.items() if k != "_auto"}, banned, subjects)
    if errs:
        raise llm.LLMError(f"Icon-Stilblatt: noch Fehler: {errs}")
    return obj, 5


def compose(name, pic, style):
    """Motiv aus Zeichen + Familie: Ordner und Dateien teilen die Grundform."""
    fam = iconset.FAMILY[name]
    if fam == "folder":
        return style["folder"].rstrip(". ") + (f", with {pic} mounted large on its front" if pic else "")
    if fam == "document":
        return style["sheet"].rstrip(". ") + f", with {pic} painted large in its centre"
    return pic


def catalog_motifs(style):
    return {name: {"source": "catalog", "picture": iconset.PICTURE[name],
                   "motif": compose(name, iconset.PICTURE[name], style)} for name in iconset.PAINTED}


def icon_prompt(motif, style):
    """Prompt für ein Katalog-Icon: Motiv + Stilblatt, feste Reihenfolge."""
    nobody = "" if wants_person(motif) else "A single object only, no people, no faces, no hands. "
    return (f"{style['medium'].rstrip('. ')}, square icon picture, the subject fills the frame edge to edge: "
            f"{motif}. {nobody}Colours: {style['palette'].rstrip('. ')}. Materials: "
            f"{style['materials'].rstrip('. ')}. Details: {style['elements'].rstrip('. ')}. "
            f"{style['lighting'].rstrip('. ')}. Background: {style['background'].rstrip('. ')}. "
            "No frame, no border, no text, no letters, no numbers, no logos.")


def plan(spec, private=False, log=print, seed=None, themed_icons=False):
    if not themed_icons:
        return _plan_catalog(spec, private, log, seed)
    return _plan_themed(spec, private, log, seed)


def scene_subjects(result):
    """Namen der Elemente aller Varianten — im Stilblatt verboten."""
    return sorted({e["name"] for v in result["variants"].values() for e in v["elements"]})


def _plan_catalog(spec, private, log, seed):
    """Standard: Szenen je Variante wie bisher, Icons aus Katalog + Stilblatt."""
    result = _scenes(spec, private, log, seed)
    style, r = style_sheet(spec, private, log, seed, subjects=scene_subjects(result))
    result["style"] = style
    result["icons"] = catalog_motifs(style)
    result["rounds"]["style"] = r
    return result


def _scenes(spec, private, log, seed):
    meta = spec.get("_meta", {})
    request, brief = meta.get("request", ""), meta.get("brief", "")
    banned = _banned(spec, private)
    rule = _names_rule(private)
    result = {"private": private, "variants": {}, "icons": None, "rounds": {}}
    others_all = {v["id"]: [o["id"] for o in spec["variants"] if o["id"] != v["id"]] for v in spec["variants"]}
    for v in spec["variants"]:
        anchor = next((a["name"] for a in meta.get("anchors", []) if a.get("lead") == v["lead"]), v["id"])
        voted = vote_elements(request, anchor, log=log) if private else []
        vtext = ("   Abgestimmte Elemente (aus mehreren Befragungen, nimm diese): " + ", ".join(voted)
                 if voted else "")
        user = SCENES_USER.format(request=request, brief=brief, vname=v["name"], mode=v["mode"],
                                  lead=v["lead"], surface=v["colors"]["surface"], names_rule=rule, voted=vtext)
        others = others_all[v["id"]]
        obj, r = _ask(SCENES_SYSTEM, user, SCENE_SCHEMA,
                      lambda o, voted=voted, others=others: check_scenes(o, banned, private, voted, others),
                      log, f"Szenen {v['id']}", seed=seed)
        result["variants"][v["id"]] = obj
        result["rounds"][f"scenes-{v['id']}"] = r
    return result


def _plan_themed(spec, private, log, seed):
    """Alternative (--themed-icons): das LLM erfindet je Icon ein Motiv aus der Bildwelt der Vorlage."""
    meta = spec.get("_meta", {})
    request, brief = meta.get("request", ""), meta.get("brief", "")
    banned = _banned(spec, private)
    rule = _names_rule(private)
    result = _scenes(spec, private, log, seed)
    elements = "\n".join(f"- {e['name']}: {e['look']}" for v in result["variants"].values()
                          for e in v["elements"])
    user = ICONS_USER.format(request=request, brief=brief[:1500], names_rule=rule, icons=iconset.describe(),
                             elements=elements)
    msgs = [{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": user}]
    text, info = llm.chat(msgs, schema=icon_schema(), max_tokens=10000, temperature=0.6, seed=seed)
    log(f"Icon-Motive: {info['tokens']} Token in {info['seconds']} s")
    motifs = json.loads(text)["motifs"]
    # Je fehlerhaftes Icon eine kleine Anfrage — 35 Fehler in einem 70er-Objekt
    # auf einmal hat das Modell nie behoben (Test 24.10.2026).
    item = icon_schema()["properties"]["motifs"]["properties"][iconset.PAINTED[0]]
    rounds = 0
    for rounds in range(1, 5):
        bad = check_icons(motifs, banned)
        if not bad:
            break
        log(f"  Runde {rounds}: {len(bad)} Icon(s) zu reparieren")
        for name, errs in bad.items():
            fix = ICON_FIX.format(request=request, names_rule=rule, name=name,
                                  meaning=iconset.ICONS[name][1],
                                  entry=json.dumps(motifs[name], ensure_ascii=False),
                                  errors="\n- ".join(errs))
            t, _ = llm.chat([{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": fix}],
                            schema=item, max_tokens=400, temperature=0.4, seed=(seed or 0) + rounds)
            motifs[name] = json.loads(t)
    bad = check_icons(motifs, banned)
    auto = []
    for name in list(bad):
        fixed = dict(motifs[name], motif=replace_traps(motifs[name]["motif"]))
        if not check_icon(name, fixed, banned):
            motifs[name] = fixed
            auto.append(name)
    if auto:
        log(f"  Automatik: Fallenwörter ersetzt in {', '.join(auto)}")
        result["auto"] = auto
    bad = check_icons(motifs, banned)
    if bad:
        raise llm.LLMError(f"Icon-Motive: noch Fehler: {bad}")
    result["icons"] = motifs
    result["rounds"]["icons"] = rounds
    return result


CATALOG_FIX = """Icon „{name}“ für die Funktion: {meaning}.
Bisher sollte es zeigen: {entry}
Das Bildmodell hat daraus etwas Unbrauchbares gemacht:
- {errors}
Wähle ein ANDERES, alltägliches, gegenständliches Bild für diese Funktion, das jeder sofort
erkennt und das ein Bildmodell eindeutig malen kann: ein einzelner Gegenstand, englisch,
3–12 Wörter, ohne Schrift und ohne Personen. Kein Bezug zur Stilvorlage nötig — den Stil
setzt der Motor. source: „catalog“."""


def repair_icon(name, entry, errors, spec, private, seed=None, log=print, catalog=False):
    """Ein Motiv neu formulieren lassen — nach einer Bildprüfung, die zeigte,
    was das Bildmodell daraus gemacht hat. Neue Antwort muss check_icon bestehen."""
    request = spec.get("_meta", {}).get("request", "")
    banned = _banned(spec, private)
    item = icon_schema()["properties"]["motifs"]["properties"][iconset.PAINTED[0]]
    errs = list(errors)
    for i in range(3):
        if catalog:
            msgs = [{"role": "user", "content": CATALOG_FIX.format(name=name, meaning=iconset.ICONS[name][1],
                                                                  entry=entry["motif"], errors="\n- ".join(errs))}]
        else:
            msgs = [{"role": "system", "content": ICONS_SYSTEM}, {"role": "user", "content": ICON_FIX.format(
                request=request, names_rule=_names_rule(private), name=name, meaning=iconset.ICONS[name][1],
                entry=json.dumps(entry, ensure_ascii=False), errors="\n- ".join(errs))}]
        t, _ = llm.chat(msgs, schema=item, max_tokens=400, temperature=0.5, seed=(seed or 0) + i)
        new = json.loads(t)
        left = check_icon(name, new, banned)
        if catalog and re.search(r"(?i)\b(background|backdrop|transparent)\b", new["motif"]):
            left.append(f"{name}: motif nennt einen Hintergrund — nur den Gegenstand, den Hintergrund setzt das Stilblatt")
        if new["motif"].strip().lower() == entry["motif"].strip().lower():
            left.append(f"{name}: motif unverändert — es muss ein anderes Motiv sein")
        if not left:
            log(f"  {name}: {entry['motif'][:50]}… → {new['motif'][:70]}")
            return new
        entry, errs = new, left
    fixed = dict(entry, motif=replace_traps(entry["motif"]))
    return fixed if not check_icon(name, fixed, banned) else None


# Wörter, an denen der Motor erkennt, dass ein Motiv eine Person zeigen soll.
PEOPLE = {"officer", "soldier", "soldiers", "commander", "man", "woman", "engineer", "conscript", "conscripts",
          "portrait", "face", "pilot", "general", "agent", "spy", "scientist", "operator", "figure", "trooper",
          "troopers", "girl", "boy", "person", "crew", "sniper", "commando", "technician", "radioman", "operative",
          "worker", "mechanic", "guard", "medic", "g", "gi", "hero", "heroine", "infantry", "infantryman"}


def wants_person(motif):
    return bool(_words(motif) & PEOPLE)


def strip_purpose(motif):
    """„…, representing the reboot function“ beschreibt die Funktion, nicht das Bild."""
    return re.split(r"(?i)(,?\s+(representing|symbolizing|symbolising|to represent)|,\s+for)\b", motif)[0].strip(" .")


def cameo_prompt(motif, request, private):
    """Feste Stilformel für alle Icons — so wird der Satz einheitlich.
    Erklärteile („…, representing PDF documents“) schneidet sie ab: sie
    beschreiben die Funktion, nicht das Bild. „Portrait“ stand früher in der
    Formel; Z-Image malte daraufhin auch zu Kartentisch und Schaltpult ein
    Gesicht (24 von 69, Test 24.10.2026) — ohne Person im Motiv heißt es
    jetzt ausdrücklich: keine Menschen."""
    motif = strip_purpose(motif)
    style = re.split(r"[(:]", request)[0].strip() if private else "a late-1990s real-time strategy game"
    nobody = "" if wants_person(motif) else "A single object only, no people, no faces, no hands. "
    return ("Extreme close-up painted game cameo artwork, the subject fills the entire square image edge to "
            f"edge with no empty margin: {motif}. {nobody}Painted in the style of {style} build-menu cameo "
            "pictures: rich saturated colours, dramatic rim lighting, crisp silhouette, slightly grainy painted "
            "texture. No frame, no border, no text, no letters, no logos.")


def wallpaper_prompt(scene, request, private):
    """Stilformel davor, Schlussformel dahinter — der Satz bleibt einheitlich,
    auch wenn das LLM in einer Szene „military photography“ schreibt."""
    scene = re.sub(r"(?i)^\s*(a\s+)?digital painting( in the style of [^,.:]*)?[,.:]?\s*", "", scene)
    scene = _body(scene).strip(" ,.")
    style = (re.split(r"[(:]", request)[0].strip() + " loading screens and box art") if private \
        else "late-1990s real-time strategy game loading screens"
    return f"Digital painting in the style of {style}, painterly, dramatic lighting: {scene}. No text, no logos."
