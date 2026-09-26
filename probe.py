"""
Probe run: upload two real images, call telablur-v1, poll to completion.

Answers the four unknowns the build plan needs before anything else:
does the key work, what does a real job look like, how long does it take,
does the output survive. Run with: uv run --python .venv probe.py
"""
import json
import sys
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out")
STATE_DIR = Path("state")
OUT_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)


def main():
    sources = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.jpeg")) + sorted(IMAGES_DIR.glob("*.png"))
    if len(sources) < 2:
        print(f"Need at least 2 images in {IMAGES_DIR}/, found {len(sources)}.")
        sys.exit(1)
    src1, src2 = sources[0], sources[1]
    print(f"Using {src1.name} -> {src2.name}")

    print("Resizing for upload...")
    p1 = atlas.resize_for_upload(src1, OUT_DIR / "probe_image1.png")
    p2 = atlas.resize_for_upload(src2, OUT_DIR / "probe_image2.png")

    storage_before = atlas.get_storage()

    print("Uploading image1...")
    asset1 = atlas.upload_asset(p1)
    print(f"  asset_id: {asset1}")
    print("Uploading image2...")
    asset2 = atlas.upload_asset(p2)
    print(f"  asset_id: {asset2}")

    params = {"strength": 0.5}  # defaults otherwise; testing the call, not tuning it yet
    job_id = atlas.submit_job("telablur-v1", params, {"image1": asset1, "image2": asset2})
    print(f"Submitted job {job_id}")

    print("Polling...", end="", flush=True)
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"\nDone in {elapsed:.1f}s, status={st['status']}")

    if st["status"] != "completed":
        print(f"Job did not complete: {st}")
        log = {"job_id": job_id, "status": st["status"], "elapsed_s": elapsed, "error": st.get("error")}
        (STATE_DIR / f"probe_{job_id}.json").write_text(json.dumps(log, indent=2))
        sys.exit(1)

    result = atlas.fetch_result(job_id)
    out_path = None
    for out in result.get("outputs") or []:
        out_path = OUT_DIR / f"probe_{job_id}_{out['slot']}.png"
        data = requests.get(out["url"]).content
        out_path.write_bytes(data)
        print(f"Saved {out_path} ({len(data)} bytes)")

    storage_after = atlas.get_storage()

    log = {
        "job_id": job_id,
        "engine": "telablur-v1",
        "params": params,
        "input_images": [src1.name, src2.name],
        "asset_ids": {"image1": asset1, "image2": asset2},
        "elapsed_s": round(elapsed, 1),
        "status": st["status"],
        "output_file": str(out_path) if out_path else None,
        "storage_before": storage_before,
        "storage_after": storage_after,
    }
    (STATE_DIR / f"probe_{job_id}.json").write_text(json.dumps(log, indent=2))
    print(f"\nLatency: {elapsed:.1f}s per job. Logged to state/probe_{job_id}.json")


if __name__ == "__main__":
    main()
