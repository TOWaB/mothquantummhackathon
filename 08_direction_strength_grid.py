"""
Test set 08: strength x direction grid, run twice — once with the SAME image
in both slots (image1=image2, no mask — isolates the encode/measure floor),
once with TWO different images + the person mask (image1=horn player,
image2=violinists, background protected). Same grid both times so we can
see whether the winning combo (low strength + vertical/horizontal direction)
holds up the same way in both cases.

Grid: strength in {0.1, 0.3, 0.5, 0.7, 0.9} x direction in {full, vertical, horizontal}
= 15 runs each (30 total). Wide open on purpose — not presupposing that low
strength or vertical/horizontal wins; strength across the full range may reveal
image2 content in ways the earlier narrow low-strength tests didn't show.

Run with: uv run --python .venv 08_direction_strength_grid.py
"""
import json
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/08_direction_strength_grid")
SELF_DIR = OUT_DIR / "self"
TWO_DIR = OUT_DIR / "two_images"
SELF_DIR.mkdir(parents=True, exist_ok=True)
TWO_DIR.mkdir(parents=True, exist_ok=True)

SELF_IMAGE = "H66A0009mab.jpg"
IMAGE1_NAME = "H66A1993mab.jpg"
IMAGE2_NAME = "H66A0009mab.jpg"
MASK_PATH = Path("out/04_person_mask/person_mask_background.png")

STRENGTHS = [0.1, 0.3, 0.5, 0.7, 0.9]
DIRECTIONS = ["full", "vertical", "horizontal"]


def run_grid(label, out_dir, image1_asset, image2_asset, mask_asset=None):
    manifest = []
    for strength in STRENGTHS:
        for direction in DIRECTIONS:
            run_label = f"strength_{strength}_{direction}"
            params = {"strength": strength, "direction": direction}
            input_files = {"image1": image1_asset, "image2": image2_asset}
            if mask_asset:
                input_files["mask"] = mask_asset

            print(f"\n--- [{label}] {run_label} ---")
            job_id = atlas.submit_job("telablur-v1", params, input_files)
            st, elapsed = atlas.wait_for_job(job_id)
            print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

            if st["status"] != "completed":
                print(f"FAILED: {st.get('error')}")
                manifest.append({"label": run_label, "job_id": job_id, "params": params,
                                  "status": st["status"], "error": st.get("error")})
                continue

            result = atlas.fetch_result(job_id)
            out_path = out_dir / f"{run_label}.png"
            for out in result.get("outputs") or []:
                out_path.write_bytes(requests.get(out["url"]).content)
            print(f"saved {out_path}")

            manifest.append({"label": run_label, "job_id": job_id, "params": params,
                              "elapsed_s": round(elapsed, 1), "file": str(out_path)})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    print("=== self case: image1 = image2 =", SELF_IMAGE, "===")
    self_path = atlas.resize_for_upload(IMAGES_DIR / SELF_IMAGE, SELF_DIR / "image.png")
    self_asset = atlas.upload_asset(self_path)
    run_grid("self", SELF_DIR, self_asset, self_asset)

    print(f"\n=== two-image case: image1={IMAGE1_NAME}, image2={IMAGE2_NAME}, mask=background ===")
    image1_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE1_NAME, TWO_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(IMAGES_DIR / IMAGE2_NAME, TWO_DIR / "image2.png")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)
    mask_asset = atlas.upload_asset(MASK_PATH)
    run_grid("two_images", TWO_DIR, image1_asset, image2_asset, mask_asset)

    print(f"\nDone. Results in {SELF_DIR}/ and {TWO_DIR}/.")


if __name__ == "__main__":
    main()
