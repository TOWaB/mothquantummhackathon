"""
Test set 12: distance_gradient mask (shape-aware gradient around the person's
silhouette, from mask.py) run through telablur-v1 for real, at 3 radii.

image1=H66A1678mab.jpg, image2=H66A2008mab.jpg (same pair as sets 09/10).
strength=0.6, direction=full (baseline defaults — this test isolates the
mask shape, not strength/direction).

Run with: uv run --python .venv 12_gradient_mask_test.py
"""
import json
from pathlib import Path

import requests

import atlas
import mask

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/12_gradient_mask_test")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE1_NAME = "H66A1678mab.jpg"
IMAGE2_NAME = "H66A2008mab.jpg"
RADII = [30, 60, 100]
STRENGTH = 0.6
DIRECTION = "full"


def main():
    src1 = IMAGES_DIR / IMAGE1_NAME
    src2 = IMAGES_DIR / IMAGE2_NAME
    print(f"image1={IMAGE1_NAME}, image2={IMAGE2_NAME}, strength={STRENGTH}, direction={DIRECTION}")

    image1_path = atlas.resize_for_upload(src1, OUT_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(src2, OUT_DIR / "image2.png")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)

    print("Segmenting person out of image1...")
    alpha = mask.segment_person(image1_path)

    manifest = []
    for radius in RADII:
        label = f"gradient_radius_{radius}"
        print(f"\n--- {label} ---")
        gradient = mask.distance_gradient(alpha, radius=radius)
        mask_path = OUT_DIR / f"{label}_mask.png"
        gradient.save(mask_path)
        mask_asset = atlas.upload_asset(mask_path)

        params = {"strength": STRENGTH, "direction": DIRECTION}
        job_id = atlas.submit_job(
            "telablur-v1", params,
            {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset},
        )
        st, elapsed = atlas.wait_for_job(job_id)
        print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

        entry = {"label": label, "radius": radius, "params": params, "job_id": job_id}
        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            entry["status"] = st["status"]
            entry["error"] = st.get("error")
            manifest.append(entry)
            continue

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"{label}_result.png"
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
