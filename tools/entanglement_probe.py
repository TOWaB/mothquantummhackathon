#!/usr/bin/env python3
"""One-off probe of entanglement-shader-v1. Default params, one job, no retries.

    python tools/entanglement_probe.py

Logs submit/complete to state/api_log.jsonl via atlas.py, same shape as every
other engine. Saves the raw zip and its extracted contents to
out/materials/probe/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

import atlas

OUT_DIR = Path("out/materials/probe")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = "entanglement-shader-v1"
PARAMS = {  # documented defaults, verbatim — not tuning anything
    "absorption": 0.95,
    "incoming_rays": 8,
    "interaction": 1,
    "layers": 2,
    "reflectance": 0.2,
    "resolution": 60,
    "style": "peaked",
}


def main():
    job_id = atlas.submit_job(ENGINE, PARAMS)
    print(f"job_id: {job_id}")

    st, elapsed = atlas.wait_for_job(job_id, engine=ENGINE)
    print(f"status: {st['status']}  elapsed_s: {elapsed:.1f}")

    if st["status"] != "completed":
        print(f"NOT completed, stopping (no retry): {st}")
        sys.exit(1)

    result = atlas.fetch_result(job_id)
    outputs = result.get("outputs") or []
    if not outputs:
        print(f"completed but no outputs: {result}")
        sys.exit(1)

    out = outputs[0]
    content_type = out.get("content_type")
    zip_path = OUT_DIR / "result.zip"
    data = requests.get(out["url"]).content
    zip_path.write_bytes(data)

    print(f"content_type: {content_type}")
    print(f"size_bytes: {len(data)}")
    print(f"credits: {atlas.CREDIT_COSTS.get(ENGINE, '?')}")
    print(f"saved: {zip_path}")

    log = {
        "job_id": job_id,
        "engine": ENGINE,
        "params": PARAMS,
        "elapsed_s": round(elapsed, 1),
        "status": st["status"],
        "content_type": content_type,
        "size_bytes": len(data),
        "output_file": str(zip_path),
    }
    (Path("state") / f"probe_{job_id}.json").write_text(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
