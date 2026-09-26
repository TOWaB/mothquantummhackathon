"""
Test set 09: same strength x direction grid as 08, new image pair —
image1=H66A1678mab.jpg, image2=H66A2008mab.jpg (both b&w). Mask is a fresh
person/background segmentation of image1 (rembg), not reused from set 04 —
the person's position/silhouette is different in this photo.

Grid: strength in {0.1, 0.3, 0.5, 0.7, 0.9} x direction in {full, vertical, horizontal}
= 15 runs.

Run with: uv run --python .venv 09_direction_strength_grid_bw.py
"""
import json
from pathlib import Path

import requests
from PIL import Image, ImageOps
from rembg import remove

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/09_direction_strength_grid_bw")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE1_NAME = "H66A1678mab.jpg"
IMAGE2_NAME = "H66A2008mab.jpg"

STRENGTHS = [0.1, 0.3, 0.5, 0.7, 0.9]
DIRECTIONS = ["full", "vertical", "horizontal"]


def main():
    src1 = IMAGES_DIR / IMAGE1_NAME
    src2 = IMAGES_DIR / IMAGE2_NAME
    if not src1.exists() or not src2.exists():
        print(f"Missing source image(s): {src1.exists()=} {src2.exists()=}")
        return

    print(f"image1={IMAGE1_NAME}, image2={IMAGE2_NAME}")
    image1_path = atlas.resize_for_upload(src1, OUT_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(src2, OUT_DIR / "image2.png")

    print("Segmenting person out of image1 with rembg...")
    photo = Image.open(image1_path).convert("RGB")
    cutout = remove(photo)
    person_mask = cutout.split()[-1]
    background_mask = ImageOps.invert(person_mask)
    mask_path = OUT_DIR / "mask_background.png"
    background_mask.save(mask_path)
    print(f"Saved {mask_path}")

    print("Uploading image1, image2, mask once, reused every run...")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)
    mask_asset = atlas.upload_asset(mask_path)

    manifest = []
    for strength in STRENGTHS:
        for direction in DIRECTIONS:
            run_label = f"strength_{strength}_{direction}"
            params = {"strength": strength, "direction": direction}
            input_files = {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset}

            print(f"\n--- {run_label} ---")
            job_id = atlas.submit_job("telablur-v1", params, input_files)
            st, elapsed = atlas.wait_for_job(job_id)
            print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

            if st["status"] != "completed":
                print(f"FAILED: {st.get('error')}")
                manifest.append({"label": run_label, "job_id": job_id, "params": params,
                                  "status": st["status"], "error": st.get("error")})
                continue

            result = atlas.fetch_result(job_id)
            out_path = OUT_DIR / f"{run_label}.png"
            for out in result.get("outputs") or []:
                out_path.write_bytes(requests.get(out["url"]).content)
            print(f"saved {out_path}")

            manifest.append({"label": run_label, "job_id": job_id, "params": params,
                              "elapsed_s": round(elapsed, 1), "file": str(out_path)})

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} runs in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
