"""Anbindung an einen OpenAI-kompatiblen lokalen Server (llama.cpp, Ollama, vLLM).

Zuverlässigkeit kommt aus drei Dingen: Grammatik-gebundener Ausgabe
(response_format json_schema), einer Validierung danach und einer
Reparaturschleife, die dem Modell die konkreten Fehler zurückgibt.
"""
import json
import os
import time
import urllib.request

BASE = os.environ.get("FORGE_LLM", "http://127.0.0.1:8090/v1")
MODEL = os.environ.get("FORGE_MODEL", "local")


class LLMError(RuntimeError):
    pass


def chat(messages, schema=None, max_tokens=4096, temperature=0.4, think=False,
         timeout=600, seed=None):
    from . import gpu
    gpu.need("llm")
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature,
            "chat_template_kwargs": {"enable_thinking": think}}
    if seed is not None:
        body["seed"] = seed
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "spec", "schema": schema}}
    req = urllib.request.Request(BASE + "/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except Exception as e:  # noqa: BLE001 - Netz, Timeout, HTTP-Fehler
        raise LLMError(f"LLM nicht erreichbar ({BASE}): {e}") from e
    msg = d["choices"][0]["message"]
    content = msg.get("content") or ""
    if d["choices"][0].get("finish_reason") == "length":
        raise LLMError("Antwort abgeschnitten (max_tokens zu klein)")
    return content, {"seconds": round(time.time() - t0, 1),
                     "tokens": d.get("usage", {}).get("completion_tokens")}


def chat_json(messages, schema, validate=None, retries=3, log=None, **kw):
    """Fragt JSON nach Schema ab; `validate(obj)` liefert eine Fehlerliste.

    Bei Fehlern bekommt das Modell seine Antwort und die Fehler zurück und
    soll korrigieren. Liefert (obj, versuche)."""
    msgs = list(messages)
    for attempt in range(1, retries + 2):
        text, info = chat(msgs, schema=schema, **kw)
        if log:
            log(f"LLM-Antwort {attempt}: {info['tokens']} Token in {info['seconds']} s")
        try:
            obj = json.loads(text)
            errors = validate(obj) if validate else []
        except json.JSONDecodeError as e:
            obj, errors = None, [f"kein gültiges JSON: {e}"]
        if not errors:
            return obj, attempt
        if log:
            for e in errors:
                log(f"  Fehler: {e}")
        msgs = list(messages) + [
            {"role": "assistant", "content": text},
            {"role": "user", "content":
             "Deine Spezifikation hat diese Fehler:\n- " + "\n- ".join(errors) +
             "\nGib die vollständige, korrigierte Spezifikation zurück. "
             "Ändere nur, was nötig ist."}]
    raise LLMError(f"nach {retries + 1} Versuchen noch Fehler: {errors}")
