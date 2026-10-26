"""Connection to an OpenAI-compatible local server (llama.cpp, Ollama, vLLM).

Reliability comes from three things: output bound by a grammar
(response_format json_schema), a validation afterwards and a repair loop
that gives the model its concrete errors back.
"""
import json
import os
import time
import urllib.request

BASE = os.environ.get("FORGE_LLM", "http://127.0.0.1:8090/v1")
MODEL = os.environ.get("FORGE_MODEL", "local")
# The model that looks at pictures (visual checks, forge/review.py): the same
# server by default (Qwen3.6 with its mmproj understands images); another
# OpenAI-compatible endpoint with vision can be named here.
VISION = os.environ.get("FORGE_VISION", BASE)


class LLMError(RuntimeError):
    pass


def chat(messages, schema=None, max_tokens=4096, temperature=0.4, think=False,
         timeout=600, seed=None, base=None):
    from . import gpu
    base = base or BASE
    if base == BASE:
        gpu.need("llm")
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature,
            "chat_template_kwargs": {"enable_thinking": think}}
    if seed is not None:
        body["seed"] = seed
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "spec", "schema": schema}}
    req = urllib.request.Request(base + "/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except Exception as e:  # noqa: BLE001 - network, timeout, HTTP error
        raise LLMError(f"LLM not reachable ({base}): {e}") from e
    msg = d["choices"][0]["message"]
    content = msg.get("content") or ""
    if d["choices"][0].get("finish_reason") == "length":
        raise LLMError("answer cut off (max_tokens too small)")
    return content, {"seconds": round(time.time() - t0, 1),
                     "tokens": d.get("usage", {}).get("completion_tokens")}


def chat_json(messages, schema, validate=None, retries=3, log=None, **kw):
    """Asks for JSON by schema; `validate(obj)` returns a list of errors.

    On errors the model gets its answer and the errors back and is to
    correct them. Returns (obj, attempts)."""
    msgs = list(messages)
    for attempt in range(1, retries + 2):
        text, info = chat(msgs, schema=schema, **kw)
        if log:
            log(f"LLM answer {attempt}: {info['tokens']} tokens in {info['seconds']} s")
        try:
            obj = json.loads(text)
            errors = validate(obj) if validate else []
        except json.JSONDecodeError as e:
            obj, errors = None, [f"no valid JSON: {e}"]
        if not errors:
            return obj, attempt
        if log:
            for e in errors:
                log(f"  error: {e}")
        msgs = list(messages) + [
            {"role": "assistant", "content": text},
            {"role": "user", "content":
             "Your specification has these errors:\n- " + "\n- ".join(errors) +
             "\nReturn the complete, corrected specification. "
             "Change only what is necessary."}]
    raise LLMError(f"still errors after {retries + 1} attempts: {errors}")
