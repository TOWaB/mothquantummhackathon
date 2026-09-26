"""
Person-segmentation mask test: real subject cutout, not a geometric shape.

image1 = H66A1993mab.jpg, image2 = H66A0009mab.jpg. rembg (U2Net, runs
locally, no cloud call) segments the person(s) out of image1 into a per-pixel
alpha matte. We save that as a mask two ways:

  - mask_person.png       white = person   -> Telablur effect applies TO the person
  - mask_background.png   white = background -> Telablur effect applies to everything BUT the person

Runs both so we can compare which reads better before picking one for real.
Run with: uv run --python .venv person_mask_test.py
"""
import json
from pathlib import Path

import requests
from PIL import Image, ImageOps
from rembg import remove

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out")
STATE_DIR = Path("state")
OUT_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)

IMAGE1_NAME = "H66A1993mab.jpg"
IMAGE2_NAME = "H66A0009mab.jpg"


def run_variant(label, image1_path, image2_path, mask_path, strength=0.6):
    print(f"\n--- {label} ---")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)
    mask_asset = atlas.upload_asset(mask_path)

    job_id = atlas.submit_job(
        "telablur-v1", {"strength": strength},
        {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset},
    )
    print(f"job {job_id} submitted")
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"{st['status']} in {elapsed:.1f}s")
    if st["status"] != "completed":
        print(f"FAILED: {st.get('error')}")
        return None

    result = atlas.fetch_result(job_id)
    out_path = OUT_DIR / f"person_mask_{label}_{job_id}.png"
    for out in result.get("outputs") or []:
        out_path.write_bytes(requests.get(out["url"]).content)
    print(f"saved {out_path}")
    return {"label": label, "job_id": job_id, "elapsed_s": round(elapsed, 1), "file": str(out_path)}


def main():
    src1 = IMAGES_DIR / IMAGE1_NAME
    src2 = IMAGES_DIR / IMAGE2_NAME
    if not src1.exists() or not src2.exists():
        print(f"Missing source image(s): {src1.exists()=} {src2.exists()=}")
        return

    print(f"image1: {src1.name}, image2: {src2.name}")

    image1_path = atlas.resize_for_upload(src1, OUT_DIR / "person_mask_image1.png")
    image2_path = atlas.resize_for_upload(src2, OUT_DIR / "person_mask_image2.png")

    print("Segmenting person out of image1 with rembg (first run downloads the model, ~1min)...")
    photo = Image.open(image1_path).convert("RGB")
    cutout = remove(photo)  # RGBA, alpha = subject matte
    person_mask = cutout.split()[-1]  # alpha channel, white=subject
    person_mask_path = OUT_DIR / "person_mask_person.png"
    person_mask.save(person_mask_path)
    print(f"Saved {person_mask_path}")

    background_mask = ImageOps.invert(person_mask)
    background_mask_path = OUT_DIR / "person_mask_background.png"
    background_mask.save(background_mask_path)
    print(f"Saved {background_mask_path}")

    manifest = []
    manifest.append(run_variant("effect-on-person", image1_path, image2_path, person_mask_path))
    manifest.append(run_variant("effect-on-background", image1_path, image2_path, background_mask_path))

    (STATE_DIR / "person_mask_test.json").write_text(json.dumps(manifest, indent=2))
    print("\nBoth variants done. Compare the two result files in out/.")


if __name__ == "__main__":
    main()
