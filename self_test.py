"""
Self-test: image1 = image2 = the SAME file. Isolates whether the grid noise
comes from blending two different photos, or is baked into the quantum
encode/measure roundtrip regardless of content. No mask — with identical
inputs the mask wouldn't change anything (mask*image2 + (1-mask)*image1 =
image2 everywhere when image1==image2).

Run with: uv run --python .venv self_test.py
"""
import json
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/self_test")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_NAME = "H66A0009mab.jpg"

BASELINE = {"strength": 0.6, "direction": "full", "size": 1024, "downscale": True}

RUNS = [
    ("01_baseline_0.6", {}),
    ("02_strength_0.1", {"strength": 0.1}),
    ("03_strength_0.3", {"strength": 0.3}),
    ("04_strength_0.8", {"strength": 0.8}),
    ("05_direction_vertical", {"direction": "vertical"}),
    ("06_direction_horizontal", {"direction": "horizontal"}),
    ("07_downscale_off", {"downscale": False}),
    ("08_size_512", {"size": 512}),
]


def main():
    print(f"image1 = image2 = {IMAGE_NAME}")
    image_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE_NAME, OUT_DIR / "image.png")

    print("Uploading (once, reused as both image1 and image2)...")
    image_asset = atlas.upload_asset(image_path)

    manifest = []
    for label, overrides in RUNS:
        params = {**BASELINE, **overrides}
        print(f"\n--- {label} --- params={params}")
        job_id = atlas.submit_job(
            "telablur-v1", params,
            {"image1": image_asset, "image2": image_asset},
        )
        st, elapsed = atlas.wait_for_job(job_id)
        print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            manifest.append({"label": label, "job_id": job_id, "params": params,
                              "status": st["status"], "error": st.get("error")})
            continue

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"{label}.png"
        for out in result.get("outputs") or []:
            out_path.write_bytes(requests.get(out["url"]).content)
        print(f"saved {out_path}")

        manifest.append({"label": label, "job_id": job_id, "params": params,
                          "elapsed_s": round(elapsed, 1), "file": str(out_path)})

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} runs in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
