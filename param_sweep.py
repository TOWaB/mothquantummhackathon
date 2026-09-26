"""
One-variable-at-a-time parameter sweep on a fixed image pair.

image1 = H66A1993mab.jpg (horn player, color), image2 = H66A0009mab.jpg
(violinists, b&w) — reused as-is every run so the only thing that changes
between outputs is the one parameter listed. Mask (where noted) is the
background mask computed earlier (out/person_mask_background.png).

Run with: uv run --python .venv param_sweep.py
"""
import json
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/param_sweep")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE1_NAME = "H66A1993mab.jpg"
IMAGE2_NAME = "H66A0009mab.jpg"
MASK_PATH = Path("out/person_mask_background.png")

BASELINE = {"strength": 0.6, "direction": "full", "size": 1024, "downscale": True}

RUNS = [
    ("01_baseline", {}, True),
    ("02_strength_low_0.3", {"strength": 0.3}, True),
    ("03_strength_high_0.8", {"strength": 0.8}, True),
    ("04_direction_vertical", {"direction": "vertical"}, True),
    ("05_direction_horizontal", {"direction": "horizontal"}, True),
    ("06_downscale_off", {"downscale": False}, True),
    ("07_size_512", {"size": 512}, True),
    ("08_no_mask", {}, False),
]


def main():
    if not MASK_PATH.exists():
        print(f"{MASK_PATH} not found — run person_mask_test.py first.")
        return

    print(f"image1: {IMAGE1_NAME}, image2: {IMAGE2_NAME}")
    image1_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE1_NAME, OUT_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE2_NAME, OUT_DIR / "image2.png")

    print("Uploading image1, image2, mask once, reused every run...")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)
    mask_asset = atlas.upload_asset(MASK_PATH)

    manifest = []
    for label, overrides, use_mask in RUNS:
        params = {**BASELINE, **overrides}
        input_files = {"image1": image1_asset, "image2": image2_asset}
        if use_mask:
            input_files["mask"] = mask_asset

        print(f"\n--- {label} --- params={params} mask={'yes' if use_mask else 'no'}")
        job_id = atlas.submit_job("telablur-v1", params, input_files)
        st, elapsed = atlas.wait_for_job(job_id)
        print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            manifest.append({"label": label, "job_id": job_id, "params": params, "mask": use_mask,
                              "status": st["status"], "error": st.get("error")})
            continue

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"{label}.png"
        for out in result.get("outputs") or []:
            out_path.write_bytes(requests.get(out["url"]).content)
        print(f"saved {out_path}")

        manifest.append({
            "label": label, "job_id": job_id, "params": params, "mask": use_mask,
            "elapsed_s": round(elapsed, 1), "file": str(out_path),
        })

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} runs in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
