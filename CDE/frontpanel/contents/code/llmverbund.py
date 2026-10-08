#!/usr/bin/env python3
"""Standalone reader, logic adapted from /home/seeas/projects/llmtop/llmtop.py:
_llama_live, RateTracker, FinishedRate and guarded_ports. No import or execution
of that project. Only explicitly configured backend ports are scraped; the known
ai395 socket proxy (8090) is rejected before any transport is started.
"""
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DEFAULT_HOSTS = "245k=http://127.0.0.1:8090,ai395=ssh:18090,x9=http://x9:8090,victus=ssh:8090"
HOST = r"[A-Za-z0-9][A-Za-z0-9._-]*"
BUDGET = 3.3


def hosts_from_text(text):
    nodes = {}
    for entry in text.split(","):
        match = re.fullmatch(rf"({HOST})=(http://({HOST}):(\d{{1,5}})|ssh:(\d{{1,5}}))", entry.strip())
        if not match:
            continue
        name, target, address, http_port, ssh_port = match.groups()
        port = int(http_port or ssh_port)
        if not 1 <= port <= 65535:
            continue
        # Never probe the socket-activated proxy, including HTTP configuration.
        if port == 8090 and (name.lower() == "ai395" or
                            (address or "").lower().split(".")[0] == "ai395"):
            continue
        nodes[name] = {"name": name, "target": target, "ssh": ssh_port is not None}
    return list(nodes.values())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # A redirect must not lead us to a socket proxy.


def read_endpoint(node, endpoint, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return None, "unreachable"
    if node["ssh"]:
        port = node["target"].split(":")[1]  # validated digits only
        command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
                   "-o", "ConnectionAttempts=1", "-o", "StrictHostKeyChecking=yes",
                   "-o", "UpdateHostKeys=no", "--", node["name"],
                   f"curl -s -m2 http://127.0.0.1:{port}/{endpoint}"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=remaining)
            if result.returncode == 7:  # curl couldn't connect; SSH itself succeeded
                return None, "sleeping"
            return (result.stdout, "running") if result.returncode == 0 else (None, "unreachable")
        except (OSError, subprocess.TimeoutExpired):
            return None, "unreachable"
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(node["target"] + "/" + endpoint, timeout=min(1.5, remaining)) as response:
            return response.read().decode("utf-8"), "running"
    except urllib.error.HTTPError:
        return "", "running"  # /slots disabled: try /metrics
    except (OSError, UnicodeError, urllib.error.URLError):
        return None, "unreachable"


def number(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("invalid counter")
    return result


def query(node, previous):
    row = {"name": node["name"], "tokens_per_second": 0, "state": "unreachable"}
    deadline = time.monotonic() + BUDGET
    text, state = read_endpoint(node, "slots", deadline)
    row["state"] = state
    if text is None:
        return row, None
    try:
        slots = json.loads(text)
        if not isinstance(slots, list) or not all(isinstance(s, dict) for s in slots):
            raise ValueError("slots unavailable")
        total = 0
        for slot in slots:
            nxt = slot.get("next_token") or {}
            if isinstance(nxt, list):
                nxt = nxt[0] if nxt else {}
            total += number(nxt.get("n_decoded") or 0)
        now = time.monotonic()
        current = {"mode": "slots", "counter": total, "time": now}
        row["state"] = "busy" if any(s.get("is_processing") for s in slots) else "running"
        if previous and previous["mode"] == "slots":
            delta, elapsed = total - previous["counter"], now - previous["time"]
            if delta >= 0 and elapsed > 0:
                row["tokens_per_second"] = delta / elapsed
        return row, current
    except (ValueError, TypeError, AttributeError):
        pass
    text, state = read_endpoint(node, "metrics", deadline)
    if text is None:
        row["state"] = state
        return row, None
    try:
        counters = {}
        for line in text.splitlines():
            match = re.fullmatch(r"(llamacpp:tokens_predicted(?:_seconds)?_total)(?:\{[^}]*\})?\s+(\S+)(?:\s+\S+)?", line)
            if match:
                counters[match[1]] = number(match[2])
        tokens = counters["llamacpp:tokens_predicted_total"]
        seconds = counters["llamacpp:tokens_predicted_seconds_total"]
        rate = 0
        if previous and previous["mode"] == "metrics":
            dt, ds = tokens - previous["counter"], seconds - previous["seconds"]
            if dt >= 0 and ds >= 0:
                rate = dt / ds if dt > 0 and ds > 0 else previous["rate"]
        # Unlike the lifetime-average first scrape, the first sample is always 0.
        row.update(state="running", tokens_per_second=rate)
        return row, {"mode": "metrics", "counter": tokens, "seconds": seconds, "rate": rate}
    except (KeyError, ValueError, TypeError):
        row["state"] = "unreachable"
        return row, None


def state_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    folder = Path(runtime) / "cde-llmverbund" if runtime else Path(f"/tmp/cde-llmverbund-{os.getuid()}")
    folder.mkdir(mode=0o700, parents=False, exist_ok=True)
    stat = folder.lstat()
    if folder.is_symlink() or not folder.is_dir() or stat.st_uid != os.getuid():
        raise OSError("unsafe status directory")
    folder.chmod(0o700)
    return folder / "state.json"


def load_state(path):
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return {}
        for sample in data.values():
            if sample["mode"] not in ("slots", "metrics"):
                return {}
            for field in ("counter", "time") if sample["mode"] == "slots" else ("counter", "seconds", "rate"):
                sample[field] = number(sample[field])
        return data
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def save_state(path, data):
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(data, stream, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def collect(nodes, path):
    previous = load_state(path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(nodes))) as pool:
        results = list(pool.map(lambda n: query(n, previous.get(n["name"] + "=" + n["target"])), nodes))
    history = {n["name"] + "=" + n["target"]: sample for n, (_, sample) in zip(nodes, results) if sample is not None}
    save_state(path, history)
    rows = [row for row, _ in results]
    return {"nodes": rows, "total": sum(r["tokens_per_second"] for r in rows)}


if __name__ == "__main__":
    nodes = hosts_from_text(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOSTS)
    try:
        result = collect(nodes, state_path())
    except OSError as error:
        print(f"CDE LLM status: {error}", file=sys.stderr)
        result = {"nodes": [{"name": n["name"], "state": "unreachable", "tokens_per_second": 0} for n in nodes], "total": 0}
    print(json.dumps(result, separators=(",", ":"), allow_nan=False))
