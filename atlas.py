"""Minimal Atlas API client — shared by probe.py and the recursion test.

Just the calls we actually use: upload an asset, submit a job, poll it,
fetch the result. No retry/backoff cleverness yet — add it if a real job
ever needs it.

Every submit/complete is appended to state/api_log.jsonl (see log_event) so
any consumer — the Flask app's live log panel, or a manifest audit later —
has a single, complete, real-time record of every Atlas call this repo has
ever made. This is the proof trail for the challenge claims, not decoration.
"""
import json
import mimetypes
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

API_KEY = os.environ.get("MOTH_API_KEY") or os.environ.get("MOTH_Quantum_API_KEY")
API_BASE = os.environ.get("MOTH_API_BASE", "https://api.mothquantum.com/api/v1")

if not API_KEY:
    raise RuntimeError("MOTH_API_KEY not set (check .env)")

H = {"Authorization": f"Bearer {API_KEY}"}

MAX_EDGE = 1024  # Telablur's own pixel-budget cap; no point uploading bigger

# No call here had a timeout, anywhere, until a real spin got stuck on one
# of them for over an hour (checked directly: process state, thread count,
# not guessed) and silently jammed the whole piece — /api/spin serializes
# spins, so one hung request blocks every future spin too, indefinitely.
# 30s comfortably covers a real asset upload or a status poll; it is not
# the job's own processing time (that can legitimately take longer and is
# handled by wait_for_job's own polling loop, each poll individually capped
# by this same timeout).
HTTP_TIMEOUT = 30

# That same incident recurred live tonight (26-09-2026, twice in ten minutes)
# despite HTTP_TIMEOUT above — because it only bounds each individual poll
# request, not the polling loop itself. A job Atlas leaves at status:running
# forever (never erroring, never timing out any single request) made
# wait_for_job's `while True` spin forever right along with it, wedging
# _active_spin_id and returning 409 spin_in_progress to every visitor with
# no recovery short of restarting the process by hand. A real job never
# legitimately runs anywhere near this long (typical: 3-10s) — 180s is a
# generous, clearly-a-hang bound, not a tight one.
MAX_JOB_WAIT = 180

# Credits/run per engine, from docs/atlas-api-docs-reference (§ engine catalog).
# Used only to annotate the log with running spend — not fetched live, Atlas
# has no live balance endpoint.
CREDIT_COSTS = {
    "telablur-v1": 1, "blur-v1": 1, "blur-core-v1": 1, "tessa-image-v1": 1,
    "deep-fryer-v1": 1, "entanglement-shader-v1": 1, "qpixl-v1": 1,
    "otoc-echo-v1": 1, "blur-midi-v1": 1,
    "coin-toss-v1": 2, "retrocausal-echo-v1": 2,
    "qrc-audio-v1": 5, "qrc-midi-v1": 5, "qrc-train-v2": 5,
    "graph-v1": 5, "labyrinth-v1": 5,
    "tamagotchi-v1": 0,
}

LOG_PATH = Path("state/api_log.jsonl")
_log_lock = threading.Lock()

# Broadcast hook for live consumers (the Flask app's /stream). Empty unless
# something calls subscribe() — every existing caller of log_event (probe
# scripts, quantum.py, run_spin) is completely unaffected either way.
_broadcast_hooks: list[Callable[[dict], None]] = []


def subscribe(callback: Callable[[dict], None]) -> None:
    _broadcast_hooks.append(callback)


def log_event(event: dict) -> dict:
    """Append one event to the shared, persistent API/quantum log."""
    event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with _log_lock:
        LOG_PATH.parent.mkdir(exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(json.dumps(event) + "\n")
    for hook in _broadcast_hooks:
        try:
            hook(event)
        except Exception:
            pass  # a dead subscriber must never break logging
    return event


def read_log(limit: int = 200) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with _log_lock:
        lines = LOG_PATH.read_text().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def resize_for_upload(src: Path, dest: Path) -> Path:
    img = Image.open(src).convert("RGB")
    img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    img.save(dest, "PNG")
    return dest


def upload_asset(path: Path) -> str:
    data = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "image/png"
    asset = requests.post(
        f"{API_BASE}/assets",
        headers=H,
        json={"filename": path.name, "content_type": content_type, "size_bytes": len(data)},
        timeout=HTTP_TIMEOUT,
    ).json()
    if "asset_id" not in asset:
        raise RuntimeError(f"asset registration failed: {asset}")
    put = requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"], timeout=HTTP_TIMEOUT)
    put.raise_for_status()
    requests.post(f"{API_BASE}/assets/{asset['asset_id']}/complete", headers=H, timeout=HTTP_TIMEOUT).raise_for_status()
    return asset["asset_id"]


def submit_job(engine: str, params: dict, input_files: dict | None = None) -> str:
    payload = {"params": params}
    if input_files:
        payload["input_files"] = input_files
    resp = requests.post(
        f"{API_BASE}/engines/{engine}/process",
        headers=H,
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    if resp.status_code != 202:
        raise RuntimeError(f"submit failed: {resp.status_code} {resp.text}")
    job_id = resp.json()["job_id"]
    log_event({
        "type": "submit", "engine": engine, "job_id": job_id, "params": params,
        "credits": CREDIT_COSTS.get(engine, 1),
    })
    return job_id


def wait_for_job(job_id: str, poll_interval=2.0, engine: str | None = None):
    t0 = time.time()
    while True:
        st = requests.get(f"{API_BASE}/jobs/{job_id}/status", headers=H, timeout=HTTP_TIMEOUT).json()
        if st["status"] in ("completed", "failed", "cancelled"):
            elapsed = time.time() - t0
            log_event({
                "type": "complete", "engine": engine, "job_id": job_id,
                "status": st["status"], "elapsed_s": round(elapsed, 1),
                "error": st.get("error"),
            })
            return st, elapsed
        elapsed = time.time() - t0
        if elapsed > MAX_JOB_WAIT:
            log_event({
                "type": "complete", "engine": engine, "job_id": job_id,
                "status": "timeout", "elapsed_s": round(elapsed, 1),
                "error": f"still {st['status']} after {MAX_JOB_WAIT}s, giving up",
            })
            raise RuntimeError(f"{engine or 'job'} {job_id} timed out after {MAX_JOB_WAIT}s (still {st['status']})")
        time.sleep(poll_interval)


def fetch_result(job_id: str) -> dict:
    return requests.get(f"{API_BASE}/jobs/{job_id}/result", headers=H, timeout=HTTP_TIMEOUT).json()


def get_storage() -> dict:
    return requests.get(f"{API_BASE}/me/storage", headers=H, timeout=HTTP_TIMEOUT).json()
