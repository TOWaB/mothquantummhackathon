"""
Test set 13: the 3 distance_gradient masks from set 12 (radius 30/60/100)
x 5 strengths each = 15 runs. Direction fixed to "full" (isolating mask
shape x strength; direction already covered in sets 08/09).

Reuses the mask PNGs already generated in out/12_gradient_mask_test/ instead
of re-running rembg segmentation.

Run with: uv run --python .venv 13_gradient_strength_grid.py
"""
import json
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
PREV_DIR = Path("out/12_gradient_mask_test")
OUT_DIR = Path("out/13_gradient_strength_grid")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE1_NAME = "H66A1678mab.jpg"
IMAGE2_NAME = "H66A2008mab.jpg"
RADII = [30, 60, 100]
STRENGTHS = [0.1, 0.3, 0.5, 0.7, 0.9]
DIRECTION = "full"


def main():
    print(f"image1={IMAGE1_NAME}, image2={IMAGE2_NAME}, direction={DIRECTION}")
    image1_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE1_NAME, OUT_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE2_NAME, OUT_DIR / "image2.png")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)

    mask_assets = {}
    for radius in RADII:
        mask_path = PREV_DIR / f"gradient_radius_{radius}_mask.png"
        if not mask_path.exists():
            print(f"Missing {mask_path} — run 12_gradient_mask_test.py first.")
            return
        mask_assets[radius] = atlas.upload_asset(mask_path)

    manifest = []
    for radius in RADII:
        for strength in STRENGTHS:
            run_label = f"radius_{radius}_strength_{strength}"
            params = {"strength": strength, "direction": DIRECTION}
            print(f"\n--- {run_label} ---")
            job_id = atlas.submit_job(
                "telablur-v1", params,
                {"image1": image1_asset, "image2": image2_asset, "mask": mask_assets[radius]},
            )
            st, elapsed = atlas.wait_for_job(job_id)
            print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

            entry = {"label": run_label, "radius": radius, "params": params, "job_id": job_id}
            if st["status"] != "completed":
                print(f"FAILED: {st.get('error')}")
                entry["status"] = st["status"]
                entry["error"] = st.get("error")
                manifest.append(entry)
                continue

            result = atlas.fetch_result(job_id)
            out_path = OUT_DIR / f"{run_label}.png"
            for out in result.get("outputs") or []:
                out_path.write_bytes(requests.get(out["url"]).content)
            print(f"saved {out_path}")

            entry["elapsed_s"] = round(elapsed, 1)
            entry["file"] = str(out_path)
            manifest.append(entry)

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} runs in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
