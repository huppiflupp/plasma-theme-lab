"""Der LLM-Teil: Stilanalyse (frei) → Spezifikation (grammatik-gebunden)."""
import json

from . import fonts, llm, spec

BRIEF_SYSTEM = """Du bist Art Director für Desktop-Themes (KDE Plasma).
Du beschreibst die visuelle Sprache einer Vorlage so, dass ein Theme daraus
entstehen kann. Konkret und knapp, keine Einleitung."""

BRIEF_USER = """Stilvorlage: {request}

Beschreibe in höchstens 250 Wörtern:
1. Farbwelt mit Hex-Werten; wenn die Vorlage Fraktionen/Varianten kennt, je Variante.
   Beginne jede Variante mit „Leitfarbe: #……“ — die eine Farbe, an der man sie sofort
   erkennt (keine Warn- oder Effektfarbe). Danach Grundton und Akzente.
   Gib an, ob die Varianten eher dunkel oder hell sind.
2. Materialien und Oberflächen (z. B. gebürstetes Metall, Papier, Glas).
3. Formen: Ecken (eckig, abgeschrägt, rund), Kanten, Rahmenstärke, 3D-Wirkung.
4. Typografie (Charakter, nicht Markenname).
5. Motive und Bildwelt für Hintergrundbilder (Szenen, Licht, Stimmung).
6. Ein einfaches Symbol/Emblem, das zum Stil passt.
Halte dich eng an die Vorlage: ihre echten Farben, ihre Fraktionen, ihre Bildwelt.
Namen der Vorlage darfst du hier nennen (der Brief ist intern); das fertige Theme
wird später ohne Markennamen gebaut."""

SPEC_SYSTEM = """Du setzt einen Design-Brief in eine Theme-Spezifikation (JSON) um.
Die Generatoren bauen daraus Farbschema, Plasma Style, Fensterdekoration,
Hintergrundbilder, Plymouth- und GRUB-Theme. Du schreibst nur das JSON.

Felder:
- id: kurz, klein, mit Bindestrich (z. B. "iron-front"). name: Anzeigename, eigene Erfindung,
  KEIN Markenname der Vorlage. description: ein kurzer englischer Satz (höchstens 140 Zeichen).
- shape.corner: square | chamfer (abgeschrägte Ecke, technisch/militärisch) | round.
  shape.corner_size: 0 bei square, sonst 2–8 px. shape.bevel: flat | raised (3D-Kante).
  shape.bevel_width: 0 bei flat, sonst 1–3. shape.outer_border: dunkle Außenlinie 0–2 px.
  shape.edge_glow: true = dünne Leuchtlinie in glow-Farbe innen an Rahmen.
- decoration: Fensterrahmen. title_height 18–40, border 1–8, button_size mindestens
  2 kleiner als title_height, button_shape square|round|chamfer|diamond,
  title_align left|center|right. Knöpfe als Buchstaben: M Menü, S auf allen Arbeitsflächen,
  H Hilfe, F im Vordergrund, B im Hintergrund, L Fensterheber, I Minimieren,
  A Maximieren, X Schließen, _ Abstand. I, A und X müssen vorkommen, kein Knopf doppelt.
- font: Schrift für Titel, Startbildschirm und GRUB. Auswahl:
{fonts}
- emblem.shape: eines von {emblems}. emblem.render: blender (3D-Metall, plastisch)
  oder inkscape (flach, grafisch). emblem.label: kurzes Wort für den Startbildschirm
  (eigene Erfindung, kein Markenname).
- boot.plymouth: emblem-bar (Emblem + Fortschrittsbalken) | emblem-pulse (pulsierendes
  Emblem) | text-bar (Name + Balken). boot.grub: centered | left-panel.
- variants: 1–3 Farbvarianten (z. B. Fraktionen der Vorlage). Je Variante:
  id (klein, ohne Bindestrich), name, look, lead, mode (dark|light), colors, wallpaper_prompt.
  look: ein Satz, welche Farben der Vorlage diese Variante trägt (Leitfarbe, Grundton,
  Material) — schreib ihn zuerst und wähle die Farben danach genau so.
  lead: die Leitfarbe der Variante als Hex — übernimm die „Leitfarbe“ aus dem Brief
  (nicht eine Akzent- oder Warnfarbe); title_active trägt genau diese Leitfarbe.
  Die Leitfarbe gehört in title_active (und gern auch in accent); surface, window und panel sind ein passender Grundton
  (dunkles Metall, Papier, …), nicht beliebig neutral.
  colors (Hex, klein geschrieben):
{colors}
  Regeln: text muss auf surface, window UND panel mindestens 4.5:1 Kontrast haben.
  mode dark heißt: surface und window dunkel (Luminanz ≤ 0.18), Text hell.
  mode light heißt: surface und window hell, Text dunkel.
  accent ist kräftig, damit weißer oder schwarzer Text darauf lesbar ist.
  wallpaper_prompt: englisch, ein durchgehender Absatz (40–120 Wörter) für ein
  Bildmodell: zuerst das Medium („Digital painting …“), dann Motiv aus der Bildwelt
  der Vorlage, Licht, Farbwelt passend zu colors, Bildaufbau mit einer ruhigen, leeren
  Fläche (Himmel, Boden, Nebel). Das Bildmodell malt jedes Wort wörtlich: nenne keine
  Symbole, Icons, Bildschirme, Oberflächen, Schilder, Plakate, Karten, Schrift.
  Keine Marken- oder Figurennamen. Ende immer mit „no text, no logos, no brand names“."""


ANCHOR_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["variants"],
    "properties": {"variants": {"type": "array", "minItems": 1, "maxItems": 3, "items": {
        "type": "object", "additionalProperties": False, "required": ["name", "lead"],
        "properties": {"name": {"type": "string", "maxLength": 30}, "lead": spec.HEX}}}}}
ANCHOR_Q = ("Stilvorlage: {request}\nWelche Varianten oder Fraktionen hat die Vorlage? Nenne für jede "
            "ihre kennzeichnende Erkennungsfarbe — die bunte Farbe, die man sofort mit ihr verbindet "
            "(Fraktionsfarbe, Leuchtfarbe, Markenfarbe), nicht den schwarzen, weißen oder grauen "
            "Hintergrund. Nur wenn die Vorlage wirklich farblos ist, nenne ein Grau.")


def anchors(request, samples=7, log=print):
    """Leitfarben per Mehrheitsentscheid.

    Einzelne Antworten des Modells streuen (bei „Red Alert 2“ kamen für die
    Sowjets Rot, aber auch Schwarz, Grau, Blau oder — im langen Brief —
    Oliv). Die Mehrheit liegt fast immer richtig. Deshalb: mehrere kurze
    Befragungen, je Variante die Farbtöne bündeln, der größte Bündel gewinnt."""
    import colorsys
    import re
    from .palette import rgb
    votes = {}
    for i in range(samples):
        try:
            text, _ = llm.chat([{"role": "user", "content": ANCHOR_Q.format(request=request)}],
                               schema=ANCHOR_SCHEMA, temperature=0.8, max_tokens=300, seed=7000 + i)
        except llm.LLMError:
            continue
        for v in json.loads(text)["variants"]:
            key = re.sub(r"[^a-zäöüß]", "", v["name"].lower())[:5]
            if key:
                votes.setdefault(key, {"names": [], "leads": []})
                votes[key]["names"].append(v["name"])
                votes[key]["leads"].append(v["lead"])
    result = []
    for key, d in votes.items():
        if len(d["names"]) < (samples + 1) // 2:
            continue                    # Minderheitsvariante (z. B. Erweiterung)
        cols = []
        for c in d["leads"]:
            h, l, sat = colorsys.rgb_to_hls(*(x / 255 for x in rgb(c)))
            if sat >= 0.25 and 0.08 <= l <= 0.85:
                cols.append((h * 360, l, c))
        if not cols:
            continue

        def near(a, b):
            dd = abs(a - b) % 360
            return min(dd, 360 - dd) <= 25
        best = max(cols, key=lambda x: sum(near(x[0], y[0]) for y in cols))
        cluster = sorted((y for y in cols if near(best[0], y[0])), key=lambda y: y[1])
        if len(cluster) < max(2, round(samples * 0.4)):
            continue                    # zu wenig Einigkeit: der Brief entscheidet
        name = max(set(d["names"]), key=d["names"].count)
        result.append({"name": name, "lead": cluster[len(cluster) // 2][2],
                       "support": f"{len(cluster)}/{samples}"})
    log("Leitfarben: " + (", ".join(f"{a['name']} {a['lead']} ({a['support']})" for a in result) or "keine Einigung"))
    return result


def brief(request, log=print, lead_colors=()):
    user = BRIEF_USER.format(request=request)
    if lead_colors:
        user += ("\n\nAbgestimmte Leitfarben (aus mehreren Befragungen, verbindlich): " +
                 ", ".join(f"{a['name']}: {a['lead']}" for a in lead_colors) +
                 ". Nimm sie als Leitfarben der Varianten.")
    text, info = llm.chat([{"role": "system", "content": BRIEF_SYSTEM},
                           {"role": "user", "content": user}],
                          think=True, max_tokens=8000, temperature=0.3)
    log(f"Brief: {info['tokens']} Token in {info['seconds']} s")
    return text.strip()


def _sub_schema(path):
    node = spec.SCHEMA
    for key in path:
        node = node["items"] if isinstance(key, int) else node["properties"][key]
    return node


def _get(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def _set(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def repair_part(system, request, design_brief, current, path, errors, log=print, seed=None):
    """Nur das fehlerhafte Teilstück neu erzeugen lassen.

    Muss ein kleines Modell die ganze Spezifikation wiederholen, um ein Wort zu
    ersetzen, schleppt es den Fehler oft mit. Mit Teilschema und nur diesem
    Ausschnitt ist die Aufgabe klein genug."""
    name = ".".join(str(k) for k in path)
    part = _get(current, path)
    user = (f"Stilvorlage: {request}\n\nDesign-Brief:\n{design_brief}\n\n"
            f"Aktuelle Spezifikation:\n{json.dumps(current, ensure_ascii=False)}\n\n"
            f"Der Teil „{name}“ ist fehlerhaft:\n- " + "\n- ".join(errors) +
            f"\n\nGib nur diesen Teil korrigiert zurück, als {{\"value\": …}}. "
            "Übernimm vorgeschlagene Werte genau. Ändere sonst so wenig wie möglich.\n"
            f"Bisher: {json.dumps(part, ensure_ascii=False)}")
    schema = {"type": "object", "additionalProperties": False, "required": ["value"],
              "properties": {"value": _sub_schema(path)}}
    text, info = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                          schema=schema, max_tokens=3000, temperature=0.3, seed=seed)
    log(f"  Reparatur {name}: {info['tokens']} Token in {info['seconds']} s")
    return json.loads(text)["value"]


def design(request, design_brief, avoid=(), log=print, retries=4, seed=None):
    system = SPEC_SYSTEM.format(
        fonts=fonts.describe(),
        emblems=", ".join(spec.EMBLEMS),
        colors="\n".join(f"    {k}: {v}" for k, v in spec.COLOR_KEYS.items()))
    user = (f"Stilvorlage: {request}\n\nDesign-Brief:\n{design_brief}\n\n"
            "Erzeuge die Spezifikation.")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text, info = llm.chat(messages, schema=spec.SCHEMA, max_tokens=6000, temperature=0.5, seed=seed)
    log(f"Spezifikation: {info['tokens']} Token in {info['seconds']} s")
    current = json.loads(text)
    current["_meta"] = {"request": request}
    rounds = 0
    for rounds in range(1, retries + 1):
        errs = spec.validate_paths(current, avoid)
        if not errs:
            return current, rounds
        groups = {}
        for path, msg in errs:
            groups.setdefault(path, []).append(msg)
            log(f"  Fehler: {msg}")
        for path, msgs in groups.items():
            if path == ():
                # Querbezüge (z. B. doppelte ids): ganze Spezifikation
                current, _ = llm.chat_json(
                    messages + [{"role": "assistant", "content": json.dumps(current, ensure_ascii=False)},
                                {"role": "user", "content": "Fehler:\n- " + "\n- ".join(msgs) +
                                 "\nGib die vollständige, korrigierte Spezifikation zurück."}],
                    spec.SCHEMA, retries=0, max_tokens=6000, temperature=0.3, seed=seed)
                current["_meta"] = {"request": request}
            else:
                _set(current, path, repair_part(system, request, design_brief, current, path, msgs,
                                                log=log, seed=seed))
    # Letzte Stufe ohne LLM, nur für Fallenwörter im Bild-Prompt.
    auto = []
    for i, v in enumerate(current["variants"]):
        if spec.trap_sentences(v["wallpaper_prompt"]):
            v["wallpaper_prompt"] = spec.strip_traps(v["wallpaper_prompt"])
            auto.append(f"variants.{i}.wallpaper_prompt: Sätze mit Fallenwörtern gestrichen")
    d = current["decoration"]
    used = d["buttons_left"] + d["buttons_right"]
    if any(ch not in used for ch in "IAX") or any(used.count(ch) > 1 for ch in used if ch != "_"):
        d.update(spec.fixed_buttons(d))
        auto.append("decoration: Pflichtknöpfe I, A, X ergänzt")
    if auto:
        log("  Automatik: " + "; ".join(auto))
        current.setdefault("_auto", []).extend(auto)
    errs = spec.validate(current, avoid)
    if errs:
        raise llm.LLMError(f"nach {retries} Reparaturrunden noch Fehler: {errs}")
    return current, rounds + 1


def run(request, avoid=(), log=print, seed=None):
    leads = anchors(request, log=log)
    b = brief(request, log=log, lead_colors=leads)
    s, attempts = design(request, b, avoid=avoid, log=log, seed=seed)
    s["_meta"].update({"anchors": leads, "brief": b, "attempts": attempts})
    return s
