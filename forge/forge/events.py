"""The event log: one JSON line per step, for overlays in a recorded video.

Each line carries the wall-clock time, the seconds since the run began, the
stage and what happened in it — what the LLM decided (shortened), prompts
sent to ComfyUI, check results, repairs, durations. `forge.py … --events
<file>` (default <out>/events.jsonl) writes it; `tail -f` or a small
overlay script can show it beside the screen recording.

    {"ts": "2026-10-26T14:05:10", "t": 12.4, "stage": "colors", "event": "decided",
     "data": {...}}
"""
import json
import time

_LOG = None


class EventLog:
    def __init__(self, path):
        self.path = path
        self.t0 = time.time()
        self.stage_t0 = {}
        open(path, "a").close()

    def emit(self, stage, event, **data):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "t": round(time.time() - self.t0, 1),
               "stage": stage, "event": event}
        if data:
            rec["data"] = _short(data)
        with open(self.path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def begin(self, stage, **data):
        self.stage_t0[stage] = time.time()
        return self.emit(stage, "begin", **data)

    def end(self, stage, **data):
        t = self.stage_t0.pop(stage, None)
        if t is not None:
            data["seconds"] = round(time.time() - t, 1)
        return self.emit(stage, "end", **data)


def _short(value, limit=400):
    """Long texts shortened, so a line stays readable as an overlay."""
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit - 1] + "…"
    if isinstance(value, dict):
        return {k: _short(v, limit) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_short(v, limit) for v in value[:20]]
    return value


def open_log(path):
    global _LOG
    _LOG = EventLog(path) if path else None
    return _LOG


def emit(stage, event, **data):
    """Write to the run's log if there is one (modules call this freely)."""
    if _LOG:
        return _LOG.emit(stage, event, **data)
    return None


def begin(stage, **data):
    return _LOG.begin(stage, **data) if _LOG else None


def end(stage, **data):
    return _LOG.end(stage, **data) if _LOG else None
